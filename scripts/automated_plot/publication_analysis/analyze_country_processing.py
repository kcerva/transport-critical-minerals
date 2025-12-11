"""
Country-Level Processing Analysis by Type and Amount

Provides detailed breakdown of processing by country, showing:
- Processing volumes by type (Beneficiation, Early refining, Precursor)
- Breakdown across different scenarios
- Key messages about country-level processing patterns
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plot_config import mineral_processing_stages, reference_minerals

# Scenario configurations for analysis
SCENARIO_CONFIG = [
    # (goal, policy, constraint, label)
    ('baseline', None, None, 'Baseline'),
    ('bau', 'min', 'unconstrained', 'BAU_U_N'),
    ('bau', 'max', 'unconstrained', 'BAU_U_R'),
    ('precursor', 'min', 'constrained', 'Prec_C_N'),
    ('precursor', 'min', 'unconstrained', 'Prec_U_N'),
    ('precursor', 'max', 'constrained', 'Prec_C_R'),
    ('precursor', 'max', 'unconstrained', 'Prec_U_R'),
]

PROCESSING_TYPES = ['Beneficiation', 'Early refining', 'Precursor related product']


def get_processing_type(mineral, stage):
    """
    Get processing type for a given mineral and stage

    Args:
        mineral: Mineral name
        stage: Processing stage

    Returns:
        str: Processing type or None if stage not found
    """
    if mineral in mineral_processing_stages:
        stage_info = mineral_processing_stages[mineral]['stages'].get(stage)
        if stage_info:
            return stage_info['type']
    return None


def prepare_country_processing_by_type(df):
    """
    Prepare country-level processing data broken down by type

    Args:
        df: Main data DataFrame

    Returns:
        dict: Nested dict [scenario_label][demand][country][processing_type] = production_tonnes
    """
    df_processing = df[df['processing_stage'] > 0].copy()

    # Add processing type column
    df_processing['processing_type'] = df_processing.apply(
        lambda row: get_processing_type(row['reference_mineral'], row['processing_stage']),
        axis=1
    )

    # Filter out rows without processing type
    df_processing = df_processing[df_processing['processing_type'].notna()].copy()

    country_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        country_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        if goal == 'baseline':
            scenario_name = '2022_baseline'
            df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

            for demand in ['low', 'mid', 'high']:
                if not df_scenario.empty:
                    # Group by country and processing type
                    grouped = df_scenario.groupby(['iso3', 'processing_type'])['production_tonnes'].sum()

                    for (country, ptype), value in grouped.items():
                        if country not in country_data[label][demand]:
                            country_data[label][demand][country] = {}
                        country_data[label][demand][country][ptype] = value

        else:  # BAU and Precursor scenarios
            for demand in ['low', 'mid', 'high']:
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                df_scenario = df_processing[
                    (df_processing['scenario'] == scenario_name) &
                    (df_processing['constraint'] == constraint_col)
                ].copy()

                if not df_scenario.empty:
                    # Group by country and processing type
                    grouped = df_scenario.groupby(['iso3', 'processing_type'])['production_tonnes'].sum()

                    for (country, ptype), value in grouped.items():
                        if country not in country_data[label][demand]:
                            country_data[label][demand][country] = {}
                        country_data[label][demand][country][ptype] = value

    return country_data


def get_top_countries_by_processing(country_data, n=10):
    """
    Get top N countries by total processing volume across all scenarios

    Args:
        country_data: Country processing data dict
        n: Number of top countries

    Returns:
        list: Top N country ISO codes
    """
    country_totals = {}

    for label in country_data:
        for demand in ['low', 'mid', 'high']:
            for country, types in country_data[label][demand].items():
                if country not in country_totals:
                    country_totals[country] = 0
                country_totals[country] += sum(types.values())

    # Sort by total volume
    sorted_countries = sorted(country_totals.items(), key=lambda x: x[1], reverse=True)
    return [c[0] for c in sorted_countries[:n]]


def analyze_country_processing(country_data, top_countries):
    """
    Analyze country-level processing patterns with key messages

    Args:
        country_data: Country processing data dict
        top_countries: List of top countries to analyze

    Returns:
        dict: Analysis results and metrics
    """
    print("=" * 80)
    print("COUNTRY-LEVEL PROCESSING ANALYSIS BY TYPE")
    print("=" * 80)

    results = {}

    # Country name mapping for better readability
    country_names = {
        'ZAF': 'South Africa',
        'COD': 'DRC',
        'ZMB': 'Zambia',
        'ZWE': 'Zimbabwe',
        'MOZ': 'Mozambique',
        'NAM': 'Namibia',
        'BWA': 'Botswana',
        'TZA': 'Tanzania',
        'MDG': 'Madagascar',
        'AGO': 'Angola',
        'KEN': 'Kenya',
        'MWI': 'Malawi',
        'BDI': 'Burundi'
    }

    for country in top_countries:
        print(f"\n{'=' * 80}")
        print(f"COUNTRY: {country_names.get(country, country)} ({country})")
        print(f"{'=' * 80}")

        country_metrics = {}

        for label in ['Baseline', 'BAU_U_N', 'BAU_U_R', 'Prec_U_N', 'Prec_U_R']:
            if label not in country_data:
                continue

            print(f"\n{label}:")

            # Get mid demand data
            country_types = country_data[label]['mid'].get(country, {})

            if not country_types:
                print(f"  No processing activity")
                country_metrics[label] = {'total_mt': 0, 'by_type': {}}
                continue

            # Calculate total and by type
            total = sum(country_types.values())
            total_mt = total / 1e6

            print(f"  Total Processing: {total_mt:.3f} Mt")

            by_type = {}
            print(f"  By Processing Type:")
            for ptype in PROCESSING_TYPES:
                val = country_types.get(ptype, 0)
                val_mt = val / 1e6
                share = (val / total * 100) if total > 0 else 0

                if val > 0:
                    print(f"    {ptype}: {val_mt:.3f} Mt ({share:.1f}%)")
                    by_type[ptype] = {'mt': val_mt, 'share_pct': share}
                else:
                    by_type[ptype] = {'mt': 0, 'share_pct': 0}

            country_metrics[label] = {
                'total_mt': total_mt,
                'by_type': by_type
            }

        # Calculate growth rates
        if 'Baseline' in country_metrics and 'Prec_U_N' in country_metrics:
            baseline_total = country_metrics['Baseline']['total_mt']
            prec_total = country_metrics['Prec_U_N']['total_mt']

            if baseline_total > 0:
                growth = ((prec_total / baseline_total) - 1) * 100
                print(f"\n  Growth (Baseline → Prec_U_N): {growth:+.1f}%")

        # Compare National vs Regional (Precursor Unconstrained)
        if 'Prec_U_N' in country_metrics and 'Prec_U_R' in country_metrics:
            n_total = country_metrics['Prec_U_N']['total_mt']
            r_total = country_metrics['Prec_U_R']['total_mt']

            if n_total > 0:
                regional_diff = ((r_total / n_total) - 1) * 100
                print(f"  Regional vs National (Prec_U): {regional_diff:+.1f}%")

        results[country] = country_metrics

    return results


def generate_key_messages(country_data, results, top_countries):
    """
    Generate key messages about country processing patterns

    Args:
        country_data: Country processing data dict
        results: Analysis results from analyze_country_processing
        top_countries: List of top countries

    Returns:
        list: Key message strings
    """
    print("\n" + "=" * 80)
    print("KEY MESSAGES: COUNTRY PROCESSING PATTERNS")
    print("=" * 80)

    messages = []

    country_names = {
        'ZAF': 'South Africa',
        'COD': 'DRC',
        'ZMB': 'Zambia',
        'ZWE': 'Zimbabwe',
        'MOZ': 'Mozambique',
        'NAM': 'Namibia',
        'BWA': 'Botswana',
        'TZA': 'Tanzania',
        'MDG': 'Madagascar',
        'AGO': 'Angola',
        'KEN': 'Kenya',
        'MWI': 'Malawi',
        'BDI': 'Burundi'
    }

    # Message 1: Top processing countries in Precursor scenarios
    print("\n1. TOP PROCESSING COUNTRIES (Precursor Unconstrained National)")
    prec_totals = []
    for country in top_countries:
        if country in results and 'Prec_U_N' in results[country]:
            total = results[country]['Prec_U_N']['total_mt']
            prec_totals.append((country, total))

    prec_totals.sort(key=lambda x: x[1], reverse=True)
    top_5 = prec_totals[:5]

    msg = f"Top 5 processing countries (Prec_U_N): "
    msg += ", ".join([f"{country_names.get(c, c)} ({t:.2f} Mt)" for c, t in top_5])
    print(f"   {msg}")
    messages.append(msg)

    # Message 2: Countries with highest Precursor processing
    print("\n2. PRECURSOR PRODUCT PROCESSING LEADERS")
    precursor_leaders = []
    for country in top_countries:
        if country in results and 'Prec_U_N' in results[country]:
            by_type = results[country]['Prec_U_N']['by_type']
            precursor_mt = by_type.get('Precursor related product', {}).get('mt', 0)
            if precursor_mt > 0:
                precursor_leaders.append((country, precursor_mt))

    precursor_leaders.sort(key=lambda x: x[1], reverse=True)
    if precursor_leaders:
        top_precursor = precursor_leaders[:3]
        msg = f"Top precursor processors: "
        msg += ", ".join([f"{country_names.get(c, c)} ({v:.3f} Mt)" for c, v in top_precursor])
        print(f"   {msg}")
        messages.append(msg)

    # Message 3: Countries with highest growth from Baseline to Precursor
    print("\n3. HIGHEST GROWTH COUNTRIES (Baseline → Precursor)")
    growth_rates = []
    for country in top_countries:
        if country in results:
            baseline = results[country].get('Baseline', {}).get('total_mt', 0)
            precursor = results[country].get('Prec_U_N', {}).get('total_mt', 0)

            if baseline > 0.001:  # Only consider countries with baseline processing
                growth = ((precursor / baseline) - 1) * 100
                growth_rates.append((country, growth, baseline, precursor))

    growth_rates.sort(key=lambda x: x[1], reverse=True)
    if growth_rates:
        top_growth = growth_rates[:3]
        for c, g, b, p in top_growth:
            msg = f"{country_names.get(c, c)}: {g:+.1f}% growth ({b:.3f} Mt → {p:.3f} Mt)"
            print(f"   {msg}")
            messages.append(msg)

    # Message 4: Regional integration impact
    print("\n4. REGIONAL INTEGRATION IMPACT (National vs Regional, Precursor Unconstrained)")
    regional_impacts = []
    for country in top_countries:
        if country in results:
            national = results[country].get('Prec_U_N', {}).get('total_mt', 0)
            regional = results[country].get('Prec_U_R', {}).get('total_mt', 0)

            if national > 0.001:
                diff_pct = ((regional / national) - 1) * 100
                regional_impacts.append((country, diff_pct, national, regional))

    # Sort by absolute difference
    regional_impacts.sort(key=lambda x: abs(x[1]), reverse=True)
    if regional_impacts:
        # Biggest winners and losers
        top_3 = regional_impacts[:3]
        for c, d, n, r in top_3:
            direction = "gains" if d > 0 else "loses"
            msg = f"{country_names.get(c, c)} {direction} {abs(d):.1f}% with regional integration ({n:.3f} Mt → {r:.3f} Mt)"
            print(f"   {msg}")
            messages.append(msg)

    # Message 5: Processing type distribution in Precursor scenarios
    print("\n5. PROCESSING TYPE DISTRIBUTION (Precursor Unconstrained National)")
    for country in top_countries[:5]:  # Top 5 countries only
        if country in results and 'Prec_U_N' in results[country]:
            by_type = results[country]['Prec_U_N']['by_type']
            total = results[country]['Prec_U_N']['total_mt']

            if total > 0.01:  # Only countries with significant processing
                type_shares = []
                for ptype in PROCESSING_TYPES:
                    share = by_type.get(ptype, {}).get('share_pct', 0)
                    if share > 5:  # Only show types > 5%
                        type_shares.append(f"{ptype}: {share:.1f}%")

                if type_shares:
                    msg = f"{country_names.get(country, country)} processing mix: {', '.join(type_shares)}"
                    print(f"   {msg}")
                    messages.append(msg)

    return messages


def main():
    """Main analysis function"""
    print("Loading data...")

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    df = pd.read_excel(data_path)

    print(f"Loaded {len(df)} rows of data\n")

    # Prepare country-level processing data by type
    country_data = prepare_country_processing_by_type(df)

    # Get top countries
    top_countries = get_top_countries_by_processing(country_data, n=10)
    print(f"Top 10 processing countries: {', '.join(top_countries)}\n")

    # Analyze country patterns
    results = analyze_country_processing(country_data, top_countries)

    # Generate key messages
    messages = generate_key_messages(country_data, results, top_countries)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return {
        'country_data': country_data,
        'results': results,
        'key_messages': messages,
        'top_countries': top_countries
    }


if __name__ == '__main__':
    analysis = main()
