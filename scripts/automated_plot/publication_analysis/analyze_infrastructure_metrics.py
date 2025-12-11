"""
Infrastructure Indicators Key Metrics Analysis

Extracts key metrics from infrastructure indicators figure data for paper reporting.
Uses the same data processing logic as figure_infrastructure_indicators.py
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the figure generation script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from figure_infrastructure_indicators import (
    prepare_infrastructure_data,
    SCENARIO_CONFIG,
    MINERAL_ORDER,
    ENERGY_COST_ORDER
)


def analyze_transport_by_mineral(transport_data):
    """
    Analyze Panel A: Transport Volume by Mineral
    """
    print("=" * 80)
    print("PANEL A: TRANSPORT VOLUME BY MINERAL")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(transport_data[label]['low'].values())  # Already in Million tonkm
        total_mid = sum(transport_data[label]['mid'].values())
        total_high = sum(transport_data[label]['high'].values())

        print(f"  Total Transport: {total_mid:.0f} Million tonkm (range: {total_low:.0f}-{total_high:.0f})")

        metrics[label] = {
            'total_million_tonkm': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = transport_data[label]['low'].get(mineral, 0)
            val_mid = transport_data[label]['mid'].get(mineral, 0)
            val_high = transport_data[label]['high'].get(mineral, 0)

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: {val_mid:.0f} M tonkm ({share:.1f}%) [{val_low:.0f}-{val_high:.0f}]")

            metrics[label]['by_mineral'][mineral] = {
                'million_tonkm': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['total_million_tonkm']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['total_million_tonkm']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0
        print(f"  {label} vs Baseline: {growth_pct:+.1f}%")

    # Precursor vs BAU
    bau_u_mid = metrics['BAU_U']['total_million_tonkm']['mid']
    prec_u_n_mid = metrics['Prec_U_N']['total_million_tonkm']['mid']
    prec_u_r_mid = metrics['Prec_U_R']['total_million_tonkm']['mid']

    print(f"  Prec_U_N vs BAU_U: {((prec_u_n_mid/bau_u_mid)-1)*100:+.1f}%")
    print(f"  Prec_U_R vs BAU_U: {((prec_u_r_mid/bau_u_mid)-1)*100:+.1f}%")
    print(f"  Prec_U_R vs Prec_U_N: {((prec_u_r_mid/prec_u_n_mid)-1)*100:+.1f}%")

    return metrics


def analyze_energy_by_mineral(energy_data):
    """
    Analyze Panel B: Energy Capacity by Mineral
    """
    print("\n" + "=" * 80)
    print("PANEL B: ENERGY CAPACITY BY MINERAL")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(energy_data[label]['low'].values())  # Already in GW
        total_mid = sum(energy_data[label]['mid'].values())
        total_high = sum(energy_data[label]['high'].values())

        print(f"  Total Energy Capacity: {total_mid:.1f} GW (range: {total_low:.1f}-{total_high:.1f})")

        metrics[label] = {
            'total_gw': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = energy_data[label]['low'].get(mineral, 0)
            val_mid = energy_data[label]['mid'].get(mineral, 0)
            val_high = energy_data[label]['high'].get(mineral, 0)

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: {val_mid:.1f} GW ({share:.1f}%) [{val_low:.1f}-{val_high:.1f}]")

            metrics[label]['by_mineral'][mineral] = {
                'gw': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['total_gw']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['total_gw']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0
        print(f"  {label} vs Baseline: {growth_pct:+.1f}%")

    return metrics


def analyze_transport_by_country(transport_data, top_countries):
    """
    Analyze Panel C: Transport Volume by Country
    """
    print("\n" + "=" * 80)
    print("PANEL C: TRANSPORT VOLUME BY COUNTRY (Top 8 + Other)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate total (including Other)
        all_countries = top_countries + ['Other']
        total_low = sum(transport_data[label]['low'].get(c, 0) for c in all_countries)
        total_mid = sum(transport_data[label]['mid'].get(c, 0) for c in all_countries)
        total_high = sum(transport_data[label]['high'].get(c, 0) for c in all_countries)

        print(f"  Total Transport: {total_mid:.0f} Million tonkm")

        metrics[label] = {
            'total_million_tonkm': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_country': {}
        }

        # Top 5 countries
        country_values = [(c, transport_data[label]['mid'].get(c, 0)) for c in all_countries]
        country_values.sort(key=lambda x: x[1], reverse=True)

        print(f"  Top 5 Countries:")
        for country, value in country_values[:5]:
            share = (value / total_mid * 100) if total_mid > 0 else 0
            print(f"    {country}: {value:.0f} M tonkm ({share:.1f}%)")
            metrics[label]['by_country'][country] = {
                'million_tonkm': value,
                'share_pct': share
            }

    return metrics


def analyze_energy_by_country(energy_data, top_countries):
    """
    Analyze Panel D: Energy Capacity by Country
    """
    print("\n" + "=" * 80)
    print("PANEL D: ENERGY CAPACITY BY COUNTRY (Top 8 + Other)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate total (including Other)
        all_countries = top_countries + ['Other']
        total_low = sum(energy_data[label]['low'].get(c, 0) for c in all_countries)
        total_mid = sum(energy_data[label]['mid'].get(c, 0) for c in all_countries)
        total_high = sum(energy_data[label]['high'].get(c, 0) for c in all_countries)

        print(f"  Total Energy Capacity: {total_mid:.1f} GW")

        metrics[label] = {
            'total_gw': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_country': {}
        }

        # Top 5 countries
        country_values = [(c, energy_data[label]['mid'].get(c, 0)) for c in all_countries]
        country_values.sort(key=lambda x: x[1], reverse=True)

        print(f"  Top 5 Countries:")
        for country, value in country_values[:5]:
            share = (value / total_mid * 100) if total_mid > 0 else 0
            print(f"    {country}: {value:.1f} GW ({share:.1f}%)")
            metrics[label]['by_country'][country] = {
                'gw': value,
                'share_pct': share
            }

    return metrics


def analyze_transport_costs(transport_cost_data):
    """
    Analyze Panel E: Transport Costs by Mineral
    """
    print("\n" + "=" * 80)
    print("PANEL E: TRANSPORT COSTS BY MINERAL")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(transport_cost_data[label]['low'].values())  # Already in Billion USD
        total_mid = sum(transport_cost_data[label]['mid'].values())
        total_high = sum(transport_cost_data[label]['high'].values())

        print(f"  Total Transport Costs: ${total_mid:.2f}B (range: ${total_low:.2f}B-${total_high:.2f}B)")

        metrics[label] = {
            'total_billion_usd': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = transport_cost_data[label]['low'].get(mineral, 0)
            val_mid = transport_cost_data[label]['mid'].get(mineral, 0)
            val_high = transport_cost_data[label]['high'].get(mineral, 0)

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: ${val_mid:.2f}B ({share:.1f}%) [${val_low:.2f}B-${val_high:.2f}B]")

            metrics[label]['by_mineral'][mineral] = {
                'billion_usd': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['total_billion_usd']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['total_billion_usd']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0
        print(f"  {label} vs Baseline: {growth_pct:+.1f}%")

    return metrics


def analyze_energy_costs(energy_cost_data):
    """
    Analyze Panel F: Energy Costs (Investment vs Opex)
    """
    print("\n" + "=" * 80)
    print("PANEL F: ENERGY COSTS (Investment vs Opex)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        investment_low = energy_cost_data[label]['low'].get('Investment', 0)
        investment_mid = energy_cost_data[label]['mid'].get('Investment', 0)
        investment_high = energy_cost_data[label]['high'].get('Investment', 0)

        opex_low = energy_cost_data[label]['low'].get('Opex', 0)
        opex_mid = energy_cost_data[label]['mid'].get('Opex', 0)
        opex_high = energy_cost_data[label]['high'].get('Opex', 0)

        total_low = investment_low + opex_low
        total_mid = investment_mid + opex_mid
        total_high = investment_high + opex_high

        print(f"  Total Energy Costs: ${total_mid:.2f}B (range: ${total_low:.2f}B-${total_high:.2f}B)")
        print(f"    Investment: ${investment_mid:.2f}B ({investment_mid/total_mid*100:.1f}%)")
        print(f"    Opex: ${opex_mid:.2f}B ({opex_mid/total_mid*100:.1f}%)")

        metrics[label] = {
            'total_billion_usd': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'investment': {
                'billion_usd': {'low': investment_low, 'mid': investment_mid, 'high': investment_high},
                'share_pct': (investment_mid/total_mid*100) if total_mid > 0 else 0
            },
            'opex': {
                'billion_usd': {'low': opex_low, 'mid': opex_mid, 'high': opex_high},
                'share_pct': (opex_mid/total_mid*100) if total_mid > 0 else 0
            }
        }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['total_billion_usd']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['total_billion_usd']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0
        print(f"  {label} vs Baseline: {growth_pct:+.1f}%")

    # Investment vs Opex comparison
    print(f"\n{'Investment Share Across Scenarios':}")
    for label in ['Baseline', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        if label in metrics:
            inv_share = metrics[label]['investment']['share_pct']
            print(f"  {label}: {inv_share:.1f}%")

    return metrics


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

    # Prepare data using same logic as figure
    (transport_mineral_data, energy_mineral_data,
     transport_country_data, energy_country_data,
     transport_cost_data, energy_cost_data,
     top_transport_countries, top_energy_countries, country_colormap) = prepare_infrastructure_data(df)

    # Analyze each panel
    transport_mineral_metrics = analyze_transport_by_mineral(transport_mineral_data)
    energy_mineral_metrics = analyze_energy_by_mineral(energy_mineral_data)
    transport_country_metrics = analyze_transport_by_country(transport_country_data, top_transport_countries)
    energy_country_metrics = analyze_energy_by_country(energy_country_data, top_energy_countries)
    transport_cost_metrics = analyze_transport_costs(transport_cost_data)
    energy_cost_metrics = analyze_energy_costs(energy_cost_data)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return {
        'transport_by_mineral': transport_mineral_metrics,
        'energy_by_mineral': energy_mineral_metrics,
        'transport_by_country': transport_country_metrics,
        'energy_by_country': energy_country_metrics,
        'transport_costs': transport_cost_metrics,
        'energy_costs': energy_cost_metrics,
        'top_transport_countries': top_transport_countries,
        'top_energy_countries': top_energy_countries
    }


if __name__ == '__main__':
    metrics = main()
