#!/usr/bin/env python3
"""
Test script for new scenario comparison subplot functionality
"""

import os
import json
import pandas as pd
from plot_production_by_country_all_constraints import plot_production_scenario_comparison_subplots

# Load configuration
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(project_root, "config.json")
with open(config_path, 'r') as f:
    config = json.load(f)

# Define paths
data_path = os.path.join(config['paths']['results'], "all_data.xlsx")
output_base = os.path.join(config['paths']['figures'], "automated_plots", "scenario_comparison_test")

# Load data
print(f"Loading data from: {data_path}")
df = pd.read_excel(data_path)
print(f"Loaded {len(df)} rows of data")

# Create output directory
os.makedirs(output_base, exist_ok=True)

# Generate scenario comparison subplots
print("\n=== Generating Production Scenario Comparison Subplots ===")
try:
    saved_files = plot_production_scenario_comparison_subplots(df, output_base)
    print(f"✓ Generated {len(saved_files)} scenario comparison subplot files:")
    for file_path in saved_files:
        print(f"  - {os.path.basename(file_path)}")
except Exception as e:
    print(f"✗ Error generating scenario comparison subplots: {e}")
    import traceback
    traceback.print_exc()

print(f"\nOutput directory: {output_base}")
print("✅ Test complete!")