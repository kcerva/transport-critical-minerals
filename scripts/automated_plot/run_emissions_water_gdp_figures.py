#!/usr/bin/env python3
"""
Run emissions, water, and GDP share figures with new data
"""

import os
import json
import pandas as pd
from plot_emissions_water_all_countries import (
    plot_emissions_by_country_all_constraints,
    plot_water_by_country_all_constraints
)
from plot_gdp_share_by_country_all_constraints import plot_gdp_share_by_country_all_constraints

# Load configuration
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(project_root, "config.json")
with open(config_path, 'r') as f:
    config = json.load(f)

# Define paths
data_path = os.path.join(config['paths']['results'], "all_data.xlsx")
output_base = os.path.join(config['paths']['figures'], "automated_plots", "all_countries")

# Load data
print(f"Loading data from: {data_path}")
df = pd.read_excel(data_path)
print(f"Loaded {len(df)} rows of data")

# Create output directory
os.makedirs(output_base, exist_ok=True)

# Generate emissions figures
print("\n=== Generating Emissions Figures ===")
try:
    emissions_files = plot_emissions_by_country_all_constraints(df, output_base)
    print(f"✓ Generated {len(emissions_files) if emissions_files else 0} emissions figures")
except Exception as e:
    print(f"✗ Error generating emissions figures: {e}")

# Generate water figures
print("\n=== Generating Water Usage Figures ===")
try:
    water_files = plot_water_by_country_all_constraints(df, output_base)
    print(f"✓ Generated {len(water_files) if water_files else 0} water usage figures")
except Exception as e:
    print(f"✗ Error generating water figures: {e}")

# Generate GDP share figures (Revenue share)
print("\n=== Generating Revenue Share of GDP Figures ===")
try:
    from plot_gdp_share_by_country_all_constraints import compute_revenue_share
    
    # Compute revenue share data
    revenue_share_df = compute_revenue_share(df)
    
    # Generate the plots with proper parameters
    revenue_files = plot_gdp_share_by_country_all_constraints(
        revenue_share_df, 
        output_base,
        value_column='value',  # The column created by compute_revenue_share
        title_prefix='Revenue Share of GDP',
        ylabel='Revenue Share of GDP (%)'
    )
    print(f"✓ Generated {len(revenue_files) if revenue_files else 0} revenue share of GDP figures")
except Exception as e:
    print(f"✗ Error generating revenue share figures: {e}")

# Generate Value Addition share of GDP figures
print("\n=== Generating Value Addition Share of GDP Figures ===")
try:
    from plot_gdp_share_by_country_all_constraints import compute_value_addition_share
    
    # Compute value addition share data
    value_addition_df = compute_value_addition_share(df)
    
    # Generate the plots with proper parameters
    value_files = plot_gdp_share_by_country_all_constraints(
        value_addition_df,
        output_base, 
        value_column='value',  # The column created by compute_value_addition_share
        title_prefix='Value Addition Share of GDP',
        ylabel='Value Addition Share of GDP (%)'
    )
    print(f"✓ Generated {len(value_files) if value_files else 0} value addition share of GDP figures")
except Exception as e:
    print(f"✗ Error generating value addition share figures: {e}")

print("\n✅ Figure generation complete!")
print(f"Output directory: {output_base}")