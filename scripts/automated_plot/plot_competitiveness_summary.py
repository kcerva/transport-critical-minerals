#!/usr/bin/env python3
"""
Competitiveness Summary Heatmaps

This script creates competitiveness matrix heatmaps showing country-level cost
competitiveness across minerals and policy scenarios. The visualizations aggregate
cumulative unit costs from supply curve analysis into intuitive heatmap format.

Design Specifications (see COMPETITIVENESS_HEATMAP_ANALYSIS.md):
- Color scheme: White-to-green sequential (darker = more competitive)
- Ranking: Within-mineral quintiles (Q1-Q5)
- Annotations: Cost in thousands ($XXk) + rank number (#X)
- Country order: Alphabetical by ISO3
- Mineral order: By country participation (Copper, Cobalt, Nickel, Manganese, Lithium, Graphite)
- Layout: Side-by-side (National | Regional)
- Scenarios: Early Refining and Precursor Product only

Usage:
    python plot_competitiveness_summary.py

Or integrate into run_all_figures.py workflow.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Add script directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plot_config import reference_minerals
from plot_supply_curves import create_country_color_map


# Scenario configuration matching plot_supply_curves.py cumulative cost logic
SCENARIO_CONFIG = {
    'early_refining_2040': {
        'title': 'Early Refining',
        'included_types': ['Beneficiation', 'Early refining'],
        'target_type': 'Early refining'
    },
    'precursor_2040': {
        'title': 'Precursor Product',
        'included_types': ['Beneficiation', 'Early refining', 'Precursor related product'],
        'target_type': 'Precursor related product'
    }
}

# Mineral order by country participation (descending)
MINERAL_ORDER = ['copper', 'cobalt', 'nickel', 'manganese', 'lithium', 'graphite']

# Constraint mapping for display
CONSTRAINT_LABELS = {
    'country_unconstrained': 'National Focus\n(Unconstrained)',
    'region_unconstrained': 'Regional Integration\n(Unconstrained)'
}


def get_valid_cost_stages(df_country_mineral, scenario_config):
    """
    Determine which stages should contribute costs using production chain validation.

    This validates the production chain to include:
    - All stages with actual production
    - Intermediate stages with costs but zero production (consumed internally)

    And excludes:
    - Orphan stages (costs exist but no downstream production)
    - Dead-end stages (beyond max production stage)

    Parameters:
    -----------
    df_country_mineral : pd.DataFrame
        Data for single country-mineral-scenario combination
    scenario_config : dict
        Scenario configuration with included_types and target_type

    Returns:
    --------
    list of float
        Processing stage numbers to include in cumulative cost calculation
    """
    # Find all stages with actual production
    production_stages = df_country_mineral[
        df_country_mineral['production_tonnes'] > 0
    ]['processing_stage'].unique()

    if len(production_stages) == 0:
        return []

    max_production_stage = max(production_stages)

    # Build list of valid cost stages (by stage number, not type)
    valid_stages = []

    # Filter to only included processing types
    included_data = df_country_mineral[
        df_country_mineral['processing_type'].isin(scenario_config['included_types'])
    ]

    for _, row in included_data.iterrows():
        stage_num = row['processing_stage']
        has_production = row['production_tonnes'] > 0
        has_cost = row['production_transport_energy_unit_cost_usd_per_tonne'] > 0

        if not has_cost:
            continue

        # Include if:
        # A) Stage has production, OR
        # B) Stage is intermediate (< max production stage) with costs
        if has_production or (stage_num < max_production_stage):
            valid_stages.append(stage_num)

    return valid_stages


def extract_cumulative_costs(df, scenario_key, constraint, scenario_config):
    """
    Extract cumulative unit costs for all countries and minerals.

    Uses production chain validation to correctly handle:
    - Complete processing chains (all stages have production)
    - Incomplete chains (intermediate stages consumed internally)
    - Orphan stages (spurious cost data without production chain)

    Parameters:
    -----------
    df : pd.DataFrame
        The main dataset from all_data.xlsx
    scenario_key : str
        Scenario key ('early_refining_2040' or 'precursor_2040')
    constraint : str
        Constraint type ('country_unconstrained' or 'region_unconstrained')
    scenario_config : dict
        Configuration for scenario (included types, target type)

    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: [iso3, reference_mineral, cumulative_cost, production]
    """
    # Determine which demand scenario to use (matching supply curves logic)
    if 'country' in constraint:
        demand_scenario = 'mid_min'
    else:  # region
        demand_scenario = 'mid_max'

    # Filter data - relaxed filter to include intermediate stages with zero production
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["production_transport_energy_unit_cost_usd_per_tonne"] > 0) &
        (df["scenario"].str.contains(scenario_key)) &
        (df["scenario"].str.contains(demand_scenario)) &
        (df["constraint"] == constraint)
    ].copy()

    if len(df_filtered) == 0:
        print(f"Warning: No data for {scenario_key} / {constraint}")
        return pd.DataFrame(columns=['iso3', 'reference_mineral', 'cumulative_cost', 'production'])

    # Calculate cumulative costs for each country-mineral combination
    results = []

    for mineral in df_filtered["reference_mineral"].unique():
        mineral_data = df_filtered[df_filtered["reference_mineral"] == mineral]

        for country in mineral_data["iso3"].unique():
            country_data = mineral_data[mineral_data["iso3"] == country]

            # Get production from target processing type
            target_production = country_data[
                country_data["processing_type"] == scenario_config['target_type']
            ]["production_tonnes_for_costs"].sum()

            # Skip if no production at target stage
            if target_production == 0:
                continue

            # Get valid stages using production chain validation
            valid_stages = get_valid_cost_stages(country_data, scenario_config)

            if not valid_stages:
                continue

            # Calculate cumulative costs from valid stages only
            cumulative_unit_cost = 0
            for stage_num in valid_stages:
                stage_data = country_data[country_data["processing_stage"] == stage_num]
                if not stage_data.empty:
                    stage_cost = stage_data["production_transport_energy_unit_cost_usd_per_tonne"].iloc[0]
                    cumulative_unit_cost += stage_cost

            results.append({
                'iso3': country,
                'reference_mineral': mineral,
                'cumulative_cost': cumulative_unit_cost,
                'production': target_production
            })

    return pd.DataFrame(results)


def calculate_quintile_ranks(df):
    """
    Calculate within-mineral quintile rankings.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with columns: [iso3, reference_mineral, cumulative_cost]

    Returns:
    --------
    pd.DataFrame
        Input DataFrame with added 'quintile' and 'rank' columns
    """
    df = df.copy()

    # Calculate quintile and rank within each mineral
    for mineral in df['reference_mineral'].unique():
        mineral_mask = df['reference_mineral'] == mineral
        mineral_costs = df.loc[mineral_mask, 'cumulative_cost']

        n = len(mineral_costs)
        if n == 0:
            continue

        # Quintile: 1 (lowest 20%) to 5 (highest 20%)
        # Use qcut with labels=False to get numeric quintiles
        try:
            quintiles = pd.qcut(mineral_costs, q=5, labels=False, duplicates='drop') + 1
            # Check if qcut returned NaN (happens with single value or insufficient unique values)
            if quintiles.isna().all():
                raise ValueError("qcut returned all NaN")
            df.loc[mineral_mask, 'quintile'] = quintiles
        except (ValueError, TypeError):
            # If not enough unique values for quintiles, use rank-based approach
            # For single value: rank=1, quintile = ceil(1/1 * 5) = 5... but we want Q1 for best
            # Better approach: map rank directly to quintile range [1-5]
            ranks = mineral_costs.rank(method='min')
            if n <= 5:
                # For 5 or fewer countries, assign quintile = rank (1=Q1, 2=Q2, etc.)
                quintiles = ranks.astype(int)
            else:
                # For >5 countries, distribute into quintiles
                quintiles = np.ceil(ranks / n * 5).astype(int)
            df.loc[mineral_mask, 'quintile'] = quintiles

        # Rank: 1 (lowest cost) to N (highest cost)
        df.loc[mineral_mask, 'rank'] = mineral_costs.rank(method='min').astype(int)

    return df


def create_heatmap_matrix(df, countries):
    """
    Create country × mineral matrix for heatmap.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with columns: [iso3, reference_mineral, cumulative_cost, quintile, rank]
    countries : list
        Ordered list of country ISO3 codes (alphabetical)

    Returns:
    --------
    tuple of (cost_matrix, quintile_matrix, rank_matrix)
        Each as pd.DataFrame with countries as rows, minerals as columns
    """
    # Pivot data
    cost_matrix = df.pivot(index='iso3', columns='reference_mineral', values='cumulative_cost')
    quintile_matrix = df.pivot(index='iso3', columns='reference_mineral', values='quintile')
    rank_matrix = df.pivot(index='iso3', columns='reference_mineral', values='rank')

    # Reindex to ensure all countries present (with NaN for missing)
    cost_matrix = cost_matrix.reindex(index=countries, columns=MINERAL_ORDER)
    quintile_matrix = quintile_matrix.reindex(index=countries, columns=MINERAL_ORDER)
    rank_matrix = rank_matrix.reindex(index=countries, columns=MINERAL_ORDER)

    return cost_matrix, quintile_matrix, rank_matrix


def format_cost_annotation(cost, rank):
    """
    Format cost and rank for cell annotation.

    Parameters:
    -----------
    cost : float
        Cumulative unit cost (USD/tonne)
    rank : int
        Rank within mineral (1 = best)

    Returns:
    --------
    str
        Formatted annotation string
    """
    if pd.isna(cost) or pd.isna(rank):
        return "—"

    # Format cost in thousands with no decimals
    cost_k = int(round(cost / 1000))

    # Two-line format: cost on top, rank below
    return f"${cost_k}k\n#{int(rank)}"


def format_rank_only_annotation(cost, rank):
    """
    Format rank only for cell annotation (no cost).

    Parameters:
    -----------
    cost : float
        Cumulative unit cost (USD/tonne) - not used but kept for consistency
    rank : int
        Rank within mineral (1 = best)

    Returns:
    --------
    str
        Formatted annotation string with rank only
    """
    if pd.isna(rank):
        return "—"

    # Single line format: rank only
    return f"#{int(rank)}"


def plot_competitiveness_heatmap(cost_matrix_national, quintile_matrix_national, rank_matrix_national,
                                  cost_matrix_regional, quintile_matrix_regional, rank_matrix_regional,
                                  scenario_title, output_path, rank_only=False):
    """
    Create side-by-side heatmaps for National and Regional constraints.

    Parameters:
    -----------
    cost_matrix_national, quintile_matrix_national, rank_matrix_national : pd.DataFrame
        Matrices for National Focus constraint
    cost_matrix_regional, quintile_matrix_regional, rank_matrix_regional : pd.DataFrame
        Matrices for Regional Integration constraint
    scenario_title : str
        Scenario name for figure title
    output_path : str
        Path to save figure
    rank_only : bool
        If True, show only rank numbers. If False, show both cost and rank (default)
    """
    # Create figure with 2 subplots (side-by-side)
    fig, axes = plt.subplots(1, 2, figsize=(20, 12))

    # Common parameters
    cmap = 'Greens_r'  # Reversed: Q1 (low value) = dark green, Q5 (high value) = light green
    cbar_kws = {'label': 'Competitiveness Quintile\n(Darker = More Competitive)'}

    # Define consistent vmin/vmax for color scale (1-5 for quintiles)
    vmin, vmax = 1, 5

    # Select annotation formatter based on rank_only parameter
    annotation_func = format_rank_only_annotation if rank_only else format_cost_annotation

    # Plot National Focus (left)
    ax_national = axes[0]

    # Create annotations
    annot_national = np.empty(cost_matrix_national.shape, dtype=object)
    for i in range(cost_matrix_national.shape[0]):
        for j in range(cost_matrix_national.shape[1]):
            cost = cost_matrix_national.iloc[i, j]
            rank = rank_matrix_national.iloc[i, j]
            annot_national[i, j] = annotation_func(cost, rank)

    # Plot heatmap with quintile colors, but annotate with cost+rank
    sns.heatmap(
        quintile_matrix_national,
        annot=annot_national,
        fmt='',
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        cbar_kws=cbar_kws,
        ax=ax_national,
        linewidths=0.5,
        linecolor='gray',
        square=False,
        annot_kws={'fontsize': 16, 'va': 'center'},
        cbar=True,
        mask=quintile_matrix_national.isna()  # Mask missing data
    )

    # Increase colorbar label font size
    cbar_national = ax_national.collections[0].colorbar
    cbar_national.set_label('Competitiveness Quintile\n(Darker = More Competitive)',
                            fontsize=15, fontweight='bold')
    cbar_national.ax.tick_params(labelsize=13)  # Also increase colorbar tick labels

    ax_national.set_title(CONSTRAINT_LABELS['country_unconstrained'],
                         fontsize=18, fontweight='bold', pad=15)
    ax_national.set_xlabel('Mineral', fontsize=17, fontweight='bold')
    ax_national.set_ylabel('Country (ISO3)', fontsize=17, fontweight='bold')
    ax_national.set_yticklabels(ax_national.get_yticklabels(), rotation=0, fontsize=18)
    ax_national.set_xticklabels([m.capitalize() for m in MINERAL_ORDER], rotation=0, ha='center', fontsize=15)

    # Plot Regional Integration (right)
    ax_regional = axes[1]

    # Create annotations
    annot_regional = np.empty(cost_matrix_regional.shape, dtype=object)
    for i in range(cost_matrix_regional.shape[0]):
        for j in range(cost_matrix_regional.shape[1]):
            cost = cost_matrix_regional.iloc[i, j]
            rank = rank_matrix_regional.iloc[i, j]
            annot_regional[i, j] = annotation_func(cost, rank)

    # Plot heatmap
    sns.heatmap(
        quintile_matrix_regional,
        annot=annot_regional,
        fmt='',
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        cbar_kws=cbar_kws,
        ax=ax_regional,
        linewidths=0.5,
        linecolor='gray',
        square=False,
        annot_kws={'fontsize': 16, 'va': 'center'},
        cbar=True,
        mask=quintile_matrix_regional.isna()
    )

    # Increase colorbar label font size
    cbar_regional = ax_regional.collections[0].colorbar
    cbar_regional.set_label('Competitiveness Quintile\n(Darker = More Competitive)',
                            fontsize=15, fontweight='bold')
    cbar_regional.ax.tick_params(labelsize=13)  # Also increase colorbar tick labels

    ax_regional.set_title(CONSTRAINT_LABELS['region_unconstrained'],
                         fontsize=18, fontweight='bold', pad=15)
    ax_regional.set_xlabel('Mineral', fontsize=17, fontweight='bold')
    ax_regional.set_ylabel('')  # No y-label on right plot
    ax_regional.set_yticklabels(ax_regional.get_yticklabels(), rotation=0, fontsize=18)
    ax_regional.set_xticklabels([m.capitalize() for m in MINERAL_ORDER], rotation=0, ha='center', fontsize=15)

    # Main title
    fig.suptitle(f'{scenario_title} (2040)',
                fontsize=22, fontweight='bold', y=0.98)

    # Add interpretation note at bottom
    if rank_only:
        note_text = (
            "Colors show within-mineral quintile rankings (Q1-Q5). Darker green = more competitive (lower cost).\n"
            "Cell annotations: Rank only (#1 = lowest cost).\n"
            "Rankings based on cumulative unit costs (production + transport + energy) for all processing stages up to scenario target."
        )
    else:
        note_text = (
            "Colors show within-mineral quintile rankings (Q1-Q5). Darker green = more competitive (lower cost).\n"
            "Cell annotations: Cost in thousands (USD/tonne) / Rank (#1 = lowest cost).\n"
            "Costs are cumulative unit costs (production + transport + energy) for all processing stages up to scenario target."
        )
    fig.text(0.5, 0.01, note_text, ha='center', fontsize=12, style='italic',
             wrap=True, color='gray')

    # Adjust layout
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])

    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved competitiveness heatmap: {os.path.basename(output_path)}")


def create_competitiveness_heatmaps(df, output_dir):
    """
    Main function to create all competitiveness heatmaps.

    Parameters:
    -----------
    df : pd.DataFrame
        The main dataset from all_data.xlsx
    output_dir : str
        Directory to save the plots

    Returns:
    --------
    list
        Paths to saved figures
    """
    # Create output directory
    competitiveness_dir = os.path.join(output_dir, 'competitiveness_summary')
    os.makedirs(competitiveness_dir, exist_ok=True)

    saved_paths = []

    # Get all countries (alphabetically sorted)
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["scenario"].str.contains("2040")) &
        (df["constraint"].str.contains("unconstrained"))
    ]
    countries = sorted(df_filtered["iso3"].unique())

    print("\n" + "=" * 80)
    print("Generating Competitiveness Heatmaps")
    print("=" * 80)
    print(f"Countries: {len(countries)} ({', '.join(countries)})")
    print(f"Minerals: {len(MINERAL_ORDER)} ({', '.join([m.capitalize() for m in MINERAL_ORDER])})")
    print(f"Scenarios: {len(SCENARIO_CONFIG)} ({', '.join([s for s in SCENARIO_CONFIG.keys()])})")

    # Process each scenario
    for scenario_key, config in SCENARIO_CONFIG.items():
        print(f"\n--- Processing {config['title']} ---")

        # Extract data for both constraints
        df_national = extract_cumulative_costs(df, scenario_key, 'country_unconstrained', config)
        df_regional = extract_cumulative_costs(df, scenario_key, 'region_unconstrained', config)

        if df_national.empty or df_regional.empty:
            print(f"Skipping {scenario_key} - insufficient data")
            continue

        print(f"  National: {len(df_national)} country-mineral combinations")
        print(f"  Regional: {len(df_regional)} country-mineral combinations")

        # Calculate quintiles and ranks
        df_national = calculate_quintile_ranks(df_national)
        df_regional = calculate_quintile_ranks(df_regional)

        # Create matrices
        cost_nat, quintile_nat, rank_nat = create_heatmap_matrix(df_national, countries)
        cost_reg, quintile_reg, rank_reg = create_heatmap_matrix(df_regional, countries)

        # Plot heatmap with costs and ranks
        output_path = os.path.join(competitiveness_dir, f"competitiveness_heatmap_{scenario_key}.png")
        plot_competitiveness_heatmap(
            cost_nat, quintile_nat, rank_nat,
            cost_reg, quintile_reg, rank_reg,
            config['title'],
            output_path,
            rank_only=False
        )
        saved_paths.append(output_path)

        # Plot heatmap with ranks only (no costs)
        output_path_rank_only = os.path.join(competitiveness_dir, f"competitiveness_heatmap_{scenario_key}_rank_only.png")
        plot_competitiveness_heatmap(
            cost_nat, quintile_nat, rank_nat,
            cost_reg, quintile_reg, rank_reg,
            config['title'],
            output_path_rank_only,
            rank_only=True
        )
        saved_paths.append(output_path_rank_only)

    print("\n" + "=" * 80)
    print(f"Competitiveness heatmaps completed. Saved {len(saved_paths)} figures.")
    print(f"Output directory: {competitiveness_dir}")
    print("=" * 80 + "\n")

    return saved_paths


if __name__ == "__main__":
    import json

    # Load config
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "..", "config.json")

    with open(config_path, "r") as f:
        config = json.load(f)

    # Load data
    data_file = os.path.join(config["paths"]["results"], "all_data.xlsx")
    print(f"Loading data from: {data_file}")
    df = pd.read_excel(data_file, index_col=[0,1,2,3,4])
    df = df.reset_index()

    # Generate heatmaps
    figure_path = os.path.join(config["paths"]["figures"], "automated_plots")
    saved_paths = create_competitiveness_heatmaps(df, figure_path)

    print(f"\nGenerated {len(saved_paths)} competitiveness heatmap(s):")
    for path in saved_paths:
        print(f"  - {path}")
