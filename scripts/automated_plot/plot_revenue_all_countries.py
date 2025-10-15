import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os


def extract_revenue_data(df):
    """
    Extract revenue data for single-axis stacked bar charts.

    Returns:
        revenue_bars: List of tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in Billion USD
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # Bar 1: Baseline 2022
    baseline = df[(df['scenario'] == '2022_baseline') & (df['year'] == 2022)].copy()
    revenue_baseline = baseline.groupby('reference_mineral')['revenue_usd'].sum()
    baseline_revenue = [revenue_baseline.get(m, 0) / 1e9 for m in minerals]  # Convert to Billion USD

    # Bar 2: BAU 2040 Unconstrained (mid_min = country, but for BAU country=region)
    bau = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
             (df['constraint'] == 'country_unconstrained') &
             (df['year'] == 2040)].copy()
    revenue_bau = bau.groupby('reference_mineral')['revenue_usd'].sum()
    bau_revenue = [revenue_bau.get(m, 0) / 1e9 for m in minerals]

    # Bar 3: Early Refining 2040 Country Unconstrained
    early_country = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                       (df['constraint'] == 'country_unconstrained') &
                       (df['year'] == 2040)].copy()
    revenue_early_country = early_country.groupby('reference_mineral')['revenue_usd'].sum()
    early_country_revenue = [revenue_early_country.get(m, 0) / 1e9 for m in minerals]

    # Bar 4: Early Refining 2040 Region Unconstrained
    early_region = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                      (df['constraint'] == 'region_unconstrained') &
                      (df['year'] == 2040)].copy()
    revenue_early_region = early_region.groupby('reference_mineral')['revenue_usd'].sum()
    early_region_revenue = [revenue_early_region.get(m, 0) / 1e9 for m in minerals]

    # Bar 5: Precursor 2040 Country Unconstrained
    precursor_country = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                          (df['constraint'] == 'country_unconstrained') &
                          (df['year'] == 2040)].copy()
    revenue_precursor_country = precursor_country.groupby('reference_mineral')['revenue_usd'].sum()
    precursor_country_revenue = [revenue_precursor_country.get(m, 0) / 1e9 for m in minerals]

    # Bar 6: Precursor 2040 Region Unconstrained
    precursor_region = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                         (df['constraint'] == 'region_unconstrained') &
                         (df['year'] == 2040)].copy()
    revenue_precursor_region = precursor_region.groupby('reference_mineral')['revenue_usd'].sum()
    precursor_region_revenue = [revenue_precursor_region.get(m, 0) / 1e9 for m in minerals]

    # Create bar data structures
    revenue_bars = [
        ("Baseline", baseline_revenue),
        ("Unconstrained", bau_revenue),
        ("Country Unconstrained", early_country_revenue),
        ("Region Unconstrained", early_region_revenue),
        ("Country Unconstrained", precursor_country_revenue),
        ("Region Unconstrained", precursor_region_revenue),
    ]

    return revenue_bars


def plot_revenue_single_axis_clean(df, output_dir):
    """Generate clean single-axis revenue stacked bar chart"""
    # Import the generalized plotting function from emissions/water script
    import sys
    sys.path.append(os.path.dirname(__file__))
    from plot_emissions_water_all_countries import plot_clean_stacks

    os.makedirs(output_dir, exist_ok=True)

    revenue_bars = extract_revenue_data(df)

    centers = [0, 1, (2+3)/2, (4+5)/2]
    headings = ["Baseline (2022)", "BAU (2040)",
                "Early Refining (2040)", "Precursor Product (2040)"]

    revenue_path = os.path.join(output_dir, "revenue_single_axis_clean.png")
    plot_clean_stacks(
        bars=revenue_bars,
        ylabel="Revenue (Billion USD)",
        total_fmt=lambda v: f"{int(round(v,0))}",
        seg_label_threshold=5,  # 5 billion USD
        centers=centers,
        headings=headings,
        outfile=revenue_path
    )

    return [revenue_path]


def extract_revenue_data_comparison(df):
    """
    Extract both constrained and unconstrained revenue data for 2040 scenarios (NO baseline).

    Returns 10 bars: BAU (C+U), Early Refining (CC+CU+RC+RU), Precursor (CC+CU+RC+RU)

    Returns:
        revenue_bars: List of 10 tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in Billion USD
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # BAU 2040 - Constrained and Unconstrained
    bau_constrained = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
                         (df['constraint'] == 'country_constrained') &
                         (df['year'] == 2040)].copy()

    bau_unconstrained = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
                           (df['constraint'] == 'country_unconstrained') &
                           (df['year'] == 2040)].copy()

    # Early Refining 2040 - All 4 combinations
    early_country_constrained = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                                   (df['constraint'] == 'country_constrained') &
                                   (df['year'] == 2040)].copy()

    early_country_unconstrained = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                                     (df['constraint'] == 'country_unconstrained') &
                                     (df['year'] == 2040)].copy()

    early_region_constrained = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                                  (df['constraint'] == 'region_constrained') &
                                  (df['year'] == 2040)].copy()

    early_region_unconstrained = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                                    (df['constraint'] == 'region_unconstrained') &
                                    (df['year'] == 2040)].copy()

    # Precursor 2040 - All 4 combinations
    precursor_country_constrained = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                                       (df['constraint'] == 'country_constrained') &
                                       (df['year'] == 2040)].copy()

    precursor_country_unconstrained = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                                         (df['constraint'] == 'country_unconstrained') &
                                         (df['year'] == 2040)].copy()

    precursor_region_constrained = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                                      (df['constraint'] == 'region_constrained') &
                                      (df['year'] == 2040)].copy()

    precursor_region_unconstrained = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                                        (df['constraint'] == 'region_unconstrained') &
                                        (df['year'] == 2040)].copy()

    # Aggregate revenue for each scenario
    def aggregate_revenue(data_frame):
        revenue = data_frame.groupby('reference_mineral')['revenue_usd'].sum() / 1e9  # Billion USD
        return [revenue.get(m, 0) for m in minerals]

    bau_c_revenue = aggregate_revenue(bau_constrained)
    bau_u_revenue = aggregate_revenue(bau_unconstrained)
    early_cc_revenue = aggregate_revenue(early_country_constrained)
    early_cu_revenue = aggregate_revenue(early_country_unconstrained)
    early_rc_revenue = aggregate_revenue(early_region_constrained)
    early_ru_revenue = aggregate_revenue(early_region_unconstrained)
    prec_cc_revenue = aggregate_revenue(precursor_country_constrained)
    prec_cu_revenue = aggregate_revenue(precursor_country_unconstrained)
    prec_rc_revenue = aggregate_revenue(precursor_region_constrained)
    prec_ru_revenue = aggregate_revenue(precursor_region_unconstrained)

    # Create 10 bars (NO baseline)
    revenue_bars = [
        ("Constrained", bau_c_revenue),
        ("Unconstrained", bau_u_revenue),
        ("Country Constrained", early_cc_revenue),
        ("Country Unconstrained", early_cu_revenue),
        ("Region Constrained", early_rc_revenue),
        ("Region Unconstrained", early_ru_revenue),
        ("Country Constrained", prec_cc_revenue),
        ("Country Unconstrained", prec_cu_revenue),
        ("Region Constrained", prec_rc_revenue),
        ("Region Unconstrained", prec_ru_revenue),
    ]

    return revenue_bars


def plot_revenue_single_axis_comparison(df, output_dir):
    """Generate comparison chart with both constrained and unconstrained (10 bars, no baseline)"""
    # Import the generalized plotting function from emissions/water script
    import sys
    sys.path.append(os.path.dirname(__file__))
    from plot_emissions_water_all_countries import plot_clean_stacks

    os.makedirs(output_dir, exist_ok=True)

    revenue_bars = extract_revenue_data_comparison(df)

    # Centers for 10 bars: [BAU×2] [Early×4] [Precursor×4]
    centers = [(0+1)/2, (2+3+4+5)/4, (6+7+8+9)/4]
    headings = ["BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    revenue_path = os.path.join(output_dir, "revenue_single_axis_constrained_vs_unconstrained.png")
    plot_clean_stacks(
        bars=revenue_bars,
        ylabel="Revenue (Billion USD)",
        total_fmt=lambda v: f"{int(round(v,0))}",
        seg_label_threshold=5,  # 5 billion USD
        centers=centers,
        headings=headings,
        outfile=revenue_path
    )

    return [revenue_path]
