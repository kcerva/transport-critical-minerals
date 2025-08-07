"""
Debug stage flow connectivity issues
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
from global_constraint_dashboards import get_mid_scenarios_symmetric

def debug_stage_flows():
    """Debug why stages appear disconnected"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Filter to mid scenarios
    df_mid = get_mid_scenarios_symmetric(df)
    df_mid['goal_type'] = df_mid['scenario'].apply(get_goal_from_scenario)
    
    # Focus on a specific case for debugging
    df_test = df_mid[
        (df_mid['constraint'] == 'country_unconstrained') &
        (df_mid['goal_type'] == 'early_refining')
    ]
    
    print("=== DEBUGGING STAGE FLOW CONNECTIVITY ===\n")
    
    # Check each mineral's flow pattern
    for mineral in ['copper', 'nickel', 'cobalt']:
        print(f"\n{mineral.upper()} FLOW ANALYSIS:")
        
        mineral_data = df_test[df_test['reference_mineral'] == mineral]
        if mineral_data.empty:
            continue
            
        # Group by stage
        stage_summary = mineral_data.groupby('processing_stage').agg({
            'production_tonnes': 'sum',
            'export_tonnes': 'sum',
            'import_tonnes': 'sum'
        }).reset_index()
        
        stage_summary = stage_summary.sort_values('processing_stage')
        
        print("Stage | Production | Exports | Imports | Retained | Flow to Next |")
        print("------|------------|---------|---------|----------|--------------|")
        
        stages = stage_summary['processing_stage'].values
        for i, row in stage_summary.iterrows():
            stage = row['processing_stage']
            prod = row['production_tonnes'] / 1e3  # kt
            exp = row['export_tonnes'] / 1e3
            imp = row['import_tonnes'] / 1e3
            retained = prod + imp - exp
            
            # Calculate what could flow to next stage
            if i < len(stage_summary) - 1:
                next_stage_prod = stage_summary.iloc[i+1]['production_tonnes'] / 1e3
                flow_to_next = min(retained, next_stage_prod)  # What actually flows
            else:
                flow_to_next = 0  # Last stage
            
            print(f"{stage:5.1f} | {prod:10.1f} | {exp:7.1f} | {imp:7.1f} | {retained:8.1f} | {flow_to_next:10.1f} |")
        
        # Check for disconnections
        print("\nConnectivity Analysis:")
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            
            current_row = stage_summary[stage_summary['processing_stage'] == current_stage].iloc[0]
            next_row = stage_summary[stage_summary['processing_stage'] == next_stage].iloc[0]
            
            current_retained = (current_row['production_tonnes'] + current_row['import_tonnes'] - current_row['export_tonnes']) / 1e3
            next_production = next_row['production_tonnes'] / 1e3
            
            print(f"  Stage {current_stage} → {next_stage}:")
            print(f"    Available from {current_stage}: {current_retained:.1f} kt")
            print(f"    Production at {next_stage}: {next_production:.1f} kt")
            
            if next_production > current_retained * 1.5:  # Allowing some margin
                print(f"    ⚠️  DISCONNECTION: Next stage needs more than available!")
            elif current_retained < 1:  # Very small flow
                print(f"    ⚠️  WEAK CONNECTION: Very small flow ({current_retained:.3f} kt)")
            else:
                print(f"    ✓  Connected")
    
    print("\n=== RECOMMENDATIONS ===")
    print("1. For very small flows (<1 kt), consider aggregating or using minimum thresholds")
    print("2. Show all connections, even tiny ones, to maintain physical realism")
    print("3. Consider using logarithmic scaling for very small flows")
    print("4. Ensure minimum flow width for visibility")

if __name__ == "__main__":
    debug_stage_flows()