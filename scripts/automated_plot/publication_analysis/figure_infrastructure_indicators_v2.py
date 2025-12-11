"""
Infrastructure Indicators Figure V2

Creates a 6-panel figure (2 columns × 3 rows) showing transport and energy infrastructure:
- Row 1: By Mineral (Transport Volume | Energy Capacity)
- Row 2: By Country (Transport Volume | Electricity Capacity Change %)
- Row 3: Costs (Transport Costs | Energy Costs)

Panel E is modified to show electricity capacity percentage change by country (Precursor scenarios only)
All other panels show 7 bars: Baseline + 2 BAU + 4 Precursor scenarios
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publication_analysis.config import (
    FIGURE_SIZES, DPI_PUBLICATION, DPI_SCREEN,
    PUBLICATION_STYLE
)
from publication_analysis.scenario_utils import (
    filter_scenarios_by_goal,
    extract_scenario_attributes
)
from plot_config import reference_mineral_colormap
from plot_utils import generate_country_colormap

# Scenario configuration (7 bars)
SCENARIO_CONFIG = [
    ('baseline', None, None, 'Baseline'),
    ('bau', 'min', 'constrained', 'BAU_C'),
    ('bau', 'min', 'unconstrained', 'BAU_U'),
    ('precursor', 'min', 'constrained', 'Prec_C_N'),
    ('precursor', 'min', 'unconstrained', 'Prec_U_N'),
    ('precursor', 'max', 'constrained', 'Prec_C_R'),
    ('precursor', 'max', 'unconstrained', 'Prec_U_R'),
]

# Mineral order
MINERAL_ORDER = ['copper', 'manganese', 'graphite', 'cobalt', 'nickel', 'lithium']

# Energy cost breakdown
ENERGY_COST_ORDER = ['Investment', 'Opex']
ENERGY_COST_COLORS = {
    'Investment': '#08519c',  # Dark blue
    'Opex': '#6baed6'  # Light blue
}

# Electricity capacity change data (from electricity_demand_changes.py)
# Percentage change relative to baseline for Precursor scenarios (unconstrained)
ELECTRICITY_CAPACITY_CHANGE = {
    "AGO": {"Prec_U_R": 3, "Prec_U_N": 0},    # Angola
    "BDI": {"Prec_U_R": 15, "Prec_U_N": 0},   # Burundi
    "BWA": {"Prec_U_R": 2, "Prec_U_N": 0},    # Botswana
    "COD": {"Prec_U_R": 35, "Prec_U_N": 31},  # DR of Congo
    "KEN": {"Prec_U_R": 0, "Prec_U_N": 0},    # Kenya
    "MDG": {"Prec_U_R": 6, "Prec_U_N": 0},    # Madagascar
    "MOZ": {"Prec_U_R": 4, "Prec_U_N": 1},    # Mozambique
    "MWI": {"Prec_U_R": 7, "Prec_U_N": 5},    # Malawi
    "NAM": {"Prec_U_R": 35, "Prec_U_N": 6},   # Namibia
    "TZA": {"Prec_U_R": 20, "Prec_U_N": 5},   # Tanzania
    "UGA": {"Prec_U_R": 0, "Prec_U_N": 0},    # Uganda
    "ZAF": {"Prec_U_R": 1, "Prec_U_N": 0},    # South Africa
    "ZMB": {"Prec_U_R": 5, "Prec_U_N": 2},    # Zambia
    "ZWE": {"Prec_U_R": 2, "Prec_U_N": 1}     # Zimbabwe
}


def get_top_countries(df, metric_col, n=8):
    """
    Get top N countries by total metric value across all scenarios

    Args:
        df: DataFrame
        metric_col: Column to aggregate
        n: Number of top countries

    Returns:
        list: Top N country ISO3 codes
    """
    country_totals = df.groupby('iso3')[metric_col].sum().nlargest(n)
    return country_totals.index.tolist()


def prepare_infrastructure_data(df):
    """
    Prepare data for infrastructure panels (A, B, C, E, F)
    Panel E uses separate electricity capacity change data

    Returns:
        tuple: Five dictionaries for panels A, B, C, E, F plus metadata
    """
    # Filter for processing only (stage > 0 for most metrics)
    df_processing = df[df['processing_stage'] > 0].copy()

    # Initialize data structures
    transport_mineral_data = {}
    energy_mineral_data = {}
    transport_country_data = {}
    transport_cost_data = {}
    energy_cost_data = {}

    # Get top 8 countries for transport and energy (to match original infrastructure figure)
    top_transport_countries = get_top_countries(df_processing, 'transport_total_tonkm', n=8)
    top_energy_countries = get_top_countries(df_processing, 'energy_req_capacity_kW', n=8)

    # Generate consistent country color mapping for all countries (sorted union)
    # This ensures colors are consistent with the original infrastructure indicators figure
    all_countries = sorted(set(top_transport_countries) | set(top_energy_countries))
    country_colormap = generate_country_colormap(all_countries)

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        transport_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        energy_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        transport_country_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        transport_cost_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        energy_cost_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        if goal == 'baseline':
            scenario_name = '2022_baseline'
            df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

            for demand in ['low', 'mid', 'high']:
                if df_scenario.empty:
                    continue

                # Transport by mineral
                by_mineral_transport = df_scenario.groupby('reference_mineral')['transport_total_tonkm'].sum()
                for mineral in MINERAL_ORDER:
                    transport_mineral_data[label][demand][mineral] = by_mineral_transport.get(mineral, 0) / 1e6  # Convert to Million tonkm

                # Energy capacity by mineral
                by_mineral_energy = df_scenario.groupby('reference_mineral')['energy_req_capacity_kW'].sum()
                for mineral in MINERAL_ORDER:
                    energy_mineral_data[label][demand][mineral] = by_mineral_energy.get(mineral, 0) / 1e6  # Convert to GW

                # Transport by country (top 8 + Other)
                by_country_transport = df_scenario.groupby('iso3')['transport_total_tonkm'].sum()
                for country in top_transport_countries:
                    transport_country_data[label][demand][country] = by_country_transport.get(country, 0) / 1e6
                other_transport = by_country_transport[~by_country_transport.index.isin(top_transport_countries)].sum()
                transport_country_data[label][demand]['Other'] = other_transport / 1e6

                # Transport costs by mineral
                df_scenario['total_transport_cost'] = df_scenario['export_transport_cost_usd'] + df_scenario['import_transport_cost_usd']
                by_mineral_transport_cost = df_scenario.groupby('reference_mineral')['total_transport_cost'].sum()
                for mineral in MINERAL_ORDER:
                    transport_cost_data[label][demand][mineral] = by_mineral_transport_cost.get(mineral, 0) / 1e9  # Billion USD

                # Energy costs by type
                total_investment = df_scenario['energy_investment_usd'].sum() / 1e9
                total_opex = df_scenario['energy_opex'].sum() / 1e9
                energy_cost_data[label][demand]['Investment'] = total_investment
                energy_cost_data[label][demand]['Opex'] = total_opex

        else:
            # Handle BAU and Precursor scenarios
            for demand in ['low', 'mid', 'high']:
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                df_scenario = df_processing[
                    (df_processing['scenario'] == scenario_name) &
                    (df_processing['constraint'] == constraint_col)
                ].copy()

                if df_scenario.empty:
                    print(f"Warning: No data for {label} {demand} demand")
                    continue

                # Transport by mineral
                by_mineral_transport = df_scenario.groupby('reference_mineral')['transport_total_tonkm'].sum()
                for mineral in MINERAL_ORDER:
                    transport_mineral_data[label][demand][mineral] = by_mineral_transport.get(mineral, 0) / 1e6

                # Energy capacity by mineral
                by_mineral_energy = df_scenario.groupby('reference_mineral')['energy_req_capacity_kW'].sum()
                for mineral in MINERAL_ORDER:
                    energy_mineral_data[label][demand][mineral] = by_mineral_energy.get(mineral, 0) / 1e6

                # Transport by country
                by_country_transport = df_scenario.groupby('iso3')['transport_total_tonkm'].sum()
                for country in top_transport_countries:
                    transport_country_data[label][demand][country] = by_country_transport.get(country, 0) / 1e6
                other_transport = by_country_transport[~by_country_transport.index.isin(top_transport_countries)].sum()
                transport_country_data[label][demand]['Other'] = other_transport / 1e6

                # Transport costs by mineral
                df_scenario['total_transport_cost'] = df_scenario['export_transport_cost_usd'] + df_scenario['import_transport_cost_usd']
                by_mineral_transport_cost = df_scenario.groupby('reference_mineral')['total_transport_cost'].sum()
                for mineral in MINERAL_ORDER:
                    transport_cost_data[label][demand][mineral] = by_mineral_transport_cost.get(mineral, 0) / 1e9

                # Energy costs by type
                total_investment = df_scenario['energy_investment_usd'].sum() / 1e9
                total_opex = df_scenario['energy_opex'].sum() / 1e9
                energy_cost_data[label][demand]['Investment'] = total_investment
                energy_cost_data[label][demand]['Opex'] = total_opex

    return (transport_mineral_data, energy_mineral_data,
            transport_country_data, transport_cost_data, energy_cost_data,
            top_transport_countries, country_colormap)


def plot_stacked_panel(ax, data, stack_order, colors, title, xlabel):
    """
    Plot a single panel with horizontal stacked bars

    Args:
        ax: Matplotlib axis
        data: Nested dict [scenario_label][demand][stack_category] = value
        stack_order: List of categories for stacking
        colors: Dict mapping categories to colors
        title: Panel title
        xlabel: X-axis label
    """
    n_bars = len(SCENARIO_CONFIG)
    y_positions = np.arange(n_bars, dtype=float)

    # Add gaps
    baseline_gap = 0.6
    bau_precursor_gap = 0.8
    y_positions[1:] += baseline_gap
    y_positions[3:] += bau_precursor_gap

    bar_height = 0.7

    for i, (goal, policy, constraint, label) in enumerate(SCENARIO_CONFIG):
        mid_values = data[label]['mid']
        low_values = data[label]['low']
        high_values = data[label]['high']

        # Calculate total for error bar
        total_mid = sum(mid_values.get(cat, 0) for cat in stack_order)
        total_low = sum(low_values.get(cat, 0) for cat in stack_order)
        total_high = sum(high_values.get(cat, 0) for cat in stack_order)

        # Stack bars
        left = 0
        for category in stack_order:
            value = mid_values.get(category, 0)
            if value > 0:
                color = colors.get(category, '#999999')
                hatch = '////' if constraint == 'constrained' else None

                ax.barh(y_positions[i], value, bar_height, left=left,
                       color=color, edgecolor='black', linewidth=0.8,
                       hatch=hatch)
                left += value

        # Error bar (handle potential negative values)
        if goal != 'baseline':
            error_low = max(0, total_mid - total_low)
            error_high = max(0, total_high - total_mid)
            if error_low > 0 or error_high > 0:
                ax.errorbar(total_mid, y_positions[i], xerr=[[error_low], [error_high]],
                           fmt='none', ecolor='black', capsize=3, capthick=1.5, zorder=10)

    # Formatting
    ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_yticks(y_positions)
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)
    ax.invert_yaxis()

    # Separator lines
    baseline_separator_y = (y_positions[0] + y_positions[1]) / 2
    bau_precursor_separator_y = (y_positions[2] + y_positions[3]) / 2
    ax.axhline(baseline_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(bau_precursor_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    return y_positions


def plot_electricity_capacity_change_panel(ax):
    """
    Plot Panel E: Electricity capacity change by country (Precursor scenarios only)
    Uses grouped horizontal bars sorted by Regional Precursor value (descending)

    Args:
        ax: Matplotlib axis
    """
    # Prepare data and sort by Regional Precursor value
    countries = list(ELECTRICITY_CAPACITY_CHANGE.keys())
    regional_values = [ELECTRICITY_CAPACITY_CHANGE[c]["Prec_U_R"] for c in countries]
    national_values = [ELECTRICITY_CAPACITY_CHANGE[c]["Prec_U_N"] for c in countries]

    # Sort by regional value (descending)
    sorted_indices = np.argsort(regional_values)[::-1]
    countries_sorted = [countries[i] for i in sorted_indices]
    regional_sorted = [regional_values[i] for i in sorted_indices]
    national_sorted = [national_values[i] for i in sorted_indices]

    # Create grouped horizontal bars
    n_countries = len(countries_sorted)
    y_positions = np.arange(n_countries)
    bar_height = 0.35

    # Colors for the two scenarios
    color_regional = '#2b8cbe'  # Blue for Regional
    color_national = '#f46d43'  # Orange for National

    # Plot bars
    ax.barh(y_positions - bar_height/2, regional_sorted, bar_height,
            label='Prec_U_R', color=color_regional, edgecolor='black', linewidth=0.8)
    ax.barh(y_positions + bar_height/2, national_sorted, bar_height,
            label='Prec_U_N', color=color_national, edgecolor='black', linewidth=0.8)

    # Formatting
    ax.set_xlabel('Percentage Change from Baseline (%)', fontsize=11, fontweight='bold')
    ax.set_title('E) Electricity Capacity Change by Country', fontsize=12, fontweight='bold', pad=10)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(countries_sorted, fontsize=9)
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)
    ax.invert_yaxis()

    # Legend positioned outside plot area (consistent with other panels)
    legend_capacity = ax.legend(
        title='Precursor\nScenarios',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=8,
        title_fontsize=9,
        framealpha=0.98,
        edgecolor='black'
    )

    return legend_capacity


def generate_infrastructure_indicators_v2_figures(df, output_dir):
    """
    Main entry point for generating infrastructure indicators V2 figure

    Args:
        df: Main data DataFrame
        output_dir: Output directory

    Returns:
        List of saved file paths
    """
    print("  Generating infrastructure indicators V2 6-panel figure...")

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Prepare data
    (transport_mineral_data, energy_mineral_data,
     transport_country_data, transport_cost_data, energy_cost_data,
     top_transport_countries, country_colormap) = prepare_infrastructure_data(df)

    # Create figure with 6 panels (2 columns × 3 rows)
    # Wider figure to accommodate legends without cropping
    fig, axes = plt.subplots(3, 2, figsize=(17, 10))
    fig.subplots_adjust(hspace=0.55, wspace=0.60, right=0.68, top=0.92, bottom=0.06)

    # Unpack axes
    ax_transport_mineral = axes[0, 0]
    ax_energy_mineral = axes[0, 1]
    ax_transport_country = axes[1, 0]
    ax_energy_country = axes[1, 1]  # This will be the new panel D
    ax_transport_cost = axes[2, 0]
    ax_energy_cost = axes[2, 1]

    # Row 1: By Mineral
    plot_stacked_panel(
        ax_transport_mineral, transport_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='B) Transport Volume by Mineral',
        xlabel='Transport Volume (Million tonne-km)'
    )

    plot_stacked_panel(
        ax_energy_mineral, energy_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='C) Installed Electricity Capacity by Mineral',
        xlabel='Capacity (GW)'
    )

    # Row 2: Panel D (transport by country) and Panel E (electricity capacity change)
    country_order_transport = top_transport_countries + ['Other']
    country_colors_transport = {country: country_colormap.get(country, '#999999') for country in top_transport_countries}
    country_colors_transport['Other'] = '#999999'

    plot_stacked_panel(
        ax_transport_country, transport_country_data,
        stack_order=country_order_transport,
        colors=country_colors_transport,
        title='D) Transport Volume by Country',
        xlabel='Transport Volume (Million tonne-km)'
    )

    # NEW Panel E: Electricity capacity change
    legend_capacity_change = plot_electricity_capacity_change_panel(ax_energy_country)
    ax_energy_country.add_artist(legend_capacity_change)

    # Row 3: Costs
    plot_stacked_panel(
        ax_transport_cost, transport_cost_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='F) Transport Costs',
        xlabel='Cost (Billion USD)'
    )

    plot_stacked_panel(
        ax_energy_cost, energy_cost_data,
        stack_order=ENERGY_COST_ORDER,
        colors=ENERGY_COST_COLORS,
        title='G) Energy Costs',
        xlabel='Cost (Billion USD)'
    )

    # Set y-axis labels for panels B, C, D, F, G (not E which has country names)
    y_labels = [label for _, _, _, label in SCENARIO_CONFIG]
    for ax in [ax_transport_mineral, ax_energy_mineral, ax_transport_country, ax_transport_cost, ax_energy_cost]:
        ax.set_yticklabels(y_labels, fontsize=9)

    # Create legends positioned outside plot area
    # Mineral legend (for row 1 and transport costs)
    mineral_patches = []
    for mineral in MINERAL_ORDER:
        color = reference_mineral_colormap.get(mineral, '#999999')
        label = mineral.capitalize()
        patch = mpatches.Patch(facecolor=color, label=label, edgecolor='black', linewidth=0.8)
        mineral_patches.append(patch)

    legend_minerals = ax_energy_mineral.legend(handles=mineral_patches,
                                               title='Minerals',
                                               bbox_to_anchor=(1.02, 1),
                                               loc='upper left',
                                               fontsize=8,
                                               title_fontsize=9,
                                               framealpha=0.98,
                                               edgecolor='black')

    # Country legend for Panel D
    transport_country_patches = []
    for country in (top_transport_countries + ['Other']):
        color = country_colors_transport[country]
        patch = mpatches.Patch(facecolor=color, label=country, edgecolor='black', linewidth=0.8)
        transport_country_patches.append(patch)

    legend_transport_countries = ax_transport_country.legend(
        handles=transport_country_patches,
        title='Countries (Transport)',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=7,
        title_fontsize=8,
        framealpha=0.98,
        edgecolor='black',
        ncol=1
    )
    ax_transport_country.add_artist(legend_transport_countries)

    # Energy cost type legend
    energy_cost_patches = []
    for cost_type in ENERGY_COST_ORDER:
        color = ENERGY_COST_COLORS[cost_type]
        patch = mpatches.Patch(facecolor=color, label=cost_type, edgecolor='black', linewidth=0.8)
        energy_cost_patches.append(patch)

    legend_energy = ax_energy_cost.legend(handles=energy_cost_patches,
                                          title='Energy Cost\nComponents',
                                          bbox_to_anchor=(1.02, 1),
                                          loc='upper left',
                                          fontsize=8,
                                          title_fontsize=9,
                                          framealpha=0.98,
                                          edgecolor='black')

    # Constraint & Uncertainty legend (for panels A, B, C, E, F)
    constraint_patches = [
        mpatches.Patch(facecolor='white', hatch='////', edgecolor='black',
                      label='Constrained'),
        mpatches.Patch(facecolor='white', edgecolor='black',
                      label='Unconstrained')
    ]
    error_patch = mpatches.Patch(facecolor='none', edgecolor='none',
                                 label='Error bars: Low-High demand')

    legend_constraint = ax_energy_mineral.legend(handles=constraint_patches + [error_patch],
                                                 title='Constraint &\nUncertainty',
                                                 bbox_to_anchor=(1.02, 0.40),
                                                 loc='upper left',
                                                 fontsize=8,
                                                 title_fontsize=9,
                                                 framealpha=0.98,
                                                 edgecolor='black')

    # Keep legends
    ax_energy_mineral.add_artist(legend_minerals)
    ax_energy_mineral.add_artist(legend_constraint)
    ax_energy_cost.add_artist(legend_energy)

    # Ensure consistent x-axis for cost panels (E and F)
    max_cost_xlim = max(ax_transport_cost.get_xlim()[1], ax_energy_cost.get_xlim()[1])
    ax_transport_cost.set_xlim(0, max_cost_xlim)
    ax_energy_cost.set_xlim(0, max_cost_xlim)

    # Overall title
    # fig.suptitle('Infrastructure Indicators: Baseline, BAU vs Precursor\n' +
    #              '(Mid-demand with Low-High range; Panel D: Unconstrained Precursor only)',
    #              fontsize=13, fontweight='bold', y=0.985)

    # Note
    # fig.text(0.5, 0.005,
    #          'Note: BAU scenarios have no National/Regional distinction (identical outcomes). Panel D shows Precursor scenarios only.',
    #          fontsize=7, style='italic', color='gray', ha='center',
    #          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3, pad=0.3))

    # Save figure
    # Collect all legend artists to ensure they're included in bbox calculation
    all_artists = [
        legend_minerals,
        legend_constraint,
        legend_transport_countries,
        legend_capacity_change,
        legend_energy
    ]

    saved_paths = []

    png_path = os.path.join(output_dir, 'infrastructure_indicators_v2_six_panel.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight',
                bbox_extra_artists=all_artists, facecolor='white')
    saved_paths.append(png_path)
    print(f"    ✓ Saved: {os.path.basename(png_path)}")

    pdf_path = os.path.join(output_dir, 'infrastructure_indicators_v2_six_panel.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight',
                bbox_extra_artists=all_artists, facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    ✓ Saved: {os.path.basename(pdf_path)}")

    preview_path = os.path.join(output_dir, 'infrastructure_indicators_v2_six_panel_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight',
                bbox_extra_artists=all_artists, facecolor='white')
    saved_paths.append(preview_path)
    print(f"    ✓ Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


if __name__ == '__main__':
    """Test the figure generation"""
    import json

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load data
    data_file = os.path.join(config['paths']['results'], 'all_data.xlsx')
    df = pd.read_excel(data_file, index_col=[0,1,2,3,4]).reset_index()

    # Create output directory
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'publication', 'infrastructure_indicators_v2')
    os.makedirs(output_dir, exist_ok=True)

    # Generate figure
    print("Testing infrastructure indicators V2 figure generation...")
    paths = generate_infrastructure_indicators_v2_figures(df, output_dir)
    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
