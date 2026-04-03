# Bumblebee Image Evaluation Configuration
# Based on 16 Bombus species from GBIF_MA_BUMBLEBEES dataset

# ============================================
# MODE CONFIGURATION
# ============================================

MODE = "calibration"  # "calibration" or "full"

if MODE == "calibration":
    IMAGES_PER_USER = 10
    TOTAL_IMAGES = 10
    MAX_USERS_PER_SUBSET = 1
    ACTIVE_DB = "sqlite:///bumblebee_evaluation_calibration.db"
else:  # full
    IMAGES_PER_USER = 150
    TOTAL_IMAGES = 150
    MAX_USERS_PER_SUBSET = 1
    ACTIVE_DB = "sqlite:///bumblebee_evaluation_full.db"

# Species with synthetic images (expert validation set)
SPECIES_WITH_SYNTHETIC = [
    "Bombus_ashtoni",      # 50 images
    "Bombus_sandersoni",   # 50 images
    "Bombus_flavidus"      # 50 images
]

# Asset paths
METADATA_JSON = f"assets/bumblebee_images_metadata_{MODE}.json"
STATIC_IMAGES_DIR = "static/bumblebees"
STATIC_REFERENCES_DIR = "static/references"

# Workflow configuration
USE_SINGLE_PAGE_WORKFLOW = True  # Two-stage single-page design
USE_TAXONOMY_DROPDOWNS = True  # Dropdowns for Family/Genus

# ============================================
# REFERENCE IMAGES CONFIGURATION
# ============================================

SHOW_REFERENCE_IMAGES = True  # Show after Stage 1 reveal
MAX_REFERENCE_IMAGES = 5  # Maximum reference images to display
REFERENCE_IMAGE_LAYOUT = "grid"  # "grid" or "carousel"

# ============================================
# QUESTION 1: Blind Species ID with Dropdowns
# ============================================

# All 16 bumblebee species from GBIF_MA_BUMBLEBEES + "No match"
BUMBLEBEE_SPECIES = [
    "Bombus affinis",
    "Bombus ashtoni",
    "Bombus bimaculatus",
    "Bombus borealis",
    "Bombus citrinus",
    "Bombus fervidus",
    "Bombus flavidus",
    "Bombus griseocollis",
    "Bombus impatiens",
    "Bombus pensylvanicus",
    "Bombus perplexus",
    "Bombus rufocinctus",
    "Bombus sandersoni",
    "Bombus ternarius",
    "Bombus terricola",
    "Bombus vagans",
    "No match"  # Expert cannot identify to any known species
]

# Taxonomy options for dropdowns
TAXONOMY_OPTIONS = {
    "families": [
        "Apidae",
    ],
    "genera_by_family": {
        "Apidae": [
            "Bombus",
        ]
    },
    "species_by_genus": {
        "Bombus": [
            "Bombus affinis",
            "Bombus ashtoni",
            "Bombus bimaculatus",
            "Bombus borealis",
            "Bombus citrinus",
            "Bombus fervidus",
            "Bombus flavidus",
            "Bombus griseocollis",
            "Bombus impatiens",
            "Bombus pensylvanicus",
            "Bombus perplexus",
            "Bombus rufocinctus",
            "Bombus sandersoni",
            "Bombus ternarius",
            "Bombus terricola",
            "Bombus vagans",
            "No match"
        ]
    }
}

# ============================================
# QUESTION 2: Morphological Fidelity (5 FEATURES)
# ============================================

MORPHOLOGICAL_FEATURES = [
    ("legs_appendages", "Legs/Appendages"),
    ("wing_venation_texture", "Wing Venation/Texture"),
    ("head_antennae", "Head/Antennae"),
    ("abdomen_banding", "Abdomen Banding"),  # Critical for Bombus ID
    ("thorax_coloration", "Thorax Coloration")  # Critical for Bombus ID
]

# ============================================
# QUESTION 2B: Blind Caste Identification
# ============================================

# Per-species caste options (cuckoo vs eusocial have different castes)
CASTE_OPTIONS_BY_SPECIES = {
    "Bombus ashtoni":    [("female", "Female"), ("male", "Male"), ("uncertain", "Uncertain")],
    "Bombus flavidus":   [("female", "Female"), ("male", "Male"), ("uncertain", "Uncertain")],
    "Bombus sandersoni": [("worker", "Worker"), ("queen", "Queen"), ("male", "Male"), ("uncertain", "Uncertain")],
}

# Fallback for unknown species
CASTE_OPTIONS_DEFAULT = [
    ("worker", "Worker"),
    ("queen", "Queen"),
    ("male", "Male"),
    ("female", "Female"),
    ("uncertain", "Uncertain"),
]

# ============================================
# QUESTION 3: Diagnostic Completeness (SIMPLIFIED)
# ============================================

DIAGNOSTIC_LEVELS = [
    ("none", "Not identifiable (unusable image)"),
    ("family", "Family level only (Apidae)"),
    ("genus", "Genus level (Bombus)"),
    ("species", "Species level (full identification)")
]

# ============================================
# QUESTION 4: Failure Modes (MULTI-SELECT)
# Split into two categories:
#   A) Species Fidelity/Correctness
#   B) Image Quality
# ============================================

FAILURE_MODE_SPECIES = [
    ("species_no_failure", "No Failure"),
    ("extra_missing_limbs", "Extra/Missing Limbs"),
    ("wrong_coloration", "Wrong Coloration/Pattern"),
    ("impossible_geometry", "Impossible Geometry/Unnatural Pose"),
    ("species_other", "Other"),
]

FAILURE_MODE_QUALITY = [
    ("quality_no_failure", "No Failure"),
    ("blurry_artifacts", "Blurry/Visual Artifacts"),
    ("background_bleed", "Background Bleed/Contamination"),
    ("flower_unrealistic", "Unrealistic Flower Geometry"),
    ("repetitive_pattern", "Repetitive/Cloned Patterns"),
    ("quality_other", "Other"),
]

# Combined for backward compatibility
FAILURE_MODE_OPTIONS = FAILURE_MODE_SPECIES + FAILURE_MODE_QUALITY

# ============================================
# PROLIFIC INTEGRATION
# ============================================

COMPLETION_CODE = "BUMBLEBEE_EVAL_2025"  # Update for your study

# Omit completed subsets (update as you collect data)
OMIT_SUBSETS = []
OMIT_IMAGE_IDS = []  # Specific images to exclude

# ============================================
# SPECIES METADATA (Optional - for display)
# ============================================

SPECIES_COMMON_NAMES = {
    "Bombus affinis": "Rusty Patched Bumble Bee",
    "Bombus ashtoni": "Ashton Cuckoo Bumble Bee",
    "Bombus bimaculatus": "Two-spotted Bumble Bee",
    "Bombus borealis": "Northern Amber Bumble Bee",
    "Bombus citrinus": "Lemon Cuckoo Bumble Bee",
    "Bombus fervidus": "Yellow Bumble Bee",
    "Bombus flavidus": "Fernald's Cuckoo Bumble Bee",
    "Bombus griseocollis": "Brown-belted Bumble Bee",
    "Bombus impatiens": "Common Eastern Bumble Bee",
    "Bombus pensylvanicus": "American Bumble Bee",
    "Bombus perplexus": "Confusing Bumble Bee",
    "Bombus rufocinctus": "Red-belted Bumble Bee",
    "Bombus sandersoni": "Sanderson's Bumble Bee",
    "Bombus ternarius": "Tri-colored Bumble Bee",
    "Bombus terricola": "Yellow-banded Bumble Bee",
    "Bombus vagans": "Half-black Bumble Bee"
}

# Critical morphological features per species (for reference)
SPECIES_KEY_FEATURES = {
    "Bombus impatiens": "Yellow and black banding, fuzzy thorax, very common",
    "Bombus sandersoni": "Smaller, T1-2 yellow, T3-5 black, some black between wing bases",
    "Bombus ashtoni": "Hair on head almost entirely black, white on abdomen end",
    "Bombus flavidus": "Cuckoo bee, variable coloration, often yellowish pile on thorax",
    "Bombus affinis": "Rusty patch on abdomen, critically endangered",
}
