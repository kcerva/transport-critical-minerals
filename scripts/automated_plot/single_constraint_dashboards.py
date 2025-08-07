"""
Single Constraint Executive Dashboards - Part 1 (Dashboards 1-2)
Each dashboard shows one specific constraint scenario
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

from plot_config import get_goal_from_scenario, get_target_stage_for_goal, mineral_processing_stages
from data_tables import calc_value_added
from policy_comparison_dashboard import create_policy_comparison_dashboard

def get_mid_scenarios_symmetric(df_country):
    """Get mid-scenarios with symmetric filtering logic"""
    mid_scenarios = df_country[
        (df_country['scenario'].str.contains('mid_min|mid_max', na=False)) |
        (df_country['scenario'] == '2022_baseline')
    ].copy()
    
    return mid_scenarios

def calculate_value_addition(df_analysis):
    """Calculate value addition using the original logic"""
    df_va = df_analysis[df_analysis["processing_stage"] > 0].copy()
    
    if df_va.empty:
        return pd.DataFrame()
    
    df_va = df_va.groupby(['scenario', 'constraint', 'reference_mineral'], group_keys=False).apply(calc_value_added).reset_index(drop=True)
    df_va['value_added_musd'] = df_va['value_added'] / 1e6
    
    return df_va

def get_goal_stage_production(df_analysis, goal_type):
    """Get production for target stages only for a specific goal"""
    
    if goal_type == 'baseline':
        return df_analysis[df_analysis['processing_stage'] == 0]['production_tonnes'].sum()
    
    goal_to_processing = {
        'bau': 'Beneficiation',
        'early_refining': 'Early refining', 
        'precursor': 'Precursor related product'
    }
    
    processing_type = goal_to_processing.get(goal_type)
    if not processing_type:
        return 0
    
    total_production = 0
    
    for mineral in df_analysis['reference_mineral'].unique():
        mineral_data = df_analysis[df_analysis['reference_mineral'] == mineral]
        
        if mineral in mineral_processing_stages:
            target_stages = mineral_processing_stages[mineral]['target_stages']
            target_stage = target_stages.get(processing_type)
            
            if target_stage:
                stage_production = mineral_data[mineral_data['processing_stage'] == target_stage]['production_tonnes'].sum()
                total_production += stage_production
    
    return total_production


def generate_constraint_insights(df_filtered, constraint):
    """Generate insights for a specific constraint scenario"""
    
    constraint_names = {
        'country_unconstrained': 'Country Unconstrained',
        'country_constrained': 'Country Constrained', 
        'region_unconstrained': 'Region Unconstrained',
        'region_constrained': 'Region Constrained'
    }
    
    constraint_name = constraint_names[constraint]
    insights = [f"## {constraint_name} Policy Dashboard Insights\n"]
    
    # Calculate key metrics by goal
    goal_metrics = {}
    for goal in df_filtered['goal_type'].unique():
        goal_data = df_filtered[df_filtered['goal_type'] == goal]
        if not goal_data.empty:
            goal_metrics[goal] = {
                'metal_production': goal_data[goal_data['processing_stage'] == 0]['production_tonnes'].sum() / 1e6,
                'products_production': goal_data[goal_data['processing_stage'] > 0]['production_tonnes'].sum() / 1e6,
                'revenue': goal_data['revenue_usd'].sum() / 1e9,
                'co2_emissions': (goal_data['transport_total_tonsCO2eq'].sum() + goal_data['energy_tonsCO2eq'].sum()) / 1e3
            }
    
    if not goal_metrics:
        insights.append("- No data available for analysis")
        return "\n".join(insights)
    
    # Identify highest performing scenarios
    if goal_metrics:
        # Revenue leader
        revenue_leader = max(goal_metrics.keys(), key=lambda x: goal_metrics[x]['revenue'])
        revenue_value = goal_metrics[revenue_leader]['revenue']
        insights.append(f"- **Revenue Leader**: {revenue_leader.replace('_', ' ').title()} generates ${revenue_value:.1f}B in revenue")
        
        # Production leader
        prod_leader = max(goal_metrics.keys(), key=lambda x: goal_metrics[x]['metal_production'])
        prod_value = goal_metrics[prod_leader]['metal_production']
        insights.append(f"- **Production Leader**: {prod_leader.replace('_', ' ').title()} produces {prod_value:.2f}Mt of metal content")
        
        # Environmental comparison
        if len(goal_metrics) > 1:
            co2_values = [(goal, metrics['co2_emissions']) for goal, metrics in goal_metrics.items() if metrics['co2_emissions'] > 0]
            if co2_values:
                lowest_co2 = min(co2_values, key=lambda x: x[1])
                highest_co2 = max(co2_values, key=lambda x: x[1])
                insights.append(f"- **Environmental Impact**: {lowest_co2[0].replace('_', ' ').title()} has lowest CO2 emissions ({lowest_co2[1]:.1f}kt), {highest_co2[0].replace('_', ' ').title()} has highest ({highest_co2[1]:.1f}kt)")
        
        # Processing insights
        products_scenarios = [(goal, metrics['products_production']) for goal, metrics in goal_metrics.items() if metrics['products_production'] > 0]
        if products_scenarios:
            top_processing = max(products_scenarios, key=lambda x: x[1])
            insights.append(f"- **Value Addition**: {top_processing[0].replace('_', ' ').title()} leads in processed products ({top_processing[1]:.2f}Mt)")
    
    return "\n".join(insights)

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
            
            # Transport volumes
            transport_country = country_data['transport_total_tonkm'].sum() / 1e6  # Million ton-km
            transport_region = region_data['transport_total_tonkm'].sum() / 1e6    # Million ton-km
            
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
                ('Transport_Volume_Million_tonkm', transport_country, transport_region),
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

def create_single_constraint_dashboard(df_country, constraint, output_dir, country_name="Country"):
    """Create single constraint dashboard (2x4 layout)"""
    
    constraint_names = {
        'country_unconstrained': 'Country Unconstrained Policy',
        'country_constrained': 'Country Constrained Policy', 
        'region_unconstrained': 'Region Unconstrained Policy',
        'region_constrained': 'Region Constrained Policy'
    }
    
    print(f"=== CREATING {constraint_names[constraint].upper()} DASHBOARD ===")
    
    # Filter to specific constraint only
    df_analysis = get_mid_scenarios_symmetric(df_country)
    df_filtered = df_analysis[df_analysis['constraint'] == constraint].copy()
    df_filtered['goal_type'] = df_filtered['scenario'].apply(get_goal_from_scenario)
    
    print(f"Filtered to {constraint}: {len(df_analysis)} → {len(df_filtered)} records")
    
    if df_filtered.empty:
        print(f"No data for constraint {constraint}")
        return None
    
    # Calculate value addition
    df_va = calculate_value_addition(df_filtered)
    
    # Create 2x4 subplot grid
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle(f'{country_name} Critical Minerals - {constraint_names[constraint]}', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Color scheme
    goal_colors = {
        'baseline': '#2E86AB',
        'bau': '#A23B72', 
        'early_refining': '#F18F01',
        'precursor': '#C73E1D'
    }
    
    # === ROW 1: PRODUCTION ANALYSIS ===
    
    # 1.1 Metal Content Production (Stage 0)
    ax = axes[0, 0]
    stage0_data = df_filtered[df_filtered['processing_stage'] == 0]
    goal_prod_metal = stage0_data.groupby('goal_type')['production_tonnes'].sum() / 1e6
    goal_prod_metal_filtered = goal_prod_metal[goal_prod_metal > 0]
    
    if not goal_prod_metal_filtered.empty:
        bars = ax.bar(goal_prod_metal_filtered.index, goal_prod_metal_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_prod_metal_filtered.index])
        ax.set_title('Metal Content Production\n[Stage 0]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, val in zip(bars, goal_prod_metal_filtered.values):
            y_offset = 0.05  # Fixed offset instead of dynamic
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No stage 0 data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Metal Content Production\n[Stage 0]', fontweight='bold')
    
    # 1.2 Products Production - All Stages >0
    ax = axes[0, 1]
    stage_pos_data = df_filtered[df_filtered['processing_stage'] > 0]
    goal_prod_products = stage_pos_data.groupby('goal_type')['production_tonnes'].sum() / 1e6
    goal_prod_products_filtered = goal_prod_products[goal_prod_products > 0]
    
    if not goal_prod_products_filtered.empty:
        bars = ax.bar(goal_prod_products_filtered.index, goal_prod_products_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_prod_products_filtered.index])
        ax.set_title('Products Production\n[All Stages >0]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, val in zip(bars, goal_prod_products_filtered.values):
            y_offset = 0.05  # Fixed offset instead of dynamic
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No products data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Products Production\n[All Stages >0]', fontweight='bold')
    
    # 1.3 Goal Target Stages Only
    ax = axes[0, 2]
    goal_stage_production = {}
    for goal in ['baseline', 'bau', 'early_refining', 'precursor']:
        goal_data = df_filtered[df_filtered['goal_type'] == goal]
        if not goal_data.empty:
            prod = get_goal_stage_production(goal_data, goal) / 1e6
            if prod > 0:
                goal_stage_production[goal] = prod
    
    if goal_stage_production:
        bars = ax.bar(goal_stage_production.keys(), goal_stage_production.values(),
                     color=[goal_colors.get(goal, '#888888') for goal in goal_stage_production.keys()])
        ax.set_title('Goal Target Stages Only\n[Specific Target per Goal]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, goal in zip(bars, goal_stage_production.keys()):
            val = goal_stage_production[goal]
            y_offset = 0.05  # Fixed offset instead of dynamic
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'{val:.3f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No goal stage data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Goal Target Stages Only\n[Specific Target per Goal]', fontweight='bold')
    
    # 1.4 Revenue by Goal
    ax = axes[0, 3]
    goal_revenue = df_filtered.groupby('goal_type')['revenue_usd'].sum() / 1e9
    goal_revenue_filtered = goal_revenue[goal_revenue > 0]
    
    if not goal_revenue_filtered.empty:
        bars = ax.bar(goal_revenue_filtered.index, goal_revenue_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_revenue_filtered.index])
        ax.set_title('Revenue by Goal', fontweight='bold')
        ax.set_ylabel('Revenue ($B)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, val in zip(bars, goal_revenue_filtered.values):
            y_offset = 0.2  # Fixed offset instead of dynamic
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'${val:.1f}B', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue by Goal', fontweight='bold')
    
    # === ROW 2: ECONOMIC & INFRASTRUCTURE ===
    
    # 2.1 Value Addition
    ax = axes[1, 0]
    if not df_va.empty:
        goal_va = df_va.groupby('goal_type')['value_added_musd'].sum()
        
        if not goal_va.empty:
            bars = ax.bar(goal_va.index, goal_va.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_va.index])
            ax.set_title('Value Addition\n[Negative = Processing Losses]', fontweight='bold')
            ax.set_ylabel('Value Added (M USD)')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            for bar, val in zip(bars, goal_va.values):
                y_offset = 50 if val >= 0 else -50  # Fixed offset instead of dynamic
                ax.text(bar.get_x() + bar.get_width()/2, 
                       bar.get_height() + y_offset, 
                       f'${val:.0f}M', ha='center', va='bottom' if val >= 0 else 'top', fontsize=8)
        else:
            ax.text(0.5, 0.5, 'No value addition', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Value Addition\n[Negative = Processing Losses]', fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No value addition data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Value Addition\n[Negative = Processing Losses]', fontweight='bold')
    
    # 2.2 Transport Volumes
    ax = axes[1, 1]
    transport_data = df_filtered[df_filtered['transport_total_tonkm'] > 0]
    if not transport_data.empty:
        goal_transport = transport_data.groupby('goal_type')['transport_total_tonkm'].sum() / 1e6
        if not goal_transport.empty:
            bars = ax.bar(goal_transport.index, goal_transport.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_transport.index])
            ax.set_title('Transport Volumes', fontweight='bold')
            ax.set_ylabel('Volume (M ton-km)')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            for bar, val in zip(bars, goal_transport.values):
                y_offset = 200  # Fixed offset instead of dynamic
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                       f'{val:.0f}M', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No transport data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Transport Volumes', fontweight='bold')
    
    # 2.3 Energy Capacity
    ax = axes[1, 2]
    energy_data = df_filtered[df_filtered['energy_req_capacity_kW'] > 0]
    if not energy_data.empty:
        goal_energy = energy_data.groupby('goal_type')['energy_req_capacity_kW'].sum() / 1e6
        if not goal_energy.empty:
            bars = ax.bar(goal_energy.index, goal_energy.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_energy.index])
            ax.set_title('Energy Capacity Required', fontweight='bold')
            ax.set_ylabel('Capacity (MW)')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            for bar, val in zip(bars, goal_energy.values):
                y_offset = 0.1  # Fixed offset instead of dynamic
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                       f'{val:.1f}MW', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No energy data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Energy Capacity Required', fontweight='bold')
    
    # 2.4 Transport Costs
    ax = axes[1, 3]
    cost_cols = ['export_transport_cost_usd', 'import_transport_cost_usd']
    transport_cost_data = df_filtered[df_filtered[cost_cols].sum(axis=1) > 0]
    if not transport_cost_data.empty:
        transport_cost_data = transport_cost_data.copy()
        transport_cost_data['total_transport_cost'] = transport_cost_data[cost_cols].sum(axis=1)
        goal_cost = transport_cost_data.groupby('goal_type')['total_transport_cost'].sum() / 1e6
        if not goal_cost.empty:
            bars = ax.bar(goal_cost.index, goal_cost.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_cost.index])
            ax.set_title('Transport Costs', fontweight='bold')
            ax.set_ylabel('Cost (M USD)')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            for bar, val in zip(bars, goal_cost.values):
                y_offset = 5  # Fixed offset instead of dynamic
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                       f'${val:.0f}M', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No transport cost data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Transport Costs', fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.93], h_pad=3.0)
    
    # Save dashboard
    country_code = df_country['iso3'].iloc[0].upper() if not df_country.empty else 'COUNTRY'
    filename = f'{country_code}_{constraint}_dashboard.png'
    dashboard_path = os.path.join(output_dir, filename)
    fig.savefig(dashboard_path, dpi=300, bbox_inches=None)
    plt.close(fig)
    
    print(f"✓ {constraint_names[constraint]} dashboard saved: {dashboard_path}")
    
    # Generate constraint-specific insights
    insights_text = generate_constraint_insights(df_filtered, constraint)
    
    # Save insights as text file
    insights_filename = f'{country_code}_{constraint}_insights.txt'
    insights_path = os.path.join(output_dir, insights_filename)
    with open(insights_path, 'w') as f:
        f.write(insights_text)
    print(f"✓ {constraint_names[constraint]} insights saved: {insights_path}")
    
    # Also print insights to console
    print(f"\n{insights_text}")
    
    return dashboard_path

def test_dashboards_3_4():
    """Test dashboards 3-4 (region constraints)"""
    
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
    output_dir = os.path.join(output_data_path, 'country_reports', 'single_constraint_dashboards_ZMB')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create dashboards 3-4 (region constraints)
    constraints = ['region_unconstrained', 'region_constrained']
    dashboard_paths = []
    
    for constraint in constraints:
        country_name = df_country['country_name'].iloc[0] if 'country_name' in df_country.columns and not df_country.empty else 'Country'
        dashboard_path = create_single_constraint_dashboard(df_country, constraint, output_dir, country_name)
        if dashboard_path:
            dashboard_paths.append(dashboard_path)
    
    print(f"\n✓ Generated {len(dashboard_paths)} region dashboards in: {output_dir}")
    return output_dir

def test_all_single_constraint_dashboards():
    """Test all 4 single constraint dashboards"""
    
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
    output_dir = os.path.join(output_data_path, 'country_reports', 'single_constraint_dashboards_ZMB')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create all 4 dashboards
    constraints = ['country_unconstrained', 'country_constrained', 'region_unconstrained', 'region_constrained']
    dashboard_paths = []
    
    for constraint in constraints:
        country_name = df_country['country_name'].iloc[0] if 'country_name' in df_country.columns and not df_country.empty else 'Country'
        dashboard_path = create_single_constraint_dashboard(df_country, constraint, output_dir, country_name)
        if dashboard_path:
            dashboard_paths.append(dashboard_path)
    
    # Generate comprehensive pivot summary table with all constraints 
    mid_data = get_mid_scenarios_symmetric(df_country)
    pivot_summary = create_pivot_summary_table(mid_data)
    country_code = df_country['iso3'].iloc[0].upper() if not df_country.empty else 'COUNTRY'
    summary_filename = f'{country_code}_all_constraints_summary_table.csv'
    summary_path = os.path.join(output_dir, summary_filename)
    pivot_summary.to_csv(summary_path, index=False)
    print(f"✓ Comprehensive pivot summary table saved: {summary_path}")
    
    print(f"\n✓ Generated {len(dashboard_paths)} total single constraint dashboards in: {output_dir}")
    return output_dir

def generate_all_countries_dashboards():
    """Generate single constraint dashboards for all countries"""
    
    # Load configuration
    import json
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load all data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Get unique countries
    countries = df['iso3'].dropna().unique()
    print(f"Found {len(countries)} countries: {', '.join(countries)}")
    
    # Generate dashboards for each country
    all_outputs = {}
    
    for country_code in countries:
        print(f"\n{'='*60}")
        print(f"PROCESSING COUNTRY: {country_code}")
        print(f"{'='*60}")
        
        df_country = df[df['iso3'] == country_code].copy()
        
        if df_country.empty:
            print(f"No data found for {country_code}")
            continue
            
        # Check if country has meaningful data
        total_production = df_country['production_tonnes'].sum()
        if total_production == 0:
            print(f"No production data for {country_code}, skipping...")
            continue
        
        # Create output directory for this country
        output_dir = os.path.join(output_data_path, 'country_reports', f'single_constraint_dashboards_{country_code}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate dashboards for all 4 constraints
        constraints = ['country_unconstrained', 'country_constrained', 'region_unconstrained', 'region_constrained']
        dashboard_paths = []
        
        for constraint in constraints:
            country_name = df_country['country_name'].iloc[0] if 'country_name' in df_country.columns and not df_country.empty else country_code
            dashboard_path = create_single_constraint_dashboard(df_country, constraint, output_dir, country_name)
            if dashboard_path:
                dashboard_paths.append(dashboard_path)
        
        # Generate policy comparison dashboard
        try:
            policy_dashboard_path = create_policy_comparison_dashboard(df_country, output_dir, country_name)
            if policy_dashboard_path:
                dashboard_paths.append(policy_dashboard_path)
                print(f"✓ Policy comparison dashboard generated for {country_code}")
        except Exception as e:
            print(f"Warning: Could not generate policy comparison dashboard for {country_code}: {e}")
        
        # Generate comprehensive pivot summary table with all constraints 
        mid_data = get_mid_scenarios_symmetric(df_country)
        if not mid_data.empty:
            pivot_summary = create_pivot_summary_table(mid_data)
            summary_filename = f'{country_code.upper()}_all_constraints_summary_table.csv'
            summary_path = os.path.join(output_dir, summary_filename)
            pivot_summary.to_csv(summary_path, index=False)
            print(f"✓ Comprehensive pivot summary table saved: {summary_path}")
        
        all_outputs[country_code] = {
            'output_dir': output_dir,
            'dashboards': len(dashboard_paths),
            'has_summary': not mid_data.empty
        }
        
        print(f"✓ Generated {len(dashboard_paths)} dashboards for {country_code}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY OF ALL COUNTRY DASHBOARDS")
    print(f"{'='*60}")
    
    total_dashboards = sum(info['dashboards'] for info in all_outputs.values())
    countries_with_data = len([c for c, info in all_outputs.items() if info['dashboards'] > 0])
    
    print(f"✓ Total countries processed: {countries_with_data}")
    print(f"✓ Total dashboards generated: {total_dashboards}")
    print(f"✓ Output location: {os.path.join(output_data_path, 'country_reports')}")
    
    return all_outputs

if __name__ == "__main__":
    generate_all_countries_dashboards()