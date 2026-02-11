from flask import Flask, render_template, request, redirect, url_for, session
import json
from flask_session import Session
import sys
from datetime import datetime
import os
from flask_sqlalchemy import SQLAlchemy
import numpy as np
from constants import *
from threading import Lock
import random
from util import load_identity_assets, create_subsets, build_repack_manifest

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = str(np.random.randint(sys.maxsize))
app.config['SQLALCHEMY_DATABASE_URI'] = DB_PROD
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)
db = SQLAlchemy(app)

# Create a lock object for thread-safe user assignment
transaction_lock = Lock()

# Load data
instance_pairs, sentinels = load_identity_assets()
# subsets = create_subsets(instance_pairs, sentinels)
all_abs_ids = [p["absolute_index"] for p in instance_pairs]
manifest = build_repack_manifest(
    all_abs_ids,
    exclude_abs_ids=OMIT_PAIR_IDS,
    version="v2_after_omit"
)
# Filter instance pairs before creating new subsets
kept_pairs = [p for p in instance_pairs if p["absolute_index"] not in OMIT_PAIR_IDS]
subsets = create_subsets(kept_pairs, sentinels)

# Define the model for storing identity judgements
class IdentityJudgement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prolific_pid = db.Column(db.String(255))
    study_id = db.Column(db.String(255))
    session_id = db.Column(db.String(255))
    subset_id = db.Column(db.Integer)
    pair_index = db.Column(db.Integer)
    absolute_pair_index = db.Column(db.Integer)  # New: absolute index in original pairs_data
    instance_a_images = db.Column(db.Text)  # JSON string of image paths
    instance_b_images = db.Column(db.Text)  # JSON string of image paths
    decision = db.Column(db.String(50))
    datetime = db.Column(db.String(255))
    is_sentinel = db.Column(db.Integer)
    sentinel_gt = db.Column(db.String(255))
    instance_a_id = db.Column(db.String(255))  # New: original instance ID
    instance_b_id = db.Column(db.String(255))  # New: original instance ID
    sentinel_key = db.Column(db.String(255))   # New: sentinel identifier
    is_shuffled = db.Column(db.Integer)  # New: tracks if left/right images were shuffled
    reference_images = db.Column(db.Text)  # JSON string of reference image paths for the pair
    text_prompt = db.Column(db.Text)  # Text prompt describing the object for this pair

# Define the model for tracking users
class IdentityUsers(db.Model):
    prolific_pid = db.Column(db.String(255), primary_key=True)
    study_id = db.Column(db.String(255))
    session_id = db.Column(db.String(255))
    subset_id = db.Column(db.Integer)
    subset_number = db.Column(db.Integer)
    done = db.Column(db.Integer)

with app.app_context():
    db.create_all()

def assign_user_to_subset(pid):
    """Assign user to a subset for annotation"""
    with transaction_lock:
        try:
            existing_user = IdentityUsers.query.get(pid)
            if existing_user is None:
                # Assign new user to a subset
                users = IdentityUsers.query.all()
                users_per_subset = {}
                
                # Initialize counts for all subsets (excluding omitted ones)
                available_subsets = [sid for sid in subsets.keys() if sid not in OMIT_SUBSETS]
                users_per_subset = {}
                for subset_id in available_subsets:
                    users_per_subset[subset_id] = 0
                
                # Count existing users per subset (only for available subsets)
                for user in users:
                    if user.subset_id in available_subsets:
                        users_per_subset[user.subset_id] += 1
                
                # Check if we have any available subsets
                if not available_subsets:
                    print(f"ERROR: No available subsets for assignment. All subsets are omitted: {OMIT_SUBSETS}")
                    raise ValueError("No available subsets for assignment. All subsets are omitted.")
                
                # Log subset assignment info
                if OMIT_SUBSETS:
                    print(f"Subset assignment: Available subsets {available_subsets}, Omitted subsets {OMIT_SUBSETS}")
                
                # Find next available subset or use round-robin if all are full
                next_subset = None
                for subset_id, count in users_per_subset.items():
                    if count < MAX_USERS_PER_SUBSET:
                        next_subset = subset_id
                        break
                
                if next_subset is None:
                    # All available subsets are full, use round-robin assignment
                    # Find the subset with the minimum number of users
                    min_count = min(users_per_subset.values())
                    subsets_with_min = [sid for sid, count in users_per_subset.items() if count == min_count]
                    # Choose the first subset with minimum count (maintains order)
                    next_subset = min(subsets_with_min)

                session['subset_id'] = next_subset
                session['subset_number'] = users_per_subset[next_subset] + 1
                
                new_user = IdentityUsers(
                    prolific_pid=str(session['prolific_pid']),
                    study_id=str(session['study_id']),
                    session_id=str(session['session_id']),
                    subset_id=int(session['subset_id']),
                    subset_number=int(session['subset_number']),
                    done=0
                )
                db.session.add(new_user)
                db.session.commit()
                
                # Log user assignment event
                assignment_type = "available" if users_per_subset[next_subset] < MAX_USERS_PER_SUBSET else "round-robin"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] USER_ASSIGNED: PID={session['prolific_pid']}, subset_id={next_subset}, subset_number={session['subset_number']}, type={assignment_type}, available_subsets={len(available_subsets)}")
                
                return False
            else:
                if existing_user.done == 1:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] USER_RETURNING: PID={pid}, status=completed, subset_id={existing_user.subset_id}")
                    return True
                else:
                    session['subset_id'] = existing_user.subset_id
                    session['subset_number'] = existing_user.subset_number
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] USER_RETURNING: PID={pid}, status=in_progress, subset_id={existing_user.subset_id}, subset_number={existing_user.subset_number}")
                    return False
        except Exception as e:
            db.session.rollback()
            raise e

@app.route('/')
def start():
    pid = str(request.args.get('PROLIFIC_PID', '0'))
    study_id = str(request.args.get('STUDY_ID', '0'))
    session_id = str(request.args.get('SESSION_ID', '0'))
    session['prolific_pid'] = pid
    session['study_id'] = study_id
    session['session_id'] = session_id
    is_done = assign_user_to_subset(pid)

    if 'current_pair_index' in session:
        # Check actual subset length instead of fixed TOTAL_PAIRS_PER_USER
        subset_id = session.get('subset_id', 0)
        actual_subset_length = len(subsets[subset_id])
        is_done = session['current_pair_index'] >= actual_subset_length
        
    if is_done:
        return render_template('already_completed.html')
    else:
        return render_template('start.html', 
                             pid=pid, 
                             subset_id=session['subset_id'], 
                             subset_number=session['subset_number'])

@app.route('/index')
def index():
    if 'current_pair_index' not in session:
        session['current_pair_index'] = 0
    if 'current_pair' not in session:
        session['current_pair'] = None
    if 'is_sentinel' not in session:
        session['is_sentinel'] = 0
    if 'sentinel_gt' not in session:
        session['sentinel_gt'] = 'N/A'

    # Get current pair
    subset_id = session['subset_id']
    
    # Check if we've reached the end of the subset
    subset_length = len(subsets[subset_id])
    current_index = session['current_pair_index']
    
    if current_index >= subset_length:
        print(f"User {session['prolific_pid']} completed subset {subset_id}: {current_index}/{subset_length} pairs")
        existing_user = IdentityUsers.query.get(session['prolific_pid'])
        existing_user.done = 1
        db.session.commit()
        return redirect(url_for('close'))
    
    current_pair_data = subsets[subset_id][session['current_pair_index']]
    
    # Store the full pair data in session for robust tracking
    session['current_pair_data'] = current_pair_data
    
    if current_pair_data['is_sentinel']:
        session['current_pair'] = [current_pair_data['images_a'], current_pair_data['images_b']]
        session['is_sentinel'] = 1
        session['sentinel_gt'] = current_pair_data['ground_truth']
        reference_images = []  # No references for sentinels
        text_prompt = ''  # No text prompt for sentinels
    else:
        session['current_pair'] = [current_pair_data['images_a'], current_pair_data['images_b']]
        session['is_sentinel'] = 0
        session['sentinel_gt'] = "N/A"
        # Get reference images if enabled
        if SHOW_REFERENCE_IMAGES:
            reference_images = current_pair_data.get('reference_images', [])
        else:
            reference_images = []
        # Get text prompt
        text_prompt = current_pair_data.get('text_prompt', '')
    
    return render_template('index_identity.html', 
                         current_pair=session['current_pair'],
                         current_pair_index=session['current_pair_index'],
                         total=subset_length,
                         response_options=RESPONSE_OPTIONS,
                         reference_images=reference_images,
                         show_references=SHOW_REFERENCE_IMAGES,
                         text_prompt=text_prompt,
                         task_prompt=TASK_PROMPT)

@app.route('/select', methods=['POST'])
def select():
    selected_response = request.form.get('selected_response')
    dt = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
    
    if selected_response:
        current_pair_data = session['current_pair_data']
        
        # Extract metadata from session data
        if current_pair_data['is_sentinel']:
            absolute_pair_index = -1  # Sentinels don't have absolute indices
            instance_a_id = "sentinel"
            instance_b_id = "sentinel"
            sentinel_key = current_pair_data.get('sentinel_key', 'unknown')
        else:
            absolute_pair_index = current_pair_data['absolute_index']
            instance_a_id = current_pair_data['instance_a_id']
            instance_b_id = current_pair_data['instance_b_id']
            sentinel_key = "N/A"
        
        # Get shuffling information from the pair data
        is_shuffled = current_pair_data.get('is_shuffled', False)
        
        # Get reference images and text prompt
        reference_images = current_pair_data.get('reference_images', [])
        text_prompt = current_pair_data.get('text_prompt', '')
        
        decision = IdentityJudgement(
            prolific_pid=str(session['prolific_pid']),
            study_id=str(session['study_id']),
            session_id=str(session['session_id']),
            subset_id=int(session['subset_id']),
            pair_index=int(session['current_pair_index']),
            absolute_pair_index=int(absolute_pair_index),
            instance_a_images=json.dumps(session['current_pair'][0]),
            instance_b_images=json.dumps(session['current_pair'][1]),
            decision=str(selected_response),
            datetime=str(dt),
            is_sentinel=int(session['is_sentinel']),
            sentinel_gt=str(session['sentinel_gt']),
            instance_a_id=str(instance_a_id),
            instance_b_id=str(instance_b_id),
            sentinel_key=str(sentinel_key),
            is_shuffled=int(is_shuffled),
            reference_images=json.dumps(reference_images),
            text_prompt=str(text_prompt)
        )
        db.session.add(decision)
        db.session.commit()
        session['current_pair_index'] += 1
        
    return redirect(url_for('index'))

@app.route('/close')
def close():
    return render_template('close.html')

@app.route('/finish')
def finish():
    return redirect(f"https://app.prolific.co/submissions/complete?cc={COMPLETION_CODE}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)





