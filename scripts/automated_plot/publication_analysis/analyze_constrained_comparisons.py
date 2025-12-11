"""
Constrained vs Unconstrained Policy Comparison Analysis

Focuses on the impact of environmental/social constraints across all indicators.
Highlights C vs U differences for BAU and Precursor scenarios.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from figure_production_indicators import prepare_extraction_data, prepare_processing_data
from figure_economic_indicators import prepare_economic_data
from figure_infrastructure_indicators import prepare_infrastructure_data
from figure_environmental_indicators import prepare_environmental_data


def print_section_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"{title:^80}")
    print("=" * 80)


def calculate_percentage_change(constrained, unconstrained):
    """Calculate percentage change from constrained to unconstrained"""
    if constrained == 0:
        return float('inf') if unconstrained > 0 else 0
    return ((unconstrained / constrained) - 1) * 100


def analyze_production_constraints(df):
    """Analyze production impacts of constraints"""
    print_section_header("PRODUCTION INDICATORS: CONSTRAINED vs UNCONSTRAINED")

    # Prepare data
    extraction_data = prepare_extraction_data(df)
    processing_type_data, processing_mineral_data = prepare_processing_data(df)

    print("\n1. EXTRACTION (Stage 0 - Metal Content)")
    print("-" * 80)

    # 2040 Constrained vs Unconstrained
    c_total = sum(extraction_data['2040_C']['mid'].values()) / 1e6
    u_total = sum(extraction_data['2040_U']['mid'].values()) / 1e6
    change = calculate_percentage_change(c_total, u_total)

    print(f"  2040 Constrained:   {c_total:.2f} Mt")
    print(f"  2040 Unconstrained: {u_total:.2f} Mt")
    print(f"  Change: {change:+.1f}%")
    print(f"\n  Impact: Unconstrained policies enable {u_total - c_total:.2f} Mt more extraction")

    print("\n2. PROCESSING BY TYPE (Stage > 0)")
    print("-" * 80)

    scenarios = [
        ('BAU_C', 'BAU_U', 'BAU 2040'),
        ('Prec_C_N', 'Prec_U_N', 'Precursor National'),
        ('Prec_C_R', 'Prec_U_R', 'Precursor Regional')
    ]

    for c_label, u_label, name in scenarios:
        c_total = sum(processing_type_data[c_label]['mid'].values()) / 1e6
        u_total = sum(processing_type_data[u_label]['mid'].values()) / 1e6
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   {c_total:.2f} Mt")
        print(f"    Unconstrained: {u_total:.2f} Mt")
        print(f"    Change: {change:+.1f}%")


def analyze_economic_constraints(df):
    """Analyze economic impacts of constraints"""
    print_section_header("ECONOMIC INDICATORS: CONSTRAINED vs UNCONSTRAINED")

    # Prepare data
    revenue_mineral, revenue_processing, gdp_share, cost_mineral, cost_breakdown = prepare_economic_data(df)

    print("\n1. EXPORT REVENUE")
    print("-" * 80)

    scenarios = [
        ('BAU_C', 'BAU_U', 'BAU 2040'),
        ('Prec_C_N', 'Prec_U_N', 'Precursor National'),
        ('Prec_C_R', 'Prec_U_R', 'Precursor Regional')
    ]

    for c_label, u_label, name in scenarios:
        c_total = sum(revenue_mineral[c_label]['mid'].values()) / 1e9
        u_total = sum(revenue_mineral[u_label]['mid'].values()) / 1e9
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   ${c_total:.2f}B")
        print(f"    Unconstrained: ${u_total:.2f}B")
        print(f"    Change: {change:+.1f}%")
        print(f"    Revenue gain: ${u_total - c_total:.2f}B ({(u_total - c_total)/c_total*100:.1f}%)")

    print("\n2. GDP SHARE")
    print("-" * 80)

    for c_label, u_label, name in scenarios:
        c_gdp = gdp_share[c_label]['mid']
        u_gdp = gdp_share[u_label]['mid']
        diff_pp = u_gdp - c_gdp

        print(f"\n  {name}:")
        print(f"    Constrained:   {c_gdp:.2f}%")
        print(f"    Unconstrained: {u_gdp:.2f}%")
        print(f"    Difference: {diff_pp:+.2f} percentage points")

    print("\n3. TOTAL COSTS")
    print("-" * 80)

    for c_label, u_label, name in scenarios:
        c_total = sum(cost_mineral[c_label]['mid'].values()) / 1e9
        u_total = sum(cost_mineral[u_label]['mid'].values()) / 1e9
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   ${c_total:.2f}B")
        print(f"    Unconstrained: ${u_total:.2f}B")
        print(f"    Change: {change:+.1f}%")
        print(f"    Additional cost: ${u_total - c_total:.2f}B")


def analyze_infrastructure_constraints(df):
    """Analyze infrastructure impacts of constraints"""
    print_section_header("INFRASTRUCTURE INDICATORS: CONSTRAINED vs UNCONSTRAINED")

    # Prepare data
    (transport_mineral, energy_mineral, transport_country, energy_country,
     transport_cost, energy_cost, _, _, _) = prepare_infrastructure_data(df)

    print("\n1. TRANSPORT VOLUME")
    print("-" * 80)

    scenarios = [
        ('BAU_C', 'BAU_U', 'BAU 2040'),
        ('Prec_C_N', 'Prec_U_N', 'Precursor National'),
        ('Prec_C_R', 'Prec_U_R', 'Precursor Regional')
    ]

    for c_label, u_label, name in scenarios:
        c_total = sum(transport_mineral[c_label]['mid'].values())
        u_total = sum(transport_mineral[u_label]['mid'].values())
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   {c_total:,.0f} M tonkm")
        print(f"    Unconstrained: {u_total:,.0f} M tonkm")
        print(f"    Change: {change:+.1f}%")

    print("\n2. ENERGY CAPACITY")
    print("-" * 80)

    for c_label, u_label, name in scenarios:
        c_total = sum(energy_mineral[c_label]['mid'].values())
        u_total = sum(energy_mineral[u_label]['mid'].values())
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   {c_total:.2f} GW")
        print(f"    Unconstrained: {u_total:.2f} GW")
        print(f"    Change: {change:+.1f}%")

    print("\n3. TRANSPORT COSTS")
    print("-" * 80)

    for c_label, u_label, name in scenarios:
        c_total = sum(transport_cost[c_label]['mid'].values())
        u_total = sum(transport_cost[u_label]['mid'].values())
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   ${c_total:.2f}B")
        print(f"    Unconstrained: ${u_total:.2f}B")
        print(f"    Change: {change:+.1f}%")

    print("\n4. ENERGY COSTS")
    print("-" * 80)

    for c_label, u_label, name in scenarios:
        c_total = sum(energy_cost[c_label]['mid'].values())
        u_total = sum(energy_cost[u_label]['mid'].values())
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   ${c_total:.2f}B")
        print(f"    Unconstrained: ${u_total:.2f}B")
        print(f"    Change: {change:+.1f}%")


def analyze_environmental_constraints(df):
    """Analyze environmental impacts of constraints"""
    print_section_header("ENVIRONMENTAL INDICATORS: CONSTRAINED vs UNCONSTRAINED")

    # Prepare data
    (emissions_mineral, water_mineral, emissions_country, water_country,
     emissions_source, water_processing, _, _, _) = prepare_environmental_data(df)

    print("\n1. CO2 EMISSIONS")
    print("-" * 80)

    scenarios = [
        ('BAU_C', 'BAU_U', 'BAU 2040'),
        ('Prec_C_N', 'Prec_U_N', 'Precursor National'),
        ('Prec_C_R', 'Prec_U_R', 'Precursor Regional')
    ]

    for c_label, u_label, name in scenarios:
        c_total = sum(emissions_mineral[c_label]['mid'].values())
        u_total = sum(emissions_mineral[u_label]['mid'].values())
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   {c_total:.0f} kt CO2eq")
        print(f"    Unconstrained: {u_total:.0f} kt CO2eq")
        print(f"    Change: {change:+.1f}%")
        print(f"    Additional emissions: {u_total - c_total:.0f} kt CO2eq")

    print("\n2. WATER USAGE")
    print("-" * 80)

    for c_label, u_label, name in scenarios:
        c_total = sum(water_mineral[c_label]['mid'].values())
        u_total = sum(water_mineral[u_label]['mid'].values())
        change = calculate_percentage_change(c_total, u_total)

        print(f"\n  {name}:")
        print(f"    Constrained:   {c_total:.1f} MCM")
        print(f"    Unconstrained: {u_total:.1f} MCM")
        print(f"    Change: {change:+.1f}%")
        print(f"    Additional water: {u_total - c_total:.1f} MCM")


def generate_summary_table(df):
    """Generate summary comparison table"""
    print_section_header("SUMMARY: UNCONSTRAINED vs CONSTRAINED BENEFITS & COSTS")

    # Prepare all data
    extraction_data = prepare_extraction_data(df)
    processing_type_data, _ = prepare_processing_data(df)
    revenue_mineral, _, gdp_share, cost_mineral, _ = prepare_economic_data(df)
    (transport_mineral, energy_mineral, _, _, transport_cost, energy_cost,
     _, _, _) = prepare_infrastructure_data(df)
    (emissions_mineral, water_mineral, _, _, _, _, _, _, _) = prepare_environmental_data(df)

    print("\n" + "=" * 100)
    print(f"{'Indicator':<30} {'BAU':<20} {'Prec National':<20} {'Prec Regional':<20}")
    print("=" * 100)

    # Production
    print("\nPRODUCTION GAINS (Unconstrained vs Constrained):")
    print("-" * 100)

    bau_prod = sum(processing_type_data['BAU_U']['mid'].values()) - sum(processing_type_data['BAU_C']['mid'].values())
    prec_n_prod = sum(processing_type_data['Prec_U_N']['mid'].values()) - sum(processing_type_data['Prec_C_N']['mid'].values())
    prec_r_prod = sum(processing_type_data['Prec_U_R']['mid'].values()) - sum(processing_type_data['Prec_C_R']['mid'].values())

    print(f"{'Processing volume (Mt)':<30} {bau_prod/1e6:>18.2f}  {prec_n_prod/1e6:>18.2f}  {prec_r_prod/1e6:>18.2f}")

    # Economic Benefits
    print("\nECONOMIC BENEFITS (Unconstrained vs Constrained):")
    print("-" * 100)

    bau_rev = (sum(revenue_mineral['BAU_U']['mid'].values()) - sum(revenue_mineral['BAU_C']['mid'].values())) / 1e9
    prec_n_rev = (sum(revenue_mineral['Prec_U_N']['mid'].values()) - sum(revenue_mineral['Prec_C_N']['mid'].values())) / 1e9
    prec_r_rev = (sum(revenue_mineral['Prec_U_R']['mid'].values()) - sum(revenue_mineral['Prec_C_R']['mid'].values())) / 1e9

    print(f"{'Revenue gain ($B)':<30} {bau_rev:>18.2f}  {prec_n_rev:>18.2f}  {prec_r_rev:>18.2f}")

    bau_gdp = gdp_share['BAU_U']['mid'] - gdp_share['BAU_C']['mid']
    prec_n_gdp = gdp_share['Prec_U_N']['mid'] - gdp_share['Prec_C_N']['mid']
    prec_r_gdp = gdp_share['Prec_U_R']['mid'] - gdp_share['Prec_C_R']['mid']

    print(f"{'GDP share gain (pp)':<30} {bau_gdp:>18.2f}  {prec_n_gdp:>18.2f}  {prec_r_gdp:>18.2f}")

    # Economic Costs
    print("\nECONOMIC COSTS (Unconstrained vs Constrained):")
    print("-" * 100)

    bau_cost = (sum(cost_mineral['BAU_U']['mid'].values()) - sum(cost_mineral['BAU_C']['mid'].values())) / 1e9
    prec_n_cost = (sum(cost_mineral['Prec_U_N']['mid'].values()) - sum(cost_mineral['Prec_C_N']['mid'].values())) / 1e9
    prec_r_cost = (sum(cost_mineral['Prec_U_R']['mid'].values()) - sum(cost_mineral['Prec_C_R']['mid'].values())) / 1e9

    print(f"{'Additional costs ($B)':<30} {bau_cost:>18.2f}  {prec_n_cost:>18.2f}  {prec_r_cost:>18.2f}")

    # Infrastructure Requirements
    print("\nINFRASTRUCTURE REQUIREMENTS (Unconstrained vs Constrained):")
    print("-" * 100)

    bau_trans = sum(transport_mineral['BAU_U']['mid'].values()) - sum(transport_mineral['BAU_C']['mid'].values())
    prec_n_trans = sum(transport_mineral['Prec_U_N']['mid'].values()) - sum(transport_mineral['Prec_C_N']['mid'].values())
    prec_r_trans = sum(transport_mineral['Prec_U_R']['mid'].values()) - sum(transport_mineral['Prec_C_R']['mid'].values())

    print(f"{'Transport (M tonkm)':<30} {bau_trans:>18.0f}  {prec_n_trans:>18.0f}  {prec_r_trans:>18.0f}")

    bau_energy = sum(energy_mineral['BAU_U']['mid'].values()) - sum(energy_mineral['BAU_C']['mid'].values())
    prec_n_energy = sum(energy_mineral['Prec_U_N']['mid'].values()) - sum(energy_mineral['Prec_C_N']['mid'].values())
    prec_r_energy = sum(energy_mineral['Prec_U_R']['mid'].values()) - sum(energy_mineral['Prec_C_R']['mid'].values())

    print(f"{'Energy capacity (GW)':<30} {bau_energy:>18.2f}  {prec_n_energy:>18.2f}  {prec_r_energy:>18.2f}")

    bau_trans_cost = sum(transport_cost['BAU_U']['mid'].values()) - sum(transport_cost['BAU_C']['mid'].values())
    prec_n_trans_cost = sum(transport_cost['Prec_U_N']['mid'].values()) - sum(transport_cost['Prec_C_N']['mid'].values())
    prec_r_trans_cost = sum(transport_cost['Prec_U_R']['mid'].values()) - sum(transport_cost['Prec_C_R']['mid'].values())

    print(f"{'Transport costs ($B)':<30} {bau_trans_cost:>18.2f}  {prec_n_trans_cost:>18.2f}  {prec_r_trans_cost:>18.2f}")

    bau_energy_cost = sum(energy_cost['BAU_U']['mid'].values()) - sum(energy_cost['BAU_C']['mid'].values())
    prec_n_energy_cost = sum(energy_cost['Prec_U_N']['mid'].values()) - sum(energy_cost['Prec_C_N']['mid'].values())
    prec_r_energy_cost = sum(energy_cost['Prec_U_R']['mid'].values()) - sum(energy_cost['Prec_C_R']['mid'].values())

    print(f"{'Energy costs ($B)':<30} {bau_energy_cost:>18.2f}  {prec_n_energy_cost:>18.2f}  {prec_r_energy_cost:>18.2f}")

    # Environmental Costs
    print("\nENVIRONMENTAL COSTS (Unconstrained vs Constrained):")
    print("-" * 100)

    bau_emissions = sum(emissions_mineral['BAU_U']['mid'].values()) - sum(emissions_mineral['BAU_C']['mid'].values())
    prec_n_emissions = sum(emissions_mineral['Prec_U_N']['mid'].values()) - sum(emissions_mineral['Prec_C_N']['mid'].values())
    prec_r_emissions = sum(emissions_mineral['Prec_U_R']['mid'].values()) - sum(emissions_mineral['Prec_C_R']['mid'].values())

    print(f"{'CO2 emissions (kt)':<30} {bau_emissions:>18.0f}  {prec_n_emissions:>18.0f}  {prec_r_emissions:>18.0f}")

    bau_water = sum(water_mineral['BAU_U']['mid'].values()) - sum(water_mineral['BAU_C']['mid'].values())
    prec_n_water = sum(water_mineral['Prec_U_N']['mid'].values()) - sum(water_mineral['Prec_C_N']['mid'].values())
    prec_r_water = sum(water_mineral['Prec_U_R']['mid'].values()) - sum(water_mineral['Prec_C_R']['mid'].values())

    print(f"{'Water usage (MCM)':<30} {bau_water:>18.1f}  {prec_n_water:>18.1f}  {prec_r_water:>18.1f}")

    print("\n" + "=" * 100)

    # Cost-Benefit Ratio
    print("\nCOST-BENEFIT ANALYSIS:")
    print("-" * 100)

    for scenario, rev_gain, cost_increase, emissions_increase, water_increase in [
        ('BAU', bau_rev, bau_cost, bau_emissions, bau_water),
        ('Precursor National', prec_n_rev, prec_n_cost, prec_n_emissions, prec_n_water),
        ('Precursor Regional', prec_r_rev, prec_r_cost, prec_r_emissions, prec_r_water)
    ]:
        print(f"\n{scenario}:")
        print(f"  Revenue gain per $1B cost increase: ${rev_gain/cost_increase:.2f}B" if cost_increase > 0 else "  N/A")
        print(f"  Revenue gain per 100 kt CO2: ${rev_gain/(emissions_increase/100):.2f}B" if emissions_increase > 0 else "  N/A")
        print(f"  Revenue gain per MCM water: ${rev_gain/water_increase:.2f}B" if water_increase > 0 else "  N/A")


def main():
    """Main analysis function"""
    print("\n" + "=" * 80)
    print("CONSTRAINED vs UNCONSTRAINED POLICY COMPARISON ANALYSIS")
    print("=" * 80)

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"\nLoading data from: {data_path}")
    df = pd.read_excel(data_path)
    print(f"Loaded {len(df)} rows of data")

    # Run analyses
    analyze_production_constraints(df)
    analyze_economic_constraints(df)
    analyze_infrastructure_constraints(df)
    analyze_environmental_constraints(df)
    generate_summary_table(df)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
