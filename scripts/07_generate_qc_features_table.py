import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suvr-csv", required=True)
    ap.add_argument("--zscore-csv", required=True)
    ap.add_argument("--processing-log", required=True)
    ap.add_argument("--output-dir", default="outputs")
    ap.add_argument("--review-z", type=float, default=2.5)
    ap.add_argument("--fail-z", type=float, default=4.0)
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    suvr = pd.read_csv(args.suvr_csv)
    z = pd.read_csv(args.zscore_csv)
    log = pd.read_csv(args.processing_log)

    z["robust_Z"] = pd.to_numeric(z["robust_Z"], errors="coerce")
    suvr["SUVR"] = pd.to_numeric(suvr["SUVR"], errors="coerce")

    # Scan-level QC from ROI table
    rows = []
    for (study, scan, tracer), g in z.groupby(["Study_ID", "Scan_ID", "tracer"], dropna=False):
        absz = g["robust_Z"].abs()
        n_regions = g["region_name"].nunique()
        n_valid = g["SUVR"].notna().sum() if "SUVR" in g else len(g)
        extreme_review = int((absz >= args.review_z).sum())
        extreme_fail = int((absz >= args.fail_z).sum())
        missing_suvr = int(g["SUVR"].isna().sum()) if "SUVR" in g else 0

        label = "pass"
        reasons = []
        if n_regions == 0 or n_valid == 0:
            label = "failed_processing"
            reasons.append("no valid ROI values")
        if missing_suvr > 0:
            label = "moderate_review" if label == "pass" else label
            reasons.append("missing SUVR values")
        if extreme_fail > 0:
            label = "extreme_review"  # robust Z is for triage support, not diagnosis
            reasons.append(f"robust |Z| >= {args.fail_z}")
        elif extreme_review > 0 and label == "pass":
            label = "moderate_review"
            reasons.append(f"robust |Z| >= {args.review_z}")

        amy = ""
        if "amyloid_tracer" in g.columns:
            amy_vals = [x for x in g["amyloid_tracer"].dropna().unique() if str(x).strip()]
            amy = amy_vals[0] if amy_vals else ""

        rows.append({
            "Study_ID": study,
            "Scan_ID": scan,
            "tracer": tracer,
            "amyloid_tracer": amy,
            "n_regions": n_regions,
            "n_valid_suvr": int(n_valid),
            "missing_suvr_values": missing_suvr,
            "extreme_z_review_count": extreme_review,
            "extreme_z_fail_count": extreme_fail,
            "max_abs_robust_Z": float(absz.max()) if len(absz.dropna()) else np.nan,
            "QC_label": label,
            "review_reason": "; ".join(reasons) if reasons else "none"
        })

    qc = pd.DataFrame(rows)

    # Add failed scans from processing log
    if "status" in log.columns:
        failed = log[log["status"].astype(str).str.lower() != "success"].copy()
        add = []
        existing = set(zip(qc["Study_ID"], qc["Scan_ID"], qc["tracer"]))
        for _, r in failed.iterrows():
            key = (r.get("Study_ID"), r.get("Scan_ID"), r.get("tracer"))
            if key in existing:
                continue
            add.append({
                "Study_ID": r.get("Study_ID"),
                "Scan_ID": r.get("Scan_ID"),
                "tracer": r.get("tracer"),
                "amyloid_tracer": "",
                "n_regions": 0,
                "n_valid_suvr": 0,
                "missing_suvr_values": "",
                "extreme_z_review_count": "",
                "extreme_z_fail_count": "",
                "max_abs_robust_Z": "",
                "QC_label": "failed_processing",
                "review_reason": r.get("reason", "processing failed")
            })
        if add:
            qc = pd.concat([qc, pd.DataFrame(add)], ignore_index=True)

    qc.to_csv(out/"QC_features.csv", index=False, encoding="utf-8-sig")
    print(f"Wrote {out/'QC_features.csv'} rows={len(qc)}")
    print(qc["QC_label"].value_counts(dropna=False).to_string())

if __name__ == "__main__":
    main()
