# Data Preparation Guide for Bumblebee Evaluation Server

## Overview

This guide walks you through preparing the evaluation server to use your actual synthetic bumblebee images.

**Current Status**: ✓ Metadata JSON generated (146 images from 3 species)

---

## 1. Current Dataset Summary

Based on your actual data in `GBIF_MA_BUMBLEBEES/prepared_synthetic/train`:

| Species | Synthetic Images | Reference Images | Status |
|---------|------------------|------------------|--------|
| **Bombus ashtoni** | 46 | ✓ 2 refs | Ready |
| **Bombus sandersoni** | 50 | ✓ 2 refs | Ready |
| **Bombus ternarius** | 50 | ✓ 2 refs | Ready |
| Bombus affinis | 0 | - | No synthetic images yet |
| Bombus bimaculatus | 0 | - | No synthetic images yet |
| Bombus borealis | 0 | - | No synthetic images yet |
| Bombus citrinus | 0 | - | No synthetic images yet |
| Bombus fervidus | 0 | - | No synthetic images yet |
| Bombus flavidus | 0 | - | No synthetic images yet |
| Bombus griseocollis | 0 | - | No synthetic images yet |
| Bombus impatiens | 0 | - | No synthetic images yet |
| Bombus pensylvanicus | 0 | - | No synthetic images yet |
| Bombus perplexus | 0 | - | No synthetic images yet |
| Bombus rufocinctus | 0 | - | No synthetic images yet |
| Bombus terricola | 0 | - | No synthetic images yet |
| Bombus vagans | 0 | - | No synthetic images yet |

**Total Images Ready for Evaluation**: 146

---

## 2. Directory Structure Setup

### Required Directory Structure:

```
eval_server/
├── assets/
│   └── bumblebee_images_metadata.json  ✓ Generated
├── static/
│   ├── bumblebees/                      ← COPY IMAGES HERE
│   │   ├── Bombus_ashtoni/
│   │   │   ├── synthetic_001_female_dorsal.png
│   │   │   ├── synthetic_002_female_lateral.png
│   │   │   └── ... (46 images total)
│   │   ├── Bombus_sandersoni/
│   │   │   └── ... (50 images)
│   │   └── Bombus_ternarius_Say/
│   │       └── ... (50 images)
│   └── references/                      ← COPY REFERENCES HERE
│       ├── Bombus_ashtoni/
│       │   ├── Bombus-ashtoni-M.jpg
│       │   └── bombus_ashtoni female_posed_on_dandelion scolla.jpg
│       ├── Bombus_sandersoni/
│       │   ├── Bombus-sandersoni-5335.jpeg
│       │   └── sandersoni_photo.jpg
│       └── Bombus_ternarius_Say/
│           ├── medium.jpg
│           └── INS018-00110.jpg
└── scripts/
    └── generate_bumblebee_metadata.py   ✓ Created
```

---

## 3. Step-by-Step Setup

### Step 1: Copy Synthetic Images

```bash
# Create directory structure
mkdir -p static/bumblebees

# Copy synthetic images for the 3 species with data
cp -r /Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus/GBIF_MA_BUMBLEBEES/prepared_synthetic/train/Bombus_ashtoni \
      static/bumblebees/

cp -r /Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus/GBIF_MA_BUMBLEBEES/prepared_synthetic/train/Bombus_sandersoni \
      static/bumblebees/

cp -r /Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus/GBIF_MA_BUMBLEBEES/prepared_synthetic/train/Bombus_ternarius_Say \
      static/bumblebees/
```

**Result**: 146 synthetic images in `static/bumblebees/`

### Step 2: Copy Reference Images

```bash
# Create directory structure
mkdir -p static/references

# Copy reference images
cp -r /Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus/SYNTHETIC_BUMBLEBEES/references/Bombus_ashtoni \
      static/references/

cp -r /Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus/SYNTHETIC_BUMBLEBEES/references/Bombus_sandersoni \
      static/references/

cp -r /Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus/SYNTHETIC_BUMBLEBEES/references/Bombus_ternarius_Say \
      static/references/
```

**Result**: Reference images for 3 species in `static/references/`

### Step 3: Verify Metadata JSON

The metadata JSON has already been generated at:
```
assets/bumblebee_images_metadata.json
```

Verify it contains 146 entries:
```bash
python3 -c "import json; data = json.load(open('assets/bumblebee_images_metadata.json')); print(f'Total entries: {len(data)}')"
```

Expected output: `Total entries: 146`

---

## 4. Quick Copy Script

For convenience, create this script to copy all data at once:

```bash
#!/bin/bash
# save as: scripts/setup_bumblebee_data.sh

set -e  # Exit on error

BUMBLEBEE_BASE="/Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus"
SOURCE_IMAGES="$BUMBLEBEE_BASE/GBIF_MA_BUMBLEBEES/prepared_synthetic/train"
SOURCE_REFS="$BUMBLEBEE_BASE/SYNTHETIC_BUMBLEBEES/references"

echo "Setting up bumblebee evaluation data..."

# Create directories
mkdir -p static/bumblebees
mkdir -p static/references

# Copy the 3 species with synthetic images
for species in Bombus_ashtoni Bombus_sandersoni Bombus_ternarius_Say; do
    echo "Copying $species images..."
    cp -r "$SOURCE_IMAGES/$species" static/bumblebees/

    if [ -d "$SOURCE_REFS/$species" ]; then
        echo "Copying $species references..."
        cp -r "$SOURCE_REFS/$species" static/references/
    fi
done

echo "✓ Data setup complete!"
echo "  Synthetic images: static/bumblebees/"
echo "  Reference images: static/references/"
echo ""
echo "Next: Run the metadata generation script if not already done:"
echo "  python3 scripts/generate_bumblebee_metadata.py"
```

Run it:
```bash
chmod +x scripts/setup_bumblebee_data.sh
./scripts/setup_bumblebee_data.sh
```

---

## 5. Verification Checklist

After copying, verify the setup:

```bash
# Check synthetic images
echo "Synthetic images per species:"
for species in Bombus_ashtoni Bombus_sandersoni Bombus_ternarius_Say; do
    count=$(find "static/bumblebees/$species" -name "synthetic_*.png" 2>/dev/null | wc -l | tr -d ' ')
    echo "  $species: $count"
done

# Check reference images
echo ""
echo "Reference images per species:"
for species in Bombus_ashtoni Bombus_sandersoni Bombus_ternarius_Say; do
    count=$(find "static/references/$species" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "  $species: $count"
done

# Check metadata
echo ""
python3 -c "import json; data = json.load(open('assets/bumblebee_images_metadata.json')); print(f'Metadata entries: {len(data)}')"
```

**Expected Output**:
```
Synthetic images per species:
  Bombus_ashtoni: 46
  Bombus_sandersoni: 50
  Bombus_ternarius_Say: 50

Reference images per species:
  Bombus_ashtoni: 2
  Bombus_sandersoni: 2
  Bombus_ternarius_Say: 2

Metadata entries: 146
```

---

## 6. Configuration Updates

The following configuration files have been updated for your dataset:

### `constants_BUMBLEBEE.py`:
- ✓ `TOTAL_IMAGES = 146`
- ✓ `SPECIES_WITH_SYNTHETIC` lists 3 species
- ✓ Asset paths configured
- ✓ All 16 species preserved in `BUMBLEBEE_SPECIES` (for future expansion)

### `assets/bumblebee_images_metadata.json`:
- ✓ 146 entries generated
- ✓ Ground truth metadata included
- ✓ Reference image paths mapped
- ✓ Generation metadata preserved (angle, gender, environmental context)

---

## 7. Image Filename Patterns

Your synthetic images follow this naming convention:
```
synthetic_{number}_{gender}_{angle}.png
```

Examples:
- `synthetic_001_female_dorsal.png`
- `synthetic_012_male_frontal.png`
- `synthetic_023_female_lateral.png`

Metadata extraction from filenames:
- **Number**: Sequential ID (001-050)
- **Gender**: `female` or `male`
- **Angle**: `dorsal`, `lateral`, or `frontal`

This information is automatically extracted and included in the metadata JSON.

---

## 8. Reference Image Mapping

Reference images are stored per species:

| Species | Reference Count | Files |
|---------|-----------------|-------|
| Bombus ashtoni | 2 | Bombus-ashtoni-M.jpg, bombus_ashtoni female_posed_on_dandelion scolla.jpg |
| Bombus sandersoni | 2 | Bombus-sandersoni-5335.jpeg, sandersoni_photo.jpg |
| Bombus ternarius | 2 | medium.jpg, INS018-00110.jpg |

These references will be displayed in the evaluation interface AFTER the blind species ID stage.

---

## 9. Future Expansion

When you generate synthetic images for the remaining 13 species:

1. **Generate new images** using your pipeline
2. **Re-run metadata generation**:
   ```bash
   python3 scripts/generate_bumblebee_metadata.py
   ```
3. **Copy new images** to `static/bumblebees/{species}/`
4. **Add reference images** to `SYNTHETIC_BUMBLEBEES/references/{species}/`
5. **Update `TOTAL_IMAGES`** in `constants_BUMBLEBEE.py`

The metadata generation script automatically detects all species with synthetic images.

---

## 10. Study Configuration

With **146 images** available:

### Option A: Small Pilot (Recommended First)
- **50 images per expert** (from metadata JSON)
- **3 subsets** (overlap for reliability testing)
- **~60-70 minutes** per participant
- **Prolific payment**: ~$15-16

### Option B: Full Dataset Evaluation
- **146 images per expert** (all images)
- **~175-205 minutes** per participant (too long!)
- **Not recommended** - split into multiple sessions

### Option C: Split Dataset
- **Two sessions** of 73 images each
- **90-100 minutes** per session
- Better for participant attention and data quality

**Recommended**: Start with Option A for pilot testing.

---

## 11. Ready to Launch Checklist

Before running the evaluation server:

- [ ] Synthetic images copied to `static/bumblebees/`
- [ ] Reference images copied to `static/references/`
- [ ] Metadata JSON exists at `assets/bumblebee_images_metadata.json`
- [ ] `constants_BUMBLEBEE.py` updated with correct `TOTAL_IMAGES`
- [ ] Database models updated (next step in implementation)
- [ ] Evaluation template created (next step in implementation)
- [ ] Flask routes updated (next step in implementation)

**Current Status**: Steps 1-4 complete ✓

---

## Next Steps

Now that the data is prepared, the next implementation tasks are:

1. **Update database schema** (use `InsectEvaluation` model from IMPLEMENTATION_PLAN.md)
2. **Create evaluation template** (`templates/evaluation_form.html`)
3. **Update Flask routes** for two-stage workflow
4. **Add form validation** for multi-question evaluation
5. **Test locally** with sample data

Refer to [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed technical specifications.
