"""
Complete Executive Dashboard with Value Addition and Proper Production Units
Includes pivot-style summary table format
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
from data_tables import create_summary_mid_demand_unconstrained, calc_value_added

def get_mid_scenarios_symmetric(df_country):
    """Get mid-scenarios with symmetric filtering logic"""
    mid_scenarios = df_country[
        (df_country['scenario'].str.contains('mid_min|mid_max', na=False)) |
        (df_country['scenario'] == '2022_baseline')
    ].copy()
    
    print(f"Symmetric mid-scenario filtering: {len(df_country)} → {len(mid_scenarios)} records")
    return mid_scenarios

def calculate_value_addition(df_analysis):
    """Calculate value addition using the original logic"""
    df_va = df_analysis[df_analysis["processing_stage"] > 0].copy()
    
    if df_va.empty:
        return pd.DataFrame()
    
    # Apply value addition calculation by scenario/constraint/mineral groups
    df_va = df_va.groupby(['scenario', 'constraint', 'reference_mineral']).apply(calc_value_added).reset_index(drop=True)
    df_va['value_added_musd'] = df_va['value_added'] / 1e6  # Convert to millions USD
    
    return df_va

def create_pivot_summary_table(df_analysis):
    """Create pivot-style summary table with indicators as rows"""
    
    # Add goal type and constraint type columns
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    df_analysis['constraint_type'] = df_analysis['constraint'].str.split('_').str[0]
    
    # Define constraint combinations for comparison
    constraint_combos = [
        ('country_unconstrained', 'region_unconstrained', 'Unconstrained'),
        ('country_constrained', 'region_constrained', 'Constrained')
    ]
    
    summary_rows = []
    
    for goal in ['bau', 'early_refining', 'precursor']:
        goal_data = df_analysis[df_analysis['goal_type'] == goal].copy()
        
        if goal_data.empty:
            continue
            
        for country_constraint, region_constraint, constraint_label in constraint_combos:
            country_data = goal_data[goal_data['constraint'] == country_constraint]
            region_data = goal_data[goal_data['constraint'] == region_constraint]
            
            if country_data.empty or region_data.empty:
                continue
            
            # Calculate metrics
            metrics = {}
            
            # Production - Metal Content (Stage 0 only)
            prod_country_metal = country_data[country_data['processing_stage'] == 0]['production_tonnes'].sum() / 1e6  # Mt
            prod_region_metal = region_data[region_data['processing_stage'] == 0]['production_tonnes'].sum() / 1e6   # Mt
            
            # Production - Products (Stage >0 only) 
            prod_country_products = country_data[country_data['processing_stage'] > 0]['production_tonnes'].sum() / 1e6  # Mt
            prod_region_products = region_data[region_data['processing_stage'] > 0]['production_tonnes'].sum() / 1e6   # Mt
            
            # Revenue
            rev_country = country_data['revenue_usd'].sum() / 1e9  # Billion USD
            rev_region = region_data['revenue_usd'].sum() / 1e9    # Billion USD
            
            # Water usage
            water_country = country_data['water_usage_m3'].sum() / 1e6  # Million m³
            water_region = region_data['water_usage_m3'].sum() / 1e6    # Million m³
            
            # CO2 emissions
            co2_country = country_data['transport_total_tonsCO2eq'].sum() / 1e3  # kt
            co2_region = region_data['transport_total_tonsCO2eq'].sum() / 1e3    # kt
            
            # Value addition
            df_va = calculate_value_addition(goal_data)
            if not df_va.empty:
                va_country = df_va[df_va['constraint'] == country_constraint]['value_added_musd'].sum()
                va_region = df_va[df_va['constraint'] == region_constraint]['value_added_musd'].sum()
            else:
                va_country = va_region = 0
            
            # Helper function for percentage change
            def pct_change(country_val, region_val):
                if country_val == 0:
                    return 0 if region_val == 0 else float('inf')
                return ((region_val / country_val) * 100) - 100
            
            # Build metrics dictionary
            metrics_data = [
                ('Production_Metal_Content_Mt', prod_country_metal, prod_region_metal),
                ('Production_Products_Mt', prod_country_products, prod_region_products), 
                ('Revenue_Billion_USD', rev_country, rev_region),
                ('Water_Usage_Million_m3', water_country, water_region),
                ('CO2_Emissions_kt', co2_country, co2_region),
                ('Value_Addition_Million_USD', va_country, va_region)
            ]
            
            for metric_name, country_val, region_val in metrics_data:
                summary_rows.append({
                    'Goal': goal.replace('_', ' ').title(),
                    'Constraint_Scenario': constraint_label,
                    'Indicator': metric_name,
                    'National_Policy': round(country_val, 2),
                    'Regional_Policy': round(region_val, 2),
                    'Percentage_Change': round(pct_change(country_val, region_val), 1)
                })
    
    return pd.DataFrame(summary_rows)

def create_zambia_executive_dashboard_complete(df_country, output_dir):
    """Create complete executive dashboard with value addition and production clarity"""
    
    print("=== CREATING COMPLETE ZAMBIA EXECUTIVE DASHBOARD ===")
    
    # Use symmetric mid-scenario filtering
    df_analysis = get_mid_scenarios_symmetric(df_country)
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    df_analysis['constraint_type'] = df_analysis['constraint'].str.split('_').str[0]
    
    # Calculate value addition
    df_va = calculate_value_addition(df_analysis)
    
    # Create 2x4 subplot grid
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle('Zambia Critical Minerals Executive Dashboard - Complete Analysis', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Color schemes
    goal_colors = {
        'baseline': '#2E86AB',
        'bau': '#A23B72', 
        'early_refining': '#F18F01',
        'precursor': '#C73E1D'
    }
    constraint_colors = {'country': '#1f77b4', 'region': '#ff7f0e'}
    
    # 1. Production - Metal Content (Stage 0 only)
    ax1 = axes[0, 0]
    stage0_data = df_analysis[df_analysis['processing_stage'] == 0]
    goal_prod_metal = stage0_data.groupby('goal_type')['production_tonnes'].sum() / 1e6  # Mt
    goal_prod_metal_filtered = goal_prod_metal[goal_prod_metal > 0]
    
    if not goal_prod_metal_filtered.empty:
        bars1 = ax1.bar(goal_prod_metal_filtered.index, goal_prod_metal_filtered.values,
                       color=[goal_colors.get(goal, '#888888') for goal in goal_prod_metal_filtered.index])
        ax1.set_title('Metal Content Production (Mt)\n[Stage 0 Only]', fontweight='bold')
        ax1.set_ylabel('Production (Mt)')
        ax1.tick_params(axis='x', rotation=45)
        for bar, val in zip(bars1, goal_prod_metal_filtered.values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)
    else:
        ax1.text(0.5, 0.5, 'No stage 0 data', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Metal Content Production (Mt)\n[Stage 0 Only]', fontweight='bold')
    
    # 2. Production - Products (Stage >0 only)
    ax2 = axes[0, 1] 
    stage_pos_data = df_analysis[df_analysis['processing_stage'] > 0]
    goal_prod_products = stage_pos_data.groupby('goal_type')['production_tonnes'].sum() / 1e6  # Mt
    goal_prod_products_filtered = goal_prod_products[goal_prod_products > 0]
    
    if not goal_prod_products_filtered.empty:
        bars2 = ax2.bar(goal_prod_products_filtered.index, goal_prod_products_filtered.values,
                       color=[goal_colors.get(goal, '#888888') for goal in goal_prod_products_filtered.index])
        ax2.set_title('Products Production (Mt)\n[Stage >0 Only]', fontweight='bold')
        ax2.set_ylabel('Production (Mt)')
        ax2.tick_params(axis='x', rotation=45)
        for bar, val in zip(bars2, goal_prod_products_filtered.values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'No products data', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Products Production (Mt)\n[Stage >0 Only]', fontweight='bold')
    
    # 3. Value Addition (Million USD)
    ax3 = axes[0, 2]
    if not df_va.empty:
        goal_va = df_va.groupby('goal_type')['value_added_musd'].sum()
        goal_va_filtered = goal_va[goal_va > 0]
        
        if not goal_va_filtered.empty:
            bars3 = ax3.bar(goal_va_filtered.index, goal_va_filtered.values,
                           color=[goal_colors.get(goal, '#888888') for goal in goal_va_filtered.index])
            ax3.set_title('Value Addition (M USD)', fontweight='bold')
            ax3.set_ylabel('Value Added (M USD)')
            ax3.tick_params(axis='x', rotation=45)
            for bar, val in zip(bars3, goal_va_filtered.values):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                        f'${val:.0f}M', ha='center', va='bottom', fontsize=9)
        else:
            ax3.text(0.5, 0.5, 'No value addition', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Value Addition (M USD)', fontweight='bold')
    else:
        ax3.text(0.5, 0.5, 'No value addition data', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Value Addition (M USD)', fontweight='bold')
    
    # 4. Water Usage (Million m³)
    ax4 = axes[0, 3]
    goal_water = df_analysis.groupby('goal_type')['water_usage_m3'].sum() / 1e6
    goal_water_filtered = goal_water[goal_water > 0]
    
    if not goal_water_filtered.empty:
        bars4 = ax4.bar(goal_water_filtered.index, goal_water_filtered.values,
                       color=[goal_colors.get(goal, '#888888') for goal in goal_water_filtered.index])
        ax4.set_title('Water Usage (M m³)', fontweight='bold')
        ax4.set_ylabel('Water Usage (M m³)')
        ax4.tick_params(axis='x', rotation=45)
        for bar, val in zip(bars4, goal_water_filtered.values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    f'{val:.0f}M', ha='center', va='bottom', fontsize=9)
    else:
        ax4.text(0.5, 0.5, 'No water data', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Water Usage (M m³)', fontweight='bold')
    
    # Bottom row: Policy comparisons (Country vs Region)
    
    # 5. Revenue Policy Comparison
    ax5 = axes[1, 0]
    policy_rev = df_analysis.groupby(['goal_type', 'constraint_type'])['revenue_usd'].sum() / 1e9
    if not policy_rev.empty:
        policy_rev_pivot = policy_rev.unstack(level=1, fill_value=0)
        if not policy_rev_pivot.empty:
            policy_rev_pivot.plot(kind='bar', ax=ax5, color=[constraint_colors.get(col, '#888888') 
                                                           for col in policy_rev_pivot.columns])
            ax5.set_title('Revenue: Country vs Region ($B)', fontweight='bold')
            ax5.set_ylabel('Revenue ($B)')
            ax5.tick_params(axis='x', rotation=45)
            ax5.legend(title='Policy Focus')
    
    # 6. Value Addition Policy Comparison
    ax6 = axes[1, 1]
    if not df_va.empty:
        policy_va = df_va.groupby(['goal_type', 'constraint_type'])['value_added_musd'].sum()
        if not policy_va.empty:
            policy_va_pivot = policy_va.unstack(level=1, fill_value=0)
            if not policy_va_pivot.empty:
                policy_va_pivot.plot(kind='bar', ax=ax6, color=[constraint_colors.get(col, '#888888') 
                                                              for col in policy_va_pivot.columns])
                ax6.set_title('Value Addition: Country vs Region', fontweight='bold')
                ax6.set_ylabel('Value Added (M USD)')
                ax6.tick_params(axis='x', rotation=45)
                ax6.legend(title='Policy Focus')
    
    if ax6.get_legend() is None:  # If no plot was made
        ax6.text(0.5, 0.5, 'No value addition policy data', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Value Addition: Country vs Region', fontweight='bold')
    
    # 7. Water Policy Comparison
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
    
    # 8. CO2 Policy Comparison
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
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save dashboard
    dashboard_path = os.path.join(output_dir, 'zambia_executive_dashboard_complete.png')
    fig.savefig(dashboard_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Complete dashboard saved: {dashboard_path}")
    return dashboard_path

def test_complete_dashboard():
    """Test the complete dashboard with all improvements"""
    
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
    output_dir = os.path.join(output_data_path, 'country_reports', 'test_executive_dashboard_ZMB_complete')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create complete dashboard
    dashboard_path = create_zambia_executive_dashboard_complete(df_country, output_dir)
    
    # Create pivot-style summary table
    print("\n=== CREATING PIVOT-STYLE SUMMARY TABLE ===")
    mid_data = get_mid_scenarios_symmetric(df_country)
    pivot_summary = create_pivot_summary_table(mid_data)
    
    if not pivot_summary.empty:
        summary_path = os.path.join(output_dir, 'zambia_pivot_summary_table.csv')
        pivot_summary.to_csv(summary_path, index=False)
        print(f"✓ Pivot summary table saved: {summary_path}")
        print(f"Table shape: {pivot_summary.shape}")
        
        # Display sample of pivot table
        print("\nSample of pivot summary table:")
        print(pivot_summary.head(10).to_string(index=False))
    else:
        print("✗ Pivot summary table is empty")
    
    return output_dir

if __name__ == "__main__":
    test_complete_dashboard()