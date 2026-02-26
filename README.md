# Bumblebee Synthetic Image Evaluation Server

Expert evaluation server for AI-generated bumblebee images. Experts evaluate synthetic images through a two-stage workflow:

1. **Stage 1 — Blind Identification**: Expert identifies the species from the image alone (Family → Genus → Species dropdowns)
2. **Stage 2 — Detailed Evaluation**: After revealing the target species and reference images, expert rates morphological fidelity, diagnostic completeness, and failure modes

## Project Structure

```
eval_server/
├── app.py                  # Flask application (routes, DB models, logic)
├── constants.py            # Configuration (species, taxonomy, evaluation options)
├── wsgi.py                 # Gunicorn entry point
├── requirements.txt        # Python dependencies
├── gunicorn_config.py      # Gunicorn settings (workers, ports, logging)
├── nginx.conf              # Nginx reverse proxy config
├── deploy_server.sh        # Start/stop/restart server
├── reset_server.sh         # Hard reset (kill processes, clear sessions)
├── templates/
│   ├── start_evaluation.html       # Landing page
│   ├── evaluation_form.html        # Two-stage evaluation interface
│   ├── complete_evaluation.html    # Completion page with Prolific code
│   └── already_completed.html      # Shown to returning users
├── assets/
│   └── bumblebee_images_metadata.json  # Image metadata (paths, ground truth)
├── scripts/
│   ├── generate_bumblebee_metadata.py  # Generate metadata from image directories
│   └── setup_bumblebee_data.sh         # Data setup helper
├── static/
│   ├── bumblebees/         # Synthetic images organized by species
│   └── references/         # Reference images for each species
├── instance/               # SQLite databases (auto-created)
├── logs/                   # Gunicorn/Nginx logs (auto-created)
└── flask_session/          # Server-side session files (auto-created)
```

## Setup

### Prerequisites

- Python 3.10+
- Nginx (`brew install nginx` on macOS)

### 1. Create virtual environment and install dependencies

```bash
cd eval_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Prepare image data

Place synthetic images and reference images under `static/`:

```
static/
├── bumblebees/
│   ├── Bombus_ashtoni/
│   │   ├── image_001.png
│   │   └── ...
│   ├── Bombus_sandersoni/
│   └── Bombus_ternarius_Say/
└── references/
    ├── Bombus_ashtoni/
    │   ├── ref_001.jpg
    │   └── ...
    └── ...
```

### 3. Generate metadata (if not already present)

```bash
python scripts/generate_bumblebee_metadata.py
```

This scans `static/bumblebees/` and writes `assets/bumblebee_images_metadata.json`.

### 4. Configure evaluation parameters

Edit `constants.py` to adjust:

- `IMAGES_PER_USER` — number of images each expert evaluates
- `MAX_USERS_PER_SUBSET` — max experts assigned to the same image subset
- `COMPLETION_CODE` — Prolific completion code
- `OMIT_SUBSETS` / `OMIT_IMAGE_IDS` — exclude specific subsets or images

## Running the Server

### Development (Flask dev server)

```bash
source venv/bin/activate
python app.py
# Runs on http://localhost:5001
```

### Production (Gunicorn + Nginx)

```bash
bash deploy_server.sh start      # Start both Gunicorn and Nginx
bash deploy_server.sh stop       # Stop both
bash deploy_server.sh restart    # Restart both
bash deploy_server.sh status     # Check running status
```

The app is served at **http://localhost:8080**.

Architecture: `Nginx (:8080) → Gunicorn (:5001) → Flask app`

- Nginx serves static files directly and proxies requests to Gunicorn
- Gunicorn runs 2 sync workers with the Flask app

### Hard reset (development)

```bash
bash reset_server.sh
```

Kills all Gunicorn/Nginx processes, clears logs and Flask sessions.

## Usage

### For participants (Prolific integration)

Direct participants to:

```
http://localhost:8080/?PROLIFIC_PID={pid}&STUDY_ID={study_id}&SESSION_ID={session_id}
```

Or for manual testing:

```
http://localhost:8080/?PARTICIPANT_ID=test_user
```

### Admin endpoints

- `GET /status` — JSON with evaluation statistics (total users, completions, evaluations per subset)

## Database

SQLite databases are stored in `instance/`. Two tables:

- **insect_evaluation** — all evaluation responses (blind ID, morphology scores, failure modes, timing)
- **evaluation_users** — user tracking and subset assignment

The database is auto-created on first run.

## Evaluation Questions

| Stage | Question | Format |
|-------|----------|--------|
| 1 | Species identification (blind) | Family → Genus → Species dropdowns |
| 2 | Morphological fidelity | 1–5 slider per feature (legs, wings, head, abdomen, thorax) |
| 2 | Diagnostic completeness | Single-select (not identifiable / family / genus / species) |
| 2 | Failure modes: Species fidelity | Multi-select checkboxes + "Other" free text |
| 2 | Failure modes: Image quality | Multi-select checkboxes + "Other" free text |
