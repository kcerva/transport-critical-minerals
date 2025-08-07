#!/usr/bin/env python3
"""
Test script to demonstrate the complete new dashboard implementation
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from single_constraint_dashboards import generate_all_countries_dashboards

def test_sample_countries():
    """Test dashboard generation for a subset of countries"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load all data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Get unique countries
    all_countries = df['iso3'].dropna().unique()
    print(f"All countries in dataset: {', '.join(sorted(all_countries))}")
    
    # Test with a small subset (3 countries)
    test_countries = ['ZMB', 'BWA', 'NAM']  # Zambia, Botswana, Namibia
    
    print(f"\nTesting implementation with {len(test_countries)} countries: {', '.join(test_countries)}")
    
    # Create test output base directory
    test_base_dir = os.path.join(output_data_path, 'country_reports', 'test_full_implementation')
    os.makedirs(test_base_dir, exist_ok=True)
    
    # Process each test country
    results = {}
    
    for country_code in test_countries:
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
        output_dir = os.path.join(test_base_dir, f'single_constraint_dashboards_{country_code}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate dashboards for all 4 constraints + policy dashboard
        from single_constraint_dashboards import create_single_constraint_dashboard, create_pivot_summary_table, get_mid_scenarios_symmetric
        from policy_comparison_dashboard import create_policy_comparison_dashboard
        
        constraints = ['country_unconstrained', 'country_constrained', 'region_unconstrained', 'region_constrained']
        dashboard_paths = []
        
        country_name = df_country['country_name'].iloc[0] if 'country_name' in df_country.columns and not df_country.empty else country_code
        
        # Generate single constraint dashboards
        for constraint in constraints:
            try:
                dashboard_path = create_single_constraint_dashboard(df_country, constraint, output_dir, country_name)
                if dashboard_path:
                    dashboard_paths.append(dashboard_path)
                    print(f"✓ Generated: {os.path.basename(dashboard_path)}")
            except Exception as e:
                print(f"✗ Error generating {constraint} dashboard: {e}")
        
        # Generate policy comparison dashboard
        try:
            policy_dashboard_path = create_policy_comparison_dashboard(df_country, output_dir, country_name)
            if policy_dashboard_path:
                dashboard_paths.append(policy_dashboard_path)
                print(f"✓ Generated: {os.path.basename(policy_dashboard_path)}")
        except Exception as e:
            print(f"✗ Error generating policy comparison dashboard: {e}")
        
        # Generate summary table
        try:
            mid_data = get_mid_scenarios_symmetric(df_country)
            if not mid_data.empty:
                pivot_summary = create_pivot_summary_table(mid_data)
                summary_filename = f'{country_code.upper()}_all_constraints_summary_table.csv'
                summary_path = os.path.join(output_dir, summary_filename)
                pivot_summary.to_csv(summary_path, index=False)
                print(f"✓ Generated: {summary_filename}")
        except Exception as e:
            print(f"✗ Error generating summary table: {e}")
        
        results[country_code] = {
            'output_dir': output_dir,
            'dashboards': len(dashboard_paths),
            'files': os.listdir(output_dir)
        }
        
        print(f"✓ Generated {len(dashboard_paths)} dashboards for {country_code}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY OF TEST IMPLEMENTATION")
    print(f"{'='*60}")
    
    total_dashboards = sum(info['dashboards'] for info in results.values())
    
    print(f"✓ Countries processed: {len(results)}")
    print(f"✓ Total dashboards generated: {total_dashboards}")
    print(f"✓ Expected: {len(test_countries) * 5} dashboards (4 single constraint + 1 policy per country)")
    
    # List files for each country
    for country_code, info in results.items():
        print(f"\n{country_code} files ({len(info['files'])} total):")
        for file in sorted(info['files']):
            file_path = os.path.join(info['output_dir'], file)
            file_size = os.path.getsize(file_path)
            print(f"  - {file} ({file_size:,} bytes)")
    
    print(f"\n✓ Test completed. Check output in: {test_base_dir}")
    return results

if __name__ == "__main__":
    test_sample_countries()