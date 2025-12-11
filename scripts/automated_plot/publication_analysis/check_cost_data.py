"""
Check cost data columns and magnitudes in economic indicators
"""
import pandas as pd
import sys
import json

# Load config
with open('/home/karlac/critical_minerals_Africa/transport-critical-minerals/config.json', 'r') as f:
    config = json.load(f)

# Load data
df = pd.read_excel(config['paths']['results'] + '/all_data.xlsx')
df = df.reset_index() if hasattr(df, 'reset_index') else df

# Filter for processing only (stage > 0)
df_processing = df[df['processing_stage'] > 0].copy()

print("="*80)
print("COST COLUMN VERIFICATION FOR ECONOMIC INDICATORS")
print("="*80)

# Check available cost columns
print("\n1. Available cost-related columns:")
print("-" * 80)
cost_cols = [col for col in df.columns if 'cost' in col.lower() or 'opex' in col.lower() or 'investment' in col.lower()]
for col in cost_cols:
    print(f"  - {col}")

print("\n2. Cost breakdown for a sample scenario (Prec_U_N mid demand):")
print("-" * 80)

scenario_name = 'precursor_2040_mid_min_threshold_metal_tons'
constraint_col = 'country_unconstrained'

df_scenario = df_processing[
    (df_processing['scenario'] == scenario_name) &
    (df_processing['constraint'] == constraint_col)
].copy()

if not df_scenario.empty:
    production_cost = df_scenario['production_cost_usd'].sum()
    transport_cost = (df_scenario['export_transport_cost_usd'].sum() +
                     df_scenario['import_transport_cost_usd'].sum())
    energy_cost = (df_scenario['energy_investment_usd'].sum() +
                  df_scenario['energy_opex'].sum())
    all_cost = df_scenario['all_cost_usd'].sum()

    print(f"Production cost:  ${production_cost/1e9:.2f} Billion")
    print(f"Transport cost:   ${transport_cost/1e9:.2f} Billion")
    print(f"Energy cost:      ${energy_cost/1e9:.2f} Billion")
    print(f"Sum of above:     ${(production_cost + transport_cost + energy_cost)/1e9:.2f} Billion")
    print(f"'all_cost_usd':   ${all_cost/1e9:.2f} Billion")

    print(f"\nProduction cost is {production_cost/transport_cost:.1f}x transport cost")
    print(f"Production cost is {production_cost/energy_cost:.1f}x energy cost")

# Check what production_cost_usd contains
print("\n3. Checking production_cost_usd column values:")
print("-" * 80)
print(f"Non-zero values: {len(df_scenario[df_scenario['production_cost_usd'] != 0])}")
print(f"Mean (non-zero): ${df_scenario[df_scenario['production_cost_usd'] != 0]['production_cost_usd'].mean():.2f}")
print(f"Max value: ${df_scenario['production_cost_usd'].max():.2f}")

# Sample some rows
print("\nSample rows (first 10 with production cost > 0):")
sample = df_scenario[df_scenario['production_cost_usd'] > 0][['reference_mineral', 'iso3', 'processing_stage',
                                                                'production_cost_usd', 'export_transport_cost_usd',
                                                                'energy_investment_usd', 'energy_opex']].head(10)
print(sample.to_string())

# Check if there are other cost columns that might be relevant
print("\n4. Checking for other potential cost columns:")
print("-" * 80)
print("Stage 1 production cost column check:")
stage1_cols = [col for col in df.columns if 'stage_1' in col.lower() and 'cost' in col.lower()]
for col in stage1_cols:
    print(f"  - {col}")
    if col in df_scenario.columns:
        print(f"    Total: ${df_scenario[col].sum()/1e9:.2f} Billion")

# Compare production_cost_usd with production_tonnes and price
print("\n5. Checking if production_cost_usd relates to production volume:")
print("-" * 80)
sample_mineral = df_scenario[df_scenario['reference_mineral'] == 'copper'].head(5)
print("Sample copper rows:")
if 'production_tonnes_for_costs' in df_scenario.columns:
    print(sample_mineral[['iso3', 'processing_stage', 'production_tonnes', 'production_tonnes_for_costs',
                          'production_cost_usd']].to_string())
else:
    print(sample_mineral[['iso3', 'processing_stage', 'production_tonnes',
                          'production_cost_usd']].to_string())

# Check column descriptions or calculation
print("\n6. Checking column formula (if calculable):")
print("-" * 80)
if 'stage_1_production_cost_usd_per_tonne' in df_scenario.columns and 'production_tonnes_for_costs' in df_scenario.columns:
    df_scenario['calc_prod_cost'] = df_scenario['stage_1_production_cost_usd_per_tonne'] * df_scenario['production_tonnes_for_costs']
    diff = (df_scenario['production_cost_usd'] - df_scenario['calc_prod_cost']).abs().sum()
    print(f"Comparing production_cost_usd with stage_1_cost × production_tonnes_for_costs:")
    print(f"  Total difference: ${diff/1e9:.2f} Billion")

    # Sample comparison
    print("\nSample comparison (first 5 rows with production):")
    comparison = df_scenario[df_scenario['production_tonnes_for_costs'] > 0][
        ['reference_mineral', 'iso3', 'processing_stage', 'production_cost_usd', 'calc_prod_cost']
    ].head(5)
    print(comparison.to_string())
