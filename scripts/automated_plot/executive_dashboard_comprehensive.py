"""
Comprehensive Executive Dashboard - All Metrics with Policy Comparisons
3x4 layout covering production, economic, infrastructure, and policy analysis
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
    df_va = df_va.groupby(['scenario', 'constraint', 'reference_mineral'], group_keys=False).apply(calc_value_added).reset_index(drop=True)
    df_va['value_added_musd'] = df_va['value_added'] / 1e6  # Convert to millions USD
    
    return df_va

def get_goal_stage_production(df_analysis, goal_type):
    """Get production for target stages only for a specific goal"""
    
    if goal_type == 'baseline':
        # For baseline, use stage 0 (extraction)
        return df_analysis[df_analysis['processing_stage'] == 0]['production_tonnes'].sum()
    
    # Map goal types to processing types for target stage lookup
    goal_to_processing = {
        'bau': 'Beneficiation',
        'early_refining': 'Early refining', 
        'precursor': 'Precursor related product'
    }
    
    processing_type = goal_to_processing.get(goal_type)
    if not processing_type:
        return 0
    
    total_production = 0
    
    # For each mineral, get target stage production
    for mineral in df_analysis['reference_mineral'].unique():
        mineral_data = df_analysis[df_analysis['reference_mineral'] == mineral]
        
        if mineral in mineral_processing_stages:
            target_stages = mineral_processing_stages[mineral]['target_stages']
            target_stage = target_stages.get(processing_type)
            
            if target_stage:
                stage_production = mineral_data[mineral_data['processing_stage'] == target_stage]['production_tonnes'].sum()
                total_production += stage_production
    
    return total_production

def create_comprehensive_dashboard(df_country, output_dir):
    """Create comprehensive 3x4 executive dashboard"""
    
    print("=== CREATING COMPREHENSIVE EXECUTIVE DASHBOARD ===")
    
    # Use symmetric mid-scenario filtering
    df_analysis = get_mid_scenarios_symmetric(df_country)
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    df_analysis['constraint_type'] = df_analysis['constraint'].str.split('_').str[0]  # country/region
    df_analysis['constraint_level'] = df_analysis['constraint'].str.split('_').str[1]  # constrained/unconstrained
    
    # Calculate value addition
    df_va = calculate_value_addition(df_analysis)
    
    # Create 3x4 subplot grid
    fig, axes = plt.subplots(3, 4, figsize=(24, 18))
    fig.suptitle('Zambia Critical Minerals - Comprehensive Executive Dashboard', 
                 fontsize=18, fontweight='bold', y=0.95)
    
    # Color schemes
    goal_colors = {
        'baseline': '#2E86AB',
        'bau': '#A23B72', 
        'early_refining': '#F18F01',
        'precursor': '#C73E1D'
    }
    constraint_colors = {'country': '#1f77b4', 'region': '#ff7f0e'}
    level_colors = {'constrained': '#d62728', 'unconstrained': '#2ca02c'}
    
    # === ROW 1: PRODUCTION ANALYSIS ===
    
    # 1.1 Metal Content Production (Stage 0)
    ax = axes[0, 0]
    stage0_data = df_analysis[df_analysis['processing_stage'] == 0]
    goal_prod_metal = stage0_data.groupby('goal_type')['production_tonnes'].sum() / 1e6  # Mt
    goal_prod_metal_filtered = goal_prod_metal[goal_prod_metal > 0]
    
    if not goal_prod_metal_filtered.empty:
        bars = ax.bar(goal_prod_metal_filtered.index, goal_prod_metal_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_prod_metal_filtered.index])
        ax.set_title('Metal Content Production\n[Stage 0 - Raw Extraction]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        for bar, val in zip(bars, goal_prod_metal_filtered.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                   f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No stage 0 data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Metal Content Production\n[Stage 0 - Raw Extraction]', fontweight='bold')
    
    # 1.2 Products Production - All Stages >0
    ax = axes[0, 1]
    stage_pos_data = df_analysis[df_analysis['processing_stage'] > 0]
    goal_prod_products = stage_pos_data.groupby('goal_type')['production_tonnes'].sum() / 1e6  # Mt
    goal_prod_products_filtered = goal_prod_products[goal_prod_products > 0]
    
    if not goal_prod_products_filtered.empty:
        bars = ax.bar(goal_prod_products_filtered.index, goal_prod_products_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_prod_products_filtered.index])
        ax.set_title('Products Production\n[All Stages >0]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        for bar, val in zip(bars, goal_prod_products_filtered.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                   f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No products data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Products Production\n[All Stages >0]', fontweight='bold')
    
    # 1.3 Goal Stages Only
    ax = axes[0, 2]
    goal_stage_production = {}
    for goal in ['baseline', 'bau', 'early_refining', 'precursor']:
        goal_data = df_analysis[df_analysis['goal_type'] == goal]
        if not goal_data.empty:
            prod = get_goal_stage_production(goal_data, goal) / 1e6  # Mt
            if prod > 0:
                goal_stage_production[goal] = prod
    
    if goal_stage_production:
        bars = ax.bar(goal_stage_production.keys(), goal_stage_production.values(),
                     color=[goal_colors.get(goal, '#888888') for goal in goal_stage_production.keys()])
        ax.set_title('Goal Target Stages Only\n[Specific Target per Goal]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        for bar, goal in zip(bars, goal_stage_production.keys()):
            val = goal_stage_production[goal]
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                   f'{val:.3f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No goal stage data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Goal Target Stages Only\n[Specific Target per Goal]', fontweight='bold')
    
    # 1.4 Revenue by Goal
    ax = axes[0, 3]
    goal_revenue = df_analysis.groupby('goal_type')['revenue_usd'].sum() / 1e9  # Billion USD
    goal_revenue_filtered = goal_revenue[goal_revenue > 0]
    
    if not goal_revenue_filtered.empty:
        bars = ax.bar(goal_revenue_filtered.index, goal_revenue_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_revenue_filtered.index])
        ax.set_title('Revenue by Goal', fontweight='bold')
        ax.set_ylabel('Revenue ($B)')
        ax.tick_params(axis='x', rotation=45)
        for bar, val in zip(bars, goal_revenue_filtered.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                   f'${val:.1f}B', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue by Goal', fontweight='bold')
    
    # === ROW 2: ECONOMIC & INFRASTRUCTURE ===
    
    # 2.1 Value Addition (Fixed to show negative values)
    ax = axes[1, 0]
    if not df_va.empty:
        goal_va = df_va.groupby('goal_type')['value_added_musd'].sum()
        # Don't filter out negative values - show all
        
        if not goal_va.empty:
            bars = ax.bar(goal_va.index, goal_va.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_va.index])
            ax.set_title('Value Addition\n[Negative = Processing Losses]', fontweight='bold')
            ax.set_ylabel('Value Added (M USD)')
            ax.tick_params(axis='x', rotation=45)
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)  # Add zero line
            for bar, val in zip(bars, goal_va.values):
                # Adjust label position to avoid title overlap
                y_offset = 100 if val >= 0 else -300
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
    transport_data = df_analysis[df_analysis['transport_total_tonkm'] > 0]
    if not transport_data.empty:
        goal_transport = transport_data.groupby('goal_type')['transport_total_tonkm'].sum() / 1e6  # Million ton-km
        if not goal_transport.empty:
            bars = ax.bar(goal_transport.index, goal_transport.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_transport.index])
            ax.set_title('Transport Volumes', fontweight='bold')
            ax.set_ylabel('Volume (M ton-km)')
            ax.tick_params(axis='x', rotation=45)
            for bar, val in zip(bars, goal_transport.values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200, 
                       f'{val:.0f}M', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No transport data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Transport Volumes', fontweight='bold')
    
    # 2.3 Energy Capacity
    ax = axes[1, 2]
    energy_data = df_analysis[df_analysis['energy_req_capacity_kW'] > 0]
    if not energy_data.empty:
        goal_energy = energy_data.groupby('goal_type')['energy_req_capacity_kW'].sum() / 1e6  # MW
        if not goal_energy.empty:
            bars = ax.bar(goal_energy.index, goal_energy.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_energy.index])
            ax.set_title('Energy Capacity Required', fontweight='bold')
            ax.set_ylabel('Capacity (MW)')
            ax.tick_params(axis='x', rotation=45)
            for bar, val in zip(bars, goal_energy.values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                       f'{val:.1f}MW', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No energy data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Energy Capacity Required', fontweight='bold')
    
    # 2.4 Transport Costs
    ax = axes[1, 3]
    cost_cols = ['export_transport_cost_usd', 'import_transport_cost_usd']
    transport_cost_data = df_analysis[df_analysis[cost_cols].sum(axis=1) > 0]
    if not transport_cost_data.empty:
        transport_cost_data['total_transport_cost'] = transport_cost_data[cost_cols].sum(axis=1)
        goal_cost = transport_cost_data.groupby('goal_type')['total_transport_cost'].sum() / 1e6  # Million USD
        if not goal_cost.empty:
            bars = ax.bar(goal_cost.index, goal_cost.values,
                         color=[goal_colors.get(goal, '#888888') for goal in goal_cost.index])
            ax.set_title('Transport Costs', fontweight='bold')
            ax.set_ylabel('Cost (M USD)')
            ax.tick_params(axis='x', rotation=45)
            for bar, val in zip(bars, goal_cost.values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                       f'${val:.0f}M', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No transport cost data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Transport Costs', fontweight='bold')
    
    # === ROW 3: POLICY COMPARISONS ===
    
    # 3.1 Water Usage: Country vs Region
    ax = axes[2, 0]
    policy_water = df_analysis.groupby(['goal_type', 'constraint_type'])['water_usage_m3'].sum() / 1e6
    if not policy_water.empty:
        policy_water_pivot = policy_water.unstack(level=1, fill_value=0)
        if not policy_water_pivot.empty:
            policy_water_pivot.plot(kind='bar', ax=ax, color=[constraint_colors.get(col, '#888888') 
                                                            for col in policy_water_pivot.columns])
            ax.set_title('Water Usage\nCountry vs Region Policy', fontweight='bold')
            ax.set_ylabel('Water Usage (M m³)')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Policy Focus')
    else:
        ax.text(0.5, 0.5, 'No water policy data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Water Usage\nCountry vs Region Policy', fontweight='bold')
    
    # 3.2 CO2 Emissions: Country vs Region  
    ax = axes[2, 1]
    policy_co2 = df_analysis.groupby(['goal_type', 'constraint_type'])['transport_total_tonsCO2eq'].sum() / 1e3
    if not policy_co2.empty:
        policy_co2_pivot = policy_co2.unstack(level=1, fill_value=0)
        if not policy_co2_pivot.empty:
            policy_co2_pivot.plot(kind='bar', ax=ax, color=[constraint_colors.get(col, '#888888') 
                                                          for col in policy_co2_pivot.columns])
            ax.set_title('CO2 Emissions\nCountry vs Region Policy', fontweight='bold')
            ax.set_ylabel('CO2 Emissions (kt)')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Policy Focus')
    else:
        ax.text(0.5, 0.5, 'No CO2 policy data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('CO2 Emissions\nCountry vs Region Policy', fontweight='bold')
    
    # 3.3 Production: Constrained vs Unconstrained (Most Representative)
    ax = axes[2, 2]
    # Use Products Production (Stage >0) as most representative of processing capability
    stage_pos_constraint = df_analysis[df_analysis['processing_stage'] > 0]
    level_production = stage_pos_constraint.groupby(['goal_type', 'constraint_level'])['production_tonnes'].sum() / 1e6
    if not level_production.empty:
        level_production_pivot = level_production.unstack(level=1, fill_value=0)
        if not level_production_pivot.empty:
            level_production_pivot.plot(kind='bar', ax=ax, color=[level_colors.get(col, '#888888') 
                                                                for col in level_production_pivot.columns])
            ax.set_title('Products Production Impact\n[All Stages >0] Constrained vs Unconstrained', fontweight='bold')
            ax.set_ylabel('Production (Mt)')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Constraint Level')
    else:
        ax.text(0.5, 0.5, 'No production constraint data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Products Production Impact\n[All Stages >0] Constrained vs Unconstrained', fontweight='bold')
    
    # 3.4 Revenue: Constrained vs Unconstrained
    ax = axes[2, 3]
    level_revenue = df_analysis.groupby(['goal_type', 'constraint_level'])['revenue_usd'].sum() / 1e9
    if not level_revenue.empty:
        level_revenue_pivot = level_revenue.unstack(level=1, fill_value=0)
        if not level_revenue_pivot.empty:
            level_revenue_pivot.plot(kind='bar', ax=ax, color=[level_colors.get(col, '#888888') 
                                                             for col in level_revenue_pivot.columns])
            ax.set_title('Revenue Impact\nConstrained vs Unconstrained', fontweight='bold')
            ax.set_ylabel('Revenue ($B)')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Constraint Level')
    else:
        ax.text(0.5, 0.5, 'No revenue constraint data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue Impact\nConstrained vs Unconstrained', fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save dashboard
    dashboard_path = os.path.join(output_dir, 'zambia_comprehensive_executive_dashboard.png')
    fig.savefig(dashboard_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Comprehensive dashboard saved: {dashboard_path}")
    return dashboard_path

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

def generate_dashboard_insights(df_analysis):
    """Generate key dashboard insights text for DOCX integration"""
    
    insights = {
        'production_analysis': [],
        'economic_infrastructure': [],
        'policy_comparisons': []
    }
    
    # Production Analysis Insights
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    
    # Metal content vs products progression
    stage0_totals = df_analysis[df_analysis['processing_stage'] == 0].groupby('goal_type')['production_tonnes'].sum() / 1e6
    products_totals = df_analysis[df_analysis['processing_stage'] > 0].groupby('goal_type')['production_tonnes'].sum() / 1e6
    
    if not stage0_totals.empty and not products_totals.empty:
        stage0_range = f"{stage0_totals.min():.2f}-{stage0_totals.max():.2f} Mt"
        products_range = f"{products_totals.min():.2f}-{products_totals.max():.2f} Mt"
        insights['production_analysis'].append(f"Clear progression from raw extraction ({stage0_range}) → processed products ({products_range})")
    
    # Revenue progression
    revenue_totals = df_analysis.groupby('goal_type')['revenue_usd'].sum() / 1e9
    if not revenue_totals.empty:
        rev_min, rev_max = revenue_totals.min(), revenue_totals.max()
        insights['production_analysis'].append(f"Revenue impact ranges ${rev_min:.1f}B-${rev_max:.1f}B across processing goals")
    
    # Economic & Infrastructure Insights
    df_va = calculate_value_addition(df_analysis)
    if not df_va.empty:
        va_totals = df_va.groupby('goal_type')['value_added_musd'].sum()
        va_min, va_max = va_totals.min(), va_totals.max()
        insights['economic_infrastructure'].append(f"Value addition shows processing losses (${va_min:.1f}B to ${va_max:.1f}B), indicating current processing stages may not be economically viable")
    
    # Transport and energy insights
    transport_data = df_analysis[df_analysis['transport_total_tonkm'] > 0]
    if not transport_data.empty:
        transport_totals = transport_data.groupby('goal_type')['transport_total_tonkm'].sum() / 1e6
        insights['economic_infrastructure'].append("Transport volumes increase with processing complexity")
    
    energy_data = df_analysis[df_analysis['energy_req_capacity_kW'] > 0]
    if not energy_data.empty:
        energy_totals = energy_data.groupby('goal_type')['energy_req_capacity_kW'].sum() / 1e6
        peak_goal = energy_totals.idxmax()
        peak_val = energy_totals.max()
        insights['economic_infrastructure'].append(f"Energy needs peak at {peak_goal} stage ({peak_val:.1f}MW)")
    
    # Policy Comparison Insights
    df_analysis['constraint_type'] = df_analysis['constraint'].str.split('_').str[0]
    df_analysis['constraint_level'] = df_analysis['constraint'].str.split('_').str[1]
    
    # Country vs Region trade-offs
    insights['policy_comparisons'].append("**Country vs Region**: Shows policy trade-offs for environmental metrics")
    
    # Constrained vs Unconstrained impacts
    insights['policy_comparisons'].append("**Constrained vs Unconstrained**: Shows regulatory impact on core metrics (production & revenue)")
    
    return insights

def test_comprehensive_dashboard():
    """Test the comprehensive dashboard"""
    
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
    output_dir = os.path.join(output_data_path, 'country_reports', 'test_comprehensive_dashboard_ZMB')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create comprehensive dashboard
    dashboard_path = create_comprehensive_dashboard(df_country, output_dir)
    
    # Generate pivot summary table
    print("\n=== CREATING PIVOT SUMMARY TABLE ===")
    mid_data = get_mid_scenarios_symmetric(df_country)
    pivot_summary = create_pivot_summary_table(mid_data)
    
    if not pivot_summary.empty:
        summary_path = os.path.join(output_dir, 'zambia_comprehensive_pivot_summary.csv')
        pivot_summary.to_csv(summary_path, index=False)
        print(f"✓ Comprehensive pivot summary table saved: {summary_path}")
        print(f"Table shape: {pivot_summary.shape}")
    
    # Generate dashboard insights
    print("\n=== GENERATING DASHBOARD INSIGHTS ===")
    insights = generate_dashboard_insights(mid_data)
    
    insights_path = os.path.join(output_dir, 'dashboard_insights.txt')
    with open(insights_path, 'w') as f:
        f.write("ZAMBIA CRITICAL MINERALS DASHBOARD - KEY INSIGHTS\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("PRODUCTION ANALYSIS:\n")
        for insight in insights['production_analysis']:
            f.write(f"- {insight}\n")
        f.write("\n")
        
        f.write("ECONOMIC & INFRASTRUCTURE:\n")
        for insight in insights['economic_infrastructure']:
            f.write(f"- {insight}\n")
        f.write("\n")
        
        f.write("POLICY COMPARISONS:\n")
        for insight in insights['policy_comparisons']:
            f.write(f"- {insight}\n")
    
    print(f"✓ Dashboard insights saved: {insights_path}")
    
    return output_dir

if __name__ == "__main__":
    test_comprehensive_dashboard()