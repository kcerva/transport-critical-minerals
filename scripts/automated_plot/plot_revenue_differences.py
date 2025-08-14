"""
Revenue Difference Analysis for Critical Minerals Policy Scenarios

This module creates visualizations comparing revenue differences between:
1. Regional vs National policy approaches
2. Constrained vs Unconstrained scenarios

Uses precalculated revenue_usd column from the data for analysis.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from typing import Dict, List, Tuple, Optional
import seaborn as sns
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plot_config import reference_mineral_colormap
from plot_utils import get_processing_type_colors

# Set up plotting style
plt.style.use('default')
sns.set_palette("husl")

def get_scenario_names(base_scenario: str, constraint_type: str) -> List[str]:
    """Generate scenario names based on base scenario and constraint type."""
    if constraint_type == 'country':
        return [f"{base_scenario}_mid_min_threshold_metal_tons"]
    elif constraint_type == 'region':  
        return [f"{base_scenario}_mid_max_threshold_metal_tons"]
    else:
        raise ValueError(f"Unknown constraint type: {constraint_type}")

def calculate_regional_vs_national_revenue_difference(df: pd.DataFrame, scenario_base: str, constraint_level: str) -> pd.DataFrame:
    """
    Calculate revenue differences between Regional and National approaches.
    
    Args:
        df: All data DataFrame with revenue_usd column
        scenario_base: Base scenario (e.g., 'precursor_2040')
        constraint_level: 'constrained' or 'unconstrained'
        
    Returns:
        DataFrame with revenue differences by country, processing type, and mineral
    """
    # Get scenario names
    regional_scenarios = get_scenario_names(scenario_base, 'region')
    national_scenarios = get_scenario_names(scenario_base, 'country')
    
    # Create constraint filter based on actual constraint naming
    constraint_filter_regional = f"region_{constraint_level}"
    constraint_filter_national = f"country_{constraint_level}"
    
    # Filter data for the specific scenarios and constraint level
    regional_data = df[
        (df['scenario'].isin(regional_scenarios)) & 
        (df['constraint'] == constraint_filter_regional)
    ].copy()
    
    national_data = df[
        (df['scenario'].isin(national_scenarios)) & 
        (df['constraint'] == constraint_filter_national)
    ].copy()
    
    if regional_data.empty or national_data.empty:
        print(f"Warning: No data found for scenarios {regional_scenarios} or {national_scenarios} with constraint {constraint_level}")
        return pd.DataFrame()
    
    # Aggregate by country, processing stage, processing type, and mineral
    regional_agg = regional_data.groupby(['iso3', 'processing_stage', 'processing_type', 'reference_mineral'])['revenue_usd'].sum().reset_index()
    national_agg = national_data.groupby(['iso3', 'processing_stage', 'processing_type', 'reference_mineral'])['revenue_usd'].sum().reset_index()
    
    # Merge and calculate differences
    merged = pd.merge(
        regional_agg, national_agg, 
        on=['iso3', 'processing_stage', 'processing_type', 'reference_mineral'],
        suffixes=('_regional', '_national'),
        how='outer'
    ).fillna(0)
    
    # Calculate difference (Regional - National)
    merged['revenue_diff_musd'] = (merged['revenue_usd_regional'] - merged['revenue_usd_national']) / 1000
    merged['revenue_diff_percent'] = np.where(
        merged['revenue_usd_national'] != 0,
        (merged['revenue_diff_musd'] * 1000) / merged['revenue_usd_national'] * 100,
        0
    )
    
    return merged

def calculate_constrained_vs_unconstrained_revenue_difference(df: pd.DataFrame, scenario_base: str, policy_type: str) -> pd.DataFrame:
    """
    Calculate revenue differences between Constrained and Unconstrained scenarios.
    
    Args:
        df: All data DataFrame with revenue_usd column
        scenario_base: Base scenario (e.g., 'precursor_2040')
        policy_type: 'country' or 'region'
        
    Returns:
        DataFrame with revenue differences by country, processing type, and mineral
    """
    # Get scenario names
    scenario_names = get_scenario_names(scenario_base, policy_type)
    
    # Create constraint filters based on actual constraint naming
    constraint_filter_constrained = f"{policy_type}_constrained"
    constraint_filter_unconstrained = f"{policy_type}_unconstrained"
    
    # Filter data for the specific scenario
    constrained_data = df[
        (df['scenario'].isin(scenario_names)) & 
        (df['constraint'] == constraint_filter_constrained)
    ].copy()
    
    unconstrained_data = df[
        (df['scenario'].isin(scenario_names)) & 
        (df['constraint'] == constraint_filter_unconstrained)
    ].copy()
    
    if constrained_data.empty or unconstrained_data.empty:
        print(f"Warning: No data found for scenarios {scenario_names} with both constraint levels")
        return pd.DataFrame()
    
    # Aggregate by country, processing stage, processing type, and mineral
    constrained_agg = constrained_data.groupby(['iso3', 'processing_stage', 'processing_type', 'reference_mineral'])['revenue_usd'].sum().reset_index()
    unconstrained_agg = unconstrained_data.groupby(['iso3', 'processing_stage', 'processing_type', 'reference_mineral'])['revenue_usd'].sum().reset_index()
    
    # Merge and calculate differences
    merged = pd.merge(
        constrained_agg, unconstrained_agg, 
        on=['iso3', 'processing_stage', 'processing_type', 'reference_mineral'],
        suffixes=('_constrained', '_unconstrained'),
        how='outer'
    ).fillna(0)
    
    # Calculate difference (Constrained - Unconstrained)
    merged['revenue_diff_musd'] = (merged['revenue_usd_constrained'] - merged['revenue_usd_unconstrained']) / 1000
    merged['revenue_diff_percent'] = np.where(
        merged['revenue_usd_unconstrained'] != 0,
        (merged['revenue_diff_musd'] * 1000) / merged['revenue_usd_unconstrained'] * 100,
        0
    )
    
    return merged

def create_aggregated_revenue_difference_plot(df: pd.DataFrame, title: str, output_path: str, scenario_year: str = '2040'):
    """Create aggregated revenue difference plot across all minerals."""
    
    # Aggregate by country and processing stage (sum across minerals)
    agg_data = df.groupby(['iso3', 'processing_stage']).agg({
        'revenue_diff_musd': 'sum'
    }).reset_index()
    
    # Filter processing stages to focus on meaningful ones
    processing_stages = [2.0, 5.0]  # Early refining and Precursor related product
    agg_data = agg_data[agg_data['processing_stage'].isin(processing_stages)]
    
    if agg_data.empty:
        print(f"No data available for aggregated plot: {title}")
        return
    
    # Map stage numbers to names
    stage_names = {2.0: 'Early refining', 5.0: 'Precursor related product'}
    agg_data['processing_stage_name'] = agg_data['processing_stage'].map(stage_names)
    
    # Create pivot table for plotting
    pivot_data = agg_data.pivot(index='iso3', columns='processing_stage_name', values='revenue_diff_musd').fillna(0)
    
    # Sort by total absolute difference
    pivot_data['total_abs'] = pivot_data.abs().sum(axis=1)
    pivot_data = pivot_data.sort_values('total_abs', ascending=True)
    pivot_data = pivot_data.drop('total_abs', axis=1)
    
    # Create figure
    fig, axes = plt.subplots(1, len(processing_stages), figsize=(15, 8))
    if len(processing_stages) == 1:
        axes = [axes]
    
    # Calculate consistent x-axis range
    all_values = []
    for stage in processing_stages:
        if stage in pivot_data.columns:
            all_values.extend(pivot_data[stage].values)
    
    if all_values:
        x_range = max(abs(min(all_values)), abs(max(all_values))) * 1.1
        x_lim = [-x_range, x_range]
    else:
        x_lim = [-1, 1]
    
    colors = plt.cm.RdBu_r(np.linspace(0, 1, len(pivot_data)))
    
    for i, stage in enumerate(processing_stages):
        ax = axes[i]
        
        if stage in pivot_data.columns:
            stage_data = pivot_data[stage]
            
            # Create horizontal bar plot
            bars = ax.barh(range(len(stage_data)), stage_data.values, color=colors)
            
            # Add value labels
            for j, (idx, value) in enumerate(stage_data.items()):
                if abs(value) > 0.01:
                    ax.text(value + (0.05 * x_range if value >= 0 else -0.05 * x_range), j, 
                           f'{value:.1f}', ha='left' if value >= 0 else 'right', va='center', fontsize=8)
        
        ax.set_xlim(x_lim)
        ax.set_yticks(range(len(pivot_data)))
        ax.set_yticklabels(pivot_data.index, fontsize=10)
        ax.set_xlabel('Revenue Difference (Million USD)', fontsize=10)
        ax.set_title(f'{stage} {scenario_year}', fontsize=11, pad=10)
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        ax.grid(True, axis='x', alpha=0.3)
    
    plt.suptitle(title, fontsize=14, y=0.95)
    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved aggregated revenue difference plot: {output_path}")

def create_scenario_revenue_difference_plot_by_stage(scenario_dfs: Dict[str, pd.DataFrame], 
                                                    comparison_type: str, constraint_level: str,
                                                    output_path: str, scenario_labels: Dict[str, str] = None):
    """Create stacked bar revenue difference plot by processing stage with subplots for multiple scenarios."""
    
    # Use the correct processing type colors and patterns from production differences
    processing_colors = get_processing_type_colors()
    
    # Process data for all scenarios
    scenarios_data = {}
    for scenario_name, df in scenario_dfs.items():
        if df.empty:
            continue
        # Aggregate across minerals by processing_type and country
        agg_data = df.groupby(['iso3', 'processing_type']).agg({
            'revenue_diff_musd': 'sum'
        }).reset_index()
        
        # Filter out Metal content as it's not relevant for processing comparisons
        agg_data = agg_data[agg_data['processing_type'] != 'Metal content']
        
        # Pivot to get processing types as columns and countries as rows
        pivot_data = agg_data.pivot(index='iso3', columns='processing_type', values='revenue_diff_musd').fillna(0)
        scenarios_data[scenario_name] = pivot_data
    
    if not scenarios_data:
        print(f"No data available for stage plot: {comparison_type}")
        return
    
    # Get all countries and processing types across all scenarios
    all_countries = set()
    all_processing_types = set()
    for pivot in scenarios_data.values():
        all_countries.update(pivot.index)
        all_processing_types.update(pivot.columns)
    all_countries = sorted(all_countries)
    all_processing_types = sorted([pt for pt in all_processing_types if pt in processing_colors])
    
    # Determine number of scenarios and create subplots
    n_scenarios = len(scenarios_data)
    fig, axes = plt.subplots(1, n_scenarios, figsize=(8*n_scenarios, max(8, len(all_countries) * 0.4)))
    if n_scenarios == 1:
        axes = [axes]
    
    # Calculate overall x-axis range for consistency
    all_values = []
    for pivot in scenarios_data.values():
        # Calculate stacked totals for x-axis range
        for country in pivot.index:
            pos_sum = pivot.loc[country][pivot.loc[country] > 0].sum()
            neg_sum = pivot.loc[country][pivot.loc[country] < 0].sum()
            all_values.extend([pos_sum, neg_sum])
    
    if all_values:
        max_abs_val = max(abs(v) for v in all_values if pd.notna(v))
        x_range = max_abs_val * 1.1 if max_abs_val > 0 else 1
    else:
        x_range = 1
    
    # Plot each scenario
    for idx, (scenario_name, pivot_data) in enumerate(scenarios_data.items()):
        ax = axes[idx]
        if len(pivot_data) == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            scenario_title = scenario_labels.get(scenario_name, scenario_name) if scenario_labels else scenario_name.replace('_', ' ').title()
            ax.set_title(scenario_title, fontsize=12, fontweight='bold')
            continue
        
        # Ensure all countries are present
        pivot_data = pivot_data.reindex(all_countries, fill_value=0)
        
        # Sort countries by total absolute revenue difference
        total_abs = pivot_data.abs().sum(axis=1).sort_values()
        pivot_data = pivot_data.loc[total_abs.index]
        
        y_positions = np.arange(len(pivot_data))
        
        # Track cumulative positions for stacking
        pos_left = np.zeros(len(pivot_data))
        neg_right = np.zeros(len(pivot_data))
        
        # Plot each processing type as a stacked bar with appropriate patterns
        for proc_type in all_processing_types:
            if proc_type in pivot_data.columns:
                values = pivot_data[proc_type].values
                color = processing_colors.get(proc_type, '#cccccc')
                
                # Apply patterns like in production differences
                if proc_type == "Beneficiation":
                    hatches = None
                    alpha = 0.8
                elif proc_type == "Early refining":
                    hatches = '///'
                    alpha = 0.7
                else:  # Precursor related product
                    hatches = '...'
                    alpha = 0.6
                
                # Separate positive and negative values
                pos_values = np.where(values > 0, values, 0)
                neg_values = np.where(values < 0, values, 0)
                
                # Plot positive values
                if pos_values.any():
                    ax.barh(y_positions, pos_values, left=pos_left, 
                           color=color, alpha=alpha, hatch=hatches, 
                           edgecolor='white', linewidth=0.5,
                           label=proc_type)
                    pos_left += pos_values
                
                # Plot negative values
                if neg_values.any():
                    ax.barh(y_positions, neg_values, left=neg_right,
                           color=color, alpha=alpha, hatch=hatches,
                           edgecolor='white', linewidth=0.5)
                    neg_right += neg_values
        
        # Add value labels for totals (only if space permits)
        for i, country in enumerate(pivot_data.index):
            total = pivot_data.loc[country].sum()
            if abs(total) > 0.01:
                # Check if there's enough space to avoid overlap
                if i == 0 or abs(y_positions[i] - y_positions[i-1]) > 0.5:
                    ax.text(total + (0.02 * x_range if total >= 0 else -0.02 * x_range),
                           i, f'{total:.0f}', ha='left' if total >= 0 else 'right',
                           va='center', fontsize=7)
        
        # Set labels and formatting
        ax.set_yticks(y_positions)
        ax.set_yticklabels(pivot_data.index, fontsize=10)
        ax.set_xlim([-x_range, x_range])
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        ax.grid(True, axis='x', alpha=0.3)
        
        # Set proper x-axis label with comparison direction
        if comparison_type == 'regional_vs_national':
            xlabel = "Revenue Difference: Regional minus National (Million USD)"
        else:
            xlabel = "Revenue Difference: Constrained minus Unconstrained (Million USD)"
        ax.set_xlabel(xlabel, fontsize=11)
        scenario_title = scenario_labels.get(scenario_name, scenario_name) if scenario_labels else scenario_name.replace('_', ' ').title()
        ax.set_title(scenario_title, fontsize=12, fontweight='bold')
        
        # Add legend only to first subplot
        if idx == 0:
            handles, labels = ax.get_legend_handles_labels()
            # Remove duplicates while preserving order
            seen = set()
            unique_handles_labels = [(h, l) for h, l in zip(handles, labels) 
                                    if l not in seen and not seen.add(l)]
            if unique_handles_labels:
                unique_handles, unique_labels = zip(*unique_handles_labels)
                ax.legend(unique_handles, unique_labels, loc='lower right', fontsize=9)
    
    # Create title based on comparison type
    if comparison_type == 'regional_vs_national':
        title = f"Regional vs National Revenue Differences by Stage - {constraint_level}"
    else:
        title = f"Constrained vs Unconstrained Revenue Differences by Stage - {constraint_level}"
    
    plt.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.1)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved stage-based revenue difference plot: {output_path}")

def create_scenario_revenue_difference_plot(scenario_dfs: Dict[str, pd.DataFrame], 
                                           comparison_type: str, constraint_level: str,
                                           output_path: str, scenario_labels: Dict[str, str] = None):
    """Create stacked bar revenue difference plot with subplots for multiple scenarios.
    
    Args:
        scenario_dfs: Dictionary mapping scenario names to DataFrames
        comparison_type: 'regional_vs_national' or 'constrained_vs_unconstrained'
        constraint_level: Additional context for the comparison
        output_path: Path to save the figure
    """
    
    # Use the correct mineral colors from plot_config
    mineral_colors = reference_mineral_colormap
    
    # Process data for all scenarios
    scenarios_data = {}
    for scenario_name, df in scenario_dfs.items():
        if df.empty:
            continue
        # Aggregate across all processing stages by mineral and country
        agg_data = df.groupby(['iso3', 'reference_mineral']).agg({
            'revenue_diff_musd': 'sum'
        }).reset_index()
        
        # Pivot to get minerals as columns and countries as rows
        pivot_data = agg_data.pivot(index='iso3', columns='reference_mineral', values='revenue_diff_musd').fillna(0)
        scenarios_data[scenario_name] = pivot_data
    
    if not scenarios_data:
        print(f"No data available for plot: {comparison_type}")
        return
    
    # Get all countries and minerals across all scenarios
    all_countries = set()
    all_minerals = set()
    for pivot in scenarios_data.values():
        all_countries.update(pivot.index)
        all_minerals.update(pivot.columns)
    all_countries = sorted(all_countries)
    all_minerals = sorted(all_minerals)
    
    # Determine number of scenarios and create subplots
    n_scenarios = len(scenarios_data)
    fig, axes = plt.subplots(1, n_scenarios, figsize=(8*n_scenarios, max(8, len(all_countries) * 0.4)))
    if n_scenarios == 1:
        axes = [axes]
    
    # Calculate overall x-axis range for consistency
    all_values = []
    for pivot in scenarios_data.values():
        # Calculate stacked totals for x-axis range
        for country in pivot.index:
            pos_sum = pivot.loc[country][pivot.loc[country] > 0].sum()
            neg_sum = pivot.loc[country][pivot.loc[country] < 0].sum()
            all_values.extend([pos_sum, neg_sum])
    
    if all_values:
        max_abs_val = max(abs(v) for v in all_values if pd.notna(v))
        x_range = max_abs_val * 1.1 if max_abs_val > 0 else 1
    else:
        x_range = 1
    
    # Plot each scenario
    for idx, (scenario_name, pivot_data) in enumerate(scenarios_data.items()):
        ax = axes[idx]
        if len(pivot_data) == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            scenario_title = scenario_labels.get(scenario_name, scenario_name) if scenario_labels else scenario_name.replace('_', ' ').title()
            ax.set_title(scenario_title, fontsize=12, fontweight='bold')
            continue
        
        # Ensure all countries are present
        pivot_data = pivot_data.reindex(all_countries, fill_value=0)
        
        # Sort countries by total absolute revenue difference
        total_abs = pivot_data.abs().sum(axis=1).sort_values()
        pivot_data = pivot_data.loc[total_abs.index]
        
        y_positions = np.arange(len(pivot_data))
        
        # Track cumulative positions for stacking
        pos_left = np.zeros(len(pivot_data))
        neg_right = np.zeros(len(pivot_data))
        
        # Plot each mineral as a stacked bar
        for mineral in all_minerals:
            if mineral in pivot_data.columns:
                values = pivot_data[mineral].values
                color = mineral_colors.get(mineral, '#cccccc')
                
                # Separate positive and negative values
                pos_values = np.where(values > 0, values, 0)
                neg_values = np.where(values < 0, values, 0)
                
                # Plot positive values
                if pos_values.any():
                    ax.barh(y_positions, pos_values, left=pos_left, 
                           color=color, alpha=0.7, edgecolor='black', linewidth=0.5,
                           label=mineral.replace('_', ' ').title())
                    pos_left += pos_values
                
                # Plot negative values
                if neg_values.any():
                    ax.barh(y_positions, neg_values, left=neg_right,
                           color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
                    neg_right += neg_values
        
        # Add value labels for totals (only if space permits)
        for i, country in enumerate(pivot_data.index):
            total = pivot_data.loc[country].sum()
            if abs(total) > 0.01:
                # Check if there's enough space to avoid overlap
                if i == 0 or abs(y_positions[i] - y_positions[i-1]) > 0.5:
                    ax.text(total + (0.02 * x_range if total >= 0 else -0.02 * x_range),
                           i, f'{total:.0f}', ha='left' if total >= 0 else 'right',
                           va='center', fontsize=7)
        
        # Set labels and formatting
        ax.set_yticks(y_positions)
        ax.set_yticklabels(pivot_data.index, fontsize=10)
        ax.set_xlim([-x_range, x_range])
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        ax.grid(True, axis='x', alpha=0.3)
        
        # Set proper x-axis label with comparison direction
        if comparison_type == 'regional_vs_national':
            xlabel = "Revenue Difference: Regional minus National (Million USD)"
        else:
            xlabel = "Revenue Difference: Constrained minus Unconstrained (Million USD)"
        ax.set_xlabel(xlabel, fontsize=11)
        scenario_title = scenario_labels.get(scenario_name, scenario_name) if scenario_labels else scenario_name.replace('_', ' ').title()
        ax.set_title(scenario_title, fontsize=12, fontweight='bold')
        
        # Add legend only to first subplot
        if idx == 0:
            handles, labels = ax.get_legend_handles_labels()
            # Remove duplicates while preserving order
            seen = set()
            unique_handles_labels = [(h, l) for h, l in zip(handles, labels) 
                                    if l not in seen and not seen.add(l)]
            if unique_handles_labels:
                unique_handles, unique_labels = zip(*unique_handles_labels)
                ax.legend(unique_handles, unique_labels, loc='lower right', fontsize=9)
    
    # Create title based on comparison type
    if comparison_type == 'regional_vs_national':
        title = f"Regional vs National Revenue Differences - {constraint_level}"
    else:
        title = f"Constrained vs Unconstrained Revenue Differences - {constraint_level}"
    
    plt.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.1)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved stacked revenue difference plot: {output_path}")

def create_mineral_breakdown_revenue_plot(df: pd.DataFrame, title: str, output_path: str):
    """Create revenue difference plot broken down by mineral."""
    
    # Map processing stages to names and filter
    stage_names = {1.0: 'Beneficiation', 2.0: 'Early refining', 5.0: 'Precursor related product'}
    df = df.copy()
    df['processing_stage_name'] = df['processing_stage'].map(stage_names)
    
    # Filter processing stages and get unique minerals
    processing_stages = ['Beneficiation', 'Early refining', 'Precursor related product']
    df = df[df['processing_stage_name'].isin(processing_stages)]
    minerals = df['reference_mineral'].unique()
    
    # Create figure with subplots
    fig, axes = plt.subplots(len(minerals), len(processing_stages), figsize=(18, 4*len(minerals)))
    if len(minerals) == 1:
        axes = axes.reshape(1, -1)
    if len(processing_stages) == 1:
        axes = axes.reshape(-1, 1)
    
    # Calculate x-axis ranges for each processing stage
    x_ranges = {}
    for stage in processing_stages:
        stage_data = df[df['processing_stage_name'] == stage]
        if not stage_data.empty:
            countries = stage_data['iso3'].unique()
            all_stacked_values = []
            
            # Calculate stacked totals by country
            for country in countries:
                country_data = stage_data[stage_data['iso3'] == country]
                country_stacked_total = country_data['revenue_diff_musd'].sum()
                all_stacked_values.append(country_stacked_total)
            
            if all_stacked_values:
                max_abs_val = max(abs(min(all_stacked_values)), abs(max(all_stacked_values)))
                x_ranges[stage] = max_abs_val * 1.1
            else:
                x_ranges[stage] = 1
        else:
            x_ranges[stage] = 1
    
    for i, mineral in enumerate(minerals):
        for j, stage in enumerate(processing_stages):
            ax = axes[i, j] if len(minerals) > 1 else axes[j]
            
            # Filter data for this mineral and processing stage
            plot_data = df[
                (df['reference_mineral'] == mineral) & 
                (df['processing_stage_name'] == stage)
            ]
            
            if not plot_data.empty:
                # Sort by absolute value
                plot_data = plot_data.copy()
                plot_data['abs_diff'] = plot_data['revenue_diff_musd'].abs()
                plot_data = plot_data.sort_values('abs_diff')
                
                # Create horizontal bar plot
                bars = ax.barh(range(len(plot_data)), plot_data['revenue_diff_musd'], 
                             color=color_map[mineral], alpha=0.7, edgecolor='black', linewidth=0.5)
                
                # Add value labels for significant values
                for k, (_, row) in enumerate(plot_data.iterrows()):
                    value = row['revenue_diff_musd']
                    if abs(value) > 0.01:
                        ax.text(value + (0.05 * x_ranges[stage] if value >= 0 else -0.05 * x_ranges[stage]), 
                               k, f'{value:.1f}', ha='left' if value >= 0 else 'right', 
                               va='center', fontsize=7)
                
                ax.set_yticks(range(len(plot_data)))
                ax.set_yticklabels(plot_data['iso3'], fontsize=8)
            
            # Set consistent x-axis range
            ax.set_xlim([-x_ranges[stage], x_ranges[stage]])
            ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
            ax.grid(True, axis='x', alpha=0.3)
            
            if i == len(minerals) - 1:
                ax.set_xlabel('Revenue Difference (Million USD)', fontsize=9)
            if j == 0:
                ax.set_ylabel(mineral, fontsize=10, fontweight='bold')
            if i == 0:
                ax.set_title(stage, fontsize=11, pad=10)
    
    plt.suptitle(title, fontsize=14, y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94, hspace=0.3)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved mineral breakdown revenue plot: {output_path}")

def calculate_scenario_revenue_differences(df: pd.DataFrame, scenario_base: str, constraint_type: str) -> Dict[str, pd.DataFrame]:
    """Calculate revenue differences for different scenario comparisons.
    
    Returns a dictionary with scenario names as keys and difference DataFrames as values.
    """
    results = {}
    
    # For early_refining and precursor scenarios
    for scenario_prefix in ['early_refining_2040', 'precursor_2040']:
        if constraint_type == 'regional_vs_national':
            # Calculate differences for both constrained and unconstrained
            for constraint_level in ['constrained', 'unconstrained']:
                diff_df = calculate_regional_vs_national_revenue_difference(df, scenario_prefix, constraint_level)
                if not diff_df.empty:
                    scenario_name = f"{scenario_prefix.split('_')[0].title()} ({constraint_level.title()})"
                    results[scenario_name] = diff_df
        
        elif constraint_type == 'constrained_vs_unconstrained':
            # Calculate differences for both country and region policies
            for policy_type in ['country', 'region']:
                diff_df = calculate_constrained_vs_unconstrained_revenue_difference(df, scenario_prefix, policy_type)
                if not diff_df.empty:
                    scenario_name = f"{scenario_prefix.split('_')[0].title()} ({'National' if policy_type == 'country' else 'Regional'})"
                    results[scenario_name] = diff_df
    
    return results

def generate_essential_revenue_difference_plots(output_dir: str):
    """Generate the essential revenue difference plots."""
    
    # Load data
    data_path = "/home/karlac/critical_minerals_Africa/transport-outputs/results/all_data.xlsx"
    
    print("Loading data for revenue difference analysis...")
    try:
        df = pd.read_excel(data_path, sheet_name='Sheet1')
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Verify revenue_usd column exists
    if 'revenue_usd' not in df.columns:
        print("Error: revenue_usd column not found in data")
        return
    
    print("Generating revenue difference plots...")
    
    # 1. Regional vs National comparisons - Constrained scenarios
    print("Calculating Regional vs National revenue differences (Constrained)...")
    reg_nat_constrained_scenarios = {}
    for scenario_prefix in ['early_refining_2040', 'precursor_2040']:
        diff_df = calculate_regional_vs_national_revenue_difference(df, scenario_prefix, 'constrained')
        if not diff_df.empty:
            if scenario_prefix == 'early_refining_2040':
                scenario_name = 'Early Processing 2040'
            else:  # precursor_2040
                scenario_name = 'Product Manufacturing 2040'
            reg_nat_constrained_scenarios[scenario_name] = diff_df
    
    if reg_nat_constrained_scenarios:
        # Mineral-stacked plots
        create_scenario_revenue_difference_plot(
            reg_nat_constrained_scenarios,
            'regional_vs_national',
            'Constrained Scenarios',
            os.path.join(output_dir, "regional_vs_national_constrained_revenue.png")
        )
        
        # Stage-stacked plots
        create_scenario_revenue_difference_plot_by_stage(
            reg_nat_constrained_scenarios,
            'regional_vs_national',
            'Constrained Scenarios',
            os.path.join(output_dir, "regional_vs_national_constrained_revenue_by_stage.png")
        )
    
    # 2. Regional vs National comparisons - Unconstrained scenarios
    print("Calculating Regional vs National revenue differences (Unconstrained)...")
    reg_nat_unconstrained_scenarios = {}
    for scenario_prefix in ['early_refining_2040', 'precursor_2040']:
        diff_df = calculate_regional_vs_national_revenue_difference(df, scenario_prefix, 'unconstrained')
        if not diff_df.empty:
            if scenario_prefix == 'early_refining_2040':
                scenario_name = 'Early Processing 2040'
            else:  # precursor_2040
                scenario_name = 'Product Manufacturing 2040'
            reg_nat_unconstrained_scenarios[scenario_name] = diff_df
    
    if reg_nat_unconstrained_scenarios:
        # Mineral-stacked plots
        create_scenario_revenue_difference_plot(
            reg_nat_unconstrained_scenarios,
            'regional_vs_national',
            'Unconstrained Scenarios',
            os.path.join(output_dir, "regional_vs_national_unconstrained_revenue.png")
        )
        
        # Stage-stacked plots
        create_scenario_revenue_difference_plot_by_stage(
            reg_nat_unconstrained_scenarios,
            'regional_vs_national',
            'Unconstrained Scenarios',
            os.path.join(output_dir, "regional_vs_national_unconstrained_revenue_by_stage.png")
        )
    
    # 3. Constrained vs Unconstrained comparisons - National Focus
    print("Calculating Constrained vs Unconstrained revenue differences (National Focus)...")
    cons_uncons_national_scenarios = {}
    for scenario_prefix in ['bau_2040', 'early_refining_2040', 'precursor_2040']:
        diff_df = calculate_constrained_vs_unconstrained_revenue_difference(df, scenario_prefix, 'country')
        if not diff_df.empty:
            if scenario_prefix == 'bau_2040':
                scenario_name = 'BAU 2040'
            elif scenario_prefix == 'early_refining_2040':
                scenario_name = 'Early Processing 2040'
            else:  # precursor_2040
                scenario_name = 'Product Manufacturing 2040'
            cons_uncons_national_scenarios[scenario_name] = diff_df
    
    if cons_uncons_national_scenarios:
        # Mineral-stacked plots
        create_scenario_revenue_difference_plot(
            cons_uncons_national_scenarios,
            'constrained_vs_unconstrained', 
            'National Focus',
            os.path.join(output_dir, "constrained_vs_unconstrained_country_revenue.png")
        )
        
        # Stage-stacked plots
        create_scenario_revenue_difference_plot_by_stage(
            cons_uncons_national_scenarios,
            'constrained_vs_unconstrained',
            'National Focus',
            os.path.join(output_dir, "constrained_vs_unconstrained_country_revenue_by_stage.png")
        )
    
    # 4. Constrained vs Unconstrained comparisons - Regional Integration
    print("Calculating Constrained vs Unconstrained revenue differences (Regional Integration)...")
    cons_uncons_regional_scenarios = {}
    for scenario_prefix in ['bau_2040', 'early_refining_2040', 'precursor_2040']:
        diff_df = calculate_constrained_vs_unconstrained_revenue_difference(df, scenario_prefix, 'region')
        if not diff_df.empty:
            if scenario_prefix == 'bau_2040':
                scenario_name = 'BAU 2040'
            elif scenario_prefix == 'early_refining_2040':
                scenario_name = 'Early Processing 2040'
            else:  # precursor_2040
                scenario_name = 'Product Manufacturing 2040'
            cons_uncons_regional_scenarios[scenario_name] = diff_df
    
    if cons_uncons_regional_scenarios:
        # Mineral-stacked plots
        create_scenario_revenue_difference_plot(
            cons_uncons_regional_scenarios,
            'constrained_vs_unconstrained',
            'Regional Integration',
            os.path.join(output_dir, "constrained_vs_unconstrained_region_revenue.png")
        )
        
        # Stage-stacked plots
        create_scenario_revenue_difference_plot_by_stage(
            cons_uncons_regional_scenarios,
            'constrained_vs_unconstrained',
            'Regional Integration',
            os.path.join(output_dir, "constrained_vs_unconstrained_region_revenue_by_stage.png")
        )
    
    print("Revenue difference analysis complete!")

if __name__ == "__main__":
    output_directory = "/home/karlac/critical_minerals_Africa/transport-outputs/figures/automated_plots/revenue_differences"
    generate_essential_revenue_difference_plots(output_directory)