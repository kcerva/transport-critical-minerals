"""
Production Difference Visualization
Plots showing Regional vs National production differences across scenarios and processing types
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from plot_utils import get_processing_type_colors, get_mineral_colors
from plot_config import reference_minerals, reference_mineral_colors, reference_mineral_colormap

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

def filter_by_processing_type_stages(df, scenario, constraint):
    """Filter data using existing processing_type information"""
    
    # Filter data - use original processing_type from data
    filtered = df[
        (df['scenario'] == scenario) & 
        (df['constraint'] == constraint) &
        (df['processing_stage'] > 0) &  # Exclude stage 0
        (df['processing_type'] != 'Metal content')  # Exclude Metal content for processing comparisons
    ].copy()
    
    return filtered

def calculate_regional_vs_national_difference(df, scenario_base, constraint_level):
    """
    Calculate Regional - National production difference
    
    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        constraint_level: 'constrained' or 'unconstrained'
    """
    
    # Get correct scenario names with proper endings
    regional_scenario = get_scenario_name(scenario_base, 'region')  # _mid_max_
    national_scenario = get_scenario_name(scenario_base, 'country') # _mid_min_
    
    # Get constraint combinations  
    regional_constraint = f"region_{constraint_level}"
    national_constraint = f"country_{constraint_level}"
    
    print(f"Calculating difference for {scenario_base} ({constraint_level}):")
    print(f"  Regional: {regional_scenario} + {regional_constraint}")
    print(f"  National: {national_scenario} + {national_constraint}")
    
    # Filter data with proper processing stage filtering per type
    regional_data = filter_by_processing_type_stages(df, regional_scenario, regional_constraint)
    national_data = filter_by_processing_type_stages(df, national_scenario, national_constraint)
    
    print(f"  Regional data shape: {regional_data.shape}")
    print(f"  National data shape: {national_data.shape}")
    
    if regional_data.empty or national_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({constraint_level})")
        return pd.DataFrame()
    
    # Aggregate by country, mineral, and processing type
    regional_agg = regional_data.groupby(['iso3', 'reference_mineral', 'processing_type'])['production_tonnes'].sum().reset_index()
    national_agg = national_data.groupby(['iso3', 'reference_mineral', 'processing_type'])['production_tonnes'].sum().reset_index()
    
    # Merge and calculate difference
    merged = pd.merge(
        regional_agg, national_agg, 
        on=['iso3', 'reference_mineral', 'processing_type'], 
        suffixes=('_regional', '_national'),
        how='outer'
    ).fillna(0)
    
    # Calculate difference (Regional - National) in million tonnes
    merged['production_diff_mt'] = (merged['production_tonnes_regional'] - merged['production_tonnes_national']) / 1e6
    
    print(f"  Final difference data shape: {merged.shape}")
    return merged[['iso3', 'reference_mineral', 'processing_type', 'production_diff_mt']]

def calculate_constrained_vs_unconstrained_difference(df, scenario_base, policy_type):
    """
    Calculate Constrained - Unconstrained production difference
    
    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        policy_type: 'country' or 'region'
    """
    
    # Get correct scenario name with proper ending
    scenario = get_scenario_name(scenario_base, policy_type)
    
    # Get constraint combinations  
    constrained_constraint = f"{policy_type}_constrained"
    unconstrained_constraint = f"{policy_type}_unconstrained"
    
    print(f"Calculating constrained vs unconstrained difference for {scenario_base} ({policy_type}):")
    print(f"  Constrained: {scenario} + {constrained_constraint}")
    print(f"  Unconstrained: {scenario} + {unconstrained_constraint}")
    
    # Filter data with proper processing stage filtering per type
    constrained_data = filter_by_processing_type_stages(df, scenario, constrained_constraint)
    unconstrained_data = filter_by_processing_type_stages(df, scenario, unconstrained_constraint)
    
    print(f"  Constrained data shape: {constrained_data.shape}")
    print(f"  Unconstrained data shape: {unconstrained_data.shape}")
    
    if constrained_data.empty or unconstrained_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({policy_type})")
        return pd.DataFrame()
    
    # Aggregate by country, mineral, and processing type
    constrained_agg = constrained_data.groupby(['iso3', 'reference_mineral', 'processing_type'])['production_tonnes'].sum().reset_index()
    unconstrained_agg = unconstrained_data.groupby(['iso3', 'reference_mineral', 'processing_type'])['production_tonnes'].sum().reset_index()
    
    # Merge and calculate difference
    merged = pd.merge(
        constrained_agg, unconstrained_agg, 
        on=['iso3', 'reference_mineral', 'processing_type'], 
        suffixes=('_constrained', '_unconstrained'),
        how='outer'
    ).fillna(0)
    
    # Calculate difference (Constrained - Unconstrained) in million tonnes
    merged['production_diff_mt'] = (merged['production_tonnes_constrained'] - merged['production_tonnes_unconstrained']) / 1e6
    
    print(f"  Final difference data shape: {merged.shape}")
    return merged[['iso3', 'reference_mineral', 'processing_type', 'production_diff_mt']]

def create_horizontal_stacked_difference_plot(difference_data, title, output_path):
    """
    Create horizontal stacked bar plot showing production differences
    Uses processing type patterns with mineral colors
    """
    
    if difference_data.empty:
        print(f"No data for {title}")
        return
    
    # Get colors and processing types
    processing_colors = get_processing_type_colors()
    mineral_colors = get_mineral_colors()
    
    # Get unique countries and sort them
    countries = sorted(difference_data['iso3'].unique())
    processing_types = ["Beneficiation", "Early refining", "Precursor related product"]
    minerals = reference_minerals
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(14, max(8, len(countries) * 0.8)), dpi=300)
    
    # Prepare data structure for plotting
    y_pos = np.arange(len(countries))
    
    # For each country, we'll plot stacked bars
    left_positions = np.zeros(len(countries))
    
    # Plot each processing type separately
    for proc_type in processing_types:
        proc_data = difference_data[difference_data['processing_type'] == proc_type]
        
        if proc_data.empty:
            continue
            
        # Get base color for this processing type
        base_color = processing_colors.get(proc_type, '#666666')
        
        # For each mineral within this processing type
        for mineral in minerals:
            mineral_data = proc_data[proc_data['reference_mineral'] == mineral]
            
            if mineral_data.empty:
                continue
            
            # Create country-aligned data
            country_values = []
            for country in countries:
                country_mineral_data = mineral_data[mineral_data['iso3'] == country]
                if not country_mineral_data.empty:
                    country_values.append(country_mineral_data['production_diff_mt'].iloc[0])
                else:
                    country_values.append(0.0)
            
            # Use mineral color with processing type pattern
            mineral_color = mineral_colors.get(mineral, '#cccccc')
            
            # Apply different patterns for processing types
            if proc_type == "Beneficiation":
                # Solid colors
                hatches = None
                alpha = 0.8
            elif proc_type == "Early refining":
                # Diagonal hatching
                hatches = '///'
                alpha = 0.7
            else:  # Precursor related product
                # Dots
                hatches = '...'
                alpha = 0.6
            
            # Plot the bars
            bars = ax.barh(
                y_pos, country_values, left=left_positions,
                color=mineral_color, alpha=alpha, 
                hatch=hatches, linewidth=0.5, edgecolor='white',
                label=f"{mineral} ({proc_type})" if proc_type == "Beneficiation" else ""
            )
            
            # Update left positions for stacking
            left_positions += np.array(country_values)
    
    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(countries)
    ax.set_xlabel('Production Difference: Regional - National (Million Tonnes)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add zero reference line
    ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
    
    # Grid
    ax.grid(True, axis='x', linestyle='--', alpha=0.6)
    
    # Legend - simplified to avoid clutter
    # Create custom legend showing processing types
    from matplotlib.patches import Patch
    legend_elements = []
    for proc_type in processing_types:
        if proc_type == "Beneficiation":
            patch = Patch(facecolor=processing_colors.get(proc_type, '#666'), alpha=0.8, label=proc_type)
        elif proc_type == "Early refining":
            patch = Patch(facecolor=processing_colors.get(proc_type, '#666'), alpha=0.7, hatch='///', label=proc_type)
        else:
            patch = Patch(facecolor=processing_colors.get(proc_type, '#666'), alpha=0.6, hatch='...', label=proc_type)
        legend_elements.append(patch)
    
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
    
    # Tight layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {output_path}")
    plt.close()

def generate_constrained_vs_unconstrained_plots(df, output_dir):
    """
    Generate Constrained vs Unconstrained comparison plots for both Regional and National policies
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
    scenario_labels = ['BAU 2040', 'Early Refining 2040', 'Precursor Product 2040']
    policy_types = ['country', 'region']
    policy_labels = ['National Focus', 'Regional Integration']
    
    # Generate plots for both policy types
    for policy_idx, (policy_type, policy_label) in enumerate(zip(policy_types, policy_labels)):
        
        print(f"\n=== Generating CONSTRAINED vs UNCONSTRAINED plots for {policy_label} ===")
        
        # Create figure with subplots
        fig, axes = plt.subplots(1, 3, figsize=(20, 10), dpi=300)
        
        # First pass: collect data and determine global x-axis range
        all_diff_data = []
        for scenario in scenarios:
            diff_data = calculate_constrained_vs_unconstrained_difference(df, scenario, policy_type)
            all_diff_data.append(diff_data)
        
        # Calculate global x-axis range from all data
        all_values = []
        for diff_data in all_diff_data:
            if not diff_data.empty:
                country_totals = diff_data.groupby('iso3')['production_diff_mt'].sum()
                all_values.extend(country_totals.values)
        
        if all_values:
            x_min = min(all_values) * 1.1  # Add 10% padding
            x_max = max(all_values) * 1.1
            # Ensure we include zero
            x_min = min(x_min, 0)
            x_max = max(x_max, 0)
        else:
            x_min, x_max = -1, 1
        
        # Second pass: create plots with consistent x-axis
        for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            
            print(f"\nProcessing {scenario} ({policy_type})...")
            
            diff_data = all_diff_data[i]
            
            if diff_data.empty:
                print(f"No data for {scenario} ({policy_type})")
                continue
            
            # Create individual subplot
            ax = axes[i]
            
            # Get unique countries and sort them
            countries = sorted(diff_data['iso3'].unique())
            processing_types = ["Beneficiation", "Early refining", "Precursor related product"]
            
            # Prepare data for stacked plotting
            y_pos = np.arange(len(countries))
            
            # Colors
            processing_colors = get_processing_type_colors()
            
            # Plot stacked bars
            left_positions = np.zeros(len(countries))
            
            for proc_idx, proc_type in enumerate(processing_types):
                proc_data = diff_data[diff_data['processing_type'] == proc_type]
                
                if proc_data.empty:
                    continue
                
                # Aggregate by country for this processing type
                country_totals = proc_data.groupby('iso3')['production_diff_mt'].sum().reindex(countries, fill_value=0)
                
                # Apply patterns
                if proc_type == "Beneficiation":
                    hatches = None
                    alpha = 0.8
                elif proc_type == "Early refining":
                    hatches = '///'
                    alpha = 0.7
                else:  # Precursor
                    hatches = '...'
                    alpha = 0.6
                
                ax.barh(
                    y_pos, country_totals.values, left=left_positions,
                    color=processing_colors.get(proc_type, '#666666'),
                    alpha=alpha, hatch=hatches, linewidth=0.5, edgecolor='white',
                    label=proc_type if i == 0 else ""  # Only show legend on first subplot
                )
                
                left_positions += country_totals.values
            
            # Subplot formatting
            ax.set_yticks(y_pos)
            ax.set_yticklabels(countries, fontsize=10)
            ax.set_xlabel('Production Difference: Constrained - Unconstrained (Million Tonnes)', fontsize=11)
            ax.set_title(f'{label}', fontsize=12, fontweight='bold', pad=15)  # Removed policy_label, increased pad
            ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
            ax.grid(True, axis='x', linestyle='--', alpha=0.6)
            ax.set_xlim(x_min, x_max)  # Set consistent x-axis range
            
            # Legend only on first subplot
            if i == 0:
                ax.legend(loc='lower right', fontsize=9)
        
        # Overall figure formatting
        fig.suptitle(f'Constrained vs Unconstrained Production Differences - {policy_label}', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle
        
        # Save
        output_path = os.path.join(output_dir, f'constrained_vs_unconstrained_{policy_type}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\nSaved combined plot: {output_path}")
        plt.close()

def generate_regional_vs_national_plots(df, output_dir):
    """
    Generate the main Regional vs National comparison plots
    Updated to exclude BAU scenario (since Regional = National for BAU)
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Remove BAU since Regional vs National is always zero for BAU
    scenarios = ['early_refining_2040', 'precursor_2040']
    scenario_labels = ['Early Refining 2040', 'Precursor Product 2040']
    
    # Generate plots for both constrained and unconstrained
    for constraint_level in ['constrained', 'unconstrained']:
        
        print(f"\n=== Generating {constraint_level.upper()} Regional vs National plots ===")
        
        # Create figure with subplots (now 1x2 instead of 1x3)
        fig, axes = plt.subplots(1, 2, figsize=(16, 10), dpi=300)
        
        # First pass: collect data and determine global x-axis range
        all_diff_data = []
        for scenario in scenarios:
            diff_data = calculate_regional_vs_national_difference(df, scenario, constraint_level)
            all_diff_data.append(diff_data)
        
        # Calculate global x-axis range from all data
        all_values = []
        for diff_data in all_diff_data:
            if not diff_data.empty:
                country_totals = diff_data.groupby('iso3')['production_diff_mt'].sum()
                all_values.extend(country_totals.values)
        
        if all_values:
            x_min = min(all_values) * 1.1  # Add 10% padding
            x_max = max(all_values) * 1.1
            # Ensure we include zero
            x_min = min(x_min, 0)
            x_max = max(x_max, 0)
        else:
            x_min, x_max = -1, 1
        
        # Second pass: create plots with consistent x-axis
        for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            
            print(f"\nProcessing {scenario} ({constraint_level})...")
            
            diff_data = all_diff_data[i]
            
            if diff_data.empty:
                print(f"No data for {scenario} ({constraint_level})")
                continue
            
            # Create individual subplot
            ax = axes[i]
            
            # Get unique countries and sort them
            countries = sorted(diff_data['iso3'].unique())
            processing_types = ["Beneficiation", "Early refining", "Precursor related product"]
            
            # Prepare data for stacked plotting
            y_pos = np.arange(len(countries))
            
            # Colors
            processing_colors = get_processing_type_colors()
            
            # Plot stacked bars
            left_positions = np.zeros(len(countries))
            
            for proc_idx, proc_type in enumerate(processing_types):
                proc_data = diff_data[diff_data['processing_type'] == proc_type]
                
                if proc_data.empty:
                    continue
                
                # Aggregate by country for this processing type
                country_totals = proc_data.groupby('iso3')['production_diff_mt'].sum().reindex(countries, fill_value=0)
                
                # Apply patterns
                if proc_type == "Beneficiation":
                    hatches = None
                    alpha = 0.8
                elif proc_type == "Early refining":
                    hatches = '///'
                    alpha = 0.7
                else:  # Precursor
                    hatches = '...'
                    alpha = 0.6
                
                ax.barh(
                    y_pos, country_totals.values, left=left_positions,
                    color=processing_colors.get(proc_type, '#666666'),
                    alpha=alpha, hatch=hatches, linewidth=0.5, edgecolor='white',
                    label=proc_type if i == 0 else ""  # Only show legend on first subplot
                )
                
                left_positions += country_totals.values
            
            # Subplot formatting
            ax.set_yticks(y_pos)
            ax.set_yticklabels(countries, fontsize=10)
            ax.set_xlabel('Production Difference: Regional - National (Million Tonnes)', fontsize=11)
            ax.set_title(f'{label}', fontsize=12, fontweight='bold', pad=15)  # Removed constraint_level, increased pad
            ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
            ax.grid(True, axis='x', linestyle='--', alpha=0.6)
            ax.set_xlim(x_min, x_max)  # Set consistent x-axis range
            
            # Legend only on first subplot
            if i == 0:
                ax.legend(loc='lower right', fontsize=9)
        
        # Overall figure formatting
        fig.suptitle(f'Regional vs National Production Differences - {constraint_level.title()} Scenarios', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle
        
        # Save
        output_path = os.path.join(output_dir, f'regional_vs_national_{constraint_level}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\nSaved combined plot: {output_path}")
        plt.close()

def generate_mineral_breakdown_plots(df, output_dir):
    """
    Generate Processing Type Subplots with Mineral Colors
    3x3 grid: 3 scenarios × 3 processing types, showing mineral breakdown within each
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
    scenario_labels = ['BAU 2040', 'Early Refining 2040', 'Precursor Product 2040']
    all_processing_types = ["Beneficiation", "Early refining", "Precursor related product"]
    
    # Generate for both comparison types
    comparison_configs = [
        {
            'name': 'constrained_vs_unconstrained_country_mineral_breakdown',
            'title': 'Constrained vs Unconstrained (National Focus) - Mineral Breakdown',
            'calc_func': calculate_constrained_vs_unconstrained_difference,
            'policy_param': 'country',
            'scenarios': scenarios,  # Include all scenarios for constrained vs unconstrained
            'processing_types': all_processing_types  # Include Beneficiation (will show differences when data is fixed)
        },
        {
            'name': 'constrained_vs_unconstrained_region_mineral_breakdown', 
            'title': 'Constrained vs Unconstrained (Regional Integration) - Mineral Breakdown',
            'calc_func': calculate_constrained_vs_unconstrained_difference,
            'policy_param': 'region',
            'scenarios': scenarios,  # Include all scenarios
            'processing_types': all_processing_types  # Include Beneficiation (will show differences when data is fixed)
        },
        {
            'name': 'regional_vs_national_constrained_mineral_breakdown',
            'title': 'Regional vs National (Constrained) - Mineral Breakdown',
            'calc_func': calculate_regional_vs_national_difference,
            'policy_param': 'constrained',
            'scenarios': ['early_refining_2040', 'precursor_2040'],  # Exclude BAU
            'processing_types': ["Early refining", "Precursor related product"]  # Exclude Beneficiation for cleaner visuals
        },
        {
            'name': 'regional_vs_national_unconstrained_mineral_breakdown',
            'title': 'Regional vs National (Unconstrained) - Mineral Breakdown', 
            'calc_func': calculate_regional_vs_national_difference,
            'policy_param': 'unconstrained',
            'scenarios': ['early_refining_2040', 'precursor_2040'],  # Exclude BAU
            'processing_types': ["Early refining", "Precursor related product"]  # Exclude Beneficiation for cleaner visuals
        }
    ]
    
    for config in comparison_configs:
        print(f"\n=== Generating {config['title']} ===")
        
        # Determine grid size based on number of scenarios and processing types
        n_scenarios = len(config['scenarios'])
        n_processing_types = len(config['processing_types'])
        processing_types = config['processing_types']
        
        if n_scenarios == 3:
            figsize = (7 * n_processing_types, 15)  # Adjust width based on number of processing types
        else:  # 2 scenarios
            figsize = (7 * n_processing_types, 12)  # Adjust width based on number of processing types
            
        # Create figure with n_processing_types×n_scenarios grid
        fig, axes = plt.subplots(n_scenarios, n_processing_types, figsize=figsize, dpi=300)
        
        # Ensure axes is always 2D array
        if n_scenarios == 1 and n_processing_types == 1:
            axes = axes.reshape(1, 1)
        elif n_scenarios == 1:
            axes = axes.reshape(1, -1)
        elif n_processing_types == 1:
            axes = axes.reshape(-1, 1)
        elif len(axes.shape) == 1:
            axes = axes.reshape(-1, 1)
        
        # Collect all data for consistent axis scaling
        all_stacked_values = []
        all_data = {}
        
        for s_idx, scenario in enumerate(config['scenarios']):
            scenario_data = {}
            for p_idx, proc_type in enumerate(processing_types):
                
                # Calculate differences
                if config['calc_func'] == calculate_constrained_vs_unconstrained_difference:
                    diff_data = config['calc_func'](df, scenario, config['policy_param'])
                else:  # regional vs national
                    diff_data = config['calc_func'](df, scenario, config['policy_param'])
                
                # Filter for this processing type
                proc_data = diff_data[diff_data['processing_type'] == proc_type] if not diff_data.empty else pd.DataFrame()
                scenario_data[proc_type] = proc_data
                
                # Collect STACKED values for axis scaling (not individual mineral values)
                if not proc_data.empty:
                    # Calculate stacked totals by country (same logic as in plotting)
                    countries = sorted(proc_data['iso3'].unique())
                    for country in countries:
                        country_data = proc_data[proc_data['iso3'] == country]
                        country_stacked_total = country_data['production_diff_mt'].sum()
                        all_stacked_values.append(country_stacked_total)
            
            all_data[scenario] = scenario_data
        
        # Calculate global axis range based on stacked totals
        if all_stacked_values:
            x_min = min(all_stacked_values) * 1.1
            x_max = max(all_stacked_values) * 1.1
            x_min = min(x_min, 0)
            x_max = max(x_max, 0)
        else:
            x_min, x_max = -1, 1
        
        # Create subplots
        mineral_colors = get_mineral_colors()
        
        for s_idx, scenario in enumerate(config['scenarios']):
            scenario_label = scenario_labels[scenarios.index(scenario)] if scenario in scenarios else scenario
            
            for p_idx, proc_type in enumerate(processing_types):
                ax = axes[s_idx, p_idx]
                proc_data = all_data[scenario][proc_type]
                
                if proc_data.empty:
                    ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes, 
                           ha='center', va='center', fontsize=12, color='gray')
                    ax.set_xlim(x_min, x_max)
                    continue
                
                # Get unique countries and minerals
                countries = sorted(proc_data['iso3'].unique())
                minerals = sorted(proc_data['reference_mineral'].unique())
                
                # Prepare data for plotting
                y_pos = np.arange(len(countries))
                # Track positive and negative positions separately
                left_pos_positions = np.zeros(len(countries))  # For positive values
                left_neg_positions = np.zeros(len(countries))  # For negative values
                
                # Plot each mineral
                for mineral in minerals:
                    mineral_data = proc_data[proc_data['reference_mineral'] == mineral]
                    
                    if mineral_data.empty:
                        continue
                    
                    # Create country-aligned values
                    country_values = []
                    for country in countries:
                        country_mineral = mineral_data[mineral_data['iso3'] == country]
                        if not country_mineral.empty:
                            country_values.append(country_mineral['production_diff_mt'].iloc[0])
                        else:
                            country_values.append(0.0)
                    
                    # Separate positive and negative values for proper stacking
                    country_values_array = np.array(country_values)
                    
                    # Determine left positions based on sign
                    left_positions = np.where(
                        country_values_array >= 0,
                        left_pos_positions,
                        left_neg_positions
                    )
                    
                    # Plot bars
                    bars = ax.barh(
                        y_pos, country_values, left=left_positions,
                        color=mineral_colors.get(mineral, '#cccccc'),
                        alpha=0.8, linewidth=0.5, edgecolor='white',
                        label=mineral if s_idx == 0 and p_idx == 0 else ""
                    )
                    
                    # Update positions for next mineral
                    # Positive values stack to the right
                    left_pos_positions = np.where(
                        country_values_array > 0,
                        left_pos_positions + country_values_array,
                        left_pos_positions
                    )
                    # Negative values stack to the left
                    left_neg_positions = np.where(
                        country_values_array < 0,
                        left_neg_positions + country_values_array,
                        left_neg_positions
                    )
                
                # Formatting
                ax.set_yticks(y_pos)
                ax.set_yticklabels(countries, fontsize=9)
                ax.set_xlim(x_min, x_max)
                ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
                ax.grid(True, axis='x', linestyle='--', alpha=0.6)
                
                # Titles
                if s_idx == 0:
                    ax.set_title(proc_type, fontsize=12, fontweight='bold', pad=10)
                if p_idx == 0:
                    ax.set_ylabel(scenario_label, fontsize=12, fontweight='bold')
                if s_idx == len(config['scenarios']) - 1:
                    ax.set_xlabel('Production Difference (Million Tonnes)', fontsize=10)
                
                # Legend on first subplot only
                if s_idx == 0 and p_idx == 0:
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        # Overall formatting
        fig.suptitle(config['title'], fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save
        output_path = os.path.join(output_dir, f"{config['name']}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

def generate_beneficiation_only_plots(df, output_dir):
    """
    Generate constrained vs unconstrained plots for Beneficiation only with mineral breakdown
    Uses 1x3 layout (one row, three columns) for space efficiency
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
    scenario_labels = ['BAU 2040', 'Early Refining 2040', 'Precursor Product 2040']
    
    # Two policy types to generate
    policy_configs = [
        {
            'policy': 'country',
            'title': 'Constrained vs Unconstrained Production Differences - National Focus (Beneficiation Only)',
            'filename': 'constrained_vs_unconstrained_country_beneficiation_only.png'
        },
        {
            'policy': 'region',
            'title': 'Constrained vs Unconstrained Production Differences - Regional Integration (Beneficiation Only)',
            'filename': 'constrained_vs_unconstrained_region_beneficiation_only.png'
        }
    ]
    
    for policy_config in policy_configs:
        print(f"\n=== Generating Beneficiation-only plot for {policy_config['policy']} policy ===")
        
        # Create figure with 1x3 layout
        fig, axes = plt.subplots(1, 3, figsize=(18, 8), dpi=300)
        
        # Collect all data for consistent axis scaling
        all_data = []
        all_stacked_values = []
        
        # First pass: collect data and calculate axis range
        for scenario in scenarios:
            diff_data = calculate_constrained_vs_unconstrained_difference(df, scenario, policy_config['policy'])
            
            # Filter for Beneficiation only
            benef_data = diff_data[diff_data['processing_type'] == 'Beneficiation'] if not diff_data.empty else pd.DataFrame()
            all_data.append(benef_data)
            
            # Calculate stacked totals for axis scaling
            if not benef_data.empty:
                countries = sorted(benef_data['iso3'].unique())
                for country in countries:
                    country_data = benef_data[benef_data['iso3'] == country]
                    total = country_data['production_diff_mt'].sum()
                    all_stacked_values.append(total)
        
        # Calculate consistent x-axis range
        if all_stacked_values:
            x_min = min(all_stacked_values) * 1.15
            x_max = max(all_stacked_values) * 1.15
            x_min = min(x_min, 0)
            x_max = max(x_max, 0)
        else:
            x_min, x_max = -1, 1
        
        # Get mineral colors
        mineral_colors = get_mineral_colors()
        
        # Second pass: create plots
        for idx, (scenario, label, benef_data) in enumerate(zip(scenarios, scenario_labels, all_data)):
            ax = axes[idx]
            
            if benef_data.empty:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(label, fontsize=12, fontweight='bold')
                continue
            
            # Get unique countries and minerals
            countries = sorted(benef_data['iso3'].unique())
            minerals = reference_minerals
            
            # Prepare data for plotting
            y_pos = np.arange(len(countries))
            # Track positive and negative positions separately
            left_pos_positions = np.zeros(len(countries))  # For positive values
            left_neg_positions = np.zeros(len(countries))  # For negative values
            
            # Plot each mineral
            for mineral in minerals:
                mineral_data = benef_data[benef_data['reference_mineral'] == mineral]
                
                if mineral_data.empty:
                    continue
                
                # Create country-aligned data
                country_values = []
                for country in countries:
                    country_mineral_data = mineral_data[mineral_data['iso3'] == country]
                    if not country_mineral_data.empty:
                        country_values.append(country_mineral_data['production_diff_mt'].iloc[0])
                    else:
                        country_values.append(0.0)
                
                # Separate positive and negative values for proper stacking
                country_values_array = np.array(country_values)
                
                # Determine left positions based on sign
                left_positions = np.where(
                    country_values_array >= 0,
                    left_pos_positions,
                    left_neg_positions
                )
                
                # Plot with mineral color
                ax.barh(
                    y_pos, country_values, left=left_positions,
                    color=mineral_colors.get(mineral, '#cccccc'),
                    alpha=0.8, linewidth=0.5, edgecolor='white',
                    label=mineral if idx == 0 else ""  # Only show legend on first subplot
                )
                
                # Update positions for next mineral
                # Positive values stack to the right
                left_pos_positions = np.where(
                    country_values_array > 0,
                    left_pos_positions + country_values_array,
                    left_pos_positions
                )
                # Negative values stack to the left  
                left_neg_positions = np.where(
                    country_values_array < 0,
                    left_neg_positions + country_values_array,
                    left_neg_positions
                )
            
            # Formatting
            ax.set_yticks(y_pos)
            ax.set_yticklabels(countries, fontsize=9)
            ax.set_xlim(x_min, x_max)
            ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
            ax.grid(True, axis='x', linestyle='--', alpha=0.6)
            ax.set_title(label, fontsize=12, fontweight='bold', pad=10)
            ax.set_xlabel('Production Difference: Constrained - Unconstrained (Million Tonnes)', fontsize=10)
            
            # Legend only on first subplot
            if idx == 0:
                ax.legend(bbox_to_anchor=(0, -0.15), loc='upper left', ncol=3, fontsize=8)
        
        # Overall title
        fig.suptitle(policy_config['title'], fontsize=14, fontweight='bold', y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save
        output_path = os.path.join(output_dir, policy_config['filename'])
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

def generate_essential_difference_plots(output_dir):
    """
    Main function to generate essential production difference plots
    """
    
    print("Loading production data from all_data.xlsx...")
    
    # Load data
    data_path = '/home/karlac/critical_minerals_Africa/transport-outputs/results/all_data.xlsx'
    df = pd.read_excel(data_path)
    
    print(f"Loaded data shape: {df.shape}")
    print(f"Available scenarios: {sorted(df['scenario'].unique())}")
    print(f"Available constraints: {sorted(df['constraint'].unique())}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate the main plots
    print("Generating Regional vs National plots (excluding BAU)...")
    generate_regional_vs_national_plots(df, output_dir)
    
    print("Generating Constrained vs Unconstrained plots (all scenarios)...")
    generate_constrained_vs_unconstrained_plots(df, output_dir)
    
    print("Generating Mineral Breakdown plots (Processing Type Subplots)...")
    generate_mineral_breakdown_plots(df, output_dir)
    
    print("Generating Beneficiation-only Constrained vs Unconstrained plots...")
    generate_beneficiation_only_plots(df, output_dir)
    
    print(f"\nAll plots saved to: {output_dir}")

if __name__ == "__main__":
    output_dir = '/home/karlac/critical_minerals_Africa/transport-outputs/figures/automated_plots/production_differences'
    generate_essential_difference_plots(output_dir)