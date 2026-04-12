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
├── nginx.conf              # Nginx reverse proxy config (optional)
├── deploy_server.sh        # Start/stop/restart/switch-mode server
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
├── logs/                   # Gunicorn logs (auto-created)
└── flask_session/          # Server-side session files (auto-created)
```

## Setup

### Prerequisites

- Python 3.10+
- Nginx is optional (Gunicorn alone is sufficient for single-user evaluation)

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
MODE = "calibration"  # 10 images, calibration DB (for practice)
MODE = "full"         # 150 images, production DB (real evaluation)
```

Or use the CLI to switch (see below).

## Running the Server

### Start / stop

```bash
bash deploy_server.sh start       # Start Gunicorn (skips Nginx if not installed)
bash deploy_server.sh stop        # Stop server
bash deploy_server.sh restart     # Restart server
bash deploy_server.sh status      # Show mode, running status
bash deploy_server.sh switch-mode # Toggle calibration <-> full (clears sessions, restarts)
```

The app runs on **http://localhost:5050** (Gunicorn direct).
If Nginx is installed, it also proxies on port 8080.

### Remote access (SSH tunnel)

If the server runs on a remote machine (e.g. MIT cluster), set up an SSH tunnel from your laptop:

```bash
ssh -L 5050:localhost:5050 msun14@login007.mit.edu
```

Then open `http://localhost:5050/?PARTICIPANT_ID=your_name` in your laptop browser.

### Switching modes

```bash
# Start in calibration mode (10 images, practice)
bash deploy_server.sh start

# When ready for real evaluation:
bash deploy_server.sh switch-mode   # switches to full (150 images)
```

Each mode has its own database — switching does not affect the other mode's data.
Sessions are cleared automatically on switch (required because session stores progress).

### Hard reset

```bash
bash reset_server.sh
```

Kills all Gunicorn processes, clears logs and Flask sessions. Does **not** delete databases.

### Development (Flask dev server)

```bash
source venv/bin/activate
python app.py
# Runs on http://localhost:5050
```

## Usage

### URL Format

```
http://<host>:<port>/?PARTICIPANT_ID=<id>&STUDY_ID=<study>&SESSION_ID=<session>
```

| Parameter        | Required | Default | Description                            |
| ---------------- | -------- | ------- | -------------------------------------- |
| `PARTICIPANT_ID` | Yes      | `0`     | Unique identifier for the participant  |
| `STUDY_ID`       | No       | `0`     | Study identifier (useful for grouping) |
| `SESSION_ID`     | No       | `0`     | Session identifier                     |

**Examples:**

```
http://localhost:5050/?PARTICIPANT_ID=expert_1
http://localhost:5050/?PARTICIPANT_ID=expert_1&STUDY_ID=pilot&SESSION_ID=1
```

Different `PARTICIPANT_ID` values create separate user entries in the same database. Use a new ID to start fresh without clearing the DB.

### Public Access with ngrok

Since the server runs on `localhost`, remote participants cannot access it directly. Use [ngrok](https://ngrok.com/) to create a public tunnel:

1. Install ngrok:

   ```bash
   brew install ngrok    # macOS
   ```

2. Start the tunnel (while the server is running):

   ```bash
   ngrok http 8080       # if using Nginx
   ngrok http 5050       # if using Gunicorn directly
   ```

3. ngrok will output a public URL like:

   ```
   Forwarding  https://abc123.ngrok-free.app -> http://localhost:8080
   ```

4. Send the public URL to participants:
   ```
   https://abc123.ngrok-free.app/?PARTICIPANT_ID=expert_1&STUDY_ID=pilot&SESSION_ID=1
   ```

> **Note:** The free ngrok tier generates a new URL each time. For a stable URL, use a paid plan or consider deploying to a cloud server.

### Admin endpoints

- `GET /status` — JSON with evaluation statistics (mode, users, completions)
- `GET /export` — Download all evaluation results as CSV

## Database

SQLite databases are stored in `instance/`:

| Mode        | Database file                         | Purpose                           |
| ----------- | ------------------------------------- | --------------------------------- |
| calibration | `bumblebee_evaluation_calibration.db` | Practice/testing (safe to delete) |
| full        | `bumblebee_evaluation_full.db`        | Real evaluation data (keep this)  |

Two tables:

- **insect_evaluation** — all evaluation responses (blind ID, morphology scores, caste, failure modes, timing)
- **evaluation_users** — user tracking and subset assignment

## Evaluation Questions

| Stage | Question                        | Format                                                      |
| ----- | ------------------------------- | ----------------------------------------------------------- |
| 1     | Species identification (blind)  | Family → Genus → Species dropdowns (includes "No match")    |
| 2     | Morphological fidelity          | 1–5 slider per feature (legs, wings, head, abdomen, thorax) |
| 2     | Diagnostic completeness         | Single-select (not identifiable / family / genus / species) |
| 2     | Caste identification (blind)    | Dropdown (worker / queen / male / female / uncertain)       |
| 2     | Failure modes: Species fidelity | Multi-select checkboxes + "Other" free text                 |
| 2     | Failure modes: Image quality    | Multi-select checkboxes + "Other" free text                 |
