"""
Net Export Revenue - Slide-Ready Horizontal Bar Chart

Creates a compact, visually appealing horizontal bar chart showing
net export revenue totals comparing National vs Regional policy.
Designed to occupy 1/3 of a presentation slide.

Output: net_export_revenue_slide.png
"""

import os
import sys
import json
import pandas as pd
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


def load_tonnage_flows_data():
    """Load tonnage flows with revenue/cost data"""
    config = load_config()
    results_path = Path(config['paths']['results'])
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'

    print(f"Loading data from: {flows_path}")
    df = pd.read_excel(flows_path, sheet_name='All_Flows')
    print(f"  Loaded {len(df):,} flow records")

    return df


def calculate_total_net_revenue(df, scenario, constraint):
    """
    Calculate total net export revenue for a specific scenario/constraint.

    Uses MARKET PRICE basis for imports (import_cost_at_price_usd).

    Returns:
        float: Total net revenue in USD
    """
    # Filter for scenario and constraint
    df_scenario = df[
        (df['scenario'] == scenario) &
        (df['constraint'] == constraint)
    ].copy()

    if df_scenario.empty:
        print(f"  Warning: No data for {scenario} / {constraint}")
        return 0

    # Calculate total exports
    total_exports = df_scenario[
        df_scenario['trade_type'] == 'Export'
    ]['export_revenue_usd'].sum()

    # Calculate total imports (using market price basis)
    total_imports = df_scenario[
        df_scenario['trade_type'].str.contains('Import', na=False)
    ]['import_cost_at_price_usd'].sum()

    return total_exports - total_imports


def generate_slide_chart(output_dir):
    """
    Generate slide-ready horizontal bar chart for net export revenue.

    Args:
        output_dir: Output directory for the chart

    Returns:
        str: Path to generated chart
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print("\n[Net Export Revenue - Slide Chart]")
    print("-" * 60)
    df = load_tonnage_flows_data()

    # Calculate totals for each scenario
    print("\nCalculating net export revenues...")

    # Baseline 2022
    baseline = calculate_total_net_revenue(
        df, '2022_baseline', 'country_unconstrained'
    ) / 1e9
    print(f"  Baseline 2022: ${baseline:.0f}B")

    # BAU 2040 (only country/national - no regional distinction for BAU)
    bau = calculate_total_net_revenue(
        df, 'bau_2040_mid_min_threshold_metal_tons', 'country_unconstrained'
    ) / 1e9
    print(f"  BAU 2040: ${bau:.0f}B")

    # Early Refining 2040
    early_national = calculate_total_net_revenue(
        df, 'early_refining_2040_mid_min_threshold_metal_tons', 'country_unconstrained'
    ) / 1e9
    early_regional = calculate_total_net_revenue(
        df, 'early_refining_2040_mid_max_threshold_metal_tons', 'region_unconstrained'
    ) / 1e9
    print(f"  Early Refining - National: ${early_national:.0f}B, Regional: ${early_regional:.0f}B")

    # Precursor 2040
    prec_national = calculate_total_net_revenue(
        df, 'precursor_2040_mid_min_threshold_metal_tons', 'country_unconstrained'
    ) / 1e9
    prec_regional = calculate_total_net_revenue(
        df, 'precursor_2040_mid_max_threshold_metal_tons', 'region_unconstrained'
    ) / 1e9
    print(f"  Precursor - National: ${prec_national:.0f}B, Regional: ${prec_regional:.0f}B")

    # --- Create the visualization ---
    print("\nGenerating chart...")

    # Colors
    COLOR_NATIONAL = '#4a86c7'  # Steel blue
    COLOR_REGIONAL = '#e8744f'  # Coral
    COLOR_BAU = '#7a7a7a'       # Gray for BAU (no policy distinction)
    COLOR_BASELINE = '#2d2d2d'  # Dark gray for baseline reference

    # Figure setup - compact for slide
    fig, ax = plt.subplots(figsize=(8, 5))

    # Data structure: (label, value, color, is_regional)
    # We'll plot from bottom to top
    bars_data = [
        ('BAU (2040)', bau, COLOR_BAU, None),
        ('Early Refining - National', early_national, COLOR_NATIONAL, False),
        ('Early Refining - Regional', early_regional, COLOR_REGIONAL, True),
        ('Precursor - National', prec_national, COLOR_NATIONAL, False),
        ('Precursor - Regional', prec_regional, COLOR_REGIONAL, True),
    ]

    y_positions = np.arange(len(bars_data))
    bar_height = 0.65

    # Plot horizontal bars
    for i, (label, value, color, is_regional) in enumerate(bars_data):
        bar = ax.barh(i, value, height=bar_height, color=color,
                      edgecolor='white', linewidth=0.5)

        # Value label at end of bar
        ax.text(value + 3, i, f'${value:.0f}B',
                va='center', ha='left', fontsize=12, fontweight='bold',
                color='#333333')

    # Add percentage increase annotations
    # Early Refining: National -> Regional
    early_pct = ((early_regional / early_national) - 1) * 100
    mid_y_early = 1.5  # Between bars at positions 1 and 2
    ax.annotate('', xy=(early_regional, 2), xytext=(early_regional, 1),
                arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))
    ax.text(early_regional + 8, mid_y_early, f'+{early_pct:.0f}%',
            va='center', ha='left', fontsize=11, fontweight='bold',
            color='#e8744f')

    # Precursor: National -> Regional
    prec_pct = ((prec_regional / prec_national) - 1) * 100
    mid_y_prec = 3.5  # Between bars at positions 3 and 4
    ax.annotate('', xy=(prec_regional, 4), xytext=(prec_regional, 3),
                arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))
    ax.text(prec_regional + 8, mid_y_prec, f'+{prec_pct:.0f}%',
            va='center', ha='left', fontsize=11, fontweight='bold',
            color='#e8744f')

    # Baseline reference line
    ax.axvline(x=baseline, color=COLOR_BASELINE, linestyle='--',
               linewidth=2, alpha=0.7, zorder=0)
    ax.text(baseline + 2, -0.35, f'2022\nBaseline\n${baseline:.0f}B',
            va='top', ha='left', fontsize=9, fontweight='bold',
            color=COLOR_BASELINE)

    # Styling
    ax.set_yticks(y_positions)
    ax.set_yticklabels([b[0] for b in bars_data], fontsize=12)
    ax.set_xlabel('Net Export Revenue (Billion USD)', fontsize=13, fontweight='bold')

    # Set axis limits with room for labels
    max_val = max(early_regional, prec_regional)
    ax.set_xlim(0, max_val * 1.25)
    ax.set_ylim(-0.9, len(bars_data) - 0.5)

    # Light vertical gridlines
    ax.xaxis.grid(True, linestyle='--', alpha=0.3, zorder=0)
    ax.yaxis.grid(False)

    # Remove box frame
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Add subtle separator lines between scenario groups
    ax.axhline(y=0.5, color='#cccccc', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.axhline(y=2.5, color='#cccccc', linestyle='-', linewidth=0.5, alpha=0.5)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLOR_NATIONAL, edgecolor='white', label='National Policy'),
        Patch(facecolor=COLOR_REGIONAL, edgecolor='white', label='Regional Policy'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=11,
              frameon=True, fancybox=True, framealpha=0.9)

    # Title
    ax.set_title('Net Export Revenue by Policy Scenario',
                 fontsize=14, fontweight='bold', pad=15)

    # Tight layout
    plt.tight_layout()

    # Save
    output_path = os.path.join(output_dir, 'net_export_revenue_slide.png')
    plt.savefig(output_path, dpi=200, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)

    print(f"\n  Saved: {output_path}")
    print("-" * 60)

    return output_path


if __name__ == '__main__':
    """Standalone execution"""
    config = load_config()
    output_dir = Path(config['paths']['figures']) / 'automated_plots' / 'single_axis'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NET EXPORT REVENUE - SLIDE CHART")
    print("=" * 60)
    print(f"Output directory: {output_dir}")

    chart_path = generate_slide_chart(output_dir)

    print("\n" + "=" * 60)
    print("COMPLETED")
    print("=" * 60)
