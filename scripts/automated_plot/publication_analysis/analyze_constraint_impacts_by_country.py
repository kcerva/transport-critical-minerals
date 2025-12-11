"""
Country-Level Constrained vs Unconstrained Processing Impact Analysis

Identifies which countries GAIN or LOSE processing under environmental constraints,
broken down by processing type (Beneficiation, Early refining, Precursor).
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plot_config import mineral_processing_stages

# Processing type order
PROCESSING_TYPES = ['Beneficiation', 'Early refining', 'Precursor related product']

# Country name mapping
COUNTRY_NAMES = {
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
    'BDI': 'Burundi',
    'UGA': 'Uganda'
}


def get_processing_type(mineral, stage):
    """Get processing type for a given mineral and stage"""
    if mineral in mineral_processing_stages:
        stage_info = mineral_processing_stages[mineral]['stages'].get(stage)
        if stage_info:
            return stage_info['type']
    return None


def get_country_processing_by_type(df, scenario_name, constraint_col):
    """
    Get country-level processing volumes by type for a specific scenario

    Returns:
        dict: {country: {processing_type: volume_tonnes}}
    """
    df_processing = df[df['processing_stage'] > 0].copy()

    # Add processing type
    df_processing['processing_type'] = df_processing.apply(
        lambda row: get_processing_type(row['reference_mineral'], row['processing_stage']),
        axis=1
    )

    # Filter for scenario
    df_scenario = df_processing[
        (df_processing['scenario'] == scenario_name) &
        (df_processing['constraint'] == constraint_col)
    ].copy()

    # Group by country and processing type
    country_data = {}

    if not df_scenario.empty:
        grouped = df_scenario.groupby(['iso3', 'processing_type'])['production_tonnes'].sum()

        for (country, ptype), value in grouped.items():
            if country not in country_data:
                country_data[country] = {}
            country_data[country][ptype] = value

    return country_data


def compare_constrained_unconstrained(df, goal='bau', policy='min', demand='mid'):
    """
    Compare constrained vs unconstrained for a given scenario

    Args:
        df: Main data DataFrame
        goal: 'bau' or 'precursor'
        policy: 'min' (National) or 'max' (Regional)
        demand: 'low', 'mid', or 'high'

    Returns:
        dict: Country-level comparison data
    """
    scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'

    constraint_col = f'country_constrained' if policy == 'min' else f'region_constrained'
    unconstrain_col = f'country_unconstrained' if policy == 'min' else f'region_unconstrained'

    # Get data for both constraints
    constrained_data = get_country_processing_by_type(df, scenario_name, constraint_col)
    unconstrained_data = get_country_processing_by_type(df, scenario_name, unconstrain_col)

    # Get all countries
    all_countries = set(list(constrained_data.keys()) + list(unconstrained_data.keys()))

    # Calculate differences
    comparison = {}

    for country in all_countries:
        c_data = constrained_data.get(country, {})
        u_data = unconstrained_data.get(country, {})

        country_comp = {
            'constrained': {},
            'unconstrained': {},
            'difference': {},
            'pct_change': {}
        }

        for ptype in PROCESSING_TYPES:
            c_val = c_data.get(ptype, 0)
            u_val = u_data.get(ptype, 0)
            diff = u_val - c_val

            if c_val > 0:
                pct = (diff / c_val) * 100
            elif u_val > 0:
                pct = float('inf')
            else:
                pct = 0

            country_comp['constrained'][ptype] = c_val
            country_comp['unconstrained'][ptype] = u_val
            country_comp['difference'][ptype] = diff
            country_comp['pct_change'][ptype] = pct

        # Calculate totals
        c_total = sum(c_data.values())
        u_total = sum(u_data.values())
        diff_total = u_total - c_total
        pct_total = ((diff_total / c_total) * 100) if c_total > 0 else (float('inf') if u_total > 0 else 0)

        country_comp['constrained']['Total'] = c_total
        country_comp['unconstrained']['Total'] = u_total
        country_comp['difference']['Total'] = diff_total
        country_comp['pct_change']['Total'] = pct_total

        comparison[country] = country_comp

    return comparison


def analyze_constraint_impacts(comparison_data, scenario_label):
    """Analyze and report constraint impacts"""

    print("\n" + "=" * 80)
    print(f"SCENARIO: {scenario_label}")
    print("=" * 80)

    # Separate gainers and losers
    gainers = {}
    losers = {}
    neutral = {}

    for country, data in comparison_data.items():
        diff_total = data['difference']['Total']

        if diff_total > 1000:  # Threshold: 1 kt
            gainers[country] = data
        elif diff_total < -1000:
            losers[country] = data
        else:
            neutral[country] = data

    # Report gainers
    if gainers:
        print(f"\n{'COUNTRIES THAT GAIN PROCESSING UNDER CONSTRAINTS':^80}")
        print("-" * 80)
        print(f"{'Country':<20} {'Total Change':<15} {'% Change':<12} {'Key Processing Types'}")
        print("-" * 80)

        # Sort by total gain
        sorted_gainers = sorted(gainers.items(),
                               key=lambda x: x[1]['difference']['Total'],
                               reverse=True)

        for country, data in sorted_gainers:
            name = COUNTRY_NAMES.get(country, country)
            total_diff = data['difference']['Total'] / 1e6  # Mt
            pct_change = data['pct_change']['Total']

            # Identify which processing types gained
            type_gains = []
            for ptype in PROCESSING_TYPES:
                diff = data['difference'].get(ptype, 0)
                if diff > 1000:  # > 1 kt gain
                    type_gains.append(f"{ptype}: +{diff/1e6:.3f} Mt")

            if pct_change == float('inf'):
                pct_str = "NEW"
            else:
                pct_str = f"{pct_change:+.1f}%"

            type_str = "; ".join(type_gains) if type_gains else "All types"

            print(f"{name:<20} {total_diff:>+8.3f} Mt   {pct_str:<12} {type_str}")
    else:
        print(f"\n{'NO COUNTRIES GAIN PROCESSING UNDER CONSTRAINTS':^80}")

    # Report losers
    if losers:
        print(f"\n{'COUNTRIES THAT LOSE PROCESSING UNDER CONSTRAINTS':^80}")
        print("-" * 80)
        print(f"{'Country':<20} {'Total Change':<15} {'% Change':<12} {'Key Processing Types'}")
        print("-" * 80)

        # Sort by total loss (most negative first)
        sorted_losers = sorted(losers.items(),
                              key=lambda x: x[1]['difference']['Total'])

        for country, data in sorted_losers:
            name = COUNTRY_NAMES.get(country, country)
            total_diff = data['difference']['Total'] / 1e6  # Mt
            pct_change = data['pct_change']['Total']

            # Identify which processing types lost
            type_losses = []
            for ptype in PROCESSING_TYPES:
                diff = data['difference'].get(ptype, 0)
                if diff < -1000:  # > 1 kt loss
                    type_losses.append(f"{ptype}: {diff/1e6:.3f} Mt")

            type_str = "; ".join(type_losses) if type_losses else "All types"

            print(f"{name:<20} {total_diff:>+8.3f} Mt   {pct_change:+.1f}%     {type_str}")

    # Summary statistics
    print(f"\n{'SUMMARY':^80}")
    print("-" * 80)
    print(f"  Countries gaining processing:  {len(gainers)}")
    print(f"  Countries losing processing:   {len(losers)}")
    print(f"  Countries largely unchanged:   {len(neutral)}")

    if gainers:
        total_gain = sum(d['difference']['Total'] for d in gainers.values()) / 1e6
        print(f"  Total volume gained:           {total_gain:+.3f} Mt")

    if losers:
        total_loss = sum(d['difference']['Total'] for d in losers.values()) / 1e6
        print(f"  Total volume lost:             {total_loss:+.3f} Mt")

    return gainers, losers, neutral


def detailed_country_breakdown(country, data, scenario_label):
    """Print detailed breakdown for a specific country"""
    name = COUNTRY_NAMES.get(country, country)

    print(f"\n{'=' * 80}")
    print(f"{name} - DETAILED BREAKDOWN ({scenario_label})")
    print(f"{'=' * 80}")

    print(f"\n{'Processing Type':<30} {'Constrained':<15} {'Unconstrained':<15} {'Change':<15} {'% Change'}")
    print("-" * 80)

    for ptype in PROCESSING_TYPES + ['Total']:
        c_val = data['constrained'].get(ptype, 0) / 1e6
        u_val = data['unconstrained'].get(ptype, 0) / 1e6
        diff = data['difference'].get(ptype, 0) / 1e6
        pct = data['pct_change'].get(ptype, 0)

        if pct == float('inf'):
            pct_str = "NEW"
        else:
            pct_str = f"{pct:+.1f}%"

        if ptype == 'Total':
            print("-" * 80)

        print(f"{ptype:<30} {c_val:>8.3f} Mt    {u_val:>8.3f} Mt    {diff:>+8.3f} Mt   {pct_str}")


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

    # Analyze different scenarios
    scenarios = [
        ('bau', 'min', 'mid', 'BAU National (mid demand)'),
        ('precursor', 'min', 'mid', 'Precursor National (mid demand)'),
        ('precursor', 'max', 'mid', 'Precursor Regional (mid demand)'),
    ]

    all_results = {}

    for goal, policy, demand, label in scenarios:
        print("\n" + "=" * 80)
        print(f"ANALYZING: {label}")
        print("=" * 80)

        comparison = compare_constrained_unconstrained(df, goal, policy, demand)
        gainers, losers, neutral = analyze_constraint_impacts(comparison, label)

        all_results[label] = {
            'comparison': comparison,
            'gainers': gainers,
            'losers': losers,
            'neutral': neutral
        }

    # Detailed breakdowns for interesting cases
    print("\n\n" + "=" * 80)
    print("DETAILED COUNTRY BREAKDOWNS")
    print("=" * 80)

    # Show detailed breakdown for top gainers and losers in each scenario
    for label, results in all_results.items():
        if results['gainers']:
            # Show top gainer
            top_gainer = max(results['gainers'].items(),
                           key=lambda x: x[1]['difference']['Total'])
            country, data = top_gainer
            detailed_country_breakdown(country, data, label)

        if results['losers']:
            # Show top loser
            top_loser = min(results['losers'].items(),
                          key=lambda x: x[1]['difference']['Total'])
            country, data = top_loser
            detailed_country_breakdown(country, data, label)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return all_results


if __name__ == '__main__':
    results = main()
