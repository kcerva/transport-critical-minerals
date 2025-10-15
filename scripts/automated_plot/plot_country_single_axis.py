"""
Country-level Single-Axis Charts
Generates single-axis stacked bar charts for individual countries showing indicators by mineral
"""

import os
import pandas as pd
import numpy as np


def get_scenario_name(base_scenario, constraint_type):
    """Get correct scenario name based on constraint type"""
    if constraint_type == 'country':
        return f"{base_scenario}_mid_min_threshold_metal_tons"
    elif constraint_type == 'region':
        return f"{base_scenario}_mid_max_threshold_metal_tons"
    else:
        raise ValueError(f"Unknown constraint_type: {constraint_type}")


def extract_country_revenue_data_clean(df, country_iso3):
    """
    Extract revenue data for country single-axis chart with baseline + unconstrained scenarios

    Returns:
        revenue_bars: List of tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in Million USD
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    country_df = df[df['iso3'] == country_iso3]

    # Bar 1: Baseline 2022
    baseline = country_df[(country_df['scenario'] == '2022_baseline') & (country_df['year'] == 2022)].copy()
    revenue_baseline = baseline.groupby('reference_mineral')['revenue_usd'].sum() / 1e6
    baseline_revenue = [revenue_baseline.get(m, 0) for m in minerals]

    # Bar 2: BAU 2040 Unconstrained
    bau = country_df[
        (country_df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()
    revenue_bau = bau.groupby('reference_mineral')['revenue_usd'].sum() / 1e6
    bau_revenue = [revenue_bau.get(m, 0) for m in minerals]

    # Bar 3: Early Refining 2040 Country Unconstrained
    early_country = country_df[
        (country_df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()
    revenue_early_country = early_country.groupby('reference_mineral')['revenue_usd'].sum() / 1e6
    early_country_revenue = [revenue_early_country.get(m, 0) for m in minerals]

    # Bar 4: Early Refining 2040 Region Unconstrained
    early_region = country_df[
        (country_df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()
    revenue_early_region = early_region.groupby('reference_mineral')['revenue_usd'].sum() / 1e6
    early_region_revenue = [revenue_early_region.get(m, 0) for m in minerals]

    # Bar 5: Precursor 2040 Country Unconstrained
    precursor_country = country_df[
        (country_df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()
    revenue_precursor_country = precursor_country.groupby('reference_mineral')['revenue_usd'].sum() / 1e6
    precursor_country_revenue = [revenue_precursor_country.get(m, 0) for m in minerals]

    # Bar 6: Precursor 2040 Region Unconstrained
    precursor_region = country_df[
        (country_df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()
    revenue_precursor_region = precursor_region.groupby('reference_mineral')['revenue_usd'].sum() / 1e6
    precursor_region_revenue = [revenue_precursor_region.get(m, 0) for m in minerals]

    revenue_bars = [
        ("Baseline", baseline_revenue),
        ("Unconstrained", bau_revenue),
        ("Country Unconstrained", early_country_revenue),
        ("Region Unconstrained", early_region_revenue),
        ("Country Unconstrained", precursor_country_revenue),
        ("Region Unconstrained", precursor_region_revenue),
    ]

    return revenue_bars


def extract_country_revenue_data_comparison(df, country_iso3):
    """
    Extract revenue data for country comparison chart (constrained + unconstrained, no baseline)

    Returns 10 bars: BAU (C+U), Early Refining (CC+CU+RC+RU), Precursor (CC+CU+RC+RU)
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    country_df = df[df['iso3'] == country_iso3]

    # BAU 2040 - Constrained and Unconstrained
    bau_c = country_df[
        (country_df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_constrained') &
        (country_df['year'] == 2040)
    ].copy()

    bau_u = country_df[
        (country_df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()

    # Early Refining 2040 - All 4 combinations
    early_cc = country_df[
        (country_df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_constrained') &
        (country_df['year'] == 2040)
    ].copy()

    early_cu = country_df[
        (country_df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()

    early_rc = country_df[
        (country_df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_constrained') &
        (country_df['year'] == 2040)
    ].copy()

    early_ru = country_df[
        (country_df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()

    # Precursor 2040 - All 4 combinations
    prec_cc = country_df[
        (country_df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_constrained') &
        (country_df['year'] == 2040)
    ].copy()

    prec_cu = country_df[
        (country_df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()

    prec_rc = country_df[
        (country_df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_constrained') &
        (country_df['year'] == 2040)
    ].copy()

    prec_ru = country_df[
        (country_df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_unconstrained') &
        (country_df['year'] == 2040)
    ].copy()

    # Aggregate revenue for each scenario
    def aggregate_revenue(data_frame):
        revenue = data_frame.groupby('reference_mineral')['revenue_usd'].sum() / 1e6  # Million USD
        return [revenue.get(m, 0) for m in minerals]

    revenue_bars = [
        ("Constrained", aggregate_revenue(bau_c)),
        ("Unconstrained", aggregate_revenue(bau_u)),
        ("Country Constrained", aggregate_revenue(early_cc)),
        ("Country Unconstrained", aggregate_revenue(early_cu)),
        ("Region Constrained", aggregate_revenue(early_rc)),
        ("Region Unconstrained", aggregate_revenue(early_ru)),
        ("Country Constrained", aggregate_revenue(prec_cc)),
        ("Country Unconstrained", aggregate_revenue(prec_cu)),
        ("Region Constrained", aggregate_revenue(prec_rc)),
        ("Region Unconstrained", aggregate_revenue(prec_ru)),
    ]

    return revenue_bars


def extract_country_water_co2_data_clean(df, country_iso3):
    """
    Extract water and CO2 data for country single-axis chart with baseline + unconstrained scenarios

    Returns:
        tuple: (water_bars, co2_bars)
        - water_bars: in Million m³
        - co2_bars: in Kilotonne CO2e
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    country_df = df[df['iso3'] == country_iso3]

    def extract_for_scenario(scenario_filter):
        """Helper to extract water and CO2 for a scenario"""
        data = country_df[scenario_filter].copy()

        # Calculate total CO2 (transport + energy)
        data['total_co2_kt'] = (data['transport_total_tonsCO2eq'] + data['energy_tonsCO2eq']) / 1000

        water = data.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
        co2 = data.groupby('reference_mineral')['total_co2_kt'].sum()

        return ([water.get(m, 0) for m in minerals],
                [co2.get(m, 0) for m in minerals])

    # Bar 1: Baseline 2022
    baseline_water, baseline_co2 = extract_for_scenario(
        (country_df['scenario'] == '2022_baseline') & (country_df['year'] == 2022)
    )

    # Bar 2: BAU 2040 Unconstrained
    bau_water, bau_co2 = extract_for_scenario(
        (country_df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    )

    # Bar 3: Early Refining Country Unconstrained
    early_c_water, early_c_co2 = extract_for_scenario(
        (country_df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    )

    # Bar 4: Early Refining Region Unconstrained
    early_r_water, early_r_co2 = extract_for_scenario(
        (country_df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_unconstrained') &
        (country_df['year'] == 2040)
    )

    # Bar 5: Precursor Country Unconstrained
    prec_c_water, prec_c_co2 = extract_for_scenario(
        (country_df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
        (country_df['constraint'] == 'country_unconstrained') &
        (country_df['year'] == 2040)
    )

    # Bar 6: Precursor Region Unconstrained
    prec_r_water, prec_r_co2 = extract_for_scenario(
        (country_df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
        (country_df['constraint'] == 'region_unconstrained') &
        (country_df['year'] == 2040)
    )

    water_bars = [
        ("Baseline", baseline_water),
        ("Unconstrained", bau_water),
        ("Country Unconstrained", early_c_water),
        ("Region Unconstrained", early_r_water),
        ("Country Unconstrained", prec_c_water),
        ("Region Unconstrained", prec_r_water),
    ]

    co2_bars = [
        ("Baseline", baseline_co2),
        ("Unconstrained", bau_co2),
        ("Country Unconstrained", early_c_co2),
        ("Region Unconstrained", early_r_co2),
        ("Country Unconstrained", prec_c_co2),
        ("Region Unconstrained", prec_r_co2),
    ]

    return water_bars, co2_bars


def extract_country_water_co2_data_comparison(df, country_iso3):
    """
    Extract water and CO2 data for country comparison chart (10 bars, no baseline)

    Returns:
        tuple: (water_bars, co2_bars)
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    country_df = df[df['iso3'] == country_iso3]

    # Calculate total CO2
    country_df = country_df.copy()
    country_df['total_co2_kt'] = (country_df['transport_total_tonsCO2eq'] + country_df['energy_tonsCO2eq']) / 1000

    def aggregate_data(data_frame):
        """Helper to aggregate water and CO2"""
        water = data_frame.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
        co2 = data_frame.groupby('reference_mineral')['total_co2_kt'].sum()
        return ([water.get(m, 0) for m in minerals],
                [co2.get(m, 0) for m in minerals])

    # Extract all 10 scenarios
    scenarios = [
        ('bau_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Constrained'),
        ('bau_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Unconstrained'),
        ('early_refining_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Country Constrained'),
        ('early_refining_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Country Unconstrained'),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_constrained', 'Region Constrained'),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Region Unconstrained'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Country Constrained'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Country Unconstrained'),
        ('precursor_2040_mid_max_threshold_metal_tons', 'region_constrained', 'Region Constrained'),
        ('precursor_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Region Unconstrained'),
    ]

    water_bars = []
    co2_bars = []

    for scenario, constraint, label in scenarios:
        data = country_df[
            (country_df['scenario'] == scenario) &
            (country_df['constraint'] == constraint) &
            (country_df['year'] == 2040)
        ]
        water, co2 = aggregate_data(data)
        water_bars.append((label, water))
        co2_bars.append((label, co2))

    return water_bars, co2_bars


def extract_country_transport_data_clean(df, country_iso3):
    """
    Extract transport volume data for country single-axis chart with baseline + unconstrained scenarios

    Returns:
        transport_bars: in Million tonne-km
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    country_df = df[df['iso3'] == country_iso3]

    def extract_transport(scenario_filter):
        data = country_df[scenario_filter].copy()
        transport = data.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
        return [transport.get(m, 0) for m in minerals]

    transport_bars = [
        ("Baseline", extract_transport(
            (country_df['scenario'] == '2022_baseline') & (country_df['year'] == 2022)
        )),
        ("Unconstrained", extract_transport(
            (country_df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
            (country_df['constraint'] == 'country_unconstrained') &
            (country_df['year'] == 2040)
        )),
        ("Country Unconstrained", extract_transport(
            (country_df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
            (country_df['constraint'] == 'country_unconstrained') &
            (country_df['year'] == 2040)
        )),
        ("Region Unconstrained", extract_transport(
            (country_df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
            (country_df['constraint'] == 'region_unconstrained') &
            (country_df['year'] == 2040)
        )),
        ("Country Unconstrained", extract_transport(
            (country_df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
            (country_df['constraint'] == 'country_unconstrained') &
            (country_df['year'] == 2040)
        )),
        ("Region Unconstrained", extract_transport(
            (country_df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
            (country_df['constraint'] == 'region_unconstrained') &
            (country_df['year'] == 2040)
        )),
    ]

    return transport_bars


def extract_country_transport_data_comparison(df, country_iso3):
    """
    Extract transport volume data for country comparison chart (10 bars, no baseline)

    Returns:
        transport_bars: in Million tonne-km
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    country_df = df[df['iso3'] == country_iso3]

    def aggregate_transport(data_frame):
        transport = data_frame.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
        return [transport.get(m, 0) for m in minerals]

    scenarios = [
        ('bau_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Constrained'),
        ('bau_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Unconstrained'),
        ('early_refining_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Country Constrained'),
        ('early_refining_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Country Unconstrained'),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_constrained', 'Region Constrained'),
        ('early_refining_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Region Unconstrained'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'country_constrained', 'Country Constrained'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'country_unconstrained', 'Country Unconstrained'),
        ('precursor_2040_mid_max_threshold_metal_tons', 'region_constrained', 'Region Constrained'),
        ('precursor_2040_mid_max_threshold_metal_tons', 'region_unconstrained', 'Region Unconstrained'),
    ]

    transport_bars = []

    for scenario, constraint, label in scenarios:
        data = country_df[
            (country_df['scenario'] == scenario) &
            (country_df['constraint'] == constraint) &
            (country_df['year'] == 2040)
        ]
        transport = aggregate_transport(data)
        transport_bars.append((label, transport))

    return transport_bars


def generate_country_single_axis_charts(df, country_iso3, output_dir):
    """
    Generate all single-axis charts for a specific country

    Args:
        df: Full DataFrame
        country_iso3: Country ISO3 code
        output_dir: Output directory for charts

    Returns:
        dict: Paths to generated charts
    """
    from plot_emissions_water_all_countries import plot_clean_stacks

    os.makedirs(output_dir, exist_ok=True)

    chart_paths = {}

    # Common parameters
    centers = [0, 1, (2+3)/2, (4+5)/2]
    headings = ["Baseline (2022)", "BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    centers_comp = [(0+1)/2, (2+3+4+5)/4, (6+7+8+9)/4]
    headings_comp = ["BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    print(f"Generating single-axis charts for {country_iso3}...")

    # Revenue charts
    try:
        revenue_bars = extract_country_revenue_data_clean(df, country_iso3)
        revenue_path_clean = os.path.join(output_dir, "revenue_single_axis_clean.png")
        plot_clean_stacks(
            bars=revenue_bars,
            ylabel="Revenue (Million USD)",
            total_fmt=lambda v: f"{int(round(v,0))}",
            seg_label_threshold=max([sum(bar[1]) for bar in revenue_bars]) * 0.05,  # 5% of max
            centers=centers,
            headings=headings,
            outfile=revenue_path_clean
        )
        chart_paths['revenue_clean'] = revenue_path_clean

        revenue_bars_comp = extract_country_revenue_data_comparison(df, country_iso3)
        revenue_path_comp = os.path.join(output_dir, "revenue_single_axis_comparison.png")
        plot_clean_stacks(
            bars=revenue_bars_comp,
            ylabel="Revenue (Million USD)",
            total_fmt=lambda v: f"{int(round(v,0))}",
            seg_label_threshold=max([sum(bar[1]) for bar in revenue_bars_comp]) * 0.05,
            centers=centers_comp,
            headings=headings_comp,
            outfile=revenue_path_comp
        )
        chart_paths['revenue_comparison'] = revenue_path_comp
        print(f"  ✓ Revenue charts")
    except Exception as e:
        print(f"  ✗ Revenue charts failed: {e}")

    # Water and CO2 charts
    try:
        water_bars, co2_bars = extract_country_water_co2_data_clean(df, country_iso3)

        water_path_clean = os.path.join(output_dir, "water_single_axis_clean.png")
        plot_clean_stacks(
            bars=water_bars,
            ylabel="Water Usage (Million m³)",
            total_fmt=lambda v: f"{int(round(v,0))}",
            seg_label_threshold=max([sum(bar[1]) for bar in water_bars]) * 0.05,
            centers=centers,
            headings=headings,
            outfile=water_path_clean
        )
        chart_paths['water_clean'] = water_path_clean

        co2_path_clean = os.path.join(output_dir, "co2_single_axis_clean.png")
        plot_clean_stacks(
            bars=co2_bars,
            ylabel="CO₂ Emissions (Kilotonne)",
            total_fmt=lambda v: f"{v:.1f}",
            seg_label_threshold=max([sum(bar[1]) for bar in co2_bars]) * 0.05,
            centers=centers,
            headings=headings,
            outfile=co2_path_clean
        )
        chart_paths['co2_clean'] = co2_path_clean
        print(f"  ✓ Water and CO2 charts (clean)")

        water_bars_comp, co2_bars_comp = extract_country_water_co2_data_comparison(df, country_iso3)

        water_path_comp = os.path.join(output_dir, "water_single_axis_comparison.png")
        plot_clean_stacks(
            bars=water_bars_comp,
            ylabel="Water Usage (Million m³)",
            total_fmt=lambda v: f"{int(round(v,0))}",
            seg_label_threshold=max([sum(bar[1]) for bar in water_bars_comp]) * 0.05,
            centers=centers_comp,
            headings=headings_comp,
            outfile=water_path_comp
        )
        chart_paths['water_comparison'] = water_path_comp

        co2_path_comp = os.path.join(output_dir, "co2_single_axis_comparison.png")
        plot_clean_stacks(
            bars=co2_bars_comp,
            ylabel="CO₂ Emissions (Kilotonne)",
            total_fmt=lambda v: f"{v:.1f}",
            seg_label_threshold=max([sum(bar[1]) for bar in co2_bars_comp]) * 0.05,
            centers=centers_comp,
            headings=headings_comp,
            outfile=co2_path_comp
        )
        chart_paths['co2_comparison'] = co2_path_comp
        print(f"  ✓ Water and CO2 charts (comparison)")
    except Exception as e:
        print(f"  ✗ Water/CO2 charts failed: {e}")

    # Transport volume charts
    try:
        transport_bars = extract_country_transport_data_clean(df, country_iso3)
        transport_path_clean = os.path.join(output_dir, "transport_volume_single_axis_clean.png")
        plot_clean_stacks(
            bars=transport_bars,
            ylabel="Transport Volume (Million tonne km)",
            total_fmt=lambda v: f"{int(round(v,0))}",
            seg_label_threshold=max([sum(bar[1]) for bar in transport_bars]) * 0.05,
            centers=centers,
            headings=headings,
            outfile=transport_path_clean
        )
        chart_paths['transport_clean'] = transport_path_clean

        transport_bars_comp = extract_country_transport_data_comparison(df, country_iso3)
        transport_path_comp = os.path.join(output_dir, "transport_volume_single_axis_comparison.png")
        plot_clean_stacks(
            bars=transport_bars_comp,
            ylabel="Transport Volume (Million tonne km)",
            total_fmt=lambda v: f"{int(round(v,0))}",
            seg_label_threshold=max([sum(bar[1]) for bar in transport_bars_comp]) * 0.05,
            centers=centers_comp,
            headings=headings_comp,
            outfile=transport_path_comp
        )
        chart_paths['transport_comparison'] = transport_path_comp
        print(f"  ✓ Transport volume charts")
    except Exception as e:
        print(f"  ✗ Transport charts failed: {e}")

    print(f"Generated {len(chart_paths)} charts for {country_iso3}")

    return chart_paths
