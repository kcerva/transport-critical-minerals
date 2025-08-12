#!/usr/bin/env python
"""Test how invalid routes should be handled"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(__file__))

from plot_config import (
    get_mineral_processing_routes,
    get_invalid_mineral_routes, 
    validate_route_sequence
)

def test_invalid_route_behavior():
    print("🔍 TESTING INVALID ROUTE BEHAVIOR")
    print("=" * 50)
    
    # Case: Kenya with only stages 1.0 and 5.0 (invalid direct route)
    kenya_stages = [1.0, 5.0]
    
    # Get copper routes
    valid_routes = get_mineral_processing_routes('copper')
    invalid_routes = get_invalid_mineral_routes('copper')
    
    print(f"Country stages: {kenya_stages}")
    print(f"Valid routes: {valid_routes}")
    print(f"Invalid routes: {invalid_routes}")
    print()
    
    # Check if this is an invalid route
    is_invalid, invalid_route_found = validate_route_sequence(kenya_stages, invalid_routes)
    
    if is_invalid:
        print(f"❌ INVALID ROUTE DETECTED: {invalid_route_found}")
        print("Question: Should we:")
        print("  A) Skip calculation entirely (zero value addition)")
        print("  B) Find best valid route match and calculate anyway") 
        print("  C) Use fallback sequential calculation")
        print()
        
        # Current behavior (Option B)
        from plot_config import find_matching_route
        matching_route = find_matching_route(kenya_stages, valid_routes)
        print(f"Current behavior (Option B): Find matching route = {matching_route}")
        print("  -> Calculates value addition despite invalid route")
        print()
        
        print("🤔 POLICY QUESTION:")
        print("Should countries with invalid processing routes (like 1→5 direct)")
        print("receive zero value addition, or should we use the best valid route?")
        print()
        print("Current implementation: Uses best valid route (may be too lenient)")
        print("Alternative: Zero value addition for invalid routes (more strict)")

if __name__ == "__main__":
    test_invalid_route_behavior()