# Implementation Plan: Insect Image Expert Evaluation System

## Overview
Transform the current pair-comparison server into a multi-stage expert evaluation system for AI-generated insect images.

---

## Key Differences from Current System

| Current System | New System |
|----------------|------------|
| Pair comparison (A vs B) | Single image evaluation |
| Simple binary choice | Multi-question, multi-stage workflow |
| One question per pair | 5 different question types |
| No staged reveal | Blind ID → Species reveal → Detailed rating |
| ~2-3 seconds per annotation | ~2-3 minutes per image (expert evaluation) |

---

## Data Structure Changes

### 1. Input Data Format (JSON in `assets/`)

**Current:** `instance_pairs_round1_baseline_vs_custom.json`
```json
{
  "0": ["path/to/image1.png"],
  "1": ["path/to/image2.png"]
}
```

**New:** `insect_images_metadata.json`
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
    "prompt": "A Bombus impatiens bumblebee on a purple flower",
    "metadata": {
      "diagnostic_features": [
        "Yellow and black banding pattern",
        "Fuzzy thorax",
        "Transparent wings with specific venation"
      ]
    }
  }
}
```

**No longer needed:**
- `pairs_round1_baseline_vs_custom.json` (no pairs)
- `reference_images.json` (reference is the ground truth species)

---

## Database Schema Changes

### Current: `IdentityJudgement` model
```python
class IdentityJudgement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prolific_pid = db.Column(db.String(255))
    pair_index = db.Column(db.Integer)
    decision = db.Column(db.String(50))  # "Left" or "Right"
    # ... other fields
```

### New: `InsectEvaluation` model (FINALIZED)

```python
class InsectEvaluation(db.Model):
    """Database model for expert insect image evaluations"""
    id = db.Column(db.Integer, primary_key=True)

    # User tracking (Prolific integration)
    prolific_pid = db.Column(db.String(255), nullable=False)
    study_id = db.Column(db.String(255))
    session_id = db.Column(db.String(255))
    subset_id = db.Column(db.Integer, nullable=False)
    image_index = db.Column(db.Integer)  # Index within user's subset
    absolute_image_index = db.Column(db.Integer)  # Global index in dataset

    # Image metadata
    image_path = db.Column(db.Text, nullable=False)
    ground_truth_family = db.Column(db.String(255))
    ground_truth_genus = db.Column(db.String(255))
    ground_truth_species = db.Column(db.String(255))
    model_type = db.Column(db.String(100))  # e.g., "custom_v2", "baseline"

    # STAGE 1: Blind Species ID (with dropdowns)
    blind_id_family = db.Column(db.String(255))      # From dropdown
    blind_id_genus = db.Column(db.String(255))       # From dropdown (filtered by family)
    blind_id_species = db.Column(db.String(255))     # Free text input

    # STAGE 2 - Question 2: Morphological Fidelity (ALL 6 features, 1-5 scale)
    morph_legs_appendages = db.Column(db.Integer)        # 1-5
    morph_wing_venation_texture = db.Column(db.Integer)  # 1-5
    morph_head_antennae = db.Column(db.Integer)          # 1-5
    morph_abdomen_banding = db.Column(db.Integer)        # 1-5
    morph_thorax_coloration = db.Column(db.Integer)      # 1-5
    morph_wing_pit_markings = db.Column(db.Integer)      # 1-5

    # STAGE 2 - Question 3: Diagnostic Completeness (SIMPLIFIED - single value)
    diagnostic_level = db.Column(db.String(50))  # "none", "family", "genus", or "species"

    # STAGE 2 - Question 4: Failure Modes (Multi-select, stored as JSON array)
    failure_modes = db.Column(db.Text)  # JSON: ["extra_missing_limbs", "wrong_coloration"]

    # Question 5: REMOVED (no Real vs Synthetic question)

    # Timing and metadata
    time_stage1 = db.Column(db.Float)  # Seconds spent on blind ID
    time_stage2 = db.Column(db.Float)  # Seconds on detailed evaluation
    datetime = db.Column(db.String(255))  # Timestamp of submission
```

**Note:** The old `IdentityUsers` model can be reused (just rename if needed):
```python
class EvaluationUsers(db.Model):
    """Track which users are assigned to which image subsets"""
    prolific_pid = db.Column(db.String(255), primary_key=True)
    study_id = db.Column(db.String(255))
    session_id = db.Column(db.String(255))
    subset_id = db.Column(db.Integer)
    subset_number = db.Column(db.Integer)
    done = db.Column(db.Integer)  # 0 = in progress, 1 = completed
```

---

## Workflow Changes

### Current Flow:
```
Start → Pair 1 → Select Left/Right → Pair 2 → ... → Complete
```

### New Flow (Per Image) - **FINALIZED DESIGN**:

**Single-page, two-stage workflow:**

```
┌─────────────────────────────────────────────────────┐
│  [Image Display - Always Visible]                   │
├─────────────────────────────────────────────────────┤
│  STAGE 1: Blind Species ID          [~15-20 sec]    │
│  Family:  [Dropdown ▼]                              │
│  Genus:   [Dropdown ▼] (filtered by family)         │
│  Species: [Text input]                              │
│  [Submit & Reveal Ground Truth] ────────────────────┤
├─────────────────────────────────────────────────────┤
│  ✓ Ground Truth: Bombus impatiens   (appears after) │
├─────────────────────────────────────────────────────┤
│  STAGE 2: Detailed Evaluation       [~60-70 sec]    │
│                                                      │
│  Q2: Morphological Fidelity (6 features, 1-5 scale) │
│    • Legs/Appendages         [slider 1-5]           │
│    • Wing Venation/Texture   [slider 1-5]           │
│    • Head/Antennae           [slider 1-5]           │
│    • Abdomen Banding         [slider 1-5]           │
│    • Thorax Coloration       [slider 1-5]           │
│    • Wing Pit Markings       [slider 1-5]           │
│                                                      │
│  Q3: Diagnostic Completeness (single dropdown)      │
│    Highest ID level: [None/Family/Genus/Species ▼]  │
│                                                      │
│  Q4: Failure Modes (multi-select checkboxes)        │
│    ☐ Extra/Missing Limbs                            │
│    ☐ Impossible Geometry                            │
│    ☐ Wrong Coloration                               │
│    ☐ Blurry/Artifacts                               │
│    ☐ Background Bleed                               │
│                                                      │
│  [Submit & Next Image] ─────────────────────────────┤
└─────────────────────────────────────────────────────┘

Total Time: ~75-90 seconds per image (1.25-1.5 min)
For 50 images: ~60-75 minutes total
```

**Key Design Decisions:**
- ✅ Use dropdowns for Family/Genus (faster, standardized data)
- ✅ Keep all 6 morphological features (comprehensive evaluation)
- ✅ Simplified diagnostic completeness (1 dropdown vs 3 yes/no)
- ✅ Multi-select failure modes (allow multiple defects)
- ✅ No optional questions (removed Real vs Synthetic)
- ✅ Single-page progressive reveal (better UX)

---

## File Modifications Required

### 1. **constants.py** - Update configuration

```python
# Evaluation configuration
IMAGES_PER_USER = 50  # How many images each expert evaluates
TOTAL_IMAGES = 500  # Total dataset size
MAX_USERS_PER_SUBSET = 3  # Maximum experts per subset

# Database configuration
DB_DEBUG = "sqlite:///insect_evaluation_debug.db"
DB_PROD = "sqlite:///insect_evaluation_prod.db"

# Workflow configuration
USE_SINGLE_PAGE_WORKFLOW = True  # Two-stage single-page design
USE_TAXONOMY_DROPDOWNS = True  # Dropdowns for Family/Genus (not free text)

# Question 1: Blind Species ID with Dropdowns
# NOTE: You'll populate these from your actual dataset
TAXONOMY_OPTIONS = {
    "families": [
        "Apidae",      # Bees
        "Vespidae",    # Wasps
        "Formicidae",  # Ants
        "Coccinellidae",  # Ladybugs
        "Papilionidae",   # Swallowtail butterflies
        # Add all families in your dataset
    ],
    "genera_by_family": {
        "Apidae": ["Bombus", "Apis", "Xylocopa", "Megachile"],
        "Vespidae": ["Vespula", "Polistes", "Dolichovespula"],
        "Formicidae": ["Camponotus", "Formica", "Lasius"],
        # Add genus mappings for each family
    }
}

# Question 2: Morphological Fidelity (ALL 6 FEATURES)
MORPHOLOGICAL_FEATURES = [
    ("legs_appendages", "Legs/Appendages"),
    ("wing_venation_texture", "Wing Venation/Texture"),
    ("head_antennae", "Head/Antennae"),
    ("abdomen_banding", "Abdomen Banding"),
    ("thorax_coloration", "Thorax Coloration"),
    ("wing_pit_markings", "Wing Pit Markings")
]

# Question 3: Diagnostic Completeness (SIMPLIFIED - Single Dropdown)
DIAGNOSTIC_LEVELS = [
    ("none", "Not identifiable"),
    ("family", "Family level only"),
    ("genus", "Genus level"),
    ("species", "Species level (full identification)")
]

# Question 4: Failure Modes (MULTI-SELECT)
FAILURE_MODE_OPTIONS = [
    ("extra_missing_limbs", "Extra/Missing Limbs"),
    ("impossible_geometry", "Impossible Geometry (unnatural poses)"),
    ("wrong_coloration", "Wrong Coloration"),
    ("blurry_artifacts", "Blurry/Artifacts"),
    ("background_bleed", "Background Bleed")
]

# Question 5: REMOVED (no optional questions)
# Real vs Synthetic question removed per final design

# Completion
COMPLETION_CODE = "INSECT_EVAL_2025"  # Prolific completion code

# Remove old pair-comparison constants
# TOTAL_PAIRS = 600  ← DELETE
# PAIRS_PER_USER = 100  ← DELETE
# RESPONSE_OPTIONS = ["Left", "Right"]  ← DELETE
# SHOW_REFERENCE_IMAGES = True  ← DELETE
```

### 2. **util.py** - Update data loading

**Current:** `load_identity_assets()`
**New:** `load_insect_evaluation_assets()`

```python
def load_insect_evaluation_assets():
    """Load insect image metadata for expert evaluation"""

    # Load main dataset
    with open("assets/insect_images_metadata.json", 'r') as f:
        images_data = json.load(f)

    # Convert to list format with index tracking
    images = []
    for idx, (img_id, metadata) in enumerate(images_data.items()):
        image_data = {
            'absolute_index': idx,
            'image_id': img_id,
            'image_path': metadata['image_path'],
            'ground_truth': metadata['ground_truth'],
            'model': metadata.get('model', 'unknown'),
            'prompt': metadata.get('prompt', ''),
            'diagnostic_features': metadata.get('metadata', {}).get('diagnostic_features', [])
        }
        images.append(image_data)

    return images
```

**Update:** `create_subsets()` - Simpler now (no pairs, no sentinels)
```python
def create_subsets(images, sentinels=None):
    """Create subsets of images for different users"""
    subsets = {}
    images_per_subset = IMAGES_PER_USER

    num_subsets = (len(images) + images_per_subset - 1) // images_per_subset

    for subset_id in range(num_subsets):
        start_idx = subset_id * images_per_subset
        end_idx = min(start_idx + images_per_subset, len(images))
        subsets[subset_id] = images[start_idx:end_idx]

    return subsets
```

### 3. **app_human_identity_db.py** - Major refactor

**Key Changes:**

#### Route: `/index` → Display current image + evaluation form
```python
@app.route('/index')
def index():
    if 'current_image_index' not in session:
        session['current_image_index'] = 0
        session['stage1_submitted'] = False  # Track stage completion

    subset_id = session['subset_id']
    current_index = session['current_image_index']

    # Check completion
    if current_index >= len(subsets[subset_id]):
        mark_user_complete()
        return redirect(url_for('close'))

    current_image_data = subsets[subset_id][current_index]
    session['current_image_data'] = current_image_data

    return render_template('evaluation_form.html',
                         image_data=current_image_data,
                         current_index=current_index,
                         total=len(subsets[subset_id]),
                         stage1_complete=session.get('stage1_submitted', False),
                         morphological_features=MORPHOLOGICAL_FEATURES,
                         failure_modes=FAILURE_MODE_OPTIONS,
                         use_single_page=USE_SINGLE_PAGE_WORKFLOW)
```

#### Route: `/submit_stage1` → Handle blind ID submission
```python
@app.route('/submit_stage1', methods=['POST'])
def submit_stage1():
    """Store Stage 1 (blind ID) and reveal ground truth"""
    session['blind_id_family'] = request.form.get('family', '')
    session['blind_id_genus'] = request.form.get('genus', '')
    session['blind_id_species'] = request.form.get('species', '')
    session['stage1_submitted'] = True
    session['stage1_time'] = time.time() - session.get('stage1_start', time.time())

    return redirect(url_for('index'))  # Refresh to show Stage 2+
```

#### Route: `/submit_final` → Save complete evaluation (FINALIZED)
```python
@app.route('/submit_final', methods=['POST'])
def submit_final():
    """Save all evaluation data and move to next image"""
    import time

    current_image_data = session['current_image_data']

    # Create database record with FINALIZED schema
    evaluation = InsectEvaluation(
        # User tracking
        prolific_pid=session['prolific_pid'],
        study_id=session['study_id'],
        session_id=session['session_id'],
        subset_id=session['subset_id'],
        image_index=session['current_image_index'],
        absolute_image_index=current_image_data['absolute_index'],

        # Image metadata
        image_path=current_image_data['image_path'],
        ground_truth_family=current_image_data['ground_truth']['family'],
        ground_truth_genus=current_image_data['ground_truth']['genus'],
        ground_truth_species=current_image_data['ground_truth']['species'],
        model_type=current_image_data.get('model', 'unknown'),

        # STAGE 1: Blind ID (from session - saved during /submit_stage1)
        blind_id_family=session.get('blind_id_family', ''),
        blind_id_genus=session.get('blind_id_genus', ''),
        blind_id_species=session.get('blind_id_species', ''),

        # STAGE 2 - Question 2: Morphological Fidelity (ALL 6 FEATURES)
        morph_legs_appendages=int(request.form.get('morph_legs_appendages', 3)),
        morph_wing_venation_texture=int(request.form.get('morph_wing_venation_texture', 3)),
        morph_head_antennae=int(request.form.get('morph_head_antennae', 3)),
        morph_abdomen_banding=int(request.form.get('morph_abdomen_banding', 3)),
        morph_thorax_coloration=int(request.form.get('morph_thorax_coloration', 3)),
        morph_wing_pit_markings=int(request.form.get('morph_wing_pit_markings', 3)),

        # STAGE 2 - Question 3: Diagnostic Completeness (SIMPLIFIED)
        diagnostic_level=request.form.get('diagnostic_level', 'none'),

        # STAGE 2 - Question 4: Failure Modes (multi-select, stored as JSON)
        failure_modes=json.dumps(request.form.getlist('failure_modes')),

        # Question 5: REMOVED (no Real vs Synthetic)

        # Timing metadata
        time_stage1=session.get('stage1_time', 0),
        time_stage2=time.time() - session.get('stage2_start', time.time()),
        datetime=datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
    )

    db.session.add(evaluation)
    db.session.commit()

    # Reset for next image
    session['current_image_index'] += 1
    session['stage1_submitted'] = False
    session.pop('current_image_data', None)
    session.pop('blind_id_family', None)
    session.pop('blind_id_genus', None)
    session.pop('blind_id_species', None)

    return redirect(url_for('index'))
```

### 4. **New Template: `evaluation_form.html`** (FINALIZED)

Complete single-page evaluation form with finalized design:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insect Image Expert Evaluation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: #f7f7f7;
            max-width: 1200px;
            margin: 0 auto;
        }
        .progress-bar {
            background: #e0e0e0;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }
        .image-section {
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .image-section img {
            max-width: 100%;
            max-height: 600px;
            cursor: pointer;
            border: 3px solid #007bff;
            border-radius: 8px;
        }
        .stage {
            background: white;
            margin: 20px 0;
            padding: 20px;
            border: 2px solid #ddd;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .stage h3 {
            margin-top: 0;
            color: #007bff;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .stage.locked {
            opacity: 0.4;
            pointer-events: none;
            position: relative;
        }
        .stage.locked::before {
            content: "🔒 Complete Stage 1 to unlock";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 18px;
            font-weight: bold;
            color: #666;
        }
        .ground-truth-box {
            background: #d4edda;
            border: 3px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            display: none;
            text-align: center;
        }
        .ground-truth-box.visible {
            display: block;
        }
        .ground-truth-box h4 {
            margin: 0 0 10px 0;
            color: #155724;
        }
        .ground-truth-box .species-name {
            font-size: 24px;
            font-weight: bold;
            color: #155724;
        }

        /* Form elements */
        .form-row {
            margin: 15px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        select, input[type="text"] {
            width: 100%;
            padding: 8px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        select:focus, input[type="text"]:focus {
            border-color: #007bff;
            outline: none;
        }

        /* Slider styling */
        .slider-container {
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .slider-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-weight: bold;
        }
        .slider-value {
            color: #007bff;
            font-size: 18px;
        }
        input[type="range"] {
            width: 100%;
            height: 8px;
            background: #ddd;
            outline: none;
            border-radius: 5px;
        }
        input[type="range"]::-webkit-slider-thumb {
            width: 20px;
            height: 20px;
            background: #007bff;
            cursor: pointer;
            border-radius: 50%;
        }
        .slider-scale {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }

        /* Checkboxes */
        .checkbox-group label {
            display: flex;
            align-items: center;
            padding: 8px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 5px;
            cursor: pointer;
        }
        .checkbox-group input[type="checkbox"] {
            margin-right: 10px;
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        /* Buttons */
        button {
            padding: 12px 30px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-submit-stage1 {
            background-color: #007bff;
            color: white;
            width: 100%;
            margin-top: 15px;
        }
        .btn-submit-stage1:hover {
            background-color: #0056b3;
        }
        .btn-submit-final {
            background-color: #28a745;
            color: white;
            width: 100%;
            margin-top: 20px;
            font-size: 18px;
        }
        .btn-submit-final:hover {
            background-color: #218838;
        }

        /* Modal for fullscreen image */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
        }
        .modal-content {
            margin: auto;
            display: block;
            max-width: 95%;
            max-height: 95%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        .close-modal {
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="progress-bar">
        Image {{ current_index + 1 }} of {{ total }} |
        Estimated time remaining: {{ ((total - current_index - 1) * 1.5)|round(1) }} minutes
    </div>

    <!-- Image Display -->
    <div class="image-section">
        <img src="{{ url_for('static', filename=image_data.image_path) }}"
             alt="Insect Image {{ current_index + 1 }}"
             id="main-image"
             onclick="openFullscreen()">
        <p style="color: #666; margin-top: 10px;">Click image to enlarge</p>
    </div>

    <form method="post" action="/submit_final" id="evaluation-form">

        <!-- ============================================ -->
        <!-- STAGE 1: Blind Species ID (With Dropdowns) -->
        <!-- ============================================ -->
        <div class="stage" id="stage1">
            <h3>Question 1: Species Identification (Blind)</h3>
            <p>Based on the image alone, provide your best taxonomic identification:</p>

            <div class="form-row">
                <label for="family">Family:</label>
                <select name="family" id="family" required onchange="updateGenusOptions()">
                    <option value="">-- Select Family --</option>
                    {% for family in taxonomy_options.families %}
                    <option value="{{ family }}">{{ family }}</option>
                    {% endfor %}
                </select>
            </div>

            <div class="form-row">
                <label for="genus">Genus:</label>
                <select name="genus" id="genus" required>
                    <option value="">-- First select a family --</option>
                </select>
            </div>

            <div class="form-row">
                <label for="species">Species (full name or "Unknown"):</label>
                <input type="text" name="species" id="species"
                       placeholder="e.g., Bombus impatiens or Unknown" required>
            </div>

            {% if not stage1_complete %}
            <button type="button" class="btn-submit-stage1" onclick="submitStage1()">
                Submit Identification & Reveal Ground Truth
            </button>
            {% endif %}
        </div>

        <!-- Ground Truth Reveal -->
        <div class="ground-truth-box {% if stage1_complete %}visible{% endif %}">
            <h4>✓ Ground Truth Species</h4>
            <div class="species-name">{{ image_data.ground_truth.species }}</div>
            <p style="margin-top: 10px;">
                Family: <strong>{{ image_data.ground_truth.family }}</strong> |
                Genus: <strong>{{ image_data.ground_truth.genus }}</strong>
            </p>
            {% if image_data.ground_truth.common_name %}
            <p style="font-style: italic; color: #666;">
                ({{ image_data.ground_truth.common_name }})
            </p>
            {% endif %}
        </div>

        <!-- ============================================ -->
        <!-- STAGE 2: Detailed Evaluation (Locked until Stage 1 done) -->
        <!-- ============================================ -->
        <div class="{% if not stage1_complete %}locked{% endif %}">

            <!-- Question 2: Morphological Fidelity (ALL 6 FEATURES) -->
            <div class="stage">
                <h3>Question 2: Morphological Fidelity</h3>
                <p>Now that you know the ground truth species, rate the anatomical correctness of each feature:</p>
                <p style="font-style: italic; color: #666;">
                    1 = Very Poor (major errors) | 3 = Acceptable | 5 = Excellent (publication quality)
                </p>

                {% for feature_id, feature_label in morphological_features %}
                <div class="slider-container">
                    <div class="slider-label">
                        <span>{{ feature_label }}</span>
                        <span class="slider-value" id="value-{{ feature_id }}">3</span>
                    </div>
                    <input type="range" name="morph_{{ feature_id }}"
                           id="slider-{{ feature_id }}" min="1" max="5" value="3" required
                           oninput="updateSliderValue('{{ feature_id }}', this.value)">
                    <div class="slider-scale">
                        <span>1 (Poor)</span>
                        <span>2</span>
                        <span>3 (OK)</span>
                        <span>4</span>
                        <span>5 (Excellent)</span>
                    </div>
                </div>
                {% endfor %}
            </div>

            <!-- Question 3: Diagnostic Completeness (SIMPLIFIED) -->
            <div class="stage">
                <h3>Question 3: Diagnostic Completeness</h3>
                <p>What is the <strong>highest taxonomic level</strong> at which this image contains
                   sufficient diagnostic features to identify <strong>{{ image_data.ground_truth.species }}</strong>?</p>

                <div class="form-row">
                    <select name="diagnostic_level" id="diagnostic_level" required>
                        <option value="">-- Select highest ID level --</option>
                        {% for level_id, level_label in diagnostic_levels %}
                        <option value="{{ level_id }}">{{ level_label }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>

            <!-- Question 4: Failure Modes (MULTI-SELECT) -->
            <div class="stage">
                <h3>Question 4: Failure Modes</h3>
                <p>If this image has significant defects, select <strong>all</strong> that apply (leave unchecked if none):</p>

                <div class="checkbox-group">
                    {% for mode_id, mode_label in failure_modes %}
                    <label>
                        <input type="checkbox" name="failure_modes" value="{{ mode_id }}">
                        {{ mode_label }}
                    </label>
                    {% endfor %}
                </div>
                <p style="font-size: 14px; color: #666; margin-top: 10px;">
                    <em>Note: You can select multiple defects or none at all.</em>
                </p>
            </div>

            <button type="submit" class="btn-submit-final">
                Submit Evaluation & Continue to Next Image
            </button>
        </div>
    </form>

    <!-- Fullscreen Image Modal -->
    <div id="imageModal" class="modal" onclick="closeFullscreen()">
        <span class="close-modal">&times;</span>
        <img class="modal-content" id="modal-image">
    </div>

    <script>
        // Taxonomy dropdown data (passed from Flask)
        const genusOptions = {{ taxonomy_options.genera_by_family | tojson }};

        function updateGenusOptions() {
            const familySelect = document.getElementById('family');
            const genusSelect = document.getElementById('genus');
            const selectedFamily = familySelect.value;

            // Clear current options
            genusSelect.innerHTML = '<option value="">-- Select Genus --</option>';

            // Populate genus dropdown based on selected family
            if (selectedFamily && genusOptions[selectedFamily]) {
                genusOptions[selectedFamily].forEach(genus => {
                    const option = document.createElement('option');
                    option.value = genus;
                    option.textContent = genus;
                    genusSelect.appendChild(option);
                });
            }
        }

        function updateSliderValue(featureId, value) {
            document.getElementById('value-' + featureId).textContent = value;
        }

        function submitStage1() {
            // Validate required fields
            const family = document.getElementById('family').value;
            const genus = document.getElementById('genus').value;
            const species = document.getElementById('species').value;

            if (!family || !genus || !species) {
                alert('Please fill in all three fields: Family, Genus, and Species');
                return;
            }

            // Send Stage 1 data via AJAX
            const formData = new FormData();
            formData.append('family', family);
            formData.append('genus', genus);
            formData.append('species', species);

            fetch('/submit_stage1', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    location.reload();  // Reload to show ground truth and unlock Stage 2
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error submitting Stage 1. Please try again.');
            });
        }

        function openFullscreen() {
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modal-image');
            const img = document.getElementById('main-image');

            modal.style.display = 'block';
            modalImg.src = img.src;
        }

        function closeFullscreen() {
            document.getElementById('imageModal').style.display = 'none';
        }

        // Close modal on ESC key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeFullscreen();
            }
        });

        // Form validation before final submit
        document.getElementById('evaluation-form').addEventListener('submit', function(e) {
            const diagnosticLevel = document.getElementById('diagnostic_level').value;
            if (!diagnosticLevel) {
                e.preventDefault();
                alert('Please select a diagnostic completeness level (Question 3)');
                return false;
            }
        });
    </script>
</body>
</html>
```

---

## Implementation Steps (Recommended Order)

1. **Create sample data** (`assets/insect_images_metadata.json`) with 5-10 test images
2. **Update `constants.py`** with new configuration
3. **Update `util.py`** data loading functions
4. **Create new database model** in `app_human_identity_db.py`
5. **Create `evaluation_form.html`** template
6. **Update Flask routes** for new workflow
7. **Test with dummy data** locally
8. **Add full dataset** and deploy

---

## Testing Checklist

- [ ] Single image loads correctly
- [ ] Stage 1 submission reveals ground truth
- [ ] All form fields save to database
- [ ] Multi-select checkboxes work
- [ ] Sliders show current value
- [ ] Progress tracking works (X of Y images)
- [ ] User can refresh and resume
- [ ] Database stores all fields correctly
- [ ] Export annotations to CSV/JSON for analysis

---

## Data Analysis After Collection

You'll want to create analysis scripts to:

```python
# Calculate taxonomic accuracy
def calculate_accuracy(df):
    df['family_correct'] = df['blind_id_family'] == df['ground_truth_family']
    df['genus_correct'] = df['blind_id_genus'] == df['ground_truth_genus']
    df['species_correct'] = df['blind_id_species'] == df['ground_truth_species']
    return df

# Average morphological scores
morph_cols = [col for col in df.columns if col.startswith('morph_')]
df['avg_morphology_score'] = df[morph_cols].mean(axis=1)

# Failure mode distribution
failure_counts = df['failure_modes'].apply(json.loads).explode().value_counts()
```

---

## Estimated Timeline

- Data preparation: 1-2 days
- Backend implementation: 2-3 days
- Frontend template: 2-3 days
- Testing & refinement: 2-3 days
- **Total: ~1-2 weeks**

---

## ✅ FINALIZED Design Summary

### **Time Budget (Per Image)**
```
Stage 1: Blind Species ID
  - Select Family dropdown        ~5 sec
  - Select Genus dropdown          ~5 sec
  - Type Species name              ~8 sec
  - Submit & reveal                ~2 sec
  ─────────────────────────────────────
  Subtotal:                        ~20 sec

Stage 2: Detailed Evaluation
  - Question 2: 6 morphology sliders  ~35-40 sec
  - Question 3: Diagnostic dropdown   ~8-10 sec
  - Question 4: Failure modes         ~10-15 sec
  ─────────────────────────────────────
  Subtotal:                        ~55-65 sec

Total per image:                   ~75-85 sec (1.2-1.4 min)
```

### **Study Duration**
- **50 images/expert**: ~60-70 minutes ✅ (Reasonable for paid study)
- **100 images/expert**: ~120-140 minutes ❌ (Too long)
- **Recommended**: 50 images with 10 min break = ~80 min total

### **Prolific Compensation Estimate**
- 60-70 min × $12/hour = **~$12-14 per participant**
- Add buffer for technical issues: **$15-16 recommended**

### **Final Design Decisions**

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Q1: Species ID** | Dropdowns for Family/Genus | Faster (~15-20s vs ~30s), cleaner data |
| **Q2: Morphology** | Keep all 6 features | Comprehensive evaluation needed |
| **Q3: Diagnostic** | Single dropdown (simplified) | Faster (~10s vs ~20s for 3 yes/no) |
| **Q4: Failure Modes** | Multi-select checkboxes | Allow multiple defects |
| **Q5: Real vs Synthetic** | **REMOVED** | Not needed, saves ~10s/image |
| **Workflow** | Single-page, 2-stage | Better UX, less navigation |
| **Images per expert** | 50 recommended | ~60-75 min total |

### **Data Quality Features**
✅ Blind evaluation prevents bias (Stage 1)
✅ Standardized taxonomy via dropdowns
✅ All morphology fields required (no skipping)
✅ Timing data captures annotation speed
✅ Multi-select allows nuanced failure analysis
✅ Ground truth reveal validates expert knowledge

### **Prolific Integration**
- ✅ Keep existing Prolific URL parameters (PROLIFIC_PID, STUDY_ID, SESSION_ID)
- ✅ Keep automatic user assignment to subsets
- ✅ Keep completion code redirect: `https://app.prolific.co/submissions/complete?cc=INSECT_EVAL_2025`
- ✅ Users can refresh and resume (progress saved)
