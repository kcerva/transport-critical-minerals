"""
Grid Selection Figure

Dual-axis bar chart showing annual electricity demand split by technology type:
  - Grid Connection (GWh/year, left axis, blue)
  - Off-Grid       (MWh/year, right axis, orange)

Scenarios shown: Baseline 2022 + BAU/Early Refining/Precursor × Country/Region (mid demand, unconstrained).
Data source: incoming_data/energy_camilo/all_scenarios_comparison_combined.xlsx
Output:       figures/automated_plots/publication/electricity/grid_selection.png
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOMATED_PLOT_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(AUTOMATED_PLOT_DIR)

sys.path.insert(0, AUTOMATED_PLOT_DIR)

# Load project config
config_path = os.path.join(SCRIPT_DIR, "..", "..", "..", "config.json")
with open(config_path) as f:
    config = json.load(f)

INCOMING_DATA = config["paths"]["incoming_data"]
FIGURES_DIR   = config["paths"]["figures"]

ENERGY_DATA_PATH = os.path.join(INCOMING_DATA, "energy_camilo", "all_scenarios_comparison_combined.xlsx")
OUTPUT_DIR = os.path.join(FIGURES_DIR, "automated_plots", "publication", "electricity")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Scenario selection
# "mid" demand level, unconstrained, matching the structure of the original figure
# ---------------------------------------------------------------------------
SCENARIO_MAP = {
    "2022_baseline_country_unconstrained":
        "Baseline 2022",
    "bau_2040_mid_min_threshold_metal_tons_country_unconstrained":
        "BAU - Country 2040",
    "precursor_2040_mid_max_threshold_metal_tons_region_unconstrained":
        "Precursor\n- Region 2040",
    "precursor_2040_mid_min_threshold_metal_tons_country_unconstrained":
        "Precursor\n- Country 2040",
}

# ---------------------------------------------------------------------------
# Load and filter data
# ---------------------------------------------------------------------------
df_raw = pd.read_excel(ENERGY_DATA_PATH, sheet_name="Decision Split Summary")

df_grid   = df_raw[df_raw["Decision"] == "Grid Connection"].set_index("Scenario")
df_offgrid = df_raw[df_raw["Decision"] == "Off-Grid"].set_index("Scenario")

scenario_keys = list(SCENARIO_MAP.keys())
labels        = list(SCENARIO_MAP.values())

grid_gwh   = [df_grid.loc[s, "Total_Annual_Demand_kWh"] / 1e6 for s in scenario_keys]
offgrid_mwh = [df_offgrid.loc[s, "Total_Annual_Demand_kWh"] / 1e3 for s in scenario_keys]

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
GRID_COLOR    = "#1f77b4"
OFFGRID_COLOR = "#ff7f0e"
FONT_SIZE     = 11
LABEL_SIZE    = 12

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": FONT_SIZE,
    "axes.labelsize": LABEL_SIZE,
    "xtick.labelsize": FONT_SIZE,
    "ytick.labelsize": FONT_SIZE,
    "legend.fontsize": FONT_SIZE,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,
})

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(12, 7))

x = np.arange(len(labels))
width = 0.35

# Grid Connection bars (left axis)
bars1 = ax1.bar(x - width / 2, grid_gwh, width,
                label="Grid Connection",
                color=GRID_COLOR, edgecolor="#1a5490", linewidth=0.8)

ax1.set_ylabel("Grid Connection (GWh/year)", color=GRID_COLOR,
               fontsize=LABEL_SIZE, fontweight="bold")
ax1.tick_params(axis="y", labelcolor=GRID_COLOR)
max_grid = max(grid_gwh)
ax1.set_ylim(0, max_grid * 1.15)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

# Off-Grid bars (right axis)
ax2 = ax1.twinx()
bars2 = ax2.bar(x + width / 2, offgrid_mwh, width,
                label="Off-Grid",
                color=OFFGRID_COLOR, edgecolor="#cc5200", linewidth=0.8)

ax2.set_ylabel("Off-Grid (MWh/year)", color=OFFGRID_COLOR,
               fontsize=LABEL_SIZE, fontweight="bold")
ax2.tick_params(axis="y", labelcolor=OFFGRID_COLOR)
max_offgrid = max(offgrid_mwh)
ax2.set_ylim(0, max_offgrid * 1.15)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

# X-axis
ax1.set_xticks(x)
ax1.set_xticklabels(labels, rotation=0, ha="center", fontsize=FONT_SIZE)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           loc="upper left", frameon=True, fancybox=False, edgecolor="#cccccc")

fig.patch.set_facecolor("white")
ax1.set_facecolor("white")

plt.tight_layout()

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_path = os.path.join(OUTPUT_DIR, "grid_selection.png")
fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
print(f"Saved: {out_path}")

out_pdf = os.path.join(OUTPUT_DIR, "grid_selection.pdf")
fig.savefig(out_pdf, bbox_inches="tight", facecolor="white")
print(f"Saved: {out_pdf}")

plt.close(fig)
