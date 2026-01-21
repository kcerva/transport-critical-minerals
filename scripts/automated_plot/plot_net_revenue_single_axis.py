"""
Regional Net Export Revenue Single-Axis Charts
Generates single-axis stacked bar charts showing regional net export revenues
(export revenue - import cost) by mineral across scenarios.

IMPORTANT: Uses MARKET PRICE basis for imports (import_cost_at_price_usd)
This reflects actual cash flows and trade balance.

Data source: tonnage_flows_with_revenues.xlsx
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plot_config import reference_mineral_colormap


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
    print(f"  ✓ Loaded {len(df):,} flow records")

    return df


def calculate_regional_net_revenue(df, scenario, constraint):
    """
    Calculate regional net export revenue for a specific scenario/constraint

    Args:
        df: Tonnage flows DataFrame
        scenario: Scenario name (e.g., '2022_baseline', 'bau_2040_mid_min_threshold_metal_tons')
        constraint: Constraint type (e.g., 'country_unconstrained', 'region_constrained')

    Returns:
        dict: {mineral: net_revenue} in USD
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # Filter for scenario and constraint
    df_scenario = df[
        (df['scenario'] == scenario) &
        (df['constraint'] == constraint)
    ].copy()

    if df_scenario.empty:
        print(f"  Warning: No data for {scenario} / {constraint}")
        return {m: 0 for m in minerals}

    # Calculate exports by mineral
    exports = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('reference_mineral')['export_revenue_usd'].sum()

    # Calculate imports by mineral (both CCG and NonCCG) - USING MARKET PRICE BASIS
    imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('reference_mineral')['import_cost_at_price_usd'].sum()

    # Calculate net revenue for each mineral
    net_revenue = {}
    for mineral in minerals:
        export_rev = exports.get(mineral, 0)
        import_cost = imports.get(mineral, 0)
        net_revenue[mineral] = export_rev - import_cost

    return net_revenue


def extract_regional_net_revenue_clean(df):
    """
    Extract regional net revenue data for clean chart (6 bars: baseline + unconstrained scenarios)

    Returns:
        List of tuples: [(label, [cobalt, copper, graphite, lithium, manganese, nickel]), ...]
        Values in Billion USD
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # Bar 1: Baseline 2022
    net_rev_baseline = calculate_regional_net_revenue(df, '2022_baseline', 'country_unconstrained')
    baseline_values = [net_rev_baseline[m] / 1e9 for m in minerals]

    # Bar 2: BAU 2040 Unconstrained (use country_unconstrained)
    net_rev_bau = calculate_regional_net_revenue(df, 'bau_2040_mid_min_threshold_metal_tons', 'country_unconstrained')
    bau_values = [net_rev_bau[m] / 1e9 for m in minerals]

    # Bar 3: Early Refining 2040 Country Unconstrained
    net_rev_early_country = calculate_regional_net_revenue(df, 'early_refining_2040_mid_min_threshold_metal_tons', 'country_unconstrained')
    early_country_values = [net_rev_early_country[m] / 1e9 for m in minerals]

    # Bar 4: Early Refining 2040 Region Unconstrained
    net_rev_early_region = calculate_regional_net_revenue(df, 'early_refining_2040_mid_max_threshold_metal_tons', 'region_unconstrained')
    early_region_values = [net_rev_early_region[m] / 1e9 for m in minerals]

    # Bar 5: Precursor 2040 Country Unconstrained
    net_rev_prec_country = calculate_regional_net_revenue(df, 'precursor_2040_mid_min_threshold_metal_tons', 'country_unconstrained')
    prec_country_values = [net_rev_prec_country[m] / 1e9 for m in minerals]

    # Bar 6: Precursor 2040 Region Unconstrained
    net_rev_prec_region = calculate_regional_net_revenue(df, 'precursor_2040_mid_max_threshold_metal_tons', 'region_unconstrained')
    prec_region_values = [net_rev_prec_region[m] / 1e9 for m in minerals]

    bars = [
        ("Baseline", baseline_values),
        ("Unconstrained", bau_values),
        ("Country Unconstrained", early_country_values),
        ("Region Unconstrained", early_region_values),
        ("Country Unconstrained", prec_country_values),
        ("Region Unconstrained", prec_region_values),
    ]

    return bars


def extract_regional_net_revenue_comparison(df):
    """
    Extract regional net revenue data for comparison chart (10 bars: all constrained/unconstrained)

    Returns:
        List of tuples: [(label, [cobalt, copper, graphite, lithium, manganese, nickel]), ...]
        Values in Billion USD
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    scenarios = [
        ('bau_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Constrained'),
        ('bau_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Unconstrained'),
        ('early_refining_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Country Constrained'),
        ('early_refining_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Country Unconstrained'),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_constrained', 'Region Constrained'),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Region Unconstrained'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Country Constrained'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Country Unconstrained'),
        ('precursor_2040_mid_max_threshold_metal_tons', 'region_constrained', 'Region Constrained'),
        ('precursor_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Region Unconstrained'),
    ]

    bars = []
    for scenario, constraint, label in scenarios:
        net_rev = calculate_regional_net_revenue(df, scenario, constraint)
        values = [net_rev[m] / 1e9 for m in minerals]
        bars.append((label, values))

    return bars


def generate_regional_net_revenue_charts(output_dir):
    """
    Generate regional net export revenue single-axis charts

    Args:
        output_dir: Output directory for charts

    Returns:
        dict: Paths to generated charts
    """
    from plot_emissions_water_all_countries import plot_clean_stacks

    os.makedirs(output_dir, exist_ok=True)

    chart_paths = {}

    # Load data
    print("\n[Regional Net Export Revenue Single-Axis Charts]")
    print("-" * 80)
    df = load_tonnage_flows_data()

    # Common parameters for clean version (6 bars)
    centers_clean = [0, 1, (2+3)/2, (4+5)/2]
    headings_clean = ["Baseline (2022)", "BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    # Common parameters for comparison version (10 bars)
    centers_comp = [(0+1)/2, (2+3+4+5)/4, (6+7+8+9)/4]
    headings_comp = ["BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    print("\nGenerating regional net export revenue charts...")

    # Clean version (6 bars: baseline + unconstrained)
    try:
        print("  Extracting data for clean version...")
        net_revenue_bars_clean = extract_regional_net_revenue_clean(df)

        output_path_clean = os.path.join(output_dir, "net_export_revenue_single_axis_clean.png")

        print("  Creating clean version chart...")
        plot_clean_stacks(
            bars=net_revenue_bars_clean,
            ylabel="Net Export Revenue (Billion USD)",
            total_fmt=lambda v: f"{v:.0f}",
            seg_label_threshold=max([sum(bar[1]) for bar in net_revenue_bars_clean]) * 0.05,  # 5% of max
            centers=centers_clean,
            headings=headings_clean,
            outfile=output_path_clean
        )
        chart_paths['net_revenue_clean'] = output_path_clean
        print(f"  ✓ Saved: {output_path_clean}")
    except Exception as e:
        print(f"  ✗ Clean version failed: {e}")
        import traceback
        traceback.print_exc()

    # Comparison version (10 bars: all constrained/unconstrained)
    try:
        print("  Extracting data for comparison version...")
        net_revenue_bars_comp = extract_regional_net_revenue_comparison(df)

        output_path_comp = os.path.join(output_dir, "net_export_revenue_single_axis_constrained_vs_unconstrained.png")

        print("  Creating comparison version chart...")
        plot_clean_stacks(
            bars=net_revenue_bars_comp,
            ylabel="Net Export Revenue (Billion USD)",
            total_fmt=lambda v: f"{v:.0f}",
            seg_label_threshold=max([sum(bar[1]) for bar in net_revenue_bars_comp]) * 0.05,
            centers=centers_comp,
            headings=headings_comp,
            outfile=output_path_comp
        )
        chart_paths['net_revenue_comparison'] = output_path_comp
        print(f"  ✓ Saved: {output_path_comp}")
    except Exception as e:
        print(f"  ✗ Comparison version failed: {e}")
        import traceback
        traceback.print_exc()

    print(f"\nGenerated {len(chart_paths)} charts")
    print("-" * 80)

    return chart_paths


if __name__ == '__main__':
    """Standalone execution for testing"""
    config = load_config()
    output_dir = Path(config['paths']['figures']) / 'automated_plots' / 'single_axis'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("REGIONAL NET EXPORT REVENUE SINGLE-AXIS CHARTS")
    print("=" * 80)
    print(f"Output directory: {output_dir}")

    chart_paths = generate_regional_net_revenue_charts(output_dir)

    print("\n" + "=" * 80)
    print(f"COMPLETED - Generated {len(chart_paths)} charts")
    print("=" * 80)
