import argparse
from pathlib import Path
import re
import pandas as pd
import numpy as np

TRACER_KEYWORDS = {
    "FDG": ["fdg"],
    "Amyloid": ["amy", "amyloid", "av45", "fbb", "florbetapir", "florbetaben", "ucberkeley_amy", "ucberkeleyamy"],
    "Tau": ["tau", "av1451", "flortaucipir"]
}

REGION_COL_CANDIDATES = ["ROINAME", "ROI", "REGION", "REGION_NAME", "BRAIN_REGION", "MASKNAME"]
VALUE_COL_CANDIDATES = ["MEAN", "SUVR", "SUMMARYSUVR", "VALUE", "SUVR_MEAN", "NORM_MEAN"]
IMAGE_COL_CANDIDATES = ["IMAGEUID", "UID", "LONIUID", "IMAGE_ID", "Image_ID"]
DATE_COL_CANDIDATES = ["EXAMDATE", "SCANDATE", "SCAN_DATE", "DATE"]
VISIT_COL_CANDIDATES = ["VISCODE2", "VISCODE", "VISIT", "Visit"]
RID_COL_CANDIDATES = ["RID", "rid"]

# Wide PET tables: keep true SUVR columns only.
# Exclude volumes, warnings, status, centiloids, and other non-region columns.
def is_valid_wide_suvr_column(c: str) -> bool:
    cu = str(c).upper()
    if not cu.endswith("_SUVR"):
        return False
    bad_tokens = ["WARNING", "STATUS", "VOLUME", "QC", "FLAG"]
    if any(tok in cu for tok in bad_tokens):
        return False
    return True

def read_csv_flexible(path: Path) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "latin1", "gbk"]:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            pass
    return pd.read_csv(path, low_memory=False)

def find_col(df, candidates, contains=None):
    cols = list(df.columns)
    upper = {str(c).upper(): c for c in cols}
    for cand in candidates:
        if cand.upper() in upper:
            return upper[cand.upper()]
    if contains:
        for c in cols:
            cu = str(c).upper()
            if any(x.upper() in cu for x in contains):
                return c
    return None

def parse_rid(adni_subject_id):
    m = re.search(r"_S_(\d+)", str(adni_subject_id))
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)$", str(adni_subject_id))
    return int(m.group(1)) if m else np.nan

def normalize_image_id(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    s = re.sub(r"\.0$", "", s)
    s = s.replace("I", "").replace("i", "")
    return s

def choose_files(tables_dir, fdg, amyloid, tau):
    if fdg and amyloid and tau:
        return {"FDG": Path(fdg), "Amyloid": Path(amyloid), "Tau": Path(tau)}
    csvs = sorted(Path(tables_dir).glob("*.csv"))
    chosen = {}
    for tracer, kws in TRACER_KEYWORDS.items():
        matches = [p for p in csvs if any(k in p.name.lower() for k in kws)]
        if matches:
            matches = sorted(matches, key=lambda p: (("berkeley" not in p.name.lower()), len(p.name)))
            chosen[tracer] = matches[0]
    return chosen

def detect_long_or_wide(df, tracer):
    # FDG UC Berkeley table is long: ROINAME + MEAN.
    region_col = find_col(df, REGION_COL_CANDIDATES)
    if tracer == "FDG":
        value_col = "MEAN" if "MEAN" in df.columns else find_col(df, VALUE_COL_CANDIDATES)
        if region_col and value_col:
            return "long", region_col, value_col

    # Amyloid/Tau UC Berkeley 6mm tables are wide with many *_SUVR columns.
    suvr_cols = [c for c in df.columns if is_valid_wide_suvr_column(c)]
    if suvr_cols:
        return "wide_suvr_only", None, None

    # fallback long table if available
    value_col = find_col(df, VALUE_COL_CANDIDATES, contains=["SUVR"])
    if region_col and value_col:
        return "long", region_col, value_col

    return "unknown", region_col, value_col

def load_dataset_master(path: Path):
    """Load a locked cohort file.

    The original manuscript workflow used an Excel workbook with sheets
    named `scan_level` and `subject_level`. For public reproducibility, this
    version also accepts a single CSV file containing the scan-level columns.
    Required scan-level columns are:
    Study_ID, Scan_ID, ADNI_Subject_ID, Image_ID, Visit, Scan_Date, Modality, Tracer.
    """
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        scan = pd.read_excel(path, sheet_name="scan_level")
        try:
            subj = pd.read_excel(path, sheet_name="subject_level")
        except Exception:
            subj = pd.DataFrame()
    elif suffix == ".csv":
        scan = pd.read_csv(path)
        subj = pd.DataFrame()
    else:
        raise ValueError(f"Unsupported dataset master format: {path}. Use .xlsx or .csv")

    required = ["Study_ID", "Scan_ID", "ADNI_Subject_ID", "Image_ID", "Visit", "Scan_Date", "Modality", "Tracer"]
    missing = [c for c in required if c not in scan.columns]
    if missing:
        raise ValueError("Missing required columns in dataset master: " + ", ".join(missing))

    scan["RID"] = scan["ADNI_Subject_ID"].apply(parse_rid)
    scan["Image_ID_norm"] = scan["Image_ID"].apply(normalize_image_id)
    scan["Scan_Date_dt"] = pd.to_datetime(scan["Scan_Date"], errors="coerce")
    pet = scan[scan["Modality"].astype(str).str.upper().eq("PET")].copy()
    pet["Tracer_norm"] = pet["Tracer"].replace({"Amyloid":"Amyloid", "Tau":"Tau", "FDG":"FDG"})
    return pet, subj

def match_rows(table, scan_row):
    df = table.copy()
    rid_col = find_col(df, RID_COL_CANDIDATES)
    img_col = find_col(df, IMAGE_COL_CANDIDATES)
    date_col = find_col(df, DATE_COL_CANDIDATES)
    visit_col = find_col(df, VISIT_COL_CANDIDATES)

    candidates = df
    strategy = []

    if rid_col:
        candidates = candidates[pd.to_numeric(candidates[rid_col], errors="coerce") == scan_row["RID"]]
        strategy.append("RID")

    if img_col and scan_row.get("Image_ID_norm"):
        uid = scan_row["Image_ID_norm"]
        cand2 = candidates[candidates[img_col].apply(normalize_image_id) == uid]
        if len(cand2) > 0:
            strategy.append("IMAGEUID")
            return cand2, "+".join(strategy)

    if date_col and pd.notna(scan_row.get("Scan_Date_dt")):
        dates = pd.to_datetime(candidates[date_col], errors="coerce")
        target = scan_row["Scan_Date_dt"]
        cand2 = candidates[dates == target]
        if len(cand2) > 0:
            strategy.append(date_col)
            return cand2, "+".join(strategy)

    if visit_col and pd.notna(scan_row.get("Visit")):
        visit = str(scan_row["Visit"]).lower()
        cand2 = candidates[candidates[visit_col].astype(str).str.lower().eq(visit)]
        if len(cand2) > 0:
            strategy.append("VISIT")
            return cand2, "+".join(strategy)

    if len(candidates) > 0:
        strategy.append("RID_ONLY")
    return candidates, "+".join(strategy) if strategy else "NO_MATCH_KEY"

def infer_amyloid_tracer(scan_row):
    if str(scan_row.get("Tracer","")).lower() != "amyloid":
        return ""
    desc = str(scan_row.get("Description","")).lower()
    if "fbb" in desc or "florbetaben" in desc:
        return "FBB"
    if "av45" in desc or "florbetapir" in desc:
        return "AV45"
    return "Amyloid_unspecified"

def clean_region_name_from_wide_col(col):
    name = str(col)
    if name.upper().endswith("_SUVR"):
        name = name[:-5]
    return name

def standardize_table_for_scan(table, scan_row, tracer):
    matched, strategy = match_rows(table, scan_row)
    if len(matched) == 0:
        return pd.DataFrame(), {
            "Study_ID": scan_row["Study_ID"], "Scan_ID": scan_row["Scan_ID"],
            "tracer": tracer, "status": "fail", "reason": "no matching rows",
            "match_strategy": strategy
        }

    mode, region_col, value_col = detect_long_or_wide(matched, tracer)
    rows = []

    base = {
        "Study_ID": scan_row["Study_ID"],
        "Scan_ID": scan_row["Scan_ID"],
        "ADNI_Subject_ID_internal": scan_row["ADNI_Subject_ID"],
        "RID_internal": scan_row["RID"],
        "Image_ID_internal": scan_row["Image_ID"],
        "Visit_internal": scan_row["Visit"],
        "Scan_Date_internal": scan_row["Scan_Date"],
        "tracer": tracer,
        "amyloid_tracer": infer_amyloid_tracer(scan_row),
        "match_strategy": strategy
    }

    if mode == "long":
        for _, r in matched.iterrows():
            value = pd.to_numeric(r[value_col], errors="coerce")
            if pd.isna(value):
                continue
            row = dict(base)
            row.update({
                "region_name": str(r[region_col]),
                "SUVR": float(value),
                "source_value_column": value_col,
                "source_region_column": region_col,
                "source_table_mode": "long"
            })
            rows.append(row)

    elif mode == "wide_suvr_only":
        # If multiple rows match, use the first; IMAGEUID match should make this one row for AMY/TAU.
        r = matched.iloc[0]
        suvr_cols = [c for c in matched.columns if is_valid_wide_suvr_column(c)]
        for c in suvr_cols:
            value = pd.to_numeric(r[c], errors="coerce")
            if pd.isna(value):
                continue
            row = dict(base)
            row.update({
                "region_name": clean_region_name_from_wide_col(c),
                "SUVR": float(value),
                "source_value_column": str(c),
                "source_region_column": "wide_suvr_column",
                "source_table_mode": "wide_suvr_only"
            })
            rows.append(row)
    else:
        return pd.DataFrame(), {
            "Study_ID": scan_row["Study_ID"], "Scan_ID": scan_row["Scan_ID"],
            "tracer": tracer, "status": "fail",
            "reason": "cannot detect ROI/value columns",
            "match_strategy": strategy
        }

    status = "success" if rows else "fail"
    reason = "ok" if rows else "matched rows but no numeric ROI/SUVR values"
    return pd.DataFrame(rows), {
        "Study_ID": scan_row["Study_ID"], "Scan_ID": scan_row["Scan_ID"],
        "tracer": tracer, "status": status, "reason": reason,
        "match_strategy": strategy, "n_regions": len(rows),
        "n_matched_source_rows": len(matched), "table_mode": mode
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-master", required=True)
    ap.add_argument("--tables-dir", default="adni_tables")
    ap.add_argument("--fdg")
    ap.add_argument("--amyloid")
    ap.add_argument("--tau")
    ap.add_argument("--output-dir", default="outputs")
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pet, subj = load_dataset_master(Path(args.dataset_master))
    chosen = choose_files(args.tables_dir, args.fdg, args.amyloid, args.tau)

    missing = [t for t in ["FDG", "Amyloid", "Tau"] if t not in chosen]
    if missing:
        raise SystemExit(f"Could not identify CSV file(s) for: {missing}. Use --fdg --amyloid --tau to specify manually.")

    tables = {}
    for tracer, path in chosen.items():
        tables[tracer] = read_csv_flexible(path)
        print(f"{tracer}: using {path} with {len(tables[tracer])} rows and {len(tables[tracer].columns)} columns")

    all_rows = []
    logs = []
    debug = []

    for _, scan in pet.iterrows():
        tracer = scan["Tracer_norm"]
        if tracer not in tables:
            logs.append({"Study_ID": scan["Study_ID"], "Scan_ID": scan["Scan_ID"], "tracer": tracer, "status": "fail", "reason": "no source table"})
            continue
        df_scan, log = standardize_table_for_scan(tables[tracer], scan, tracer)
        logs.append(log)
        if len(df_scan):
            all_rows.append(df_scan)
        debug.append({
            "Study_ID": scan["Study_ID"],
            "Scan_ID": scan["Scan_ID"],
            "tracer": tracer,
            "RID": scan["RID"],
            "Image_ID": scan["Image_ID"],
            "Visit": scan["Visit"],
            "Scan_Date": scan["Scan_Date"],
            "status": log.get("status"),
            "reason": log.get("reason"),
            "match_strategy": log.get("match_strategy"),
            "table_mode": log.get("table_mode"),
            "n_regions": log.get("n_regions", 0),
            "n_matched_source_rows": log.get("n_matched_source_rows", 0)
        })

    if not all_rows:
        raise SystemExit("No ROI/SUVR rows were produced. Check source table columns.")

    suvr = pd.concat(all_rows, ignore_index=True)

    # Add an analysis flag for summary/composite regions versus ROI columns.
    suvr["region_category"] = np.where(
        suvr["region_name"].astype(str).str.upper().isin(["SUMMARY", "META_TEMPORAL", "WHOLECEREBELLUM", "COMPOSITE_REF", "CEREBELLUM_CORTEX", "INFERIORCEREBELLUM"]),
        "summary_or_reference",
        "regional"
    )

    suvr.to_csv(out/"SUVR_region_table.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(logs).to_csv(out/"processing_log.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(debug).to_csv(out/"match_debug_report.csv", index=False, encoding="utf-8-sig")

    print(f"Wrote {out/'SUVR_region_table.csv'} rows={len(suvr)}")
    print(f"Wrote {out/'processing_log.csv'}")
    print(f"Wrote {out/'match_debug_report.csv'}")
    print("Processing status counts:")
    print(pd.DataFrame(logs)["status"].value_counts(dropna=False).to_string())
    print("Region count by tracer:")
    print(pd.DataFrame(debug).groupby("tracer")["n_regions"].describe().to_string())

if __name__ == "__main__":
    main()
