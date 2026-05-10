#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QC trigger breakdown by tracer

Input:
    outputs/deid_exports/QC_features_deid.csv

Output:
    figures/Fig2_QC_trigger_breakdown.pdf
    figures/Fig2_QC_trigger_breakdown.png
    figures/Fig2_QC_trigger_breakdown.svg
    figures/Fig2_QC_trigger_breakdown_counts.csv
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.patches import Patch


# =========================
# Configuration
# =========================

import argparse

FIG_BASENAME = "Fig2_QC_trigger_breakdown"

REQUIRED_COLS = [
    "tracer",
    "QC_label",
    "review_reason",
    "extreme_z_review_count",
    "extreme_z_fail_count",
    "missing_suvr_values",
]

CATEGORY_ORDER = [
    "Pass",
    "Robust Z ≥ 2.5",
    "Extreme robust Z ≥ 4.0",
    "Missing SUVR",
    "Other QC review",
]

# 柔和、适合论文的配色
CATEGORY_COLORS = {
    "Pass": "#D8DEE9",                    # soft gray
    "Robust Z ≥ 2.5": "#5E81AC",          # muted blue
    "Extreme robust Z ≥ 4.0": "#BF616A",  # muted red
    "Missing SUVR": "#EBCB8B",            # soft gold
    "Other QC review": "#A3BE8C",         # soft green
}


# =========================
# Helper functions
# =========================

def safe_numeric(series: pd.Series) -> pd.Series:
    """Convert a column to numeric counts. Non-numeric values become 0."""
    return pd.to_numeric(series, errors="coerce").fillna(0)


def has_missing_suvr(value) -> bool:
    """Detect whether missing_suvr_values indicates at least one missing SUVR value."""
    if pd.isna(value):
        return False

    if isinstance(value, (int, float, np.integer, np.floating)):
        return value > 0

    text = str(value).strip().lower()

    if text in {"", "0", "0.0", "none", "nan", "na", "n/a", "[]", "{}", "false", "no"}:
        return False

    return True


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def classify_qc_trigger(row) -> str:
    """
    Assign one exclusive QC trigger category per scan.

    Priority:
        1. Extreme robust Z ≥ 4.0
        2. Robust Z ≥ 2.5
        3. Missing SUVR
        4. Pass
        5. Other QC review
    """
    qc_label = normalize_text(row["QC_label"])
    review_reason = normalize_text(row["review_reason"])

    review_count = row["_extreme_z_review_count_num"]
    fail_count = row["_extreme_z_fail_count_num"]
    missing_flag = row["_missing_suvr_flag"]

    has_extreme_z_fail = (
        fail_count > 0
        or bool(re.search(r"extreme|z\s*>=?\s*4|z\s*≥\s*4|4\.0|fail", review_reason))
    )

    has_robust_z_review = (
        review_count > 0
        or bool(re.search(r"robust|z\s*>=?\s*2\.5|z\s*≥\s*2\.5|2\.5", review_reason))
    )

    has_missing = (
        missing_flag
        or bool(re.search(r"missing|suvr", review_reason))
    )

    if has_extreme_z_fail:
        return "Extreme robust Z ≥ 4.0"

    if has_robust_z_review:
        return "Robust Z ≥ 2.5"

    if has_missing:
        return "Missing SUVR"

    if qc_label in {"pass", "passed", "ok", "normal"}:
        return "Pass"

    return "Other QC review"


def hex_to_luminance(hex_color: str) -> float:
    """Return relative luminance for choosing black or white label text."""
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def adjust(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = adjust(r), adjust(g), adjust(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def label_color_for_category(cat: str) -> str:
    return "white" if hex_to_luminance(CATEGORY_COLORS[cat]) < 0.45 else "black"


def add_count_labels(ax, prop_df, count_df, categories_to_plot):
    """Add count labels inside sufficiently large stacked bar segments."""
    y_positions = np.arange(len(prop_df))
    left = np.zeros(len(prop_df))

    for cat in categories_to_plot:
        values = prop_df[cat].values
        counts = count_df[cat].values

        for i, (pct, cnt) in enumerate(zip(values, counts)):
            if cnt <= 0:
                continue

            if pct >= 7:
                ax.text(
                    left[i] + pct / 2,
                    y_positions[i],
                    str(int(cnt)),
                    ha="center",
                    va="center",
                    fontsize=9,
                    color=label_color_for_category(cat),
                    fontweight="bold",
                )

        left += values


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser(description="Make Fig. 2 QC trigger breakdown plot.")
    parser.add_argument("--input-csv", default="outputs/deid_exports/QC_features_deid.csv")
    parser.add_argument("--out-dir", default="outputs/figures")
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_csv.exists():
        raise FileNotFoundError(f"Cannot find input file: {input_csv}")

    df = pd.read_csv(input_csv)

    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            "Missing required columns in QC_features_deid.csv: "
            + ", ".join(missing_cols)
        )

    df["tracer"] = df["tracer"].astype(str).str.strip()
    df["QC_label"] = df["QC_label"].astype(str).str.strip()

    df["_extreme_z_review_count_num"] = safe_numeric(df["extreme_z_review_count"])
    df["_extreme_z_fail_count_num"] = safe_numeric(df["extreme_z_fail_count"])
    df["_missing_suvr_flag"] = df["missing_suvr_values"].apply(has_missing_suvr)

    df["QC_trigger_category"] = df.apply(classify_qc_trigger, axis=1)

    count_df = (
        df.groupby(["tracer", "QC_trigger_category"])
        .size()
        .unstack(fill_value=0)
    )

    for cat in CATEGORY_ORDER:
        if cat not in count_df.columns:
            count_df[cat] = 0

    count_df = count_df[CATEGORY_ORDER]

    count_df["Total"] = count_df.sum(axis=1)
    count_df["Non-pass"] = count_df["Total"] - count_df["Pass"]
    count_df["Non-pass rate"] = count_df["Non-pass"] / count_df["Total"].replace(0, np.nan)

    count_df = count_df.sort_values(
        by=["Non-pass rate", "Total"],
        ascending=[False, False],
    )

    plot_counts = count_df[CATEGORY_ORDER]
    plot_prop = plot_counts.div(plot_counts.sum(axis=1), axis=0) * 100

    count_df.to_csv(out_dir / f"{FIG_BASENAME}_counts.csv")

    categories_to_plot = [
        cat for cat in CATEGORY_ORDER
        if plot_counts[cat].sum() > 0
    ]

    # =========================
    # Plot
    # =========================

    n_tracers = len(plot_prop)

    fig_width = 8.0
    fig_height = max(2.8, 0.62 * n_tracers + 1.25)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 10,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.9,
    })

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    y = np.arange(n_tracers)
    left = np.zeros(n_tracers)

    for cat in categories_to_plot:
        values = plot_prop[cat].values

        ax.barh(
            y,
            values,
            left=left,
            height=0.64,
            label=cat,
            color=CATEGORY_COLORS[cat],
            edgecolor="white",
            linewidth=1.0,
        )

        left += values

    add_count_labels(ax, plot_prop, plot_counts, categories_to_plot)

    for i, total in enumerate(count_df["Total"].values):
        ax.text(
            101.2,
            i,
            f"n={int(total)}",
            va="center",
            ha="left",
            fontsize=9,
            color="#333333",
            clip_on=False,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(plot_prop.index)
    ax.invert_yaxis()

    ax.set_xlim(0, 108)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=100))

    ax.set_xlabel("Scans within tracer (%)", labelpad=8)
    ax.set_ylabel("Tracer", labelpad=8)

    # 不设置 ax.set_title，所以图片上方不会出现 Fig. 2 文字

    ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.25)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=3, width=0.8)

    legend_handles = [
        Patch(facecolor=CATEGORY_COLORS[cat], edgecolor="none", label=cat)
        for cat in categories_to_plot
    ]

    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.52, 0.98),
        ncol=min(3, len(categories_to_plot)),
        frameon=False,
        handlelength=1.6,
        columnspacing=1.4,
    )

    fig.subplots_adjust(
        left=0.13,
        right=0.91,
        bottom=0.20,
        top=0.78,
    )

    fig.savefig(out_dir / f"{FIG_BASENAME}.pdf", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(out_dir / f"{FIG_BASENAME}.svg", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(out_dir / f"{FIG_BASENAME}.png", dpi=600, bbox_inches="tight", pad_inches=0.04)

    plt.close(fig)

    print("Done.")
    print(f"Saved: {out_dir / f'{FIG_BASENAME}.pdf'}")
    print(f"Saved: {out_dir / f'{FIG_BASENAME}.png'}")
    print(f"Saved: {out_dir / f'{FIG_BASENAME}.svg'}")
    print(f"Saved: {out_dir / f'{FIG_BASENAME}_counts.csv'}")


if __name__ == "__main__":
    main()