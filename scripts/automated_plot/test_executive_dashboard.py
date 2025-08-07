"""
Test Executive Dashboard for Uganda (UGA)
Comprehensive single-country dashboard to replace 20+ individual plots
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import seaborn as sns

# Add paths for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from plot_config import (
    reference_minerals,
    reference_mineral_colors,
    reference_mineral_colormap,
    reference_mineral_namemap,
    mineral_processing_stages,
    goal_based_processing,
    get_target_stage_for_goal,
    get_goal_from_scenario
)

from data_tables import create_summary_mid_demand_unconstrained

# Set consistent styling
plt.style.use('default')
sns.set_palette("husl")

def calculate_value_addition(df_country, goal_type):
    """Calculate value addition for a goal using target stages"""
    if goal_type == 'baseline':
        # For baseline, show all processing compared to stage 0
        stage_0_data = df_country[df_country['processing_stage'] == 0.0]
        processed_data = df_country[df_country['processing_stage'] > 0.0]
        
        stage_0_revenue = stage_0_data['revenue_usd'].sum()
        processed_revenue = processed_data['revenue_usd'].sum()
        
        return processed_revenue - stage_0_revenue
    
    # For goal-specific scenarios, use target stages
    focus_type = goal_based_processing[goal_type]['focus_type']
    if focus_type == 'comprehensive':
        # Baseline case - all stages
        stage_0_revenue = df_country[df_country['processing_stage'] == 0.0]['revenue_usd'].sum()
        all_revenue = df_country['revenue_usd'].sum()
        return all_revenue - stage_0_revenue
    
    # Calculate based on target stages for specific goals
    value_addition = 0
    stage_0_revenue = 0
    target_revenue = 0
    
    for mineral in df_country['reference_mineral'].unique():
        if mineral in mineral_processing_stages:
            target_stage = get_target_stage_for_goal(mineral, focus_type)
            if target_stage is not None:
                mineral_data = df_country[df_country['reference_mineral'] == mineral]
                
                stage_0_rev = mineral_data[mineral_data['processing_stage'] == 0.0]['revenue_usd'].sum()
                target_rev = mineral_data[mineral_data['processing_stage'] == target_stage]['revenue_usd'].sum()
                
                stage_0_revenue += stage_0_rev
                target_revenue += target_rev
    
    return target_revenue - stage_0_revenue

def create_goal_comparison_subplot(ax, df_country, metric, title, unit, scale_factor=1e6):
    """Create goal comparison subplot using target stages"""
    goal_data = {}
    
    # Filter to mid-demand scenarios for clean comparison
    mid_scenarios = df_country[
        (df_country['scenario'].str.contains('mid_min') & df_country['constraint'].str.contains('country')) |
        (df_country['scenario'].str.contains('mid_max') & df_country['constraint'].str.contains('region')) |
        (df_country['scenario'] == '2022_baseline')
    ].copy()
    
    mid_scenarios['goal_type'] = mid_scenarios['scenario'].apply(get_goal_from_scenario)
    
    goals = ['baseline', 'bau', 'early_refining', 'precursor']
    goal_labels = ['2022 Baseline', 'BAU 2040', 'Early Refining 2040', 'Precursor 2040']
    colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']
    
    values = []
    labels = []
    bar_colors = []
    
    for i, goal in enumerate(goals):
        goal_subset = mid_scenarios[mid_scenarios['goal_type'] == goal]
        
        if goal_subset.empty:
            continue
            
        if metric == 'value_addition':
            # Calculate value addition using our new function
            value = calculate_value_addition(goal_subset, goal) / scale_factor
        else:
            # Standard metrics
            value = goal_subset[metric].sum() / scale_factor
            
        values.append(value)
        labels.append(goal_labels[i])
        bar_colors.append(colors[i])
    
    if values:
        bars = ax.bar(labels, values, color=bar_colors, alpha=0.8)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(unit, fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}', ha='center', va='bottom', fontsize=10)
    else:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=14, fontweight='bold')

def create_policy_comparison_subplot(ax, df_country, metric, title, unit, scale_factor=1e6):
    """Create policy comparison subplot (National vs Regional)"""
    # Filter to mid-demand 2040 scenarios
    policy_scenarios = df_country[
        (df_country['scenario'].str.contains('mid_min') & df_country['constraint'].str.contains('country')) |
        (df_country['scenario'].str.contains('mid_max') & df_country['constraint'].str.contains('region'))
    ].copy()
    
    policy_scenarios['goal_type'] = policy_scenarios['scenario'].apply(get_goal_from_scenario)
    policy_scenarios['policy_type'] = policy_scenarios['constraint'].apply(
        lambda x: 'National Focus' if 'country' in x else 'Regional Integration'
    )
    
    # Group by goal and policy
    grouped = policy_scenarios.groupby(['goal_type', 'policy_type'])[metric].sum().reset_index()
    grouped[metric] = grouped[metric] / scale_factor
    
    if not grouped.empty:
        # Pivot for grouped bar chart
        pivot = grouped.pivot(index='goal_type', columns='policy_type', values=metric).fillna(0)
        
        goal_order = ['bau', 'early_refining', 'precursor']
        goal_labels = ['BAU', 'Early Refining', 'Precursor']
        
        # Filter to available goals
        available_goals = [goal for goal in goal_order if goal in pivot.index]
        available_labels = [goal_labels[goal_order.index(goal)] for goal in available_goals]
        
        if available_goals:
            pivot_filtered = pivot.loc[available_goals]
            pivot_filtered.index = available_labels
            
            pivot_filtered.plot(kind='bar', ax=ax, color=['#ff7f0e', '#2ca02c'], alpha=0.8)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_ylabel(unit, fontsize=12)
            ax.set_xlabel('')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Policy Approach', loc='upper left')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                    transform=ax.transAxes, fontsize=14)
            ax.set_title(title, fontsize=14, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=14, fontweight='bold')

def create_constraint_comparison_subplot(ax, df_country, metric, title, unit, scale_factor=1e6):
    """Create environmental constraint comparison"""
    # Filter to mid-demand scenarios
    constraint_scenarios = df_country[
        df_country['scenario'].str.contains('mid') & 
        df_country['year'] == 2040
    ].copy()
    
    if constraint_scenarios.empty:
        ax.text(0.5, 0.5, 'No 2040 data available', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=14, fontweight='bold')
        return
    
    constraint_scenarios['goal_type'] = constraint_scenarios['scenario'].apply(get_goal_from_scenario)
    constraint_scenarios['constraint_type'] = constraint_scenarios['constraint'].apply(
        lambda x: 'Environmentally Constrained' if 'constrained' in x and 'unconstrained' not in x else 'Unconstrained'
    )
    
    # Group by goal and constraint
    grouped = constraint_scenarios.groupby(['goal_type', 'constraint_type'])[metric].sum().reset_index()
    grouped[metric] = grouped[metric] / scale_factor
    
    if not grouped.empty:
        # Pivot for grouped bar chart
        pivot = grouped.pivot(index='goal_type', columns='constraint_type', values=metric).fillna(0)
        
        goal_order = ['bau', 'early_refining', 'precursor']
        goal_labels = ['BAU', 'Early Refining', 'Precursor']
        
        available_goals = [goal for goal in goal_order if goal in pivot.index]
        available_labels = [goal_labels[goal_order.index(goal)] for goal in available_goals]
        
        if available_goals:
            pivot_filtered = pivot.loc[available_goals]
            pivot_filtered.index = available_labels
            
            pivot_filtered.plot(kind='bar', ax=ax, color=['#d62728', '#1f77b4'], alpha=0.8)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_ylabel(unit, fontsize=12)
            ax.set_xlabel('')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Environmental Approach', loc='upper left')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                    transform=ax.transAxes, fontsize=14)
            ax.set_title(title, fontsize=14, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=14, fontweight='bold')

def create_mineral_breakdown_subplot(ax, df_country, metric, title, unit, scale_factor=1e6):
    """Create mineral breakdown for latest scenario"""
    # Use best available scenario (mid-demand, unconstrained)
    mineral_data = df_country[
        (df_country['scenario'].str.contains('precursor_2040_mid_min')) |
        (df_country['scenario'].str.contains('early_refining_2040_mid_min')) |
        (df_country['scenario'].str.contains('bau_2040_mid_min'))
    ].copy()
    
    if mineral_data.empty:
        # Fallback to any available data
        mineral_data = df_country[df_country['year'] == 2040].copy()
    
    if not mineral_data.empty:
        # Group by mineral and sum
        grouped = mineral_data.groupby('reference_mineral')[metric].sum().reset_index()
        grouped[metric] = grouped[metric] / scale_factor
        grouped = grouped.sort_values(metric, ascending=False)
        
        if not grouped.empty and grouped[metric].sum() > 0:
            # Get colors for minerals
            colors = [reference_mineral_colormap.get(mineral, '#999999') for mineral in grouped['reference_mineral']]
            
            bars = ax.bar(grouped['reference_mineral'], grouped[metric], color=colors, alpha=0.8)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_ylabel(unit, fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar, value in zip(bars, grouped[metric]):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}', ha='center', va='bottom', fontsize=10)
        else:
            ax.text(0.5, 0.5, 'No production data', ha='center', va='center', 
                    transform=ax.transAxes, fontsize=14)
            ax.set_title(title, fontsize=14, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=14, fontweight='bold')

def create_zambia_executive_dashboard(df_country, output_dir):
    """
    Create comprehensive executive dashboard for Zambia
    Replaces 20+ individual plots with single comparative view
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create 2x4 subplot layout
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle('Zambia Critical Minerals Executive Dashboard', fontsize=20, fontweight='bold', y=0.95)
    
    # Row 1: Goal Comparisons (Target stages)
    create_goal_comparison_subplot(
        axes[0,0], df_country, 'production_tonnes', 
        '2040 Goals: Production', 'Production (kt)', 1e3
    )
    
    create_goal_comparison_subplot(
        axes[0,1], df_country, 'revenue_usd',
        '2040 Goals: Revenue', 'Revenue (Million USD)', 1e6
    )
    
    create_goal_comparison_subplot(
        axes[0,2], df_country, 'value_addition',
        '2040 Goals: Value Addition', 'Value Added (Million USD)', 1e6
    )
    
    # Environmental comparison - combine CO2 sources
    df_env = df_country.copy()
    df_env['total_co2_tonnes'] = df_env['transport_total_tonsCO2eq'] + df_env['energy_tonsCO2eq']
    create_goal_comparison_subplot(
        axes[0,3], df_env, 'total_co2_tonnes',
        '2040 Goals: CO2 Emissions', 'CO2 Emissions (kt)', 1e3
    )
    
    # Row 2: Policy & Analysis Comparisons
    create_policy_comparison_subplot(
        axes[1,0], df_country, 'production_tonnes',
        'Policy Impact: Production', 'Production (kt)', 1e3
    )
    
    create_policy_comparison_subplot(
        axes[1,1], df_country, 'revenue_usd',
        'Policy Impact: Revenue', 'Revenue (Million USD)', 1e6
    )
    
    create_constraint_comparison_subplot(
        axes[1,2], df_country, 'water_usage_m3',
        'Environmental Constraints: Water', 'Water Usage (Million m³)', 1e6
    )
    
    create_mineral_breakdown_subplot(
        axes[1,3], df_country, 'production_tonnes',
        'Production by Mineral', 'Production (kt)', 1e3
    )
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    
    # Save dashboard
    dashboard_path = os.path.join(output_dir, 'zambia_executive_dashboard.png')
    fig.savefig(dashboard_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return dashboard_path

def create_summary_table_display(df_country, output_dir):
    """Create and save executive summary table"""
    summary_df = create_summary_mid_demand_unconstrained(df_country)
    
    if not summary_df.empty:
        # Save as CSV for easy viewing
        summary_path = os.path.join(output_dir, 'zambia_executive_summary_table.csv')
        summary_df.to_csv(summary_path, index=False)
        
        # Create a simple visualization of the summary
        if len(summary_df) > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot key metrics comparison
            metrics = ['production_Mt_country', 'production_Mt_region', 'revenue_MUSD_country', 'revenue_MUSD_region']
            available_metrics = [m for m in metrics if m in summary_df.columns]
            
            if available_metrics:
                summary_plot = summary_df[['goal_type'] + available_metrics].set_index('goal_type')
                summary_plot.plot(kind='bar', ax=ax, alpha=0.8)
                ax.set_title('Executive Summary: Key Metrics Comparison', fontsize=16, fontweight='bold')
                ax.set_ylabel('Values', fontsize=12)
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Metrics', bbox_to_anchor=(1.05, 1), loc='upper left')
                
                plt.tight_layout()
                summary_viz_path = os.path.join(output_dir, 'zambia_summary_table_visualization.png')
                fig.savefig(summary_viz_path, dpi=300, bbox_inches='tight')
                plt.close(fig)
                
                return summary_path, summary_viz_path
    
    return None, None

def test_zambia_executive_dashboard():
    """Test the executive dashboard with Zambia data"""
    print("=== ZAMBIA EXECUTIVE DASHBOARD TEST ===")
    
    # Load configuration for correct output paths
    import json
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config.json")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    df_country = df[df['iso3'] == 'ZMB'].copy()
    
    print(f"Loaded {len(df_country)} records for Zambia")
    
    # Create output directory in correct location
    output_dir = os.path.join(output_data_path, 'country_reports', 'test_executive_dashboard_ZMB')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate executive dashboard
    print("Creating comprehensive executive dashboard...")
    dashboard_path = create_zambia_executive_dashboard(df_country, output_dir)
    print(f"✓ Executive dashboard saved: {dashboard_path}")
    
    # Generate summary table
    print("Creating executive summary table...")
    summary_table_path, summary_viz_path = create_summary_table_display(df_country, output_dir)
    if summary_table_path:
        print(f"✓ Summary table saved: {summary_table_path}")
        if summary_viz_path:
            print(f"✓ Summary visualization saved: {summary_viz_path}")
    else:
        print("⚠ No summary table data available")
    
    # Generate comparison report
    print("\n=== COMPARISON WITH CURRENT APPROACH ===")
    print("Current approach would generate:")
    print("- 20+ individual plots per country")
    print("- 8+ separate charts for production analysis")
    print("- 4+ charts each for revenue, emissions, water usage")
    print("- Multiple constraint and scenario combinations")
    print("- Total: ~25-30 individual visualization files")
    
    print("\nNew executive dashboard approach generates:")
    print("- 1 comprehensive dashboard (8 subplots)")
    print("- 1 executive summary table")
    print("- 1 summary visualization")
    print("- Total: 3 files with complete analytical coverage")
    
    print(f"\n✓ Test completed successfully!")
    print(f"Results saved in: {output_dir}")
    
    return output_dir

if __name__ == "__main__":
    test_zambia_executive_dashboard()