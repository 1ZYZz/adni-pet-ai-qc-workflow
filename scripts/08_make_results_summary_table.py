import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def safe_read(path):
    p = Path(path)
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="outputs")
    args = ap.parse_args()
    out = Path(args.output_dir)

    suvr = safe_read(out/"SUVR_region_table.csv")
    z = safe_read(out/"Zscore_table.csv")
    qc = safe_read(out/"QC_features.csv")
    log = safe_read(out/"processing_log.csv")

    metrics = []
    def add(metric, value):
        metrics.append({"Metric": metric, "Value": value})

    if len(log):
        add("PET processing units in log", len(log))
        add("Successful PET processing units", int((log["status"].astype(str).str.lower() == "success").sum()) if "status" in log else "")
        add("Failed PET processing units", int((log["status"].astype(str).str.lower() != "success").sum()) if "status" in log else "")
        if "status" in log:
            success = (log["status"].astype(str).str.lower() == "success").mean() * 100
            add("Processing success rate (%)", round(success, 1))
    if len(suvr):
        add("Region-level SUVR rows", len(suvr))
        add("Unique subjects with SUVR", suvr["Study_ID"].nunique())
        add("Unique scans with SUVR", suvr["Scan_ID"].nunique())
        add("Unique regions", suvr["region_name"].nunique())
    if len(qc):
        for label, n in qc["QC_label"].value_counts(dropna=False).items():
            add(f"QC {label} scans", int(n))
    if len(z):
        add("Region-level Z-score rows", len(z))
        add("Max absolute robust Z", round(float(pd.to_numeric(z["robust_Z"], errors="coerce").abs().max()), 3))

    metrics_df = pd.DataFrame(metrics)

    tracer_summary = pd.DataFrame()
    if len(qc):
        tracer_summary = qc.groupby(["tracer", "QC_label"]).size().unstack(fill_value=0).reset_index()

    source_summary = pd.DataFrame()
    if len(suvr):
        source_summary = suvr.groupby(["tracer"]).agg(
            scans=("Scan_ID","nunique"),
            subjects=("Study_ID","nunique"),
            regions=("region_name","nunique"),
            rows=("region_name","size")
        ).reset_index()

    metrics_df.to_csv(out/"Table1_metrics_for_summary.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(out/"results_summary.xlsx", engine="openpyxl") as writer:
        metrics_df.to_excel(writer, sheet_name="metrics", index=False)
        if len(tracer_summary):
            tracer_summary.to_excel(writer, sheet_name="tracer_qc_summary", index=False)
        if len(source_summary):
            source_summary.to_excel(writer, sheet_name="tracer_roi_summary", index=False)
        if len(log):
            log.to_excel(writer, sheet_name="processing_log", index=False)
        if len(qc):
            qc.to_excel(writer, sheet_name="QC_features", index=False)

    print(f"Wrote {out/'Table1_metrics_for_summary.csv'}")
    print(f"Wrote {out/'results_summary.xlsx'}")
    print(metrics_df.to_string(index=False))

if __name__ == "__main__":
    main()
