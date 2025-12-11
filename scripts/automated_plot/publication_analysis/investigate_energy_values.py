"""
Investigate energy costs and capacity values across scenarios
"""
import os
import sys
import pandas as pd
import json

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load config
config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Load data
data_file = os.path.join(config['paths']['results'], 'all_data.xlsx')
df = pd.read_excel(data_file, index_col=[0,1,2,3,4]).reset_index()

# Filter for processing only (stage > 0)
df_processing = df[df['processing_stage'] > 0].copy()

print("="*80)
print("INVESTIGATING ENERGY CAPACITY AND COSTS")
print("="*80)

# Scenario configuration (same as in figure)
SCENARIO_CONFIG = [
    ('baseline', None, None, 'Baseline'),
    ('bau', 'min', 'constrained', 'BAU_C'),
    ('bau', 'min', 'unconstrained', 'BAU_U'),
    ('precursor', 'min', 'constrained', 'Prec_C_N'),
    ('precursor', 'min', 'unconstrained', 'Prec_U_N'),
    ('precursor', 'max', 'constrained', 'Prec_C_R'),
    ('precursor', 'max', 'unconstrained', 'Prec_U_R'),
]

print("\n1. ENERGY CAPACITY (energy_req_capacity_kW) by Scenario and Demand")
print("-" * 80)
print(f"{'Scenario':<15} {'Demand':<8} {'Total (GW)':<15} {'By Mineral (GW)'}")
print("-" * 80)

for goal, policy, constraint, label in SCENARIO_CONFIG:
    if goal == 'baseline':
        scenario_name = '2022_baseline'
        df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

        for demand in ['low', 'mid', 'high']:
            if df_scenario.empty:
                print(f"{label:<15} {demand:<8} NO DATA")
                continue

            total = df_scenario['energy_req_capacity_kW'].sum() / 1e6  # Convert to GW
            by_mineral = df_scenario.groupby('reference_mineral')['energy_req_capacity_kW'].sum() / 1e6

            mineral_str = ", ".join([f"{m[:2]}:{v:.2f}" for m, v in by_mineral.items()])
            print(f"{label:<15} {demand:<8} {total:<15.2f} {mineral_str}")
    else:
        for demand in ['low', 'mid', 'high']:
            scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
            constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

            df_scenario = df_processing[
                (df_processing['scenario'] == scenario_name) &
                (df_processing['constraint'] == constraint_col)
            ].copy()

            if df_scenario.empty:
                print(f"{label:<15} {demand:<8} NO DATA")
                continue

            total = df_scenario['energy_req_capacity_kW'].sum() / 1e6  # Convert to GW
            by_mineral = df_scenario.groupby('reference_mineral')['energy_req_capacity_kW'].sum() / 1e6

            mineral_str = ", ".join([f"{m[:2]}:{v:.2f}" for m, v in by_mineral.items()])
            print(f"{label:<15} {demand:<8} {total:<15.2f} {mineral_str}")

print("\n" + "="*80)
print("2. ENERGY COSTS (Investment + Opex) by Scenario and Demand")
print("-" * 80)
print(f"{'Scenario':<15} {'Demand':<8} {'Investment (B$)':<18} {'Opex (B$)':<15} {'Total (B$)':<15}")
print("-" * 80)

for goal, policy, constraint, label in SCENARIO_CONFIG:
    if goal == 'baseline':
        scenario_name = '2022_baseline'
        df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

        for demand in ['low', 'mid', 'high']:
            if df_scenario.empty:
                print(f"{label:<15} {demand:<8} NO DATA")
                continue

            investment = df_scenario['energy_investment_usd'].sum() / 1e9
            opex = df_scenario['energy_opex'].sum() / 1e9
            total = investment + opex

            print(f"{label:<15} {demand:<8} {investment:<18.2f} {opex:<15.2f} {total:<15.2f}")
    else:
        for demand in ['low', 'mid', 'high']:
            scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
            constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

            df_scenario = df_processing[
                (df_processing['scenario'] == scenario_name) &
                (df_processing['constraint'] == constraint_col)
            ].copy()

            if df_scenario.empty:
                print(f"{label:<15} {demand:<8} NO DATA")
                continue

            investment = df_scenario['energy_investment_usd'].sum() / 1e9
            opex = df_scenario['energy_opex'].sum() / 1e9
            total = investment + opex

            print(f"{label:<15} {demand:<8} {investment:<18.2f} {opex:<15.2f} {total:<15.2f}")

print("\n" + "="*80)
print("3. CHECK FOR ZERO OR NEAR-ZERO VALUES")
print("-" * 80)

# Check which scenarios have very low values
threshold = 0.01  # 0.01 GW or 0.01 B$

for goal, policy, constraint, label in SCENARIO_CONFIG:
    if goal == 'baseline':
        scenario_name = '2022_baseline'
        df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

        for demand in ['low', 'mid', 'high']:
            if df_scenario.empty:
                continue

            capacity = df_scenario['energy_req_capacity_kW'].sum() / 1e6
            investment = df_scenario['energy_investment_usd'].sum() / 1e9
            opex = df_scenario['energy_opex'].sum() / 1e9

            if capacity < threshold or investment < threshold or opex < threshold:
                print(f"⚠ {label} {demand}: capacity={capacity:.4f}GW, invest={investment:.4f}B$, opex={opex:.4f}B$")
    else:
        for demand in ['low', 'mid', 'high']:
            scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
            constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

            df_scenario = df_processing[
                (df_processing['scenario'] == scenario_name) &
                (df_processing['constraint'] == constraint_col)
            ].copy()

            if df_scenario.empty:
                continue

            capacity = df_scenario['energy_req_capacity_kW'].sum() / 1e6
            investment = df_scenario['energy_investment_usd'].sum() / 1e9
            opex = df_scenario['energy_opex'].sum() / 1e9

            if capacity < threshold or investment < threshold or opex < threshold:
                print(f"⚠ {label} {demand}: capacity={capacity:.4f}GW, invest={investment:.4f}B$, opex={opex:.4f}B$")

print("\n" + "="*80)
print("4. SAMPLE RAW DATA FOR PROBLEMATIC SCENARIOS")
print("-" * 80)

# Show raw data for a few rows of potentially problematic scenarios
for label_check in ['BAU_C', 'BAU_U', 'Prec_C_N', 'Prec_U_N']:
    goal_map = {'BAU_C': 'bau', 'BAU_U': 'bau', 'Prec_C_N': 'precursor', 'Prec_U_N': 'precursor'}
    policy_map = {'BAU_C': 'min', 'BAU_U': 'min', 'Prec_C_N': 'min', 'Prec_U_N': 'min'}
    constraint_map = {'BAU_C': 'constrained', 'BAU_U': 'unconstrained',
                      'Prec_C_N': 'constrained', 'Prec_U_N': 'unconstrained'}

    goal = goal_map[label_check]
    policy = policy_map[label_check]
    constraint = constraint_map[label_check]

    scenario_name = f'{goal}_2040_low_{policy}_threshold_metal_tons'
    constraint_col = f'country_{constraint}'

    df_scenario = df_processing[
        (df_processing['scenario'] == scenario_name) &
        (df_processing['constraint'] == constraint_col)
    ].copy()

    if not df_scenario.empty:
        print(f"\n{label_check} (low demand) - First 3 rows:")
        cols_to_show = ['reference_mineral', 'iso3', 'processing_stage', 'production_tonnes',
                       'energy_req_capacity_kW', 'energy_investment_usd', 'energy_opex']
        print(df_scenario[cols_to_show].head(3).to_string())