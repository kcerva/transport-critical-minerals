"""
Check if countries gain processing shares under environmental constraints (regional case)
"""
import pandas as pd

# Load data
df = pd.read_excel('/home/karlac/critical_minerals_Africa/transport-outputs/results/all_data.xlsx')
df = df.reset_index() if hasattr(df, 'reset_index') else df

# Filter for processing only (stage > 0)
df_processing = df[df['processing_stage'] > 0].copy()

print('PRODUCTION SHARE ANALYSIS: Regional Case with Environmental Constraints')
print('='*80)
print('Countries to check: South Africa, Tanzania, Namibia, Botswana, Mozambique')
print('Comparing: Regional Constrained vs Regional Unconstrained (Precursor scenarios)')
print()

countries_to_check = ['ZAF', 'TZA', 'NAM', 'BWA', 'MOZ']
country_names = {
    'ZAF': 'South Africa',
    'TZA': 'Tanzania',
    'NAM': 'Namibia',
    'BWA': 'Botswana',
    'MOZ': 'Mozambique'
}

# Regional Unconstrained (Prec_U_R)
df_unconstrained = df_processing[
    (df_processing['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
    (df_processing['constraint'] == 'region_unconstrained')
].copy()

# Regional Constrained (Prec_C_R)
df_constrained = df_processing[
    (df_processing['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
    (df_processing['constraint'] == 'region_constrained')
].copy()

# Calculate total production for each
total_unconstrained = df_unconstrained['production_tonnes'].sum()
total_constrained = df_constrained['production_tonnes'].sum()

print('TOTAL PRODUCTION SHARES BY COUNTRY:')
print('-'*80)
print(f"{'Country':<20} {'Unconstrained':<25} {'Constrained':<25} {'Change (pp)':<15}")
print('-'*80)

gains = {}
for country in countries_to_check:
    prod_unconstrained = df_unconstrained[df_unconstrained['iso3'] == country]['production_tonnes'].sum()
    prod_constrained = df_constrained[df_constrained['iso3'] == country]['production_tonnes'].sum()

    share_unconstrained = (prod_unconstrained / total_unconstrained * 100) if total_unconstrained > 0 else 0
    share_constrained = (prod_constrained / total_constrained * 100) if total_constrained > 0 else 0

    change = share_constrained - share_unconstrained
    gains[country] = change

    unc_str = f"{share_unconstrained:.2f}% ({prod_unconstrained/1e6:.2f}Mt)"
    con_str = f"{share_constrained:.2f}% ({prod_constrained/1e6:.2f}Mt)"

    marker = "✓ GAIN" if change > 0 else "✗ LOSS" if change < 0 else "="

    print(f"{country_names[country]:<20} {unc_str:<25} {con_str:<25} {change:>+7.2f} {marker}")

print()
print('SUMMARY:')
print('-'*80)
gainers = [c for c in countries_to_check if gains[c] > 0]
losers = [c for c in countries_to_check if gains[c] < 0]

if gainers:
    print(f"Countries that GAIN processing shares: {', '.join([country_names[c] for c in gainers])}")
if losers:
    print(f"Countries that LOSE processing shares: {', '.join([country_names[c] for c in losers])}")

print()
print('BREAKDOWN BY PROCESSING TYPE FOR GAINERS:')
print('='*80)

for country in gainers if gainers else []:
    print(f'\n{country_names[country]} ({country}):')
    print('-'*80)

    unconstrained_by_type = df_unconstrained[df_unconstrained['iso3'] == country].groupby('processing_type')['production_tonnes'].sum()
    constrained_by_type = df_constrained[df_constrained['iso3'] == country].groupby('processing_type')['production_tonnes'].sum()

    all_types = sorted(set(unconstrained_by_type.index) | set(constrained_by_type.index))

    if all_types:
        print(f"{'Processing Type':<30} {'Unconstrained (kt)':<20} {'Constrained (kt)':<20} {'Change':<15}")
        for ptype in all_types:
            unc_val = unconstrained_by_type.get(ptype, 0) / 1e3
            con_val = constrained_by_type.get(ptype, 0) / 1e3
            change = con_val - unc_val
            pct_change = ((con_val / unc_val - 1) * 100) if unc_val > 0 else 0

            print(f'{ptype:<30} {unc_val:>18.1f}  {con_val:>18.1f}  {change:>+7.1f}kt ({pct_change:>+6.1f}%)')

print()
print('BREAKDOWN BY MINERAL FOR GAINERS:')
print('='*80)

for country in gainers if gainers else []:
    print(f'\n{country_names[country]} ({country}):')
    print('-'*80)

    unconstrained_by_mineral = df_unconstrained[df_unconstrained['iso3'] == country].groupby('reference_mineral')['production_tonnes'].sum()
    constrained_by_mineral = df_constrained[df_constrained['iso3'] == country].groupby('reference_mineral')['production_tonnes'].sum()

    all_minerals = sorted(set(unconstrained_by_mineral.index) | set(constrained_by_mineral.index))

    if all_minerals:
        print(f"{'Mineral':<15} {'Unconstrained (kt)':<20} {'Constrained (kt)':<20} {'Change':<20}")
        for mineral in all_minerals:
            unc_val = unconstrained_by_mineral.get(mineral, 0) / 1e3
            con_val = constrained_by_mineral.get(mineral, 0) / 1e3
            change = con_val - unc_val
            pct_change = ((con_val / unc_val - 1) * 100) if unc_val > 0 else 0

            print(f'{mineral:<15} {unc_val:>18.1f}  {con_val:>18.1f}  {change:>+7.1f}kt ({pct_change:>+6.1f}%)')
