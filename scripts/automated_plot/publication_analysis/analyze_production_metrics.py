"""
Production Indicators Key Metrics Analysis

Extracts key metrics from production indicators figure data for paper reporting.
Uses the same data processing logic as figure_production_indicators.py
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from figure_production_indicators import (
    prepare_extraction_data,
    prepare_processing_data,
    SCENARIO_CONFIG_EXTRACTION,
    SCENARIO_CONFIG_PROCESSING,
    MINERAL_ORDER,
    PROCESSING_ORDER
)


def analyze_extraction_metrics(extraction_data):
    """
    Analyze Panel A: Total extraction by mineral (stage 0 - metal content)

    Returns key metrics:
    - Total extraction by scenario (Baseline, 2040_C, 2040_U)
    - Growth rates from baseline
    - Breakdown by mineral
    """
    print("=" * 80)
    print("PANEL A: TOTAL EXTRACTION BY MINERAL (Stage 0 - Metal Content)")
    print("=" * 80)

    metrics = {}

    for label in ['Baseline', '2040_C', '2040_U']:
        print(f"\n{label}:")

        # Calculate totals across all minerals
        total_low = sum(extraction_data[label]['low'].values()) / 1e6  # Convert to Mt
        total_mid = sum(extraction_data[label]['mid'].values()) / 1e6
        total_high = sum(extraction_data[label]['high'].values()) / 1e6

        print(f"  Total Extraction: {total_mid:.2f} Mt (range: {total_low:.2f}-{total_high:.2f} Mt)")

        metrics[label] = {
            'total_mt': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = extraction_data[label]['low'].get(mineral, 0) / 1e6
            val_mid = extraction_data[label]['mid'].get(mineral, 0) / 1e6
            val_high = extraction_data[label]['high'].get(mineral, 0) / 1e6

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: {val_mid:.2f} Mt ({share:.1f}%) [range: {val_low:.2f}-{val_high:.2f}]")

            metrics[label]['by_mineral'][mineral] = {
                'mt': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Calculate growth rates
    print(f"\n{'Growth from Baseline':}")
    baseline_mid = metrics['Baseline']['total_mt']['mid']

    for label in ['2040_C', '2040_U']:
        scenario_mid = metrics[label]['total_mt']['mid']
        growth_pct = ((scenario_mid / baseline_mid) - 1) * 100 if baseline_mid > 0 else 0

        print(f"  {label}: {growth_pct:+.1f}%")
        metrics[label]['growth_from_baseline_pct'] = growth_pct

        # By mineral growth
        print(f"    By Mineral:")
        for mineral in MINERAL_ORDER:
            baseline_val = metrics['Baseline']['by_mineral'][mineral]['mt']['mid']
            scenario_val = metrics[label]['by_mineral'][mineral]['mt']['mid']

            if baseline_val > 0:
                mineral_growth = ((scenario_val / baseline_val) - 1) * 100
            else:
                mineral_growth = np.inf if scenario_val > 0 else 0

            print(f"      {mineral.capitalize()}: {mineral_growth:+.1f}%")
            metrics[label]['by_mineral'][mineral]['growth_from_baseline_pct'] = mineral_growth

    # Constrained vs Unconstrained comparison
    print(f"\n{'Unconstrained vs Constrained (2040)':}")
    c_mid = metrics['2040_C']['total_mt']['mid']
    u_mid = metrics['2040_U']['total_mt']['mid']
    diff_pct = ((u_mid / c_mid) - 1) * 100 if c_mid > 0 else 0

    print(f"  Total: {diff_pct:+.1f}%")
    metrics['u_vs_c_diff_pct'] = diff_pct

    print(f"    By Mineral:")
    for mineral in MINERAL_ORDER:
        c_val = metrics['2040_C']['by_mineral'][mineral]['mt']['mid']
        u_val = metrics['2040_U']['by_mineral'][mineral]['mt']['mid']

        if c_val > 0:
            mineral_diff = ((u_val / c_val) - 1) * 100
        else:
            mineral_diff = np.inf if u_val > 0 else 0

        print(f"      {mineral.capitalize()}: {mineral_diff:+.1f}%")

    return metrics


def analyze_processing_type_metrics(processing_data):
    """
    Analyze Panel B: Total processing by type (stage > 0)

    Returns key metrics for:
    - Baseline, BAU_C, BAU_U, Prec_C_N, Prec_U_N, Prec_C_R, Prec_U_R
    - Breakdown by processing type (Beneficiation, Early refining, Precursor)
    """
    print("\n" + "=" * 80)
    print("PANEL B: TOTAL PROCESSING BY TYPE (Stage > 0)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG_PROCESSING:
        print(f"\n{label}:")

        # Calculate totals across all processing types
        total_low = sum(processing_data[label]['low'].values()) / 1e6  # Convert to Mt
        total_mid = sum(processing_data[label]['mid'].values()) / 1e6
        total_high = sum(processing_data[label]['high'].values()) / 1e6

        print(f"  Total Processing: {total_mid:.2f} Mt (range: {total_low:.2f}-{total_high:.2f} Mt)")

        metrics[label] = {
            'total_mt': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_type': {}
        }

        # By processing type
        print(f"  By Processing Type:")
        for ptype in PROCESSING_ORDER:
            val_low = processing_data[label]['low'].get(ptype, 0) / 1e6
            val_mid = processing_data[label]['mid'].get(ptype, 0) / 1e6
            val_high = processing_data[label]['high'].get(ptype, 0) / 1e6

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {ptype}: {val_mid:.2f} Mt ({share:.1f}%) [range: {val_low:.2f}-{val_high:.2f}]")

            metrics[label]['by_type'][ptype] = {
                'mt': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

    # Key comparisons
    print(f"\n{'Key Comparisons':}")

    # BAU vs Baseline
    baseline_mid = metrics['Baseline']['total_mt']['mid']
    bau_c_mid = metrics['BAU_C']['total_mt']['mid']
    bau_u_mid = metrics['BAU_U']['total_mt']['mid']

    print(f"  BAU_C vs Baseline: {((bau_c_mid/baseline_mid)-1)*100:+.1f}%")
    print(f"  BAU_U vs Baseline: {((bau_u_mid/baseline_mid)-1)*100:+.1f}%")

    # Precursor vs BAU
    prec_u_n_mid = metrics['Prec_U_N']['total_mt']['mid']
    prec_u_r_mid = metrics['Prec_U_R']['total_mt']['mid']

    print(f"  Prec_U_N vs BAU_U: {((prec_u_n_mid/bau_u_mid)-1)*100:+.1f}%")
    print(f"  Prec_U_R vs BAU_U: {((prec_u_r_mid/bau_u_mid)-1)*100:+.1f}%")

    # Regional vs National (Precursor Unconstrained)
    print(f"  Prec_U_R vs Prec_U_N: {((prec_u_r_mid/prec_u_n_mid)-1)*100:+.1f}%")

    return metrics


def analyze_processing_mineral_metrics(mineral_data):
    """
    Analyze Panel C: Total processing by mineral (stage > 0)

    Returns key metrics for processed volumes by mineral
    """
    print("\n" + "=" * 80)
    print("PANEL C: TOTAL PROCESSING BY MINERAL (Stage > 0)")
    print("=" * 80)

    metrics = {}

    for _, _, _, label in SCENARIO_CONFIG_PROCESSING:
        print(f"\n{label}:")

        # Calculate totals
        total_low = sum(mineral_data[label]['low'].values()) / 1e6
        total_mid = sum(mineral_data[label]['mid'].values()) / 1e6
        total_high = sum(mineral_data[label]['high'].values()) / 1e6

        print(f"  Total Processed: {total_mid:.2f} Mt (range: {total_low:.2f}-{total_high:.2f} Mt)")

        metrics[label] = {
            'total_mt': {'low': total_low, 'mid': total_mid, 'high': total_high},
            'by_mineral': {}
        }

        # By mineral
        print(f"  By Mineral:")
        for mineral in MINERAL_ORDER:
            val_low = mineral_data[label]['low'].get(mineral, 0) / 1e6
            val_mid = mineral_data[label]['mid'].get(mineral, 0) / 1e6
            val_high = mineral_data[label]['high'].get(mineral, 0) / 1e6

            share = (val_mid / total_mid * 100) if total_mid > 0 else 0

            print(f"    {mineral.capitalize()}: {val_mid:.2f} Mt ({share:.1f}%) [range: {val_low:.2f}-{val_high:.2f}]")

            metrics[label]['by_mineral'][mineral] = {
                'mt': {'low': val_low, 'mid': val_mid, 'high': val_high},
                'share_pct': share
            }

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
    extraction_data = prepare_extraction_data(df)
    processing_type_data, processing_mineral_data = prepare_processing_data(df)

    # Analyze each panel
    extraction_metrics = analyze_extraction_metrics(extraction_data)
    processing_type_metrics = analyze_processing_type_metrics(processing_type_data)
    processing_mineral_metrics = analyze_processing_mineral_metrics(processing_mineral_data)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return {
        'extraction': extraction_metrics,
        'processing_by_type': processing_type_metrics,
        'processing_by_mineral': processing_mineral_metrics
    }


if __name__ == '__main__':
    metrics = main()
