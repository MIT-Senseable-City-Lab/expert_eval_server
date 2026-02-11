# Bumblebee Synthetic Image Evaluation Server

Expert evaluation system for AI-generated bumblebee images using a comprehensive multi-question assessment protocol.

---

## 🎯 Quick Start

### 1. Copy Images (5 minutes)
```bash
./scripts/setup_bumblebee_data.sh
```

### 2. Review Documentation
- **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** ← START HERE for complete overview
- **[DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md)** for detailed setup instructions
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** for technical specifications
- **[DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)** for design decisions

### 3. Implement the System
Follow the step-by-step guide in [SETUP_SUMMARY.md](SETUP_SUMMARY.md#what-you-need-to-do-next)

---

## 📊 Dataset Overview

**Current Dataset**: 146 synthetic bumblebee images

| Species | Images | References |
|---------|--------|------------|
| Bombus ashtoni | 46 | 2 |
| Bombus sandersoni | 50 | 2 |
| Bombus ternarius | 50 | 2 |
| **Total** | **146** | **6** |

---

## 🔬 Evaluation Protocol

### Two-Stage Workflow

**Stage 1: Blind Species ID** (~20 seconds)
- Family (dropdown)
- Genus (dropdown, filtered by family)
- Species (text input)

**Stage 2: Detailed Evaluation** (~55-65 seconds)
- **Q2**: Morphological Fidelity (6 features, 1-5 scale)
  - Legs/Appendages
  - Wing Venation/Texture
  - Head/Antennae
  - Abdomen Banding
  - Thorax Coloration
  - Wing Pit Markings
- **Q3**: Diagnostic Completeness (single dropdown)
- **Q4**: Failure Modes (multi-select checkboxes)

**Total Time**: ~75-85 seconds per image (1.2-1.4 minutes)

---

## 📁 File Structure

```
eval_server/
├── README_BUMBLEBEE.md           ← YOU ARE HERE
├── SETUP_SUMMARY.md              ← Next: Read this
├── constants_BUMBLEBEE.py        ✓ Configuration ready
├── assets/
│   └── bumblebee_images_metadata.json ✓ 146 entries generated
└── scripts/
    ├── setup_bumblebee_data.sh        ✓ Run this first
    └── generate_bumblebee_metadata.py ✓ Metadata generator
```

---

## ✅ What's Complete

- [x] Dataset discovery and analysis
- [x] Metadata generation (146 images)
- [x] Configuration files updated
- [x] Data preparation scripts created
- [x] Documentation complete

## 🔧 What's Next

- [ ] Copy images using `setup_bumblebee_data.sh`
- [ ] Update database models
- [ ] Create evaluation template
- [ ] Update Flask routes
- [ ] Test locally

**Estimated time**: 3-5 hours of focused development

---

## 📖 Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [SETUP_SUMMARY.md](SETUP_SUMMARY.md) | **Start here** - Complete overview and next steps | First read |
| [DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md) | Detailed data setup instructions | Before copying images |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Complete technical specification | During development |
| [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) | Design decisions and workflow | Reference |

---

## 🚀 Running the Evaluation Server

```bash
# After implementation is complete:
python3 app_human_identity_db.py

# Visit in browser:
http://localhost:5000

# With Prolific:
http://localhost:5000/?PROLIFIC_PID=test123&STUDY_ID=test&SESSION_ID=1
```

---

## 📞 Configuration

**Main config file**: [constants_BUMBLEBEE.py](constants_BUMBLEBEE.py)

Key settings:
- `TOTAL_IMAGES = 146`
- `IMAGES_PER_USER = 50`
- `SHOW_REFERENCE_IMAGES = True`
- `MAX_REFERENCE_IMAGES = 5`
- All 16 Bombus species defined (ready for expansion)

---

## 🔄 Regenerating Metadata

If you add more synthetic images:

```bash
python3 scripts/generate_bumblebee_metadata.py
```

The script automatically:
- Scans all synthetic image directories
- Extracts generation metadata
- Maps reference images
- Outputs complete JSON

---

**For detailed setup instructions, see [SETUP_SUMMARY.md](SETUP_SUMMARY.md)**
