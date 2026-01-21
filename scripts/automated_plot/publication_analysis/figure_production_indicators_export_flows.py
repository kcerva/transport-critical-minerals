"""
BAU vs Precursor Product Comparison Figure (EXPORT FLOWS VERSION)

Creates a five-panel HYBRID figure comparing Business as Usual (BAU) and Precursor Product
scenarios with demand uncertainty ranges:

HYBRID DATA SOURCES:
- Extraction panels (B, E): all_data.xlsx - TOTAL production (domestic + export)
- Processing panels (C, D, F): tonnage_flows_with_revenues.xlsx - EXPORT production only

Panel B: Total extraction by mineral (stage 0) - FROM all_data.xlsx
Panel C: Export processing by mineral (stage > 0) - FROM export flows
Panel D: Export processing by type (stage > 0) - FROM export flows
Panel E: Extraction by country (stage 0) - FROM all_data.xlsx
Panel F: Export processing by country (stage > 0) - FROM export flows

Panels B, C, D show 7 bars representing:
- Baseline: 2022 actual production (1 bar)
- BAU: Constrained/Unconstrained (2 bars - National = Regional for BAU)
- Precursor: Constrained/Unconstrained × National/Regional (4 bars)

Error bars show demand uncertainty (Low-Mid-High range)
Hatching patterns differentiate Constrained (hatched) vs Unconstrained (solid)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle

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


# Scenario configuration for extraction panel (3 bars - only constraint matters, not BAU vs Precursor)
SCENARIO_CONFIG_EXTRACTION = [
    ('baseline', None, None, 'Baseline'),
    ('2040', None, 'constrained', '2040_C'),
    ('2040', None, 'unconstrained', '2040_U'),
]

# Scenario configuration for processing panels (7 bars - Baseline + BAU + Precursor)
SCENARIO_CONFIG_PROCESSING = [
    ('baseline', None, None, 'Baseline'),
    ('bau', 'min', 'constrained', 'BAU_C'),
    ('bau', 'min', 'unconstrained', 'BAU_U'),
    ('precursor', 'min', 'constrained', 'Prec_C_N'),
    ('precursor', 'min', 'unconstrained', 'Prec_U_N'),
    ('precursor', 'max', 'constrained', 'Prec_C_R'),
    ('precursor', 'max', 'unconstrained', 'Prec_U_R'),
]

# Mineral order by production volume (for stacking)
MINERAL_ORDER = ['copper', 'manganese', 'graphite', 'cobalt', 'nickel', 'lithium']

# Processing type order (for stacking)
PROCESSING_ORDER = ['Beneficiation', 'Early refining', 'Precursor related product']


def prepare_extraction_data(df):
    """
    Prepare extraction data (stage 0) with 3 bars: Baseline, 2040 Constrained, 2040 Unconstrained

    For extraction, BAU and Precursor scenarios have identical volumes, so we aggregate
    all 2040 scenarios by constraint type only.

    Args:
        df: Main data DataFrame

    Returns:
        dict: panel_metal_data[scenario_label][demand][mineral] = production (stage 0 only)
    """
    df_metal = df[df['processing_stage'] == 0].copy()
    panel_metal_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG_EXTRACTION:
        panel_metal_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        if goal == 'baseline':
            # Baseline scenario
            scenario_name = '2022_baseline'
            df_scenario_metal = df_metal[df_metal['scenario'] == scenario_name].copy()

            # Use same data for low/mid/high (no demand uncertainty for baseline)
            for demand in ['low', 'mid', 'high']:
                if not df_scenario_metal.empty:
                    by_mineral = df_scenario_metal.groupby('reference_mineral')['production_tonnes'].sum()
                    for mineral in MINERAL_ORDER:
                        panel_metal_data[label][demand][mineral] = by_mineral.get(mineral, 0)

        else:  # goal == '2040'
            # Use BAU scenarios (extraction is identical for BAU and Precursor)
            for demand in ['low', 'mid', 'high']:
                # Build BAU scenario name
                scenario_name = f'bau_2040_{demand}_min_threshold_metal_tons'

                # Build constraint column name (BAU uses country policy)
                constraint_col = f'country_{constraint}'

                # Filter for this specific BAU scenario and constraint
                df_scenario_metal = df_metal[
                    (df_metal['scenario'] == scenario_name) &
                    (df_metal['constraint'] == constraint_col)
                ].copy()

                if not df_scenario_metal.empty:
                    by_mineral = df_scenario_metal.groupby('reference_mineral')['production_tonnes'].sum()
                    for mineral in MINERAL_ORDER:
                        panel_metal_data[label][demand][mineral] = by_mineral.get(mineral, 0)
                else:
                    print(f"  WARNING: No data for {label} {demand} demand (scenario: {scenario_name}, constraint: {constraint_col})")

    # Debug: Check all mineral values
    print("\nDebug - Extraction values by mineral (Mt):")
    for mineral in MINERAL_ORDER:
        print(f"\n  {mineral.upper()}:")
        for label in ['Baseline', '2040_C', '2040_U']:
            if label in panel_metal_data:
                low = panel_metal_data[label]['low'].get(mineral, 0) / 1e6
                mid = panel_metal_data[label]['mid'].get(mineral, 0) / 1e6
                high = panel_metal_data[label]['high'].get(mineral, 0) / 1e6
                print(f"    {label}: low={low:.2f}, mid={mid:.2f}, high={high:.2f}")

    return panel_metal_data


def prepare_processing_data(df_flows, df_all):
    """
    Prepare processing data (stage > 0) from EXPORT FLOWS with 7 bars distinguishing BAU vs Precursor

    Args:
        df_flows: Tonnage flows DataFrame (with export flows filtered)
        df_all: all_data.xlsx DataFrame (for processing_type mapping)

    Returns:
        tuple: (panel_processing_data, panel_mineral_data)
            panel_processing_data: Dict[scenario_label][demand][processing_type] = export production (stage > 0)
            panel_mineral_data: Dict[scenario_label][demand][mineral] = export production (stage > 0)
    """
    # Create processing_type mapping from all_data.xlsx
    stage_type_mapping = df_all[['reference_mineral', 'processing_stage', 'processing_type']].drop_duplicates()
    stage_type_dict = {
        (row['reference_mineral'], row['processing_stage']): row['processing_type']
        for _, row in stage_type_mapping.iterrows()
    }

    # Apply processing_type to flows data
    df_flows['processing_type'] = df_flows.apply(
        lambda row: stage_type_dict.get(
            (row['reference_mineral'], row['final_processing_stage']),
            'Unknown'
        ),
        axis=1
    )

    # Filter out "Metal content" (stage 0.0) - not physical exports
    df_processing = df_flows[df_flows['processing_type'] != 'Metal content'].copy()

    panel_processing_data = {}
    panel_mineral_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG_PROCESSING:
        panel_processing_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        panel_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants, different naming)
        if goal == 'baseline':
            scenario_name = '2022_baseline'
            df_scenario_processing = df_processing[df_processing['scenario'] == scenario_name].copy()

            if df_scenario_processing.empty:
                print(f"Warning: No processing data for {label}")

            # Use same data for low/mid/high (no demand uncertainty for baseline)
            for demand in ['low', 'mid', 'high']:
                # Processing Panel: Group by processing type (stage > 0)
                if not df_scenario_processing.empty:
                    by_processing = df_scenario_processing.groupby('processing_type')['final_stage_production_tons'].sum()
                    for ptype in PROCESSING_ORDER:
                        panel_processing_data[label][demand][ptype] = by_processing.get(ptype, 0)

                    # Mineral Panel: Group by mineral (stage > 0)
                    by_mineral_processing = df_scenario_processing.groupby('reference_mineral')['final_stage_production_tons'].sum()
                    for mineral in MINERAL_ORDER:
                        panel_mineral_data[label][demand][mineral] = by_mineral_processing.get(mineral, 0)

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                # Build scenario name
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'

                # Build constraint column name
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                # Filter data for processing (stage > 0)
                df_scenario_processing = df_processing[
                    (df_processing['scenario'] == scenario_name) &
                    (df_processing['constraint'] == constraint_col)
                ].copy()

                if df_scenario_processing.empty:
                    print(f"Warning: No processing data for {label} {demand} demand")
                    continue

                # Processing Panel: Group by processing type (stage > 0)
                by_processing = df_scenario_processing.groupby('processing_type')['final_stage_production_tons'].sum()
                for ptype in PROCESSING_ORDER:
                    panel_processing_data[label][demand][ptype] = by_processing.get(ptype, 0)

                # Mineral Panel: Group by mineral (stage > 0)
                by_mineral_processing = df_scenario_processing.groupby('reference_mineral')['final_stage_production_tons'].sum()
                for mineral in MINERAL_ORDER:
                    panel_mineral_data[label][demand][mineral] = by_mineral_processing.get(mineral, 0)

    return panel_processing_data, panel_mineral_data


def get_top_countries(df, metric_column, n=8):
    """
    Get top N countries by total metric value

    Args:
        df: DataFrame with country data
        metric_column: Column to aggregate
        n: Number of top countries to return

    Returns:
        list: Top N country ISO codes
    """
    country_totals = df.groupby('iso3')[metric_column].sum().sort_values(ascending=False)
    return country_totals.head(n).index.tolist()


def prepare_country_extraction_data(df):
    """
    Prepare country-level extraction data (stage 0) with 3 bars

    Args:
        df: Main data DataFrame

    Returns:
        tuple: (country_extraction_data, top_countries)
            country_extraction_data: Dict[scenario_label][demand][country] = production
            top_countries: List of top 8 country ISO codes
    """
    df_metal = df[df['processing_stage'] == 0].copy()

    # Get top 8 countries by total extraction
    top_countries = get_top_countries(df_metal, 'production_tonnes', n=8)

    country_extraction_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG_EXTRACTION:
        country_extraction_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        if goal == 'baseline':
            scenario_name = '2022_baseline'
            df_scenario = df_metal[df_metal['scenario'] == scenario_name].copy()

            for demand in ['low', 'mid', 'high']:
                if not df_scenario.empty:
                    by_country = df_scenario.groupby('iso3')['production_tonnes'].sum()

                    # Top 8 countries
                    for country in top_countries:
                        country_extraction_data[label][demand][country] = by_country.get(country, 0)

                    # Other
                    other_countries = set(by_country.index) - set(top_countries)
                    country_extraction_data[label][demand]['Other'] = sum(by_country.get(c, 0) for c in other_countries)

        else:  # 2040 scenarios
            for demand in ['low', 'mid', 'high']:
                scenario_name = f'bau_2040_{demand}_min_threshold_metal_tons'
                constraint_col = f'country_{constraint}'

                df_scenario = df_metal[
                    (df_metal['scenario'] == scenario_name) &
                    (df_metal['constraint'] == constraint_col)
                ].copy()

                if not df_scenario.empty:
                    by_country = df_scenario.groupby('iso3')['production_tonnes'].sum()

                    # Top 8 countries
                    for country in top_countries:
                        country_extraction_data[label][demand][country] = by_country.get(country, 0)

                    # Other
                    other_countries = set(by_country.index) - set(top_countries)
                    country_extraction_data[label][demand]['Other'] = sum(by_country.get(c, 0) for c in other_countries)

    return country_extraction_data, top_countries


def prepare_country_processing_data(df_flows):
    """
    Prepare country-level processing data (stage > 0) from EXPORT FLOWS with 7 bars

    Args:
        df_flows: Tonnage flows DataFrame (with export flows filtered)

    Returns:
        tuple: (country_processing_data, top_countries)
            country_processing_data: Dict[scenario_label][demand][country] = export production
            top_countries: List of top 8 country ISO codes
    """
    df_processing = df_flows.copy()

    # Get top 8 countries by total processing
    top_countries = get_top_countries(df_processing, 'final_stage_production_tons', n=8)

    country_processing_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG_PROCESSING:
        country_processing_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        if goal == 'baseline':
            scenario_name = '2022_baseline'
            df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

            for demand in ['low', 'mid', 'high']:
                if not df_scenario.empty:
                    by_country = df_scenario.groupby('iso3')['final_stage_production_tons'].sum()

                    # Top 8 countries
                    for country in top_countries:
                        country_processing_data[label][demand][country] = by_country.get(country, 0)

                    # Other
                    other_countries = set(by_country.index) - set(top_countries)
                    country_processing_data[label][demand]['Other'] = sum(by_country.get(c, 0) for c in other_countries)

        else:  # BAU and Precursor scenarios
            for demand in ['low', 'mid', 'high']:
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                df_scenario = df_processing[
                    (df_processing['scenario'] == scenario_name) &
                    (df_processing['constraint'] == constraint_col)
                ].copy()

                if not df_scenario.empty:
                    by_country = df_scenario.groupby('iso3')['final_stage_production_tons'].sum()

                    # Top 8 countries
                    for country in top_countries:
                        country_processing_data[label][demand][country] = by_country.get(country, 0)

                    # Other
                    other_countries = set(by_country.index) - set(top_countries)
                    country_processing_data[label][demand]['Other'] = sum(by_country.get(c, 0) for c in other_countries)

    return country_processing_data, top_countries


def plot_grouped_vertical_bars_by_mineral(ax, data, title, ylabel):
    """
    Plot vertical grouped bars by mineral for extraction panel

    Each mineral gets 3 bars: Baseline, 2040_C, 2040_U
    Colors represent scenarios, not minerals
    Error bars show demand uncertainty for 2040 scenarios

    Args:
        ax: Matplotlib axis
        data: Nested dict [scenario_label][demand][mineral] = value
        title: Panel title
        ylabel: Y-axis label
    """
    # Scenario colors
    scenario_colors = {
        'Baseline': '#CCCCCC',  # Light gray
        '2040_C': '#4472C4',     # Blue
        '2040_U': '#4472C4'      # Same blue (distinguish by hatching)
    }

    n_minerals = len(MINERAL_ORDER)
    n_scenarios = len(SCENARIO_CONFIG_EXTRACTION)
    bar_width = 0.25
    group_spacing = 0.2  # Space between mineral groups

    # Calculate x positions for each bar
    # Create groups for each mineral
    x_base = np.arange(n_minerals) * (n_scenarios * bar_width + group_spacing)

    # Plot bars for each scenario
    for i, (goal, policy, constraint, label) in enumerate(SCENARIO_CONFIG_EXTRACTION):
        x_positions = x_base + i * bar_width
        heights_mid = []
        heights_low = []
        heights_high = []

        for mineral in MINERAL_ORDER:
            heights_mid.append(data[label]['mid'].get(mineral, 0) / 1e6)  # Convert to Mt
            heights_low.append(data[label]['low'].get(mineral, 0) / 1e6)
            heights_high.append(data[label]['high'].get(mineral, 0) / 1e6)

        # Plot bars
        color = scenario_colors[label]
        hatch = '////' if constraint == 'constrained' else None

        ax.bar(x_positions, heights_mid,
               width=bar_width,
               color=color,
               edgecolor='black',
               linewidth=0.8,
               hatch=hatch,
               alpha=0.9,
               label=label)

        # Add error bars for 2040 scenarios (not baseline)
        if goal != 'baseline':
            # Calculate error bar sizes
            yerr_lower = [max(0, mid - low) for mid, low in zip(heights_mid, heights_low)]
            yerr_upper = [max(0, high - mid) for mid, high in zip(heights_high, heights_mid)]

            # Only plot error bars if there's actual variance
            for j, mineral in enumerate(MINERAL_ORDER):
                if yerr_lower[j] > 0 or yerr_upper[j] > 0:
                    ax.errorbar(x_positions[j], heights_mid[j],
                               yerr=[[yerr_lower[j]], [yerr_upper[j]]],
                               fmt='none',
                               ecolor='black',
                               elinewidth=1.5,
                               capsize=4,
                               capthick=1.5,
                               zorder=10)

    # Add value labels on top of bars (after all bars are plotted)
    for i, (goal, policy, constraint, label) in enumerate(SCENARIO_CONFIG_EXTRACTION):
        x_positions = x_base + i * bar_width

        for j, mineral in enumerate(MINERAL_ORDER):
            height_mid = data[label]['mid'].get(mineral, 0) / 1e6
            if height_mid >= 0.01:  # Show label for any non-zero bar
                # Format: Use 1 decimal for small values (<0.5), no decimals for larger
                if height_mid < 0.5:
                    label_text = f'{height_mid:.1f}'
                else:
                    label_text = f'{height_mid:.0f}'
                # Position text higher above bar to avoid error bar overlap
                # Add offset proportional to y-axis range for consistent spacing
                y_offset = 0.3  # Fixed offset in Mt units
                ax.text(x_positions[j], height_mid + y_offset, label_text,
                       ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Formatting
    ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)

    # Set x-axis ticks at group centers
    group_centers = x_base + (n_scenarios - 1) * bar_width / 2
    ax.set_xticks(group_centers)
    ax.set_xticklabels([m.capitalize() for m in MINERAL_ORDER], rotation=0, ha='center')

    ax.set_ylim(0, None)  # Auto-scale y-axis
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)


def calculate_max_value_from_data(data, scenario_config):
    """
    Calculate maximum value from prepared data including error bars

    Args:
        data: Nested dict [scenario_label][demand][category] = value
        scenario_config: List of scenario tuples

    Returns:
        float: Maximum value in Mt (including high demand values)
    """
    max_val = 0
    for _, _, _, label in scenario_config:
        # Sum all categories for this scenario (high demand for maximum)
        total = sum(data[label]['high'].values()) / 1e6  # Convert to Mt
        max_val = max(max_val, total)
    return max_val


def plot_stacked_panel(ax, data, stack_order, colors, title, xlabel='Production (Mt)', scenario_config=None, xlim_max=None):
    """
    Plot a single panel with horizontal stacked bars and error bars

    Args:
        ax: Matplotlib axis
        data: Nested dict [scenario_label][demand][stack_category] = value
        stack_order: List of categories for stacking (left to right)
        colors: Dict mapping stack_category to color
        title: Panel title
        xlabel: X-axis label
        scenario_config: List of scenario tuples to use (defaults to SCENARIO_CONFIG_PROCESSING)
        xlim_max: Optional fixed x-axis maximum (if None, calculated dynamically)
    """
    if scenario_config is None:
        scenario_config = SCENARIO_CONFIG_PROCESSING

    n_bars = len(scenario_config)
    y_positions = np.arange(n_bars, dtype=float)

    # Add gaps based on number of bars
    if n_bars == 3:
        # For extraction panel: Baseline, 2040_C, 2040_U
        baseline_gap = 0.6
        y_positions[1:] += baseline_gap
    else:
        # For processing panels: Baseline + BAU + Precursor
        baseline_gap = 0.6
        bau_precursor_gap = 0.8
        # Shift BAU bars down (after baseline)
        y_positions[1:] += baseline_gap
        # Shift Precursor bars down further (after BAU)
        y_positions[3:] += bau_precursor_gap

    bar_height = 0.7

    # For each bar, stack the components and track maximum
    max_with_error = 0
    for i, (goal, policy, constraint, label) in enumerate(scenario_config):
        # Get mid-demand values for bar widths
        mid_values = data[label]['mid']
        low_values = data[label]['low']
        high_values = data[label]['high']

        # Calculate stacked positions
        left = 0
        segment_widths = []

        for category in stack_order:
            width_mid = mid_values.get(category, 0) / 1e6  # Convert to Mt
            width_low = low_values.get(category, 0) / 1e6
            width_high = high_values.get(category, 0) / 1e6

            segment_widths.append({
                'category': category,
                'mid': width_mid,
                'low': width_low,
                'high': width_high,
                'left': left
            })

            # Plot segment (horizontal bar)
            color = colors.get(category, '#999999')
            # Only apply hatching for non-baseline scenarios with constraints
            hatch = '////' if (constraint == 'constrained' and goal != 'baseline') else None

            ax.barh(y_positions[i], width_mid,
                    height=bar_height,
                    left=left,
                    color=color,
                    edgecolor='black',
                    linewidth=0.8,
                    hatch=hatch,
                    alpha=0.9)

            left += width_mid

        # Add error bar to right end of stack
        total_mid = sum(seg['mid'] for seg in segment_widths)
        total_low = sum(seg['low'] for seg in segment_widths)
        total_high = sum(seg['high'] for seg in segment_widths)

        # Error bar: asymmetric (ensure non-negative)
        xerr_lower = max(0, total_mid - total_low)
        xerr_upper = max(0, total_high - total_mid)

        # Track maximum value including error bar
        max_with_error = max(max_with_error, total_high)

        # Only plot error bar if there's actual variance
        if xerr_lower > 0 or xerr_upper > 0:
            ax.errorbar(total_mid, y_positions[i],
                       xerr=[[xerr_lower], [xerr_upper]],
                       fmt='none',
                       ecolor='black',
                       elinewidth=1.5,
                       capsize=4,
                       capthick=1.5,
                       zorder=10)

    # Formatting
    ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_yticks(y_positions)
    # Set x-axis limit: use provided xlim_max or calculate dynamically
    if xlim_max is None:
        # Calculate dynamically: 10% buffer above maximum value (with error bars)
        xlim_max = max_with_error * 1.10 if max_with_error > 0 else 1
    ax.set_xlim(0, xlim_max)
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)  # Only vertical grid lines
    ax.yaxis.grid(False)  # Explicitly disable y-axis grid
    ax.set_axisbelow(True)
    ax.invert_yaxis()  # Put first bar at top

    # Add horizontal lines to separate scenario groups
    if n_bars == 3:
        # For extraction: only separator after baseline
        baseline_separator_y = (y_positions[0] + y_positions[1]) / 2
        ax.axhline(baseline_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    else:
        # For processing: separate Baseline, BAU, and Precursor
        baseline_separator_y = (y_positions[0] + y_positions[1]) / 2
        bau_precursor_separator_y = (y_positions[2] + y_positions[3]) / 2
        ax.axhline(baseline_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axhline(bau_precursor_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    return y_positions


def create_comprehensive_legend(fig, ax_metal, ax_country_extraction, ax_country_processing,
                               ax_mineral, ax_processing, country_colormap,
                               top_extraction_countries, top_processing_countries):
    """
    Create comprehensive legends for all panels, positioned outside plot area

    Args:
        fig: Figure object
        ax_metal: Panel B (extraction by mineral - vertical bars)
        ax_country_extraction: Panel E (extraction by country)
        ax_country_processing: Panel F (processing by country)
        ax_mineral: Panel C (minerals by processing)
        ax_processing: Panel D (processing types)
        country_colormap: Dict mapping country ISO codes to colors
        top_extraction_countries: List of top extraction countries
        top_processing_countries: List of top processing countries
    """
    # Scenario legend for Panel B (extraction - vertical bars)
    scenario_patches = [
        mpatches.Patch(facecolor='#CCCCCC', label='Baseline', edgecolor='black', linewidth=0.8),
        mpatches.Patch(facecolor='#4472C4', hatch='////', label='2040 Constrained',
                      edgecolor='black', linewidth=0.8),
        mpatches.Patch(facecolor='#4472C4', label='2040 Unconstrained',
                      edgecolor='black', linewidth=0.8)
    ]

    # Country legends for Panels E & F
    extraction_country_patches = []
    for country in top_extraction_countries + ['Other']:
        color = country_colormap.get(country, '#999999')
        patch = mpatches.Patch(facecolor=color, label=country, edgecolor='black', linewidth=0.8)
        extraction_country_patches.append(patch)

    processing_country_patches = []
    for country in top_processing_countries + ['Other']:
        color = country_colormap.get(country, '#999999')
        patch = mpatches.Patch(facecolor=color, label=country, edgecolor='black', linewidth=0.8)
        processing_country_patches.append(patch)

    # Mineral legend (Panel C)
    mineral_patches = []
    for mineral in MINERAL_ORDER:
        color = reference_mineral_colormap.get(mineral, '#999999')
        label = mineral.capitalize()
        patch = mpatches.Patch(facecolor=color, label=label, edgecolor='black', linewidth=0.8)
        mineral_patches.append(patch)

    # Processing Types legend (Panel D)
    processing_patches = []
    for ptype in PROCESSING_ORDER:
        color = PROCESSING_TYPE_COLORS.get(ptype, '#999999')
        patch = mpatches.Patch(facecolor=color, label=ptype, edgecolor='black', linewidth=0.8)
        processing_patches.append(patch)

    # Constraint patterns
    constraint_patches = [
        mpatches.Patch(facecolor='white', hatch='////', edgecolor='black',
                      label='Constrained'),
        mpatches.Patch(facecolor='white', edgecolor='black',
                      label='Unconstrained')
    ]

    # Error bar explanation
    error_patch = mpatches.Patch(facecolor='none', edgecolor='none',
                                 label='Error bars: Low-High demand')

    # Panel B: Scenarios
    legend_metal = ax_metal.legend(handles=scenario_patches + [error_patch],
                                   title='Scenarios',
                                   bbox_to_anchor=(1.02, 1),
                                   loc='upper left',
                                   fontsize=8,
                                   title_fontsize=9,
                                   framealpha=0.98,
                                   edgecolor='black',
                                   ncol=1)
    ax_metal.add_artist(legend_metal)

    # Panel E: Extraction Countries
    legend_extraction_countries = ax_country_extraction.legend(
        handles=extraction_country_patches,
        title='Countries\n(Extraction)',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=7,
        title_fontsize=8,
        framealpha=0.98,
        edgecolor='black',
        ncol=1
    )
    ax_country_extraction.add_artist(legend_extraction_countries)

    # Panel F: Processing Countries
    legend_processing_countries = ax_country_processing.legend(
        handles=processing_country_patches,
        title='Countries\n(Processing)',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=7,
        title_fontsize=8,
        framealpha=0.98,
        edgecolor='black',
        ncol=1
    )
    ax_country_processing.add_artist(legend_processing_countries)

    # Panel C: Minerals + Constraint info
    legend_minerals = ax_mineral.legend(handles=mineral_patches,
                                        title='Minerals',
                                        bbox_to_anchor=(1.02, 1),
                                        loc='upper left',
                                        fontsize=8,
                                        title_fontsize=9,
                                        framealpha=0.98,
                                        edgecolor='black',
                                        ncol=1)
    ax_mineral.add_artist(legend_minerals)

    legend_constraint = ax_mineral.legend(handles=constraint_patches + [error_patch],
                                         title='Constraint &\nUncertainty',
                                         bbox_to_anchor=(1.02, 0.50),
                                         loc='upper left',
                                         fontsize=8,
                                         title_fontsize=9,
                                         framealpha=0.98,
                                         edgecolor='black')
    ax_mineral.add_artist(legend_constraint)

    # Panel D: Processing Types
    legend_processing = ax_processing.legend(handles=processing_patches,
                                            title='Processing Types',
                                            bbox_to_anchor=(1.02, 1),
                                            loc='upper left',
                                            fontsize=8,
                                            title_fontsize=9,
                                            framealpha=0.98,
                                            edgecolor='black')

    # Return all legend objects for bbox_extra_artists
    return [legend_metal, legend_extraction_countries, legend_processing_countries,
            legend_minerals, legend_constraint, legend_processing]


def create_production_indicators_figure(df_all, df_flows, output_dir):
    """
    Generate complete production indicators comparison figure (HYBRID VERSION)

    Args:
        df_all: all_data.xlsx DataFrame (for extraction panels)
        df_flows: tonnage_flows DataFrame (export flows only, for processing panels)
        output_dir: Output directory for figure

    Returns:
        List of saved file paths
    """
    print("  Generating production indicators three-panel figure (EXPORT FLOWS VERSION)...")

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Prepare data - HYBRID APPROACH
    # Extraction panels use all_data.xlsx (total production)
    panel_metal_data = prepare_extraction_data(df_all)
    country_extraction_data, top_extraction_countries = prepare_country_extraction_data(df_all)

    # Processing panels use export flows (export production only)
    panel_processing_data, panel_mineral_data = prepare_processing_data(df_flows, df_all)
    country_processing_data, top_processing_countries = prepare_country_processing_data(df_flows)

    # Generate consistent country color mapping
    all_countries = sorted(set(top_extraction_countries) | set(top_processing_countries) | {'Other'})
    country_colormap = generate_country_colormap(all_countries)
    # Force "Other" to be grey for consistency across all plots
    country_colormap['Other'] = '#999999'

    # Calculate unified x-axis maximum for all horizontal panels (C, D, E, F)
    # This ensures visual comparability across all panels
    max_c = calculate_max_value_from_data(panel_mineral_data, SCENARIO_CONFIG_PROCESSING)
    max_d = calculate_max_value_from_data(panel_processing_data, SCENARIO_CONFIG_PROCESSING)
    max_e = calculate_max_value_from_data(country_extraction_data, SCENARIO_CONFIG_EXTRACTION)
    max_f = calculate_max_value_from_data(country_processing_data, SCENARIO_CONFIG_PROCESSING)

    unified_xlim_max = max(max_c, max_d, max_e, max_f) * 1.10  # 10% buffer

    # Create figure with 4 rows (last row has 2 columns for country comparisons)
    # Row 0: Panel B (vertical bars - extraction by mineral)
    # Row 1: Panel C (minerals - processing by mineral)
    # Row 2: Panel D (processing types)
    # Row 3: Panels E & F (country extraction and processing) - BOTTOM ROW
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(4, 2, height_ratios=[0.5, 0.85, 0.85, 0.7], hspace=0.40, wspace=0.53,
                          right=0.54, left=0.08, top=0.96, bottom=0.05)

    # Panel B spans both columns in row 0
    ax_metal = fig.add_subplot(gs[0, :])

    # Panel C spans both columns in row 1
    ax_mineral = fig.add_subplot(gs[1, :])

    # Panel D spans both columns in row 2
    ax_processing = fig.add_subplot(gs[2, :])

    # Panel E & F in row 3 (2 columns) - BOTTOM ROW
    ax_country_extraction = fig.add_subplot(gs[3, 0])
    ax_country_processing = fig.add_subplot(gs[3, 1])

    # Plot Panel B (Metal Content - Stage 0) - Vertical grouped bars by mineral
    plot_grouped_vertical_bars_by_mineral(
        ax_metal, panel_metal_data,
        title='B) Total Extraction by Mineral',
        ylabel='Metal Content (Mt)'
    )

    # Plot Panel E (Extraction by Country) - 3 scenarios
    country_order_extraction = top_extraction_countries + ['Other']
    country_colors_extraction = {country: country_colormap.get(country, '#999999') for country in country_order_extraction}

    plot_stacked_panel(
        ax_country_extraction, country_extraction_data,
        stack_order=country_order_extraction,
        colors=country_colors_extraction,
        title='E) Extraction by Country',
        xlabel='Metal Content (Mt)',
        scenario_config=SCENARIO_CONFIG_EXTRACTION,
        xlim_max=unified_xlim_max
    )

    # Plot Panel F (Processing by Country) - 7 scenarios
    country_order_processing = top_processing_countries + ['Other']
    country_colors_processing = {country: country_colormap.get(country, '#999999') for country in country_order_processing}

    plot_stacked_panel(
        ax_country_processing, country_processing_data,
        stack_order=country_order_processing,
        colors=country_colors_processing,
        title='F) Processed Exports by Country',
        xlabel='Production (Mt)',
        scenario_config=SCENARIO_CONFIG_PROCESSING,
        xlim_max=unified_xlim_max
    )

    # Plot Panel C (Minerals - Stage > 0) - 7 bars
    plot_stacked_panel(
        ax_mineral, panel_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='C) Total Processed Exports by Mineral',
        xlabel='Production (Mt)',
        scenario_config=SCENARIO_CONFIG_PROCESSING,
        xlim_max=unified_xlim_max
    )

    # Plot Panel D (Processing Types - Stage > 0) - 7 bars
    plot_stacked_panel(
        ax_processing, panel_processing_data,
        stack_order=PROCESSING_ORDER,
        colors=PROCESSING_TYPE_COLORS,
        title='D) Total Processed Exports by Processing Type',
        xlabel='Production (Mt)',
        scenario_config=SCENARIO_CONFIG_PROCESSING,
        xlim_max=unified_xlim_max
    )

    # Set y-axis labels (scenario names on left)
    # Panel B uses vertical bars with mineral names on x-axis
    y_labels_extraction = [label for _, _, _, label in SCENARIO_CONFIG_EXTRACTION]
    y_labels_processing = [label for _, _, _, label in SCENARIO_CONFIG_PROCESSING]

    ax_country_extraction.set_yticklabels(y_labels_extraction, fontsize=9)
    ax_country_processing.set_yticklabels(y_labels_processing, fontsize=9)
    ax_mineral.set_yticklabels(y_labels_processing, fontsize=9)
    ax_processing.set_yticklabels(y_labels_processing, fontsize=9)

    # Add overall title
    # fig.suptitle('Mineral Extraction and Processing',
    #             #  '(Mid-demand with Low-High range)',
    #              fontsize=13, fontweight='bold', y=0.99)

    # Create comprehensive legend and collect legend objects
    all_legends = create_comprehensive_legend(fig, ax_metal, ax_country_extraction, ax_country_processing,
                                              ax_mineral, ax_processing, country_colormap,
                                              top_extraction_countries, top_processing_countries)

    # Add note about BAU scenarios (below figure)
    # fig.text(0.12, 0.001,
    #          'Note: BAU scenarios have no National/Regional distinction (identical outcomes)',
    #          fontsize=7, style='italic', color='gray',
    #          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3, pad=0.3))

    # Save figure
    saved_paths = []

    # High-res PNG for publication
    png_path = os.path.join(output_dir, 'production_indicators_three_panel_export_flows.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight',
                bbox_extra_artists=all_legends, facecolor='white')
    saved_paths.append(png_path)
    print(f"    ✓ Saved: {os.path.basename(png_path)}")

    # PDF for vector graphics
    pdf_path = os.path.join(output_dir, 'production_indicators_three_panel_export_flows.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight',
                bbox_extra_artists=all_legends, facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    ✓ Saved: {os.path.basename(pdf_path)}")

    # Low-res PNG for quick preview
    preview_path = os.path.join(output_dir, 'production_indicators_three_panel_export_flows_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight',
                bbox_extra_artists=all_legends, facecolor='white')
    saved_paths.append(preview_path)
    print(f"    ✓ Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


def generate_production_indicators_figures(df_all, df_flows, output_dir):
    """
    Main entry point for generating production indicators figures (EXPORT FLOWS VERSION)

    Args:
        df_all: all_data.xlsx DataFrame
        df_flows: tonnage_flows DataFrame (export flows only)
        output_dir: Output directory

    Returns:
        List of saved file paths
    """
    return create_production_indicators_figure(df_all, df_flows, output_dir)


if __name__ == '__main__':
    """Test the figure generation"""
    import json

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = config['paths']['results']

    # Load data - HYBRID APPROACH
    # Load all_data.xlsx for extraction panels
    all_data_file = os.path.join(results_path, 'all_data.xlsx')
    df_all = pd.read_excel(all_data_file, index_col=[0,1,2,3,4]).reset_index()
    print(f"Loaded all_data.xlsx: {len(df_all):,} rows")

    # Load tonnage flows for processing panels
    flows_file = os.path.join(results_path, 'tonnage_flows_with_revenues.xlsx')
    df_flows = pd.read_excel(flows_file, sheet_name='All_Flows')
    print(f"Loaded tonnage_flows: {len(df_flows):,} rows")

    # Filter for export flows only
    df_flows = df_flows[df_flows['trade_type'] == 'Export'].copy()
    print(f"  Export flows: {len(df_flows):,} rows")

    # Create output directory (match run_all_figures.py path structure with automated_plots)
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'publication', 'production_indicators')
    os.makedirs(output_dir, exist_ok=True)

    # Generate figure (match run_all_figures.py path structure)
    print("\nTesting production indicators figure generation (EXPORT FLOWS VERSION)...")
    paths = generate_production_indicators_figures(df_all, df_flows, output_dir)
    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
