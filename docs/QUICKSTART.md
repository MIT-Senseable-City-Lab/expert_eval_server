# Bumblebee Evaluation Server - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Copy Images (2 minutes)

```bash
cd /Users/mingyang/Desktop/Thesis/BioGen/expert_eval_pipeline/eval_server
./scripts/setup_bumblebee_data.sh
```

This will:
- Copy 146 synthetic images to `static/bumblebees/`
- Copy 6 reference images to `static/references/`
- Verify the setup

**Expected output:**
```
Bombus_ashtoni: 46 images + 2 references
Bombus_sandersoni: 50 images + 2 references
Bombus_ternarius: 50 images + 2 references
✓ Data setup complete!
```

### Step 2: Run the Server (1 minute)

```bash
python3 app_bumblebee_eval.py
```

**Expected output:**
```
============================================================
BUMBLEBEE EVALUATION SERVER
============================================================
Database: sqlite:///bumblebee_evaluation_prod.db
Total images: 146
Subsets: 3
Images per user: 50
Max users per subset: 3
============================================================

✓ Loaded 146 images from assets/bumblebee_images_metadata.json
✓ Created 3 subsets with up to 50 images each
✓ Database initialized
 * Running on http://0.0.0.0:5000
```

### Step 3: Test the Workflow (5 minutes)

1. **Open in browser:**
   ```
   http://localhost:5000/?PROLIFIC_PID=test123&STUDY_ID=test&SESSION_ID=1
   ```

2. **Test the two-stage workflow:**
   - **Stage 1**: Select family/genus, enter species → Submit
   - **Ground truth reveals** with reference images
   - **Stage 2**: Rate 6 morphology features, select diagnostic level, check failure modes
   - Submit and move to next image

3. **Verify database:**
   ```bash
   sqlite3 bumblebee_evaluation_prod.db "SELECT COUNT(*) FROM insect_evaluation;"
   ```

---

## ✅ Files Created

### Application Files
- ✅ `app_bumblebee_eval.py` - Flask application with two-stage evaluation
- ✅ `constants_BUMBLEBEE.py` - Configuration (146 images, 3 species)

### Templates (all with modern, responsive design)
- ✅ `templates/start_evaluation.html` - Welcome/instructions page
- ✅ `templates/evaluation_form.html` - Main two-stage evaluation interface
- ✅ `templates/complete_evaluation.html` - Completion with Prolific code
- ✅ `templates/already_completed.html` - Already completed message

### Data & Scripts
- ✅ `assets/bumblebee_images_metadata.json` - 146 image metadata entries
- ✅ `scripts/generate_bumblebee_metadata.py` - Metadata generator
- ✅ `scripts/setup_bumblebee_data.sh` - Automated data setup

### Documentation
- ✅ `README_BUMBLEBEE.md` - Project overview
- ✅ `SETUP_SUMMARY.md` - Complete setup guide
- ✅ `DATA_PREPARATION_GUIDE.md` - Detailed data prep instructions
- ✅ `IMPLEMENTATION_PLAN.md` - Technical specification
- ✅ `DESIGN_SUMMARY.md` - Design decisions
- ✅ `QUICKSTART.md` - This file!

---

## 🎯 What's Implemented

### Two-Stage Workflow
✅ **Stage 1: Blind Species ID** (~20 seconds)
- Family dropdown (dynamically filtered)
- Genus dropdown (filtered by selected family)
- Species text input
- AJAX submission (no page reload)

✅ **Stage 2: Detailed Evaluation** (~60 seconds)
After ground truth reveal:
- 6 morphological feature sliders (1-5 scale)
- Diagnostic completeness dropdown
- Failure modes multi-select checkboxes
- Reference images displayed (if available)

### Database
✅ **InsectEvaluation model** with 25+ fields:
- User tracking (Prolific PID, subset assignment)
- Image metadata (path, ground truth, generation params)
- Stage 1 blind ID data
- Stage 2 detailed evaluation data
- Timing for both stages

✅ **EvaluationUsers model** for tracking participants

### User Experience
✅ Progressive disclosure (Stage 1 hidden after submission)
✅ Modal fullscreen image viewer
✅ Real-time slider value updates
✅ Form validation
✅ Progress tracking
✅ Responsive design (works on mobile/desktop)
✅ Professional styling with smooth transitions

### Prolific Integration
✅ URL parameter capture (PROLIFIC_PID, STUDY_ID, SESSION_ID)
✅ Automatic user assignment to subsets
✅ Round-robin distribution with max users per subset
✅ Completion code display
✅ Already-completed detection

---

## 📊 Current Dataset

| Metric | Value |
|--------|-------|
| **Total Images** | 146 |
| **Species** | 3 (Bombus ashtoni, sandersoni, ternarius) |
| **Images per species** | 46-50 |
| **Reference images** | 2 per species |
| **Image variations** | 3 angles × 2 genders |

---

## 🔧 Configuration

Edit `constants_BUMBLEBEE.py` to adjust:

```python
IMAGES_PER_USER = 50           # Images per participant
TOTAL_IMAGES = 146             # Total in dataset
MAX_USERS_PER_SUBSET = 3       # Max participants per subset
SHOW_REFERENCE_IMAGES = True   # Show refs after Stage 1
MAX_REFERENCE_IMAGES = 5       # Max refs to display
```

---

## 🐛 Troubleshooting

### Images not loading
```bash
# Check images were copied:
ls -l static/bumblebees/*/synthetic*.png | wc -l
# Should show 146

# Check references:
ls -l static/references/*/*.jpg static/references/*/*.jpeg 2>/dev/null | wc -l
# Should show 6
```

### Metadata not found
```bash
# Regenerate metadata:
python3 scripts/generate_bumblebee_metadata.py

# Verify:
python3 -c "import json; print(len(json.load(open('assets/bumblebee_images_metadata.json'))))"
# Should print: 146
```

### Database errors
```bash
# Reset database:
rm bumblebee_evaluation_prod.db
python3 app_bumblebee_eval.py  # Will recreate
```

### Port 5000 already in use
```bash
# Change port in app_bumblebee_eval.py (last line):
app.run(debug=True, host='0.0.0.0', port=5001)
```

---

## 📈 Monitoring

### Check system status:
```bash
curl http://localhost:5000/status | python3 -m json.tool
```

**Example output:**
```json
{
  "total_images": 146,
  "num_subsets": 3,
  "images_per_user": 50,
  "total_users": 5,
  "completed_users": 2,
  "in_progress_users": 3,
  "total_evaluations": 97,
  "users_per_subset": {
    "0": 2,
    "1": 2,
    "2": 1
  }
}
```

### Query database:
```bash
# Count evaluations:
sqlite3 bumblebee_evaluation_prod.db \
  "SELECT COUNT(*) FROM insect_evaluation;"

# Check latest submissions:
sqlite3 bumblebee_evaluation_prod.db \
  "SELECT prolific_pid, image_index, datetime FROM insect_evaluation ORDER BY id DESC LIMIT 5;"

# Get average morphology scores:
sqlite3 bumblebee_evaluation_prod.db \
  "SELECT AVG(morph_legs_appendages), AVG(morph_wing_venation_texture) FROM insect_evaluation;"
```

---

## 🚢 Deployment

### For Production:

1. **Update database setting:**
   ```python
   # In constants_BUMBLEBEE.py:
   DB_PROD = "sqlite:///bumblebee_evaluation_prod.db"
   ```

2. **Disable debug mode:**
   ```python
   # In app_bumblebee_eval.py (last line):
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

3. **Use production server:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app_bumblebee_eval:app
   ```

---

## 📞 Need Help?

- **Setup issues**: See [DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md)
- **Technical details**: See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **Design decisions**: See [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)
- **Complete overview**: See [SETUP_SUMMARY.md](SETUP_SUMMARY.md)

---

**Ready to go!** 🎉

Run `./scripts/setup_bumblebee_data.sh` and `python3 app_bumblebee_eval.py` to start evaluating.
