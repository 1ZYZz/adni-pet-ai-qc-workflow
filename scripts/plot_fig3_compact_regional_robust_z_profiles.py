#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fig. 3 | Compact representative regional robust Z-score profiles

Purpose
-------
A cleaner, manuscript-friendly replacement for the long regional profile figure.
Instead of plotting every brain region, this version shows only the top abnormal
regions for each representative case, with minimal labels and no dense annotations.

Input files
-----------
Place this script in the same folder as:
1) Zscore_table_deid.csv
   Required columns: Scan_ID, tracer, region_name, SUVR, robust_Z
2) QC_features_deid.csv
   Required/expected columns: Scan_ID, QC_label, review_reason

Outputs
-------
figures/Fig3_compact_regional_robust_Z_profiles.pdf
figures/Fig3_compact_regional_robust_Z_profiles.svg
figures/Fig3_compact_regional_robust_Z_profiles.png
figures/Fig3_compact_representative_cases_used.csv

Run
---
python plot_fig3_compact_regional_robust_z_profiles.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import argparse

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# =========================
# User settings
# =========================
DATA_DIR = Path(__file__).resolve().parent
ZSCORE_CSV = DATA_DIR / "Zscore_table_deid.csv"
QC_CSV = DATA_DIR / "QC_features_deid.csv"
OUT_DIR = DATA_DIR / "figures"

# If you know the exact representative examples, fill them here.
# Example: {"Pass": "SCAN_001", "Moderate review": "SCAN_057", "Severe review": "SCAN_103"}
MANUAL_CASES: Dict[str, Optional[str]] = {
    "Pass": None,
    "Moderate review": None,
    "Severe review": None,
}

# Main simplification: show only the most abnormal regions in each representative scan.
TOP_N_REGIONS = 10

# Z-score thresholds used for visualization.
NORMAL_Z = 2.0
REVIEW_Z = 3.0

# Compact figure size suitable for manuscript figures.
FIG_WIDTH = 10.2
FIG_HEIGHT = 4.6

# Shorten long atlas labels to reduce visual clutter.
MAX_REGION_LABEL_CHARS = 28


# =========================
# Visual style
# =========================
def set_publication_style() -> None:
    """Clean, compact journal-style Matplotlib settings."""
    mpl.rcParams.update({
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "axes.titlesize": 9.2,
        "axes.labelsize": 8.4,
        "xtick.labelsize": 7.6,
        "ytick.labelsize": 7.2,
        "legend.fontsize": 7.6,
        "axes.linewidth": 0.7,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
    })


COLORS = {
    "normal": "#4C78A8",      # blue
    "moderate": "#F2A541",    # amber
    "severe": "#D64B3C",      # red
    "line": "#B8BDC7",
    "zero": "#30343B",
    "grid": "#E8EAED",
    "text": "#202124",
    "muted": "#6B7280",
    "band": "#F7F8FA",
}

PANEL_COLORS = {
    "Pass": "#4C78A8",
    "Moderate review": "#F2A541",
    "Severe review": "#D64B3C",
    "Severe-like review": "#D64B3C",
}


# =========================
# Data handling
# =========================
def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def require_columns(df: pd.DataFrame, required: Iterable[str], file_name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{file_name} is missing required columns: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )


def normalize_qc_label(x: object) -> str:
    """Map common QC labels to Pass / Moderate review / Severe review."""
    if pd.isna(x):
        return "Unknown"
    s = str(x).strip().lower().replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)

    if s in {"pass", "passed", "ok", "normal", "usable", "accept", "accepted"}:
        return "Pass"
    if "severe" in s or "extreme" in s or "major" in s or "fail" in s or "exclude" in s:
        return "Severe review"
    if "moderate" in s or "minor" in s or "review" in s or "flag" in s:
        return "Moderate review"
    return str(x).strip()


def load_and_merge(zscore_csv: Path, qc_csv: Path) -> pd.DataFrame:
    if not zscore_csv.exists():
        raise FileNotFoundError(f"Cannot find Z-score CSV: {zscore_csv}")
    if not qc_csv.exists():
        raise FileNotFoundError(f"Cannot find QC CSV: {qc_csv}")

    z = clean_column_names(pd.read_csv(zscore_csv))
    q = clean_column_names(pd.read_csv(qc_csv))

    require_columns(z, ["Scan_ID", "tracer", "region_name", "SUVR", "robust_Z"], str(zscore_csv))
    require_columns(q, ["Scan_ID"], str(qc_csv))

    qc_cols = [c for c in ["Scan_ID", "QC_label", "review_reason", "tracer"] if c in q.columns]
    q_small = q[qc_cols].drop_duplicates(subset=["Scan_ID"])
    merged = z.merge(q_small, on="Scan_ID", how="left", suffixes=("", "_qc"))

    if "tracer_qc" in merged.columns:
        merged["tracer"] = merged["tracer"].fillna(merged["tracer_qc"])
        merged = merged.drop(columns=["tracer_qc"])

    for c in ["QC_label", "review_reason"]:
        alt = f"{c}_qc"
        if alt in merged.columns:
            if c in merged.columns:
                merged[c] = merged[c].fillna(merged[alt])
            else:
                merged[c] = merged[alt]
            merged = merged.drop(columns=[alt])

    if "QC_label" not in merged.columns:
        raise ValueError("QC_label was not found in either input file.")
    if "review_reason" not in merged.columns:
        merged["review_reason"] = ""

    merged["QC_group"] = merged["QC_label"].map(normalize_qc_label)
    merged["robust_Z"] = pd.to_numeric(merged["robust_Z"], errors="coerce")
    merged["SUVR"] = pd.to_numeric(merged["SUVR"], errors="coerce")
    merged = merged.dropna(subset=["Scan_ID", "region_name", "robust_Z"])
    merged["region_name"] = merged["region_name"].astype(str)
    return merged


def summarize_scan_level(df: pd.DataFrame) -> pd.DataFrame:
    def first_nonempty(s: pd.Series) -> str:
        vals = [str(v).strip() for v in s if pd.notna(v) and str(v).strip()]
        return vals[0] if vals else ""

    scan = (
        df.groupby(["Scan_ID", "QC_group"], dropna=False)
        .agg(
            tracer=("tracer", first_nonempty),
            n_regions=("region_name", "nunique"),
            mean_abs_z=("robust_Z", lambda x: np.nanmean(np.abs(x))),
            median_abs_z=("robust_Z", lambda x: np.nanmedian(np.abs(x))),
            max_abs_z=("robust_Z", lambda x: np.nanmax(np.abs(x))),
            n_abs_z_ge_2=("robust_Z", lambda x: int(np.nansum(np.abs(x) >= 2.0))),
            n_abs_z_ge_3=("robust_Z", lambda x: int(np.nansum(np.abs(x) >= 3.0))),
            review_reason=("review_reason", first_nonempty),
        )
        .reset_index()
    )
    scan["severity_score"] = (
        scan["mean_abs_z"]
        + 0.20 * scan["max_abs_z"]
        + 0.12 * scan["n_abs_z_ge_2"]
        + 0.25 * scan["n_abs_z_ge_3"]
    )
    return scan


def choose_representative_cases(scan: pd.DataFrame) -> pd.DataFrame:
    """
    Select one representative scan for Pass, Moderate review, and Severe review.
    Manual Scan_ID values override automatic selection.
    """
    rows = []
    used_ids = set()
    targets = {
        "Pass": 0.33,
        "Moderate review": 0.50,
        "Severe review": 0.50,
    }

    def pick_quantile(subset: pd.DataFrame, q: float) -> pd.DataFrame:
        target = subset["severity_score"].quantile(q)
        tmp = subset.copy()
        tmp["distance_to_target"] = (tmp["severity_score"] - target).abs()
        return tmp.sort_values(
            ["distance_to_target", "n_abs_z_ge_3", "max_abs_z"],
            ascending=[True, True, True],
        ).iloc[[0]].copy()

    def pick_highest_severity(subset: pd.DataFrame) -> pd.DataFrame:
        return subset.sort_values(
            ["severity_score", "max_abs_z", "n_abs_z_ge_3", "n_abs_z_ge_2"],
            ascending=[False, False, False, False],
        ).iloc[[0]].copy()

    for group, q in targets.items():
        manual_id = MANUAL_CASES.get(group)
        subset = scan.loc[scan["QC_group"].eq(group)].copy()
        panel_group = group
        selection_note = "Selected from matching QC_group."

        if manual_id:
            row = scan.loc[scan["Scan_ID"].astype(str).eq(str(manual_id))].copy()
            if row.empty:
                raise ValueError(f"Manual {group} Scan_ID not found: {manual_id}")
            row = row.iloc[[0]].copy()
            selection_note = f"Manual Scan_ID supplied for {group}."
        else:
            subset_unused = subset.loc[~subset["Scan_ID"].astype(str).isin(used_ids)].copy()
            if not subset_unused.empty:
                subset = subset_unused

            if not subset.empty:
                row = pick_quantile(subset, q)
            elif group == "Severe review":
                fallback = scan.loc[~scan["QC_group"].eq("Pass")].copy()
                fallback_unused = fallback.loc[~fallback["Scan_ID"].astype(str).isin(used_ids)].copy()
                if not fallback_unused.empty:
                    fallback = fallback_unused
                if fallback.empty:
                    fallback = scan.copy()
                row = pick_highest_severity(fallback)
                panel_group = "Severe-like review"
                selection_note = "No true Severe review label found; selected highest-severity non-pass scan."
            elif group == "Moderate review":
                fallback = scan.loc[~scan["QC_group"].eq("Pass")].copy()
                fallback_unused = fallback.loc[~fallback["Scan_ID"].astype(str).isin(used_ids)].copy()
                if not fallback_unused.empty:
                    fallback = fallback_unused
                if fallback.empty:
                    raise ValueError("No Moderate review scan and no non-pass fallback scan found.")
                row = pick_quantile(fallback, q)
                selection_note = "No Moderate review scan found; selected non-pass fallback scan."
            else:
                raise ValueError(f"No scans found for QC_group='{group}'.")

        row["panel_group"] = panel_group
        row["selection_note"] = selection_note
        rows.append(row)
        used_ids.add(str(row.iloc[0]["Scan_ID"]))

    return pd.concat(rows, ignore_index=True)


# =========================
# Plotting helpers
# =========================
def classify_point(z: float) -> str:
    az = abs(float(z))
    if az >= REVIEW_Z:
        return "severe"
    if az >= NORMAL_Z:
        return "moderate"
    return "normal"


def compact_region_label(label: object, max_chars: int = MAX_REGION_LABEL_CHARS) -> str:
    """Make atlas labels easier to read in a compact figure."""
    s = str(label).strip()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)

    # Common harmless abbreviation for long left/right prefixes.
    s = re.sub(r"^left\s+", "L ", s, flags=re.IGNORECASE)
    s = re.sub(r"^right\s+", "R ", s, flags=re.IGNORECASE)

    if len(s) > max_chars:
        s = s[: max_chars - 1].rstrip() + "…"
    return s


def panel_title(row: pd.Series) -> str:
    group = str(row["panel_group"])
    tracer = str(row.get("tracer", "") or "tracer NA")
    return f"{group}\n{tracer} · max |Z|={row['max_abs_z']:.1f}"


def make_plot(df: pd.DataFrame, selected: pd.DataFrame, out_dir: Path) -> None:
    set_publication_style()
    out_dir.mkdir(parents=True, exist_ok=True)

    selected_ids = selected["Scan_ID"].astype(str).tolist()
    plot_df = df.loc[df["Scan_ID"].astype(str).isin(selected_ids)].copy()

    max_abs = float(np.nanmax(np.abs(plot_df["robust_Z"]))) if not plot_df.empty else REVIEW_Z
    x_lim = max(REVIEW_Z + 0.8, np.ceil(max_abs + 0.3))
    x_lim = min(max(x_lim, 4.0), 8.0) if max_abs < 8 else np.ceil(max_abs + 0.5)

    fig, axes = plt.subplots(
        1, 3,
        figsize=(FIG_WIDTH, FIG_HEIGHT),
        sharex=True,
        constrained_layout=False,
        gridspec_kw={"wspace": 0.55},
    )

    for ax, (_, sel_row) in zip(axes, selected.iterrows()):
        sid = str(sel_row["Scan_ID"])
        group = str(sel_row["panel_group"])
        sub = plot_df.loc[plot_df["Scan_ID"].astype(str).eq(sid)].copy()
        sub["abs_Z"] = sub["robust_Z"].abs()
        sub = sub.sort_values("abs_Z", ascending=False).head(TOP_N_REGIONS)
        sub = sub.sort_values("robust_Z", ascending=True).reset_index(drop=True)
        sub["y"] = np.arange(len(sub))

        # Very light threshold shading: enough context, not visually heavy.
        ax.axvspan(-NORMAL_Z, NORMAL_Z, color=COLORS["band"], zorder=0)
        ax.axvline(0, color=COLORS["zero"], lw=0.8, zorder=1)
        for t in [-REVIEW_Z, -NORMAL_Z, NORMAL_Z, REVIEW_Z]:
            ax.axvline(t, color="#AAB0BA", lw=0.65, ls=(0, (2.5, 2.5)), zorder=1)

        for _, r in sub.iterrows():
            z = float(r["robust_Z"])
            y = float(r["y"])
            ax.plot([0, z], [y, y], color=COLORS["line"], lw=1.1, zorder=2)

        point_colors = [COLORS[classify_point(z)] for z in sub["robust_Z"].to_numpy()]
        ax.scatter(
            sub["robust_Z"],
            sub["y"],
            s=34,
            c=point_colors,
            edgecolor="white",
            linewidth=0.55,
            zorder=3,
        )

        ax.set_yticks(sub["y"])
        ax.set_yticklabels([compact_region_label(x) for x in sub["region_name"]])
        ax.set_title(panel_title(sel_row), color=PANEL_COLORS.get(group, COLORS["text"]), fontweight="bold", pad=7)
        ax.set_xlim(-x_lim, x_lim)
        ax.set_ylim(-0.7, max(len(sub) - 0.3, 0.7))
        ax.grid(axis="x", color=COLORS["grid"], lw=0.5, alpha=0.9)
        ax.tick_params(axis="both", length=2.2)

        # Small, unobtrusive case ID inside panel.
        ax.text(
            0.02,
            0.02,
            f"Scan {sid}",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=6.8,
            color=COLORS["muted"],
        )

    fig.supxlabel("Regional robust Z-score", y=0.075, fontsize=8.8)

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["normal"],
               markeredgecolor="white", markersize=5.5, label=f"|Z| < {NORMAL_Z:g}"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["moderate"],
               markeredgecolor="white", markersize=5.5, label=f"{NORMAL_Z:g} ≤ |Z| < {REVIEW_Z:g}"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["severe"],
               markeredgecolor="white", markersize=5.5, label=f"|Z| ≥ {REVIEW_Z:g}"),
    ]
    fig.legend(
        handles=handles,
        loc="upper right",
        bbox_to_anchor=(0.985, 0.975),
        ncol=3,
        frameon=False,
        handlelength=1.0,
        columnspacing=0.9,
    )

    fig.subplots_adjust(left=0.115, right=0.985, top=0.82, bottom=0.17, wspace=0.55)

    stem = out_dir / "Fig3_compact_regional_robust_Z_profiles"
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".svg"))
    fig.savefig(stem.with_suffix(".png"))
    plt.close(fig)


# =========================
# Main
# =========================
def main() -> None:
    parser = argparse.ArgumentParser(description="Make compact Fig. 3 regional robust Z-score profiles.")
    parser.add_argument("--zscore-csv", default=str(ZSCORE_CSV))
    parser.add_argument("--qc-csv", default=str(QC_CSV))
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()

    zscore_csv = Path(args.zscore_csv)
    qc_csv = Path(args.qc_csv)
    out_dir = Path(args.out_dir)

    df = load_and_merge(zscore_csv, qc_csv)
    scan = summarize_scan_level(df)
    selected = choose_representative_cases(scan)

    out_dir.mkdir(parents=True, exist_ok=True)
    selected_out = out_dir / "Fig3_compact_representative_cases_used.csv"
    selected.to_csv(selected_out, index=False)

    make_plot(df, selected, out_dir)

    print("Done. Wrote:")
    print(f"  {out_dir / 'Fig3_compact_regional_robust_Z_profiles.pdf'}")
    print(f"  {out_dir / 'Fig3_compact_regional_robust_Z_profiles.svg'}")
    print(f"  {out_dir / 'Fig3_compact_regional_robust_Z_profiles.png'}")
    print(f"  {selected_out}")
    print("\nSelected representative cases:")
    cols = [
        "panel_group", "Scan_ID", "tracer", "QC_group", "max_abs_z",
        "n_abs_z_ge_2", "n_abs_z_ge_3", "selection_note",
    ]
    print(selected[cols].to_string(index=False))

    if "Severe-like review" in selected["panel_group"].astype(str).tolist():
        observed = sorted(scan["QC_group"].dropna().unique().tolist())
        print("\nWARNING: No true 'Severe review' cases were found in QC_label.")
        print(f"Observed QC groups: {observed}")
        print("The third panel was drawn as 'Severe-like review' using the highest-severity non-pass scan.")


if __name__ == "__main__":
    main()
