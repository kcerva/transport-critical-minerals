#!/usr/bin/env python3
"""
Debug script for global policy comparison dashboard
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from plot_config import get_goal_from_scenario

def debug_policy_data():
    """Debug the policy comparison data to understand what's not working"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load all data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Filter to producing countries only
    producing_countries = []
    for country in df['iso3'].dropna().unique():
        country_data = df[df['iso3'] == country]
        if country_data['production_tonnes'].sum() > 0:
            producing_countries.append(country)
    
    df_producing = df[df['iso3'].isin(producing_countries)].copy()
    print(f"Loaded data for {len(producing_countries)} producing countries")
    
    # Get mid-scenarios
    mid_scenarios = df_producing[
        (df_producing['scenario'].str.contains('mid_min|mid_max', na=False)) |
        (df_producing['scenario'] == '2022_baseline')
    ].copy()
    
    mid_scenarios['goal_type'] = mid_scenarios['scenario'].apply(get_goal_from_scenario)
    # Remove baseline for comparability
    df_analysis = mid_scenarios[mid_scenarios['goal_type'] != 'baseline'].copy()
    
    print(f"\nPolicy comparison data: {len(df_analysis)} records after filtering")
    
    # Debug constraints
    print(f"\nUnique constraints: {df_analysis['constraint'].unique()}")
    
    # Check unconstrained data
    unconstrained_data = df_analysis[df_analysis['constraint'].str.contains('unconstrained')]
    print(f"\nUnconstrained data: {len(unconstrained_data)} records")
    
    if not unconstrained_data.empty:
        unconstrained_data['constraint_type'] = unconstrained_data['constraint'].str.split('_').str[0]
        print(f"Constraint types in unconstrained: {unconstrained_data['constraint_type'].unique()}")
        
        # Check production by constraint type
        constraint_production = unconstrained_data.groupby('constraint_type')['production_tonnes'].sum() / 1e6
        print(f"Production by constraint type (unconstrained):")
        for ct, prod in constraint_production.items():
            print(f"  {ct}: {prod:.2f} Mt")
        
        # Check revenue by constraint type
        constraint_revenue = unconstrained_data.groupby('constraint_type')['revenue_usd'].sum() / 1e9
        print(f"Revenue by constraint type (unconstrained):")
        for ct, rev in constraint_revenue.items():
            print(f"  {ct}: ${rev:.1f}B")
    
    # Check constrained data
    constrained_data = df_analysis[df_analysis['constraint'].str.contains('constrained') & ~df_analysis['constraint'].str.contains('unconstrained')]
    print(f"\nConstrained data: {len(constrained_data)} records")
    
    if not constrained_data.empty:
        constrained_data['constraint_type'] = constrained_data['constraint'].str.split('_').str[0]
        print(f"Constraint types in constrained: {constrained_data['constraint_type'].unique()}")
        
        # Check production by constraint type
        constraint_production = constrained_data.groupby('constraint_type')['production_tonnes'].sum() / 1e6
        print(f"Production by constraint type (constrained):")
        for ct, prod in constraint_production.items():
            print(f"  {ct}: {prod:.2f} Mt")
    
    # Check country vs region data
    country_data = df_analysis[df_analysis['constraint'].str.contains('country')]
    region_data = df_analysis[df_analysis['constraint'].str.contains('region')]
    
    print(f"\nCountry policy data: {len(country_data)} records")
    print(f"Region policy data: {len(region_data)} records")
    
    if not country_data.empty:
        country_data['constraint_level'] = country_data['constraint'].str.split('_').str[1]
        print(f"Country constraint levels: {country_data['constraint_level'].unique()}")
        
    if not region_data.empty:
        region_data['constraint_level'] = region_data['constraint'].str.split('_').str[1]
        print(f"Region constraint levels: {region_data['constraint_level'].unique()}")

if __name__ == "__main__":
    debug_policy_data()