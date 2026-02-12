# Evaluation Server Infrastructure - Complete Explanation

## 📊 Overview: Old System vs New System

You have **TWO separate Flask applications** that share the same infrastructure but serve different purposes:

### Old System: `app_human_identity_db.py`
**Purpose**: Pair-wise image comparison ("which is more similar to references?")
- **Database**: `instance/identity_judgements_prod_part2_round4.db`
- **Port**: 5001 (originally)
- **Last used**: November 2025 (you have 53 judgements recorded)

### New System: `app_bumblebee_eval.py`
**Purpose**: Multi-question expert evaluation of bumblebee images
- **Database**: `instance/bumblebee_evaluation_prod.db`
- **Port**: 5001 (configured)
- **Status**: Just implemented, ready to test

---

## 🗄️ What Gets Saved in the Database

### Old System Database Tables

**Table: `identity_judgement`** (53 records)
```sql
CREATE TABLE identity_judgement (
    id INTEGER PRIMARY KEY,
    prolific_pid VARCHAR(255),           -- User identifier from Prolific
    study_id VARCHAR(255),               -- Study ID from Prolific
    session_id VARCHAR(255),             -- Session ID from Prolific
    subset_id INTEGER,                   -- Which subset user was assigned
    pair_index INTEGER,                  -- Index within subset
    absolute_pair_index INTEGER,         -- Global index in full dataset
    instance_a_images TEXT,              -- JSON: left image paths
    instance_b_images TEXT,              -- JSON: right image paths
    decision VARCHAR(50),                -- "Left" or "Right"
    datetime VARCHAR(255),               -- When submitted
    is_sentinel INTEGER,                 -- 1 if quality control image
    sentinel_gt VARCHAR(255),            -- Ground truth for sentinel
    instance_a_id VARCHAR(255),          -- ID of left instance
    instance_b_id VARCHAR(255),          -- ID of right instance
    sentinel_key VARCHAR(255),           -- Sentinel identifier
    is_shuffled INTEGER,                 -- Whether images were shuffled
    reference_images TEXT,               -- JSON: reference image paths
    text_prompt TEXT                     -- Task description
);
```

**Table: `identity_users`**
```sql
CREATE TABLE identity_users (
    prolific_pid VARCHAR(255) PRIMARY KEY,  -- Unique user
    study_id VARCHAR(255),
    session_id VARCHAR(255),
    subset_id INTEGER,                      -- Assigned subset
    subset_number INTEGER,                  -- User number within subset
    done INTEGER                            -- 0=in progress, 1=completed
);
```

### New System Database Tables

**Table: `insect_evaluation`** (your new system)
```sql
CREATE TABLE insect_evaluation (
    id INTEGER PRIMARY KEY,

    -- User tracking
    prolific_pid VARCHAR(255) NOT NULL,
    study_id VARCHAR(255),
    session_id VARCHAR(255),
    subset_id INTEGER NOT NULL,
    image_index INTEGER NOT NULL,           -- Position in subset
    absolute_image_index INTEGER NOT NULL,  -- Global image ID

    -- Image metadata
    image_path TEXT NOT NULL,
    ground_truth_family VARCHAR(255),
    ground_truth_genus VARCHAR(255),
    ground_truth_species VARCHAR(255),
    model_type VARCHAR(100),
    generation_angle VARCHAR(50),           -- dorsal/lateral/frontal
    generation_gender VARCHAR(50),          -- male/female

    -- STAGE 1: Blind Species ID
    blind_id_family VARCHAR(255),
    blind_id_genus VARCHAR(255),
    blind_id_species VARCHAR(255),

    -- STAGE 2: Morphological Fidelity (1-5 scale)
    morph_legs_appendages INTEGER,
    morph_wing_venation_texture INTEGER,
    morph_head_antennae INTEGER,
    morph_abdomen_banding INTEGER,
    morph_thorax_coloration INTEGER,
    morph_wing_pit_markings INTEGER,

    -- STAGE 2: Diagnostic Completeness
    diagnostic_level VARCHAR(50),           -- none/family/genus/species

    -- STAGE 2: Failure Modes
    failure_modes TEXT,                     -- JSON array of selected issues

    -- Timing data
    time_stage1 FLOAT,                      -- Seconds for Stage 1
    time_stage2 FLOAT,                      -- Seconds for Stage 2
    datetime VARCHAR(255),                  -- Submission timestamp

    -- Reference images
    reference_images TEXT                   -- JSON array of ref image paths
);
```

**Table: `evaluation_users`**
```sql
CREATE TABLE evaluation_users (
    prolific_pid VARCHAR(255) PRIMARY KEY,
    study_id VARCHAR(255),
    session_id VARCHAR(255),
    subset_id INTEGER,
    subset_number INTEGER,
    done INTEGER,                           -- 0=in progress, 1=completed
    datetime_started VARCHAR(255),
    datetime_completed VARCHAR(255)
);
```

---

## 📁 Directory Structure & What Each Does

### 1. `/flask_session/` - Session Storage
**What it is**: Flask-Session stores user session data in files

**Files**: `2029240f6d1128be89ddc32729463129`, `21d053ff...`, etc.
- These are **session ID hashes**
- Each file contains serialized session data for one user

**What's stored**:
```python
session = {
    'prolific_pid': 'user123',
    'subset_id': 0,
    'current_image_index': 15,
    'blind_id_family': 'Apidae',
    'blind_id_genus': 'Bombus',
    'time_stage1': 22.5,
    # ... etc
}
```

**Why no updates when you run server**:
- Sessions are created **when users access the site**
- Running the server alone doesn't create sessions
- You need to **visit the site in a browser** to create a session

**Lifetime**: Sessions persist across server restarts until they expire or are cleared

---

### 2. `/logs/` - Production Server Logs

**`access.log`** (22 MB):
```
127.0.0.1 - - [18/Sep/2025:18:05:08 -0400] "GET / HTTP/1.1" 200 10677
```
- HTTP access logs (all requests)
- IP addresses, timestamps, URLs accessed
- Response codes (200=success, 404=not found)
- User agents (browsers)

**`error.log`** (3.2 MB):
```
[2025-09-18 17:20:43 -0400] [1462240] [INFO] Starting gunicorn 23.0.0
[2025-09-18 17:20:43 -0400] [1462240] [INFO] Listening at: http://0.0.0.0:5001
```
- Server startup/shutdown events
- Gunicorn worker processes
- Application errors (crashes, exceptions)

**When are they created**:
- Only when running with **Gunicorn** (production server)
- NOT when running with `python app.py` (development mode)
- That's why you don't see new logs - you're in dev mode!

**Development mode**: Logs print to console/terminal instead

---

### 3. `/results/` - Exported Data

**Purpose**: Periodic data exports from database to CSV

**Files**:
- `judgements_updated_20251102_095513.csv` (349 KB) - All evaluation records
- `users_20251102_095513.csv` (1.4 KB) - All user records

**When created**: Manually exported, not automatic

**How to export** (example for new system):
```bash
sqlite3 instance/bumblebee_evaluation_prod.db \
  -header -csv \
  "SELECT * FROM insect_evaluation;" \
  > results/bumblebee_evaluations_$(date +%Y%m%d_%H%M%S).csv
```

---

### 4. `/instance/` - Database Files

**Why `instance/`**: Flask convention for instance-specific files (databases, config)

**Databases**:
- `identity_judgements_prod_part2_round4.db` - Old system (53 records)
- `bumblebee_evaluation_prod.db` - New system (just created, 0 records)

**When created**: First time you run the Flask app
```python
with app.app_context():
    db.create_all()  # Creates tables if they don't exist
```

---

## 🔄 Data Flow: How Results Are Saved

### Old System (`app_human_identity_db.py`)

```
User visits → Session created in flask_session/
↓
User makes decision → POST /select
↓
Create IdentityJudgement object with all data
↓
db.session.add(decision)
db.session.commit()
↓
Data saved to: instance/identity_judgements_prod_part2_round4.db
```

**Code snippet** (lines 261-282 in old app):
```python
decision = IdentityJudgement(
    prolific_pid=str(session['prolific_pid']),
    subset_id=int(session['subset_id']),
    decision=str(selected_response),  # "Left" or "Right"
    datetime=str(dt),
    # ... more fields ...
)
db.session.add(decision)
db.session.commit()  # ← Saves to SQLite database
```

### New System (`app_bumblebee_eval.py`)

```
User visits → Session created in flask_session/
↓
STAGE 1: User submits blind ID → POST /submit_stage1 (AJAX)
↓
Store in session (NOT database yet):
  session['blind_id_family'] = 'Apidae'
  session['blind_id_genus'] = 'Bombus'
  session['time_stage1'] = 22.5
↓
STAGE 2: User completes evaluation → POST /submit_evaluation
↓
Create InsectEvaluation object with ALL data
  (Stage 1 from session + Stage 2 from form)
↓
db.session.add(evaluation)
db.session.commit()
↓
Data saved to: instance/bumblebee_evaluation_prod.db
```

**Code snippet** (lines 411-469 in new app):
```python
# Stage 1 data stored in session
session['blind_id_family'] = data.get('family', '')
session['blind_id_genus'] = data.get('genus', '')
# ... not saved to database yet ...

# Stage 2: Create complete record
evaluation = InsectEvaluation(
    # User info
    prolific_pid=session['prolific_pid'],
    subset_id=session['subset_id'],

    # Ground truth
    ground_truth_species=ground_truth.get('species', ''),

    # Stage 1 (from session)
    blind_id_family=session.get('blind_id_family', ''),
    blind_id_genus=session.get('blind_id_genus', ''),

    # Stage 2 (from form)
    morph_legs_appendages=int(form_data.get('morph_legs_appendages', 0)),
    diagnostic_level=form_data.get('diagnostic_level', ''),

    # Timing
    time_stage1=session.get('time_stage1', 0.0),
    time_stage2=time_stage2
)
db.session.add(evaluation)
db.session.commit()  # ← Saves to SQLite database
```

---

## 🔍 Logging System Explained

### Console Logging (What you see when running)

**Old system prints**:
```python
print(f"[{timestamp}] USER_ASSIGNED: PID={pid}, subset_id={next_subset}")
print(f"[{timestamp}] USER_RETURNING: PID={pid}, status=completed")
print(f"User {session['prolific_pid']} completed subset {subset_id}")
```

**New system prints**:
```python
print(f"✓ Loaded 146 images from {metadata_path}")
print(f"  Subset 0: 50 images (IDs 28-44)")
print(f"[{timestamp}] USER_ASSIGNED: PID={pid}, subset={next_subset}")
print(f"Evaluation saved: User {pid}, Image {image_id}")
```

**Purpose**:
1. **Debugging** - See what's happening in real-time
2. **Monitoring** - Track user assignments and submissions
3. **Error detection** - Spot issues immediately

### File Logging (Production only)

**Only active with Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5001 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  app_bumblebee_eval:app
```

**Development mode** (`python app.py`):
- No file logging
- Everything prints to terminal
- That's why `/logs/` has old dates!

---

## 🧪 Testing: Why Nothing Updates

### Why `flask_session/` isn't updating:

**You haven't visited the site yet!**

Sessions are created when:
1. User opens `http://localhost:5001/?PROLIFIC_PID=test123`
2. Flask-Session creates a new session file
3. User interacts with forms
4. Session data gets updated

**To see session files update**:
```bash
# Terminal 1: Run server
source venv/bin/activate
python app_bumblebee_eval.py

# Terminal 2: Watch sessions
watch -n 1 'ls -lht flask_session/ | head -10'

# Browser: Visit the site
# → You'll see new session files appear!
```

### Why `logs/` isn't updating:

**Development mode doesn't write to log files!**

Old logs are from when you ran Gunicorn in production mode.

**To create new logs**:
```bash
# Install gunicorn if needed
pip install gunicorn

# Run in production mode
gunicorn -w 4 -b 0.0.0.0:5001 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  app_bumblebee_eval:app
```

### Why `results/` isn't updating:

**Manual exports only!**

These are CSV exports you create manually:

```bash
# Export evaluations
sqlite3 instance/bumblebee_evaluation_prod.db <<EOF
.headers on
.mode csv
.output results/bumblebee_eval_$(date +%Y%m%d_%H%M%S).csv
SELECT * FROM insect_evaluation;
.quit
EOF

# Export users
sqlite3 instance/bumblebee_evaluation_prod.db <<EOF
.headers on
.mode csv
.output results/bumblebee_users_$(date +%Y%m%d_%H%M%S).csv
SELECT * FROM evaluation_users;
.quit
EOF
```

---

## 🔧 Shared Infrastructure

Both systems use the same:

### Flask Components
- `Flask` - Web framework
- `Flask-Session` - Session management (same `flask_session/` directory)
- `Flask-SQLAlchemy` - Database ORM

### Session Storage
- Same `flask_session/` directory
- Sessions isolated by session ID (won't conflict)

### Static Files
- Same `static/` directory
- Old system: `static/all_ds_sampled/uco3d/images/...`
- New system: `static/bumblebees/`, `static/references/`

### Templates
- Same `templates/` directory
- Old: `index_identity.html`, `start.html`, `close.html`
- New: `evaluation_form.html`, `start_evaluation.html`, `complete_evaluation.html`

### Can they run simultaneously?

**NO** - Same port (5001)

**Options**:
1. Run on different ports:
   ```python
   # Old: app_human_identity_db.py, line 296
   app.run(debug=True, port=5000)

   # New: app_bumblebee_eval.py, line 519
   app.run(debug=True, port=5001)
   ```

2. Use different databases (already configured ✓)
3. Use different completion codes (already configured ✓)

---

## 📝 Quick Reference

### Check what's in the databases:

```bash
# Old system
sqlite3 instance/identity_judgements_prod_part2_round4.db \
  "SELECT COUNT(*) FROM identity_judgement;"

sqlite3 instance/identity_judgements_prod_part2_round4.db \
  "SELECT prolific_pid, decision, datetime FROM identity_judgement LIMIT 5;"

# New system
sqlite3 instance/bumblebee_evaluation_prod.db \
  "SELECT COUNT(*) FROM insect_evaluation;"

sqlite3 instance/bumblebee_evaluation_prod.db \
  "SELECT prolific_pid, blind_id_species, diagnostic_level FROM insect_evaluation LIMIT 5;"
```

### Monitor sessions:

```bash
# Watch sessions being created
watch -n 2 'ls -lht flask_session/ | head -5'

# View a session file (binary, hard to read):
python3 -c "
import pickle
with open('flask_session/2029240f6d1128be89ddc32729463129', 'rb') as f:
    session = pickle.load(f)
    print(session)
"
```

### Test the new system:

```bash
# 1. Start server
source venv/bin/activate
python app_bumblebee_eval.py

# 2. Visit in browser
http://localhost:5001/?PROLIFIC_PID=test123&STUDY_ID=test&SESSION_ID=1

# 3. Watch database grow
watch -n 2 'sqlite3 instance/bumblebee_evaluation_prod.db "SELECT COUNT(*) FROM insect_evaluation;"'
```

---

## 🎯 Summary

| Component | Purpose | When Updated | Location |
|-----------|---------|--------------|----------|
| **Database** | Permanent storage of evaluations | On form submission | `instance/*.db` |
| **Sessions** | Temporary user state during evaluation | On user interaction | `flask_session/` |
| **Logs** | HTTP access logs, errors | Production mode only | `logs/*.log` |
| **Results** | CSV exports | Manual export only | `results/*.csv` |

**The actual evaluation data lives in the SQLite database!**

Everything else is temporary, auxiliary, or for monitoring.
