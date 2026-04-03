"""
Bumblebee Synthetic Image Evaluation Server
Multi-stage expert evaluation for AI-generated bumblebee images
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = str(np.random.randint(sys.maxsize))
app.config['SQLALCHEMY_DATABASE_URI'] = ACTIVE_DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)
db = SQLAlchemy(app)

# Thread-safe user assignment
transaction_lock = Lock()

# ============================================
# DATABASE MODELS
# ============================================

class InsectEvaluation(db.Model):
    """Database model for expert insect image evaluations"""
    __tablename__ = 'insect_evaluation'

    id = db.Column(db.Integer, primary_key=True)

    # User tracking
    participant_id = db.Column(db.String(255), nullable=False)
    study_id = db.Column(db.String(255))
    session_id = db.Column(db.String(255))
    subset_id = db.Column(db.Integer, nullable=False)
    image_index = db.Column(db.Integer, nullable=False)  # Index within subset
    absolute_image_index = db.Column(db.Integer, nullable=False)  # Global image ID

    # Image metadata
    image_path = db.Column(db.Text, nullable=False)
    ground_truth_family = db.Column(db.String(255))
    ground_truth_genus = db.Column(db.String(255))
    ground_truth_species = db.Column(db.String(255))
    model_type = db.Column(db.String(100))
    generation_angle = db.Column(db.String(50))
    generation_gender = db.Column(db.String(50))

    # STAGE 1: Blind Species ID
    blind_id_family = db.Column(db.String(255))
    blind_id_genus = db.Column(db.String(255))
    blind_id_species = db.Column(db.String(255))

    # STAGE 2: Blind Caste ID
    blind_id_caste = db.Column(db.String(50))
    caste_ground_truth = db.Column(db.String(50))

    # LLM judge metadata (for disagreement analysis)
    tier = db.Column(db.String(50))
    llm_morph_mean = db.Column(db.Float)

    # STAGE 2: Morphological Fidelity (1-5 scale)
    morph_legs_appendages = db.Column(db.Integer)
    morph_wing_venation_texture = db.Column(db.Integer)
    morph_head_antennae = db.Column(db.Integer)
    morph_abdomen_banding = db.Column(db.Integer)
    morph_thorax_coloration = db.Column(db.Integer)

    # STAGE 2: Diagnostic Completeness
    diagnostic_level = db.Column(db.String(50))  # "none", "family", "genus", "species"

    # STAGE 2: Failure Modes (JSON array)
    failure_modes = db.Column(db.Text)  # Stored as JSON string

    # Timing
    time_stage1 = db.Column(db.Float)  # Seconds for Stage 1
    time_stage2 = db.Column(db.Float)  # Seconds for Stage 2
    datetime = db.Column(db.String(255))

    # Reference images shown (JSON array)
    reference_images = db.Column(db.Text)


class EvaluationUsers(db.Model):
    """Track users and their assigned subsets"""
    __tablename__ = 'evaluation_users'

    participant_id = db.Column(db.String(255), primary_key=True)
    study_id = db.Column(db.String(255))
    session_id = db.Column(db.String(255))
    subset_id = db.Column(db.Integer)
    subset_number = db.Column(db.Integer)
    done = db.Column(db.Integer, default=0)
    datetime_started = db.Column(db.String(255))
    datetime_completed = db.Column(db.String(255))


# ============================================
# DATA LOADING
# ============================================

def load_bumblebee_metadata():
    """Load bumblebee image metadata from JSON"""
    metadata_path = os.path.join(os.path.dirname(__file__), METADATA_JSON)

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    print(f"✓ Loaded {len(metadata)} images from {metadata_path}")
    return metadata


def create_image_subsets(metadata, images_per_user=IMAGES_PER_USER):
    """
    Create overlapping subsets of images for multiple annotators.
    Each subset has exactly images_per_user images.
    """
    # Convert metadata dict to list of (image_id, data) tuples
    all_images = [(int(img_id), data) for img_id, data in metadata.items()]

    # Exclude omitted images
    all_images = [(img_id, data) for img_id, data in all_images
                  if img_id not in OMIT_IMAGE_IDS]

    # Shuffle globally so species are mixed (not grouped sequentially)
    random.seed(42)  # Reproducible shuffle
    random.shuffle(all_images)

    total_images = len(all_images)

    if total_images < images_per_user:
        print(f"WARNING: Only {total_images} images available, less than {images_per_user} requested")
        images_per_user = total_images

    # Calculate number of subsets
    num_subsets = (total_images + images_per_user - 1) // images_per_user

    subsets = {}
    for subset_id in range(num_subsets):
        start_idx = subset_id * images_per_user
        end_idx = min(start_idx + images_per_user, total_images)

        subset_images = all_images[start_idx:end_idx]

        subsets[subset_id] = subset_images
        print(f"  Subset {subset_id}: {len(subset_images)} images (IDs {subset_images[0][0]}-{subset_images[-1][0]})")

    return subsets


# Load data at startup
try:
    metadata = load_bumblebee_metadata()
    subsets = create_image_subsets(metadata)
    print(f"✓ Created {len(subsets)} subsets with up to {IMAGES_PER_USER} images each")
except Exception as e:
    print(f"ERROR loading data: {e}")
    metadata = {}
    subsets = {}


# Initialize database
with app.app_context():
    db.create_all()
    print("✓ Database initialized")


# ============================================
# USER ASSIGNMENT
# ============================================

def assign_user_to_subset(pid):
    """Assign user to a subset for evaluation. Returns True if user already completed."""
    with transaction_lock:
        try:
            existing_user = EvaluationUsers.query.get(pid)

            if existing_user is None:
                # New user - assign to subset
                users = EvaluationUsers.query.all()

                # Get available subsets (excluding omitted)
                available_subsets = [sid for sid in subsets.keys() if sid not in OMIT_SUBSETS]

                if not available_subsets:
                    raise ValueError("No available subsets for assignment")

                # Count users per subset
                users_per_subset = {sid: 0 for sid in available_subsets}
                for user in users:
                    if user.subset_id in available_subsets:
                        users_per_subset[user.subset_id] += 1

                # Find next available subset
                next_subset = None
                for subset_id, count in users_per_subset.items():
                    if count < MAX_USERS_PER_SUBSET:
                        next_subset = subset_id
                        break

                if next_subset is None:
                    # All full, use round-robin
                    min_count = min(users_per_subset.values())
                    subsets_with_min = [sid for sid, count in users_per_subset.items()
                                       if count == min_count]
                    next_subset = min(subsets_with_min)

                session['subset_id'] = next_subset
                session['subset_number'] = users_per_subset[next_subset] + 1

                new_user = EvaluationUsers(
                    participant_id=str(pid),
                    study_id=str(session.get('study_id', '0')),
                    session_id=str(session.get('session_id', '0')),
                    subset_id=int(next_subset),
                    subset_number=int(session['subset_number']),
                    done=0,
                    datetime_started=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                db.session.add(new_user)
                db.session.commit()

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] USER_ASSIGNED: PID={pid}, subset={next_subset}, "
                      f"subset_number={session['subset_number']}")

                return False
            else:
                # Returning user
                session['subset_id'] = existing_user.subset_id
                session['subset_number'] = existing_user.subset_number

                if existing_user.done == 1:
                    print(f"USER_RETURNING: PID={pid}, status=completed")
                    return True
                else:
                    print(f"USER_RETURNING: PID={pid}, status=in_progress, "
                          f"subset={existing_user.subset_id}")
                    return False

        except Exception as e:
            db.session.rollback()
            raise e


# ============================================
# ROUTES
# ============================================

@app.route('/')
def start():
    """Landing page - capture participant ID and assign user"""
    pid = str(request.args.get('PARTICIPANT_ID', request.args.get('PROLIFIC_PID', '0')))
    study_id = str(request.args.get('STUDY_ID', '0'))
    session_id_param = str(request.args.get('SESSION_ID', '0'))

    session['participant_id'] = pid
    session['study_id'] = study_id
    session['session_id'] = session_id_param

    is_done = assign_user_to_subset(pid)

    # Check if user already completed
    if 'current_image_index' in session:
        subset_id = session.get('subset_id', 0)
        subset_length = len(subsets[subset_id])
        is_done = session['current_image_index'] >= subset_length

    if is_done:
        return render_template('already_completed.html',
                             completion_code=COMPLETION_CODE)
    else:
        return render_template('start_evaluation.html',
                             pid=pid,
                             subset_id=session['subset_id'],
                             subset_number=session['subset_number'],
                             total_images=len(subsets[session['subset_id']]),
                             mode=MODE)


@app.route('/evaluate')
def evaluate():
    """Main evaluation interface - two-stage workflow"""
    # Initialize session variables
    if 'current_image_index' not in session:
        session['current_image_index'] = 0
    if 'stage1_start_time' not in session:
        session['stage1_start_time'] = None

    subset_id = session['subset_id']
    current_index = session['current_image_index']
    subset_length = len(subsets[subset_id])

    # Check if completed
    if current_index >= subset_length:
        print(f"User {session['participant_id']} completed subset {subset_id}: "
              f"{current_index}/{subset_length} images")

        existing_user = EvaluationUsers.query.get(session['participant_id'])
        existing_user.done = 1
        existing_user.datetime_completed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.session.commit()

        return redirect(url_for('complete'))

    # Get current image data
    image_id, image_data = subsets[subset_id][current_index]

    # Store in session
    session['current_image_id'] = image_id
    session['current_image_data'] = image_data
    session['stage1_start_time'] = datetime.now().timestamp()

    # Prepare data for template
    image_path = image_data['image_path']
    reference_images = image_data.get('reference_images', []) if SHOW_REFERENCE_IMAGES else []

    return render_template('evaluation_form.html',
                         image_path=image_path,
                         image_index=current_index,
                         total_images=subset_length,
                         taxonomy_options=TAXONOMY_OPTIONS,
                         morphological_features=MORPHOLOGICAL_FEATURES,
                         diagnostic_levels=DIAGNOSTIC_LEVELS,
                         failure_mode_species=FAILURE_MODE_SPECIES,
                         failure_mode_quality=FAILURE_MODE_QUALITY,
                         reference_images=reference_images,
                         show_references=SHOW_REFERENCE_IMAGES)


@app.route('/submit_stage1', methods=['POST'])
def submit_stage1():
    """AJAX endpoint for Stage 1 blind ID submission"""
    try:
        data = request.get_json()

        # Calculate Stage 1 time
        stage1_end = datetime.now().timestamp()
        stage1_start = session.get('stage1_start_time', stage1_end)
        time_stage1 = stage1_end - stage1_start

        # Store Stage 1 data in session
        session['blind_id_family'] = data.get('family', '')
        session['blind_id_genus'] = data.get('genus', '')
        session['blind_id_species'] = data.get('species', '')
        session['time_stage1'] = time_stage1
        session['stage2_start_time'] = datetime.now().timestamp()

        # Get ground truth for reveal
        image_data = session['current_image_data']
        ground_truth = image_data.get('ground_truth', {})

        # Get reference images
        reference_images = image_data.get('reference_images', []) if SHOW_REFERENCE_IMAGES else []

        # Get species-specific caste options
        species_name = ground_truth.get('species', '')
        caste_options = CASTE_OPTIONS_BY_SPECIES.get(species_name, CASTE_OPTIONS_DEFAULT)

        return jsonify({
            'success': True,
            'ground_truth': {
                'family': ground_truth.get('family', ''),
                'genus': ground_truth.get('genus', ''),
                'species': ground_truth.get('species', ''),
                'common_name': ground_truth.get('common_name', '')
            },
            'reference_images': reference_images,
            'caste_options': caste_options
        })

    except Exception as e:
        print(f"ERROR in submit_stage1: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/submit_evaluation', methods=['POST'])
def submit_evaluation():
    """Submit complete evaluation (Stage 1 + Stage 2)"""
    try:
        # Calculate Stage 2 time
        stage2_end = datetime.now().timestamp()
        stage2_start = session.get('stage2_start_time', stage2_end)
        time_stage2 = stage2_end - stage2_start

        # Get form data
        form_data = request.form

        # Get image data
        image_id = session['current_image_id']
        image_data = session['current_image_data']
        ground_truth = image_data.get('ground_truth', {})
        gen_metadata = image_data.get('generation_metadata', {})

        # Parse failure modes (multi-select checkboxes) - two categories
        failure_modes_species = form_data.getlist('failure_modes_species[]')
        failure_modes_quality = form_data.getlist('failure_modes_quality[]')
        # Include "other" text if provided
        species_other_text = form_data.get('failure_species_other_text', '').strip()
        quality_other_text = form_data.get('failure_quality_other_text', '').strip()
        # Combine into structured JSON
        failure_modes = failure_modes_species + failure_modes_quality
        failure_modes_json = json.dumps({
            'species': failure_modes_species,
            'species_other_text': species_other_text,
            'quality': failure_modes_quality,
            'quality_other_text': quality_other_text,
            'all': failure_modes
        })

        # Get reference images
        reference_images = image_data.get('reference_images', [])
        reference_images_json = json.dumps(reference_images)

        # Create database entry
        evaluation = InsectEvaluation(
            # User tracking
            participant_id=session['participant_id'],
            study_id=session.get('study_id', '0'),
            session_id=session.get('session_id', '0'),
            subset_id=session['subset_id'],
            image_index=session['current_image_index'],
            absolute_image_index=image_id,

            # Image metadata
            image_path=image_data['image_path'],
            ground_truth_family=ground_truth.get('family', ''),
            ground_truth_genus=ground_truth.get('genus', ''),
            ground_truth_species=ground_truth.get('species', ''),
            model_type=image_data.get('model', ''),
            generation_angle=gen_metadata.get('angle', ''),
            generation_gender=gen_metadata.get('gender', ''),

            # Stage 1: Blind ID (from session)
            blind_id_family=session.get('blind_id_family', ''),
            blind_id_genus=session.get('blind_id_genus', ''),
            blind_id_species=session.get('blind_id_species', ''),

            # Stage 2: Blind Caste ID
            blind_id_caste=form_data.get('blind_id_caste', ''),
            caste_ground_truth=image_data.get('caste_ground_truth', ''),

            # LLM judge metadata
            tier=image_data.get('tier', ''),
            llm_morph_mean=image_data.get('llm_morph_mean'),

            # Stage 2: Morphological Fidelity
            morph_legs_appendages=int(form_data.get('morph_legs_appendages', 0)),
            morph_wing_venation_texture=int(form_data.get('morph_wing_venation_texture', 0)),
            morph_head_antennae=int(form_data.get('morph_head_antennae', 0)),
            morph_abdomen_banding=int(form_data.get('morph_abdomen_banding', 0)),
            morph_thorax_coloration=int(form_data.get('morph_thorax_coloration', 0)),

            # Stage 2: Diagnostic Completeness
            diagnostic_level=form_data.get('diagnostic_level', ''),

            # Stage 2: Failure Modes
            failure_modes=failure_modes_json,

            # Timing
            time_stage1=session.get('time_stage1', 0.0),
            time_stage2=time_stage2,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            # Reference images
            reference_images=reference_images_json
        )

        db.session.add(evaluation)
        db.session.commit()

        # Increment image index
        session['current_image_index'] += 1

        # Clear Stage 1 data from session
        session.pop('blind_id_family', None)
        session.pop('blind_id_genus', None)
        session.pop('blind_id_species', None)
        session.pop('time_stage1', None)
        session.pop('stage1_start_time', None)
        session.pop('stage2_start_time', None)

        print(f"Evaluation saved: User {session['participant_id']}, Image {image_id}, "
              f"Index {session['current_image_index']-1}")

        return redirect(url_for('evaluate'))

    except Exception as e:
        print(f"ERROR in submit_evaluation: {e}")
        db.session.rollback()
        return f"Error submitting evaluation: {str(e)}", 500


@app.route('/complete')
def complete():
    """Completion page with Prolific redirect code"""
    return render_template('complete_evaluation.html',
                         completion_code=COMPLETION_CODE,
                         total_evaluated=session.get('current_image_index', 0))


# ============================================
# ADMIN/DEBUG ROUTES
# ============================================

@app.route('/status')
def status():
    """Show system status and statistics"""
    total_users = EvaluationUsers.query.count()
    completed_users = EvaluationUsers.query.filter_by(done=1).count()
    total_evaluations = InsectEvaluation.query.count()

    # Users per subset
    users_per_subset = {}
    for subset_id in subsets.keys():
        count = EvaluationUsers.query.filter_by(subset_id=subset_id).count()
        users_per_subset[subset_id] = count

    return jsonify({
        'total_images': len(metadata),
        'num_subsets': len(subsets),
        'images_per_user': IMAGES_PER_USER,
        'total_users': total_users,
        'completed_users': completed_users,
        'in_progress_users': total_users - completed_users,
        'total_evaluations': total_evaluations,
        'users_per_subset': users_per_subset
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("BUMBLEBEE EVALUATION SERVER")
    print("="*60)
    print(f"Mode: {MODE}")
    print(f"Database: {ACTIVE_DB}")
    print(f"Total images: {len(metadata)}")
    print(f"Subsets: {len(subsets)}")
    print(f"Images per user: {IMAGES_PER_USER}")
    print(f"Max users per subset: {MAX_USERS_PER_SUBSET}")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
