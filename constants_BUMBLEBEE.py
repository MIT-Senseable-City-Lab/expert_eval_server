# Bumblebee Image Evaluation Configuration
# Based on 16 Bombus species from GBIF_MA_BUMBLEBEES dataset

# ============================================
# DATASET CONFIGURATION
# ============================================

# Evaluation scope
IMAGES_PER_USER = 50  # How many images each expert evaluates
TOTAL_IMAGES = 146  # Total synthetic images (3 species: Bombus ashtoni, sandersoni, ternarius)
MAX_USERS_PER_SUBSET = 3  # Maximum experts per subset

# Species with synthetic images (as of generation date)
SPECIES_WITH_SYNTHETIC = [
    "Bombus_ashtoni",      # 46 images
    "Bombus_sandersoni",   # 50 images
    "Bombus_ternarius_Say" # 50 images
]

# Database configuration
DB_DEBUG = "sqlite:///bumblebee_evaluation_debug.db"
DB_PROD = "sqlite:///bumblebee_evaluation_prod.db"

# Asset paths
METADATA_JSON = "assets/bumblebee_images_metadata.json"
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

# All 16 bumblebee species from GBIF_MA_BUMBLEBEES
BUMBLEBEE_SPECIES = [
    "Bombus affinis",
    "Bombus ashtoni",
    "Bombus bimaculatus",
    "Bombus borealis",
    "Bombus citrinus",
    "Bombus fervidus",
    "Bombus flavidus",  # The 16th species!
    "Bombus griseocollis",
    "Bombus impatiens",
    "Bombus pensylvanicus",
    "Bombus perplexus",
    "Bombus rufocinctus",
    "Bombus sandersoni",
    "Bombus ternarius",  # Note: stored as "Bombus_ternarius_Say" in files
    "Bombus terricola",
    "Bombus vagans"  # Note: stored as "Bombus_vagans_Smith" in files
]

# Taxonomy options for dropdowns
TAXONOMY_OPTIONS = {
    "families": [
        "Apidae",  # All bumblebees are in this family
        # Add other families if you expand to other insects later
    ],
    "genera_by_family": {
        "Apidae": [
            "Bombus",  # All 16 species are in this genus
            # Add other genera if you expand dataset
        ]
    }
}

# ============================================
# QUESTION 2: Morphological Fidelity (ALL 6 FEATURES)
# ============================================

MORPHOLOGICAL_FEATURES = [
    ("legs_appendages", "Legs/Appendages"),
    ("wing_venation_texture", "Wing Venation/Texture"),
    ("head_antennae", "Head/Antennae"),
    ("abdomen_banding", "Abdomen Banding"),  # Critical for Bombus ID
    ("thorax_coloration", "Thorax Coloration"),  # Critical for Bombus ID
    ("wing_pit_markings", "Wing Pit Markings")  # Mentioned in your prompt
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
# ============================================

# Based on common image generation issues
FAILURE_MODE_OPTIONS = [
    ("extra_missing_limbs", "Extra/Missing Limbs"),
    ("impossible_geometry", "Impossible Geometry/Unnatural Pose"),
    ("wrong_coloration", "Wrong Coloration/Pattern"),
    ("blurry_artifacts", "Blurry/Visual Artifacts"),
    ("background_bleed", "Background Bleed/Contamination"),
    ("flower_unrealistic", "Unrealistic Flower Geometry"),  # Your prompt concern
    ("repetitive_pattern", "Repetitive/Cloned Patterns")  # Your prompt concern
]

# ============================================
# PROLIFIC INTEGRATION
# ============================================

COMPLETION_CODE = "BUMBLEBEE_EVAL_2025"  # Update for your study

# Omit completed subsets (update as you collect data)
OMIT_SUBSETS = []
OMIT_IMAGE_IDS = []  # Specific images to exclude

# ============================================
# DELETE OLD CONSTANTS (from pair comparison system)
# ============================================

# TOTAL_PAIRS = 600  ← DELETE
# PAIRS_PER_USER = 100  ← DELETE
# NUM_SENTINELS = 0  ← DELETE
# RESPONSE_OPTIONS = ["Left", "Right"]  ← DELETE

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
# This helps experts know what to look for
SPECIES_KEY_FEATURES = {
    "Bombus impatiens": "Yellow and black banding, fuzzy thorax, very common",
    "Bombus sandersoni": "Smaller, T1-2 yellow, T3-5 black, some black between wing bases",
    "Bombus ternarius": "Yellow face (distinctive!), tri-color abdomen pattern",
    "Bombus ashtoni": "Hair on head almost entirely black, white on abdomen end",
    "Bombus affinis": "Rusty patch on abdomen, critically endangered",
    # Add more as needed
}
