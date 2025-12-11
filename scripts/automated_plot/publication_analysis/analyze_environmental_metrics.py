"""
Environmental Indicators Key Metrics Analysis

Extracts key metrics from environmental indicators figure data for paper reporting.
Uses the same data processing logic as figure_environmental_indicators.py
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
from figure_environmental_indicators import (
    prepare_environmental_data,
    SCENARIO_CONFIG,
    MINERAL_ORDER,
    EMISSION_SOURCE_ORDER,
    PROCESSING_ORDER
)


def analyze_emissions_by_mineral(emissions_data):
    """
    Analyze Panel A: CO2 Emissions by Mineral
    """
    print("=" * 80)
    print("PANEL A: CO2 EMISSIONS BY MINERAL")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(emissions_data[label]['low'].values())  # Already in kt CO2eq
        total_mid = sum(emissions_data[label]['mid'].values())
        total_high = sum(emissions_data[label]['high'].values())

        print(f"  Total Emissions: {total_mid:.0f} kt CO2eq (range: {total_low:.0f}-{total_high:.0f})")

        metrics[label] = {
            'total_kt_co2eq': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = emissions_data[label]['low'].get(mineral, 0)
            val_mid = emissions_data[label]['mid'].get(mineral, 0)
            val_high = emissions_data[label]['high'].get(mineral, 0)

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: {val_mid:.0f} kt ({share:.1f}%) [{val_low:.0f}-{val_high:.0f}]")

            metrics[label]['by_mineral'][mineral] = {
                'kt_co2eq': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['total_kt_co2eq']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['total_kt_co2eq']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0
        print(f"  {label} vs Baseline: {growth_pct:+.1f}%")

    # Precursor comparisons
    prec_u_n_mid = metrics['Prec_U_N']['total_kt_co2eq']['mid']
    prec_u_r_mid = metrics['Prec_U_R']['total_kt_co2eq']['mid']

    print(f"  Prec_U_R vs Prec_U_N: {((prec_u_r_mid/prec_u_n_mid)-1)*100:+.1f}%")

    return metrics


def analyze_water_by_mineral(water_data):
    """
    Analyze Panel B: Water Usage by Mineral
    """
    print("\n" + "=" * 80)
    print("PANEL B: WATER USAGE BY MINERAL")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(water_data[label]['low'].values())  # Already in MCM
        total_mid = sum(water_data[label]['mid'].values())
        total_high = sum(water_data[label]['high'].values())

        print(f"  Total Water: {total_mid:.1f} MCM (range: {total_low:.1f}-{total_high:.1f})")

        metrics[label] = {
            'total_mcm': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = water_data[label]['low'].get(mineral, 0)
            val_mid = water_data[label]['mid'].get(mineral, 0)
            val_high = water_data[label]['high'].get(mineral, 0)

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: {val_mid:.1f} MCM ({share:.1f}%) [{val_low:.1f}-{val_high:.1f}]")

            metrics[label]['by_mineral'][mineral] = {
                'mcm': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['total_mcm']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['total_mcm']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0
        print(f"  {label} vs Baseline: {growth_pct:+.1f}%")

    return metrics


def analyze_emissions_by_country(emissions_data, top_countries):
    """
    Analyze Panel C: CO2 Emissions by Country
    """
    print("\n" + "=" * 80)
    print("PANEL C: CO2 EMISSIONS BY COUNTRY (Top 8 + Other)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate total (including Other)
        all_countries = top_countries + ['Other']
        total_low = sum(emissions_data[label]['low'].get(c, 0) for c in all_countries)
        total_mid = sum(emissions_data[label]['mid'].get(c, 0) for c in all_countries)
        total_high = sum(emissions_data[label]['high'].get(c, 0) for c in all_countries)

        print(f"  Total Emissions: {total_mid:.0f} kt CO2eq")

        metrics[label] = {
            'total_kt_co2eq': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_country': {}
        }

        # Top 5 countries
        country_values = [(c, emissions_data[label]['mid'].get(c, 0)) for c in all_countries]
        country_values.sort(key=lambda x: x[1], reverse=True)

        print(f"  Top 5 Countries:")
        for country, value in country_values[:5]:
            share = (value / total_mid * 100) if total_mid > 0 else 0
            print(f"    {country}: {value:.0f} kt ({share:.1f}%)")
            metrics[label]['by_country'][country] = {
                'kt_co2eq': value,
                'share_pct': share
            }

    return metrics


def analyze_water_by_country(water_data, top_countries):
    """
    Analyze Panel D: Water Usage by Country
    """
    print("\n" + "=" * 80)
    print("PANEL D: WATER USAGE BY COUNTRY (Top 8 + Other)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate total (including Other)
        all_countries = top_countries + ['Other']
        total_low = sum(water_data[label]['low'].get(c, 0) for c in all_countries)
        total_mid = sum(water_data[label]['mid'].get(c, 0) for c in all_countries)
        total_high = sum(water_data[label]['high'].get(c, 0) for c in all_countries)

        print(f"  Total Water: {total_mid:.1f} MCM")

        metrics[label] = {
            'total_mcm': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_country': {}
        }

        # Top 5 countries
        country_values = [(c, water_data[label]['mid'].get(c, 0)) for c in all_countries]
        country_values.sort(key=lambda x: x[1], reverse=True)

        print(f"  Top 5 Countries:")
        for country, value in country_values[:5]:
            share = (value / total_mid * 100) if total_mid > 0 else 0
            print(f"    {country}: {value:.1f} MCM ({share:.1f}%)")
            metrics[label]['by_country'][country] = {
                'mcm': value,
                'share_pct': share
            }

    return metrics


def analyze_emissions_by_source(emissions_source_data):
    """
    Analyze Panel E: CO2 Emissions by Source (Energy vs Transport)
    """
    print("\n" + "=" * 80)
    print("PANEL E: CO2 EMISSIONS BY SOURCE (Energy vs Transport)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Get values
        energy_low = emissions_source_data[label]['low'].get('Energy', 0)
        energy_mid = emissions_source_data[label]['mid'].get('Energy', 0)
        energy_high = emissions_source_data[label]['high'].get('Energy', 0)

        transport_low = emissions_source_data[label]['low'].get('Transport', 0)
        transport_mid = emissions_source_data[label]['mid'].get('Transport', 0)
        transport_high = emissions_source_data[label]['high'].get('Transport', 0)

        total_low = energy_low + transport_low
        total_mid = energy_mid + transport_mid
        total_high = energy_high + transport_high

        print(f"  Total Emissions: {total_mid:.0f} kt CO2eq")
        print(f"    Energy: {energy_mid:.0f} kt ({energy_mid/total_mid*100:.1f}%)")
        print(f"    Transport: {transport_mid:.0f} kt ({transport_mid/total_mid*100:.1f}%)")

        metrics[label] = {
            'total_kt_co2eq': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'energy': {
                'kt_co2eq': {'low': energy_low, 'mid': energy_mid, 'high': energy_high},
                'share_pct': (energy_mid/total_mid*100) if total_mid > 0 else 0
            },
            'transport': {
                'kt_co2eq': {'low': transport_low, 'mid': transport_mid, 'high': transport_high},
                'share_pct': (transport_mid/total_mid*100) if total_mid > 0 else 0
            }
        }

    # Energy share comparison
    print(f"\n{'Energy Emissions Share Across Scenarios':}")
    for label in ['Baseline', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        if label in metrics:
            energy_share = metrics[label]['energy']['share_pct']
            print(f"  {label}: {energy_share:.1f}%")

    return metrics


def analyze_water_by_processing(water_processing_data):
    """
    Analyze Panel F: Water Usage by Processing Stage
    """
    print("\n" + "=" * 80)
    print("PANEL F: WATER USAGE BY PROCESSING STAGE")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(water_processing_data[label]['low'].values())
        total_mid = sum(water_processing_data[label]['mid'].values())
        total_high = sum(water_processing_data[label]['high'].values())

        print(f"  Total Water: {total_mid:.1f} MCM")

        metrics[label] = {
            'total_mcm': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_stage': {}
        }

        # By processing type
        print(f"  By Processing Stage:")
        for ptype in PROCESSING_ORDER:
            val_low = water_processing_data[label]['low'].get(ptype, 0)
            val_mid = water_processing_data[label]['mid'].get(ptype, 0)
            val_high = water_processing_data[label]['high'].get(ptype, 0)

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {ptype}: {val_mid:.1f} MCM ({share:.1f}%) [{val_low:.1f}-{val_high:.1f}]")

            metrics[label]['by_stage'][ptype] = {
                'mcm': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Precursor water share
    print(f"\n{'Precursor Water Share Across Scenarios':}")
    for label in ['Baseline', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        if label in metrics:
            prec_share = metrics[label]['by_stage'].get('Precursor related product', {}).get('share_pct', 0)
            prec_value = metrics[label]['by_stage'].get('Precursor related product', {}).get('mcm', {}).get('mid', 0)
            print(f"  {label}: {prec_share:.1f}% ({prec_value:.1f} MCM)")

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
    (emissions_mineral_data, water_mineral_data,
     emissions_country_data, water_country_data,
     emissions_source_data, water_processing_data,
     top_emissions_countries, top_water_countries, country_colormap) = prepare_environmental_data(df)

    # Analyze each panel
    emissions_mineral_metrics = analyze_emissions_by_mineral(emissions_mineral_data)
    water_mineral_metrics = analyze_water_by_mineral(water_mineral_data)
    emissions_country_metrics = analyze_emissions_by_country(emissions_country_data, top_emissions_countries)
    water_country_metrics = analyze_water_by_country(water_country_data, top_water_countries)
    emissions_source_metrics = analyze_emissions_by_source(emissions_source_data)
    water_processing_metrics = analyze_water_by_processing(water_processing_data)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return {
        'emissions_by_mineral': emissions_mineral_metrics,
        'water_by_mineral': water_mineral_metrics,
        'emissions_by_country': emissions_country_metrics,
        'water_by_country': water_country_metrics,
        'emissions_by_source': emissions_source_metrics,
        'water_by_processing': water_processing_metrics,
        'top_emissions_countries': top_emissions_countries,
        'top_water_countries': top_water_countries
    }


if __name__ == '__main__':
    metrics = main()
