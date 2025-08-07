"""
Test script to fix the scenario filtering issues
"""
import pandas as pd

def test_scenario_filtering():
    """Test and fix scenario filtering logic"""
    
    # Load data
    df = pd.read_excel('/home/karlac/critical_minerals_Africa/transport-outputs/results/all_data.xlsx')
    zambia_data = df[df['iso3'] == 'ZMB'].copy()
    
    print('=== FIXING THE REGEX PATTERN ISSUE ===')
    
    # Test individual components
    print('\n1. Testing individual components:')
    bau_matches = zambia_data['scenario'].str.contains('bau_2040', na=False)
    early_matches = zambia_data['scenario'].str.contains('early_refining_2040', na=False)  
    precursor_matches = zambia_data['scenario'].str.contains('precursor_2040', na=False)
    baseline_matches = zambia_data['scenario'].str.contains('2022_baseline', na=False)
    
    print(f'BAU matches: {bau_matches.sum()}')
    print(f'Early refining matches: {early_matches.sum()}')  
    print(f'Precursor matches: {precursor_matches.sum()}')
    print(f'Baseline matches: {baseline_matches.sum()}')
    
    # Combine using boolean OR
    print('\n2. Testing combined boolean logic:')
    combined_mask = bau_matches | early_matches | precursor_matches | baseline_matches
    print(f'Combined boolean OR: {combined_mask.sum()}')
    
    # Apply filtering steps
    step1_filtered = zambia_data[combined_mask].copy()
    print(f'After scenario filtering: {len(step1_filtered)} records')
    
    # Apply constraint filtering
    step2_filtered = step1_filtered[
        step1_filtered['constraint'].isin(['country_unconstrained', 'region_unconstrained', 'country_constrained', 'region_constrained'])
    ].copy()
    print(f'After constraint filtering: {len(step2_filtered)} records')
    
    # Apply mid filtering
    step3_filtered = step2_filtered[
        step2_filtered['scenario'].str.contains('mid_min|mid_max|2022_baseline', na=False)
    ].copy()
    print(f'After mid filtering: {len(step3_filtered)} records')
    
    print('\n3. Final breakdown by scenario and constraint:')
    if len(step3_filtered) > 0:
        breakdown = step3_filtered.groupby(['scenario', 'constraint']).size().reset_index(name='count')
        for _, row in breakdown.iterrows():
            print(f'  {row["scenario"]} + {row["constraint"]}: {row["count"]} records')
            
        # Check water data
        water_data = step3_filtered[step3_filtered['water_usage_m3'] > 0]
        print(f'\nWater records in corrected filter: {len(water_data)}')
        print(f'Total water: {water_data["water_usage_m3"].sum():.2e} m³')
        
        if len(water_data) > 0:
            water_by_constraint = water_data.groupby('constraint')['water_usage_m3'].agg(['count', 'sum'])
            print('Water by constraint:')
            for constraint, data in water_by_constraint.iterrows():
                print(f'  {constraint}: {data["count"]} records, {data["sum"]:.2e} m³')
                
    return step3_filtered

def test_alternative_mid_only_approach():
    """Test alternative approach: focus on mid scenarios only"""
    
    df = pd.read_excel('/home/karlac/critical_minerals_Africa/transport-outputs/results/all_data.xlsx')
    zambia_data = df[df['iso3'] == 'ZMB'].copy()
    
    print('\n=== ALTERNATIVE: MID-SCENARIOS ONLY ===')
    
    # Get all mid scenarios + baseline
    mid_scenarios = zambia_data[
        (zambia_data['scenario'].str.contains('mid_min|mid_max', na=False)) |
        (zambia_data['scenario'] == '2022_baseline')
    ].copy()
    
    print(f'Mid scenarios + baseline: {len(mid_scenarios)} records')
    
    # Apply constraint filtering
    filtered_scenarios = mid_scenarios[
        mid_scenarios['constraint'].isin(['country_unconstrained', 'region_unconstrained', 'country_constrained', 'region_constrained'])
    ].copy()
    
    print(f'After constraint filtering: {len(filtered_scenarios)} records')
    
    # Check water data
    water_data = filtered_scenarios[filtered_scenarios['water_usage_m3'] > 0]
    print(f'Water records: {len(water_data)}')
    print(f'Total water: {water_data["water_usage_m3"].sum():.2e} m³')
    
    if len(water_data) > 0:
        water_by_constraint = water_data.groupby('constraint')['water_usage_m3'].agg(['count', 'sum'])
        print('Water by constraint:')
        for constraint, data in water_by_constraint.iterrows():
            print(f'  {constraint}: {data["count"]} records, {data["sum"]:.2e} m³')
    
    return filtered_scenarios

if __name__ == "__main__":
    fixed_data = test_scenario_filtering()
    alternative_data = test_alternative_mid_only_approach()