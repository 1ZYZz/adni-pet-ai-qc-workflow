# ADNI Multi-Tracer PET SUVR Workflow and AI-Assisted QC

This repository contains a reproducible table-based workflow for standardized multi-tracer brain PET quantification and expert-in-the-loop AI-assisted quality-control triage.

The workflow supports FDG, amyloid, and tau PET regional SUVR tables, builds a unified long-format SUVR table, computes tracer-region robust Z-scores, and generates scan-level QC labels and ranked regional drivers.

> Public-release note: This repository is designed to contain code, documentation, and synthetic example data only. Do **not** upload raw ADNI tables, locked cohort spreadsheets, scan dates, subject identifiers, individual-level derived SUVR/Z-score tables, or manuscript drafts unless your data-use agreement and journal policy explicitly allow it.

## Repository layout

```text
.
├── scripts/                         # Workflow scripts
├── examples/synthetic/              # Fake example data for testing the workflow
├── outputs/                         # Generated locally; ignored by git
├── results_public/                  # Optional aggregate manuscript-level outputs only
├── docs/                            # Chinese publishing guide and data-release notes
├── requirements.txt
├── CITATION.cff
├── LICENSE_TODO.txt
├── run_table_workflow.sh
└── RUN_TABLE_WORKFLOW_WINDOWS.bat
```

## Main workflow

1. Inspect source PET tables.
2. Match locked PET scans to source rows.
3. Extract regional and summary SUVR values into a unified long-format table.
4. Compute tracer-region robust Z-scores using median and MAD.
5. Generate scan-level QC features and triage labels.
6. Export local de-identified/filtered outputs for review.

## Quick start with synthetic data

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
./run_table_workflow.sh
```

On Windows, run:

```cmd
RUN_TABLE_WORKFLOW_WINDOWS.bat
```

Generated files will appear in `outputs/`. These files are ignored by git by default.

## Run with authorized local ADNI tables

Put your private files outside the repository, or in a local folder that is ignored by `.gitignore`, for example:

```text
private_data/
├── dataset_master_locked_YYYY-MM-DD.xlsx
└── adni_tables/
    ├── UCBERKELEYFDG_*.csv
    ├── UCBERKELEY_AMY_*.csv
    └── UCBERKELEY_TAU_*.csv
```

Then run:

```bash
./run_table_workflow.sh private_data/dataset_master_locked_YYYY-MM-DD.xlsx private_data/adni_tables outputs
```

Or on Windows:

```cmd
RUN_TABLE_WORKFLOW_WINDOWS.bat private_data\dataset_master_locked_YYYY-MM-DD.xlsx private_data\adni_tables outputs
```

## Script map

| Step | Script | Output |
|---|---|---|
| 1 | `scripts/04_inspect_adni_tables.py` | `table_column_report.csv`, `table_preview_report.xlsx` |
| 2 | `scripts/05_build_adni_roi_suvr_table.py` | `SUVR_region_table.csv`, `processing_log.csv`, `match_debug_report.csv` |
| 3 | `scripts/06_compute_robust_zscore_table.py` | `Zscore_table.csv`, `Zscore_reference_stats.csv` |
| 4 | `scripts/07_generate_qc_features_table.py` | `QC_features.csv` |
| 5 | `scripts/08_make_results_summary_table.py` | `Table1_metrics_for_summary.csv`, `results_summary.xlsx` |
| 6 | `scripts/09_make_deid_exports_table.py` | filtered local exports under `outputs/deid_exports/` |

## QC triage labels

Default thresholds:

- `pass`: all regional `|robust_Z| < 2.5`
- `moderate_review`: at least one regional `|robust_Z| >= 2.5` and all `< 4.0`
- `extreme_review`: at least one regional `|robust_Z| >= 4.0`
- `failed_processing`: no valid ROI/SUVR values or failed source-row matching

These labels are for review prioritization only, not autonomous diagnosis.

## Data policy

The synthetic files under `examples/synthetic/` are fake and safe for testing. Real ADNI source tables and individual-level derived tables should remain local unless your data-use agreement explicitly allows redistribution. See `docs/REPOSITORY_FILE_POLICY_CN.md`.
