"""
Dashboard 5: Policy Comparisons - Specific Constraint Combinations
Row 1: Country vs Region Comparisons (Unconstrained & Constrained)
Row 2: Constrained vs Unconstrained Comparisons (Country & Region)
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

from plot_config import get_goal_from_scenario

def get_mid_scenarios_symmetric(df_country):
    """Get mid-scenarios with symmetric filtering logic"""
    mid_scenarios = df_country[
        (df_country['scenario'].str.contains('mid_min|mid_max', na=False)) |
        (df_country['scenario'] == '2022_baseline')
    ].copy()
    
    return mid_scenarios

def create_policy_comparison_dashboard(df_country, output_dir, country_name="Country"):
    """Create Dashboard 5: Policy Comparisons (2x4 layout)"""
    
    print("=== CREATING POLICY COMPARISONS DASHBOARD ===")
    
    # Use symmetric mid-scenario filtering
    df_analysis = get_mid_scenarios_symmetric(df_country)
    df_analysis['goal_type'] = df_analysis['scenario'].apply(get_goal_from_scenario)
    
    # Remove baseline for comparability - baseline has mixed processing stages
    # while other goals are focused on target stages
    df_analysis = df_analysis[df_analysis['goal_type'] != 'baseline'].copy()
    
    print(f"Policy comparison data: {len(df_analysis)} records")
    
    # Create 2x4 subplot grid
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle(f'{country_name} Critical Minerals - Policy Comparisons', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Color schemes
    constraint_colors = {'country': '#1f77b4', 'region': '#ff7f0e'}
    level_colors = {'constrained': '#d62728', 'unconstrained': '#2ca02c'}
    
    # === ROW 1: COUNTRY vs REGION COMPARISONS ===
    
    # 1.1 Products Production - Country vs Region (Unconstrained scenarios)
    ax = axes[0, 0]
    unconstrained_data = df_analysis[df_analysis['constraint'].str.contains('unconstrained')]
    if not unconstrained_data.empty:
        unconstrained_data['constraint_type'] = unconstrained_data['constraint'].str.split('_').str[0]
        # Use Products Production (Stage >0) as most representative
        unconstrained_products = unconstrained_data[unconstrained_data['processing_stage'] > 0]
        policy_prod_unc = unconstrained_products.groupby(['goal_type', 'constraint_type'])['production_tonnes'].sum() / 1e6
        
        if not policy_prod_unc.empty:
            policy_prod_unc_pivot = policy_prod_unc.unstack(level=1, fill_value=0)
            if not policy_prod_unc_pivot.empty:
                policy_prod_unc_pivot.plot(kind='bar', ax=ax, 
                                         color=[constraint_colors.get(col, '#888888') 
                                              for col in policy_prod_unc_pivot.columns])
                ax.set_title('Products Production\nCountry vs Region (Unconstrained)', fontweight='bold')
                ax.set_ylabel('Production (Mt)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No unconstrained production data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Products Production\nCountry vs Region (Unconstrained)', fontweight='bold')
    
    # 1.2 Revenue - Country vs Region (Unconstrained scenarios)
    ax = axes[0, 1]
    if not unconstrained_data.empty:
        policy_rev_unc = unconstrained_data.groupby(['goal_type', 'constraint_type'])['revenue_usd'].sum() / 1e9
        
        if not policy_rev_unc.empty:
            policy_rev_unc_pivot = policy_rev_unc.unstack(level=1, fill_value=0)
            if not policy_rev_unc_pivot.empty:
                policy_rev_unc_pivot.plot(kind='bar', ax=ax,
                                        color=[constraint_colors.get(col, '#888888') 
                                             for col in policy_rev_unc_pivot.columns])
                ax.set_title('Revenue\nCountry vs Region (Unconstrained)', fontweight='bold')
                ax.set_ylabel('Revenue ($B)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No unconstrained revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue\nCountry vs Region (Unconstrained)', fontweight='bold')
    
    # 1.3 Products Production - Country vs Region (Constrained scenarios)
    ax = axes[0, 2]
    constrained_data = df_analysis[df_analysis['constraint'].str.contains('constrained')]
    if not constrained_data.empty:
        constrained_data['constraint_type'] = constrained_data['constraint'].str.split('_').str[0]
        # Use Products Production (Stage >0) as most representative
        constrained_products = constrained_data[constrained_data['processing_stage'] > 0]
        policy_prod_con = constrained_products.groupby(['goal_type', 'constraint_type'])['production_tonnes'].sum() / 1e6
        
        if not policy_prod_con.empty:
            policy_prod_con_pivot = policy_prod_con.unstack(level=1, fill_value=0)
            if not policy_prod_con_pivot.empty:
                policy_prod_con_pivot.plot(kind='bar', ax=ax,
                                         color=[constraint_colors.get(col, '#888888') 
                                              for col in policy_prod_con_pivot.columns])
                ax.set_title('Products Production\nCountry vs Region (Constrained)', fontweight='bold')
                ax.set_ylabel('Production (Mt)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No constrained production data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Products Production\nCountry vs Region (Constrained)', fontweight='bold')
    
    # 1.4 Revenue - Country vs Region (Constrained scenarios)
    ax = axes[0, 3]
    if not constrained_data.empty:
        policy_rev_con = constrained_data.groupby(['goal_type', 'constraint_type'])['revenue_usd'].sum() / 1e9
        
        if not policy_rev_con.empty:
            policy_rev_con_pivot = policy_rev_con.unstack(level=1, fill_value=0)
            if not policy_rev_con_pivot.empty:
                policy_rev_con_pivot.plot(kind='bar', ax=ax,
                                        color=[constraint_colors.get(col, '#888888') 
                                             for col in policy_rev_con_pivot.columns])
                ax.set_title('Revenue\nCountry vs Region (Constrained)', fontweight='bold')
                ax.set_ylabel('Revenue ($B)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Policy Focus')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No constrained revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue\nCountry vs Region (Constrained)', fontweight='bold')
    
    # === ROW 2: CONSTRAINED vs UNCONSTRAINED COMPARISONS ===
    
    # 2.1 Production - Constrained vs Unconstrained (Country policies)
    ax = axes[1, 0]
    country_data = df_analysis[df_analysis['constraint'].str.contains('country')]
    if not country_data.empty:
        country_data['constraint_level'] = country_data['constraint'].str.split('_').str[1]
        # Use Products Production (Stage >0) as most representative
        country_products = country_data[country_data['processing_stage'] > 0]
        country_prod_level = country_products.groupby(['goal_type', 'constraint_level'])['production_tonnes'].sum() / 1e6
        
        if not country_prod_level.empty:
            country_prod_pivot = country_prod_level.unstack(level=1, fill_value=0)
            if not country_prod_pivot.empty:
                country_prod_pivot.plot(kind='bar', ax=ax,
                                      color=[level_colors.get(col, '#888888') 
                                           for col in country_prod_pivot.columns])
                ax.set_title('Products Production\nConstrained vs Unconstrained (Country)', fontweight='bold')
                ax.set_ylabel('Production (Mt)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No country production data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Products Production\nConstrained vs Unconstrained (Country)', fontweight='bold')
    
    # 2.2 Revenue - Constrained vs Unconstrained (Country policies)
    ax = axes[1, 1]
    if not country_data.empty:
        country_rev_level = country_data.groupby(['goal_type', 'constraint_level'])['revenue_usd'].sum() / 1e9
        
        if not country_rev_level.empty:
            country_rev_pivot = country_rev_level.unstack(level=1, fill_value=0)
            if not country_rev_pivot.empty:
                country_rev_pivot.plot(kind='bar', ax=ax,
                                     color=[level_colors.get(col, '#888888') 
                                          for col in country_rev_pivot.columns])
                ax.set_title('Revenue\nConstrained vs Unconstrained (Country)', fontweight='bold')
                ax.set_ylabel('Revenue ($B)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No country revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue\nConstrained vs Unconstrained (Country)', fontweight='bold')
    
    # 2.3 Production - Constrained vs Unconstrained (Region policies)
    ax = axes[1, 2]
    region_data = df_analysis[df_analysis['constraint'].str.contains('region')]
    if not region_data.empty:
        region_data['constraint_level'] = region_data['constraint'].str.split('_').str[1]
        # Use Products Production (Stage >0) as most representative
        region_products = region_data[region_data['processing_stage'] > 0]
        region_prod_level = region_products.groupby(['goal_type', 'constraint_level'])['production_tonnes'].sum() / 1e6
        
        if not region_prod_level.empty:
            region_prod_pivot = region_prod_level.unstack(level=1, fill_value=0)
            if not region_prod_pivot.empty:
                region_prod_pivot.plot(kind='bar', ax=ax,
                                     color=[level_colors.get(col, '#888888') 
                                          for col in region_prod_pivot.columns])
                ax.set_title('Products Production\nConstrained vs Unconstrained (Region)', fontweight='bold')
                ax.set_ylabel('Production (Mt)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No region production data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Products Production\nConstrained vs Unconstrained (Region)', fontweight='bold')
    
    # 2.4 Revenue - Constrained vs Unconstrained (Region policies)
    ax = axes[1, 3]
    if not region_data.empty:
        region_rev_level = region_data.groupby(['goal_type', 'constraint_level'])['revenue_usd'].sum() / 1e9
        
        if not region_rev_level.empty:
            region_rev_pivot = region_rev_level.unstack(level=1, fill_value=0)
            if not region_rev_pivot.empty:
                region_rev_pivot.plot(kind='bar', ax=ax,
                                    color=[level_colors.get(col, '#888888') 
                                         for col in region_rev_pivot.columns])
                ax.set_title('Revenue\nConstrained vs Unconstrained (Region)', fontweight='bold')
                ax.set_ylabel('Revenue ($B)')
                ax.tick_params(axis='x', rotation=45)
                ax.legend(title='Constraint Level')
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    if ax.get_legend() is None:
        ax.text(0.5, 0.5, 'No region revenue data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Revenue\nConstrained vs Unconstrained (Region)', fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save dashboard
    country_code = df_country['iso3'].iloc[0].upper() if not df_country.empty else 'COUNTRY'
    filename = f'{country_code}_policy_comparisons_dashboard.png'
    dashboard_path = os.path.join(output_dir, filename)
    fig.savefig(dashboard_path, dpi=300, bbox_inches=None)
    plt.close(fig)
    
    print(f"✓ Policy Comparisons dashboard saved: {dashboard_path}")
    return dashboard_path

def test_policy_comparison_dashboard():
    """Test the policy comparison dashboard"""
    
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
    
    # Create policy comparison dashboard
    country_name = df_country['country_name'].iloc[0] if 'country_name' in df_country.columns and not df_country.empty else 'Zambia'
    dashboard_path = create_policy_comparison_dashboard(df_country, output_dir, country_name)
    
    print(f"\n✓ Policy comparison dashboard generated in: {output_dir}")
    return output_dir

if __name__ == "__main__":
    test_policy_comparison_dashboard()