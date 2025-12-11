"""
Quick check to verify transport emissions discrepancy
"""
import os
import sys
import json
import pandas as pd

# Load config
config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Load data
data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
df = pd.read_excel(data_path)

print("Checking transport emissions columns...")
print(f"Total rows: {len(df)}")

# Check which columns exist
transport_cols = [col for col in df.columns if 'transport' in col.lower() and 'co2' in col.lower()]
print(f"\nTransport CO2 columns found:")
for col in transport_cols:
    print(f"  - {col}")

# Filter for processing only (stage > 0)
df_processing = df[df['processing_stage'] > 0].copy()

# Calculate transport emissions both ways for a sample scenario
sample_scenario = 'bau_2040_mid_min_threshold_metal_tons'
sample_constraint = 'country_unconstrained'

df_sample = df_processing[
    (df_processing['scenario'] == sample_scenario) &
    (df_processing['constraint'] == sample_constraint)
].copy()

print(f"\nSample scenario: {sample_scenario}, {sample_constraint}")
print(f"Number of rows: {len(df_sample)}")

if len(df_sample) > 0:
    # Calculate using export + import
    if 'transport_export_tonsCO2eq' in df_sample.columns and 'transport_import_tonsCO2eq' in df_sample.columns:
        total_export = df_sample['transport_export_tonsCO2eq'].sum()
        total_import = df_sample['transport_import_tonsCO2eq'].sum()
        calculated_sum = total_export + total_import

        print(f"\nMethod 1 (Export + Import):")
        print(f"  Export:  {total_export:,.0f} tons CO2eq")
        print(f"  Import:  {total_import:,.0f} tons CO2eq")
        print(f"  Sum:     {calculated_sum:,.0f} tons CO2eq")

    # Check if transport_total_tonsCO2eq exists
    if 'transport_total_tonsCO2eq' in df_sample.columns:
        total_transport = df_sample['transport_total_tonsCO2eq'].sum()
        print(f"\nMethod 2 (Total Column):")
        print(f"  Total:   {total_transport:,.0f} tons CO2eq")

        if 'transport_export_tonsCO2eq' in df_sample.columns and 'transport_import_tonsCO2eq' in df_sample.columns:
            difference = total_transport - calculated_sum
            pct_diff = (difference / calculated_sum * 100) if calculated_sum > 0 else 0
            print(f"\nDifference:")
            print(f"  Absolute: {difference:,.0f} tons CO2eq")
            print(f"  Percent:  {pct_diff:.2f}%")
    else:
        print("\n  transport_total_tonsCO2eq column NOT FOUND!")

# Check a few more scenarios
print("\n" + "="*80)
print("Checking multiple scenarios:")
print("="*80)

scenarios_to_check = [
    ('2022_baseline', None),
    ('bau_2040_mid_min_threshold_metal_tons', 'country_constrained'),
    ('bau_2040_mid_min_threshold_metal_tons', 'country_unconstrained'),
    ('precursor_2040_mid_min_threshold_metal_tons', 'country_unconstrained'),
    ('precursor_2040_mid_max_threshold_metal_tons', 'region_unconstrained'),
]

for scenario, constraint in scenarios_to_check:
    if constraint:
        df_check = df_processing[
            (df_processing['scenario'] == scenario) &
            (df_processing['constraint'] == constraint)
        ].copy()
        label = f"{scenario} / {constraint}"
    else:
        df_check = df_processing[df_processing['scenario'] == scenario].copy()
        label = scenario

    if len(df_check) > 0:
        if 'transport_export_tonsCO2eq' in df_check.columns and 'transport_import_tonsCO2eq' in df_check.columns:
            calc_sum = df_check['transport_export_tonsCO2eq'].sum() + df_check['transport_import_tonsCO2eq'].sum()
        else:
            calc_sum = 0

        if 'transport_total_tonsCO2eq' in df_check.columns:
            total = df_check['transport_total_tonsCO2eq'].sum()
        else:
            total = 0

        diff = total - calc_sum

        print(f"\n{label}:")
        print(f"  Export+Import: {calc_sum:,.0f}")
        print(f"  Total column:  {total:,.0f}")
        print(f"  Difference:    {diff:,.0f} ({(diff/calc_sum*100) if calc_sum > 0 else 0:.2f}%)")
