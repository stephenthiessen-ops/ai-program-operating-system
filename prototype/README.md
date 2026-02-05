# Prototype — Executive Summary Agent (Working Example)

This prototype generates a 1-page executive brief from a structured weekly snapshot (synthetic or real).

## Run locally

```bash
python3 prototype/generate_exec_brief.py \
  --input prototype/sample_snapshot.json \
  --output outputs/exec-brief_SAMPLE.md

## CSV -> Snapshot -> Executive Brief (recommended demo)

### Step 1: Transform CSV into snapshot JSON
```bash
python3 prototype/transform_jira_csv_to_snapshot.py \
  --input prototype/jira_export_SAMPLE.csv \
  --output prototype/snapshot_from_csv.json \
  --week-ending 2026-02-06
