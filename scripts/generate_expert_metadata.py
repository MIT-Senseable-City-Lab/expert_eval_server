#!/usr/bin/env python3
"""
Generate metadata JSON for expert evaluation server.

Scans local static/bumblebees/ for images and static/references/ for reference
images. Reads the manifest (bundled in assets/) for LLM judge metadata.

All paths are relative to the project root — no external dependencies.
"""

import json
import os
from pathlib import Path
from collections import Counter

# All paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "static" / "bumblebees"
REFERENCE_DIR = PROJECT_ROOT / "static" / "references"
MANIFEST_PATH = PROJECT_ROOT / "assets" / "expert_validation_manifest.json"
OUTPUT_FILE = PROJECT_ROOT / "assets" / "bumblebee_images_metadata.json"

# Mode: set via env var or defaults to "full"
# calibration = 15 images (5 per species, tier-balanced for IRR), full = all 150
MODE = os.environ.get("EVAL_MODE", "full")
CALIBRATION_PER_SPECIES = 5
TIER_PRIORITY = ["strict_pass", "borderline", "soft_fail", "hard_fail"]

SPECIES_COMMON_NAMES = {
    "Bombus_ashtoni": "Ashton Cuckoo Bumble Bee",
    "Bombus_sandersoni": "Sanderson's Bumble Bee",
    "Bombus_flavidus": "Fernald's Cuckoo Bumble Bee",
}


def parse_filename(filename):
    """Parse 'Bombus_ashtoni::0380::female::lateral_0.jpg' into components."""
    stem = filename.rsplit(".", 1)[0]
    parts = stem.split("::")
    if len(parts) != 4:
        raise ValueError(f"Unexpected filename format: {filename}")
    return {
        "species": parts[0],
        "number": parts[1],
        "caste": parts[2],
        "angle": parts[3],
    }


def find_reference_images(species_dir_name):
    """Find reference images for a species."""
    ref_dir = REFERENCE_DIR / species_dir_name
    if not ref_dir.exists():
        return []
    refs = sorted(
        p for p in ref_dir.iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )
    return [f"references/{species_dir_name}/{img.name}" for img in refs[:5]]


def load_manifest_lookup():
    """Load manifest and build filename -> entry lookup."""
    if not MANIFEST_PATH.exists():
        print(f"Warning: manifest not found at {MANIFEST_PATH}")
        print("  LLM judge metadata will be empty.")
        return {}
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    lookup = {}
    for species_data in manifest["species"].values():
        for img in species_data["images"]:
            lookup[img["file"]] = img
    return lookup


def generate_metadata():
    manifest_lookup = load_manifest_lookup()
    all_entries = []

    for species_dir in sorted(IMAGES_DIR.iterdir()):
        if not species_dir.is_dir():
            continue

        species_key = species_dir.name
        species_name = species_key.replace("_", " ")
        common_name = SPECIES_COMMON_NAMES.get(species_key, species_name)
        ref_images = find_reference_images(species_key)

        images = sorted(species_dir.glob("*.jpg"))

        for img_path in images:
            filename = img_path.name
            parsed = parse_filename(filename)
            manifest_entry = manifest_lookup.get(filename, {})

            entry = {
                "image_path": f"bumblebees/{species_key}/{filename}",
                "ground_truth": {
                    "family": "Apidae",
                    "genus": "Bombus",
                    "species": species_name,
                    "common_name": common_name,
                },
                "model": "bumblebee_synthetic_v2",
                "generation_metadata": {
                    "angle": parsed["angle"],
                    "gender": parsed["caste"],
                },
                "reference_images": ref_images,
                # LLM judge metadata (hidden from expert, used in analysis)
                "tier": manifest_entry.get("tier", ""),
                "llm_morph_mean": manifest_entry.get("morph_mean"),
                "caste_ground_truth": manifest_entry.get("caste", parsed["caste"]),
                "llm_blind_id_species": manifest_entry.get("blind_id_species", ""),
                "llm_diag_level": manifest_entry.get("diag_level", ""),
                "llm_caste_correct": manifest_entry.get("caste_correct"),
                "llm_overall_pass": manifest_entry.get("overall_pass"),
                "llm_matches_target": manifest_entry.get("matches_target"),
            }
            all_entries.append(entry)

    if MODE == "calibration":
        # Sample 5 per species, tier-balanced for inter-rater reliability
        by_species = {}
        for entry in all_entries:
            sp = entry["ground_truth"]["species"]
            by_species.setdefault(sp, []).append(entry)

        sampled = []
        for sp in sorted(by_species.keys()):
            entries = by_species[sp]
            # Group by tier within this species
            by_tier = {}
            for e in entries:
                tier = e.get("tier", "")
                by_tier.setdefault(tier, []).append(e)

            # Pick one from each available tier first, then fill remaining
            selected = []
            for tier in TIER_PRIORITY:
                if tier in by_tier and by_tier[tier] and len(selected) < CALIBRATION_PER_SPECIES:
                    selected.append(by_tier[tier].pop(0))

            # Fill remaining slots from whatever is left
            remaining = [e for tier_entries in by_tier.values() for e in tier_entries]
            for e in remaining:
                if len(selected) >= CALIBRATION_PER_SPECIES:
                    break
                if e not in selected:
                    selected.append(e)

            sampled.extend(selected)

        all_entries = sampled

    all_metadata = {str(i): entry for i, entry in enumerate(all_entries)}

    return all_metadata


def main():
    metadata = generate_metadata()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Mode: {MODE}")
    print(f"Generated {len(metadata)} entries -> {OUTPUT_FILE}")

    species_counts = Counter()
    tier_counts = Counter()
    caste_counts = Counter()
    for entry in metadata.values():
        species_counts[entry["ground_truth"]["species"]] += 1
        tier_counts[entry["tier"]] += 1
        caste_counts[entry["caste_ground_truth"]] += 1

    print("\nSpecies:")
    for sp, c in sorted(species_counts.items()):
        print(f"  {sp}: {c}")
    print("\nTiers:")
    for t, c in sorted(tier_counts.items()):
        print(f"  {t}: {c}")
    print("\nCastes:")
    for ca, c in sorted(caste_counts.items()):
        print(f"  {ca}: {c}")


if __name__ == "__main__":
    main()
