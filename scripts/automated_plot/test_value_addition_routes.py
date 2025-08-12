#!/usr/bin/env python
"""Test script for route-based value addition calculation"""

import pandas as pd
import numpy as np
import json
import os
import sys
sys.path.append(os.path.dirname(__file__))

from plot_config import (
    get_mineral_processing_routes,
    get_invalid_mineral_routes,
    get_route_flag_message,
    find_matching_route,
    validate_route_sequence
)
from plot_emissions_water_all_countries import calc_value_added_with_routes

# Load configuration
config_path = "config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

# Load data directly from config - use the latest all_data.xlsx file  
results_dir = config['paths']['results']
data_path = os.path.join(results_dir, 'all_data.xlsx')
print(f"Loading data from: {data_path}")
df = pd.read_excel(data_path)

# Focus on value addition scenarios  
print("\n=== Testing Route-Based Value Addition Calculation ===\n")

# Filter for 2040 scenarios with processing stages
df_filtered = df[
    (df["processing_stage"] > 0) &
    (df["scenario"].str.contains("2040")) &
    (
        ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
        ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
    )
].copy()

# Sort and prepare for value addition calculation
df_filtered = df_filtered.sort_values(by=["iso3", "reference_mineral", "scenario", "processing_stage"])
df_filtered["value_added"] = 0.0

# Test on a sample of minerals and countries
test_minerals = ['copper', 'cobalt', 'nickel']
test_countries = ['ZMB', 'COD', 'TZA', 'ZWE']

print("Testing route detection for selected minerals and countries:")
print("=" * 60)

for mineral in test_minerals:
    print(f"\n{mineral.upper()}:")
    print(f"  Valid routes: {get_mineral_processing_routes(mineral)}")
    print(f"  Invalid routes: {get_invalid_mineral_routes(mineral)}")
    
    mineral_data = df_filtered[df_filtered['reference_mineral'] == mineral]
    
    for country in test_countries:
        country_data = mineral_data[mineral_data['iso3'] == country]
        if country_data.empty:
            continue
            
        # Get unique processing stages for this country-mineral
        stages = sorted(country_data['processing_stage'].unique())
        if len(stages) < 2:
            continue
            
        print(f"\n  {country}: Stages present = {stages}")
        
        # Check for invalid routes
        invalid_routes = get_invalid_mineral_routes(mineral)
        is_invalid, invalid_route = validate_route_sequence(stages, invalid_routes)
        if is_invalid:
            flag_message = get_route_flag_message(mineral)
            print(f"    ⚠️  {flag_message}")
            print(f"    Invalid route detected: {invalid_route}")
        
        # Find matching valid route
        valid_routes = get_mineral_processing_routes(mineral)
        if valid_routes:
            matching_route = find_matching_route(stages, valid_routes)
            if matching_route:
                print(f"    ✓ Matched route: {matching_route}")
            else:
                print(f"    ✗ No matching route found")

print("\n" + "=" * 60)
print("\nCalculating value addition with routes for all data...")

# Track all invalid routes found
invalid_routes_found = {}

def track_invalid_routes(group):
    """Modified calc function that tracks invalid routes"""
    mineral = group['reference_mineral'].iloc[0]
    country = group['iso3'].iloc[0]
    scenario = group['scenario'].iloc[0]
    
    # Get stages present in this country's data
    country_stages = sorted(group['processing_stage'].unique())
    
    # Check for invalid routes
    invalid_routes = get_invalid_mineral_routes(mineral)
    if invalid_routes:
        is_invalid, invalid_route = validate_route_sequence(country_stages, invalid_routes)
        if is_invalid:
            route_key = f"{mineral}_{invalid_route}"
            if route_key not in invalid_routes_found:
                invalid_routes_found[route_key] = []
            invalid_routes_found[route_key].append((country, scenario))
    
    # Continue with normal calculation
    return calc_value_added_with_routes(group)

# Apply the route-based calculation with tracking
df_with_routes = df_filtered.groupby(["scenario", "constraint", "iso3", "reference_mineral"]).apply(
    track_invalid_routes
).reset_index(drop=True)

print("\n" + "=" * 60)
print("SUMMARY OF INVALID ROUTES FOUND:")
print("=" * 60)
if invalid_routes_found:
    for route_key, occurrences in invalid_routes_found.items():
        mineral, route_str = route_key.split("_", 1)
        print(f"\n{mineral.upper()} - Invalid route {route_str}:")
        print(f"  Found in {len(set(occ[0] for occ in occurrences))} countries")
        print(f"  Total occurrences: {len(occurrences)}")
        
        # Show unique countries
        unique_countries = sorted(set(occ[0] for occ in occurrences))
        print(f"  Countries: {', '.join(unique_countries)}")
else:
    print("No invalid routes detected!")

print("\n" + "=" * 60)

# Convert to million USD and filter for non-zero values
df_with_routes["value_added_musd"] = df_with_routes["value_added"] / 1e6
df_value_added = df_with_routes[df_with_routes["value_added_musd"] > 0]

print(f"\nTotal countries with value addition: {df_value_added['iso3'].nunique()}")
print(f"Total minerals with value addition: {df_value_added['reference_mineral'].nunique()}")

# Show top value additions by country-mineral
print("\nTop 10 Value Additions (Million USD):")
print("-" * 60)
top_values = df_value_added.groupby(['iso3', 'reference_mineral'])['value_added_musd'].sum().sort_values(ascending=False).head(10)
for (country, mineral), value in top_values.items():
    print(f"  {country} - {mineral}: ${value:,.1f}M")

# Show processing stage transitions
print("\nProcessing Stage Transitions Detected:")
print("-" * 60)
for mineral in df_value_added['reference_mineral'].unique():
    mineral_data = df_value_added[df_value_added['reference_mineral'] == mineral]
    countries_with_va = mineral_data[mineral_data['value_added_musd'] > 0]['iso3'].unique()
    if len(countries_with_va) > 0:
        print(f"  {mineral}: {len(countries_with_va)} countries with value addition")

print("\n✓ Route-based value addition calculation complete!")