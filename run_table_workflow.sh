#!/usr/bin/env bash
set -euo pipefail

DATASET_MASTER="${1:-examples/synthetic/dataset_master_synthetic.csv}"
TABLES_DIR="${2:-examples/synthetic/adni_tables}"
OUTPUT_DIR="${3:-outputs}"

python scripts/04_inspect_adni_tables.py --tables-dir "$TABLES_DIR" --output-dir "$OUTPUT_DIR"
python scripts/05_build_adni_roi_suvr_table.py \
  --dataset-master "$DATASET_MASTER" \
  --tables-dir "$TABLES_DIR" \
  --output-dir "$OUTPUT_DIR"
python scripts/06_compute_robust_zscore_table.py \
  --suvr-csv "$OUTPUT_DIR/SUVR_region_table.csv" \
  --output-dir "$OUTPUT_DIR"
python scripts/07_generate_qc_features_table.py \
  --suvr-csv "$OUTPUT_DIR/SUVR_region_table.csv" \
  --zscore-csv "$OUTPUT_DIR/Zscore_table.csv" \
  --processing-log "$OUTPUT_DIR/processing_log.csv" \
  --output-dir "$OUTPUT_DIR"
python scripts/08_make_results_summary_table.py --output-dir "$OUTPUT_DIR"
python scripts/09_make_deid_exports_table.py --output-dir "$OUTPUT_DIR" --deid-dir "$OUTPUT_DIR/deid_exports"

echo "Done. Check $OUTPUT_DIR and $OUTPUT_DIR/deid_exports."
