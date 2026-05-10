import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def robust_mad(x):
    med = np.nanmedian(x)
    mad = np.nanmedian(np.abs(x - med))
    return med, mad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suvr-csv", required=True)
    ap.add_argument("--output-dir", default="outputs")
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.suvr_csv)
    df["SUVR"] = pd.to_numeric(df["SUVR"], errors="coerce")

    stats = []
    z_rows = []
    for (tracer, region), g in df.groupby(["tracer", "region_name"], dropna=False):
        vals = g["SUVR"].to_numpy(dtype=float)
        med, mad = robust_mad(vals)
        denom = 1.4826 * mad
        if not np.isfinite(denom) or denom == 0:
            mean = np.nanmean(vals)
            sd = np.nanstd(vals, ddof=1)
            denom = sd if np.isfinite(sd) and sd > 0 else np.nan
            center = mean
            method = "mean_sd_fallback"
        else:
            center = med
            method = "median_mad"
        stats.append({
            "tracer": tracer,
            "region_name": region,
            "n": int(np.sum(np.isfinite(vals))),
            "median": med,
            "MAD": mad,
            "center_used": center,
            "denominator_used": denom,
            "method": method
        })
        gg = g.copy()
        if np.isfinite(denom) and denom > 0:
            gg["robust_Z"] = (gg["SUVR"] - center) / denom
        else:
            gg["robust_Z"] = np.nan
        gg["zscore_method"] = method
        z_rows.append(gg)

    z = pd.concat(z_rows, ignore_index=True)
    stats_df = pd.DataFrame(stats)
    z.to_csv(out/"Zscore_table.csv", index=False, encoding="utf-8-sig")
    stats_df.to_csv(out/"Zscore_reference_stats.csv", index=False, encoding="utf-8-sig")

    print(f"Wrote {out/'Zscore_table.csv'} rows={len(z)}")
    print(f"Wrote {out/'Zscore_reference_stats.csv'}")

if __name__ == "__main__":
    main()
