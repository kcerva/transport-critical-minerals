"""
Environmental Indicators Figure

Creates a 6-panel figure (2 columns × 3 rows) showing emissions and water impacts:
- Row 1: By Mineral (Emissions | Water)
- Row 2: By Country (Emissions | Water)
- Row 3: By Source/Stage (Emissions by Source | Water by Stage)

All panels show 7 bars: Baseline + 2 BAU + 4 Precursor scenarios
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
from plot_utils import PROCESSING_TYPE_COLORS, generate_country_colormap

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

# Emission source breakdown
EMISSION_SOURCE_ORDER = ['Energy', 'Transport']
EMISSION_SOURCE_COLORS = {
    'Energy': '#4daf4a',  # Green
    'Transport': '#ff7f00'  # Orange
}

# Processing type order (for water breakdown)
PROCESSING_ORDER = ['Beneficiation', 'Early refining', 'Precursor related product']


def get_top_countries(df, metric_col, n=8):
    """Get top N countries by total metric value"""
    country_totals = df.groupby('iso3')[metric_col].sum().nlargest(n)
    return country_totals.index.tolist()


def prepare_environmental_data(df):
    """
    Prepare data for all 6 environmental panels

    Returns:
        tuple: Six dictionaries for each panel plus country lists
    """
    # Filter for processing only (stage > 0) - exclude extraction stage
    df_processing = df[df['processing_stage'] > 0].copy()

    # Calculate total CO2 (using transport_total_tonsCO2eq for complete transport emissions)
    df_processing['total_co2'] = (
        df_processing['energy_tonsCO2eq'] +
        df_processing['transport_total_tonsCO2eq']
    )

    # Initialize data structures
    emissions_mineral_data = {}
    water_mineral_data = {}
    emissions_country_data = {}
    water_country_data = {}
    emissions_source_data = {}
    water_processing_data = {}

    # Get top 8 countries
    top_emissions_countries = get_top_countries(df_processing, 'total_co2', n=8)
    top_water_countries = get_top_countries(df_processing, 'water_usage_m3', n=8)

    # Generate consistent country color mapping for all countries (sorted)
    all_countries = sorted(set(top_emissions_countries) | set(top_water_countries))
    country_colormap = generate_country_colormap(all_countries)

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        emissions_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        water_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        emissions_country_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        water_country_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        emissions_source_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        water_processing_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        if goal == 'baseline':
            scenario_name = '2022_baseline'
            df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

            for demand in ['low', 'mid', 'high']:
                if df_scenario.empty:
                    continue

                # Calculate total CO2 for baseline (using transport_total_tonsCO2eq)
                df_scenario['total_co2'] = (
                    df_scenario['energy_tonsCO2eq'] +
                    df_scenario['transport_total_tonsCO2eq']
                )

                # Emissions by mineral (kt CO2eq)
                by_mineral_emissions = df_scenario.groupby('reference_mineral')['total_co2'].sum()
                for mineral in MINERAL_ORDER:
                    emissions_mineral_data[label][demand][mineral] = by_mineral_emissions.get(mineral, 0) / 1000  # kt

                # Water by mineral (MCM)
                by_mineral_water = df_scenario.groupby('reference_mineral')['water_usage_m3'].sum()
                for mineral in MINERAL_ORDER:
                    water_mineral_data[label][demand][mineral] = by_mineral_water.get(mineral, 0) / 1e6  # MCM

                # Emissions by country
                by_country_emissions = df_scenario.groupby('iso3')['total_co2'].sum()
                for country in top_emissions_countries:
                    emissions_country_data[label][demand][country] = by_country_emissions.get(country, 0) / 1000
                other_emissions = by_country_emissions[~by_country_emissions.index.isin(top_emissions_countries)].sum()
                emissions_country_data[label][demand]['Other'] = other_emissions / 1000

                # Water by country
                by_country_water = df_scenario.groupby('iso3')['water_usage_m3'].sum()
                for country in top_water_countries:
                    water_country_data[label][demand][country] = by_country_water.get(country, 0) / 1e6
                other_water = by_country_water[~by_country_water.index.isin(top_water_countries)].sum()
                water_country_data[label][demand]['Other'] = other_water / 1e6

                # Emissions by source (using transport_total_tonsCO2eq)
                energy_emissions = df_scenario['energy_tonsCO2eq'].sum() / 1000
                transport_emissions = df_scenario['transport_total_tonsCO2eq'].sum() / 1000
                emissions_source_data[label][demand]['Energy'] = energy_emissions
                emissions_source_data[label][demand]['Transport'] = transport_emissions

                # Water by processing type
                by_processing_water = df_scenario.groupby('processing_type')['water_usage_m3'].sum()
                for ptype in PROCESSING_ORDER:
                    water_processing_data[label][demand][ptype] = by_processing_water.get(ptype, 0) / 1e6

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

                # Calculate total CO2 (using transport_total_tonsCO2eq)
                df_scenario['total_co2'] = (
                    df_scenario['energy_tonsCO2eq'] +
                    df_scenario['transport_total_tonsCO2eq']
                )

                # Emissions by mineral
                by_mineral_emissions = df_scenario.groupby('reference_mineral')['total_co2'].sum()
                for mineral in MINERAL_ORDER:
                    emissions_mineral_data[label][demand][mineral] = by_mineral_emissions.get(mineral, 0) / 1000

                # Water by mineral
                by_mineral_water = df_scenario.groupby('reference_mineral')['water_usage_m3'].sum()
                for mineral in MINERAL_ORDER:
                    water_mineral_data[label][demand][mineral] = by_mineral_water.get(mineral, 0) / 1e6

                # Emissions by country
                by_country_emissions = df_scenario.groupby('iso3')['total_co2'].sum()
                for country in top_emissions_countries:
                    emissions_country_data[label][demand][country] = by_country_emissions.get(country, 0) / 1000
                other_emissions = by_country_emissions[~by_country_emissions.index.isin(top_emissions_countries)].sum()
                emissions_country_data[label][demand]['Other'] = other_emissions / 1000

                # Water by country
                by_country_water = df_scenario.groupby('iso3')['water_usage_m3'].sum()
                for country in top_water_countries:
                    water_country_data[label][demand][country] = by_country_water.get(country, 0) / 1e6
                other_water = by_country_water[~by_country_water.index.isin(top_water_countries)].sum()
                water_country_data[label][demand]['Other'] = other_water / 1e6

                # Emissions by source (using transport_total_tonsCO2eq)
                energy_emissions = df_scenario['energy_tonsCO2eq'].sum() / 1000
                transport_emissions = df_scenario['transport_total_tonsCO2eq'].sum() / 1000
                emissions_source_data[label][demand]['Energy'] = energy_emissions
                emissions_source_data[label][demand]['Transport'] = transport_emissions

                # Water by processing type
                by_processing_water = df_scenario.groupby('processing_type')['water_usage_m3'].sum()
                for ptype in PROCESSING_ORDER:
                    water_processing_data[label][demand][ptype] = by_processing_water.get(ptype, 0) / 1e6

    return (emissions_mineral_data, water_mineral_data,
            emissions_country_data, water_country_data,
            emissions_source_data, water_processing_data,
            top_emissions_countries, top_water_countries, country_colormap)


def plot_stacked_panel(ax, data, stack_order, colors, title, xlabel):
    """Plot a single panel with horizontal stacked bars"""
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
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
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


def generate_environmental_indicators_figures(df, output_dir):
    """
    Main entry point for generating environmental indicators figure

    Args:
        df: Main data DataFrame
        output_dir: Output directory

    Returns:
        List of saved file paths
    """
    print("  Generating environmental indicators 6-panel figure...")

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Prepare data
    (emissions_mineral_data, water_mineral_data,
     emissions_country_data, water_country_data,
     emissions_source_data, water_processing_data,
     top_emissions_countries, top_water_countries, country_colormap) = prepare_environmental_data(df)

    # Create figure with 6 panels (2 columns × 3 rows)
    # Match layout from other publication figures (e.g., infrastructure_indicators)
    fig, axes = plt.subplots(3, 2, figsize=(16, 10))
    fig.subplots_adjust(hspace=0.55, wspace=0.95, right=0.52, top=0.90, bottom=0.06)

    # Unpack axes
    ax_emissions_mineral = axes[0, 0]
    ax_water_mineral = axes[0, 1]
    ax_emissions_country = axes[1, 0]
    ax_water_country = axes[1, 1]
    ax_emissions_source = axes[2, 0]
    ax_water_processing = axes[2, 1]

    # Row 1: By Mineral
    plot_stacked_panel(
        ax_emissions_mineral, emissions_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='A) Total Emissions by Mineral',
        xlabel='Emissions (kt CO2eq)'
    )

    plot_stacked_panel(
        ax_water_mineral, water_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='B) Total Water Use by Mineral',
        xlabel='Water Use (MCM)'
    )

    # Row 2: By Country (use consistent color mapping)
    country_order_emissions = top_emissions_countries + ['Other']
    country_colors_emissions = {country: country_colormap.get(country, '#999999') for country in top_emissions_countries}
    country_colors_emissions['Other'] = '#999999'

    country_order_water = top_water_countries + ['Other']
    country_colors_water = {country: country_colormap.get(country, '#999999') for country in top_water_countries}
    country_colors_water['Other'] = '#999999'

    plot_stacked_panel(
        ax_emissions_country, emissions_country_data,
        stack_order=country_order_emissions,
        colors=country_colors_emissions,
        title='C) Total Emissions by Country',
        xlabel='Emissions (kt CO2eq)'
    )

    plot_stacked_panel(
        ax_water_country, water_country_data,
        stack_order=country_order_water,
        colors=country_colors_water,
        title='D) Total Water Use by Country',
        xlabel='Water Use (MCM)'
    )

    # Row 3: By Source/Stage
    plot_stacked_panel(
        ax_emissions_source, emissions_source_data,
        stack_order=EMISSION_SOURCE_ORDER,
        colors=EMISSION_SOURCE_COLORS,
        title='E) Emissions by Source',
        xlabel='Emissions (kt CO2eq)'
    )

    plot_stacked_panel(
        ax_water_processing, water_processing_data,
        stack_order=PROCESSING_ORDER,
        colors=PROCESSING_TYPE_COLORS,
        title='F) Water Use by Processing Type',
        xlabel='Water Use (MCM)'
    )

    # Set y-axis labels
    y_labels = [label for _, _, _, label in SCENARIO_CONFIG]
    for ax in axes.flat:
        ax.set_yticklabels(y_labels, fontsize=10)

    # Create legends next to each subplot (matching infrastructure_indicators style)

    # Row 1: Minerals legend (shared) - place next to panel B
    mineral_patches = []
    for mineral in MINERAL_ORDER:
        color = reference_mineral_colormap.get(mineral, '#999999')
        label = mineral.capitalize()
        patch = mpatches.Patch(facecolor=color, label=label, edgecolor='black', linewidth=0.8)
        mineral_patches.append(patch)

    legend_minerals = ax_water_mineral.legend(handles=mineral_patches,
                                              title='Minerals',
                                              bbox_to_anchor=(1.02, 1),
                                              loc='upper left',
                                              fontsize=8,
                                              title_fontsize=9,
                                              framealpha=0.98,
                                              edgecolor='black')

    # Row 2: Country legends next to each panel
    emissions_country_patches = []
    for country in top_emissions_countries:
        color = country_colormap.get(country, '#999999')
        patch = mpatches.Patch(facecolor=color, label=country, edgecolor='black', linewidth=0.8)
        emissions_country_patches.append(patch)
    emissions_country_patches.append(
        mpatches.Patch(facecolor='#999999', label='Other', edgecolor='black', linewidth=0.8)
    )

    legend_emissions_countries = ax_emissions_country.legend(
        handles=emissions_country_patches,
        title='Countries',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=7,
        title_fontsize=8,
        framealpha=0.98,
        edgecolor='black'
    )
    ax_emissions_country.add_artist(legend_emissions_countries)

    water_country_patches = []
    for country in top_water_countries:
        color = country_colormap.get(country, '#999999')
        patch = mpatches.Patch(facecolor=color, label=country, edgecolor='black', linewidth=0.8)
        water_country_patches.append(patch)
    water_country_patches.append(
        mpatches.Patch(facecolor='#999999', label='Other', edgecolor='black', linewidth=0.8)
    )

    legend_water_countries = ax_water_country.legend(
        handles=water_country_patches,
        title='Countries',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=7,
        title_fontsize=8,
        framealpha=0.98,
        edgecolor='black'
    )
    ax_water_country.add_artist(legend_water_countries)

    # Row 3: Source and Processing legends
    source_patches = []
    for source in EMISSION_SOURCE_ORDER:
        color = EMISSION_SOURCE_COLORS[source]
        patch = mpatches.Patch(facecolor=color, label=source, edgecolor='black', linewidth=0.8)
        source_patches.append(patch)

    legend_sources = ax_emissions_source.legend(handles=source_patches,
                                                title='Emission\nSources',
                                                bbox_to_anchor=(1.02, 1),
                                                loc='upper left',
                                                fontsize=8,
                                                title_fontsize=9,
                                                framealpha=0.98,
                                                edgecolor='black')

    processing_patches = []
    for ptype in PROCESSING_ORDER:
        color = PROCESSING_TYPE_COLORS[ptype]
        patch = mpatches.Patch(facecolor=color, label=ptype, edgecolor='black', linewidth=0.8)
        processing_patches.append(patch)

    legend_processing = ax_water_processing.legend(handles=processing_patches,
                                                   title='Processing\nTypes',
                                                   bbox_to_anchor=(1.02, 1),
                                                   loc='upper left',
                                                   fontsize=8,
                                                   title_fontsize=9,
                                                   framealpha=0.98,
                                                   edgecolor='black')

    # Constraint legend - place next to panel B (below minerals legend)
    constraint_patches = [
        mpatches.Patch(facecolor='white', hatch='////', edgecolor='black', label='Constrained'),
        mpatches.Patch(facecolor='white', edgecolor='black', label='Unconstrained'),
        mpatches.Patch(facecolor='none', edgecolor='none', label='Error bars: Low-High')
    ]

    legend_constraint = ax_water_mineral.legend(handles=constraint_patches,
                                                title='Constraint',
                                                bbox_to_anchor=(1.02, 0.35),
                                                loc='upper left',
                                                fontsize=8,
                                                title_fontsize=9,
                                                framealpha=0.98,
                                                edgecolor='black')

    # Keep all legends
    ax_water_mineral.add_artist(legend_minerals)
    ax_emissions_source.add_artist(legend_sources)
    ax_water_processing.add_artist(legend_processing)

    # Overall title
    # fig.suptitle('Environmental Indicators: Baseline, BAU vs Precursor\n' +
    #              '(Mid-demand with Low-High range)',
    #              fontsize=14, fontweight='bold', y=0.985)

    # Note
    # fig.text(0.5, 0.005,
    #          'Note: BAU scenarios have no National/Regional distinction (identical outcomes)',
    #          fontsize=7, style='italic', color='gray', ha='center',
    #          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3, pad=0.3))

    # Save figure
    saved_paths = []

    png_path = os.path.join(output_dir, 'environmental_indicators_six_panel.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight', facecolor='white', pad_inches=0.3)
    saved_paths.append(png_path)
    print(f"    ✓ Saved: {os.path.basename(png_path)}")

    pdf_path = os.path.join(output_dir, 'environmental_indicators_six_panel.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white', pad_inches=0.3)
    saved_paths.append(pdf_path)
    print(f"    ✓ Saved: {os.path.basename(pdf_path)}")

    preview_path = os.path.join(output_dir, 'environmental_indicators_six_panel_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight', facecolor='white', pad_inches=0.3)
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
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'publication', 'environmental_indicators')
    os.makedirs(output_dir, exist_ok=True)

    # Generate figure
    print("Testing environmental indicators figure generation...")
    paths = generate_environmental_indicators_figures(df, output_dir)
    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
