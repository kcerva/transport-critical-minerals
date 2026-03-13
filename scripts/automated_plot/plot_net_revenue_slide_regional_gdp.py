"""
Net Export Revenue - Regional Policy Scenarios with GDP Share

Two-panel visualization:
- Left: Stacked horizontal bars showing total net export revenue by country
  for BAU and Early Refining under Regional policy
- Right: Horizontal bars showing Early Refining net export revenue as share of GDP

Output: net_export_revenue_slide_regional_gdp.png
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plot_utils import generate_country_colormap

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

# Scenario colors
SCENARIO_COLORS = {
    'BAU': '#1f77b4',           # Blue
    'Early Refining': '#2ca02c' # Green
}


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

    print(f"Loading tonnage flows from: {flows_path}")
    df = pd.read_excel(flows_path, sheet_name='All_Flows')
    print(f"  Loaded {len(df):,} flow records")

    return df


def load_gdp_data():
    """Load GDP data for countries from all_data.xlsx

    Note: all_data.xlsx already contains projected 2040 GDP values for 2040 scenarios.
    We extract these directly rather than applying inflation multipliers.
    """
    config = load_config()
    results_path = Path(config['paths']['results'])

    all_data_path = results_path / 'all_data.xlsx'

    print(f"Loading GDP data from: {all_data_path}")
    df = pd.read_excel(all_data_path)

    # Get 2040 GDP (already projected in the data for 2040 scenarios)
    df_2040 = df[df['scenario'].str.contains('2040')]
    gdp_2040 = df_2040[df_2040['gdp_usd'] > 0].groupby('iso3')['gdp_usd'].first().to_dict()

    print(f"  Loaded GDP data for {len(gdp_2040)} countries")

    return gdp_2040


def calculate_country_net_revenues(df, scenario, constraint):
    """Calculate net export revenue by country for a specific scenario/constraint."""
    df_scenario = df[
        (df['scenario'] == scenario) &
        (df['constraint'] == constraint)
    ].copy()

    if df_scenario.empty:
        return {}

    exports = df_scenario[
        df_scenario['trade_type'] == 'Export'
    ].groupby('iso3')['export_revenue_usd'].sum()

    imports = df_scenario[
        df_scenario['trade_type'].str.contains('Import', na=False)
    ].groupby('iso3')['import_cost_at_price_usd'].sum()

    all_countries = set(exports.index) | set(imports.index)
    return {c: exports.get(c, 0) - imports.get(c, 0) for c in all_countries}


def get_top_n_and_other(country_revenues, top_n=5):
    """Get top N countries and sum the rest as 'Other'."""
    sorted_countries = sorted(country_revenues.items(), key=lambda x: x[1], reverse=True)

    result = {}
    other_total = 0
    top_countries = []

    for i, (country, revenue) in enumerate(sorted_countries):
        if i < top_n:
            result[country] = revenue
            top_countries.append(country)
        else:
            other_total += revenue

    result['Other'] = other_total

    return result, top_countries


def calculate_gdp_share(net_revenue, gdp_value):
    """Calculate net export revenue as share of GDP (%)."""
    if gdp_value and gdp_value > 0:
        return (net_revenue / gdp_value) * 100
    return 0


def generate_dual_panel_chart(output_dir):
    """Generate dual-panel chart: revenue bars + GDP share bars (Early Refining only)."""
    os.makedirs(output_dir, exist_ok=True)

    print("\n[Net Export Revenue - Regional Policy with GDP Share]")
    print("-" * 70)

    # Load data
    df_flows = load_tonnage_flows_data()
    gdp_2040 = load_gdp_data()

    # Define scenarios (Regional policy - uses max_threshold with region_unconstrained)
    scenarios_config = [
        ('bau_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'BAU', gdp_2040),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Early Refining', gdp_2040),
    ]

    # First pass: collect all top countries across scenarios
    print("\nCalculating country revenues...")
    scenario_data = []
    all_top_countries = set()

    for scenario, constraint, label, gdp_dict in scenarios_config:
        country_revenues = calculate_country_net_revenues(df_flows, scenario, constraint)
        top_n_other, top_countries = get_top_n_and_other(country_revenues, top_n=5)

        # Convert to billions
        top_n_other_b = {k: v / 1e9 for k, v in top_n_other.items()}
        total = sum(top_n_other_b.values())

        all_top_countries.update(top_countries)

        print(f"  {label}: ${total:.0f}B total")
        print(f"    Top 5: {top_countries}")

        scenario_data.append({
            'label': label,
            'breakdown': top_n_other_b,
            'total': total,
            'top_countries': top_countries,
            'gdp_dict': gdp_dict,
            'country_revenues': country_revenues
        })

    # Second pass: calculate GDP shares for ALL countries that appear in any top 5
    print("\nCalculating GDP shares for all panel countries...")
    for data in scenario_data:
        gdp_shares = {}
        for country in all_top_countries:
            revenue = data['country_revenues'].get(country, 0)
            gdp = data['gdp_dict'].get(country, 0)
            gdp_shares[country] = calculate_gdp_share(revenue, gdp)
        data['gdp_shares'] = gdp_shares

        for c in data['top_countries'][:3]:
            print(f"    {data['label']} - {c}: ${data['breakdown'].get(c, 0):.1f}B ({gdp_shares[c]:.1f}% GDP)")

    # Generate consistent country colors
    all_top_countries_list = sorted(all_top_countries)
    country_colors = generate_country_colormap(all_top_countries_list)
    country_colors['Other'] = '#d7d7d7'

    # Determine which countries to show in GDP panel
    # Use Early Refining GDP shares for ordering (since that's the only one shown)
    er_data = next(s for s in scenario_data if s['label'] == 'Early Refining')
    gdp_panel_countries = []
    for country in all_top_countries_list:
        gdp_share = er_data['gdp_shares'].get(country, 0)
        gdp_panel_countries.append((country, gdp_share))
    gdp_panel_countries.sort(key=lambda x: x[1], reverse=True)
    gdp_panel_countries = [c[0] for c in gdp_panel_countries]

    # --- Create the visualization ---
    print("\nGenerating dual-panel chart...")

    fig, (ax_bars, ax_gdp) = plt.subplots(1, 2, figsize=(12, 5.5),
                                            gridspec_kw={'width_ratios': [1.2, 1]})

    # ========== LEFT PANEL: Stacked horizontal bars ==========
    y_positions = np.arange(len(scenarios_config))
    bar_height = 0.6

    for i, data in enumerate(scenario_data):
        breakdown = data['breakdown']
        left = 0

        # Sort segments: top countries by value, then Other
        countries_sorted = sorted(
            [(k, v) for k, v in breakdown.items() if k != 'Other'],
            key=lambda x: x[1], reverse=True
        )
        countries_sorted.append(('Other', breakdown.get('Other', 0)))

        for country, value in countries_sorted:
            color = country_colors.get(country, '#d7d7d7')
            ax_bars.barh(i, value, left=left, height=bar_height,
                         color=color, edgecolor='white', linewidth=0.5)

            # Add ISO3 label inside if segment is wide enough
            if value > 12:
                ax_bars.text(left + value / 2, i, country,
                             va='center', ha='center', fontsize=9,
                             color='white' if country != 'Other' else '#555555',
                             fontweight='bold')
            left += value

        # Total label
        ax_bars.text(data['total'] + 2, i, f"${data['total']:.0f}B",
                     va='center', ha='left', fontsize=11, fontweight='bold')

    ax_bars.set_yticks(y_positions)
    ax_bars.set_yticklabels([s['label'] for s in scenario_data], fontsize=11)
    ax_bars.set_xlabel('Net Export Revenue (Billion USD)', fontsize=11, fontweight='bold')
    ax_bars.set_title('Total Net Export Revenue\n(Regional Policy)', fontsize=12, fontweight='bold')

    max_val = max(s['total'] for s in scenario_data)
    ax_bars.set_xlim(0, max_val * 1.18)

    ax_bars.xaxis.grid(True, linestyle='--', alpha=0.3, zorder=0)
    ax_bars.spines['top'].set_visible(False)
    ax_bars.spines['right'].set_visible(False)
    ax_bars.spines['left'].set_visible(False)

    # Legend for countries (below the bars panel)
    legend_elements = [Patch(facecolor=country_colors[c], edgecolor='white',
                             label=COUNTRY_NAMES.get(c, c)) for c in all_top_countries_list]
    legend_elements.append(Patch(facecolor='#d7d7d7', edgecolor='white', label='Other'))
    ax_bars.legend(handles=legend_elements, loc='lower right', fontsize=8,
                   frameon=True, fancybox=True, ncol=2)

    # ========== RIGHT PANEL: GDP share bars (Early Refining only) ==========
    y_positions_bars = np.arange(len(gdp_panel_countries))
    bar_height_gdp = 0.6

    er_color = SCENARIO_COLORS['Early Refining']

    for i, country in enumerate(gdp_panel_countries):
        gdp_share = er_data['gdp_shares'].get(country, 0)

        ax_gdp.barh(i, gdp_share, height=bar_height_gdp,
                     color=er_color, edgecolor='white', linewidth=0.5)

        # Add value label at end of bar
        if gdp_share > 0:
            fontsize = 8 if gdp_share < 10 else 9
            ax_gdp.text(gdp_share + 1, i, f'{gdp_share:.0f}%',
                         va='center', ha='left', fontsize=fontsize,
                         color=er_color, fontweight='bold')

    ax_gdp.set_yticks(y_positions_bars)
    ax_gdp.set_yticklabels([COUNTRY_NAMES.get(c, c) for c in gdp_panel_countries], fontsize=11)
    ax_gdp.set_xlabel('Net Export Revenue as Share of GDP (%)', fontsize=11, fontweight='bold')
    ax_gdp.set_title('GDP Share by Country\n(Early Refining, Regional Policy)', fontsize=12, fontweight='bold')

    # Set x-axis limits
    max_gdp = max(er_data['gdp_shares'].values()) if er_data['gdp_shares'] else 10
    ax_gdp.set_xlim(0, max_gdp * 1.15)

    ax_gdp.xaxis.grid(True, linestyle='--', alpha=0.3, zorder=0)
    ax_gdp.yaxis.grid(False)
    ax_gdp.spines['top'].set_visible(False)
    ax_gdp.spines['right'].set_visible(False)
    ax_gdp.spines['left'].set_visible(False)

    plt.tight_layout()

    # Save
    output_path = os.path.join(output_dir, 'net_export_revenue_slide_regional_gdp.png')
    plt.savefig(output_path, dpi=200, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)

    print(f"\n  Saved: {output_path}")
    print("-" * 70)

    return output_path


if __name__ == '__main__':
    config = load_config()
    output_dir = Path(config['paths']['figures']) / 'automated_plots' / 'single_axis'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("NET EXPORT REVENUE - REGIONAL POLICY WITH GDP SHARE")
    print("=" * 70)

    chart_path = generate_dual_panel_chart(output_dir)

    print("\n" + "=" * 70)
    print("COMPLETED")
    print("=" * 70)
