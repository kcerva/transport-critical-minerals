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
    from plot_emissions_water_all_countries import plot_emissions_scenario_comparison_subplots
    
    emissions_files = plot_emissions_by_country_all_constraints(df, output_base)
    print(f"✓ Generated {len(emissions_files) if emissions_files else 0} emissions figures")
    
    # Generate emissions scenario comparison subplots (will be skipped until energy data available)
    emissions_subplot_files = plot_emissions_scenario_comparison_subplots(df, output_base)
    print(f"✓ Generated {len(emissions_subplot_files) if emissions_subplot_files else 0} emissions scenario comparison subplots")
    
except Exception as e:
    print(f"✗ Error generating emissions figures: {e}")

# Generate water figures
print("\n=== Generating Water Usage Figures ===")
try:
    from plot_emissions_water_all_countries import plot_water_scenario_comparison_subplots
    
    water_files = plot_water_by_country_all_constraints(df, output_base)
    print(f"✓ Generated {len(water_files) if water_files else 0} water usage figures")
    
    # Generate water scenario comparison subplots
    water_subplot_files = plot_water_scenario_comparison_subplots(df, output_base)
    print(f"✓ Generated {len(water_subplot_files) if water_subplot_files else 0} water usage scenario comparison subplots")
    
except Exception as e:
    print(f"✗ Error generating water figures: {e}")

# Generate GDP share figures (Revenue share)
print("\n=== Generating Revenue Share of GDP Figures ===")
try:
    from plot_gdp_share_by_country_all_constraints import compute_revenue_share, plot_gdp_share_scenario_comparison_subplots
    
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
    
    # Generate scenario comparison subplots
    revenue_subplot_files = plot_gdp_share_scenario_comparison_subplots(
        df, output_base, compute_revenue_share, 'value', 'Revenue Share of GDP', 'Revenue Share of GDP (%)'
    )
    print(f"✓ Generated {len(revenue_subplot_files) if revenue_subplot_files else 0} revenue share scenario comparison subplots")
    
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
    
    # Generate scenario comparison subplots
    value_subplot_files = plot_gdp_share_scenario_comparison_subplots(
        df, output_base, compute_value_addition_share, 'value', 'Value Addition Share of GDP', 'Value Addition Share of GDP (%)'
    )
    print(f"✓ Generated {len(value_subplot_files) if value_subplot_files else 0} value addition share scenario comparison subplots")
    
except Exception as e:
    print(f"✗ Error generating value addition share figures: {e}")

# Generate Production scenario comparison subplots
print("\n=== Generating Production Scenario Comparison Subplots ===")
try:
    from plot_production_by_country_all_constraints import plot_production_scenario_comparison_subplots
    
    production_subplot_files = plot_production_scenario_comparison_subplots(df, output_base)
    print(f"✓ Generated {len(production_subplot_files) if production_subplot_files else 0} production scenario comparison subplots")
    
except Exception as e:
    print(f"✗ Error generating production scenario comparison subplots: {e}")

# Generate Processing-focused production subplots
print("\n=== Generating Processing-Focused Production Subplots ===")
try:
    from plot_production_by_country_all_constraints import plot_production_processing_focus_subplots
    
    processing_subplot_files = plot_production_processing_focus_subplots(df, output_base)
    print(f"✓ Generated {len(processing_subplot_files) if processing_subplot_files else 0} processing-focused production subplots")
    
except Exception as e:
    print(f"✗ Error generating processing-focused production subplots: {e}")

# Generate Value Addition scenario comparison subplots  
print("\n=== Generating Value Addition Scenario Comparison Subplots ===")
try:
    from plot_emissions_water_all_countries import plot_value_addition_scenario_comparison_subplots
    
    value_addition_subplot_files = plot_value_addition_scenario_comparison_subplots(df, output_base)
    print(f"✓ Generated {len(value_addition_subplot_files) if value_addition_subplot_files else 0} value addition scenario comparison subplots")
    
except Exception as e:
    print(f"✗ Error generating value addition scenario comparison subplots: {e}")

# Generate Value Addition GDP Share scenario comparison subplots
print("\n=== Generating Value Addition GDP Share Scenario Comparison Subplots ===")
try:
    from plot_emissions_water_all_countries import plot_value_addition_gdp_share_scenario_comparison_subplots
    
    value_addition_gdp_subplot_files = plot_value_addition_gdp_share_scenario_comparison_subplots(df, output_base)
    print(f"✓ Generated {len(value_addition_gdp_subplot_files) if value_addition_gdp_subplot_files else 0} value addition GDP share scenario comparison subplots")
    
except Exception as e:
    print(f"✗ Error generating value addition GDP share scenario comparison subplots: {e}")

print("\n✅ Figure generation complete!")
print(f"Output directory: {output_base}")