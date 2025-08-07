"""
Analyze export/import flow data to understand stage-to-stage flows
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

def analyze_flow_columns(df):
    """Analyze the export/import columns and their relationships"""
    
    print("=== DATA COLUMNS ANALYSIS ===")
    
    # Check what columns exist
    flow_columns = [col for col in df.columns if any(term in col.lower() for term in ['export', 'import', 'production'])]
    print(f"\nFlow-related columns found:")
    for col in sorted(flow_columns):
        print(f"  - {col}")
    
    print(f"\nTotal records: {len(df)}")
    print(f"Records with processing_stage > 0: {len(df[df['processing_stage'] > 0])}")
    
    # Focus on processing stages > 0
    df_products = df[df['processing_stage'] > 0].copy()
    
    print("\n=== EXPORT/IMPORT ANALYSIS ===")
    
    # Check which records have exports/imports
    has_exports = df_products['export_tonnes'] > 0
    has_imports = df_products['import_tonnes'] > 0
    has_production = df_products['production_tonnes'] > 0
    
    print(f"\nRecords with exports > 0: {has_exports.sum()} ({has_exports.sum()/len(df_products)*100:.1f}%)")
    print(f"Records with imports > 0: {has_imports.sum()} ({has_imports.sum()/len(df_products)*100:.1f}%)")
    print(f"Records with production > 0: {has_production.sum()} ({has_production.sum()/len(df_products)*100:.1f}%)")
    
    # Check relationships
    print(f"\nRecords with both exports and imports: {(has_exports & has_imports).sum()}")
    print(f"Records with production but no exports: {(has_production & ~has_exports).sum()}")
    print(f"Records with exports but no production: {(has_exports & ~has_production).sum()}")
    
    return df_products

def analyze_by_mineral_stage(df_products):
    """Analyze flows by mineral and stage"""
    
    print("\n=== MINERAL/STAGE FLOW ANALYSIS ===")
    
    # Aggregate by mineral and stage
    flow_summary = df_products.groupby(['reference_mineral', 'processing_stage']).agg({
        'production_tonnes': 'sum',
        'export_tonnes': 'sum', 
        'import_tonnes': 'sum'
    }).reset_index()
    
    # Convert to millions of tonnes for readability
    for col in ['production_tonnes', 'export_tonnes', 'import_tonnes']:
        flow_summary[f'{col}_mt'] = flow_summary[col] / 1e6
    
    # Calculate ratios
    flow_summary['export_ratio'] = flow_summary['export_tonnes'] / flow_summary['production_tonnes']
    flow_summary['export_ratio'] = flow_summary['export_ratio'].fillna(0)
    
    # Show summary for each mineral
    for mineral in sorted(flow_summary['reference_mineral'].unique()):
        mineral_data = flow_summary[flow_summary['reference_mineral'] == mineral].sort_values('processing_stage')
        
        print(f"\n{mineral.upper()}:")
        print("  Stage | Production | Exports | Imports | Export% |")
        print("  ------|------------|---------|---------|---------|")
        
        for _, row in mineral_data.iterrows():
            stage = row['processing_stage']
            prod = row['production_tonnes_mt']
            exp = row['export_tonnes_mt']
            imp = row['import_tonnes_mt']
            exp_pct = row['export_ratio'] * 100
            
            print(f"  {stage:5.1f} | {prod:10.2f} | {exp:7.2f} | {imp:7.2f} | {exp_pct:6.1f}% |")
    
    return flow_summary

def check_flow_consistency(df_products):
    """Check for potential double counting or inconsistencies"""
    
    print("\n=== FLOW CONSISTENCY CHECKS ===")
    
    # Group by scenario, constraint, mineral to check stage-to-stage consistency
    scenarios_sample = df_products.groupby(['scenario', 'constraint', 'reference_mineral']).size().head(10)
    
    print(f"\nChecking flow consistency for sample scenarios...")
    
    for (scenario, constraint, mineral), _ in scenarios_sample.items():
        group_data = df_products[
            (df_products['scenario'] == scenario) & 
            (df_products['constraint'] == constraint) & 
            (df_products['reference_mineral'] == mineral)
        ].sort_values('processing_stage')
        
        if len(group_data) > 1:
            print(f"\n{mineral.upper()} - {scenario} - {constraint}:")
            print("  Stage | Production | Exports | Imports | Net Flow |")
            print("  ------|------------|---------|---------|----------|")
            
            total_production = 0
            total_exports = 0
            total_imports = 0
            
            for _, row in group_data.iterrows():
                stage = row['processing_stage']
                prod = row['production_tonnes'] / 1e3  # kt
                exp = row['export_tonnes'] / 1e3
                imp = row['import_tonnes'] / 1e3
                net_flow = prod + imp - exp  # What's available for next stage
                
                print(f"  {stage:5.1f} | {prod:10.1f} | {exp:7.1f} | {imp:7.1f} | {net_flow:8.1f} |")
                
                total_production += prod
                total_exports += exp
                total_imports += imp
            
            print(f"  TOTAL | {total_production:10.1f} | {total_exports:7.1f} | {total_imports:7.1f} |")
            
            # Check if later stage production could come from earlier stages
            stages = group_data['processing_stage'].values
            for i in range(1, len(stages)):
                curr_stage = stages[i]
                prev_stage = stages[i-1]
                
                curr_prod = group_data[group_data['processing_stage'] == curr_stage]['production_tonnes'].iloc[0]
                prev_available = (
                    group_data[group_data['processing_stage'] == prev_stage]['production_tonnes'].iloc[0] +
                    group_data[group_data['processing_stage'] == prev_stage]['import_tonnes'].iloc[0] -
                    group_data[group_data['processing_stage'] == prev_stage]['export_tonnes'].iloc[0]
                )
                
                if curr_prod > prev_available * 1.1:  # Allow 10% tolerance
                    print(f"    ⚠️  Stage {curr_stage} production ({curr_prod/1e3:.1f}kt) > available from Stage {prev_stage} ({prev_available/1e3:.1f}kt)")

def check_goal_specific_patterns(df_products):
    """Check if export/production patterns differ by goal"""
    
    print("\n=== GOAL-SPECIFIC PATTERNS ===")
    
    # Add goal type
    df_products['goal_type'] = df_products['scenario'].apply(get_goal_from_scenario)
    
    # Analyze export ratios by goal and stage category
    def categorize_stage(stage):
        if stage <= 1.5:
            return 'Beneficiation'
        elif stage <= 3.5:
            return 'Early Refining'
        else:
            return 'Precursor'
    
    df_products['stage_category'] = df_products['processing_stage'].apply(categorize_stage)
    
    # Calculate export ratios
    df_products['export_ratio'] = df_products['export_tonnes'] / df_products['production_tonnes']
    df_products['export_ratio'] = df_products['export_ratio'].fillna(0)
    
    goal_patterns = df_products.groupby(['goal_type', 'stage_category']).agg({
        'production_tonnes': 'sum',
        'export_tonnes': 'sum',
        'export_ratio': 'mean'
    }).reset_index()
    
    goal_patterns['actual_export_ratio'] = goal_patterns['export_tonnes'] / goal_patterns['production_tonnes']
    
    print("\nExport patterns by goal and stage category:")
    print("Goal          | Stage Category | Production (Mt) | Exports (Mt) | Export % |")
    print("--------------|----------------|-----------------|--------------|----------|")
    
    for _, row in goal_patterns.iterrows():
        goal = row['goal_type']
        category = row['stage_category']
        prod = row['production_tonnes'] / 1e6
        exp = row['export_tonnes'] / 1e6
        exp_pct = row['actual_export_ratio'] * 100
        
        print(f"{goal:13} | {category:14} | {prod:15.2f} | {exp:12.2f} | {exp_pct:8.1f}% |")

def main():
    """Run flow data analysis"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Filter to mid scenarios for consistency
    df_mid = get_mid_scenarios_symmetric(df)
    
    # Analyze columns and structure
    df_products = analyze_flow_columns(df_mid)
    
    # Analyze by mineral and stage
    flow_summary = analyze_by_mineral_stage(df_products)
    
    # Check consistency
    check_flow_consistency(df_products)
    
    # Check goal patterns
    check_goal_specific_patterns(df_products)
    
    print("\n=== RECOMMENDATIONS FOR SANKEY ===")
    print("1. Use export_tonnes to show actual sales at each stage")
    print("2. Use (production_tonnes + import_tonnes - export_tonnes) for flow to next stage") 
    print("3. Import_tonnes shows material coming from external sources")
    print("4. Check for any negative flows or inconsistencies")
    print("5. Consider showing imports as separate input flows")

if __name__ == "__main__":
    main()