# Insect Image Evaluation - Finalized Design

## ✅ Your Decisions

1. **Keep all 6 morphological features** (comprehensive evaluation)
2. **Use dropdowns for Family/Genus in Blind ID** (faster, cleaner data)
3. **Failure modes are multi-select** (allow multiple defects)
4. **No optional questions** (removed Real vs Synthetic entirely)
5. **Simplified Question 3** (single dropdown instead of 3 yes/no questions)

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────┐
│  Stage 1: Blind Species ID          [~20 seconds]   │
├─────────────────────────────────────────────────────┤
│  Q1: Species Identification (blind)                 │
│    • Family:  [Dropdown ▼]                          │
│    • Genus:   [Dropdown ▼] (filtered by family)     │
│    • Species: [Text input]                          │
│    [Submit & Reveal] ───────────────────────────────┤
│                                                      │
│  ✓ Ground Truth: Bombus impatiens                   │
├─────────────────────────────────────────────────────┤
│  Stage 2: Detailed Evaluation        [~60 seconds]  │
├─────────────────────────────────────────────────────┤
│  Q2: Morphological Fidelity (6 sliders, 1-5 scale)  │
│    • Legs/Appendages                                │
│    • Wing Venation/Texture                          │
│    • Head/Antennae                                  │
│    • Abdomen Banding                                │
│    • Thorax Coloration                              │
│    • Wing Pit Markings                              │
│                                                      │
│  Q3: Diagnostic Completeness (single dropdown)      │
│    Highest ID level achievable:                     │
│    [None/Family/Genus/Species ▼]                    │
│                                                      │
│  Q4: Failure Modes (multi-select)                   │
│    ☐ Extra/Missing Limbs                            │
│    ☐ Impossible Geometry                            │
│    ☐ Wrong Coloration                               │
│    ☐ Blurry/Artifacts                               │
│    ☐ Background Bleed                               │
│                                                      │
│  [Submit & Next Image] ─────────────────────────────│
└─────────────────────────────────────────────────────┘
```

---

## Time Estimates

| Component | Time | Notes |
|-----------|------|-------|
| **Stage 1** | 20 sec | Dropdowns make this fast |
| **Q2: Morphology** | 35-40 sec | 6 sliders × ~6 sec each |
| **Q3: Diagnostic** | 8-10 sec | Single dropdown selection |
| **Q4: Failure** | 10-15 sec | Multi-select checkboxes |
| **Total/Image** | **~75-85 sec** | **1.2-1.4 minutes** ✅ |

### Study Duration
- **50 images**: 60-70 minutes (recommended)
- **100 images**: 120-140 minutes (too long)

**Prolific Payment**: ~$15-16 for 60-70 min study

---

## Questions Breakdown

### Question 1: Blind Species Identification
**Type:** Dropdowns + Text input
**Purpose:** Test taxonomic accuracy without bias
**Data captured:**
- `blind_id_family` (from dropdown)
- `blind_id_genus` (from dropdown filtered by family)
- `blind_id_species` (free text or "Unknown")

### Question 2: Morphological Fidelity
**Type:** 6 sliders (1-5 scale)
**Purpose:** Evaluate anatomical correctness per feature
**Features:**
1. Legs/Appendages
2. Wing Venation/Texture
3. Head/Antennae
4. Abdomen Banding
5. Thorax Coloration
6. Wing Pit Markings

**Data captured:** 6 integer values (1-5)

### Question 3: Diagnostic Completeness (Simplified)
**Type:** Single dropdown
**Purpose:** Determine highest usable ID level
**Options:**
- "Not identifiable" (image unusable)
- "Family level only"
- "Genus level"
- "Species level" (full ID possible)

**Data captured:** Single string value

### Question 4: Failure Modes
**Type:** Multi-select checkboxes
**Purpose:** Catalog defect types
**Options:**
- Extra/Missing Limbs
- Impossible Geometry
- Wrong Coloration
- Blurry/Artifacts
- Background Bleed

**Data captured:** JSON array (e.g., `["wrong_coloration", "blurry_artifacts"]`)

### ~~Question 5: Real vs Synthetic~~ ❌ REMOVED

---

## Data You Need to Prepare

### 1. Create `assets/insect_images_metadata.json`

```json
{
  "0": {
    "image_path": "generated_insects/bombus_impatiens_001.png",
    "ground_truth": {
      "family": "Apidae",
      "genus": "Bombus",
      "species": "Bombus impatiens",
      "common_name": "Common Eastern Bumble Bee"
    },
    "model": "custom_v2",
    "prompt": "A Bombus impatiens bumblebee on a purple flower"
  },
  "1": {
    "image_path": "generated_insects/vespula_vulgaris_001.png",
    "ground_truth": {
      "family": "Vespidae",
      "genus": "Vespula",
      "species": "Vespula vulgaris",
      "common_name": "Common Wasp"
    },
    "model": "baseline",
    "prompt": "A Vespula vulgaris wasp on a wooden surface"
  }
  // ... more images
}
```

### 2. Populate Taxonomy Options in `constants.py`

```python
TAXONOMY_OPTIONS = {
    "families": [
        "Apidae",
        "Vespidae",
        "Formicidae",
        # ... all families in your dataset
    ],
    "genera_by_family": {
        "Apidae": ["Bombus", "Apis", "Xylocopa"],
        "Vespidae": ["Vespula", "Polistes"],
        # ... all genera organized by family
    }
}
```

### 3. Place Images in `static/` folder

```
static/
├── generated_insects/
│   ├── bombus_impatiens_001.png
│   ├── vespula_vulgaris_001.png
│   └── ...
```

---

## Database Schema (Finalized)

```python
class InsectEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # User tracking
    prolific_pid = db.Column(db.String(255))
    subset_id = db.Column(db.Integer)
    image_index = db.Column(db.Integer)
    absolute_image_index = db.Column(db.Integer)

    # Image metadata
    image_path = db.Column(db.Text)
    ground_truth_family = db.Column(db.String(255))
    ground_truth_genus = db.Column(db.String(255))
    ground_truth_species = db.Column(db.String(255))
    model_type = db.Column(db.String(100))

    # Q1: Blind ID
    blind_id_family = db.Column(db.String(255))
    blind_id_genus = db.Column(db.String(255))
    blind_id_species = db.Column(db.String(255))

    # Q2: Morphology (6 features)
    morph_legs_appendages = db.Column(db.Integer)
    morph_wing_venation_texture = db.Column(db.Integer)
    morph_head_antennae = db.Column(db.Integer)
    morph_abdomen_banding = db.Column(db.Integer)
    morph_thorax_coloration = db.Column(db.Integer)
    morph_wing_pit_markings = db.Column(db.Integer)

    # Q3: Diagnostic (simplified)
    diagnostic_level = db.Column(db.String(50))  # "none", "family", "genus", "species"

    # Q4: Failure modes (JSON)
    failure_modes = db.Column(db.Text)  # ["wrong_coloration", ...]

    # Timing
    time_stage1 = db.Column(db.Float)
    time_stage2 = db.Column(db.Float)
    datetime = db.Column(db.String(255))
```

---

## Next Steps

1. **Prepare your dataset** (JSON + images)
2. **Update `constants.py`** with your taxonomy
3. **Create database models** in `app_human_identity_db.py`
4. **Create `evaluation_form.html`** template
5. **Update Flask routes** for new workflow
6. **Test locally** with sample data
7. **Deploy to production**

---

## Files to Modify

| File | Changes Needed |
|------|----------------|
| `constants.py` | Update all configuration values |
| `util.py` | Change `load_identity_assets()` → `load_insect_evaluation_assets()` |
| `app_human_identity_db.py` | Update database models and routes |
| `templates/evaluation_form.html` | Create new (from plan) |
| `assets/insect_images_metadata.json` | Create new |
| `static/generated_insects/` | Add your images |

---

## Questions?

- Ready to start implementation? I can help you:
  - Create the sample JSON structure
  - Update constants.py
  - Build the database model
  - Create the template

- Want to test the workflow first with dummy data?

Let me know what you'd like to tackle first!
