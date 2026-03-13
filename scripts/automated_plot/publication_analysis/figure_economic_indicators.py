"""
Economic Indicators Comparison Figure

Creates a six-panel figure (3 rows × 2 columns) comparing economic indicators across scenarios:

Left Column (Revenue):
  Panel A: Export revenues by mineral (stage > 0)
  Panel B: Export revenues by processing type (stage > 0)
  Panel C: GDP share heatmap (Regional - National differences)

Right Column (Cost & Competitiveness):
  Panel D: Total cost by mineral
  Panel E: Total cost by component
  Panel F: Competitiveness matrix (Precursor National_U vs Regional_U)

All bar panels show 7 bars representing:
- Baseline: 2022 actual values (1 bar)
- BAU: Constrained/Unconstrained (2 bars - National = Regional for BAU)
- Precursor: Constrained/Unconstrained × National/Regional (4 bars)

Error bars show demand uncertainty (Low-Mid-High range)
Hatching patterns differentiate Constrained (hatched) vs Unconstrained (solid)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import seaborn as sns

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publication_analysis.config import (
    FIGURE_SIZES, DPI_PUBLICATION, DPI_SCREEN,
    PUBLICATION_STYLE
)
from publication_analysis.scenario_utils import (
    filter_scenarios_by_goal,
    extract_scenario_attributes
)
from plot_config import reference_mineral_colormap
from plot_utils import PROCESSING_TYPE_COLORS

# Import competitiveness functions
from plot_competitiveness_summary import (
    extract_cumulative_costs,
    calculate_quintile_ranks,
    create_heatmap_matrix,
    format_cost_annotation,
    MINERAL_ORDER as COMP_MINERAL_ORDER
)

# Competitiveness scenario config
COMP_SCENARIO_CONFIG = {
    'precursor_2040': {
        'title': 'Precursor Product',
        'included_types': ['Beneficiation', 'Early refining', 'Precursor related product'],
        'target_type': 'Precursor related product'
    }
}


# Scenario configuration for 7 bars (Baseline + BAU + Precursor)
SCENARIO_CONFIG = [
    ('baseline', None, None, 'Baseline'),
    ('bau', 'min', 'constrained', 'BAU_C'),
    ('bau', 'min', 'unconstrained', 'BAU_U'),
    ('precursor', 'min', 'constrained', 'Prec_C_N'),
    ('precursor', 'min', 'unconstrained', 'Prec_U_N'),
    ('precursor', 'max', 'constrained', 'Prec_C_R'),
    ('precursor', 'max', 'unconstrained', 'Prec_U_R'),
]

# Mineral order by production volume (for stacking)
MINERAL_ORDER = ['copper', 'manganese', 'graphite', 'cobalt', 'nickel', 'lithium']

# Processing type order (for stacking)
PROCESSING_ORDER = ['Beneficiation', 'Early refining', 'Precursor related product']

# Cost type order (for stacking in Panel E)
COST_TYPE_ORDER = ['Production', 'Transport', 'Energy']

# Cost type colors (for Panel E)
COST_TYPE_COLORS = {
    'Production': '#4daf4a',    # Green
    'Transport': '#ff7f00',      # Orange
    'Energy': '#984ea3'          # Purple
}

# GDP inflation adjustment factors
GDP_INFLATION_FACTORS = {
    '2022': 1.0,
    '2030': 1.22,
    '2040': 1.56
}


def adjust_gdp_for_inflation(df):
    """
    Adjust GDP values for inflation based on scenario year

    Args:
        df: DataFrame with 'scenario' and 'gdp_usd' columns

    Returns:
        DataFrame with adjusted 'gdp_usd' values
    """
    df = df.copy()

    for year, factor in GDP_INFLATION_FACTORS.items():
        mask = df['scenario'].str.contains(year)
        df.loc[mask, 'gdp_usd'] = df.loc[mask, 'gdp_usd'] * factor

    return df


def prepare_economic_data(df):
    """
    Prepare data for all three economic panels with identical scenario structure

    Args:
        df: Main data DataFrame

    Returns:
        tuple: (revenue_by_mineral_data, revenue_by_processing_data, gdp_share_data,
                cost_by_mineral_data, cost_breakdown_data)
            revenue_by_mineral_data: Dict[scenario_label][demand][mineral] = revenue
            revenue_by_processing_data: Dict[scenario_label][demand][processing_type] = revenue
            gdp_share_data: Dict[scenario_label][demand] = gdp_share_percentage
            cost_by_mineral_data: Dict[scenario_label][demand][mineral] = cost
            cost_breakdown_data: Dict[scenario_label][demand][cost_type] = cost
    """
    # Filter for processing only (stage > 0, exclude metal content)
    df_processing = df[df['processing_stage'] > 0].copy()

    # Adjust GDP for inflation (constant across demand levels for same scenario)
    df_processing = adjust_gdp_for_inflation(df_processing)

    revenue_by_mineral_data = {}
    revenue_by_processing_data = {}
    gdp_share_data = {}
    cost_by_mineral_data = {}
    cost_breakdown_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        revenue_by_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        revenue_by_processing_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        gdp_share_data[label] = {'low': 0.0, 'mid': 0.0, 'high': 0.0}
        cost_by_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        cost_breakdown_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants, different naming)
        if goal == 'baseline':
            scenario_name = '2022_baseline'

            # Baseline uses all constraints - sum across all
            df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

            if df_scenario.empty:
                print(f"Warning: No data for {label}")
                continue

            # Use same data for low/mid/high (no demand uncertainty for baseline)
            for demand in ['low', 'mid', 'high']:
                # Revenue by Mineral Panel
                by_mineral = df_scenario.groupby('reference_mineral')['revenue_usd'].sum()
                for mineral in MINERAL_ORDER:
                    revenue_by_mineral_data[label][demand][mineral] = by_mineral.get(mineral, 0)

                # Revenue by Processing Type Panel
                by_processing = df_scenario.groupby('processing_type')['revenue_usd'].sum()
                for ptype in PROCESSING_ORDER:
                    revenue_by_processing_data[label][demand][ptype] = by_processing.get(ptype, 0)

                # GDP Share Panel: total_revenue / total_gdp × 100
                total_revenue = df_scenario['revenue_usd'].sum()
                total_gdp = df_scenario['gdp_usd'].sum()
                gdp_share_data[label][demand] = (total_revenue / total_gdp * 100) if total_gdp > 0 else 0.0

                # Cost by Mineral Panel (Panel D)
                by_mineral_cost = df_scenario.groupby('reference_mineral')['all_cost_usd'].sum()
                for mineral in MINERAL_ORDER:
                    cost_by_mineral_data[label][demand][mineral] = by_mineral_cost.get(mineral, 0)

                # Cost Breakdown Panel (Panel E)
                production_cost = df_scenario['production_cost_usd'].sum()
                transport_cost = (df_scenario['export_transport_cost_usd'].sum() +
                                 df_scenario['import_transport_cost_usd'].sum())
                energy_cost = (df_scenario['energy_investment_usd'].sum() +
                              df_scenario['energy_opex'].sum())
                cost_breakdown_data[label][demand]['Production'] = production_cost
                cost_breakdown_data[label][demand]['Transport'] = transport_cost
                cost_breakdown_data[label][demand]['Energy'] = energy_cost

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                # Build scenario name
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'

                # Build constraint column name
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                # Filter data for processing (stage > 0)
                df_scenario = df_processing[
                    (df_processing['scenario'] == scenario_name) &
                    (df_processing['constraint'] == constraint_col)
                ].copy()

                if df_scenario.empty:
                    print(f"Warning: No data for {label} {demand} demand")
                    continue

                # Revenue by Mineral Panel
                by_mineral = df_scenario.groupby('reference_mineral')['revenue_usd'].sum()
                for mineral in MINERAL_ORDER:
                    revenue_by_mineral_data[label][demand][mineral] = by_mineral.get(mineral, 0)

                # Revenue by Processing Type Panel
                by_processing = df_scenario.groupby('processing_type')['revenue_usd'].sum()
                for ptype in PROCESSING_ORDER:
                    revenue_by_processing_data[label][demand][ptype] = by_processing.get(ptype, 0)

                # GDP Share Panel: total_revenue / total_gdp × 100
                total_revenue = df_scenario['revenue_usd'].sum()
                total_gdp = df_scenario['gdp_usd'].sum()
                gdp_share_data[label][demand] = (total_revenue / total_gdp * 100) if total_gdp > 0 else 0.0

                # Cost by Mineral Panel (Panel D)
                by_mineral_cost = df_scenario.groupby('reference_mineral')['all_cost_usd'].sum()
                for mineral in MINERAL_ORDER:
                    cost_by_mineral_data[label][demand][mineral] = by_mineral_cost.get(mineral, 0)

                # Cost Breakdown Panel (Panel E)
                production_cost = df_scenario['production_cost_usd'].sum()
                transport_cost = (df_scenario['export_transport_cost_usd'].sum() +
                                 df_scenario['import_transport_cost_usd'].sum())
                energy_cost = (df_scenario['energy_investment_usd'].sum() +
                              df_scenario['energy_opex'].sum())
                cost_breakdown_data[label][demand]['Production'] = production_cost
                cost_breakdown_data[label][demand]['Transport'] = transport_cost
                cost_breakdown_data[label][demand]['Energy'] = energy_cost

    return revenue_by_mineral_data, revenue_by_processing_data, gdp_share_data, cost_by_mineral_data, cost_breakdown_data


def prepare_country_gdp_data(df):
    """
    Prepare country-level GDP share data for heatmap visualization

    Returns country-level GDP shares (revenue as % of GDP) for:
    - All 14 countries in the study
    - All scenarios and constraint combinations
    - Low/Mid/High demand variants

    Returns:
        dict: {scenario_label: {demand: {country_iso3: gdp_share_pct}}}
              where scenario_label is like 'BAU_C', 'Prec_C_N', etc.
    """
    # Filter for processing only (stage > 0)
    df_processing = df[df['processing_stage'] > 0].copy()

    # Adjust GDP for inflation
    df_processing = adjust_gdp_for_inflation(df_processing)

    country_gdp_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        country_gdp_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants)
        if goal == 'baseline':
            scenario_name = '2022_baseline'
            df_scenario = df_processing[df_processing['scenario'] == scenario_name].copy()

            if df_scenario.empty:
                continue

            # Calculate by country
            # NOTE: GDP is repeated on each row for same country, so take max (unique non-zero value)
            by_country = df_scenario.groupby('iso3').agg({
                'revenue_usd': 'sum',
                'gdp_usd': 'max'  # Take max to get the unique non-zero GDP value
            }).reset_index()
            by_country['gdp_share_pct'] = (by_country['revenue_usd'] / by_country['gdp_usd'] * 100)

            # Use same data for low/mid/high (no demand uncertainty for baseline)
            for demand in ['low', 'mid', 'high']:
                for _, row in by_country.iterrows():
                    country_gdp_data[label][demand][row['iso3']] = row['gdp_share_pct']

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                df_scenario = df_processing[
                    (df_processing['scenario'] == scenario_name) &
                    (df_processing['constraint'] == constraint_col)
                ].copy()

                if df_scenario.empty:
                    continue

                # Calculate by country
                # NOTE: GDP is repeated on each row for same country, so take max (unique non-zero value)
                by_country = df_scenario.groupby('iso3').agg({
                    'revenue_usd': 'sum',
                    'gdp_usd': 'max'  # Take max to get the unique non-zero GDP value
                }).reset_index()
                by_country['gdp_share_pct'] = (by_country['revenue_usd'] / by_country['gdp_usd'] * 100)

                for _, row in by_country.iterrows():
                    country_gdp_data[label][demand][row['iso3']] = row['gdp_share_pct']

    return country_gdp_data


# Processing stage to processing type mapping
STAGE_TO_PROCESSING_TYPE = {
    1.0: 'Beneficiation',
    2.0: 'Early refining',
    3.0: 'Early refining',
    3.1: 'Early refining',
    4.0: 'Precursor related product',
    4.1: 'Precursor related product',
    4.2: 'Precursor related product',
    4.3: 'Precursor related product',
    5.0: 'Precursor related product',
}


def prepare_net_export_revenue_data(df):
    """
    Prepare NET export revenue data by mineral and processing type for Panels A & B

    Uses net export revenue (export revenue - import cost) from tonnage_flows_with_revenues.xlsx
    instead of gross export revenue from all_data.xlsx

    Returns:
        tuple: (net_revenue_by_mineral_data, net_revenue_by_processing_data)
            net_revenue_by_mineral_data: Dict[scenario_label][demand][mineral] = net_revenue
            net_revenue_by_processing_data: Dict[scenario_label][demand][processing_type] = net_revenue
    """
    import json
    from pathlib import Path

    # Load config to get paths
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'

    # Load tonnage flows data
    df_flows = pd.read_excel(flows_path, sheet_name='All_Flows')

    net_revenue_by_mineral_data = {}
    net_revenue_by_processing_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        net_revenue_by_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        net_revenue_by_processing_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants)
        if goal == 'baseline':
            scenario_name = '2022_baseline'
            constraint_col = 'country_unconstrained'

            # Filter for baseline
            df_scenario = df_flows[
                (df_flows['scenario'] == scenario_name) &
                (df_flows['constraint'] == constraint_col)
            ].copy()

            if df_scenario.empty:
                print(f"Warning: No flows data for {label}")
                continue

            # Calculate net export revenue
            # Exports: use export_revenue_usd
            exports = df_scenario[df_scenario['trade_type'] == 'Export'].copy()
            # Imports: use import_cost_at_price_usd
            imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].copy()

            # By mineral
            export_by_mineral = exports.groupby('reference_mineral')['export_revenue_usd'].sum()
            import_by_mineral = imports.groupby('reference_mineral')['import_cost_at_price_usd'].sum()

            for demand in ['low', 'mid', 'high']:
                for mineral in MINERAL_ORDER:
                    export_rev = export_by_mineral.get(mineral, 0)
                    import_cost = import_by_mineral.get(mineral, 0)
                    net_revenue_by_mineral_data[label][demand][mineral] = export_rev - import_cost

            # By processing type - use final_processing_stage for exports
            exports['processing_type'] = exports['final_processing_stage'].map(STAGE_TO_PROCESSING_TYPE)
            export_by_ptype = exports.groupby('processing_type')['export_revenue_usd'].sum()

            # For imports, use initial_processing_stage
            imports['processing_type'] = imports['initial_processing_stage'].map(STAGE_TO_PROCESSING_TYPE)
            import_by_ptype = imports.groupby('processing_type')['import_cost_at_price_usd'].sum()

            for demand in ['low', 'mid', 'high']:
                for ptype in PROCESSING_ORDER:
                    export_rev = export_by_ptype.get(ptype, 0)
                    import_cost = import_by_ptype.get(ptype, 0)
                    net_revenue_by_processing_data[label][demand][ptype] = export_rev - import_cost

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                df_scenario = df_flows[
                    (df_flows['scenario'] == scenario_name) &
                    (df_flows['constraint'] == constraint_col)
                ].copy()

                if df_scenario.empty:
                    print(f"Warning: No flows data for {label} {demand} demand")
                    continue

                # Calculate net export revenue
                exports = df_scenario[df_scenario['trade_type'] == 'Export'].copy()
                imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].copy()

                # By mineral
                export_by_mineral = exports.groupby('reference_mineral')['export_revenue_usd'].sum()
                import_by_mineral = imports.groupby('reference_mineral')['import_cost_at_price_usd'].sum()

                for mineral in MINERAL_ORDER:
                    export_rev = export_by_mineral.get(mineral, 0)
                    import_cost = import_by_mineral.get(mineral, 0)
                    net_revenue_by_mineral_data[label][demand][mineral] = export_rev - import_cost

                # By processing type
                exports['processing_type'] = exports['final_processing_stage'].map(STAGE_TO_PROCESSING_TYPE)
                export_by_ptype = exports.groupby('processing_type')['export_revenue_usd'].sum()

                imports['processing_type'] = imports['initial_processing_stage'].map(STAGE_TO_PROCESSING_TYPE)
                import_by_ptype = imports.groupby('processing_type')['import_cost_at_price_usd'].sum()

                for ptype in PROCESSING_ORDER:
                    export_rev = export_by_ptype.get(ptype, 0)
                    import_cost = import_by_ptype.get(ptype, 0)
                    net_revenue_by_processing_data[label][demand][ptype] = export_rev - import_cost

    return net_revenue_by_mineral_data, net_revenue_by_processing_data


def prepare_country_net_export_revenue_gdp_data(df):
    """
    Prepare country-level NET export revenue GDP share data for heatmap visualization

    Uses net export revenue (export revenue - import cost) instead of gross export revenue

    Returns:
        dict: {scenario_label: {demand: {country_iso3: gdp_share_pct}}}
              where scenario_label is like 'BAU_C', 'Prec_C_N', etc.
    """
    import json
    from pathlib import Path

    # Load config to get paths
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'

    # Load tonnage flows data
    df_flows = pd.read_excel(flows_path, sheet_name='All_Flows')

    # Get GDP data with inflation adjustment
    df_gdp = adjust_gdp_for_inflation(df.copy())
    # NOTE: GDP is repeated on each row for same country/scenario, so take max (unique non-zero value)
    # Using .first() can pick a row with GDP=0 if that row has no export revenue
    # Scenario names include year (e.g., '2022_baseline', 'bau_2040_mid_min_threshold_metal_tons')
    # so grouping by ['iso3', 'scenario'] already separates years - .max() is safe
    gdp_by_country_scenario = df_gdp.groupby(['iso3', 'scenario'])['gdp_usd'].max().to_dict()

    country_net_revenue_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        country_net_revenue_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants)
        if goal == 'baseline':
            scenario_name = '2022_baseline'
            constraint_col = 'country_unconstrained'

            # Filter for baseline
            df_scenario = df_flows[
                (df_flows['scenario'] == scenario_name) &
                (df_flows['constraint'] == constraint_col)
            ].copy()

            if df_scenario.empty:
                continue

            # Calculate net export revenue by country
            exports = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('iso3')['export_revenue_usd'].sum()
            imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('iso3')['import_cost_at_price_usd'].sum()

            # Get all countries
            all_countries = set(exports.index) | set(imports.index)

            for country in all_countries:
                export_rev = exports.get(country, 0)
                import_cost = imports.get(country, 0)
                net_revenue = export_rev - import_cost

                gdp = gdp_by_country_scenario.get((country, scenario_name), 0)

                if gdp > 0:
                    gdp_pct = (net_revenue / gdp) * 100
                    # Use same data for low/mid/high (no demand uncertainty for baseline)
                    for demand in ['low', 'mid', 'high']:
                        country_net_revenue_data[label][demand][country] = gdp_pct

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                df_scenario = df_flows[
                    (df_flows['scenario'] == scenario_name) &
                    (df_flows['constraint'] == constraint_col)
                ].copy()

                if df_scenario.empty:
                    continue

                # Calculate net export revenue by country
                exports = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('iso3')['export_revenue_usd'].sum()
                imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('iso3')['import_cost_at_price_usd'].sum()

                # Get all countries
                all_countries = set(exports.index) | set(imports.index)

                for country in all_countries:
                    export_rev = exports.get(country, 0)
                    import_cost = imports.get(country, 0)
                    net_revenue = export_rev - import_cost

                    gdp = gdp_by_country_scenario.get((country, scenario_name), 0)

                    if gdp > 0:
                        gdp_pct = (net_revenue / gdp) * 100
                        country_net_revenue_data[label][demand][country] = gdp_pct

    return country_net_revenue_data


def calculate_gdp_difference_matrix(country_gdp_data):
    """
    Calculate Regional - National GDP share differences for heatmap

    Returns:
        tuple: (difference_data, countries_sorted)
            difference_data: dict {scenario_col: {demand: {country: diff_pct}}}
            countries_sorted: list of country ISO3 codes sorted by total importance
    """
    # Scenarios to compare (exclude baseline, pair National with Regional)
    # Columns: BAU_C, BAU_U, EarlyRef_C, EarlyRef_U, Prec_C, Prec_U
    scenario_columns = [
        ('BAU_C', 'BAU_C'),      # BAU has no regional variant
        ('BAU_U', 'BAU_U'),      # BAU has no regional variant
        ('Prec_C_N', 'Prec_C_R', 'EarlyRef_C'),  # Early Refining Constrained
        ('Prec_U_N', 'Prec_U_R', 'EarlyRef_U'),  # Early Refining Unconstrained
        ('Prec_C_N', 'Prec_C_R', 'Prec_C'),      # Precursor Constrained
        ('Prec_U_N', 'Prec_U_R', 'Prec_U'),      # Precursor Unconstrained
    ]

    # Get all countries from data
    all_countries = set()
    for label_data in country_gdp_data.values():
        for demand_data in label_data.values():
            all_countries.update(demand_data.keys())

    # Calculate differences
    difference_data = {}

    # Skip BAU scenarios (no regional variant) and Early Refining (not for publication)
    # Only calculate for Precursor scenarios

    # For Precursor, calculate Regional - National
    scenario_pairs = [
        ('precursor_2040_mid_min_threshold_metal_tons', 'precursor_2040_mid_max_threshold_metal_tons', 'Prec_C', 'constrained'),
        ('precursor_2040_mid_min_threshold_metal_tons', 'precursor_2040_mid_max_threshold_metal_tons', 'Prec_U', 'unconstrained'),
    ]

    for nat_base, reg_base, col_label, constraint_type in scenario_pairs:
        difference_data[col_label] = {'low': {}, 'mid': {}, 'high': {}}

        # Find the corresponding labels in SCENARIO_CONFIG
        nat_label = None
        reg_label = None
        for goal, policy, constraint, label in SCENARIO_CONFIG:
            if goal != 'baseline':
                if policy == 'min' and constraint == constraint_type:
                    nat_label = label
                elif policy == 'max' and constraint == constraint_type:
                    reg_label = label

        if nat_label and reg_label:
            for demand in ['low', 'mid', 'high']:
                nat_data = country_gdp_data[nat_label][demand]
                reg_data = country_gdp_data[reg_label][demand]

                for country in all_countries:
                    nat_val = nat_data.get(country, 0.0)
                    reg_val = reg_data.get(country, 0.0)
                    difference_data[col_label][demand][country] = reg_val - nat_val

    # Sort countries by total absolute contribution (sum of mid-demand differences across all scenarios)
    # This puts countries with largest Regional-National GDP share differences at the top
    country_importance = {}
    for country in all_countries:
        total = sum(abs(difference_data[col]['mid'].get(country, 0))
                   for col in difference_data.keys())
        # Handle NaN values - treat as zero importance (should appear at bottom)
        if np.isnan(total) or np.isinf(total):
            total = 0.0
        country_importance[country] = total

    countries_sorted = sorted(country_importance.keys(),
                             key=lambda x: country_importance[x],
                             reverse=True)

    return difference_data, countries_sorted


def plot_gdp_difference_heatmap(ax, difference_data, countries_sorted, title,
                                 significant_threshold=2.0):
    """
    Plot heatmap showing Regional - National GDP share differences
    Now displays 6 columns: Low, Mid, High for each scenario (Prec_C and Prec_U)

    Args:
        ax: Matplotlib axis
        difference_data: dict {scenario_col: {demand: {country: diff_pct}}}
        countries_sorted: list of country ISO3 codes (sorted by importance)
        title: Panel title
        significant_threshold: Mark cells with |diff| > threshold (in percentage points)
    """
    import matplotlib.colors as mcolors
    from matplotlib import cm

    # 6 columns layout: Low, Mid, High for each scenario
    # Format: (scenario_key, demand_level, column_index)
    scenarios = ['Prec_C', 'Prec_U']
    demands = ['low', 'mid', 'high']

    # Create matrix: rows=countries, columns=6 (Low/Mid/High × 2 scenarios)
    n_countries = len(countries_sorted)
    n_cols = len(scenarios) * len(demands)  # 6 columns total

    matrix = np.zeros((n_countries, n_cols))

    # Fill matrix: column order is Prec_C_Low, Prec_C_Mid, Prec_C_High, Prec_U_Low, Prec_U_Mid, Prec_U_High
    for i, country in enumerate(countries_sorted):
        for j, scenario in enumerate(scenarios):
            for k, demand in enumerate(demands):
                col_idx = j * len(demands) + k  # Calculate column index
                matrix[i, col_idx] = difference_data[scenario][demand].get(country, 0)

    # Use fixed scale for consistent comparison (±15pp is reasonable max for regional-national differences)
    # Data max is typically ±13pp; using ±15pp gives consistent color interpretation
    vmax = 15.0
    data_max = max(abs(matrix.min()), abs(matrix.max()))
    print(f"Debug Panel C: Data range = {matrix.min():.2f}pp to {matrix.max():.2f}pp (abs max = {data_max:.2f}pp), Using vmax = ±{vmax:.0f}pp")

    # Create diverging colormap (blue=negative/worse, red=positive/better)
    cmap = plt.colormaps.get_cmap('RdBu_r')  # Red for positive (Regional better), Blue for negative
    norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    # Plot heatmap
    im = ax.imshow(matrix, cmap=cmap, norm=norm, aspect='auto')

    # Add cell annotations (now showing all low/mid/high values explicitly)
    for i in range(n_countries):
        for j in range(n_cols):
            val = matrix[i, j]

            # Adjust text color based on background
            text_color = 'white' if abs(val) > vmax * 0.5 else 'black'
            weight = 'bold' if abs(val) > significant_threshold else 'normal'

            # Format text (handle NaN/inf values)
            if np.isnan(val) or np.isinf(val):
                text = '-'
            elif abs(val) < 0.01:
                text = '0'
            else:
                text = f'{val:.1f}'

            ax.text(j, i, text, ha='center', va='center',
                   color=text_color, fontsize=11, weight=weight)

    # Column labels: Low, Mid, High (repeated for each scenario)
    column_labels = ['Low', 'Mid', 'High', 'Low', 'Mid', 'High']

    # Set ticks and labels
    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_countries))
    ax.set_xticklabels(column_labels, fontsize=11)
    ax.set_yticklabels(countries_sorted, fontsize=11)

    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=0, ha='center')

    # Add secondary x-axis labels for scenario groups
    ax_top = ax.secondary_xaxis('top')
    ax_top.set_xticks([1, 4])  # Centers of the two scenario groups (0-2 for Prec_C, 3-5 for Prec_U)
    ax_top.set_xticklabels(['Precursor C', 'Precursor U'], fontsize=11, fontweight='bold')
    ax_top.tick_params(length=0)

    # Add colorbar
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.1)
    cbar = plt.colorbar(im, cax=cax)
    cbar.set_label('Regional - National\n(percentage points)', fontsize=10, rotation=270, labelpad=15)
    cbar.ax.tick_params(labelsize=10)

    # Title
    ax.set_title(title, fontsize=12, fontweight='bold', pad=25)  # Increased pad for secondary axis

    # Grid lines between cells
    ax.set_xticks(np.arange(n_cols + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(n_countries + 1) - 0.5, minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)
    ax.tick_params(which='minor', size=0)

    # Add visual separator between scenario groups (after column 2, which is index 2.5)
    ax.axvline(2.5, color='black', linestyle='-', linewidth=2, zorder=10)

    return im


def plot_stacked_revenue_panel(ax, data, stack_order, colors, title, xlabel='Revenue (Billion USD)'):
    """
    Plot a single panel with horizontal stacked bars and error bars for revenue data

    Args:
        ax: Matplotlib axis
        data: Nested dict [scenario_label][demand][stack_category] = value (in USD)
        stack_order: List of categories for stacking (left to right)
        colors: Dict mapping stack_category to color
        title: Panel title
        xlabel: X-axis label
    """
    n_bars = len(SCENARIO_CONFIG)
    y_positions = np.arange(n_bars, dtype=float)

    # Add gaps: after Baseline, and between BAU and Precursor
    baseline_gap = 0.6
    bau_precursor_gap = 0.8

    # Shift BAU bars down (after baseline)
    y_positions[1:] += baseline_gap
    # Shift Precursor bars down further (after BAU)
    y_positions[3:] += bau_precursor_gap

    bar_height = 0.7

    # For each bar, stack the components
    for i, (goal, policy, constraint, label) in enumerate(SCENARIO_CONFIG):
        # Get mid-demand values for bar widths (convert to Billion USD)
        mid_values = {k: v / 1e9 for k, v in data[label]['mid'].items()}
        low_values = {k: v / 1e9 for k, v in data[label]['low'].items()}
        high_values = {k: v / 1e9 for k, v in data[label]['high'].items()}

        # Calculate stacked positions
        left = 0
        segment_widths = []

        for category in stack_order:
            width_mid = mid_values.get(category, 0)
            width_low = low_values.get(category, 0)
            width_high = high_values.get(category, 0)

            segment_widths.append({
                'category': category,
                'mid': width_mid,
                'low': width_low,
                'high': width_high,
                'left': left
            })

            # Plot segment (horizontal bar)
            color = colors.get(category, '#999999')
            # Only apply hatching for non-baseline scenarios with constraints
            hatch = '////' if (constraint == 'constrained' and goal != 'baseline') else None

            ax.barh(y_positions[i], width_mid,
                    height=bar_height,
                    left=left,
                    color=color,
                    edgecolor='black',
                    linewidth=0.8,
                    hatch=hatch,
                    alpha=0.9)

            left += width_mid

        # Add error bar to right end of stack
        total_mid = sum(seg['mid'] for seg in segment_widths)
        total_low = sum(seg['low'] for seg in segment_widths)
        total_high = sum(seg['high'] for seg in segment_widths)

        # Error bar: asymmetric (ensure non-negative)
        xerr_lower = max(0, total_mid - total_low)
        xerr_upper = max(0, total_high - total_mid)

        # Only plot error bar if there's actual variance
        if xerr_lower > 0 or xerr_upper > 0:
            ax.errorbar(total_mid, y_positions[i],
                       xerr=[[xerr_lower], [xerr_upper]],
                       fmt='none',
                       ecolor='black',
                       elinewidth=1.5,
                       capsize=4,
                       capthick=1.5,
                       zorder=10)

    # Formatting
    ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_yticks(y_positions)
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)  # Only vertical grid lines
    ax.yaxis.grid(False)  # Explicitly disable y-axis grid
    ax.set_axisbelow(True)
    ax.invert_yaxis()  # Put first bar at top

    # Add horizontal lines to separate Baseline, BAU, and Precursor
    baseline_separator_y = (y_positions[0] + y_positions[1]) / 2
    bau_precursor_separator_y = (y_positions[2] + y_positions[3]) / 2

    ax.axhline(baseline_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(bau_precursor_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    return y_positions


def plot_gdp_share_panel(ax, data, title, xlabel='Revenue as % of GDP'):
    """
    Plot GDP share panel with simple bars and error bars (not stacked)

    Args:
        ax: Matplotlib axis
        data: Nested dict [scenario_label][demand] = gdp_share_percentage
        title: Panel title
        xlabel: X-axis label
    """
    n_bars = len(SCENARIO_CONFIG)
    y_positions = np.arange(n_bars, dtype=float)

    # Add gaps: after Baseline, and between BAU and Precursor
    baseline_gap = 0.6
    bau_precursor_gap = 0.8

    # Shift BAU bars down (after baseline)
    y_positions[1:] += baseline_gap
    # Shift Precursor bars down further (after BAU)
    y_positions[3:] += bau_precursor_gap

    bar_height = 0.7

    # Plot simple bars (not stacked)
    for i, (goal, policy, constraint, label) in enumerate(SCENARIO_CONFIG):
        # Get mid-demand values for bar width
        value_mid = data[label]['mid']
        value_low = data[label]['low']
        value_high = data[label]['high']

        # Plot bar
        # Use a neutral color (could customize later)
        color = '#377eb8'  # Blue
        hatch = '////' if (constraint == 'constrained' and goal != 'baseline') else None

        ax.barh(y_positions[i], value_mid,
                height=bar_height,
                color=color,
                edgecolor='black',
                linewidth=0.8,
                hatch=hatch,
                alpha=0.9)

        # Add error bar
        xerr_lower = max(0, value_mid - value_low)
        xerr_upper = max(0, value_high - value_mid)

        # Only plot error bar if there's actual variance
        if xerr_lower > 0 or xerr_upper > 0:
            ax.errorbar(value_mid, y_positions[i],
                       xerr=[[xerr_lower], [xerr_upper]],
                       fmt='none',
                       ecolor='black',
                       elinewidth=1.5,
                       capsize=4,
                       capthick=1.5,
                       zorder=10)

    # Formatting
    ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_yticks(y_positions)
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)  # Only vertical grid lines
    ax.yaxis.grid(False)  # Explicitly disable y-axis grid
    ax.set_axisbelow(True)
    ax.invert_yaxis()  # Put first bar at top

    # Add horizontal lines to separate Baseline, BAU, and Precursor
    baseline_separator_y = (y_positions[0] + y_positions[1]) / 2
    bau_precursor_separator_y = (y_positions[2] + y_positions[3]) / 2

    ax.axhline(baseline_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(bau_precursor_separator_y, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    return y_positions


def create_comprehensive_legend(fig, ax_revenue_mineral, ax_revenue_processing, ax_gdp_share, ax_cost_mineral, ax_cost_breakdown):
    """
    Create a comprehensive legend for all five panels, positioned outside plot area

    Args:
        fig: Figure object
        ax_revenue_mineral: Panel A (revenue by mineral)
        ax_revenue_processing: Panel B (revenue by processing type)
        ax_gdp_share: Panel C (GDP share)
        ax_cost_mineral: Panel D (cost by mineral)
        ax_cost_breakdown: Panel E (cost breakdown by type)
    """
    # Mineral legend
    mineral_patches = []
    for mineral in MINERAL_ORDER:
        color = reference_mineral_colormap.get(mineral, '#999999')
        label = mineral.capitalize()
        patch = mpatches.Patch(facecolor=color, label=label, edgecolor='black', linewidth=0.8)
        mineral_patches.append(patch)

    # Processing Types legend
    processing_patches = []
    for ptype in PROCESSING_ORDER:
        color = PROCESSING_TYPE_COLORS.get(ptype, '#999999')
        patch = mpatches.Patch(facecolor=color, label=ptype, edgecolor='black', linewidth=0.8)
        processing_patches.append(patch)

    # Cost type legend (for Panel E)
    cost_type_patches = []
    for cost_type in COST_TYPE_ORDER:
        color = COST_TYPE_COLORS.get(cost_type, '#999999')
        patch = mpatches.Patch(facecolor=color, label=cost_type, edgecolor='black', linewidth=0.8)
        cost_type_patches.append(patch)

    # Constraint patterns
    constraint_patches = [
        mpatches.Patch(facecolor='white', hatch='////', edgecolor='black',
                      label='Constrained'),
        mpatches.Patch(facecolor='white', edgecolor='black',
                      label='Unconstrained')
    ]

    # Error bar explanation
    error_patch = mpatches.Patch(facecolor='none', edgecolor='none',
                                 label='Error bars: Low-High demand')

    # Create legends positioned OUTSIDE the plot area (bbox_to_anchor)
    # Top panel: Minerals
    legend_mineral = ax_revenue_mineral.legend(handles=mineral_patches,
                                              title='Minerals',
                                              bbox_to_anchor=(1.02, 1),
                                              loc='upper left',
                                              fontsize=8,
                                              title_fontsize=9,
                                              framealpha=0.98,
                                              edgecolor='black',
                                              ncol=1)

    # Middle panel: Processing Types
    legend_processing = ax_revenue_processing.legend(handles=processing_patches,
                                                     title='Processing Types',
                                                     bbox_to_anchor=(1.02, 1),
                                                     loc='upper left',
                                                     fontsize=8,
                                                     title_fontsize=9,
                                                     framealpha=0.98,
                                                     edgecolor='black')

    # Panel C: (no specific legend, just uses constraint below)

    # Panel D: (uses same mineral legend as Panel A, no need to add)

    # Panel E: Cost components
    legend_cost_types = ax_cost_breakdown.legend(handles=cost_type_patches,
                                                 title='Cost Components',
                                                 bbox_to_anchor=(1.02, 1),
                                                 loc='upper left',
                                                 fontsize=8,
                                                 title_fontsize=9,
                                                 framealpha=0.98,
                                                 edgecolor='black')

    # Bottom panel: Constraint info (positioned lower)
    legend_constraint = ax_cost_breakdown.legend(handles=constraint_patches + [error_patch],
                                                title='Constraint &\nUncertainty',
                                                bbox_to_anchor=(1.02, 0.5),
                                                loc='upper left',
                                                fontsize=8,
                                                title_fontsize=9,
                                                framealpha=0.98,
                                                edgecolor='black')

    # matplotlib only keeps the last legend, so add the others back
    ax_revenue_mineral.add_artist(legend_mineral)
    ax_revenue_processing.add_artist(legend_processing)
    ax_cost_breakdown.add_artist(legend_cost_types)


def plot_competitiveness_panel(ax, df):
    """
    Plot Panel F: Competitiveness matrix (2 side-by-side heatmaps)

    Shows Precursor Unconstrained scenarios:
    - Left: National (country_unconstrained)
    - Right: Regional (region_unconstrained)

    Args:
        ax: Matplotlib axis for Panel F
        df: Main data DataFrame
    """
    # Clear the axis and turn off its frame (we'll add subplots inside)
    ax.axis('off')

    # Get position of the axis to create sub-gridspec
    bbox = ax.get_position()

    # Create a sub-gridspec within Panel F for 2 side-by-side matrices
    # Regional U wider to compensate for colorbar so both heatmaps have same dimensions
    from matplotlib.gridspec import GridSpecFromSubplotSpec
    gs_comp = GridSpecFromSubplotSpec(1, 2, subplot_spec=ax.get_subplotspec(),
                                      wspace=0.30, hspace=0,
                                      width_ratios=[1, 1.25])  # Regional U wider for colorbar compensation

    # Create the two subplot axes
    ax_national = ax.figure.add_subplot(gs_comp[0, 0])
    ax_regional = ax.figure.add_subplot(gs_comp[0, 1])

    # Scenario configuration
    scenario_key = 'precursor_2040'
    scenario_config = COMP_SCENARIO_CONFIG[scenario_key]

    # First, collect all countries across both scenarios to ensure consistency
    all_countries = set()
    scenarios = [
        ('country_unconstrained', 'National U'),
        ('region_unconstrained', 'Regional U'),
    ]

    for constraint, _ in scenarios:
        cost_df = extract_cumulative_costs(df, scenario_key, constraint, scenario_config)
        if not cost_df.empty:
            all_countries.update(cost_df['iso3'].unique())

    # Sort countries alphabetically for consistent ordering
    all_countries = sorted(all_countries)

    # Extract data for both scenarios with consistent country list
    scenarios_to_plot = [
        ('country_unconstrained', ax_national, 'National U', True, False),
        ('region_unconstrained', ax_regional, 'Regional U', False, True),
    ]

    for constraint, ax_sub, title, show_ylabel, show_cbar in scenarios_to_plot:
        # Extract cumulative costs
        cost_df = extract_cumulative_costs(df, scenario_key, constraint, scenario_config)

        if cost_df.empty:
            ax_sub.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax_sub.transAxes)
            continue

        # Calculate rankings
        cost_df = calculate_quintile_ranks(cost_df)

        # Create matrices using ALL countries (not just those with data)
        cost_matrix, quintile_matrix, rank_matrix = create_heatmap_matrix(cost_df, all_countries)

        # Create annotations
        annot = np.empty(cost_matrix.shape, dtype=object)
        for i in range(cost_matrix.shape[0]):
            for j in range(cost_matrix.shape[1]):
                cost = cost_matrix.iloc[i, j]
                rank = rank_matrix.iloc[i, j]
                annot[i, j] = format_cost_annotation(cost, rank)

        # Plot heatmap
        cmap = 'Greens_r'
        cbar_kws = {'label': 'Quintile\n(Darker=Better)'} if show_cbar else None

        sns.heatmap(
            quintile_matrix,
            annot=annot,
            fmt='',
            cmap=cmap,
            vmin=1,
            vmax=5,
            cbar_kws=cbar_kws,
            ax=ax_sub,
            linewidths=0.5,
            linecolor='gray',
            square=False,
            annot_kws={'fontsize': 8, 'va': 'center'},
            cbar=show_cbar,
            mask=quintile_matrix.isna()
        )

        # Formatting
        ax_sub.set_title(title, fontsize=12, fontweight='bold', pad=8)
        ax_sub.set_xlabel('Mineral', fontsize=11)
        if show_ylabel:
            ax_sub.set_ylabel('Country', fontsize=11)
        else:
            ax_sub.set_ylabel('')

        ax_sub.set_yticklabels(ax_sub.get_yticklabels(), rotation=0, fontsize=9)
        # Use abbreviated mineral names to avoid overlap
        mineral_abbrev = {'copper': 'Cu', 'cobalt': 'Co', 'nickel': 'Ni',
                          'manganese': 'Mn', 'lithium': 'Li', 'graphite': 'Gr'}
        ax_sub.set_xticklabels([mineral_abbrev.get(m, m[:2]) for m in COMP_MINERAL_ORDER],
                               rotation=0, ha='center', fontsize=9)

    # Add Panel F label above the heatmaps using figure coordinates
    # Position it at the top-left of the Panel F area with sufficient clearance
    fig_bbox = ax.get_position()
    ax.figure.text(fig_bbox.x0-.003, fig_bbox.y1 + 0.03,
                   'F) Competitiveness for Precursor U',
                   fontsize=12, fontweight='bold',
                   va='bottom', ha='left')


def create_economic_indicators_figure(df, output_dir):
    """
    Generate complete economic indicators comparison figure

    Args:
        df: Main data DataFrame
        output_dir: Output directory for figure

    Returns:
        List of saved file paths
    """
    print("  Generating economic indicators five-panel figure...")

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Prepare data
    revenue_mineral_data, revenue_processing_data, gdp_share_data, cost_mineral_data, cost_breakdown_data = prepare_economic_data(df)

    # Prepare country-level GDP data for heatmap
    country_gdp_data = prepare_country_gdp_data(df)
    difference_data, countries_sorted = calculate_gdp_difference_matrix(country_gdp_data)

    # Create figure with nested GridSpecs for independent row width control
    fig = plt.figure(figsize=(17, 17))

    # Main GridSpec: 3 rows × 1 column (controls vertical layout only)
    main_gs = fig.add_gridspec(3, 1,
                               height_ratios=[1, 1, 1.9],  # Row 3 significantly taller for heatmaps
                               hspace=0.30,
                               left=0.08, right=0.95, top=0.94, bottom=0.10)  # Increased for Panel F x-axis labels

    # Row 1: Panels A & B with equal widths (50/50)
    row1_gs = main_gs[0].subgridspec(1, 2, wspace=0.45)
    ax_rev_mineral = fig.add_subplot(row1_gs[0, 0])
    ax_cost_mineral = fig.add_subplot(row1_gs[0, 1])

    # Row 2: Panels D & E with equal widths (50/50)
    row2_gs = main_gs[1].subgridspec(1, 2, wspace=0.45)
    ax_rev_processing = fig.add_subplot(row2_gs[0, 0])
    ax_cost_breakdown = fig.add_subplot(row2_gs[0, 1])

    # Row 3: Panels C & F with custom widths (Panel C narrower, Panel F wider for mineral names)
    row3_gs = main_gs[2].subgridspec(1, 2, wspace=0.35, width_ratios=[0.7, 1.3])
    ax_gdp = fig.add_subplot(row3_gs[0, 0])
    ax_competitiveness = fig.add_subplot(row3_gs[0, 1])

    # Plot Top Panel (Revenue by Mineral)
    y_positions = plot_stacked_revenue_panel(
        ax_rev_mineral, revenue_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='A) Export Revenue by Mineral',
        xlabel='Revenue (Billion USD)'
    )

    # Plot Middle Panel (Revenue by Processing Type)
    plot_stacked_revenue_panel(
        ax_rev_processing, revenue_processing_data,
        stack_order=PROCESSING_ORDER,
        colors=PROCESSING_TYPE_COLORS,
        title='B) Export Revenue by Processing Type',
        xlabel='Revenue (Billion USD)'
    )

    # Plot Panel C (GDP Share - HEATMAP showing Regional vs National impact)
    plot_gdp_difference_heatmap(
        ax_gdp, difference_data, countries_sorted,
        title='C) Revenue as Share of GDP - Regional vs National',
        significant_threshold=2.0  # Mark changes > 2 percentage points as significant
    )

    # Plot Panel D (Cost by Mineral)
    plot_stacked_revenue_panel(
        ax_cost_mineral, cost_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='D) Total Cost by Mineral',
        xlabel='Cost (Billion USD)'
    )

    # Plot Panel E (Total Cost by Component)
    plot_stacked_revenue_panel(
        ax_cost_breakdown, cost_breakdown_data,
        stack_order=COST_TYPE_ORDER,
        colors=COST_TYPE_COLORS,
        title='E) Total Cost by Component',
        xlabel='Cost (Billion USD)'
    )

    # Plot Panel F (Competitiveness Matrix for Precursor Unconstrained)
    plot_competitiveness_panel(ax_competitiveness, df)

    # Ensure consistent x-axis limits for all revenue and cost panels
    # Get the maximum xlim across all four panels (A, B, D, E)
    max_xlim = max(
        ax_rev_mineral.get_xlim()[1],
        ax_rev_processing.get_xlim()[1],
        ax_cost_mineral.get_xlim()[1],
        ax_cost_breakdown.get_xlim()[1]
    )
    # Apply the same limit to all panels
    ax_rev_mineral.set_xlim(0, max_xlim)
    ax_rev_processing.set_xlim(0, max_xlim)
    ax_cost_mineral.set_xlim(0, max_xlim)
    ax_cost_breakdown.set_xlim(0, max_xlim)

    # Set y-axis labels (scenario names on left) for bar chart panels
    y_labels = [label for _, _, _, label in SCENARIO_CONFIG]
    ax_rev_mineral.set_yticklabels(y_labels, fontsize=9)
    ax_rev_processing.set_yticklabels(y_labels, fontsize=9)
    # ax_gdp has its own country labels (heatmap)
    ax_cost_mineral.set_yticklabels(y_labels, fontsize=9)
    ax_cost_breakdown.set_yticklabels(y_labels, fontsize=9)

    # Add overall title (y parameter controls distance from top)
    fig.suptitle('Economic Indicators',
                #  + '(Mid-demand with Low-High range)',
                 fontsize=14, fontweight='bold', y=0.98)

    # Create comprehensive legend (excluding Panel F which has its own colorbar)
    create_comprehensive_legend(fig, ax_rev_mineral, ax_rev_processing, ax_gdp, ax_cost_mineral, ax_cost_breakdown)

    # Add note about BAU scenarios (below figure)
    # fig.text(0.12, 0.015,
    #          'Note: BAU scenarios have no National/Regional distinction (identical outcomes)',
    #          fontsize=7, style='italic', color='gray',
    #          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3, pad=0.3))

    # Save figure
    saved_paths = []

    # High-res PNG for publication
    png_path = os.path.join(output_dir, 'economic_indicators_six_panel.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight', facecolor='white')
    saved_paths.append(png_path)
    print(f"    ✓ Saved: {os.path.basename(png_path)}")

    # PDF for vector graphics
    pdf_path = os.path.join(output_dir, 'economic_indicators_six_panel.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    ✓ Saved: {os.path.basename(pdf_path)}")

    # Low-res PNG for quick preview
    preview_path = os.path.join(output_dir, 'economic_indicators_six_panel_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight', facecolor='white')
    saved_paths.append(preview_path)
    print(f"    ✓ Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


def create_economic_indicators_figure_net_revenue(df, output_dir):
    """
    Generate economic indicators comparison figure with NET export revenue

    Uses net export revenue (export revenue - import cost) for:
    - Panel A: Net Export Revenue by Mineral
    - Panel B: Net Export Revenue by Processing Type
    - Panel C: Net Export Revenue as Share of GDP (heatmap)

    Args:
        df: Main data DataFrame
        output_dir: Output directory for figure

    Returns:
        List of saved file paths
    """
    print("  Generating economic indicators five-panel figure (with net export revenue)...")

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Prepare data - use NET export revenue for Panels A & B
    # Get gross revenue data for cost panels (D, E) which don't change
    _, _, gdp_share_data, cost_mineral_data, cost_breakdown_data = prepare_economic_data(df)

    # Get NET export revenue data for Panels A & B
    net_revenue_mineral_data, net_revenue_processing_data = prepare_net_export_revenue_data(df)

    # Prepare country-level NET export revenue GDP data for heatmap (Panel C)
    country_gdp_data = prepare_country_net_export_revenue_gdp_data(df)
    difference_data, countries_sorted = calculate_gdp_difference_matrix(country_gdp_data)

    # Create figure with nested GridSpecs for independent row width control
    fig = plt.figure(figsize=(17, 17))

    # Main GridSpec: 3 rows × 1 column (controls vertical layout only)
    main_gs = fig.add_gridspec(3, 1,
                               height_ratios=[1, 1, 1.9],  # Row 3 significantly taller for heatmaps
                               hspace=0.30,
                               left=0.08, right=0.95, top=0.94, bottom=0.10)  # Increased for Panel F x-axis labels

    # Row 1: Panels A & B with equal widths (50/50)
    row1_gs = main_gs[0].subgridspec(1, 2, wspace=0.45)
    ax_rev_mineral = fig.add_subplot(row1_gs[0, 0])
    ax_cost_mineral = fig.add_subplot(row1_gs[0, 1])

    # Row 2: Panels D & E with equal widths (50/50)
    row2_gs = main_gs[1].subgridspec(1, 2, wspace=0.45)
    ax_rev_processing = fig.add_subplot(row2_gs[0, 0])
    ax_cost_breakdown = fig.add_subplot(row2_gs[0, 1])

    # Row 3: Panels C & F with custom widths (Panel C narrower, Panel F wider for mineral names)
    row3_gs = main_gs[2].subgridspec(1, 2, wspace=0.35, width_ratios=[0.7, 1.3])
    ax_gdp = fig.add_subplot(row3_gs[0, 0])
    ax_competitiveness = fig.add_subplot(row3_gs[0, 1])

    # Plot Top Panel (NET Revenue by Mineral) - using net export revenue data
    y_positions = plot_stacked_revenue_panel(
        ax_rev_mineral, net_revenue_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='A) Net Export Revenue by Mineral',
        xlabel='Net Revenue (Billion USD)'
    )

    # Plot Middle Panel (NET Revenue by Processing Type) - using net export revenue data
    plot_stacked_revenue_panel(
        ax_rev_processing, net_revenue_processing_data,
        stack_order=PROCESSING_ORDER,
        colors=PROCESSING_TYPE_COLORS,
        title='B) Net Export Revenue by Processing Type',
        xlabel='Net Revenue (Billion USD)'
    )

    # Plot Panel C (NET Export Revenue GDP Share - HEATMAP showing Regional vs National impact)
    plot_gdp_difference_heatmap(
        ax_gdp, difference_data, countries_sorted,
        title='C) Net Export Revenue as Share of GDP - Regional vs National',
        significant_threshold=2.0  # Mark changes > 2 percentage points as significant
    )

    # Plot Panel D (Cost by Mineral)
    plot_stacked_revenue_panel(
        ax_cost_mineral, cost_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='D) Total Cost by Mineral',
        xlabel='Cost (Billion USD)'
    )

    # Plot Panel E (Total Cost by Component)
    plot_stacked_revenue_panel(
        ax_cost_breakdown, cost_breakdown_data,
        stack_order=COST_TYPE_ORDER,
        colors=COST_TYPE_COLORS,
        title='E) Total Cost by Component',
        xlabel='Cost (Billion USD)'
    )

    # Plot Panel F (Competitiveness Matrix for Precursor Unconstrained)
    plot_competitiveness_panel(ax_competitiveness, df)

    # Ensure consistent x-axis limits for all revenue and cost panels
    # Get the maximum xlim across all four panels (A, B, D, E)
    max_xlim = max(
        ax_rev_mineral.get_xlim()[1],
        ax_rev_processing.get_xlim()[1],
        ax_cost_mineral.get_xlim()[1],
        ax_cost_breakdown.get_xlim()[1]
    )
    # Apply the same limit to all panels
    ax_rev_mineral.set_xlim(0, max_xlim)
    ax_rev_processing.set_xlim(0, max_xlim)
    ax_cost_mineral.set_xlim(0, max_xlim)
    ax_cost_breakdown.set_xlim(0, max_xlim)

    # Set y-axis labels (scenario names on left) for bar chart panels
    y_labels = [label for _, _, _, label in SCENARIO_CONFIG]
    ax_rev_mineral.set_yticklabels(y_labels, fontsize=9)
    ax_rev_processing.set_yticklabels(y_labels, fontsize=9)
    # ax_gdp has its own country labels (heatmap)
    ax_cost_mineral.set_yticklabels(y_labels, fontsize=9)
    ax_cost_breakdown.set_yticklabels(y_labels, fontsize=9)

    # Add overall title (y parameter controls distance from top)
    fig.suptitle('Economic Indicators',
                #  + '(Mid-demand with Low-High range)',
                 fontsize=14, fontweight='bold', y=0.98)

    # Create comprehensive legend (excluding Panel F which has its own colorbar)
    create_comprehensive_legend(fig, ax_rev_mineral, ax_rev_processing, ax_gdp, ax_cost_mineral, ax_cost_breakdown)

    # Save figure
    saved_paths = []

    # High-res PNG for publication
    png_path = os.path.join(output_dir, 'economic_indicators_six_panel_net_revenue.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight', facecolor='white')
    saved_paths.append(png_path)
    print(f"    ✓ Saved: {os.path.basename(png_path)}")

    # PDF for vector graphics
    pdf_path = os.path.join(output_dir, 'economic_indicators_six_panel_net_revenue.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    ✓ Saved: {os.path.basename(pdf_path)}")

    # Low-res PNG for quick preview
    preview_path = os.path.join(output_dir, 'economic_indicators_six_panel_net_revenue_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight', facecolor='white')
    saved_paths.append(preview_path)
    print(f"    ✓ Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


def generate_economic_indicators_figures(df, output_dir):
    """
    Main entry point for generating economic indicators figures

    Args:
        df: Main data DataFrame
        output_dir: Output directory

    Returns:
        List of saved file paths
    """
    # Generate main six-panel figure (with gross export revenue)
    saved_paths = create_economic_indicators_figure(df, output_dir)

    # Generate six-panel figure with net export revenue
    net_revenue_paths = create_economic_indicators_figure_net_revenue(df, output_dir)
    saved_paths.extend(net_revenue_paths)

    # Generate SI GDP heatmaps
    try:
        from publication_analysis.figure_gdp_share_heatmaps_SI import generate_gdp_heatmaps_SI
        si_paths = generate_gdp_heatmaps_SI(df, output_dir)
        saved_paths.extend(si_paths)
    except Exception as e:
        print(f"    ⚠ Could not generate SI GDP heatmaps: {e}")

    # Generate SI competitiveness matrices
    try:
        from publication_analysis.figure_competitiveness_SI import generate_competitiveness_matrices_SI
        comp_paths = generate_competitiveness_matrices_SI(df, output_dir)
        saved_paths.extend(comp_paths)
    except Exception as e:
        print(f"    ⚠ Could not generate SI competitiveness matrices: {e}")

    return saved_paths


if __name__ == '__main__':
    """Test the figure generation"""
    import json

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load data
    data_file = os.path.join(config['paths']['results'], 'all_data.xlsx')
    df = pd.read_excel(data_file, index_col=[0,1,2,3,4]).reset_index()

    # Create output directory (match run_all_figures.py path structure with automated_plots)
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'publication', 'economic_indicators')
    os.makedirs(output_dir, exist_ok=True)

    # Generate figure
    print("Testing economic indicators figure generation...")
    paths = generate_economic_indicators_figures(df, output_dir)
    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
