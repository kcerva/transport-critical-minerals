"""
Economic Indicators Key Metrics Analysis

Extracts key metrics from economic indicators figure data for paper reporting.
Uses the same data processing logic as figure_economic_indicators.py
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
from figure_economic_indicators import (
    prepare_economic_data,
    prepare_country_gdp_data,
    calculate_gdp_difference_matrix,
    SCENARIO_CONFIG,
    MINERAL_ORDER,
    PROCESSING_ORDER,
    COST_TYPE_ORDER
)


def analyze_revenue_by_mineral(revenue_data):
    """
    Analyze Panel A: Export Revenue by Mineral
    """
    print("=" * 80)
    print("PANEL A: EXPORT REVENUE BY MINERAL (Stage > 0)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(revenue_data[label]['low'].values()) / 1e9  # Convert to Billion USD
        total_mid = sum(revenue_data[label]['mid'].values()) / 1e9
        total_high = sum(revenue_data[label]['high'].values()) / 1e9

        print(f"  Total Revenue: ${total_mid:.2f}B (range: ${total_low:.2f}B-${total_high:.2f}B)")

        metrics[label] = {
            'total_billion_usd': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = revenue_data[label]['low'].get(mineral, 0) / 1e9
            val_mid = revenue_data[label]['mid'].get(mineral, 0) / 1e9
            val_high = revenue_data[label]['high'].get(mineral, 0) / 1e9

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

    # Precursor vs BAU
    bau_u_mid = metrics['BAU_U']['total_billion_usd']['mid']
    prec_u_n_mid = metrics['Prec_U_N']['total_billion_usd']['mid']
    prec_u_r_mid = metrics['Prec_U_R']['total_billion_usd']['mid']

    print(f"  Prec_U_N vs BAU_U: {((prec_u_n_mid/bau_u_mid)-1)*100:+.1f}%")
    print(f"  Prec_U_R vs BAU_U: {((prec_u_r_mid/bau_u_mid)-1)*100:+.1f}%")
    print(f"  Prec_U_R vs Prec_U_N: {((prec_u_r_mid/prec_u_n_mid)-1)*100:+.1f}%")

    return metrics


def analyze_revenue_by_processing(revenue_data):
    """
    Analyze Panel B: Export Revenue by Processing Type
    """
    print("\n" + "=" * 80)
    print("PANEL B: EXPORT REVENUE BY PROCESSING TYPE (Stage > 0)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(revenue_data[label]['low'].values()) / 1e9
        total_mid = sum(revenue_data[label]['mid'].values()) / 1e9
        total_high = sum(revenue_data[label]['high'].values()) / 1e9

        print(f"  Total Revenue: ${total_mid:.2f}B (range: ${total_low:.2f}B-${total_high:.2f}B)")

        metrics[label] = {
            'total_billion_usd': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_type': {}
        }

        # By processing type
        print(f"  By Processing Type:")
        for ptype in PROCESSING_ORDER:
            val_low = revenue_data[label]['low'].get(ptype, 0) / 1e9
            val_mid = revenue_data[label]['mid'].get(ptype, 0) / 1e9
            val_high = revenue_data[label]['high'].get(ptype, 0) / 1e9

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {ptype}: ${val_mid:.2f}B ({share:.1f}%) [${val_low:.2f}B-${val_high:.2f}B]")

            metrics[label]['by_type'][ptype] = {
                'billion_usd': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Key insights on processing type shifts
    print(f"\n{'Precursor Product Share':}")
    for label in ['Baseline', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        if label in metrics:
            precursor_share = metrics[label]['by_type'].get('Precursor related product', {}).get('share_pct', 0)
            precursor_value = metrics[label]['by_type'].get('Precursor related product', {}).get('billion_usd', {}).get('mid', 0)
            print(f"  {label}: {precursor_share:.1f}% (${precursor_value:.2f}B)")

    return metrics


def analyze_gdp_share(gdp_data):
    """
    Analyze Panel C: Revenue as Share of GDP
    """
    print("\n" + "=" * 80)
    print("PANEL C: REVENUE AS SHARE OF GDP")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        low_pct = gdp_data[label]['low']
        mid_pct = gdp_data[label]['mid']
        high_pct = gdp_data[label]['high']

        print(f"\n{label}: {mid_pct:.2f}% (range: {low_pct:.2f}%-{high_pct:.2f}%)")

        metrics[label] = {
            'gdp_share_pct': {'low': low_pct, 'mid': mid_pct, 'high': high_pct}
        }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['gdp_share_pct']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['gdp_share_pct']['mid']
        diff_pp = scenario_mid - baseline_mid
        print(f"  {label} vs Baseline: {diff_pp:+.2f} percentage points")

    return metrics


def analyze_cost_by_mineral(cost_data):
    """
    Analyze Panel D: Total Cost by Mineral
    """
    print("\n" + "=" * 80)
    print("PANEL D: TOTAL COST BY MINERAL")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(cost_data[label]['low'].values()) / 1e9
        total_mid = sum(cost_data[label]['mid'].values()) / 1e9
        total_high = sum(cost_data[label]['high'].values()) / 1e9

        print(f"  Total Cost: ${total_mid:.2f}B (range: ${total_low:.2f}B-${total_high:.2f}B)")

        metrics[label] = {
            'total_billion_usd': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = cost_data[label]['low'].get(mineral, 0) / 1e9
            val_mid = cost_data[label]['mid'].get(mineral, 0) / 1e9
            val_high = cost_data[label]['high'].get(mineral, 0) / 1e9

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: ${val_mid:.2f}B ({share:.1f}%) [${val_low:.2f}B-${val_high:.2f}B]")

            metrics[label]['by_mineral'][mineral] = {
                'billion_usd': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Growth comparisons
    print(f"\n{'Key Comparisons':}")
    baseline_mid = metrics['Baseline']['total_billion_usd']['mid']

    for label in ['BAU_C', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        scenario_mid = metrics[label]['total_billion_usd']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0
        print(f"  {label} vs Baseline: {growth_pct:+.1f}%")

    return metrics


def analyze_cost_breakdown(cost_data):
    """
    Analyze Panel E: Total Cost by Component
    """
    print("\n" + "=" * 80)
    print("PANEL E: TOTAL COST BY COMPONENT")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(cost_data[label]['low'].values()) / 1e9
        total_mid = sum(cost_data[label]['mid'].values()) / 1e9
        total_high = sum(cost_data[label]['high'].values()) / 1e9

        print(f"  Total Cost: ${total_mid:.2f}B (range: ${total_low:.2f}B-${total_high:.2f}B)")

        metrics[label] = {
            'total_billion_usd': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_component': {}
        }

        # By cost component
        print(f"  By Cost Component:")
        for ctype in COST_TYPE_ORDER:
            val_low = cost_data[label]['low'].get(ctype, 0) / 1e9
            val_mid = cost_data[label]['mid'].get(ctype, 0) / 1e9
            val_high = cost_data[label]['high'].get(ctype, 0) / 1e9

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {ctype}: ${val_mid:.2f}B ({share:.1f}%) [${val_low:.2f}B-${val_high:.2f}B]")

            metrics[label]['by_component'][ctype] = {
                'billion_usd': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Cost structure insights
    print(f"\n{'Production Cost Share Across Scenarios':}")
    for label in ['Baseline', 'BAU_U', 'Prec_U_N', 'Prec_U_R']:
        if label in metrics:
            prod_share = metrics[label]['by_component'].get('Production', {}).get('share_pct', 0)
            print(f"  {label}: {prod_share:.1f}%")

    return metrics


def analyze_country_gdp_differences(difference_data, countries_sorted):
    """
    Analyze Panel C heatmap: Country-level GDP share differences (Regional - National)
    """
    print("\n" + "=" * 80)
    print("PANEL C HEATMAP: COUNTRY-LEVEL GDP SHARE DIFFERENCES (Regional - National)")
    print("=" * 80)

    # Analyze Precursor Unconstrained (most relevant)
    print(f"\nPrecursor Unconstrained (Mid Demand):")
    print(f"  {'Country':<6} {'Low':<8} {'Mid':<8} {'High':<8} {'Avg':<8}")
    print(f"  {'-'*42}")

    country_stats = {}

    for country in countries_sorted:
        low_val = difference_data.get(('precursor', 'low'), {}).get(country, 0)
        mid_val = difference_data.get(('precursor', 'mid'), {}).get(country, 0)
        high_val = difference_data.get(('precursor', 'high'), {}).get(country, 0)

        avg_val = np.mean([low_val, mid_val, high_val])

        print(f"  {country:<6} {low_val:>6.1f}pp {mid_val:>6.1f}pp {high_val:>6.1f}pp {avg_val:>6.1f}pp")

        country_stats[country] = {
            'low': low_val,
            'mid': mid_val,
            'high': high_val,
            'avg': avg_val
        }

    # Top gainers
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1]['mid'], reverse=True)

    print(f"\n{'Top 5 Gainers (Regional vs National, Mid Demand)':}")
    for country, stats in sorted_countries[:5]:
        print(f"  {country}: {stats['mid']:+.2f} percentage points")

    print(f"\n{'Top 5 Losers (Regional vs National, Mid Demand)':}")
    for country, stats in sorted_countries[-5:]:
        print(f"  {country}: {stats['mid']:+.2f} percentage points")

    return country_stats


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
    revenue_mineral_data, revenue_processing_data, gdp_share_data, cost_mineral_data, cost_breakdown_data = prepare_economic_data(df)

    # Country-level GDP data
    country_gdp_data = prepare_country_gdp_data(df)
    difference_data, countries_sorted = calculate_gdp_difference_matrix(country_gdp_data)

    # Analyze each panel
    revenue_mineral_metrics = analyze_revenue_by_mineral(revenue_mineral_data)
    revenue_processing_metrics = analyze_revenue_by_processing(revenue_processing_data)
    gdp_metrics = analyze_gdp_share(gdp_share_data)
    cost_mineral_metrics = analyze_cost_by_mineral(cost_mineral_data)
    cost_breakdown_metrics = analyze_cost_breakdown(cost_breakdown_data)
    country_gdp_stats = analyze_country_gdp_differences(difference_data, countries_sorted)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return {
        'revenue_by_mineral': revenue_mineral_metrics,
        'revenue_by_processing': revenue_processing_metrics,
        'gdp_share': gdp_metrics,
        'cost_by_mineral': cost_mineral_metrics,
        'cost_by_component': cost_breakdown_metrics,
        'country_gdp_differences': country_gdp_stats
    }


if __name__ == '__main__':
    metrics = main()
