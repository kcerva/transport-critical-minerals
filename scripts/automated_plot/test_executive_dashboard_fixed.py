"""
Fixed Executive Dashboard for Critical Minerals Analysis
Focuses on mid-scenarios with symmetric filtering logic
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from plot_config import get_goal_from_scenario, get_target_stage_for_goal
from data_tables import create_summary_mid_demand_unconstrained

def get_mid_scenarios_symmetric(df_country):
    """
    Get mid-scenarios with symmetric filtering logic for proper policy comparisons.
    Uses both mid_min and mid_max scenarios with all constraint types.
    """
    # Symmetric filtering: all mid scenarios + baseline
    mid_scenarios = df_country[
        (df_country['scenario'].str.contains('mid_min|mid_max', na=False)) |
        (df_country['scenario'] == '2022_baseline')
    ].copy()
    
    print(f"Symmetric mid-scenario filtering: {len(df_country)} → {len(mid_scenarios)} records")
    print(f"Water data in mid scenarios: {mid_scenarios['water_usage_m3'].sum():.2e} m³")
    
    return mid_scenarios

def create_zambia_executive_dashboard_fixed(df_country, output_dir):
    """Create fixed executive dashboard with proper mid-scenario filtering"""
    
    print("=== CREATING FIXED ZAMBIA EXECUTIVE DASHBOARD ===")
    
    # Use symmetric mid-scenario filtering
    df_analysis = get_mid_scenarios_symmetric(df_country)
    
    # Add goal type column
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    
    # Create 2x4 subplot grid
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle('Zambia Critical Minerals Executive Dashboard - Mid Scenarios Focus', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Color scheme
    goal_colors = {
        'baseline': '#2E86AB',
        'bau': '#A23B72', 
        'early_refining': '#F18F01',
        'precursor': '#C73E1D'
    }
    
    # 1. Goal Comparisons - Production (Mt)
    ax1 = axes[0, 0]
    goal_production = df_analysis.groupby('goal_type')['production_tonnes'].sum() / 1e6  # Convert to Mt
    goal_production_filtered = goal_production[goal_production > 0]  # Remove zeros
    
    if not goal_production_filtered.empty:
        bars1 = ax1.bar(goal_production_filtered.index, goal_production_filtered.values, 
                       color=[goal_colors.get(goal, '#888888') for goal in goal_production_filtered.index])
        ax1.set_title('Production by Goal (Mt)', fontweight='bold')
        ax1.set_ylabel('Production (Mt)')
        ax1.tick_params(axis='x', rotation=45)
        # Add value labels
        for bar, val in zip(bars1, goal_production_filtered.values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)
    else:
        ax1.text(0.5, 0.5, 'No production data', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Production by Goal (Mt)', fontweight='bold')
    
    # 2. Goal Comparisons - Revenue (Billion USD)
    ax2 = axes[0, 1]
    goal_revenue = df_analysis.groupby('goal_type')['revenue_usd'].sum() / 1e9  # Convert to billions
    goal_revenue_filtered = goal_revenue[goal_revenue > 0]  # Remove zeros
    
    if not goal_revenue_filtered.empty:
        bars2 = ax2.bar(goal_revenue_filtered.index, goal_revenue_filtered.values,
                       color=[goal_colors.get(goal, '#888888') for goal in goal_revenue_filtered.index])
        ax2.set_title('Revenue by Goal ($B)', fontweight='bold')
        ax2.set_ylabel('Revenue ($B)')
        ax2.tick_params(axis='x', rotation=45)
        # Add value labels
        for bar, val in zip(bars2, goal_revenue_filtered.values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                    f'${val:.1f}B', ha='center', va='bottom', fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'No revenue data', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Revenue by Goal ($B)', fontweight='bold')
    
    # 3. Goal Comparisons - Water Usage (Million m³) - FIXED
    ax3 = axes[0, 2]
    goal_water = df_analysis.groupby('goal_type')['water_usage_m3'].sum() / 1e6  # Convert to million m³
    goal_water_filtered = goal_water[goal_water > 0]  # Remove zeros
    
    if not goal_water_filtered.empty:
        bars3 = ax3.bar(goal_water_filtered.index, goal_water_filtered.values,
                       color=[goal_colors.get(goal, '#888888') for goal in goal_water_filtered.index])
        ax3.set_title('Water Usage by Goal (M m³)', fontweight='bold')
        ax3.set_ylabel('Water Usage (M m³)')
        ax3.tick_params(axis='x', rotation=45)
        # Add value labels
        for bar, val in zip(bars3, goal_water_filtered.values):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    f'{val:.0f}M', ha='center', va='bottom', fontsize=9)
    else:
        ax3.text(0.5, 0.5, 'No water data', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Water Usage by Goal (M m³)', fontweight='bold')
    
    # 4. Goal Comparisons - CO2 Emissions (kt)
    ax4 = axes[0, 3]
    # Use transport CO2 emissions as main indicator
    goal_co2 = df_analysis.groupby('goal_type')['transport_total_tonsCO2eq'].sum() / 1e3  # Convert to kt
    goal_co2_filtered = goal_co2[goal_co2 > 0]  # Remove zeros
    
    if not goal_co2_filtered.empty:
        bars4 = ax4.bar(goal_co2_filtered.index, goal_co2_filtered.values,
                       color=[goal_colors.get(goal, '#888888') for goal in goal_co2_filtered.index])
        ax4.set_title('CO2 Emissions by Goal (kt)', fontweight='bold')
        ax4.set_ylabel('CO2 Emissions (kt)')
        ax4.tick_params(axis='x', rotation=45)
        # Add value labels
        for bar, val in zip(bars4, goal_co2_filtered.values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    f'{val:.0f}', ha='center', va='bottom', fontsize=9)
    else:
        ax4.text(0.5, 0.5, 'No emissions data', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('CO2 Emissions by Goal (kt)', fontweight='bold')
    
    # Policy Analysis Row (Country vs Region comparisons)
    constraint_colors = {'country': '#1f77b4', 'region': '#ff7f0e'}
    
    # 5. Policy Comparison - Production
    ax5 = axes[1, 0]
    # Group by constraint type (country vs region)
    df_analysis['constraint_type'] = df_analysis['constraint'].str.split('_').str[0]
    policy_prod = df_analysis.groupby(['goal_type', 'constraint_type'])['production_tonnes'].sum() / 1e6
    
    if not policy_prod.empty:
        policy_prod_pivot = policy_prod.unstack(level=1, fill_value=0)
        if not policy_prod_pivot.empty:
            policy_prod_pivot.plot(kind='bar', ax=ax5, color=[constraint_colors.get(col, '#888888') 
                                                            for col in policy_prod_pivot.columns])
            ax5.set_title('Production: Country vs Region (Mt)', fontweight='bold')
            ax5.set_ylabel('Production (Mt)')
            ax5.tick_params(axis='x', rotation=45)
            ax5.legend(title='Policy Focus')
    else:
        ax5.text(0.5, 0.5, 'No policy data', ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title('Production: Country vs Region (Mt)', fontweight='bold')
    
    # 6. Policy Comparison - Revenue
    ax6 = axes[1, 1]
    policy_rev = df_analysis.groupby(['goal_type', 'constraint_type'])['revenue_usd'].sum() / 1e9
    
    if not policy_rev.empty:
        policy_rev_pivot = policy_rev.unstack(level=1, fill_value=0)
        if not policy_rev_pivot.empty:
            policy_rev_pivot.plot(kind='bar', ax=ax6, color=[constraint_colors.get(col, '#888888') 
                                                           for col in policy_rev_pivot.columns])
            ax6.set_title('Revenue: Country vs Region ($B)', fontweight='bold')
            ax6.set_ylabel('Revenue ($B)')
            ax6.tick_params(axis='x', rotation=45)
            ax6.legend(title='Policy Focus')
    else:
        ax6.text(0.5, 0.5, 'No policy data', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Revenue: Country vs Region ($B)', fontweight='bold')
    
    # 7. Policy Comparison - Water Usage - FIXED
    ax7 = axes[1, 2]
    policy_water = df_analysis.groupby(['goal_type', 'constraint_type'])['water_usage_m3'].sum() / 1e6
    
    if not policy_water.empty:
        policy_water_pivot = policy_water.unstack(level=1, fill_value=0)
        if not policy_water_pivot.empty:
            policy_water_pivot.plot(kind='bar', ax=ax7, color=[constraint_colors.get(col, '#888888') 
                                                             for col in policy_water_pivot.columns])
            ax7.set_title('Water: Country vs Region (M m³)', fontweight='bold')
            ax7.set_ylabel('Water Usage (M m³)')
            ax7.tick_params(axis='x', rotation=45)
            ax7.legend(title='Policy Focus')
    else:
        ax7.text(0.5, 0.5, 'No water policy data', ha='center', va='center', transform=ax7.transAxes)
        ax7.set_title('Water: Country vs Region (M m³)', fontweight='bold')
    
    # 8. Policy Comparison - CO2 Emissions
    ax8 = axes[1, 3]
    policy_co2 = df_analysis.groupby(['goal_type', 'constraint_type'])['transport_total_tonsCO2eq'].sum() / 1e3
    
    if not policy_co2.empty:
        policy_co2_pivot = policy_co2.unstack(level=1, fill_value=0)
        if not policy_co2_pivot.empty:
            policy_co2_pivot.plot(kind='bar', ax=ax8, color=[constraint_colors.get(col, '#888888') 
                                                           for col in policy_co2_pivot.columns])
            ax8.set_title('CO2: Country vs Region (kt)', fontweight='bold')
            ax8.set_ylabel('CO2 Emissions (kt)')
            ax8.tick_params(axis='x', rotation=45)
            ax8.legend(title='Policy Focus')
    else:
        ax8.text(0.5, 0.5, 'No emissions policy data', ha='center', va='center', transform=ax8.transAxes)
        ax8.set_title('CO2: Country vs Region (kt)', fontweight='bold')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save dashboard
    dashboard_path = os.path.join(output_dir, 'zambia_executive_dashboard_fixed.png')
    fig.savefig(dashboard_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Fixed dashboard saved: {dashboard_path}")
    return dashboard_path

def test_fixed_dashboard():
    """Test the fixed dashboard approach"""
    
    # Load configuration
    import json
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load Zambia data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    df_country = df[df['iso3'] == 'ZMB'].copy()
    
    # Create output directory
    output_dir = os.path.join(output_data_path, 'country_reports', 'test_executive_dashboard_ZMB_fixed')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create fixed dashboard
    dashboard_path = create_zambia_executive_dashboard_fixed(df_country, output_dir)
    
    # Test summary table (should now work with regex fix)
    print("\n=== TESTING FIXED SUMMARY TABLE ===")
    try:
        summary_df = create_summary_mid_demand_unconstrained(df_country)
        if not summary_df.empty:
            print(f"✓ Summary table generated successfully: {summary_df.shape[0]} rows")
            
            # Save fixed summary table
            summary_path = os.path.join(output_dir, 'zambia_executive_summary_table_fixed.csv')
            summary_df.to_csv(summary_path, index=False)
            print(f"✓ Summary table saved: {summary_path}")
        else:
            print("✗ Summary table is still empty")
    except Exception as e:
        print(f"✗ Summary table error: {e}")
    
    # Check water data specifically
    print("\n=== WATER DATA CHECK ===")
    mid_data = get_mid_scenarios_symmetric(df_country)
    mid_data['goal_type'] = mid_data['scenario'].apply(get_goal_from_scenario)
    water_by_goal = mid_data.groupby('goal_type')['water_usage_m3'].sum()
    print("Water usage by goal in fixed filtering:")
    for goal, water in water_by_goal.items():
        print(f"  {goal}: {water:.2e} m³ ({water/1e6:.1f} million m³)")
    
    return output_dir

if __name__ == "__main__":
    test_fixed_dashboard()