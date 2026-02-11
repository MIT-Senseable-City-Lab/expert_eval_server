# Bumblebee Evaluation Server - Setup Summary

## What Has Been Completed

### ✓ 1. Dataset Discovery and Analysis
- Located synthetic images: **146 total images** from 3 species
  - Bombus ashtoni: 46 images
  - Bombus sandersoni: 50 images
  - Bombus ternarius: 50 images
- Found reference images for all 3 species (2 refs each)
- Identified generation metadata in `RESULTS_*/synthetic_generation/`

### ✓ 2. Metadata Generation
**File**: [assets/bumblebee_images_metadata.json](assets/bumblebee_images_metadata.json)

Automatically generated metadata for all 146 images including:
- Image paths (relative to `static/`)
- Ground truth taxonomy (Family, Genus, Species)
- Generation metadata (angle, gender, environmental context)
- Reference image mappings
- Model information

**Generation Script**: [scripts/generate_bumblebee_metadata.py](scripts/generate_bumblebee_metadata.py)

### ✓ 3. Configuration Files Updated
**File**: [constants_BUMBLEBEE.py](constants_BUMBLEBEE.py)

Updated with actual dataset parameters:
- `TOTAL_IMAGES = 146` (accurate count)
- `SPECIES_WITH_SYNTHETIC` list (3 species)
- Asset path configurations
- Complete list of all 16 Bombus species (for future expansion)
- Reference image settings (`SHOW_REFERENCE_IMAGES = True`)
- All evaluation questions configured

### ✓ 4. Data Preparation Tools
**Setup Script**: [scripts/setup_bumblebee_data.sh](scripts/setup_bumblebee_data.sh)
- Automated copying of synthetic images
- Automated copying of reference images
- Built-in verification checks
- Ready to run with one command

**Guide**: [DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md)
- Complete step-by-step instructions
- Verification checklists
- Directory structure documentation
- Future expansion guidance

### ✓ 5. Design Documentation
**Files Created**:
- [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) - Quick reference for finalized design
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Complete technical specification
- [DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md) - Data setup instructions

---

## What You Need to Do Next

### Step 1: Copy Images to Eval Server (5 minutes)

Run the automated setup script:

```bash
cd /Users/mingyang/Desktop/Thesis/BioGen/expert_eval_pipeline/eval_server
./scripts/setup_bumblebee_data.sh
```

This will:
- Create `static/bumblebees/` and `static/references/` directories
- Copy all 146 synthetic images
- Copy all reference images
- Verify the setup

**Expected Output**:
```
Bombus_ashtoni: 46 images + 2 references
Bombus_sandersoni: 50 images + 2 references
Bombus_ternarius: 50 images + 2 references
Metadata entries: 146
```

### Step 2: Implement Database Models (30 minutes)

Update [app_human_identity_db.py](app_human_identity_db.py) with the new `InsectEvaluation` model.

**Reference**: See Section 3 in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#3-database-models)

Key changes:
- Replace old `Comparison` model with `InsectEvaluation`
- Add all 20+ fields for multi-question evaluation
- Update database initialization

### Step 3: Create Evaluation Template (1-2 hours)

Create [templates/evaluation_form.html](templates/evaluation_form.html) with the two-stage workflow.

**Reference**: See Section 4 in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#4-evaluation-template)

Template includes:
- Stage 1: Blind species ID with dropdowns
- Stage 2: 6 morphology sliders + diagnostic dropdown + failure modes
- Reference image display (after Stage 1 reveal)
- Progress tracking
- Modal image viewer

### Step 4: Update Flask Routes (1-2 hours)

Modify Flask application routes in [app_human_identity_db.py](app_human_identity_db.py).

**Reference**: See Section 5 in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md#5-flask-routes)

Key routes to update:
- `/` - Landing page with Prolific integration
- `/evaluate` - Main evaluation interface
- `/submit_stage1` - AJAX endpoint for blind ID
- `/submit_evaluation` - Final submission for Stage 2
- `/complete` - Completion page with Prolific code

### Step 5: Test Locally (30 minutes)

```bash
# Initialize database
python3 app_human_identity_db.py

# Test in browser
# Visit: http://localhost:5000
```

Test checklist:
- [ ] Prolific ID capture works
- [ ] Images load correctly
- [ ] Stage 1 submission reveals ground truth
- [ ] Reference images display
- [ ] Stage 2 form validation works
- [ ] Data saves to database correctly
- [ ] Progress tracking accurate
- [ ] Completion code displays

### Step 6: Verify Database Schema (10 minutes)

After first test run:

```bash
# Check database was created
ls -lh *.db

# Inspect schema
sqlite3 bumblebee_evaluation_debug.db ".schema"

# Check sample data
sqlite3 bumblebee_evaluation_debug.db "SELECT * FROM insect_evaluation LIMIT 1;"
```

---

## File Structure Overview

```
eval_server/
├── app_human_identity_db.py          [TO UPDATE] Flask application
├── constants_BUMBLEBEE.py            [✓ READY] Configuration
├── util.py                           [TO UPDATE] Data loading utilities
│
├── templates/
│   ├── index_identity.html           [REFERENCE] Original template
│   └── evaluation_form.html          [TO CREATE] New template
│
├── static/                           [RUN SETUP SCRIPT]
│   ├── bumblebees/                   ← 146 synthetic images
│   │   ├── Bombus_ashtoni/
│   │   ├── Bombus_sandersoni/
│   │   └── Bombus_ternarius_Say/
│   └── references/                   ← 6 reference images
│       ├── Bombus_ashtoni/
│       ├── Bombus_sandersoni/
│       └── Bombus_ternarius_Say/
│
├── assets/
│   └── bumblebee_images_metadata.json [✓ GENERATED] 146 entries
│
├── scripts/
│   ├── setup_bumblebee_data.sh       [✓ READY] Data setup automation
│   └── generate_bumblebee_metadata.py [✓ READY] Metadata generator
│
└── docs/
    ├── DESIGN_SUMMARY.md              [✓ COMPLETE] Design decisions
    ├── IMPLEMENTATION_PLAN.md         [✓ COMPLETE] Technical spec
    ├── DATA_PREPARATION_GUIDE.md      [✓ COMPLETE] Setup guide
    └── SETUP_SUMMARY.md               [✓ YOU ARE HERE]
```

---

## Quick Start Command Sequence

```bash
# 1. Copy images
cd /Users/mingyang/Desktop/Thesis/BioGen/expert_eval_pipeline/eval_server
./scripts/setup_bumblebee_data.sh

# 2. Verify metadata
python3 -c "import json; print(f'Metadata entries: {len(json.load(open(\"assets/bumblebee_images_metadata.json\")))}')"

# 3. Review implementation plan
cat IMPLEMENTATION_PLAN.md

# 4. Update database models (manual coding)
# 5. Create evaluation template (manual coding)
# 6. Update Flask routes (manual coding)

# 7. Test locally
python3 app_human_identity_db.py
# Visit http://localhost:5000 in browser
```

---

## Dataset Statistics

### Current Dataset
- **Total images**: 146
- **Species covered**: 3 (Bombus ashtoni, sandersoni, ternarius)
- **Images per species**: 46-50
- **Reference images**: 2 per species
- **Image variations**: 3 angles × 2 genders = 6 variants per individual

### Filename Convention
```
synthetic_{number}_{gender}_{angle}.png

Examples:
- synthetic_001_female_dorsal.png
- synthetic_012_male_lateral.png
- synthetic_023_female_frontal.png
```

### Metadata Fields Per Image
- Ground truth taxonomy (family, genus, species)
- Generation parameters (angle, gender, environmental context)
- Reference image paths
- Model version
- Timestamp

---

## Evaluation Study Parameters

Based on 146 images:

### Recommended Configuration
- **Images per participant**: 50
- **Study duration**: 60-70 minutes
- **Overlapping subsets**: 3 participants per subset
- **Total subsets**: 3
- **Prolific payment**: $15-16 per participant

### Time Budget Per Image
- Stage 1 (Blind ID): ~20 seconds
- Stage 2 (Detailed eval): ~55-65 seconds
- **Total**: ~75-85 seconds (1.2-1.4 minutes)

---

## Questions or Issues?

### Common Questions:

**Q: Can I add more species later?**
A: Yes! Generate new synthetic images, re-run `generate_bumblebee_metadata.py`, and update `TOTAL_IMAGES` in constants.

**Q: Can I change the number of images per participant?**
A: Yes, update `IMAGES_PER_USER` in [constants_BUMBLEBEE.py](constants_BUMBLEBEE.py).

**Q: How do I regenerate metadata if I add images?**
A: Just run `python3 scripts/generate_bumblebee_metadata.py` again. It automatically detects all synthetic images.

**Q: What if reference images are missing for a species?**
A: The evaluation will still work, but no references will be shown after Stage 1. Add references to `SYNTHETIC_BUMBLEBEES/references/{species}/` and regenerate metadata.

---

## Next Implementation Session

**Recommended order**:

1. **Today/Now**: Run `setup_bumblebee_data.sh` (5 min)
2. **Next session**: Database models (30 min)
3. **Next session**: Evaluation template (1-2 hours)
4. **Next session**: Flask routes (1-2 hours)
5. **Next session**: Local testing (30 min)

**Total estimated time**: 3-5 hours of focused development

---

## Resources

- **Original system reference**: [app_human_identity_db.py](app_human_identity_db.py) and [templates/index_identity.html](templates/index_identity.html)
- **Complete implementation spec**: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **Design decisions**: [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)
- **Data setup guide**: [DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md)

---

**Status**: Data preparation complete ✓ | Ready for implementation phase
