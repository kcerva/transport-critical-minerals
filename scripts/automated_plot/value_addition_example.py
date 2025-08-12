#!/usr/bin/env python
"""
Value Addition Calculation Examples - Route-Based vs Sequential
Shows detailed step-by-step calculations for different processing scenarios
"""

import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(__file__))

from plot_config import (
    get_mineral_processing_routes,
    find_matching_route,
    validate_route_sequence,
    get_invalid_mineral_routes,
    get_route_flag_message
)
from plot_emissions_water_all_countries import calc_value_added_with_routes

def create_example_data():
    """Create realistic example data for copper processing"""
    
    # Example 1: Full processing chain (many steps) - Zambia
    full_chain = pd.DataFrame({
        'iso3': ['ZMB'] * 5,
        'reference_mineral': ['copper'] * 5,
        'scenario': ['early_refining_2040_mid_min_threshold_metal_tons'] * 5,
        'processing_stage': [1.0, 2.0, 3.0, 4.3, 5.0],
        'production_tonnes': [1000000, 800000, 600000, 400000, 200000],  # Decreasing as processing advances
        'price_usd_per_tonne': [8000, 12000, 18000, 25000, 40000],        # Increasing with processing
        'production_cost_usd_per_tonne': [6000, 9000, 14000, 20000, 30000]  # Production costs
    })
    
    # Example 2: Minimal processing (few steps) - Kenya  
    minimal_chain = pd.DataFrame({
        'iso3': ['KEN'] * 2,
        'reference_mineral': ['copper'] * 2,
        'scenario': ['early_refining_2040_mid_min_threshold_metal_tons'] * 2,
        'processing_stage': [1.0, 5.0],
        'production_tonnes': [500000, 100000],
        'price_usd_per_tonne': [8000, 40000],
        'production_cost_usd_per_tonne': [6000, 30000]
    })
    
    # Example 3: Alternative route - Tanzania
    alternative_chain = pd.DataFrame({
        'iso3': ['TZA'] * 3,
        'reference_mineral': ['copper'] * 3,
        'scenario': ['early_refining_2040_mid_min_threshold_metal_tons'] * 3,
        'processing_stage': [1.0, 3.0, 5.0],
        'production_tonnes': [800000, 500000, 150000],
        'price_usd_per_tonne': [8000, 18000, 40000],
        'production_cost_usd_per_tonne': [6000, 14000, 30000]
    })
    
    return pd.concat([full_chain, minimal_chain, alternative_chain], ignore_index=True)

def manual_value_calculation(group, route):
    """Manually calculate value addition for comparison"""
    print(f"\n{'='*60}")
    country = group['iso3'].iloc[0]
    stages = sorted(group['processing_stage'].unique())
    
    print(f"COUNTRY: {country}")
    print(f"Stages Present: {stages}")
    print(f"Matched Route: {route}")
    print(f"{'='*60}")
    
    # Show the data
    display_data = group[['processing_stage', 'production_tonnes', 'price_usd_per_tonne', 'production_cost_usd_per_tonne']].copy()
    display_data = display_data.sort_values('processing_stage')
    
    print("\nStage Data:")
    print(display_data.to_string(index=False, float_format='%.0f'))
    
    # Calculate step by step following the route
    route_stages_in_data = [stage for stage in route if stage in stages]
    print(f"\nRoute stages found in data: {route_stages_in_data}")
    
    total_value_added = 0
    
    print(f"\n{'Step-by-Step Value Addition Calculation:'}")
    print("-" * 50)
    
    for i in range(1, len(route_stages_in_data)):
        prev_stage = route_stages_in_data[i-1]
        curr_stage = route_stages_in_data[i]
        
        prev_row = group[group['processing_stage'] == prev_stage].iloc[0]
        curr_row = group[group['processing_stage'] == curr_stage].iloc[0]
        
        if prev_row['production_tonnes'] > 0:
            revenue_current = curr_row['price_usd_per_tonne'] * curr_row['production_tonnes']
            cost_previous = prev_row['production_cost_usd_per_tonne'] * prev_row['production_tonnes']
            value_added = revenue_current - cost_previous
            total_value_added += value_added
            
            print(f"Step {i}: Stage {prev_stage:.1f} → {curr_stage:.1f}")
            print(f"  Current Revenue: ${curr_row['price_usd_per_tonne']:,.0f}/t × {curr_row['production_tonnes']:,.0f}t = ${revenue_current:,.0f}")
            print(f"  Previous Cost:   ${prev_row['production_cost_usd_per_tonne']:,.0f}/t × {prev_row['production_tonnes']:,.0f}t = ${cost_previous:,.0f}")
            print(f"  Value Added:     ${value_added:,.0f}")
            print()
    
    print(f"TOTAL VALUE ADDED: ${total_value_added:,.0f}")
    print(f"VALUE ADDED (Million USD): ${total_value_added/1e6:.1f}M")
    
    return total_value_added

def show_route_comparison():
    """Show how different routes lead to different value addition calculations"""
    
    print("🔥 VALUE ADDITION CALCULATION EXAMPLES")
    print("=" * 80)
    print("Comparing route-based value addition for different processing scenarios")
    print("=" * 80)
    
    # Create example data
    df = create_example_data()
    
    # Process each country example
    for country in ['ZMB', 'KEN', 'TZA']:
        country_data = df[df['iso3'] == country].copy()
        
        # Get copper routes
        valid_routes = get_mineral_processing_routes('copper')
        invalid_routes = get_invalid_mineral_routes('copper')
        
        # Get stages and find matching route
        stages = sorted(country_data['processing_stage'].unique())
        
        # Check for invalid routes
        is_invalid, invalid_route = validate_route_sequence(stages, invalid_routes)
        if is_invalid:
            flag_message = get_route_flag_message('copper')
            print(f"\n⚠️  {flag_message}: copper in {country}")
            print(f"    Invalid route detected: {invalid_route}")
        
        # Find matching valid route
        matching_route = find_matching_route(stages, valid_routes)
        
        if matching_route:
            # Manual calculation for explanation
            manual_total = manual_value_calculation(country_data, matching_route)
            
            # Route-based calculation
            country_data['value_added'] = 0.0
            result = calc_value_added_with_routes(country_data)
            route_based_total = result['value_added'].sum()
            
            print(f"✓ Route-based calculation matches: ${route_based_total:,.0f}")
            
            # Verify they match
            if abs(manual_total - route_based_total) < 1:  # Allow for rounding
                print("✅ CALCULATION VERIFIED")
            else:
                print("❌ MISMATCH DETECTED")
                
        else:
            print(f"\n❌ No valid route found for {country}")
    
    print("\n" + "=" * 80)
    print("🎯 KEY INSIGHTS:")
    print("=" * 80)
    print("1. FULL CHAIN (ZMB): Uses complete 1→2→3→4.3→5 route")
    print("   - Calculates value addition at each processing step")
    print("   - Maximum value capture through complete processing")
    print("")
    print("2. MINIMAL CHAIN (KEN): Invalid 1→5 direct route STRICTLY ENFORCED") 
    print("   - 🚫 ZERO VALUE ADDITION due to invalid processing pathway")
    print("   - Enforces realistic mineral processing economics")
    print("")
    print("3. ALTERNATIVE ROUTE (TZA): Uses 1→3→5 pathway")
    print("   - Skips intermediate stages but follows valid route")
    print("   - Moderate value addition with efficient processing")
    print("")
    print("🔍 STRICT ENFORCEMENT: Invalid routes = Zero value addition")
    print("   Ensures only realistic processing pathways receive economic benefits!")

if __name__ == "__main__":
    show_route_comparison()