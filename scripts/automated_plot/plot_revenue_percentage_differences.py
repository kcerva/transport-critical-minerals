"""
Revenue Percentage Change Visualization
Shows percentage changes in revenue between different policy scenarios
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

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

def calculate_revenue_pct_change_regional_vs_national(df, scenario_base, constraint_level):
    """
    Calculate percentage change in revenue: (Regional - National) / National × 100
    
    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        constraint_level: 'constrained' or 'unconstrained'
    """
    
    # Get correct scenario names
    regional_scenario = get_scenario_name(scenario_base, 'region')
    national_scenario = get_scenario_name(scenario_base, 'country')
    
    # Get constraint combinations
    regional_constraint = f"region_{constraint_level}"
    national_constraint = f"country_{constraint_level}"
    
    print(f"Calculating revenue % change for {scenario_base} ({constraint_level}):")
    print(f"  Regional: {regional_scenario} + {regional_constraint}")
    print(f"  National: {national_scenario} + {national_constraint}")
    
    # Filter and aggregate revenue data
    regional_data = df[(df['scenario'] == regional_scenario) & (df['constraint'] == regional_constraint)]
    national_data = df[(df['scenario'] == national_scenario) & (df['constraint'] == national_constraint)]
    
    if regional_data.empty or national_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({constraint_level})")
        return pd.DataFrame()
    
    # Aggregate revenue by country (convert from USD to Million USD)
    regional_revenue = regional_data.groupby('iso3')['revenue_usd'].sum().reset_index()
    regional_revenue['revenue_usd'] = regional_revenue['revenue_usd'] / 1e6  # Convert to MUSD
    regional_revenue.columns = ['iso3', 'revenue_regional']
    
    national_revenue = national_data.groupby('iso3')['revenue_usd'].sum().reset_index()
    national_revenue['revenue_usd'] = national_revenue['revenue_usd'] / 1e6  # Convert to MUSD
    national_revenue.columns = ['iso3', 'revenue_national']
    
    # Merge and calculate percentage change
    merged = pd.merge(regional_revenue, national_revenue, on='iso3', how='outer').fillna(0)
    
    # Calculate percentage change, handling division by zero
    merged['revenue_pct_change'] = merged.apply(
        lambda row: ((row['revenue_regional'] - row['revenue_national']) / row['revenue_national'] * 100) 
        if row['revenue_national'] != 0 else 0, axis=1
    )
    
    print(f"  Countries with data: {len(merged)}")
    print(f"  Avg % change: {merged['revenue_pct_change'].mean():.1f}%")
    
    return merged[['iso3', 'revenue_pct_change']]

def calculate_revenue_pct_change_constrained_vs_unconstrained(df, scenario_base, policy_type):
    """
    Calculate percentage change in revenue: (Constrained - Unconstrained) / Unconstrained × 100
    
    Args:
        df: Raw data from all_data.xlsx
        scenario_base: 'bau_2040', 'early_refining_2040', 'precursor_2040'
        policy_type: 'country' or 'region'
    """
    
    # Get correct scenario name
    scenario = get_scenario_name(scenario_base, policy_type)
    
    # Get constraint combinations
    constrained_constraint = f"{policy_type}_constrained"
    unconstrained_constraint = f"{policy_type}_unconstrained"
    
    print(f"Calculating revenue % change for {scenario_base} ({policy_type}):")
    print(f"  Constrained: {scenario} + {constrained_constraint}")
    print(f"  Unconstrained: {scenario} + {unconstrained_constraint}")
    
    # Filter and aggregate revenue data
    constrained_data = df[(df['scenario'] == scenario) & (df['constraint'] == constrained_constraint)]
    unconstrained_data = df[(df['scenario'] == scenario) & (df['constraint'] == unconstrained_constraint)]
    
    if constrained_data.empty or unconstrained_data.empty:
        print(f"  WARNING: Empty data for {scenario_base} ({policy_type})")
        return pd.DataFrame()
    
    # Aggregate revenue by country (convert from USD to Million USD)
    constrained_revenue = constrained_data.groupby('iso3')['revenue_usd'].sum().reset_index()
    constrained_revenue['revenue_usd'] = constrained_revenue['revenue_usd'] / 1e6  # Convert to MUSD
    constrained_revenue.columns = ['iso3', 'revenue_constrained']
    
    unconstrained_revenue = unconstrained_data.groupby('iso3')['revenue_usd'].sum().reset_index()
    unconstrained_revenue['revenue_usd'] = unconstrained_revenue['revenue_usd'] / 1e6  # Convert to MUSD
    unconstrained_revenue.columns = ['iso3', 'revenue_unconstrained']
    
    # Merge and calculate percentage change
    merged = pd.merge(constrained_revenue, unconstrained_revenue, on='iso3', how='outer').fillna(0)
    
    # Calculate percentage change, handling division by zero
    merged['revenue_pct_change'] = merged.apply(
        lambda row: ((row['revenue_constrained'] - row['revenue_unconstrained']) / row['revenue_unconstrained'] * 100) 
        if row['revenue_unconstrained'] != 0 else 0, axis=1
    )
    
    print(f"  Countries with data: {len(merged)}")
    print(f"  Avg % change: {merged['revenue_pct_change'].mean():.1f}%")
    
    return merged[['iso3', 'revenue_pct_change']]

def create_revenue_pct_subplot(ax, data, scenario_label, x_min, x_max):
    """
    Create a single subplot showing revenue percentage changes
    """
    if data.empty:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(scenario_label, fontsize=12, fontweight='bold')
        return
    
    # Sort countries by revenue change for better visualization
    data_sorted = data.sort_values('revenue_pct_change')
    countries = data_sorted['iso3'].values
    values = data_sorted['revenue_pct_change'].values
    
    # Create color array based on positive/negative values
    colors = ['#2E7D32' if v > 0 else '#C62828' for v in values]  # Green for gains, Red for losses
    
    # Create horizontal bar chart
    y_pos = np.arange(len(countries))
    bars = ax.barh(y_pos, values, color=colors, alpha=0.7, edgecolor='white', linewidth=0.5)
    
    # Add value labels for significant changes
    for i, (country, value) in enumerate(zip(countries, values)):
        if abs(value) > 5:  # Only label if change is more than 5%
            # Adjust position to avoid overlap with axis
            if value > 0:
                x_pos = value + 2  # Add fixed offset for positive values
                ha = 'left'
            else:
                x_pos = value - 2  # Add fixed offset for negative values
                ha = 'right'
            
            ax.text(x_pos, i, f'{value:.0f}%', va='center', ha=ha, 
                   fontsize=8, color='darkgreen' if value > 0 else 'darkred')
    
    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(countries, fontsize=9)
    ax.set_xlim(x_min, x_max)
    ax.axvline(0, color='black', linewidth=1.0, alpha=0.8)
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)
    ax.set_title(scenario_label, fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Revenue Change (%)', fontsize=10)

def generate_revenue_pct_regional_vs_national(df, output_dir):
    """
    Generate revenue percentage change plots for Regional vs National comparison
    """
    print("\n=== Generating Revenue % Change: Regional vs National ===")
    
    # Exclude BAU as differences are always zero (no regional processing difference in BAU)
    scenarios = ['early_refining_2040', 'precursor_2040']
    scenario_labels = ['Early Processing 2040', 'Product Manufacturing 2040']
    
    for constraint_level in ['constrained', 'unconstrained']:
        print(f"\nProcessing {constraint_level} scenarios...")
        
        # Create figure with 1x2 layout (no BAU)
        fig, axes = plt.subplots(1, 2, figsize=(14, 8), dpi=300)
        
        # Collect data and determine consistent x-axis range
        all_data = []
        all_values = []
        
        for scenario in scenarios:
            pct_data = calculate_revenue_pct_change_regional_vs_national(df, scenario, constraint_level)
            all_data.append(pct_data)
            if not pct_data.empty:
                all_values.extend(pct_data['revenue_pct_change'].values)
        
        # Calculate x-axis range
        if all_values:
            # Add extra padding for negative values to accommodate text labels
            min_val = min(all_values)
            max_val = max(all_values)
            
            # For negative values, add 30% padding to accommodate text
            if min_val < 0:
                x_min = min_val * 1.3
            else:
                x_min = min_val * 1.2
                
            # Standard padding for positive values
            x_max = max_val * 1.2
            
            # Ensure we have at least ±10% range
            x_min = min(x_min, -10)
            x_max = max(x_max, 10)
        else:
            x_min, x_max = -50, 50
        
        # Create subplots
        for idx, (scenario_label, pct_data) in enumerate(zip(scenario_labels, all_data)):
            create_revenue_pct_subplot(axes[idx], pct_data, scenario_label, x_min, x_max)
        
        # Overall title
        fig.suptitle(f'Revenue Change: Regional vs National - {constraint_level.title()} Scenarios', 
                    fontsize=14, fontweight='bold', y=0.98)
        
        # Add explanatory text
        fig.text(0.5, 0.02, 'Positive values indicate higher revenue under Regional Integration; Negative values indicate higher revenue under National Focus', 
                ha='center', fontsize=10, style='italic')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        
        # Save
        output_path = os.path.join(output_dir, f'revenue_pct_change_regional_vs_national_{constraint_level}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

def generate_revenue_pct_constrained_vs_unconstrained(df, output_dir):
    """
    Generate revenue percentage change plots for Constrained vs Unconstrained comparison
    """
    print("\n=== Generating Revenue % Change: Constrained vs Unconstrained ===")
    
    scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
    scenario_labels = ['BAU 2040', 'Early Processing 2040', 'Product Manufacturing 2040']
    
    for policy_type in ['country', 'region']:
        policy_label = 'National Focus' if policy_type == 'country' else 'Regional Integration'
        print(f"\nProcessing {policy_label} policy...")
        
        # Create figure with 1x3 layout
        fig, axes = plt.subplots(1, 3, figsize=(18, 8), dpi=300)
        
        # Collect data and determine consistent x-axis range
        all_data = []
        all_values = []
        
        for scenario in scenarios:
            pct_data = calculate_revenue_pct_change_constrained_vs_unconstrained(df, scenario, policy_type)
            all_data.append(pct_data)
            if not pct_data.empty:
                all_values.extend(pct_data['revenue_pct_change'].values)
        
        # Calculate x-axis range (expect mostly negative values)
        if all_values:
            x_min = min(all_values) * 1.2
            x_max = max(all_values) * 1.2
            # Ensure we see the full negative range
            x_min = min(x_min, -10)
            x_max = max(x_max, 10)
        else:
            x_min, x_max = -50, 50
        
        # Create subplots
        for idx, (scenario_label, pct_data) in enumerate(zip(scenario_labels, all_data)):
            create_revenue_pct_subplot(axes[idx], pct_data, scenario_label, x_min, x_max)
        
        # Overall title
        fig.suptitle(f'Revenue Change: Constrained vs Unconstrained - {policy_label}', 
                    fontsize=14, fontweight='bold', y=0.98)
        
        # Add explanatory text
        fig.text(0.5, 0.02, 'Negative values indicate revenue loss due to environmental constraints; Positive values indicate revenue gain under constraints', 
                ha='center', fontsize=10, style='italic')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        
        # Save
        output_path = os.path.join(output_dir, f'revenue_pct_change_constrained_vs_unconstrained_{policy_type}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

def main():
    """
    Main function to generate revenue percentage change plots
    """
    print("=" * 60)
    print("REVENUE PERCENTAGE CHANGE ANALYSIS")
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
    
    # Check if revenue column exists
    if 'revenue_usd' not in df.columns:
        print("ERROR: 'revenue_usd' column not found in data!")
        return
    
    # Create output directory
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'revenue_percentage_changes')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Generate plots
    generate_revenue_pct_regional_vs_national(df, output_dir)
    generate_revenue_pct_constrained_vs_unconstrained(df, output_dir)
    
    print("\n" + "=" * 60)
    print("All revenue percentage change plots completed!")
    print(f"Plots saved to: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()