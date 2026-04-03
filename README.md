# Bumblebee Synthetic Image Evaluation Server

Expert evaluation server for AI-generated bumblebee images. Experts evaluate synthetic images through a two-stage workflow:

1. **Stage 1 — Blind Identification**: Expert identifies the species from the image alone (Family → Genus → Species dropdowns, includes "No match" option)
2. **Stage 2 — Detailed Evaluation**: After revealing the target species and reference images, expert rates morphological fidelity, diagnostic completeness, caste identification, and failure modes

## Species

Three target species from the expert validation set (150 images, 50 per species):

- **Bombus ashtoni** — Ashton Cuckoo Bumble Bee
- **Bombus sandersoni** — Sanderson's Bumble Bee
- **Bombus flavidus** — Fernald's Cuckoo Bumble Bee

## Project Structure

```
expert_eval_server/
├── app.py                  # Flask application (routes, DB models, logic)
├── constants.py            # Configuration (mode, species, taxonomy, evaluation options)
├── wsgi.py                 # Gunicorn entry point
├── requirements.txt        # Python dependencies
├── gunicorn_config.py      # Gunicorn settings (workers, ports, logging)
├── nginx.conf              # Nginx reverse proxy config
├── deploy_server.sh        # Start/stop/restart server
├── reset_server.sh         # Hard reset (kill processes, clear sessions)
├── templates/
│   ├── start_evaluation.html       # Landing page
│   ├── evaluation_form.html        # Two-stage evaluation interface
│   ├── complete_evaluation.html    # Completion page
│   └── already_completed.html      # Shown to returning users
├── assets/
│   ├── bumblebee_images_metadata.json    # Image metadata (auto-generated)
│   └── expert_validation_manifest.json   # LLM judge manifest (source of truth)
├── scripts/
│   └── generate_expert_metadata.py  # Generate metadata from local images + manifest
├── static/
│   ├── bumblebees/         # 150 synthetic images (50 per species)
│   └── references/         # Reference images for each species
├── instance/               # SQLite databases (auto-created)
├── logs/                   # Gunicorn/Nginx logs (auto-created)
└── flask_session/          # Server-side session files (auto-created)
```

## Setup

### Prerequisites

- Python 3.10+
- Nginx (optional, for production deployment)

### 1. Create virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Image data

Images are already bundled in `static/`:

- `static/bumblebees/{species}/` — 150 synthetic images (from expert validation set)
- `static/references/{species}/` — Reference images for each species

### 3. Generate metadata (if needed)

```bash
python scripts/generate_expert_metadata.py
```

This scans `static/bumblebees/` and reads `assets/expert_validation_manifest.json` to produce `assets/bumblebee_images_metadata.json`. All paths are local — no external dependencies.

### 4. Configure evaluation mode

Edit `constants.py`:

```python
MODE = "calibration"  # 10 images, calibration DB
MODE = "full"         # 150 images, production DB
```

Other settings:
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

### Hard reset

```bash
bash reset_server.sh
```

Kills all Gunicorn/Nginx processes, clears logs and Flask sessions.

## Usage

### For participants

```
http://localhost:8080/?PARTICIPANT_ID=expert_1
```

Or with Prolific integration:

```
http://localhost:8080/?PROLIFIC_PID={pid}&STUDY_ID={study_id}&SESSION_ID={session_id}
```

### Admin endpoints

- `GET /status` — JSON with evaluation statistics

## Database

SQLite databases are stored in `instance/`:

| Mode | Database file |
|------|--------------|
| calibration | `bumblebee_evaluation_calibration.db` |
| full | `bumblebee_evaluation_full.db` |

Two tables:

- **insect_evaluation** — all evaluation responses
- **evaluation_users** — user tracking and subset assignment

## Evaluation Questions

| Stage | Question | Format |
|-------|----------|--------|
| 1 | Species identification (blind) | Family → Genus → Species dropdowns (includes "No match") |
| 2 | Morphological fidelity | 1–5 slider per feature (legs, wings, head, abdomen, thorax) |
| 2 | Diagnostic completeness | Single-select (not identifiable / family / genus / species) |
| 2 | Caste identification (blind) | Dropdown (worker / queen / male / female / uncertain) |
| 2 | Failure modes: Species fidelity | Multi-select checkboxes + "Other" free text |
| 2 | Failure modes: Image quality | Multi-select checkboxes + "Other" free text |

## LLM Judge Metadata

Each image carries hidden LLM judge metadata (not shown to expert) for downstream disagreement analysis:

- `tier` — strict_pass / borderline / soft_fail / hard_fail
- `llm_morph_mean` — LLM judge's mean morphological score
- `caste_ground_truth` — intended caste from generation
- `llm_matches_target` — whether LLM judge identified correct species
