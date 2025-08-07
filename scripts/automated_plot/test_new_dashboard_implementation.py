#!/usr/bin/env python3
"""
Test script to validate the new dashboard implementation for Zambia
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from single_constraint_dashboards import create_single_constraint_dashboard, get_mid_scenarios_symmetric, create_pivot_summary_table
from policy_comparison_dashboard import create_policy_comparison_dashboard

def test_zambia_dashboards():
    """Test dashboard generation for Zambia with new uppercase naming"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load Zambia data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    df_country = df[df['iso3'] == 'ZMB'].copy()
    
    if df_country.empty:
        print("No data found for Zambia!")
        return
    
    # Create test output directory
    test_output_dir = os.path.join(output_data_path, 'country_reports', 'test_new_implementation_ZMB')
    os.makedirs(test_output_dir, exist_ok=True)
    
    print(f"Testing new implementation for Zambia...")
    print(f"Output directory: {test_output_dir}")
    
    # Get country name
    country_name = df_country['country_name'].iloc[0] if 'country_name' in df_country.columns and not df_country.empty else 'Zambia'
    
    # Test 1: Generate single constraint dashboards
    constraints = ['country_unconstrained', 'country_constrained', 'region_unconstrained', 'region_constrained']
    dashboard_paths = []
    
    print("\n=== Generating Single Constraint Dashboards ===")
    for constraint in constraints:
        try:
            dashboard_path = create_single_constraint_dashboard(df_country, constraint, test_output_dir, country_name)
            if dashboard_path:
                dashboard_paths.append(dashboard_path)
                print(f"✓ Generated: {os.path.basename(dashboard_path)}")
        except Exception as e:
            print(f"✗ Error generating {constraint} dashboard: {e}")
    
    # Test 2: Generate policy comparison dashboard
    print("\n=== Generating Policy Comparison Dashboard ===")
    try:
        policy_dashboard_path = create_policy_comparison_dashboard(df_country, test_output_dir, country_name)
        if policy_dashboard_path:
            dashboard_paths.append(policy_dashboard_path)
            print(f"✓ Generated: {os.path.basename(policy_dashboard_path)}")
    except Exception as e:
        print(f"✗ Error generating policy comparison dashboard: {e}")
    
    # Test 3: Generate summary table
    print("\n=== Generating Summary Table ===")
    try:
        mid_data = get_mid_scenarios_symmetric(df_country)
        if not mid_data.empty:
            pivot_summary = create_pivot_summary_table(mid_data)
            summary_filename = 'ZMB_all_constraints_summary_table.csv'
            summary_path = os.path.join(test_output_dir, summary_filename)
            pivot_summary.to_csv(summary_path, index=False)
            print(f"✓ Generated: {summary_filename}")
    except Exception as e:
        print(f"✗ Error generating summary table: {e}")
    
    # List all generated files
    print("\n=== Generated Files ===")
    for file in sorted(os.listdir(test_output_dir)):
        file_path = os.path.join(test_output_dir, file)
        file_size = os.path.getsize(file_path)
        print(f"- {file} ({file_size:,} bytes)")
    
    print(f"\n✓ Test completed. Check output in: {test_output_dir}")
    return test_output_dir

if __name__ == "__main__":
    test_zambia_dashboards()