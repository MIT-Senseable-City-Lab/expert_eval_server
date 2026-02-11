import json
import random
from constants import *
import pandas as pd
from datetime import datetime

def build_repack_manifest(
    all_abs_ids,
    exclude_abs_ids=None,
    group_size=PAIRS_PER_USER,
    seed=42,
    version="v2_repack"
):
    """
    Create a manifest mapping kept absolute_pair_index -> new subset layout.
    Keeps absolute IDs immutable; only defines new_subset_id/new_pair_index.
    """
    exclude_abs_ids = set(exclude_abs_ids or [])
    kept = [i for i in sorted(all_abs_ids) if i not in exclude_abs_ids]
    total = len(all_abs_ids)
    removed = len(exclude_abs_ids.intersection(all_abs_ids))
    kept_n = len(kept)

    if not kept:
        raise ValueError("No pairs left after exclusion!")

    rng = random.Random(seed)
    rng.shuffle(kept)

    df = pd.DataFrame({"absolute_pair_index": kept})
    df["new_subset_id"] = df.index // group_size
    df["new_pair_index"] = df.index % group_size
    df.insert(0, "version", version)
    df["created_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # Logging summary
    num_subsets = df["new_subset_id"].nunique()
    print(f"🔢 build_repack_manifest | Total: {total:,} | Omitted: {removed:,} | Kept: {kept_n:,}")
    print(f"📦 Creating {num_subsets} subsets × {group_size} pairs each (version: {version})")

    return df


def load_identity_assets():
    """Load instance pairs and sentinel data for identity evaluation"""
    
    # Load instance pairs (unique instances)
    with open("assets/instance_pairs_round1_baseline_vs_custom.json", 'r') as f:
        instance_pairs_data = json.load(f)
    
    # Load explicit pairs
    with open("assets/pairs_round1_baseline_vs_custom.json", 'r') as f:
        pairs_data = json.load(f)
    
    # Load reference images
    try:
        with open("assets/reference_images.json", 'r') as f:
            reference_images_data = json.load(f)
            # Filter out special keys that start with underscore
            reference_images_data = {k: v for k, v in reference_images_data.items() if not k.startswith('_')}
    except FileNotFoundError:
        print("Warning: reference_images.json not found. No reference images will be displayed.")
        reference_images_data = {}
    
    # Load text prompts
    try:
        with open("assets/text_prompts.json", 'r') as f:
            text_prompts_data = json.load(f)
            # Filter out special keys that start with underscore
            text_prompts_data = {k: v for k, v in text_prompts_data.items() if not k.startswith('_')}
    except FileNotFoundError:
        print("Warning: text_prompts.json not found. No text prompts will be displayed.")
        text_prompts_data = {}
    
    # # Load sentinels
    # with open("assets/sentinels_ss200k.json", 'r') as f:
    #     sentinels_data = json.load(f)
    
    # Convert pairs to list format with absolute index tracking
    instance_pairs = []
    for absolute_index, pair in enumerate(pairs_data):
        instance_a_id, instance_b_id = pair
        # Store as [images_a, images_b, metadata]
        pair_data = {
            'images_a': instance_pairs_data[instance_a_id],
            'images_b': instance_pairs_data[instance_b_id],
            'absolute_index': absolute_index,
            'instance_a_id': instance_a_id,
            'instance_b_id': instance_b_id,
            'is_sentinel': False,
            'reference_images': reference_images_data.get(str(absolute_index), [])[:MAX_REFERENCE_IMAGES],
            'text_prompt': text_prompts_data.get(str(absolute_index), '')
        }
        instance_pairs.append(pair_data)
    
    # Convert sentinels to list format with metadata
    sentinels = []
    # for key, value in sentinels_data.items():
    #     sentinel_data = {
    #         'images_a': value[0],
    #         'images_b': value[1],
    #         'ground_truth': value[2],
    #         'sentinel_key': key,
    #         'is_sentinel': True,
    #         'absolute_index': -1  # Sentinels don't have absolute indices in pairs_data
    #     }
    #     sentinels.append(sentinel_data)
    
    return instance_pairs, sentinels

def add_sentinels_to_pairs(instance_pairs, sentinels):
    """Add sentinel pairs randomly to the instance pairs"""
    result_pairs = instance_pairs[:]
    
    for sentinel_pair in sentinels:
        index = random.randint(0, len(result_pairs))
        result_pairs.insert(index, sentinel_pair)
    
    return result_pairs

def create_subsets(instance_pairs, sentinels):
    """Create subsets of pairs for different users"""
    subsets = {}
    pairs_per_subset = PAIRS_PER_USER
    
    # Calculate number of subsets needed
    num_subsets = (len(instance_pairs) + pairs_per_subset - 1) // pairs_per_subset
    
    for subset_id in range(num_subsets):
        start_idx = subset_id * pairs_per_subset
        end_idx = min(start_idx + pairs_per_subset, len(instance_pairs))
        
        # Get pairs for this subset
        subset_pairs = instance_pairs[start_idx:end_idx]
        
        # Add sentinels only if NUM_SENTINELS > 0
        if NUM_SENTINELS > 0:
            # Randomly sample NUM_SENTINELS sentinels for this subset
            sampled_sentinels = random.sample(sentinels, min(NUM_SENTINELS, len(sentinels)))
            subset_pairs = add_sentinels_to_pairs(subset_pairs, sampled_sentinels)
        
        # Randomly shuffle left/right images for each pair
        for pair in subset_pairs:
            # Randomly decide whether to swap images_a and images_b
            should_shuffle = random.choice([True, False])
            pair['is_shuffled'] = should_shuffle
            if should_shuffle:
                # Swap images_a and images_b
                pair['images_a'], pair['images_b'] = pair['images_b'], pair['images_a']
                # Also swap the instance IDs if they exist (not for sentinels)
                if not pair['is_sentinel']:
                    pair['instance_a_id'], pair['instance_b_id'] = pair['instance_b_id'], pair['instance_a_id']
                # Note: reference_images stay the same (they're for the entire pair, not instance-specific)
        
        subsets[subset_id] = subset_pairs
    
    return subsets


