#!/usr/bin/env python3
"""Test script to verify error bar charts are working correctly"""

import os
import json
import pandas as pd
from chart_adapters import create_production_subplot_charts_with_errorbars

def test_errorbar_charts():
    """Test the error bar chart generation"""
    
    # Load config
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "..", "..", "config.json")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load data
    data_file = os.path.join(config["paths"]["results"], "all_data.xlsx")
    print(f"Loading data from: {data_file}")
    
    df = pd.read_excel(data_file)
    print(f"Data loaded: {len(df)} rows")
    
    # Check scenario names
    print("\nUnique scenarios in data:")
    for s in sorted(df['scenario'].unique()):
        print(f"  - {s}")
    
    # Test with Zambia data
    test_country = 'ZMB'
    df_country = df[df['iso3'] == test_country].copy()
    print(f"\nFiltered data for {test_country}: {len(df_country)} rows")
    
    # Check 2040 scenarios
    df_2040 = df_country[df_country['scenario'].str.contains('2040')]
    print(f"2040 scenarios for {test_country}: {len(df_2040)} rows")
    
    # Check for mid scenarios
    print("\nChecking for mid scenarios:")
    for goal in ['bau', 'early_refining', 'precursor']:
        mid_scenario = f'{goal}_2040_mid_min_threshold_metal_tons'
        count = len(df_2040[df_2040['scenario'] == mid_scenario])
        print(f"  {mid_scenario}: {count} rows")
    
    # Create test output directory
    output_dir = os.path.join(config["paths"]["figures"], "test_errorbars")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate error bar charts
    print(f"\nGenerating error bar charts in: {output_dir}")
    saved_paths = create_production_subplot_charts_with_errorbars(df_country, output_dir, test_country)
    
    print(f"\nGenerated {len(saved_paths)} charts:")
    for path in saved_paths:
        print(f"  - {os.path.basename(path)}")
    
    # Also test with another country
    test_country2 = 'COD'
    df_country2 = df[df['iso3'] == test_country2].copy()
    if len(df_country2) > 0:
        print(f"\nTesting with {test_country2}...")
        saved_paths2 = create_production_subplot_charts_with_errorbars(df_country2, output_dir, test_country2)
        print(f"Generated {len(saved_paths2)} charts for {test_country2}")

if __name__ == "__main__":
    test_errorbar_charts()