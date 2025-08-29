#!/usr/bin/env python
"""Detailed analysis of value addition plots - colors and stages"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.dirname(__file__))

from plot_utils import generate_country_colormap
from plot_emissions_water_all_countries import calc_value_added_with_routes

def analyze_plots():
    print("🔍 DETAILED VALUE ADDITION PLOT ANALYSIS")
    print("=" * 60)
    
    # Load data
    df = pd.read_excel('/home/karlac/critical_minerals_Africa/transport-outputs/results/all_data.xlsx')
    
    # Same filtering as plot function
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["scenario"].str.contains("2040")) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ].copy()
    
    print(f"Total rows in filtered data: {len(df_filtered)}")
    print(f"Processing stages present: {sorted(df_filtered['processing_stage'].unique())}")
    print()
    
    # Apply route-based calculation
    df_filtered = df_filtered.sort_values(by=["iso3", "reference_mineral", "scenario", "processing_stage"])
    df_filtered["value_added"] = 0.0
    
    print("Applying route-based value addition calculation...")
    df_with_routes = df_filtered.groupby(["scenario", "constraint", "iso3", "reference_mineral"]).apply(
        calc_value_added_with_routes
    ).reset_index(drop=True)
    
    # Convert to million USD and filter
    df_with_routes["value_added_musd"] = df_with_routes["value_added"] / 1e6
    df_value_added = df_with_routes[df_with_routes["value_added_musd"] > 0]
    
    print(f"\\nRows with non-zero value addition: {len(df_value_added)}")
    print()
    
    # Check stages used in final data with value addition
    stages_with_va = sorted(df_value_added['processing_stage'].unique())
    print(f"🎯 STAGES WITH VALUE ADDITION: {stages_with_va}")
    print("This confirms which stages actually contribute to value addition")
    print()
    
    # Check countries and color mapping
    countries_with_va = sorted(df_value_added['iso3'].unique())
    country_colors = generate_country_colormap(countries_with_va)
    
    print(f"🌍 COUNTRIES WITH VALUE ADDITION ({len(countries_with_va)}): {countries_with_va}")
    print()
    
    # Check for color conflicts
    print("🎨 COUNTRY COLOR MAPPING:")
    print("-" * 40)
    color_values = list(country_colors.values())
    unique_colors = set(color_values)
    
    if len(color_values) == len(unique_colors):
        print("✅ NO COLOR CONFLICTS - All countries have unique colors")
    else:
        print("❌ COLOR CONFLICTS DETECTED")
        color_counts = {}
        for country, color in country_colors.items():
            if color not in color_counts:
                color_counts[color] = []
            color_counts[color].append(country)
        
        for color, countries in color_counts.items():
            if len(countries) > 1:
                print(f"  Conflict: {countries} share color {color}")
    
    print()
    for country, color in country_colors.items():
        # Convert RGB to hex for display
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
        )
        print(f"  {country}: {hex_color}")
    
    print()
    
    # Analyze by scenario and mineral
    print("📊 VALUE ADDITION BY SCENARIO & MINERAL:")
    print("-" * 50)
    
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining',
        'precursor_2040': 'Precursor Product'
    }
    
    for scenario_key, scenario_name in scenario_mapping.items():
        scenario_data = df_value_added[df_value_added["scenario"].str.contains(scenario_key)]
        if not scenario_data.empty:
            print(f"\\n{scenario_name}:")
            
            # Group by mineral-country to see distribution
            mineral_country_summary = scenario_data.groupby(['reference_mineral', 'iso3'])['value_added_musd'].sum().reset_index()
            mineral_country_summary = mineral_country_summary.sort_values('value_added_musd', ascending=False)
            
            print(f"  Top 10 mineral-country value additions:")
            for _, row in mineral_country_summary.head(10).iterrows():
                print(f"    {row['reference_mineral']}-{row['iso3']}: ${row['value_added_musd']:,.0f}M")
            
            # Check which stages contribute in this scenario
            stages_in_scenario = sorted(scenario_data['processing_stage'].unique())
            print(f"  Stages with value addition: {stages_in_scenario}")
    
    print()
    print("🔍 SUMMARY:")
    print("-" * 20)
    print(f"• Total countries: {len(countries_with_va)}")
    print(f"• Total minerals: {len(df_value_added['reference_mineral'].unique())}")
    print(f"• Processing stages used: {stages_with_va}")
    print(f"• Country color conflicts: {'None' if len(color_values) == len(unique_colors) else 'Yes'}")

if __name__ == "__main__":
    analyze_plots()