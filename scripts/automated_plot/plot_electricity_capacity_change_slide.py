"""
Electricity Capacity Change - Slide-Ready Horizontal Bar Chart

Shows percentage change in electricity capacity from baseline by country,
comparing National vs Regional policy under Precursor scenario.

Output: electricity_capacity_change_slide.png
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


# Country name mapping
COUNTRY_NAMES = {
    'ZAF': 'South Africa',
    'COD': 'DRC',
    'ZMB': 'Zambia',
    'ZWE': 'Zimbabwe',
    'MOZ': 'Mozambique',
    'NAM': 'Namibia',
    'BWA': 'Botswana',
    'TZA': 'Tanzania',
    'MDG': 'Madagascar',
    'AGO': 'Angola',
    'KEN': 'Kenya',
    'MWI': 'Malawi',
    'BDI': 'Burundi',
    'UGA': 'Uganda'
}

# Electricity capacity change data (from publication figure)
# Percentage change relative to baseline for Precursor scenarios (unconstrained)
ELECTRICITY_CAPACITY_CHANGE = {
    "AGO": {"Regional": 3, "National": 0},
    "BDI": {"Regional": 15, "National": 0},
    "BWA": {"Regional": 2, "National": 0},
    "COD": {"Regional": 35, "National": 31},
    "KEN": {"Regional": 0, "National": 0},
    "MDG": {"Regional": 6, "National": 0},
    "MOZ": {"Regional": 4, "National": 1},
    "MWI": {"Regional": 7, "National": 5},
    "NAM": {"Regional": 35, "National": 6},
    "TZA": {"Regional": 20, "National": 5},
    "UGA": {"Regional": 0, "National": 0},
    "ZAF": {"Regional": 1, "National": 0},
    "ZMB": {"Regional": 5, "National": 2},
    "ZWE": {"Regional": 2, "National": 1}
}

# Colors for policies
COLOR_NATIONAL = '#4a86c7'  # Steel blue
COLOR_REGIONAL = '#e8744f'  # Coral


def generate_slide_chart(output_dir):
    """
    Generate slide-ready horizontal grouped bar chart.

    Args:
        output_dir: Output directory for the chart

    Returns:
        str: Path to generated chart
    """
    os.makedirs(output_dir, exist_ok=True)

    print("\n[Electricity Capacity Change - Slide Chart]")
    print("-" * 60)

    # Filter out countries with both values = 0
    data = {k: v for k, v in ELECTRICITY_CAPACITY_CHANGE.items()
            if v["Regional"] > 0 or v["National"] > 0}

    # Sort by Regional value descending
    countries_sorted = sorted(data.keys(),
                              key=lambda x: data[x]["Regional"],
                              reverse=True)

    print(f"Countries to display: {len(countries_sorted)}")
    for c in countries_sorted:
        print(f"  {COUNTRY_NAMES.get(c, c)}: Regional {data[c]['Regional']}%, National {data[c]['National']}%")

    # --- Create the visualization ---
    print("\nGenerating chart...")

    fig, ax = plt.subplots(figsize=(8, 6))

    y_positions = np.arange(len(countries_sorted))
    bar_height = 0.35

    # Plot bars for each country
    for i, country in enumerate(countries_sorted):
        regional_val = data[country]["Regional"]
        national_val = data[country]["National"]

        # Regional bar (top of pair)
        if regional_val > 0:
            ax.barh(i + bar_height/2, regional_val, height=bar_height,
                    color=COLOR_REGIONAL, edgecolor='white', linewidth=0.5)
            # Adjust font size for small values
            fontsize = 9 if regional_val < 5 else 10
            ax.text(regional_val + 0.8, i + bar_height/2, f'{regional_val}%',
                    va='center', ha='left', fontsize=fontsize, fontweight='bold',
                    color=COLOR_REGIONAL)

        # National bar (bottom of pair)
        if national_val > 0:
            ax.barh(i - bar_height/2, national_val, height=bar_height,
                    color=COLOR_NATIONAL, edgecolor='white', linewidth=0.5)
            # Adjust font size for small values
            fontsize = 9 if national_val < 5 else 10
            ax.text(national_val + 0.8, i - bar_height/2, f'{national_val}%',
                    va='center', ha='left', fontsize=fontsize, fontweight='bold',
                    color=COLOR_NATIONAL)

    # Styling
    ax.set_yticks(y_positions)
    ax.set_yticklabels([COUNTRY_NAMES.get(c, c) for c in countries_sorted], fontsize=11)
    ax.set_xlabel('Electricity Capacity Change from Baseline (%)', fontsize=12, fontweight='bold')
    ax.set_title('Additional Electricity Capacity Required\n(Precursor Scenario - 2040 vs 2022)',
                 fontsize=13, fontweight='bold', pad=10)

    # Set x-axis limits
    max_val = max(max(v["Regional"], v["National"]) for v in data.values())
    ax.set_xlim(0, max_val * 1.15)

    # Grid and spines
    ax.xaxis.grid(True, linestyle='--', alpha=0.3, zorder=0)
    ax.yaxis.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_axisbelow(True)

    # Legend - position at upper right where values are small
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLOR_REGIONAL, edgecolor='white', label='Regional Policy'),
        Patch(facecolor=COLOR_NATIONAL, edgecolor='white', label='National Policy'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10,
              frameon=True, fancybox=True, framealpha=0.9)

    plt.tight_layout()

    # Save
    output_path = os.path.join(output_dir, 'electricity_capacity_change_slide.png')
    plt.savefig(output_path, dpi=200, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)

    print(f"\n  Saved: {output_path}")
    print("-" * 60)

    return output_path


if __name__ == '__main__':
    config = load_config()
    output_dir = Path(config['paths']['figures']) / 'automated_plots' / 'single_axis'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ELECTRICITY CAPACITY CHANGE - SLIDE CHART")
    print("=" * 60)

    chart_path = generate_slide_chart(output_dir)

    print("\n" + "=" * 60)
    print("COMPLETED")
    print("=" * 60)
