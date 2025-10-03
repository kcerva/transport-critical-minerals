"""
Production Percentage Change Visualization
Shows percentage changes in production between different policy scenarios

Specifications:
1. Include all three processing types (Beneficiation, Early refining, Precursor related product)
2. Use comprehensive view (Option A) with processing type breakdown
3. Aggregate across processing types for mineral breakdown
4. Calculate percentage changes on processing-type-specific production
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
from plot_config import reference_mineral_colormap, reference_mineral_namemap
from plot_utils import get_processing_type_colors

def get_scenario_name(base_scenario, constraint_type):
    """
    Get correct scenario name based on constraint type
    Args:
        base_scenario: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        constraint_type: 'country' or 'region'
    """
    if constraint_type == 'country':
        return f"{base_scenario}_mid_min_threshold_metal_tons"
    elif constraint_type == 'region':
        return f"{base_scenario}_mid_max_threshold_metal_tons"
    else:
        raise ValueError(f"Unknown constraint_type: {constraint_type}")

def calculate_production_pct_change_regional_vs_national(df, scenario_base, constraint_level, min_baseline_tonnes=10000):
    """
    Calculate percentage change in production: (Regional - National) / National × 100
    Calculates per processing type, then provides both aggregated and detailed views

    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        constraint_level: 'constrained' or 'unconstrained'
        min_baseline_tonnes: Minimum national production baseline to include (default 10,000 tonnes)

    Returns:
        Three DataFrames:
        - aggregated: Total production % change by country (all processing types summed)
        - by_processing_type: Production % change by country and processing type
        - by_mineral: Production % change by country and mineral (processing types aggregated)
    """

    # Get correct scenario names
    regional_scenario = get_scenario_name(scenario_base, 'region')
    national_scenario = get_scenario_name(scenario_base, 'country')

    # Get constraint combinations
    regional_constraint = f"region_{constraint_level}"
    national_constraint = f"country_{constraint_level}"

    print(f"Calculating production % change for {scenario_base} ({constraint_level}):")
    print(f"  Regional: {regional_scenario} + {regional_constraint}")
    print(f"  National: {national_scenario} + {national_constraint}")

    # Filter data - include all processing stages > 0 and all processing types
    regional_data = df[
        (df['scenario'] == regional_scenario) &
        (df['constraint'] == regional_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    national_data = df[
        (df['scenario'] == national_scenario) &
        (df['constraint'] == national_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    if regional_data.empty or national_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({constraint_level})")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Calculate by processing type (for stacked view)
    regional_by_type = regional_data.groupby(['iso3', 'processing_type'])['production_tonnes'].sum().reset_index()
    regional_by_type.columns = ['iso3', 'processing_type', 'production_regional']

    national_by_type = national_data.groupby(['iso3', 'processing_type'])['production_tonnes'].sum().reset_index()
    national_by_type.columns = ['iso3', 'processing_type', 'production_national']

    # Merge and calculate percentage change by processing type
    merged_by_type = pd.merge(regional_by_type, national_by_type, on=['iso3', 'processing_type'], how='outer').fillna(0)
    merged_by_type['production_pct_change'] = merged_by_type.apply(
        lambda row: ((row['production_regional'] - row['production_national']) / row['production_national'] * 100)
        if row['production_national'] != 0 else 0, axis=1
    )
    by_processing_type = merged_by_type[['iso3', 'processing_type', 'production_pct_change']].copy()

    # Calculate by mineral (aggregate across processing types)
    regional_by_mineral = regional_data.groupby(['iso3', 'reference_mineral'])['production_tonnes'].sum().reset_index()
    regional_by_mineral.columns = ['iso3', 'reference_mineral', 'production_regional']

    national_by_mineral = national_data.groupby(['iso3', 'reference_mineral'])['production_tonnes'].sum().reset_index()
    national_by_mineral.columns = ['iso3', 'reference_mineral', 'production_national']

    # Merge and calculate percentage change by mineral
    merged_by_mineral = pd.merge(regional_by_mineral, national_by_mineral, on=['iso3', 'reference_mineral'], how='outer').fillna(0)
    merged_by_mineral['production_pct_change'] = merged_by_mineral.apply(
        lambda row: ((row['production_regional'] - row['production_national']) / row['production_national'] * 100)
        if row['production_national'] != 0 else 0, axis=1
    )
    by_mineral = merged_by_mineral[['iso3', 'reference_mineral', 'production_pct_change']].copy()

    # Calculate aggregated (total across all processing types and minerals)
    regional_total = regional_data.groupby('iso3')['production_tonnes'].sum().reset_index()
    regional_total.columns = ['iso3', 'production_regional']

    national_total = national_data.groupby('iso3')['production_tonnes'].sum().reset_index()
    national_total.columns = ['iso3', 'production_national']

    # Apply minimum baseline threshold to filter out small-base countries
    # This prevents misleading percentages from countries with very low baseline production
    # Example: Kenya (6K tonnes baseline) showing 282% is misleading vs Tanzania (3.3M baseline) at 43%
    # The 10K threshold keeps meaningful producers (e.g., Angola at 210K tonnes, +59% is legitimate)
    # while excluding statistical artifacts from near-zero baselines
    #
    # NOTE: Angola shows +337% in Precursor Product scenario (240K baseline → 1.05M regional)
    # This is technically legitimate (baseline >> 10K threshold) but is an extreme outlier.
    # The high % reflects Angola becoming a major copper precursor product hub (stages 4.3 & 5)
    # with 811K tonne absolute gain. Kept in analysis as baseline is substantial (24x threshold).
    # If extreme percentages become problematic, consider raising threshold to 500K.
    national_total_filtered = national_total[national_total['production_national'] >= min_baseline_tonnes]
    countries_to_keep = set(national_total_filtered['iso3'].values)

    # Merge and calculate total percentage change
    merged_total = pd.merge(regional_total, national_total, on='iso3', how='outer').fillna(0)
    merged_total['production_pct_change'] = merged_total.apply(
        lambda row: ((row['production_regional'] - row['production_national']) / row['production_national'] * 100)
        if row['production_national'] != 0 else 0, axis=1
    )

    # Filter aggregated results to only include countries meeting threshold
    aggregated = merged_total[merged_total['iso3'].isin(countries_to_keep)][['iso3', 'production_pct_change']].copy()

    # Also filter by_processing_type and by_mineral to same countries
    by_processing_type = by_processing_type[by_processing_type['iso3'].isin(countries_to_keep)].copy()
    by_mineral = by_mineral[by_mineral['iso3'].isin(countries_to_keep)].copy()

    excluded_countries = len(merged_total) - len(aggregated)
    print(f"  Countries with data: {len(aggregated)} (excluded {excluded_countries} below {min_baseline_tonnes:,.0f} tonne threshold)")
    print(f"  Avg total % change: {aggregated['production_pct_change'].mean():.1f}%")

    return aggregated, by_processing_type, by_mineral

def calculate_production_pct_change_by_mineral_global(df, scenario_base, constraint_level):
    """
    Calculate percentage change in production by mineral (aggregated across all countries)

    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        constraint_level: 'constrained' or 'unconstrained'

    Returns:
        DataFrame with columns: reference_mineral, production_pct_change
    """
    # Get correct scenario names
    regional_scenario = get_scenario_name(scenario_base, 'region')
    national_scenario = get_scenario_name(scenario_base, 'country')

    regional_constraint = f"region_{constraint_level}"
    national_constraint = f"country_{constraint_level}"

    print(f"Calculating by-mineral global production % change for {scenario_base} ({constraint_level}):")
    print(f"  Regional: {regional_scenario} + {regional_constraint}")
    print(f"  National: {national_scenario} + {national_constraint}")

    # Filter data - include all processing stages > 0 and all processing types
    regional_data = df[
        (df['scenario'] == regional_scenario) &
        (df['constraint'] == regional_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    national_data = df[
        (df['scenario'] == national_scenario) &
        (df['constraint'] == national_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    if regional_data.empty or national_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({constraint_level})")
        return pd.DataFrame()

    # Aggregate by mineral across ALL countries
    regional_by_mineral = regional_data.groupby('reference_mineral')['production_tonnes'].sum().reset_index()
    regional_by_mineral.columns = ['reference_mineral', 'production_regional']

    national_by_mineral = national_data.groupby('reference_mineral')['production_tonnes'].sum().reset_index()
    national_by_mineral.columns = ['reference_mineral', 'production_national']

    # Merge and calculate percentage change
    merged = pd.merge(regional_by_mineral, national_by_mineral, on='reference_mineral', how='outer').fillna(0)
    merged['production_pct_change'] = merged.apply(
        lambda row: ((row['production_regional'] - row['production_national']) / row['production_national'] * 100)
        if row['production_national'] != 0 else 0, axis=1
    )

    result = merged[['reference_mineral', 'production_pct_change']].copy()

    print(f"  Minerals with data: {len(result)}")
    print(f"  Avg mineral % change: {result['production_pct_change'].mean():.1f}%")

    return result

def calculate_revenue_pct_change_by_mineral_global(df, scenario_base, constraint_level):
    """
    Calculate percentage change in revenue by mineral (aggregated across all countries)

    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        constraint_level: 'constrained' or 'unconstrained'

    Returns:
        DataFrame with columns: reference_mineral, revenue_pct_change
    """
    # Get correct scenario names
    regional_scenario = get_scenario_name(scenario_base, 'region')
    national_scenario = get_scenario_name(scenario_base, 'country')

    regional_constraint = f"region_{constraint_level}"
    national_constraint = f"country_{constraint_level}"

    print(f"Calculating by-mineral global revenue % change for {scenario_base} ({constraint_level}):")
    print(f"  Regional: {regional_scenario} + {regional_constraint}")
    print(f"  National: {national_scenario} + {national_constraint}")

    # Filter data - include all processing stages > 0 and all processing types
    regional_data = df[
        (df['scenario'] == regional_scenario) &
        (df['constraint'] == regional_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    national_data = df[
        (df['scenario'] == national_scenario) &
        (df['constraint'] == national_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    if regional_data.empty or national_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({constraint_level})")
        return pd.DataFrame()

    # Aggregate by mineral across ALL countries
    regional_by_mineral = regional_data.groupby('reference_mineral')['revenue_usd'].sum().reset_index()
    regional_by_mineral.columns = ['reference_mineral', 'revenue_regional']

    national_by_mineral = national_data.groupby('reference_mineral')['revenue_usd'].sum().reset_index()
    national_by_mineral.columns = ['reference_mineral', 'revenue_national']

    # Merge and calculate percentage change
    merged = pd.merge(regional_by_mineral, national_by_mineral, on='reference_mineral', how='outer').fillna(0)
    merged['revenue_pct_change'] = merged.apply(
        lambda row: ((row['revenue_regional'] - row['revenue_national']) / row['revenue_national'] * 100)
        if row['revenue_national'] != 0 else 0, axis=1
    )

    result = merged[['reference_mineral', 'revenue_pct_change']].copy()

    print(f"  Minerals with data: {len(result)}")
    print(f"  Avg mineral % change: {result['revenue_pct_change'].mean():.1f}%")

    return result

def calculate_value_added_pct_change_by_mineral_global(df, scenario_base, constraint_level):
    """
    Calculate percentage change in value added by mineral (aggregated across all countries)

    Value Added = Revenue - All Costs (production + transport + energy)

    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        constraint_level: 'constrained' or 'unconstrained'

    Returns:
        DataFrame with columns: reference_mineral, value_added_pct_change
    """
    # Get correct scenario names
    regional_scenario = get_scenario_name(scenario_base, 'region')
    national_scenario = get_scenario_name(scenario_base, 'country')

    regional_constraint = f"region_{constraint_level}"
    national_constraint = f"country_{constraint_level}"

    print(f"Calculating by-mineral global value added % change for {scenario_base} ({constraint_level}):")
    print(f"  Regional: {regional_scenario} + {regional_constraint}")
    print(f"  National: {national_scenario} + {national_constraint}")

    # Filter data - include all processing stages > 0 and all processing types
    regional_data = df[
        (df['scenario'] == regional_scenario) &
        (df['constraint'] == regional_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ].copy()

    national_data = df[
        (df['scenario'] == national_scenario) &
        (df['constraint'] == national_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ].copy()

    if regional_data.empty or national_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({constraint_level})")
        return pd.DataFrame()

    # Calculate value-added for each row: Revenue - All Costs
    regional_data['value_added'] = regional_data['revenue_usd'] - regional_data['all_cost_usd']
    national_data['value_added'] = national_data['revenue_usd'] - national_data['all_cost_usd']

    # Aggregate by mineral across ALL countries
    regional_by_mineral = regional_data.groupby('reference_mineral')['value_added'].sum().reset_index()
    regional_by_mineral.columns = ['reference_mineral', 'value_added_regional']

    national_by_mineral = national_data.groupby('reference_mineral')['value_added'].sum().reset_index()
    national_by_mineral.columns = ['reference_mineral', 'value_added_national']

    # Merge and calculate percentage change
    merged = pd.merge(regional_by_mineral, national_by_mineral, on='reference_mineral', how='outer').fillna(0)
    merged['value_added_pct_change'] = merged.apply(
        lambda row: ((row['value_added_regional'] - row['value_added_national']) / row['value_added_national'] * 100)
        if row['value_added_national'] != 0 else 0, axis=1
    )

    result = merged[['reference_mineral', 'value_added_pct_change']].copy()

    print(f"  Minerals with data: {len(result)}")
    print(f"  Avg mineral % change: {result['value_added_pct_change'].mean():.1f}%")

    return result

def calculate_production_pct_change_constrained_vs_unconstrained(df, scenario_base, policy_type, min_baseline_tonnes=10000):
    """
    Calculate percentage change in production: (Constrained - Unconstrained) / Unconstrained × 100
    Calculates per processing type, then provides both aggregated and detailed views

    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        policy_type: 'country' or 'region'
        min_baseline_tonnes: Minimum unconstrained production baseline to include (default 10,000 tonnes)

    Returns:
        Three DataFrames:
        - aggregated: Total production % change by country (all processing types summed)
        - by_processing_type: Production % change by country and processing type
        - by_mineral: Production % change by country and mineral (processing types aggregated)
    """

    # Get correct scenario name
    scenario = get_scenario_name(scenario_base, policy_type)

    # Get constraint combinations
    constrained_constraint = f"{policy_type}_constrained"
    unconstrained_constraint = f"{policy_type}_unconstrained"

    print(f"Calculating production % change for {scenario_base} ({policy_type}):")
    print(f"  Constrained: {scenario} + {constrained_constraint}")
    print(f"  Unconstrained: {scenario} + {unconstrained_constraint}")

    # Filter data - include all processing stages > 0 and all processing types
    constrained_data = df[
        (df['scenario'] == scenario) &
        (df['constraint'] == constrained_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    unconstrained_data = df[
        (df['scenario'] == scenario) &
        (df['constraint'] == unconstrained_constraint) &
        (df['processing_stage'] > 0) &
        (df['processing_type'] != 'Metal content')
    ]

    if constrained_data.empty or unconstrained_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({policy_type})")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Calculate by processing type (for stacked view)
    constrained_by_type = constrained_data.groupby(['iso3', 'processing_type'])['production_tonnes'].sum().reset_index()
    constrained_by_type.columns = ['iso3', 'processing_type', 'production_constrained']

    unconstrained_by_type = unconstrained_data.groupby(['iso3', 'processing_type'])['production_tonnes'].sum().reset_index()
    unconstrained_by_type.columns = ['iso3', 'processing_type', 'production_unconstrained']

    # Merge and calculate percentage change by processing type
    merged_by_type = pd.merge(constrained_by_type, unconstrained_by_type, on=['iso3', 'processing_type'], how='outer').fillna(0)
    merged_by_type['production_pct_change'] = merged_by_type.apply(
        lambda row: ((row['production_constrained'] - row['production_unconstrained']) / row['production_unconstrained'] * 100)
        if row['production_unconstrained'] != 0 else 0, axis=1
    )
    by_processing_type = merged_by_type[['iso3', 'processing_type', 'production_pct_change']].copy()

    # Calculate by mineral (aggregate across processing types)
    constrained_by_mineral = constrained_data.groupby(['iso3', 'reference_mineral'])['production_tonnes'].sum().reset_index()
    constrained_by_mineral.columns = ['iso3', 'reference_mineral', 'production_constrained']

    unconstrained_by_mineral = unconstrained_data.groupby(['iso3', 'reference_mineral'])['production_tonnes'].sum().reset_index()
    unconstrained_by_mineral.columns = ['iso3', 'reference_mineral', 'production_unconstrained']

    # Merge and calculate percentage change by mineral
    merged_by_mineral = pd.merge(constrained_by_mineral, unconstrained_by_mineral, on=['iso3', 'reference_mineral'], how='outer').fillna(0)
    merged_by_mineral['production_pct_change'] = merged_by_mineral.apply(
        lambda row: ((row['production_constrained'] - row['production_unconstrained']) / row['production_unconstrained'] * 100)
        if row['production_unconstrained'] != 0 else 0, axis=1
    )
    by_mineral = merged_by_mineral[['iso3', 'reference_mineral', 'production_pct_change']].copy()

    # Calculate aggregated (total across all processing types and minerals)
    constrained_total = constrained_data.groupby('iso3')['production_tonnes'].sum().reset_index()
    constrained_total.columns = ['iso3', 'production_constrained']

    unconstrained_total = unconstrained_data.groupby('iso3')['production_tonnes'].sum().reset_index()
    unconstrained_total.columns = ['iso3', 'production_unconstrained']

    # Apply minimum baseline threshold to filter out small-base countries
    # This prevents misleading percentages from countries with very low baseline production
    # See calculate_production_pct_change_regional_vs_national for detailed explanation
    unconstrained_total_filtered = unconstrained_total[unconstrained_total['production_unconstrained'] >= min_baseline_tonnes]
    countries_to_keep = set(unconstrained_total_filtered['iso3'].values)

    # Merge and calculate total percentage change
    merged_total = pd.merge(constrained_total, unconstrained_total, on='iso3', how='outer').fillna(0)
    merged_total['production_pct_change'] = merged_total.apply(
        lambda row: ((row['production_constrained'] - row['production_unconstrained']) / row['production_unconstrained'] * 100)
        if row['production_unconstrained'] != 0 else 0, axis=1
    )

    # Filter aggregated results to only include countries meeting threshold
    aggregated = merged_total[merged_total['iso3'].isin(countries_to_keep)][['iso3', 'production_pct_change']].copy()

    # Also filter by_processing_type and by_mineral to same countries
    by_processing_type = by_processing_type[by_processing_type['iso3'].isin(countries_to_keep)].copy()
    by_mineral = by_mineral[by_mineral['iso3'].isin(countries_to_keep)].copy()

    excluded_countries = len(merged_total) - len(aggregated)
    print(f"  Countries with data: {len(aggregated)} (excluded {excluded_countries} below {min_baseline_tonnes:,.0f} tonne threshold)")
    print(f"  Avg total % change: {aggregated['production_pct_change'].mean():.1f}%")

    return aggregated, by_processing_type, by_mineral

def create_aggregated_pct_subplot(ax, data, scenario_label, x_min, x_max):
    """
    Create a single subplot showing aggregated production percentage changes
    """
    if data.empty:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(scenario_label, fontsize=16, fontweight='bold')
        return

    # Sort countries by production change for better visualization
    data_sorted = data.sort_values('production_pct_change')
    countries = data_sorted['iso3'].values
    values = data_sorted['production_pct_change'].values

    # Create color array based on positive/negative values
    colors = ['#2E7D32' if v > 0 else '#C62828' for v in values]  # Green for gains, Red for losses

    # Create horizontal bar chart
    y_pos = np.arange(len(countries))
    bars = ax.barh(y_pos, values, color=colors, alpha=0.7, edgecolor='white', linewidth=0.5)

    # Add value labels for significant changes
    for i, (country, value) in enumerate(zip(countries, values)):
        if abs(value) > 5:  # Only label if change is more than 5%
            if value > 0:
                x_pos = value + (x_max - x_min) * 0.02
                ha = 'left'
            else:
                x_pos = value - (x_max - x_min) * 0.02
                ha = 'right'

            ax.text(x_pos, i, f'{value:.0f}%', va='center', ha=ha,
                   fontsize=11, fontweight='bold', color='darkgreen' if value > 0 else 'darkred')

    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(countries, fontsize=13)
    ax.set_xlim(x_min, x_max)
    ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)
    ax.set_title(scenario_label, fontsize=16, fontweight='bold', pad=10)
    ax.set_xlabel('Production Change (%)', fontsize=14)
    ax.tick_params(axis='x', labelsize=12)

def create_by_processing_type_subplot(ax, data, scenario_label, x_min, x_max):
    """
    Create stacked horizontal bar chart by processing type
    """
    if data.empty:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(scenario_label, fontsize=16, fontweight='bold')
        return

    # Pivot to get processing types as columns
    pivot = data.pivot(index='iso3', columns='processing_type', values='production_pct_change').fillna(0)

    # Ensure we have the expected processing types
    processing_types = ['Beneficiation', 'Early refining', 'Precursor related product']
    for ptype in processing_types:
        if ptype not in pivot.columns:
            pivot[ptype] = 0

    # Reorder columns
    pivot = pivot[processing_types]

    # Sort by total change
    pivot['total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('total')
    pivot = pivot.drop(columns='total')

    # Get colors for processing types
    colors = get_processing_type_colors()
    plot_colors = [colors.get(ptype, '#999999') for ptype in processing_types]

    # Create stacked horizontal bar chart
    pivot.plot(kind='barh', stacked=True, ax=ax, color=plot_colors,
               edgecolor='white', linewidth=0.5, width=0.7)

    # Formatting
    ax.set_xlim(x_min, x_max)
    ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)
    ax.set_title(scenario_label, fontsize=16, fontweight='bold', pad=10)
    ax.set_xlabel('Production Change (%)', fontsize=14)
    ax.set_ylabel('Country', fontsize=14)
    ax.tick_params(axis='both', labelsize=13)
    ax.legend(title='Processing Type', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11, title_fontsize=12)

def create_by_mineral_subplot(ax, data, scenario_label, x_min, x_max):
    """
    Create stacked horizontal bar chart by mineral
    """
    if data.empty:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(scenario_label, fontsize=12, fontweight='bold')
        return

    # Pivot to get minerals as columns
    pivot = data.pivot(index='iso3', columns='reference_mineral', values='production_pct_change').fillna(0)

    # Sort by total change
    pivot['total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('total')
    pivot = pivot.drop(columns='total')

    # Get colors for minerals
    plot_colors = [reference_mineral_colormap.get(mineral, '#999999') for mineral in pivot.columns]

    # Create stacked horizontal bar chart
    pivot.plot(kind='barh', stacked=True, ax=ax, color=plot_colors,
               edgecolor='white', linewidth=0.5, width=0.7)

    # Formatting
    ax.set_xlim(x_min, x_max)
    ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)
    ax.set_title(scenario_label, fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Production Change (%)', fontsize=10)
    ax.set_ylabel('Country', fontsize=10)

    # Create legend with short names
    handles, labels = ax.get_legend_handles_labels()
    short_labels = [reference_mineral_namemap.get(label, label) for label in labels]
    ax.legend(handles, short_labels, title='Mineral', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

def create_by_mineral_global_subplot(ax, data, scenario_label, x_min, x_max, metric='production'):
    """
    Create horizontal bar chart - one bar per mineral (global aggregation)

    Args:
        ax: Matplotlib axis
        data: DataFrame with reference_mineral and either production_pct_change or revenue_pct_change
        scenario_label: Title for subplot
        x_min, x_max: X-axis limits
        metric: 'production' or 'revenue' - determines which column to plot
    """
    if data.empty:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_title(scenario_label, fontsize=16, fontweight='bold')
        return

    # Determine column name based on metric
    pct_col = f'{metric}_pct_change'

    # Sort by percentage change
    data_sorted = data.sort_values(pct_col)

    # Get colors for minerals
    colors = [reference_mineral_colormap.get(m, '#999999')
              for m in data_sorted['reference_mineral']]

    # Get readable names
    labels = [reference_mineral_namemap.get(m, m)
              for m in data_sorted['reference_mineral']]

    # Create horizontal bar chart
    y_pos = np.arange(len(data_sorted))
    ax.barh(y_pos, data_sorted[pct_col],
            color=colors, height=0.7, edgecolor='white', linewidth=0.5)

    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=13)
    ax.set_xlim(x_min, x_max)
    ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)
    ax.set_title(scenario_label, fontsize=16, fontweight='bold', pad=10)

    # Set x-label based on metric
    if metric == 'production':
        xlabel = 'Production Change (%)'
    elif metric == 'revenue':
        xlabel = 'Revenue Change (%)'
    elif metric == 'value_added':
        xlabel = 'Value Added Change (%)'
    else:
        xlabel = 'Change (%)'

    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel('Mineral', fontsize=14)
    ax.tick_params(axis='both', labelsize=13)

def generate_aggregated_regional_vs_national(df, output_dir):
    """
    Generate aggregated production percentage change plots for Regional vs National comparison
    """
    print("\n=== Generating Aggregated Production % Change: Regional vs National ===")

    # Exclude BAU as it should be identical
    scenarios = ['early_refining_2040', 'precursor_2040']
    scenario_labels = ['Early Refining 2040', 'Precursor Product 2040']

    for constraint_level in ['constrained', 'unconstrained']:
        print(f"\nProcessing {constraint_level} scenarios...")

        # Create figure with 1x2 layout
        fig, axes = plt.subplots(1, 2, figsize=(14, 8), dpi=300)

        # Collect data and determine consistent x-axis range
        all_data = []
        all_values = []

        for scenario in scenarios:
            aggregated, _, _ = calculate_production_pct_change_regional_vs_national(df, scenario, constraint_level)
            all_data.append(aggregated)
            if not aggregated.empty:
                all_values.extend(aggregated['production_pct_change'].values)

        # Calculate x-axis range with sufficient padding for labels
        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)

            # Add fixed padding for labels (15% of range, minimum 10 units)
            range_val = max_val - min_val
            padding = max(range_val * 0.15, 10)

            x_min = min_val - padding
            x_max = max_val + padding
        else:
            x_min, x_max = -50, 50

        # Create subplots
        for idx, (scenario_label, pct_data) in enumerate(zip(scenario_labels, all_data)):
            create_aggregated_pct_subplot(axes[idx], pct_data, scenario_label, x_min, x_max)

        # Overall title
        fig.suptitle(f'Production Change: Regional vs National - {constraint_level.title()} Scenarios',
                    fontsize=14, fontweight='bold', y=0.98)

        # Add explanatory text
        fig.text(0.5, 0.02, 'Positive values indicate higher production under Regional Integration; Negative values indicate higher production under National Focus\nCountries with <10,000 tonnes baseline excluded',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save
        output_path = os.path.join(output_dir, f'production_pct_change_regional_vs_national_{constraint_level}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

def generate_aggregated_constrained_vs_unconstrained(df, output_dir):
    """
    Generate aggregated production percentage change plots for Constrained vs Unconstrained comparison
    """
    print("\n=== Generating Aggregated Production % Change: Constrained vs Unconstrained ===")

    scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
    scenario_labels = ['BAU 2040', 'Early Refining 2040', 'Precursor Product 2040']

    for policy_type in ['country', 'region']:
        policy_label = 'National Focus' if policy_type == 'country' else 'Regional Integration'
        print(f"\nProcessing {policy_label} policy...")

        # Create figure with 1x3 layout
        fig, axes = plt.subplots(1, 3, figsize=(18, 8), dpi=300)

        # Collect data and determine consistent x-axis range
        all_data = []
        all_values = []

        for scenario in scenarios:
            aggregated, _, _ = calculate_production_pct_change_constrained_vs_unconstrained(df, scenario, policy_type)
            all_data.append(aggregated)
            if not aggregated.empty:
                all_values.extend(aggregated['production_pct_change'].values)

        # Calculate x-axis range with sufficient padding for labels
        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)

            # Add fixed padding for labels (15% of range, minimum 10 units)
            range_val = max_val - min_val
            padding = max(range_val * 0.15, 10)

            x_min = min_val - padding
            x_max = max_val + padding
        else:
            x_min, x_max = -50, 50

        # Create subplots
        for idx, (scenario_label, pct_data) in enumerate(zip(scenario_labels, all_data)):
            create_aggregated_pct_subplot(axes[idx], pct_data, scenario_label, x_min, x_max)

        # Overall title
        fig.suptitle(f'Production Change: Constrained vs Unconstrained - {policy_label}',
                    fontsize=14, fontweight='bold', y=0.98)

        # Add explanatory text
        fig.text(0.5, 0.02, 'Negative values indicate production loss due to environmental constraints; Positive values indicate production gain under constraints\nCountries with <10,000 tonnes baseline excluded',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save
        output_path = os.path.join(output_dir, f'production_pct_change_constrained_vs_unconstrained_{policy_type}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

def generate_by_processing_type_regional_vs_national(df, output_dir):
    """
    Generate by-processing-type production percentage change plots for Regional vs National comparison
    """
    print("\n=== Generating By-Processing-Type Production % Change: Regional vs National ===")

    scenarios = ['early_refining_2040', 'precursor_2040']
    scenario_labels = ['Early Refining 2040', 'Precursor Product 2040']

    for constraint_level in ['constrained', 'unconstrained']:
        print(f"\nProcessing {constraint_level} scenarios...")

        # Create figure with 1x2 layout
        fig, axes = plt.subplots(1, 2, figsize=(16, 8), dpi=300)

        # Collect data and determine consistent x-axis range based on STACKED totals
        all_data = []
        all_stacked_totals = []

        for scenario in scenarios:
            _, by_processing_type, _ = calculate_production_pct_change_regional_vs_national(df, scenario, constraint_level)
            all_data.append(by_processing_type)
            if not by_processing_type.empty:
                # Calculate stacked totals per country (sum across processing types)
                country_totals = by_processing_type.groupby('iso3')['production_pct_change'].sum()
                all_stacked_totals.extend(country_totals.values)

        # Calculate x-axis range with sufficient padding for labels
        if all_stacked_totals:
            min_val = min(all_stacked_totals)
            max_val = max(all_stacked_totals)

            # Add fixed padding for labels (15% of range, minimum 10 units)
            range_val = max_val - min_val
            padding = max(range_val * 0.15, 10)

            x_min = min_val - padding
            x_max = max_val + padding
        else:
            x_min, x_max = -50, 50

        # Create subplots
        for idx, (scenario_label, pct_data) in enumerate(zip(scenario_labels, all_data)):
            create_by_processing_type_subplot(axes[idx], pct_data, scenario_label, x_min, x_max)

        # Overall title
        fig.suptitle(f'Production Change by Processing Type: Regional vs National - {constraint_level.title()}',
                    fontsize=14, fontweight='bold', y=0.98)

        fig.text(0.5, 0.02, 'Stacked by processing type - shows which processing level drives production changes\nCountries with <10,000 tonnes baseline excluded',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save
        output_path = os.path.join(output_dir, f'production_pct_change_by_processing_type_regional_vs_national_{constraint_level}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

def generate_by_processing_type_constrained_vs_unconstrained(df, output_dir):
    """
    Generate by-processing-type production percentage change plots for Constrained vs Unconstrained comparison
    """
    print("\n=== Generating By-Processing-Type Production % Change: Constrained vs Unconstrained ===")

    scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
    scenario_labels = ['BAU 2040', 'Early Refining 2040', 'Precursor Product 2040']

    for policy_type in ['country', 'region']:
        policy_label = 'National Focus' if policy_type == 'country' else 'Regional Integration'
        print(f"\nProcessing {policy_label} policy...")

        # Create figure with 1x3 layout
        fig, axes = plt.subplots(1, 3, figsize=(20, 8), dpi=300)

        # Collect data and determine consistent x-axis range based on STACKED totals
        all_data = []
        all_stacked_totals = []

        for scenario in scenarios:
            _, by_processing_type, _ = calculate_production_pct_change_constrained_vs_unconstrained(df, scenario, policy_type)
            all_data.append(by_processing_type)
            if not by_processing_type.empty:
                # Calculate stacked totals per country (sum across processing types)
                country_totals = by_processing_type.groupby('iso3')['production_pct_change'].sum()
                all_stacked_totals.extend(country_totals.values)

        # Calculate x-axis range with sufficient padding for labels
        if all_stacked_totals:
            min_val = min(all_stacked_totals)
            max_val = max(all_stacked_totals)

            # Add fixed padding for labels (15% of range, minimum 10 units)
            range_val = max_val - min_val
            padding = max(range_val * 0.15, 10)

            x_min = min_val - padding
            x_max = max_val + padding
        else:
            x_min, x_max = -50, 50

        # Create subplots
        for idx, (scenario_label, pct_data) in enumerate(zip(scenario_labels, all_data)):
            create_by_processing_type_subplot(axes[idx], pct_data, scenario_label, x_min, x_max)

        # Overall title
        fig.suptitle(f'Production Change by Processing Type: Constrained vs Unconstrained - {policy_label}',
                    fontsize=14, fontweight='bold', y=0.98)

        fig.text(0.5, 0.02, 'Stacked by processing type - shows which processing level drives production changes\nCountries with <10,000 tonnes baseline excluded',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save
        output_path = os.path.join(output_dir, f'production_pct_change_by_processing_type_constrained_vs_unconstrained_{policy_type}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

# Removed: generate_by_mineral_regional_vs_national() and generate_by_mineral_constrained_vs_unconstrained()
# Reason: Percentage change calculation doesn't work well for minerals with zero national production,
# making it ineffective for highlighting small-scale or emerging mineral production.
# The large scale differences (3 tonnes to 6M tonnes) also made single-metric visualization problematic.

def generate_by_mineral_global_regional_vs_national(df, output_dir):
    """
    Generate by-mineral bar charts (global aggregation) for Regional vs National comparison
    Shows how each mineral's global production changes under regional vs national policies
    """
    print("\n=== Generating By-Mineral Global Production % Change: Regional vs National ===")

    # Exclude BAU as it should be identical for regional vs national
    scenarios = [
        ('early_refining_2040', 'Early Refining 2040'),
        ('precursor_2040', 'Precursor Product 2040')
    ]

    for constraint_level in ['constrained', 'unconstrained']:
        print(f"\nProcessing {constraint_level} scenarios...")

        all_data = []

        for scenario_key, scenario_label in scenarios:
            by_mineral = calculate_production_pct_change_by_mineral_global(
                df, scenario_key, constraint_level
            )
            by_mineral['scenario'] = scenario_label
            all_data.append(by_mineral)

        # Calculate consistent x-axis range
        all_values = []
        for scenario_data in all_data:
            if not scenario_data.empty:
                all_values.extend(scenario_data['production_pct_change'].values)

        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)
            data_range = max_val - min_val
            padding = max(data_range * 0.15, 10)
            x_min = min_val - padding
            x_max = max_val + padding
        else:
            x_min, x_max = -50, 50

        # Create figure with 2 subplots (vertical)
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), dpi=300)

        for idx, (scenario_key, scenario_label) in enumerate(scenarios):
            create_by_mineral_global_subplot(axes[idx], all_data[idx], scenario_label, x_min, x_max)

        # Overall title
        constraint_label = constraint_level.capitalize()
        fig.suptitle(f'Production Change by Mineral: Regional vs National Integration - {constraint_label}',
                    fontsize=14, fontweight='bold', y=0.98)

        fig.text(0.5, 0.02, 'Global production aggregated across all countries - shows which minerals benefit most from regional integration',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save figure
        output_file = os.path.join(output_dir,
                                   f'production_pct_change_by_mineral_global_regional_vs_national_{constraint_level}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Saved: {output_file}")

def generate_by_mineral_global_revenue_regional_vs_national(df, config):
    """
    Generate by-mineral revenue bar charts (global aggregation) for Regional vs National comparison
    Shows how each mineral's global revenue changes under regional vs national policies
    """
    print("\n=== Generating By-Mineral Global Revenue % Change: Regional vs National ===")

    # Use revenue_percentage_changes folder (aligned with existing revenue visualizations)
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'revenue_percentage_changes')
    os.makedirs(output_dir, exist_ok=True)

    # Exclude BAU as it should be identical for regional vs national
    scenarios = [
        ('early_refining_2040', 'Early Refining 2040'),
        ('precursor_2040', 'Precursor Product 2040')
    ]

    for constraint_level in ['constrained', 'unconstrained']:
        print(f"\nProcessing {constraint_level} scenarios...")

        all_data = []

        for scenario_key, scenario_label in scenarios:
            by_mineral = calculate_revenue_pct_change_by_mineral_global(
                df, scenario_key, constraint_level
            )
            by_mineral['scenario'] = scenario_label
            all_data.append(by_mineral)

        # Calculate consistent x-axis range
        all_values = []
        for scenario_data in all_data:
            if not scenario_data.empty:
                all_values.extend(scenario_data['revenue_pct_change'].values)

        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)
            data_range = max_val - min_val
            padding = max(data_range * 0.15, 10)
            x_min = min_val - padding
            x_max = max_val + padding
        else:
            x_min, x_max = -50, 50

        # Create figure with 2 subplots (vertical)
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), dpi=300)

        for idx, (scenario_key, scenario_label) in enumerate(scenarios):
            create_by_mineral_global_subplot(axes[idx], all_data[idx], scenario_label, x_min, x_max, metric='revenue')

        # Overall title
        constraint_label = constraint_level.capitalize()
        fig.suptitle(f'Revenue Change by Mineral: Regional vs National Integration - {constraint_label}',
                    fontsize=14, fontweight='bold', y=0.98)

        fig.text(0.5, 0.02, 'Global revenue aggregated across all countries - shows which minerals\' revenues benefit most from regional integration',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save figure
        output_file = os.path.join(output_dir,
                                   f'revenue_pct_change_by_mineral_global_regional_vs_national_{constraint_level}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Saved: {output_file}")

def generate_by_mineral_global_value_added_regional_vs_national(df, config):
    """
    Generate by-mineral value added bar charts (global aggregation) for Regional vs National comparison
    Shows how each mineral's global value added changes under regional vs national policies

    Value Added = Revenue - All Costs (production + transport + energy)
    """
    print("\n=== Generating By-Mineral Global Value Added % Change: Regional vs National ===")

    # Use revenue_percentage_changes folder (aligned with revenue visualizations)
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'revenue_percentage_changes')
    os.makedirs(output_dir, exist_ok=True)

    # Exclude BAU as it should be identical for regional vs national
    scenarios = [
        ('early_refining_2040', 'Early Refining 2040'),
        ('precursor_2040', 'Precursor Product 2040')
    ]

    for constraint_level in ['constrained', 'unconstrained']:
        print(f"\nProcessing {constraint_level} scenarios...")

        all_data = []

        for scenario_key, scenario_label in scenarios:
            by_mineral = calculate_value_added_pct_change_by_mineral_global(
                df, scenario_key, constraint_level
            )
            by_mineral['scenario'] = scenario_label
            all_data.append(by_mineral)

        # Calculate consistent x-axis range
        all_values = []
        for scenario_data in all_data:
            if not scenario_data.empty:
                all_values.extend(scenario_data['value_added_pct_change'].values)

        if all_values:
            min_val = min(all_values)
            max_val = max(all_values)
            data_range = max_val - min_val
            padding = max(data_range * 0.15, 10)
            x_min = min_val - padding
            x_max = max_val + padding
        else:
            x_min, x_max = -50, 50

        # Create figure with 2 subplots (vertical)
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), dpi=300)

        for idx, (scenario_key, scenario_label) in enumerate(scenarios):
            create_by_mineral_global_subplot(axes[idx], all_data[idx], scenario_label, x_min, x_max, metric='value_added')

        # Overall title
        constraint_label = constraint_level.capitalize()
        fig.suptitle(f'Value Added Change by Mineral: Regional vs National Integration - {constraint_label}',
                    fontsize=14, fontweight='bold', y=0.98)

        fig.text(0.5, 0.02, 'Global value added (Revenue - Costs) aggregated across all countries - shows real wealth creation from regional integration',
                ha='center', fontsize=10, style='italic')

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save figure
        output_file = os.path.join(output_dir,
                                   f'value_added_pct_change_by_mineral_global_regional_vs_national_{constraint_level}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Saved: {output_file}")

def main():
    """
    Main function to generate production percentage change plots
    """
    print("=" * 60)
    print("PRODUCTION PERCENTAGE CHANGE ANALYSIS")
    print("=" * 60)

    # Load configuration
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config.json")

    with open(config_path, "r") as f:
        config = json.load(f)

    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"\nLoading data from: {data_path}")
    df = pd.read_excel(data_path)

    print(f"Data shape: {df.shape}")
    print(f"Available columns: {df.columns.tolist()}")

    # Check required columns
    required_cols = ['production_tonnes', 'processing_stage', 'processing_type', 'iso3', 'reference_mineral', 'scenario', 'constraint']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        return

    # Create output directory
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'production_percentage_changes')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Generate plot types (country-level by-mineral visualizations removed - see comment above)
    generate_aggregated_regional_vs_national(df, output_dir)
    generate_aggregated_constrained_vs_unconstrained(df, output_dir)
    generate_by_processing_type_regional_vs_national(df, output_dir)
    generate_by_processing_type_constrained_vs_unconstrained(df, output_dir)
    generate_by_mineral_global_regional_vs_national(df, output_dir)
    generate_by_mineral_global_revenue_regional_vs_national(df, config)
    generate_by_mineral_global_value_added_regional_vs_national(df, config)

    print("\n" + "=" * 60)
    print("All production percentage change plots completed!")
    print(f"Plots saved to: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()