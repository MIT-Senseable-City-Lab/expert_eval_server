#!/bin/bash
# Setup script for bumblebee evaluation data
# Copies synthetic images and reference images to eval_server static directory

set -e  # Exit on error

BUMBLEBEE_BASE="/Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus"
SOURCE_IMAGES="$BUMBLEBEE_BASE/GBIF_MA_BUMBLEBEES/prepared_synthetic/train"
SOURCE_REFS="$BUMBLEBEE_BASE/SYNTHETIC_BUMBLEBEES/references"

# Navigate to eval_server directory
cd "$(dirname "$0")/.."

echo "================================================"
echo "Bumblebee Evaluation Data Setup"
echo "================================================"
echo ""
echo "Source synthetic images: $SOURCE_IMAGES"
echo "Source references: $SOURCE_REFS"
echo "Target directory: $(pwd)/static"
echo ""

# Create directories
echo "Creating directory structure..."
mkdir -p static/bumblebees
mkdir -p static/references

# Species with synthetic images
SPECIES=("Bombus_ashtoni" "Bombus_sandersoni" "Bombus_ternarius_Say")

# Copy synthetic images
echo ""
echo "Copying synthetic images..."
for species in "${SPECIES[@]}"; do
    if [ -d "$SOURCE_IMAGES/$species" ]; then
        echo "  ✓ Copying $species images..."
        cp -r "$SOURCE_IMAGES/$species" static/bumblebees/
    else
        echo "  ⚠ $species not found in source directory"
    fi
done

# Copy reference images
echo ""
echo "Copying reference images..."
for species in "${SPECIES[@]}"; do
    if [ -d "$SOURCE_REFS/$species" ]; then
        echo "  ✓ Copying $species references..."
        cp -r "$SOURCE_REFS/$species" static/references/
    else
        echo "  ⚠ $species references not found"
    fi
done

# Verification
echo ""
echo "================================================"
echo "Verification"
echo "================================================"
echo ""
echo "Synthetic images per species:"
for species in "${SPECIES[@]}"; do
    if [ -d "static/bumblebees/$species" ]; then
        count=$(find "static/bumblebees/$species" -name "synthetic_*.png" 2>/dev/null | wc -l | tr -d ' ')
        echo "  $species: $count images"
    fi
done

echo ""
echo "Reference images per species:"
for species in "${SPECIES[@]}"; do
    if [ -d "static/references/$species" ]; then
        count=$(find "static/references/$species" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) 2>/dev/null | wc -l | tr -d ' ')
        echo "  $species: $count images"
    fi
done

# Check metadata
echo ""
if [ -f "assets/bumblebee_images_metadata.json" ]; then
    echo "Metadata JSON: ✓ Found"
    metadata_count=$(python3 -c "import json; data = json.load(open('assets/bumblebee_images_metadata.json')); print(len(data))" 2>/dev/null || echo "?")
    echo "  Total entries: $metadata_count"
else
    echo "Metadata JSON: ✗ Not found"
    echo ""
    echo "Run metadata generation:"
    echo "  python3 scripts/generate_bumblebee_metadata.py"
fi

echo ""
echo "================================================"
echo "✓ Data setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Verify the counts above match expectations"
echo "2. If metadata JSON not found, run:"
echo "   python3 scripts/generate_bumblebee_metadata.py"
echo "3. Update app.py with new models"
echo "4. Create evaluation template"
echo ""
