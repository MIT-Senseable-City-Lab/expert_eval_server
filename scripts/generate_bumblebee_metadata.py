#!/usr/bin/env python3
"""
Generate metadata JSON for bumblebee evaluation from synthetic images.

This script scans the GBIF_MA_BUMBLEBEES/prepared_synthetic directory
and creates the metadata JSON required by the evaluation server.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# Configuration
BUMBLEBEE_BASE = "/Users/mingyang/Desktop/Thesis/BioGen/bumblebee_bplusplus"
SYNTHETIC_IMAGES_DIR = f"{BUMBLEBEE_BASE}/GBIF_MA_BUMBLEBEES/prepared_synthetic/train"
REFERENCE_IMAGES_DIR = f"{BUMBLEBEE_BASE}/SYNTHETIC_BUMBLEBEES/references"
RESULTS_DIRS = [
    f"{BUMBLEBEE_BASE}/RESULTS_1103/synthetic_generation",
    f"{BUMBLEBEE_BASE}/RESULTS_1130/synthetic_generation",
    f"{BUMBLEBEE_BASE}/RESULTS/synthetic_generation"
]

OUTPUT_FILE = "../assets/bumblebee_images_metadata.json"

# Species name mapping (handle inconsistent naming)
SPECIES_NAME_MAP = {
    "Bombus_ternarius_Say": "Bombus ternarius",
    "Bombus_vagans_Smith": "Bombus vagans",
}


def normalize_species_name(species_dir_name):
    """Convert directory name to scientific name format."""
    if species_dir_name in SPECIES_NAME_MAP:
        return SPECIES_NAME_MAP[species_dir_name]
    # Convert Bombus_species to Bombus species
    return species_dir_name.replace("_", " ")


def load_generation_metadata(species_dir_name):
    """Load generation metadata from RESULTS directories."""
    metadata_by_filename = {}

    for results_dir in RESULTS_DIRS:
        metadata_file = f"{results_dir}/{species_dir_name}/generation_metadata.json"
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata_list = json.load(f)
                for item in metadata_list:
                    if 'image_file' in item:
                        metadata_by_filename[item['image_file']] = item
            print(f"✓ Loaded metadata for {species_dir_name} from {results_dir}")
            return metadata_by_filename

    print(f"⚠ No generation metadata found for {species_dir_name}")
    return {}


def find_reference_images(species_dir_name):
    """Find reference images for a species."""
    ref_dir = f"{REFERENCE_IMAGES_DIR}/{species_dir_name}"
    if not os.path.exists(ref_dir):
        return []

    ref_images = []
    for ext in ['.jpg', '.jpeg', '.png']:
        ref_images.extend(Path(ref_dir).glob(f"*{ext}"))

    # Return relative paths for the evaluation server
    return [f"references/{species_dir_name}/{img.name}" for img in sorted(ref_images)]


def extract_metadata_from_filename(filename):
    """Extract angle and gender from synthetic_NNN_gender_angle.png filename."""
    # Pattern: synthetic_001_female_dorsal.png
    parts = filename.replace('.png', '').split('_')
    if len(parts) >= 4:
        return {
            'number': parts[1],
            'gender': parts[2],
            'angle': parts[3]
        }
    return None


def generate_metadata():
    """Generate complete metadata JSON for all synthetic images."""
    all_metadata = {}
    image_id = 0

    species_stats = defaultdict(int)

    # Scan all species directories
    for species_dir in sorted(Path(SYNTHETIC_IMAGES_DIR).iterdir()):
        if not species_dir.is_dir():
            continue

        species_dir_name = species_dir.name
        species_scientific = normalize_species_name(species_dir_name)

        # Load generation metadata
        gen_metadata = load_generation_metadata(species_dir_name)

        # Find reference images
        ref_images = find_reference_images(species_dir_name)

        # Find all synthetic images for this species
        synthetic_images = sorted(species_dir.glob("synthetic_*.png"))

        if not synthetic_images:
            continue

        print(f"\nProcessing {species_scientific}: {len(synthetic_images)} images")

        for img_path in synthetic_images:
            filename = img_path.name

            # Extract metadata from generation_metadata.json if available
            gen_data = gen_metadata.get(filename, {})

            # Extract metadata from filename as fallback
            filename_data = extract_metadata_from_filename(filename)

            # Build metadata entry
            entry = {
                "image_path": f"bumblebees/{species_dir_name}/{filename}",
                "ground_truth": {
                    "family": "Apidae",
                    "genus": "Bombus",
                    "species": species_scientific,
                    "common_name": gen_data.get('common_name', species_scientific)
                },
                "model": "bumblebee_synthetic_v1",
                "generation_metadata": {}
            }

            # Add generation metadata if available
            if gen_data:
                entry["generation_metadata"] = {
                    "angle": gen_data.get('angle', filename_data['angle'] if filename_data else 'unknown'),
                    "gender": gen_data.get('gender', filename_data['gender'] if filename_data else 'unknown'),
                    "environmental_context": gen_data.get('environmental_context', ''),
                    "timestamp": gen_data.get('timestamp', '')
                }
            elif filename_data:
                entry["generation_metadata"] = {
                    "angle": filename_data['angle'],
                    "gender": filename_data['gender'],
                    "environmental_context": "",
                    "timestamp": ""
                }

            # Add reference images (same for all images of this species)
            if ref_images:
                entry["reference_images"] = ref_images[:5]  # Max 5 references
            else:
                entry["reference_images"] = []

            all_metadata[str(image_id)] = entry
            image_id += 1
            species_stats[species_scientific] += 1

    # Print summary
    print("\n" + "="*60)
    print("METADATA GENERATION SUMMARY")
    print("="*60)
    print(f"Total images: {image_id}")
    print(f"Species with synthetic images: {len(species_stats)}")
    print("\nBreakdown by species:")
    for species, count in sorted(species_stats.items()):
        print(f"  {species}: {count} images")

    return all_metadata


def main():
    """Main execution."""
    print("Generating bumblebee evaluation metadata...")
    print(f"Scanning: {SYNTHETIC_IMAGES_DIR}")
    print(f"References: {REFERENCE_IMAGES_DIR}")
    print()

    metadata = generate_metadata()

    # Write output
    output_path = Path(__file__).parent / OUTPUT_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✓ Metadata written to: {output_path}")
    print(f"  Total entries: {len(metadata)}")
    print("\nNext steps:")
    print("1. Copy synthetic images to eval_server/static/bumblebees/")
    print("2. Copy reference images to eval_server/static/references/")
    print("3. Review the generated metadata JSON")
    print("4. Update constants_BUMBLEBEE.py if needed")


if __name__ == "__main__":
    main()
