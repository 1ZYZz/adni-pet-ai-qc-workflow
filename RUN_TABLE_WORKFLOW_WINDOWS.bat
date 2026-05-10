@echo off
setlocal

set DATASET_MASTER=examples\synthetic\dataset_master_synthetic.csv
set TABLES_DIR=examples\synthetic\adni_tables
set OUTPUT_DIR=outputs

if not "%~1"=="" set DATASET_MASTER=%~1
if not "%~2"=="" set TABLES_DIR=%~2
if not "%~3"=="" set OUTPUT_DIR=%~3

echo === Step 1: Inspect source tables ===
python scripts\04_inspect_adni_tables.py --tables-dir "%TABLES_DIR%" --output-dir "%OUTPUT_DIR%"
if errorlevel 1 goto :error

echo === Step 2: Build SUVR table ===
python scripts\05_build_adni_roi_suvr_table.py --dataset-master "%DATASET_MASTER%" --tables-dir "%TABLES_DIR%" --output-dir "%OUTPUT_DIR%"
if errorlevel 1 goto :error

echo === Step 3: Compute robust Z-score ===
python scripts\06_compute_robust_zscore_table.py --suvr-csv "%OUTPUT_DIR%\SUVR_region_table.csv" --output-dir "%OUTPUT_DIR%"
if errorlevel 1 goto :error

echo === Step 4: Generate QC features ===
python scripts\07_generate_qc_features_table.py --suvr-csv "%OUTPUT_DIR%\SUVR_region_table.csv" --zscore-csv "%OUTPUT_DIR%\Zscore_table.csv" --processing-log "%OUTPUT_DIR%\processing_log.csv" --output-dir "%OUTPUT_DIR%"
if errorlevel 1 goto :error

echo === Step 5: Make summary ===
python scripts\08_make_results_summary_table.py --output-dir "%OUTPUT_DIR%"
if errorlevel 1 goto :error

echo === Step 6: Make deidentified exports ===
python scripts\09_make_deid_exports_table.py --output-dir "%OUTPUT_DIR%" --deid-dir "%OUTPUT_DIR%\deid_exports"
if errorlevel 1 goto :error

echo DONE. Check %OUTPUT_DIR% and %OUTPUT_DIR%\deid_exports.
goto :eof

:error
echo ERROR occurred. Please check messages above.
exit /b 1
