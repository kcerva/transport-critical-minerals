"""
Net Export Revenue - Slide-Ready Horizontal Stacked Bar Chart by Country

Creates a compact, visually appealing horizontal stacked bar chart showing
net export revenue by scenario, with each bar broken down by top 3 contributing
countries (per scenario) plus "Other".

Output: net_export_revenue_slide_by_country.png
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

from plot_utils import generate_country_colormap

# Country name mapping (consistent with publication folder)
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


def calculate_country_net_revenues(df, scenario, constraint):
    """
    Calculate net export revenue by country for a specific scenario/constraint.

    Uses MARKET PRICE basis for imports (import_cost_at_price_usd).

    Returns:
        dict: {iso3: net_revenue_usd}
    """
    # Filter for scenario and constraint
    df_scenario = df[
        (df['scenario'] == scenario) &
        (df['constraint'] == constraint)
    ].copy()

    if df_scenario.empty:
        print(f"  Warning: No data for {scenario} / {constraint}")
        return {}

    # Calculate exports by country
    exports = df_scenario[
        df_scenario['trade_type'] == 'Export'
    ].groupby('iso3')['export_revenue_usd'].sum()

    # Calculate imports by country (using market price basis)
    imports = df_scenario[
        df_scenario['trade_type'].str.contains('Import', na=False)
    ].groupby('iso3')['import_cost_at_price_usd'].sum()

    # Get all countries
    all_countries = set(exports.index) | set(imports.index)

    # Calculate net revenue for each country
    net_revenues = {}
    for country in all_countries:
        export_rev = exports.get(country, 0)
        import_cost = imports.get(country, 0)
        net_revenues[country] = export_rev - import_cost

    return net_revenues


def get_top3_and_other(country_revenues):
    """
    Get top 3 countries and sum the rest as "Other".

    Args:
        country_revenues: dict {iso3: net_revenue_usd}

    Returns:
        dict: {iso3_or_Other: net_revenue_usd} with exactly 4 keys
    """
    # Sort by revenue descending
    sorted_countries = sorted(country_revenues.items(), key=lambda x: x[1], reverse=True)

    result = {}
    other_total = 0

    for i, (country, revenue) in enumerate(sorted_countries):
        if i < 3:
            result[country] = revenue
        else:
            other_total += revenue

    result['Other'] = other_total

    return result


def generate_slide_chart_by_country(output_dir):
    """
    Generate slide-ready horizontal stacked bar chart by country.

    Args:
        output_dir: Output directory for the chart

    Returns:
        str: Path to generated chart
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print("\n[Net Export Revenue - Slide Chart by Country]")
    print("-" * 60)
    df = load_tonnage_flows_data()

    # Define scenarios to show
    scenarios = [
        ('bau_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'BAU (2040)', None),
        ('early_refining_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Early Refining\n- National', 'national'),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Early Refining\n- Regional', 'regional'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Precursor\n- National', 'national'),
        ('precursor_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Precursor\n- Regional', 'regional'),
    ]

    # Calculate baseline for reference line
    baseline_revenues = calculate_country_net_revenues(df, '2022_baseline', 'country_unconstrained')
    baseline_total = sum(baseline_revenues.values()) / 1e9
    print(f"\nBaseline 2022 total: ${baseline_total:.0f}B")

    # Calculate country breakdowns for each scenario
    print("\nCalculating country breakdowns...")
    scenario_data = []
    all_top_countries = set()

    for scenario, constraint, label, policy_type in scenarios:
        country_revenues = calculate_country_net_revenues(df, scenario, constraint)
        top3_other = get_top3_and_other(country_revenues)

        # Convert to billions
        top3_other_b = {k: v / 1e9 for k, v in top3_other.items()}

        # Track all countries that appear in top 3
        for country in top3_other_b.keys():
            if country != 'Other':
                all_top_countries.add(country)

        total = sum(top3_other_b.values())
        print(f"  {label.replace(chr(10), ' ')}: ${total:.0f}B - Top 3: {[k for k in top3_other_b.keys() if k != 'Other']}")

        scenario_data.append({
            'label': label,
            'policy_type': policy_type,
            'breakdown': top3_other_b,
            'total': total
        })

    # Generate consistent color mapping for all countries that appear
    print(f"\nCountries in top 3 across scenarios: {sorted(all_top_countries)}")
    country_colors = generate_country_colormap(sorted(all_top_countries))
    country_colors['Other'] = '#d7d7d7'  # Light gray for Other

    # --- Create the visualization ---
    print("\nGenerating chart...")

    fig, ax = plt.subplots(figsize=(8, 5.5))

    y_positions = np.arange(len(scenarios))
    bar_height = 0.65

    # Plot stacked horizontal bars
    for i, data in enumerate(scenario_data):
        breakdown = data['breakdown']
        left = 0

        # Sort segments: top 3 countries (by value descending), then Other
        countries_sorted = sorted(
            [(k, v) for k, v in breakdown.items() if k != 'Other'],
            key=lambda x: x[1],
            reverse=True
        )
        countries_sorted.append(('Other', breakdown.get('Other', 0)))

        for country, value in countries_sorted:
            color = country_colors.get(country, '#d7d7d7')
            ax.barh(i, value, left=left, height=bar_height,
                    color=color, edgecolor='white', linewidth=0.5)

            # Add country label inside segment if wide enough (use ISO3 codes)
            if value > data['total'] * 0.08:  # Show label if segment > 8% of total
                label_text = country  # Use ISO3 code (e.g., ZAF, COD, TZA)
                ax.text(left + value / 2, i, label_text,
                        va='center', ha='center', fontsize=9,
                        color='white' if country != 'Other' else '#555555',
                        fontweight='bold')

            left += value

        # Total value label at end of bar
        ax.text(data['total'] + 3, i, f"${data['total']:.0f}B",
                va='center', ha='left', fontsize=11, fontweight='bold',
                color='#333333')

    # Add percentage increase annotations
    # Early Refining: National (index 1) -> Regional (index 2)
    early_national = scenario_data[1]['total']
    early_regional = scenario_data[2]['total']
    early_pct = ((early_regional / early_national) - 1) * 100
    ax.annotate('', xy=(early_regional, 2), xytext=(early_regional, 1),
                arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))
    ax.text(early_regional + 8, 1.5, f'+{early_pct:.0f}%',
            va='center', ha='left', fontsize=10, fontweight='bold',
            color='#e8744f')

    # Precursor: National (index 3) -> Regional (index 4)
    prec_national = scenario_data[3]['total']
    prec_regional = scenario_data[4]['total']
    prec_pct = ((prec_regional / prec_national) - 1) * 100
    ax.annotate('', xy=(prec_regional, 4), xytext=(prec_regional, 3),
                arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))
    ax.text(prec_regional + 8, 3.5, f'+{prec_pct:.0f}%',
            va='center', ha='left', fontsize=10, fontweight='bold',
            color='#e8744f')

    # Baseline reference line
    ax.axvline(x=baseline_total, color='#2d2d2d', linestyle='--',
               linewidth=2, alpha=0.7, zorder=0)
    ax.text(baseline_total + 2, -0.35, f'2022\nBaseline\n${baseline_total:.0f}B',
            va='top', ha='left', fontsize=9, fontweight='bold',
            color='#2d2d2d')

    # Styling
    ax.set_yticks(y_positions)
    ax.set_yticklabels([s['label'] for s in scenario_data], fontsize=11)
    ax.set_xlabel('Net Export Revenue (Billion USD)', fontsize=12, fontweight='bold')

    # Set axis limits
    max_val = max(s['total'] for s in scenario_data)
    ax.set_xlim(0, max_val * 1.25)
    ax.set_ylim(-0.9, len(scenarios) - 0.5)

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

    # Legend - show all countries that appear plus Other
    from matplotlib.patches import Patch
    legend_elements = []
    for country in sorted(all_top_countries):
        name = COUNTRY_NAMES.get(country, country)
        legend_elements.append(Patch(facecolor=country_colors[country],
                                     edgecolor='white', label=name))
    legend_elements.append(Patch(facecolor='#d7d7d7', edgecolor='white', label='Other'))

    ax.legend(handles=legend_elements, loc='lower right', fontsize=9,
              frameon=True, fancybox=True, framealpha=0.9, ncol=2)

    # Title
    ax.set_title('Net Export Revenue by Policy Scenario\n(Top 3 Countries per Scenario)',
                 fontsize=13, fontweight='bold', pad=10)

    # Tight layout
    plt.tight_layout()

    # Save
    output_path = os.path.join(output_dir, 'net_export_revenue_slide_by_country.png')
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
    print("NET EXPORT REVENUE - SLIDE CHART BY COUNTRY")
    print("=" * 60)
    print(f"Output directory: {output_dir}")

    chart_path = generate_slide_chart_by_country(output_dir)

    print("\n" + "=" * 60)
    print("COMPLETED")
    print("=" * 60)
