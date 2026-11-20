#!/usr/bin/env python3
"""Generate the representative performance chart used by the model card."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "samples" / "images" / "key_performance_overview.png"

METRICS = [
    "Heritage · Direct exact",
    "Heritage · Hard choice",
    "Korean OCR · Outdoor exact",
    "Long-horizon · Tau2 overall",
    "Tool calling · BFCL V4 overall",
    "Multimodal · General-VL macro",
]
BASE = np.array([5.05, 59.79, 33.59, 40.62, 7.85, 66.19])
TUNED = np.array([74.16, 89.76, 38.87, 42.71, 15.00, 65.29])
DELTAS = np.array([69.11, 29.97, 5.27, 2.08, 7.15, -0.90])


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#D1D5DB",
            "axes.labelcolor": "#374151",
            "xtick.color": "#4B5563",
            "ytick.color": "#111827",
        }
    )

    y = np.arange(len(METRICS))
    bar_height = 0.30
    base_color = "#9CA3AF"
    tuned_color = "#7C3AED"

    fig, ax = plt.subplots(figsize=(13.5, 7.2), facecolor="white")
    ax.set_facecolor("white")
    base_bars = ax.barh(
        y - bar_height / 2,
        BASE,
        height=bar_height,
        color=base_color,
        label="Official HyperCLOVA X SEED 32B Think",
    )
    tuned_bars = ax.barh(
        y + bar_height / 2,
        TUNED,
        height=bar_height,
        color=tuned_color,
        label="HyperCLOVA X KETI-HAECHI-32B",
    )

    ax.set_yticks(y, METRICS)
    ax.invert_yaxis()
    ax.set_xlim(0, 112)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set_xlabel("Score (%)", labelpad=10)
    ax.xaxis.grid(True, color="#E5E7EB", linewidth=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0, pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)

    for bars, values in ((base_bars, BASE), (tuned_bars, TUNED)):
        for bar, value in zip(bars, values):
            ax.text(
                value + 0.9,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.2f}",
                va="center",
                ha="left",
                fontsize=9.5,
                color="#374151",
            )

    ax.text(
        106,
        -0.63,
        "Δ (pp)",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color="#374151",
    )
    for row, delta in zip(y, DELTAS):
        ax.text(
            106,
            row,
            f"{delta:+.2f}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#15803D" if delta >= 0 else "#B91C1C",
        )

    fig.suptitle(
        "Key Performance Overview",
        x=0.125,
        y=0.975,
        ha="left",
        fontsize=20,
        color="#111827",
    )
    fig.text(
        0.125,
        0.925,
        "Official base vs. HyperCLOVA X KETI-HAECHI-32B on representative benchmarks",
        ha="left",
        fontsize=11.5,
        color="#4B5563",
    )
    fig.legend(
        handles=[base_bars, tuned_bars],
        labels=[
            "Official HyperCLOVA X SEED 32B Think",
            "HyperCLOVA X KETI-HAECHI-32B",
        ],
        loc="upper left",
        bbox_to_anchor=(0.12, 0.89),
        frameon=False,
        ncol=2,
        columnspacing=2.0,
        handlelength=1.4,
        fontsize=9.5,
    )
    fig.text(
        0.125,
        0.025,
        "Values are percentages; deltas are absolute percentage points. Higher is better.",
        ha="left",
        fontsize=9.5,
        color="#6B7280",
    )

    fig.subplots_adjust(left=0.31, right=0.96, top=0.81, bottom=0.13)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUTPUT,
        dpi=180,
        facecolor="white",
        bbox_inches="tight",
        metadata={"Software": "Matplotlib"},
    )
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
