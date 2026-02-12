# Bumblebee Evaluation Database - Query Examples

## Basic Queries

### Count total evaluations
```bash
sqlite3 instance/bumblebee_evaluation_prod.db \
  "SELECT COUNT(*) as total FROM insect_evaluation;"
```

### View latest 5 evaluations (summary)
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    id,
    image_index,
    ground_truth_species,
    blind_id_species,
    diagnostic_level,
    datetime
FROM insect_evaluation
ORDER BY id DESC
LIMIT 5;
"
```

### View complete data for specific evaluation
```bash
sqlite3 -header -line instance/bumblebee_evaluation_prod.db \
  "SELECT * FROM insect_evaluation WHERE id = 5;"
```

---

## Analysis Queries

### Average morphology scores
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    AVG(morph_legs_appendages) as avg_legs,
    AVG(morph_wing_venation_texture) as avg_wings,
    AVG(morph_head_antennae) as avg_head,
    AVG(morph_abdomen_banding) as avg_abdomen,
    AVG(morph_thorax_coloration) as avg_thorax,
    AVG(morph_wing_pit_markings) as avg_wing_pits
FROM insect_evaluation;
"
```

### Blind ID accuracy by taxonomic level
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    SUM(CASE WHEN blind_id_family = ground_truth_family THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as family_accuracy_pct,
    SUM(CASE WHEN blind_id_genus = ground_truth_genus THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as genus_accuracy_pct,
    SUM(CASE WHEN blind_id_species = ground_truth_species THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as species_accuracy_pct
FROM insect_evaluation;
"
```

### Average timing per stage
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    AVG(time_stage1) as avg_stage1_seconds,
    AVG(time_stage2) as avg_stage2_seconds,
    AVG(time_stage1 + time_stage2) as avg_total_seconds
FROM insect_evaluation;
"
```

### Diagnostic level distribution
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    diagnostic_level,
    COUNT(*) as count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM insect_evaluation) as percentage
FROM insect_evaluation
GROUP BY diagnostic_level
ORDER BY count DESC;
"
```

### Most common failure modes
```bash
sqlite3 instance/bumblebee_evaluation_prod.db "
SELECT failure_modes, COUNT(*) as count
FROM insect_evaluation
GROUP BY failure_modes
ORDER BY count DESC;
"
```

### Evaluations by species
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    ground_truth_species,
    COUNT(*) as evaluations,
    AVG(morph_legs_appendages + morph_wing_venation_texture + morph_head_antennae +
        morph_abdomen_banding + morph_thorax_coloration + morph_wing_pit_markings) / 6.0 as avg_morphology_score
FROM insect_evaluation
GROUP BY ground_truth_species
ORDER BY evaluations DESC;
"
```

### Evaluations by angle and gender
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    generation_angle,
    generation_gender,
    COUNT(*) as count,
    AVG(time_stage1 + time_stage2) as avg_time
FROM insect_evaluation
GROUP BY generation_angle, generation_gender
ORDER BY count DESC;
"
```

---

## User Progress Queries

### Check user status
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    prolific_pid,
    subset_id,
    done,
    datetime_started,
    datetime_completed
FROM evaluation_users;
"
```

### User progress (how many images completed)
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    u.prolific_pid,
    u.subset_id,
    COUNT(e.id) as images_completed,
    u.done
FROM evaluation_users u
LEFT JOIN insect_evaluation e ON u.prolific_pid = e.prolific_pid
GROUP BY u.prolific_pid;
"
```

### Evaluations per user
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    prolific_pid,
    COUNT(*) as total_evaluations,
    MIN(datetime) as first_evaluation,
    MAX(datetime) as last_evaluation
FROM insect_evaluation
GROUP BY prolific_pid;
"
```

---

## Export Queries

### Export all data to CSV
```bash
sqlite3 -header -csv instance/bumblebee_evaluation_prod.db \
  "SELECT * FROM insect_evaluation ORDER BY id;" \
  > results/full_export_$(date +%Y%m%d_%H%M%S).csv
```

### Export summary for analysis
```bash
sqlite3 -header -csv instance/bumblebee_evaluation_prod.db "
SELECT
    id,
    prolific_pid,
    ground_truth_species,
    blind_id_family,
    blind_id_genus,
    blind_id_species,
    CASE WHEN blind_id_family = ground_truth_family THEN 1 ELSE 0 END as family_correct,
    CASE WHEN blind_id_genus = ground_truth_genus THEN 1 ELSE 0 END as genus_correct,
    CASE WHEN blind_id_species = ground_truth_species THEN 1 ELSE 0 END as species_correct,
    morph_legs_appendages,
    morph_wing_venation_texture,
    morph_head_antennae,
    morph_abdomen_banding,
    morph_thorax_coloration,
    morph_wing_pit_markings,
    (morph_legs_appendages + morph_wing_venation_texture + morph_head_antennae +
     morph_abdomen_banding + morph_thorax_coloration + morph_wing_pit_markings) / 6.0 as avg_morphology,
    diagnostic_level,
    failure_modes,
    time_stage1,
    time_stage2,
    time_stage1 + time_stage2 as total_time,
    generation_angle,
    generation_gender
FROM insect_evaluation
ORDER BY id;
" > results/analysis_export_$(date +%Y%m%d_%H%M%S).csv
```

### Export morphology scores only
```bash
sqlite3 -header -csv instance/bumblebee_evaluation_prod.db "
SELECT
    image_path,
    ground_truth_species,
    morph_legs_appendages,
    morph_wing_venation_texture,
    morph_head_antennae,
    morph_abdomen_banding,
    morph_thorax_coloration,
    morph_wing_pit_markings
FROM insect_evaluation;
" > results/morphology_scores.csv
```

---

## Debugging Queries

### Find evaluations with potential data issues
```bash
# Missing species ID
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT id, image_path, blind_id_species
FROM insect_evaluation
WHERE blind_id_species = '' OR blind_id_species = 'Unknown';
"

# Very fast evaluations (< 10 seconds total)
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT id, prolific_pid, time_stage1 + time_stage2 as total_time, datetime
FROM insect_evaluation
WHERE time_stage1 + time_stage2 < 10
ORDER BY total_time;
"

# Very slow evaluations (> 120 seconds)
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT id, prolific_pid, time_stage1 + time_stage2 as total_time, datetime
FROM insect_evaluation
WHERE time_stage1 + time_stage2 > 120
ORDER BY total_time DESC;
"
```

---

## Python Analysis (Alternative)

If you prefer Python for analysis:

```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('instance/bumblebee_evaluation_prod.db')

# Load all data
df = pd.read_sql_query("SELECT * FROM insect_evaluation", conn)

# Quick stats
print("Total evaluations:", len(df))
print("\nMorphology score averages:")
print(df[['morph_legs_appendages', 'morph_wing_venation_texture',
          'morph_head_antennae', 'morph_abdomen_banding',
          'morph_thorax_coloration', 'morph_wing_pit_markings']].mean())

print("\nDiagnostic level distribution:")
print(df['diagnostic_level'].value_counts())

print("\nSpecies distribution:")
print(df['ground_truth_species'].value_counts())

# Calculate accuracy
df['family_correct'] = df['blind_id_family'] == df['ground_truth_family']
df['genus_correct'] = df['blind_id_genus'] == df['ground_truth_genus']
df['species_correct'] = df['blind_id_species'] == df['ground_truth_species']

print("\nBlind ID accuracy:")
print(f"Family: {df['family_correct'].mean() * 100:.1f}%")
print(f"Genus: {df['genus_correct'].mean() * 100:.1f}%")
print(f"Species: {df['species_correct'].mean() * 100:.1f}%")

# Export
df.to_csv('results/analysis_pandas.csv', index=False)

conn.close()
```

---

## Common Use Cases

### 1. Check if user completed study
```bash
PROLIFIC_PID="test123"
sqlite3 instance/bumblebee_evaluation_prod.db \
  "SELECT done FROM evaluation_users WHERE prolific_pid = '$PROLIFIC_PID';"
```

### 2. Get user's current progress
```bash
PROLIFIC_PID="test123"
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    u.prolific_pid,
    COUNT(e.id) as completed,
    50 - COUNT(e.id) as remaining
FROM evaluation_users u
LEFT JOIN insect_evaluation e ON u.prolific_pid = e.prolific_pid
WHERE u.prolific_pid = '$PROLIFIC_PID'
GROUP BY u.prolific_pid;
"
```

### 3. Quality check: Find duplicate evaluations
```bash
sqlite3 -header -column instance/bumblebee_evaluation_prod.db "
SELECT
    prolific_pid,
    absolute_image_index,
    COUNT(*) as times_evaluated
FROM insect_evaluation
GROUP BY prolific_pid, absolute_image_index
HAVING COUNT(*) > 1;
"
```
