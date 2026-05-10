import argparse
from pathlib import Path
import pandas as pd

INTERNAL_COLS = {
    "ADNI_Subject_ID_internal",
    "RID_internal",
    "Image_ID_internal",
    "Visit_internal",
    "Scan_Date_internal",
    "Local_Path",
    "Path",
    "FilePath",
    "DICOMPath",
    "NIfTIPath"
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="outputs")
    ap.add_argument("--deid-dir", default="outputs/deid_exports")
    args = ap.parse_args()

    out = Path(args.output_dir)
    deid = Path(args.deid_dir)
    deid.mkdir(parents=True, exist_ok=True)

    for name in ["SUVR_region_table.csv", "Zscore_table.csv", "QC_features.csv", "Table1_metrics_for_summary.csv"]:
        p = out/name
        if not p.exists():
            continue
        df = pd.read_csv(p)
        drop_cols = [c for c in df.columns if c in INTERNAL_COLS or "internal" in c.lower() or "path" in c.lower()]
        df2 = df.drop(columns=drop_cols, errors="ignore")
        df2.to_csv(deid/name.replace(".csv","_deid.csv"), index=False, encoding="utf-8-sig")
        print(f"Wrote {deid/name.replace('.csv','_deid.csv')}")

if __name__ == "__main__":
    main()
