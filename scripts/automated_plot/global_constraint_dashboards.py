"""
Global Constraint Dashboards - Cross-Country Aggregated Analysis
Creates dashboards showing continental totals and country rankings across all 13 producing countries
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

def get_mid_scenarios_symmetric(df):
    """Get mid-scenarios with symmetric filtering logic"""
    mid_scenarios = df[
        (df['scenario'].str.contains('mid_min|mid_max', na=False)) |
        (df['scenario'] == '2022_baseline')
    ].copy()
    
    return mid_scenarios

def calculate_global_value_addition(df_analysis):
    """Calculate value addition aggregated across all countries"""
    df_va = df_analysis[df_analysis["processing_stage"] > 0].copy()
    
    if df_va.empty:
        return pd.DataFrame()
    
    df_va = df_va.groupby(['scenario', 'constraint', 'reference_mineral'], group_keys=False).apply(calc_value_added).reset_index(drop=True)
    df_va['value_added_musd'] = df_va['value_added'] / 1e6
    
    return df_va

def get_top_countries_by_metric(df_filtered, metric_column, top_n=5, processing_stage_filter=None):
    """Get top N countries by a specific metric"""
    df_metric = df_filtered.copy()
    
    # Apply processing stage filter if specified
    if processing_stage_filter is not None:
        if processing_stage_filter == 0:
            df_metric = df_metric[df_metric['processing_stage'] == 0]
        elif processing_stage_filter == 'positive':
            df_metric = df_metric[df_metric['processing_stage'] > 0]
    
    # Aggregate by country
    country_totals = df_metric.groupby('iso3')[metric_column].sum().sort_values(ascending=False)
    
    # Return top N countries with non-zero values
    top_countries = country_totals[country_totals > 0].head(top_n)
    
    return top_countries

def create_global_constraint_dashboard(df_all_countries, constraint, output_dir):
    """Create Global Constraint Dashboard showing continental totals and country rankings"""
    
    constraint_names = {
        'country_unconstrained': 'Global - Country Unconstrained Policy',
        'country_constrained': 'Global - Country Constrained Policy', 
        'region_unconstrained': 'Global - Region Unconstrained Policy',
        'region_constrained': 'Global - Region Constrained Policy'
    }
    
    print(f"=== CREATING {constraint_names[constraint].upper()} DASHBOARD ===")
    
    # Filter to specific constraint only (across all countries)
    df_analysis = get_mid_scenarios_symmetric(df_all_countries)
    df_filtered = df_analysis[df_analysis['constraint'] == constraint].copy()
    df_filtered['goal_type'] = df_filtered['scenario'].apply(get_goal_from_scenario)
    
    print(f"Global filtered to {constraint}: {len(df_analysis)} → {len(df_filtered)} records")
    
    if df_filtered.empty:
        print(f"No data for constraint {constraint}")
        return None
    
    # Calculate global value addition
    df_va = calculate_global_value_addition(df_filtered)
    
    # Create 2x4 subplot grid
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle(f'Critical Minerals - {constraint_names[constraint]}', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Color scheme
    goal_colors = {
        'baseline': '#2E86AB',
        'bau': '#A23B72', 
        'early_refining': '#F18F01',
        'precursor': '#C73E1D'
    }
    
    # === ROW 1: CONTINENTAL TOTALS ===
    
    # 1.1 Total Metal Content Production (Stage 0)
    ax = axes[0, 0]
    stage0_data = df_filtered[df_filtered['processing_stage'] == 0]
    goal_prod_metal = stage0_data.groupby('goal_type')['production_tonnes'].sum() / 1e6
    goal_prod_metal_filtered = goal_prod_metal[goal_prod_metal > 0]
    
    if not goal_prod_metal_filtered.empty:
        bars = ax.bar(goal_prod_metal_filtered.index, goal_prod_metal_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_prod_metal_filtered.index])
        ax.set_title('Continental Metal Production\n[Stage 0 Total]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, val in zip(bars, goal_prod_metal_filtered.values):
            y_offset = 0.1  # Fixed offset
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'{val:.1f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No stage 0 data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Continental Metal Production\n[Stage 0 Total]', fontweight='bold')
    
    # 1.2 Total Products Production (All Stages >0)
    ax = axes[0, 1]
    stage_pos_data = df_filtered[df_filtered['processing_stage'] > 0]
    goal_prod_products = stage_pos_data.groupby('goal_type')['production_tonnes'].sum() / 1e6
    goal_prod_products_filtered = goal_prod_products[goal_prod_products > 0]
    
    if not goal_prod_products_filtered.empty:
        bars = ax.bar(goal_prod_products_filtered.index, goal_prod_products_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_prod_products_filtered.index])
        ax.set_title('Continental Products\n[All Stages >0 Total]', fontweight='bold')
        ax.set_ylabel('Production (Mt)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, val in zip(bars, goal_prod_products_filtered.values):
            y_offset = 0.2  # Fixed offset
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'{val:.1f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No products data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Continental Products\n[All Stages >0 Total]', fontweight='bold')
    
    # 1.3 Total Revenue by Goal
    ax = axes[0, 2]
    goal_revenue = df_filtered.groupby('goal_type')['revenue_usd'].sum() / 1e9
    goal_revenue_filtered = goal_revenue[goal_revenue > 0]
    
    if not goal_revenue_filtered.empty:
        bars = ax.bar(goal_revenue_filtered.index, goal_revenue_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_revenue_filtered.index])
        ax.set_title('Continental Revenue\n[Total across Africa]', fontweight='bold')
        ax.set_ylabel('Revenue ($B)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, val in zip(bars, goal_revenue_filtered.values):
            y_offset = 5  # Fixed offset
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'${val:.0f}B', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Continental Revenue\n[Total across Africa]', fontweight='bold')
    
    # 1.4 Total CO2 Emissions by Goal
    ax = axes[0, 3]
    # Combine transport and energy emissions
    df_filtered['total_co2'] = df_filtered['transport_total_tonsCO2eq'] + df_filtered['energy_tonsCO2eq']
    goal_co2 = df_filtered.groupby('goal_type')['total_co2'].sum() / 1e3  # Convert to kt
    goal_co2_filtered = goal_co2[goal_co2 > 0]
    
    if not goal_co2_filtered.empty:
        bars = ax.bar(goal_co2_filtered.index, goal_co2_filtered.values,
                     color=[goal_colors.get(goal, '#888888') for goal in goal_co2_filtered.index])
        ax.set_title('Continental CO2 Emissions\n[Transport + Energy]', fontweight='bold')
        ax.set_ylabel('Emissions (kt CO2eq)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        for bar, val in zip(bars, goal_co2_filtered.values):
            y_offset = 10  # Fixed offset
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_offset, 
                   f'{val:.0f}kt', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No emissions data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Continental CO2 Emissions\n[Transport + Energy]', fontweight='bold')
    
    # === ROW 2: TOP COUNTRIES RANKINGS ===
    
    # 2.1 Top 5 Countries by Metal Production (Stage 0)
    ax = axes[1, 0]
    top_prod_countries = get_top_countries_by_metric(df_filtered, 'production_tonnes', top_n=5, processing_stage_filter=0)
    if not top_prod_countries.empty:
        top_prod_countries_mt = top_prod_countries / 1e6  # Convert to Mt
        bars = ax.barh(range(len(top_prod_countries_mt)), top_prod_countries_mt.values, color='#2E86AB')
        ax.set_yticks(range(len(top_prod_countries_mt)))
        ax.set_yticklabels(top_prod_countries_mt.index)
        ax.set_title('Top Countries\n[Metal Production]', fontweight='bold')
        ax.set_xlabel('Production (Mt)')  
        ax.grid(True, linestyle='--', alpha=0.7, axis='x')
        for i, val in enumerate(top_prod_countries_mt.values):
            x_offset = 0.05  # Fixed offset
            ax.text(val + x_offset, i, f'{val:.1f}', ha='left', va='center', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No production data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Top Countries\n[Metal Production]', fontweight='bold')
    
    # 2.2 Top 5 Countries by Revenue
    ax = axes[1, 1]
    top_revenue_countries = get_top_countries_by_metric(df_filtered, 'revenue_usd', top_n=5)
    if not top_revenue_countries.empty:
        top_revenue_countries_b = top_revenue_countries / 1e9  # Convert to billions
        bars = ax.barh(range(len(top_revenue_countries_b)), top_revenue_countries_b.values, color='#A23B72')
        ax.set_yticks(range(len(top_revenue_countries_b)))
        ax.set_yticklabels(top_revenue_countries_b.index)
        ax.set_title('Top Countries\n[Revenue Generation]', fontweight='bold')
        ax.set_xlabel('Revenue ($B)')
        ax.grid(True, linestyle='--', alpha=0.7, axis='x')
        for i, val in enumerate(top_revenue_countries_b.values):
            x_offset = 2  # Fixed offset
            ax.text(val + x_offset, i, f'${val:.0f}B', ha='left', va='center', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Top Countries\n[Revenue Generation]', fontweight='bold')
    
    # 2.3 Top 5 Countries by Products Processing (Stage >0)
    ax = axes[1, 2]
    top_processing_countries = get_top_countries_by_metric(df_filtered, 'production_tonnes', top_n=5, processing_stage_filter='positive')
    if not top_processing_countries.empty:
        top_processing_countries_mt = top_processing_countries / 1e6  # Convert to Mt
        bars = ax.barh(range(len(top_processing_countries_mt)), top_processing_countries_mt.values, color='#F18F01')
        ax.set_yticks(range(len(top_processing_countries_mt)))
        ax.set_yticklabels(top_processing_countries_mt.index)
        ax.set_title('Top Countries\n[Products Processing]', fontweight='bold')
        ax.set_xlabel('Production (Mt)')
        ax.grid(True, linestyle='--', alpha=0.7, axis='x')
        for i, val in enumerate(top_processing_countries_mt.values):
            x_offset = 0.1  # Fixed offset
            ax.text(val + x_offset, i, f'{val:.1f}', ha='left', va='center', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No processing data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Top Countries\n[Products Processing]', fontweight='bold')
    
    # 2.4 Environmental Leaders (Lowest CO2 per Mt Production)
    ax = axes[1, 3]
    # Calculate CO2 efficiency (emissions per unit production)
    country_production = df_filtered.groupby('iso3')['production_tonnes'].sum()
    country_co2 = df_filtered.groupby('iso3')['total_co2'].sum()
    
    # Only consider countries with meaningful production (>1000 tonnes)
    meaningful_producers = country_production[country_production > 1000]
    if not meaningful_producers.empty:
        co2_efficiency = (country_co2[meaningful_producers.index] / meaningful_producers) * 1000  # CO2 per kt production
        top_efficient = co2_efficiency.sort_values().head(5)  # Lowest emissions per unit = most efficient
        
        if not top_efficient.empty:
            bars = ax.barh(range(len(top_efficient)), top_efficient.values, color='#2E8B57')
            ax.set_yticks(range(len(top_efficient)))
            ax.set_yticklabels(top_efficient.index)
            ax.set_title('Environmental Leaders\n[Lowest CO2/kt Production]', fontweight='bold')
            ax.set_xlabel('CO2 Efficiency (tonnes CO2/kt)')
            ax.grid(True, linestyle='--', alpha=0.7, axis='x')
            for i, val in enumerate(top_efficient.values):
                x_offset = 0.5  # Fixed offset
                ax.text(val + x_offset, i, f'{val:.1f}', ha='left', va='center', fontsize=8)
        else:
            ax.text(0.5, 0.5, 'No efficiency data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Environmental Leaders\n[Lowest CO2/kt Production]', fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No efficiency data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Environmental Leaders\n[Lowest CO2/kt Production]', fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.93], h_pad=3.0)
    
    # Save dashboard
    filename = f'GLOBAL_{constraint}_dashboard.png'
    dashboard_path = os.path.join(output_dir, filename)
    fig.savefig(dashboard_path, dpi=300, bbox_inches=None)
    plt.close(fig)
    
    print(f"✓ {constraint_names[constraint]} dashboard saved: {dashboard_path}")
    return dashboard_path

def create_global_policy_comparison_dashboard(df_all_countries, output_dir):
    """Create Global Policy Comparison Dashboard (2x4 layout)"""
    
    print("=== CREATING GLOBAL POLICY COMPARISONS DASHBOARD ===")
    
    # Use symmetric mid-scenario filtering
    df_analysis = get_mid_scenarios_symmetric(df_all_countries)
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    
    # Remove baseline for comparability
    df_analysis = df_analysis[df_analysis['goal_type'] != 'baseline'].copy()
    
    print(f"Global policy comparison data: {len(df_analysis)} records")
    
    # Create 2x4 subplot grid
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle('Critical Minerals - Global Policy Comparisons', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Color schemes
    constraint_colors = {'country': '#1f77b4', 'region': '#ff7f0e'}
    level_colors = {'constrained': '#d62728', 'unconstrained': '#2ca02c'}
    
    # === ROW 1: COUNTRY vs REGION POLICY COMPARISONS ===
    
    # 1.1 Production - Country vs Region (Unconstrained scenarios)
    ax = axes[0, 0]
    unconstrained_data = df_analysis[df_analysis['constraint'].str.contains('unconstrained')]
    chart_created = False
    
    if not unconstrained_data.empty:
        unconstrained_data = unconstrained_data.copy()
        unconstrained_data['constraint_type'] = unconstrained_data['constraint'].str.split('_').str[0]
        
        # Group by goal_type and constraint_type to show goal breakdown
        constraint_production = unconstrained_data.groupby(['goal_type', 'constraint_type'])['production_tonnes'].sum() / 1e6
        
        if not constraint_production.empty:
            constraint_production_pivot = constraint_production.unstack(level=1, fill_value=0)
            if not constraint_production_pivot.empty:
                constraint_production_pivot.plot(kind='bar', ax=ax,
                                               color=[constraint_colors.get(col, '#888888') 
                                                    for col in constraint_production_pivot.columns])
                ax.set_title('Production\nCountry vs Region (Unconstrained)', fontweight='bold')
                ax.set_ylabel('Production (Mt)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No unconstrained production data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Production\nCountry vs Region (Unconstrained)', fontweight='bold')
    
    # 1.2 Production - Country vs Region (Constrained scenarios)
    ax = axes[0, 1] 
    constrained_data = df_analysis[df_analysis['constraint'].str.contains('constrained') & ~df_analysis['constraint'].str.contains('unconstrained')]
    chart_created = False
    
    if not constrained_data.empty:
        constrained_data = constrained_data.copy()
        constrained_data['constraint_type'] = constrained_data['constraint'].str.split('_').str[0]
        
        # Group by goal_type and constraint_type to show goal breakdown
        constraint_production = constrained_data.groupby(['goal_type', 'constraint_type'])['production_tonnes'].sum() / 1e6
        
        if not constraint_production.empty:
            constraint_production_pivot = constraint_production.unstack(level=1, fill_value=0)
            if not constraint_production_pivot.empty:
                constraint_production_pivot.plot(kind='bar', ax=ax,
                                               color=[constraint_colors.get(col, '#888888') 
                                                    for col in constraint_production_pivot.columns])
                ax.set_title('Production\nCountry vs Region (Constrained)', fontweight='bold')
                ax.set_ylabel('Production (Mt)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No constrained production data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Production\nCountry vs Region (Constrained)', fontweight='bold')
    
    # 1.3 Revenue - Country vs Region (Unconstrained)
    ax = axes[0, 2]
    chart_created = False
    if not unconstrained_data.empty:
        # Group by goal_type and constraint_type to show goal breakdown
        constraint_revenue = unconstrained_data.groupby(['goal_type', 'constraint_type'])['revenue_usd'].sum() / 1e9
        
        if not constraint_revenue.empty:
            constraint_revenue_pivot = constraint_revenue.unstack(level=1, fill_value=0)
            if not constraint_revenue_pivot.empty:
                constraint_revenue_pivot.plot(kind='bar', ax=ax,
                                             color=[constraint_colors.get(col, '#888888') 
                                                  for col in constraint_revenue_pivot.columns])
                ax.set_title('Revenue\nCountry vs Region (Unconstrained)', fontweight='bold')
                ax.set_ylabel('Revenue ($B)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No unconstrained revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue\nCountry vs Region (Unconstrained)', fontweight='bold')
    
    # 1.4 Revenue - Country vs Region (Constrained)
    ax = axes[0, 3]
    chart_created = False
    if not constrained_data.empty:
        # Group by goal_type and constraint_type to show goal breakdown
        constraint_revenue = constrained_data.groupby(['goal_type', 'constraint_type'])['revenue_usd'].sum() / 1e9
        
        if not constraint_revenue.empty:
            constraint_revenue_pivot = constraint_revenue.unstack(level=1, fill_value=0)
            if not constraint_revenue_pivot.empty:
                constraint_revenue_pivot.plot(kind='bar', ax=ax,
                                             color=[constraint_colors.get(col, '#888888') 
                                                  for col in constraint_revenue_pivot.columns])
                ax.set_title('Revenue\nCountry vs Region (Constrained)', fontweight='bold')
                ax.set_ylabel('Revenue ($B)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No constrained revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue\nCountry vs Region (Constrained)', fontweight='bold')
    
    # === ROW 2: CONSTRAINED vs UNCONSTRAINED COMPARISONS ===
    
    # 2.1 CO2 Emissions - Constrained vs Unconstrained (Country)
    ax = axes[1, 0]
    country_data = df_analysis[df_analysis['constraint'].str.contains('country')].copy()
    chart_created = False
    
    if not country_data.empty:
        country_data['constraint_level'] = country_data['constraint'].str.split('_').str[1]
        country_data['total_co2'] = country_data['transport_total_tonsCO2eq'] + country_data['energy_tonsCO2eq']
        
        # Group by goal_type and constraint_level to show goal breakdown
        level_co2 = country_data.groupby(['goal_type', 'constraint_level'])['total_co2'].sum() / 1e3
        
        if not level_co2.empty:
            level_co2_pivot = level_co2.unstack(level=1, fill_value=0)
            if not level_co2_pivot.empty:
                level_co2_pivot.plot(kind='bar', ax=ax,
                                   color=[level_colors.get(col, '#888888') 
                                        for col in level_co2_pivot.columns])
                ax.set_title('CO2 Emissions\nConstrained vs Unconstrained (Country)', fontweight='bold')
                ax.set_ylabel('Emissions (kt CO2eq)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No country CO2 data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('CO2 Emissions\nConstrained vs Unconstrained (Country)', fontweight='bold')
    
    # 2.2 CO2 Emissions - Constrained vs Unconstrained (Region)
    ax = axes[1, 1]
    region_data = df_analysis[df_analysis['constraint'].str.contains('region')].copy()
    chart_created = False
    
    if not region_data.empty:
        region_data['constraint_level'] = region_data['constraint'].str.split('_').str[1]  
        region_data['total_co2'] = region_data['transport_total_tonsCO2eq'] + region_data['energy_tonsCO2eq']
        
        # Group by goal_type and constraint_level to show goal breakdown
        level_co2 = region_data.groupby(['goal_type', 'constraint_level'])['total_co2'].sum() / 1e3
        
        if not level_co2.empty:
            level_co2_pivot = level_co2.unstack(level=1, fill_value=0)
            if not level_co2_pivot.empty:
                level_co2_pivot.plot(kind='bar', ax=ax,
                                   color=[level_colors.get(col, '#888888') 
                                        for col in level_co2_pivot.columns])
                ax.set_title('CO2 Emissions\nConstrained vs Unconstrained (Region)', fontweight='bold')
                ax.set_ylabel('Emissions (kt CO2eq)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No region CO2 data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('CO2 Emissions\nConstrained vs Unconstrained (Region)', fontweight='bold')
    
    # 2.3 Water Usage - Constrained vs Unconstrained (Country)
    ax = axes[1, 2]
    chart_created = False
    
    if not country_data.empty:
        # Group by goal_type and constraint_level to show goal breakdown
        level_water = country_data.groupby(['goal_type', 'constraint_level'])['water_usage_m3'].sum() / 1e6
        
        if not level_water.empty:
            level_water_pivot = level_water.unstack(level=1, fill_value=0)
            if not level_water_pivot.empty:
                level_water_pivot.plot(kind='bar', ax=ax,
                                     color=[level_colors.get(col, '#888888') 
                                          for col in level_water_pivot.columns])
                ax.set_title('Water Usage\nConstrained vs Unconstrained (Country)', fontweight='bold') 
                ax.set_ylabel('Water Usage (M m³)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No country water data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Water Usage\nConstrained vs Unconstrained (Country)', fontweight='bold')
    
    # 2.4 Water Usage - Constrained vs Unconstrained (Region)
    ax = axes[1, 3]
    chart_created = False
    
    if not region_data.empty:
        # Group by goal_type and constraint_level to show goal breakdown
        level_water = region_data.groupby(['goal_type', 'constraint_level'])['water_usage_m3'].sum() / 1e6
        
        if not level_water.empty:
            level_water_pivot = level_water.unstack(level=1, fill_value=0)
            if not level_water_pivot.empty:
                level_water_pivot.plot(kind='bar', ax=ax,
                                     color=[level_colors.get(col, '#888888') 
                                          for col in level_water_pivot.columns])
                ax.set_title('Water Usage\nConstrained vs Unconstrained (Region)', fontweight='bold')
                ax.set_ylabel('Water Usage (M m³)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                chart_created = True
    
    if not chart_created:
        ax.text(0.5, 0.5, 'No region water data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Water Usage\nConstrained vs Unconstrained (Region)', fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save dashboard
    filename = 'GLOBAL_policy_comparisons_dashboard.png'
    dashboard_path = os.path.join(output_dir, filename)
    fig.savefig(dashboard_path, dpi=300, bbox_inches=None)
    plt.close(fig)
    
    print(f"✓ Global Policy Comparisons dashboard saved: {dashboard_path}")
    return dashboard_path

def create_global_pivot_summary_table(df_all_countries):
    """Create pivot-style summary table with global aggregated indicators"""
    
    # Add goal type and constraint type columns
    df_analysis = get_mid_scenarios_symmetric(df_all_countries)
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
            
            # Calculate aggregated metrics across all countries
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
            
            # CO2 emissions (transport + energy)
            co2_country = (country_data['transport_total_tonsCO2eq'].sum() + country_data['energy_tonsCO2eq'].sum()) / 1e3  # kt
            co2_region = (region_data['transport_total_tonsCO2eq'].sum() + region_data['energy_tonsCO2eq'].sum()) / 1e3    # kt
            
            # Transport volumes
            transport_country = country_data['transport_total_tonkm'].sum() / 1e6  # Million ton-km
            transport_region = region_data['transport_total_tonkm'].sum() / 1e6    # Million ton-km
            
            # Value addition
            df_va = calculate_global_value_addition(goal_data)
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

def generate_all_global_dashboards():
    """Generate all global dashboards and summary tables"""
    
    # Load configuration
    import json
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load all data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Filter to producing countries only (exclude UGA which has 0 production)
    producing_countries = []
    for country in df['iso3'].dropna().unique():
        country_data = df[df['iso3'] == country]
        if country_data['production_tonnes'].sum() > 0:
            producing_countries.append(country)
    
    df_producing = df[df['iso3'].isin(producing_countries)].copy()
    
    print(f"Loaded data for {len(producing_countries)} producing countries: {', '.join(sorted(producing_countries))}")
    print(f"Total records: {len(df_producing)}")
    
    # Create output directory
    output_dir = os.path.join(output_data_path, 'country_reports', 'global_dashboards')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Global dashboards output directory: {output_dir}")
    
    # Generate all 4 global constraint dashboards
    constraints = ['country_unconstrained', 'country_constrained', 'region_unconstrained', 'region_constrained']
    dashboard_paths = []
    
    for constraint in constraints:
        try:
            dashboard_path = create_global_constraint_dashboard(df_producing, constraint, output_dir)
            if dashboard_path:
                dashboard_paths.append(dashboard_path)
                print(f"✓ Generated: {os.path.basename(dashboard_path)}")
        except Exception as e:
            print(f"✗ Error generating {constraint} dashboard: {e}")
    
    # Generate global policy comparison dashboard  
    try:
        policy_dashboard_path = create_global_policy_comparison_dashboard(df_producing, output_dir)
        if policy_dashboard_path:
            dashboard_paths.append(policy_dashboard_path)
            print(f"✓ Generated: {os.path.basename(policy_dashboard_path)}")
    except Exception as e:
        print(f"✗ Error generating global policy comparison dashboard: {e}")
    
    # Generate global mineral breakdown dashboards for each constraint
    for constraint in constraints:
        try:
            mineral_dashboard_path = create_global_mineral_breakdown_dashboard(df_producing, constraint, output_dir)
            if mineral_dashboard_path:
                dashboard_paths.append(mineral_dashboard_path)
                print(f"✓ Generated: {os.path.basename(mineral_dashboard_path)}")
        except Exception as e:
            print(f"✗ Error generating {constraint} mineral breakdown dashboard: {e}")
    
    # Generate global summary table
    try:
        global_summary = create_global_pivot_summary_table(df_producing)
        summary_filename = 'GLOBAL_all_constraints_summary_table.csv'
        summary_path = os.path.join(output_dir, summary_filename)
        global_summary.to_csv(summary_path, index=False)
        print(f"✓ Generated: {summary_filename}")
    except Exception as e:
        print(f"✗ Error generating global summary table: {e}")
    
    # Final summary
    print(f"\n{'='*60}")
    print("GLOBAL DASHBOARDS GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Generated {len(dashboard_paths)} dashboards")
    print(f"✓ Output directory: {output_dir}")
    
    # List all generated files
    generated_files = os.listdir(output_dir)
    print(f"✓ Generated files ({len(generated_files)}):")
    for file in sorted(generated_files):
        file_path = os.path.join(output_dir, file)
        file_size = os.path.getsize(file_path)
        print(f"  - {file} ({file_size:,} bytes)")
    
    return output_dir

def create_global_mineral_breakdown_dashboard(df_constraint, constraint, output_dir):
    """Create mineral breakdown dashboard for specific constraint"""
    
    print(f"=== CREATING GLOBAL MINERAL BREAKDOWN DASHBOARD - {constraint.upper()} ===")
    
    # Filter to mid-scenarios for consistency
    df_analysis = get_mid_scenarios_symmetric(df_constraint)
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    
    # Filter to specific constraint
    df_analysis = df_analysis[df_analysis['constraint'] == constraint].copy()
    
    print(f"Mineral breakdown data: {len(df_analysis)} records for {constraint}")
    
    # Create 2x4 subplot grid
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    constraint_title = constraint.replace('_', ' ').title()
    fig.suptitle(f'Critical Minerals - Global Mineral Breakdown ({constraint_title})', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Import mineral colors and country colors
    from plot_config import reference_minerals, reference_minerals_short, reference_mineral_colormap
    from plot_utils import generate_country_colormap
    
    # === ROW 1: PRODUCTION & GOAL ACHIEVEMENT ===
    
    # 1.1 Metal Content by Mineral & Goal (Stage 0)
    ax = axes[0, 0]
    metal_content = df_analysis[df_analysis['processing_stage'] == 0]
    
    if not metal_content.empty:
        # Group by mineral and goal to show goal breakdown
        mineral_goal_metal = metal_content.groupby(['reference_mineral', 'goal_type'])['production_tonnes'].sum() / 1e6
        metal_pivot = mineral_goal_metal.unstack(level=1, fill_value=0)
        # Remove baseline if present
        if 'baseline' in metal_pivot.columns:
            metal_pivot = metal_pivot.drop('baseline', axis=1)
        
        if not metal_pivot.empty:
            metal_pivot.plot(kind='bar', ax=ax, width=0.8)
            ax.set_title('Metal Content by Mineral & Goal\n[Stage 0 - By Goal]', fontweight='bold')
            ax.set_ylabel('Production (Mt)')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Goal', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        else:
            ax.text(0.5, 0.5, 'No metal content data', ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'No metal content data', ha='center', va='center', transform=ax.transAxes)
    
    # 1.2 Products Production by Mineral & Goal (Stages > 0)
    ax = axes[0, 1]
    products_data = df_analysis[df_analysis['processing_stage'] > 0]
    
    if not products_data.empty:
        # Get products production by mineral and goal
        products_by_goal = products_data.groupby(['reference_mineral', 'goal_type'])['production_tonnes'].sum() / 1e6
        
        if not products_by_goal.empty:
            products_pivot = products_by_goal.unstack(level=1, fill_value=0)
            # Remove baseline if present
            if 'baseline' in products_pivot.columns:
                products_pivot = products_pivot.drop('baseline', axis=1)
            
            products_pivot.plot(kind='bar', ax=ax, width=0.8)
            ax.set_title('Products Production by Mineral\n[Stages > 0 - By Goal]', fontweight='bold')
            ax.set_ylabel('Production (Mt)')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Goal', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        else:
            ax.text(0.5, 0.5, 'No products data', ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'No products data', ha='center', va='center', transform=ax.transAxes)
    
    # 1.3 Revenue by Goal & Mineral (Stacked)
    ax = axes[0, 2]
    revenue_by_goal = df_analysis.groupby(['goal_type', 'reference_mineral'])['revenue_usd'].sum() / 1e9
    
    if not revenue_by_goal.empty:
        revenue_pivot = revenue_by_goal.unstack(level=1, fill_value=0)
        colors = [reference_mineral_colormap.get(m, '#999999') for m in revenue_pivot.columns]
        revenue_pivot.plot(kind='bar', stacked=True, ax=ax, color=colors)
        ax.set_title('Revenue by Goal & Mineral\n[Stacked by Mineral]', fontweight='bold')
        ax.set_ylabel('Revenue ($B)')
        ax.tick_params(axis='x', rotation=45)
        ax.legend(title='Mineral', bbox_to_anchor=(1.05, 1), loc='upper left', ncol=1)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    else:
        ax.text(0.5, 0.5, 'No revenue data', ha='center', va='center', transform=ax.transAxes)
    
    # 1.4 Processing Stage Distribution by Goal (Stages > 0 only)
    ax = axes[0, 3]
    # Get production by goal, mineral and processing stage (exclude stage 0)
    products_stage_data = df_analysis[df_analysis['processing_stage'] > 0]
    
    if not products_stage_data.empty:
        # Create a combined chart showing stage distribution by goal
        goal_stage_production = products_stage_data.groupby(['goal_type', 'processing_stage'])['production_tonnes'].sum() / 1e6
        
        if not goal_stage_production.empty:
            goal_stage_pivot = goal_stage_production.unstack(level=0, fill_value=0)
            # Remove baseline if present
            if 'baseline' in goal_stage_pivot.columns:
                goal_stage_pivot = goal_stage_pivot.drop('baseline', axis=1)
            
            goal_stage_pivot.plot(kind='bar', ax=ax, width=0.8)
            ax.set_title('Processing Stage Distribution\n[Products Only - By Goal]', fontweight='bold')
            ax.set_xlabel('Processing Stage')
            ax.set_ylabel('Production (Mt)')
            ax.tick_params(axis='x', rotation=45)
            ax.legend(title='Goal', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        else:
            ax.text(0.5, 0.5, 'No processing stage data', ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'No processing stage data', ha='center', va='center', transform=ax.transAxes)
    
    # === ROW 2: GEOGRAPHIC & ENVIRONMENTAL ANALYSIS ===
    
    # 2.1 Top Countries by Mineral & Goal (Total Production - All Stages)
    ax = axes[1, 0]
    # Focus on major goals and aggregate countries by goal
    goal_country_prod = df_analysis.groupby(['goal_type', 'iso3'])['production_tonnes'].sum() / 1e6
    
    if not goal_country_prod.empty:
        goal_country_pivot = goal_country_prod.unstack(level=0, fill_value=0)
        # Remove baseline if present
        if 'baseline' in goal_country_pivot.columns:
            goal_country_pivot = goal_country_pivot.drop('baseline', axis=1)
        
        # Get top 8 producing countries
        country_totals = goal_country_pivot.sum(axis=1).sort_values(ascending=False).head(8)
        top_countries_pivot = goal_country_pivot.loc[country_totals.index]
        
        if not top_countries_pivot.empty:
            # Use country color mapping for bars but make goals different patterns/hatches
            top_countries_pivot.plot(kind='barh', ax=ax, width=0.8)
            ax.set_title('Top Countries by Goal\n[All Stages - By Goal]', fontweight='bold')
            ax.set_xlabel('Production (Mt)')
            ax.legend(title='Goal', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.7, axis='x')
        else:
            ax.text(0.5, 0.5, 'No country data', ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'No country data', ha='center', va='center', transform=ax.transAxes)
    
    # 2.2 Value Addition by Mineral
    ax = axes[1, 1]
    df_va = calculate_global_value_addition(df_analysis)
    
    if not df_va.empty:
        va_by_mineral = df_va.groupby('reference_mineral')['value_added_musd'].sum()
        va_by_mineral = va_by_mineral.sort_values(ascending=False)
        
        colors = [reference_mineral_colormap.get(m, '#999999') for m in va_by_mineral.index]
        bars = ax.bar(va_by_mineral.index, va_by_mineral.values, color=colors)
        ax.set_title('Value Addition by Mineral\n[Million USD]', fontweight='bold')
        ax.set_ylabel('Value Added (M$)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        # Add value labels
        for bar, val in zip(bars, va_by_mineral.values):
            if val != 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (va_by_mineral.max() * 0.02),
                       f'{val:.0f}', ha='center', va='bottom', fontsize=8)
    else:
        ax.text(0.5, 0.5, 'No value addition data', ha='center', va='center', transform=ax.transAxes)
    
    # 2.3 Environmental Intensity per Tonne
    ax = axes[1, 2]
    mineral_totals = df_analysis.groupby('reference_mineral').agg({
        'production_tonnes': 'sum',
        'water_usage_m3': 'sum',
        'transport_total_tonsCO2eq': 'sum',
        'energy_tonsCO2eq': 'sum'
    })
    
    if not mineral_totals.empty and mineral_totals['production_tonnes'].sum() > 0:
        mineral_totals = mineral_totals[mineral_totals['production_tonnes'] > 0]  # Filter out zero production
        mineral_totals['total_co2'] = mineral_totals['transport_total_tonsCO2eq'] + mineral_totals['energy_tonsCO2eq']
        mineral_totals['water_intensity'] = mineral_totals['water_usage_m3'] / mineral_totals['production_tonnes']
        mineral_totals['co2_intensity'] = mineral_totals['total_co2'] / mineral_totals['production_tonnes']
        
        colors = [reference_mineral_colormap.get(m, '#999999') for m in mineral_totals.index]
        sizes = (mineral_totals['production_tonnes'] / mineral_totals['production_tonnes'].max() * 300) + 50
        
        scatter = ax.scatter(mineral_totals['water_intensity'], 
                           mineral_totals['co2_intensity'],
                           s=sizes, c=colors, alpha=0.7, edgecolors='black', linewidth=1)
        
        ax.set_xlabel('Water Intensity (m³/tonne)')
        ax.set_ylabel('CO₂ Intensity (kg/tonne)')
        ax.set_title('Environmental Intensity\n[Size = Production Volume]', fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add mineral labels
        for mineral, row in mineral_totals.iterrows():
            ax.annotate(reference_minerals_short[reference_minerals.index(mineral)], 
                       (row['water_intensity'], row['co2_intensity']),
                       xytext=(5, 5), textcoords='offset points', fontsize=9, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No environmental data', ha='center', va='center', transform=ax.transAxes)
    
    # 2.4 Goal Achievement Summary Table
    ax = axes[1, 3]
    ax.axis('off')
    
    # Create summary table
    summary_data = []
    for mineral in reference_minerals:
        row_data = {'Mineral': reference_minerals_short[reference_minerals.index(mineral)]}
        # Map goal types to expected format for target stage lookup
        goal_mapping = {
            'bau': 'Beneficiation',
            'early_refining': 'Early refining', 
            'precursor': 'Precursor related product'
        }
        
        for goal in ['bau', 'early_refining', 'precursor']:
            mineral_goal_data = df_analysis[
                (df_analysis['reference_mineral'] == mineral) & 
                (df_analysis['goal_type'] == goal)
            ]
            if not mineral_goal_data.empty:
                total_prod = mineral_goal_data['production_tonnes'].sum()
                from plot_config import get_target_stage_for_goal
                mapped_goal = goal_mapping.get(goal, goal)
                target_stage = get_target_stage_for_goal(mineral, mapped_goal)
                if target_stage and total_prod > 0:
                    target_prod = mineral_goal_data[
                        mineral_goal_data['processing_stage'] == target_stage
                    ]['production_tonnes'].sum()
                    achievement_pct = (target_prod / total_prod) * 100
                    row_data[goal.upper()[:3]] = f'{achievement_pct:.0f}%'
                else:
                    row_data[goal.upper()[:3]] = '0%'
            else:
                row_data[goal.upper()[:3]] = 'N/A'
        summary_data.append(row_data)
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # Create table
        table = ax.table(cellText=summary_df.values,
                        colLabels=summary_df.columns,
                        cellLoc='center',
                        loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Color code cells based on achievement
        for i in range(1, len(summary_df) + 1):
            for j in range(1, len(summary_df.columns)):
                cell = table[(i, j)]
                text = cell.get_text().get_text()
                if text != 'N/A':
                    try:
                        value = float(text.strip('%'))
                        if value >= 80:
                            cell.set_facecolor('#90EE90')  # Light green
                        elif value >= 50:
                            cell.set_facecolor('#FFFFE0')  # Light yellow
                        else:
                            cell.set_facecolor('#FFB6C1')  # Light red
                    except:
                        pass
        
        ax.set_title('Goal Achievement Summary\n[% Production at Target Stage]', 
                    fontweight='bold', y=0.95)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save dashboard
    filename = f'GLOBAL_{constraint}_mineral_breakdown_dashboard.png'
    dashboard_path = os.path.join(output_dir, filename)
    fig.savefig(dashboard_path, dpi=300, bbox_inches=None)
    plt.close(fig)
    
    print(f"✓ Global Mineral Breakdown dashboard saved: {dashboard_path}")
    print(f"✓ Generated: {filename}")
    
    return dashboard_path

if __name__ == "__main__":
    generate_all_global_dashboards()