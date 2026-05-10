import argparse
from pathlib import Path
import pandas as pd
import json

def read_csv_flexible(path: Path) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "latin1", "gbk"]:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            pass
    return pd.read_csv(path, low_memory=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables-dir", default="adni_tables")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    tables_dir = Path(args.tables_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    csvs = sorted(tables_dir.glob("*.csv"))
    if not csvs:
        raise SystemExit(f"No CSV files found in {tables_dir.resolve()}")

    rows = []
    previews = {}
    for p in csvs:
        df = read_csv_flexible(p)
        cols = list(df.columns)
        rows.append({
            "file": p.name,
            "rows": len(df),
            "columns": len(cols),
            "column_names": " | ".join(cols),
            "has_RID": "RID" in cols,
            "has_VISCODE": "VISCODE" in cols,
            "has_VISCODE2": "VISCODE2" in cols,
            "has_EXAMDATE": "EXAMDATE" in cols,
            "has_IMAGEUID_or_UID": any(c.upper() in ["IMAGEUID","UID","LONIUID"] for c in cols),
            "possible_region_cols": " | ".join([c for c in cols if c.upper() in ["ROINAME","ROI","REGION","REGION_NAME","BRAIN_REGION","MASKNAME"]]),
            "possible_value_cols": " | ".join([c for c in cols if c.upper() in ["MEAN","SUVR","SUMMARYSUVR","VALUE","CTX_LH","CTX_RH"] or "SUVR" in c.upper()])
        })
        previews[p.stem[:31]] = df.head(20)

    pd.DataFrame(rows).to_csv(out/"table_column_report.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(out/"table_preview_report.xlsx", engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="column_report", index=False)
        for name, df in previews.items():
            df.to_excel(writer, sheet_name=name, index=False)

    print(f"Wrote {out/'table_column_report.csv'}")
    print(f"Wrote {out/'table_preview_report.xlsx'}")
    print("Detected files:")
    for r in rows:
        print(f"  {r['file']}: {r['rows']} rows, {r['columns']} columns")

if __name__ == "__main__":
    main()
