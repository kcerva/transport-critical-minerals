"""
Analyze the impact of changing value addition calculation from production_tonnes to production_tonnes_for_costs
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

def calc_value_added_old(group):
    """Old calculation using production_tonnes"""
    group = group.sort_values(by='processing_stage').copy()
    group["value_added_old"] = 0.0
    for i in range(1, len(group)):
        prev = group.iloc[i - 1]
        curr = group.iloc[i]
        if prev["production_tonnes"] > 0:
            group.at[curr.name, "value_added_old"] = (
                (curr["price_usd_per_tonne"] * curr["production_tonnes"]) -
                (prev["production_cost_usd_per_tonne"] * prev["production_tonnes"])
            )
    return group

def calc_value_added_new(group):
    """New calculation using production_tonnes_for_costs"""
    group = group.sort_values(by='processing_stage').copy()
    group["value_added_new"] = 0.0
    for i in range(1, len(group)):
        prev = group.iloc[i - 1]
        curr = group.iloc[i]
        if prev["production_tonnes_for_costs"] > 0:
            group.at[curr.name, "value_added_new"] = (
                (curr["price_usd_per_tonne"] * curr["production_tonnes_for_costs"]) -
                (prev["production_cost_usd_per_tonne"] * prev["production_tonnes_for_costs"])
            )
    return group

def analyze_value_addition_changes():
    """Compare old vs new value addition calculations"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Filter to processing stage > 0 (value addition only applies to processed products)
    df_va = df[df["processing_stage"] > 0].copy()
    
    print(f"Analyzing value addition for {len(df_va)} records with processing_stage > 0")
    
    # Check if columns exist
    print("\nColumn check:")
    print(f"- production_tonnes exists: {'production_tonnes' in df_va.columns}")
    print(f"- production_tonnes_for_costs exists: {'production_tonnes_for_costs' in df_va.columns}")
    print(f"- price_usd_per_tonne exists: {'price_usd_per_tonne' in df_va.columns}")
    print(f"- production_cost_usd_per_tonne exists: {'production_cost_usd_per_tonne' in df_va.columns}")
    
    # Sample data comparison
    print("\nSample data comparison (first 5 rows):")
    sample_cols = ['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 
                   'production_tonnes', 'production_tonnes_for_costs', 'price_usd_per_tonne', 
                   'production_cost_usd_per_tonne']
    print(df_va[sample_cols].head())
    
    # Calculate ratio of production_tonnes_for_costs to production_tonnes
    df_va['production_ratio'] = df_va['production_tonnes_for_costs'] / df_va['production_tonnes']
    
    print("\nProduction tonnes ratio analysis:")
    print(f"Mean ratio (production_tonnes_for_costs / production_tonnes): {df_va['production_ratio'].mean():.4f}")
    print(f"Median ratio: {df_va['production_ratio'].median():.4f}")
    print(f"Min ratio: {df_va['production_ratio'].min():.4f}")
    print(f"Max ratio: {df_va['production_ratio'].max():.4f}")
    print(f"Std deviation: {df_va['production_ratio'].std():.4f}")
    
    # Group and calculate both old and new value additions
    print("\nCalculating value additions...")
    
    # Apply both calculations
    df_old = df_va.groupby(['scenario', 'constraint', 'iso3', 'reference_mineral'], 
                          group_keys=False).apply(calc_value_added_old)
    df_new = df_va.groupby(['scenario', 'constraint', 'iso3', 'reference_mineral'], 
                          group_keys=False).apply(calc_value_added_new)
    
    # Merge results
    df_comparison = pd.merge(
        df_old[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 'value_added_old']],
        df_new[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 'value_added_new']],
        on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage'],
        how='outer'
    )
    
    # Calculate differences
    df_comparison['value_added_diff'] = df_comparison['value_added_new'] - df_comparison['value_added_old']
    df_comparison['value_added_pct_change'] = (df_comparison['value_added_diff'] / df_comparison['value_added_old'].abs()) * 100
    
    # Filter out zeros for meaningful comparison
    df_nonzero = df_comparison[(df_comparison['value_added_old'] != 0) | (df_comparison['value_added_new'] != 0)]
    
    print(f"\nValue addition comparison ({len(df_nonzero)} non-zero records):")
    print(f"Total value added (old method): ${df_nonzero['value_added_old'].sum()/1e6:.2f} million")
    print(f"Total value added (new method): ${df_nonzero['value_added_new'].sum()/1e6:.2f} million")
    print(f"Total difference: ${df_nonzero['value_added_diff'].sum()/1e6:.2f} million")
    print(f"Percentage change: {(df_nonzero['value_added_diff'].sum() / df_nonzero['value_added_old'].sum()) * 100:.2f}%")
    
    # By mineral
    print("\nValue addition changes by mineral (million USD):")
    mineral_comparison = df_nonzero.groupby('reference_mineral').agg({
        'value_added_old': lambda x: x.sum()/1e6,
        'value_added_new': lambda x: x.sum()/1e6,
        'value_added_diff': lambda x: x.sum()/1e6
    }).round(2)
    mineral_comparison['pct_change'] = ((mineral_comparison['value_added_new'] / mineral_comparison['value_added_old']) - 1) * 100
    print(mineral_comparison.sort_values('value_added_diff', ascending=False))
    
    # By constraint
    print("\nValue addition changes by constraint (million USD):")
    constraint_comparison = df_nonzero.groupby('constraint').agg({
        'value_added_old': lambda x: x.sum()/1e6,
        'value_added_new': lambda x: x.sum()/1e6,
        'value_added_diff': lambda x: x.sum()/1e6
    }).round(2)
    constraint_comparison['pct_change'] = ((constraint_comparison['value_added_new'] / constraint_comparison['value_added_old']) - 1) * 100
    print(constraint_comparison)
    
    # By processing stage
    print("\nValue addition changes by processing stage (million USD):")
    stage_comparison = df_nonzero.groupby('processing_stage').agg({
        'value_added_old': lambda x: x.sum()/1e6,
        'value_added_new': lambda x: x.sum()/1e6,
        'value_added_diff': lambda x: x.sum()/1e6
    }).round(2)
    stage_comparison['pct_change'] = ((stage_comparison['value_added_new'] / stage_comparison['value_added_old']) - 1) * 100
    print(stage_comparison.sort_values('processing_stage'))
    
    # Save detailed comparison
    output_file = os.path.join(output_data_path, 'value_addition_comparison.xlsx')
    with pd.ExcelWriter(output_file) as writer:
        df_comparison.to_excel(writer, sheet_name='Detailed_Comparison', index=False)
        mineral_comparison.to_excel(writer, sheet_name='By_Mineral')
        constraint_comparison.to_excel(writer, sheet_name='By_Constraint')
        stage_comparison.to_excel(writer, sheet_name='By_Stage')
    
    print(f"\nDetailed comparison saved to: {output_file}")
    
    # Find extreme cases
    print("\nExtreme cases (largest percentage changes):")
    extreme_cases = df_nonzero[df_nonzero['value_added_pct_change'].abs() > 10].sort_values('value_added_pct_change', ascending=False)
    if not extreme_cases.empty:
        print(extreme_cases[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 
                            'value_added_old', 'value_added_new', 'value_added_pct_change']].head(10))
    else:
        print("No extreme cases found (>10% change)")

if __name__ == "__main__":
    analyze_value_addition_changes()