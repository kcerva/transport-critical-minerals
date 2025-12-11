import pandas as pd
import sys
sys.path.append('/home/karlac/critical_minerals_Africa/transport-critical-minerals/scripts/automated_plot')

# Load data
df = pd.read_excel('/home/karlac/critical_minerals_Africa/transport-outputs/results/all_data.xlsx')
df = df.reset_index() if hasattr(df, 'reset_index') else df
df_processing = df[df['processing_stage'] > 0].copy()

print('='*80)
print('PRODUCTION vs ENERGY for Problematic Scenarios')
print('='*80)

# Check Prec_U_N low demand
scenario_name = 'precursor_2040_low_min_threshold_metal_tons'
constraint_col = 'country_unconstrained'

df_scenario = df_processing[
    (df_processing['scenario'] == scenario_name) &
    (df_processing['constraint'] == constraint_col)
].copy()

print('\n1. Prec_U_N (low demand):')
print('-' * 80)
if not df_scenario.empty:
    by_mineral_prod = df_scenario.groupby('reference_mineral')['production_tonnes'].sum()
    by_mineral_energy = df_scenario.groupby('reference_mineral')['energy_req_capacity_kW'].sum()

    print(f"{'Mineral':<10} {'Production (tonnes)':<20} {'Energy (kW)':<20}")
    print('-' * 80)
    for mineral in ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']:
        prod = by_mineral_prod.get(mineral, 0)
        energy = by_mineral_energy.get(mineral, 0)
        print(f'{mineral:<10} {prod:<20.2f} {energy:<20.2f}')

    # Check total rows
    print(f'\nTotal rows in this scenario: {len(df_scenario)}')

    # Check for cobalt specifically
    cobalt_data = df_scenario[df_scenario['reference_mineral'] == 'cobalt']
    print(f'Cobalt rows: {len(cobalt_data)}')
    if len(cobalt_data) > 0:
        print('\nCobalt data sample (all rows):')
        print(cobalt_data[['iso3', 'processing_stage', 'production_tonnes', 'energy_req_capacity_kW']].to_string())

    # Check for copper specifically
    copper_data = df_scenario[df_scenario['reference_mineral'] == 'copper']
    print(f'\nCopper rows: {len(copper_data)}')
    if len(copper_data) > 0:
        print('\nCopper data sample (first 10):')
        print(copper_data[['iso3', 'processing_stage', 'production_tonnes', 'energy_req_capacity_kW']].head(10).to_string())
else:
    print('NO DATA FOUND')

# Check Prec_C_R low demand
scenario_name = 'precursor_2040_low_max_threshold_metal_tons'
constraint_col = 'region_constrained'

df_scenario = df_processing[
    (df_processing['scenario'] == scenario_name) &
    (df_processing['constraint'] == constraint_col)
].copy()

print('\n\n2. Prec_C_R (low demand):')
print('-' * 80)
if not df_scenario.empty:
    by_mineral_prod = df_scenario.groupby('reference_mineral')['production_tonnes'].sum()
    by_mineral_energy = df_scenario.groupby('reference_mineral')['energy_req_capacity_kW'].sum()

    print(f"{'Mineral':<10} {'Production (tonnes)':<20} {'Energy (kW)':<20}")
    print('-' * 80)
    for mineral in ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']:
        prod = by_mineral_prod.get(mineral, 0)
        energy = by_mineral_energy.get(mineral, 0)
        print(f'{mineral:<10} {prod:<20.2f} {energy:<20.2f}')

    # Check total rows
    print(f'\nTotal rows in this scenario: {len(df_scenario)}')

    # Check for cobalt specifically
    cobalt_data = df_scenario[df_scenario['reference_mineral'] == 'cobalt']
    print(f'Cobalt rows: {len(cobalt_data)}')
    if len(cobalt_data) > 0:
        print('\nCobalt data sample (all rows):')
        print(cobalt_data[['iso3', 'processing_stage', 'production_tonnes', 'energy_req_capacity_kW']].to_string())

    # Check for copper specifically
    copper_data = df_scenario[df_scenario['reference_mineral'] == 'copper']
    print(f'\nCopper rows: {len(copper_data)}')
    if len(copper_data) > 0:
        print('\nCopper data sample (first 10):')
        print(copper_data[['iso3', 'processing_stage', 'production_tonnes', 'energy_req_capacity_kW']].head(10).to_string())
else:
    print('NO DATA FOUND')

# Compare with a working scenario (Prec_U_N mid demand)
print('\n\n3. Prec_U_N (mid demand) - FOR COMPARISON:')
print('-' * 80)
scenario_name = 'precursor_2040_mid_min_threshold_metal_tons'
constraint_col = 'country_unconstrained'

df_scenario = df_processing[
    (df_processing['scenario'] == scenario_name) &
    (df_processing['constraint'] == constraint_col)
].copy()

if not df_scenario.empty:
    by_mineral_prod = df_scenario.groupby('reference_mineral')['production_tonnes'].sum()
    by_mineral_energy = df_scenario.groupby('reference_mineral')['energy_req_capacity_kW'].sum()

    print(f"{'Mineral':<10} {'Production (tonnes)':<20} {'Energy (kW)':<20}")
    print('-' * 80)
    for mineral in ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']:
        prod = by_mineral_prod.get(mineral, 0)
        energy = by_mineral_energy.get(mineral, 0)
        print(f'{mineral:<10} {prod:<20.2f} {energy:<20.2f}')
