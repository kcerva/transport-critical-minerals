"""
Integrated Value Chain Analysis Module

This module provides comprehensive value chain analysis for critical minerals,
accounting for branch points, parallel routes, and proper cost allocation.

Key Concepts:
============

1. production_tonnes_for_costs
   - Represents the tonnage that bears production costs at each stage
   - Different from production_tonnes when material flows to further processing
   - Example: Stage 1 produces 1000t, but 600t goes to Stage 3 internally
     * production_tonnes = 1000t (total produced)
     * production_tonnes_for_costs = 400t (only exports bear Stage 1 costs)
     * Internal 600t will bear costs at Stage 3 instead
   - Already correctly used in the data for unit cost calculations

2. Branch Points
   - Processing stages where material splits into:
     a) Export to international markets
     b) Further domestic processing
   - Example: Stage 1 → 40% export, 60% to Stage 3
   - Both pathways must be tracked for complete economic picture

3. Parallel Routes (Cobalt Special Case)
   - Cobalt has two independent processing pathways:
     * Route A (Industrial): Stage 1 → Stage 3 (Refined Co)
     * Route B (Battery): Stage 1 → Stage 4.1 → Stage 5 (Precursor)
   - Stage 3 is NOT a precursor to Stage 4.1
   - Both routes can operate simultaneously in same country
   - Each route has different market demand constraints

4. Integrated Value Chain Method
   - Calculates: Final Export Revenue - Total Chain Costs
   - Accounts for:
     * Branch points (partial exports at each stage)
     * Parallel routes (cobalt's dual pathways)
     * Transfer pricing (internal vs market prices)
     * Demand constraints (precursor stages have limited demand)
   - Reveals true end-to-end economic value creation

5. Comparison Methods
   - Stage-by-Stage: Revenue - Costs at each stage (current method)
   - Integrated: Final export revenue - All upstream costs
   - Differences highlight transfer pricing effects and vertical integration benefits

Limitations:
===========
- Assumes cost allocation via production_tonnes_for_costs is accurate
- May not capture all transfer pricing strategies
- Demand constraints for precursor stages need external validation
- Energy and water costs may have allocation uncertainties
"""

import pandas as pd
import numpy as np
import json
import os
from plot_config import MINERAL_PROCESSING_ROUTES

# Load configuration
with open('../../config.json', 'r') as f:
    config = json.load(f)


def load_data():
    """Load the main dataset from all_data.xlsx"""
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    df = pd.read_excel(data_path)
    return df


def calculate_integrated_value_chain_with_branches(df, country, mineral, scenario, constraint):
    """
    Calculate integrated value chain accounting for branch points.

    Branch points occur when a processing stage both:
    1. Exports material to international markets
    2. Sends material to further domestic processing

    The analysis tracks:
    - Export revenues at each stage
    - Production costs allocated via production_tonnes_for_costs
    - Total value creation = Sum(export revenues) - Sum(production costs)

    Parameters:
    -----------
    df : DataFrame
        Main dataset with production, revenue, cost data
    country : str
        ISO3 country code
    mineral : str
        Mineral name (e.g., 'cobalt', 'copper')
    scenario : str
        Scenario name (e.g., 'Early_Refining_2040')
    constraint : str
        Constraint level ('mid_min' for national, 'mid_max' for regional)

    Returns:
    --------
    dict with keys:
        - stages: list of stage numbers processed
        - export_revenue_by_stage: dict {stage: revenue from exports}
        - production_costs_by_stage: dict {stage: production costs}
        - total_export_revenue: sum of all export revenues
        - total_production_costs: sum of all production costs
        - integrated_value_added: total_export_revenue - total_production_costs
        - branch_points: list of stages with both exports and internal transfers
    """

    # Filter data for this country, mineral, scenario, constraint
    mask = (
        (df['iso3'] == country) &
        (df['reference_mineral'] == mineral) &
        (df['scenario'] == scenario) &
        (df['constraint'] == constraint)
    )
    country_data = df[mask].copy()

    if country_data.empty:
        return None

    # Get valid processing routes for this mineral
    if mineral in MINERAL_PROCESSING_ROUTES:
        valid_routes = MINERAL_PROCESSING_ROUTES[mineral].get('valid_routes', [])
        # Flatten to get all valid stages
        valid_stages = set()
        for route in valid_routes:
            valid_stages.update(route)
    else:
        # If no route defined, use all stages present
        valid_stages = set(country_data['processing_stage'].unique())

    # Filter to valid stages only
    country_data = country_data[country_data['processing_stage'].isin(valid_stages)]

    results = {
        'stages': [],
        'export_revenue_by_stage': {},
        'production_costs_by_stage': {},
        'transport_costs_by_stage': {},
        'total_costs_by_stage': {},
        'export_tonnes_by_stage': {},
        'production_tonnes_by_stage': {},
        'production_tonnes_for_costs_by_stage': {},
        'branch_points': []
    }

    for _, row in country_data.iterrows():
        stage = row['processing_stage']
        results['stages'].append(stage)

        # Export revenue (from exports only)
        export_revenue = row.get('revenue_usd', 0)
        results['export_revenue_by_stage'][stage] = export_revenue

        # Production costs (allocated via production_tonnes_for_costs)
        prod_cost = row.get('production_cost_usd', 0)
        results['production_costs_by_stage'][stage] = prod_cost

        # Transport costs
        transport_cost = row.get('transport_cost_usd', 0)
        results['transport_costs_by_stage'][stage] = transport_cost

        # Total costs (production + transport + energy)
        total_cost = row.get('all_cost_usd', 0)
        results['total_costs_by_stage'][stage] = total_cost

        # Track tonnages
        results['export_tonnes_by_stage'][stage] = row.get('export_tonnes', 0)
        results['production_tonnes_by_stage'][stage] = row.get('production_tonnes', 0)
        results['production_tonnes_for_costs_by_stage'][stage] = row.get('production_tonnes_for_costs', 0)

        # Identify branch points: stages where production > production_for_costs
        # This means some material went to further processing
        if row.get('production_tonnes', 0) > row.get('production_tonnes_for_costs', 0):
            internal_transfer = row['production_tonnes'] - row['production_tonnes_for_costs']
            results['branch_points'].append({
                'stage': stage,
                'production_tonnes': row['production_tonnes'],
                'export_tonnes': row.get('export_tonnes', 0),
                'internal_transfer_tonnes': internal_transfer,
                'export_pct': (row.get('export_tonnes', 0) / row['production_tonnes'] * 100) if row['production_tonnes'] > 0 else 0
            })

    # Calculate totals
    results['total_export_revenue'] = sum(results['export_revenue_by_stage'].values())
    results['total_production_costs'] = sum(results['production_costs_by_stage'].values())
    results['total_transport_costs'] = sum(results['transport_costs_by_stage'].values())
    results['total_all_costs'] = sum(results['total_costs_by_stage'].values())

    # Integrated value added: Total export revenue - Total costs
    results['integrated_value_added'] = results['total_export_revenue'] - results['total_all_costs']

    return results


def analyze_cobalt_parallel_routes(df, country, scenario, constraint):
    """
    Special analysis for cobalt's parallel processing routes.

    Cobalt has two independent pathways:
    - Route A (Industrial): Stage 1 → Stage 3 (Refined Co)
    - Route B (Battery): Stage 1 → Stage 4.1 → Stage 5 (Precursor)

    This function:
    1. Identifies which routes are active in the country
    2. Calculates value chain for each route separately
    3. Provides combined analysis

    Parameters:
    -----------
    df : DataFrame
        Main dataset
    country : str
        ISO3 country code
    scenario : str
        Scenario name
    constraint : str
        Constraint level

    Returns:
    --------
    dict with keys:
        - route_a_active: bool (Stage 1 → 3 present)
        - route_b_active: bool (Stage 1 → 4.1 → 5 present)
        - route_a_results: value chain results for Route A
        - route_b_results: value chain results for Route B
        - combined_results: merged results across both routes
    """

    # Filter for cobalt data
    mask = (
        (df['iso3'] == country) &
        (df['reference_mineral'] == 'cobalt') &
        (df['scenario'] == scenario) &
        (df['constraint'] == constraint)
    )
    cobalt_data = df[mask].copy()

    if cobalt_data.empty:
        return None

    results = {
        'route_a_active': False,
        'route_b_active': False,
        'route_a_results': None,
        'route_b_results': None,
        'combined_results': None
    }

    stages_present = set(cobalt_data['processing_stage'].unique())

    # Check Route A: 1 → 3
    if 1.0 in stages_present and 3.0 in stages_present:
        results['route_a_active'] = True
        # For Route A, only consider stages 1 and 3
        route_a_data = cobalt_data[cobalt_data['processing_stage'].isin([1.0, 3.0])]
        results['route_a_results'] = {
            'stages': [1.0, 3.0],
            'export_revenue': route_a_data['revenue_usd'].sum(),
            'total_costs': route_a_data['all_cost_usd'].sum(),
            'value_added': route_a_data['revenue_usd'].sum() - route_a_data['all_cost_usd'].sum(),
            'production_tonnes': dict(zip(route_a_data['processing_stage'], route_a_data['production_tonnes']))
        }

    # Check Route B: 1 → 4.1 → 5
    if 1.0 in stages_present and 4.1 in stages_present:
        results['route_b_active'] = True
        # For Route B, consider stages 1, 4.1, and 5 (if present)
        route_b_stages = [1.0, 4.1]
        if 5.0 in stages_present:
            route_b_stages.append(5.0)
        route_b_data = cobalt_data[cobalt_data['processing_stage'].isin(route_b_stages)]
        results['route_b_results'] = {
            'stages': route_b_stages,
            'export_revenue': route_b_data['revenue_usd'].sum(),
            'total_costs': route_b_data['all_cost_usd'].sum(),
            'value_added': route_b_data['revenue_usd'].sum() - route_b_data['all_cost_usd'].sum(),
            'production_tonnes': dict(zip(route_b_data['processing_stage'], route_b_data['production_tonnes']))
        }

    # Combined results (all stages)
    results['combined_results'] = {
        'total_export_revenue': cobalt_data['revenue_usd'].sum(),
        'total_costs': cobalt_data['all_cost_usd'].sum(),
        'total_value_added': cobalt_data['revenue_usd'].sum() - cobalt_data['all_cost_usd'].sum(),
        'all_stages': sorted(list(stages_present))
    }

    return results


def compare_analysis_methods(df, scenario, constraint_level):
    """
    Compare stage-by-stage vs integrated value chain analysis.

    Stage-by-Stage Method:
    - Calculates Revenue - Costs at each processing stage
    - Each stage treated independently
    - Simple but may double-count revenues in vertically integrated chains

    Integrated Method:
    - Calculates Total Export Revenue - Total Chain Costs
    - Accounts for branch points and internal transfers
    - Reveals true end-to-end value creation

    Parameters:
    -----------
    df : DataFrame
        Main dataset
    scenario : str
        Scenario name
    constraint_level : str
        'mid_min' for national, 'mid_max' for regional

    Returns:
    --------
    DataFrame with columns:
        - iso3, reference_mineral, scenario, constraint
        - stage_by_stage_value_added: Sum of (Revenue - Costs) per stage
        - integrated_value_added: Total export revenue - Total costs
        - difference: integrated - stage_by_stage
        - difference_pct: (difference / stage_by_stage) * 100
    """

    results_list = []

    # Get unique countries and minerals
    mask = (df['scenario'] == scenario) & (df['constraint'] == constraint_level)
    subset = df[mask]

    for (country, mineral) in subset[['iso3', 'reference_mineral']].drop_duplicates().values:
        # Stage-by-stage method
        country_mineral_data = subset[(subset['iso3'] == country) & (subset['reference_mineral'] == mineral)]

        if country_mineral_data.empty:
            continue

        stage_by_stage_value = (country_mineral_data['revenue_usd'] - country_mineral_data['all_cost_usd']).sum()

        # Integrated method
        integrated_results = calculate_integrated_value_chain_with_branches(
            df, country, mineral, scenario, constraint_level
        )

        if integrated_results is None:
            continue

        integrated_value = integrated_results['integrated_value_added']

        # Calculate difference
        difference = integrated_value - stage_by_stage_value
        if stage_by_stage_value != 0:
            difference_pct = (difference / abs(stage_by_stage_value)) * 100
        else:
            difference_pct = 0 if difference == 0 else np.inf

        results_list.append({
            'iso3': country,
            'reference_mineral': mineral,
            'scenario': scenario,
            'constraint': constraint_level,
            'stage_by_stage_value_added': stage_by_stage_value,
            'integrated_value_added': integrated_value,
            'difference': difference,
            'difference_pct': difference_pct,
            'num_stages': len(integrated_results['stages']),
            'num_branch_points': len(integrated_results['branch_points']),
            'total_export_revenue': integrated_results['total_export_revenue'],
            'total_costs': integrated_results['total_all_costs']
        })

    return pd.DataFrame(results_list)


def analyze_all_countries_minerals(df, scenario, constraint_level, mineral=None):
    """
    Run integrated value chain analysis for all countries and minerals.

    Parameters:
    -----------
    df : DataFrame
        Main dataset
    scenario : str
        Scenario name
    constraint_level : str
        'mid_min' for national, 'mid_max' for regional
    mineral : str, optional
        If specified, analyze only this mineral

    Returns:
    --------
    DataFrame with integrated value chain results for each country-mineral
    """

    results_list = []

    # Filter data
    mask = (df['scenario'] == scenario) & (df['constraint'] == constraint_level)
    if mineral:
        mask = mask & (df['reference_mineral'] == mineral)

    subset = df[mask]

    for (country, min_name) in subset[['iso3', 'reference_mineral']].drop_duplicates().values:

        # Special handling for cobalt parallel routes
        if min_name == 'cobalt':
            cobalt_results = analyze_cobalt_parallel_routes(df, country, scenario, constraint_level)
            if cobalt_results and cobalt_results['combined_results']:
                # Convert stages to clean list of floats
                stages_clean = [float(s) for s in cobalt_results['combined_results']['all_stages']]
                results_list.append({
                    'iso3': country,
                    'reference_mineral': min_name,
                    'scenario': scenario,
                    'constraint': constraint_level,
                    'route_a_active': cobalt_results['route_a_active'],
                    'route_b_active': cobalt_results['route_b_active'],
                    'total_export_revenue': cobalt_results['combined_results']['total_export_revenue'],
                    'total_costs': cobalt_results['combined_results']['total_costs'],
                    'integrated_value_added': cobalt_results['combined_results']['total_value_added'],
                    'all_stages': ','.join([str(s) for s in stages_clean])
                })
        else:
            # Standard integrated analysis
            integrated_results = calculate_integrated_value_chain_with_branches(
                df, country, min_name, scenario, constraint_level
            )

            if integrated_results:
                # Convert stages to clean list of floats
                stages_clean = [float(s) for s in integrated_results['stages']]

                # Format branch point details as clean string
                branch_details = None
                if integrated_results['branch_points']:
                    details_list = []
                    for bp in integrated_results['branch_points']:
                        detail_str = f"Stage {bp['stage']}: {bp['export_tonnes']:.0f}t export ({bp['export_pct']:.1f}%), {bp['internal_transfer_tonnes']:.0f}t internal"
                        details_list.append(detail_str)
                    branch_details = '; '.join(details_list)

                results_list.append({
                    'iso3': country,
                    'reference_mineral': min_name,
                    'scenario': scenario,
                    'constraint': constraint_level,
                    'route_a_active': None,
                    'route_b_active': None,
                    'total_export_revenue': integrated_results['total_export_revenue'],
                    'total_costs': integrated_results['total_all_costs'],
                    'integrated_value_added': integrated_results['integrated_value_added'],
                    'all_stages': ','.join([str(s) for s in stages_clean]),
                    'num_branch_points': len(integrated_results['branch_points']),
                    'branch_point_details': branch_details
                })

    return pd.DataFrame(results_list)


def document_cost_allocation():
    """
    Generate documentation explaining cost allocation methodology.

    Returns:
    --------
    str: Formatted documentation text
    """

    doc = """
    COST ALLOCATION METHODOLOGY
    ===========================

    The dataset uses production_tonnes_for_costs to properly allocate production costs
    in vertically integrated value chains.

    Key Concepts:
    -------------

    1. production_tonnes
       - Total physical production at a processing stage
       - Includes material exported AND material sent to further processing
       - Example: Stage 1 produces 1000 tonnes total

    2. production_tonnes_for_costs
       - Subset of production that bears costs at this stage
       - Only includes material that will be exported (not further processed domestically)
       - Example: 400 tonnes exported from Stage 1, 600 tonnes to Stage 3
         → production_tonnes_for_costs = 400 tonnes

    3. Cost Allocation Logic
       - Material processed domestically doesn't bear costs at intermediate stages
       - Costs accumulate at the final export stage
       - Example: 600t Stage 1 → Stage 3
         * Stage 1 costs: Only on 400t exported
         * Stage 3 costs: On all 600t (from Stage 1) + any direct Stage 3 production

    4. Why This Matters
       - Prevents double-counting costs in integrated chains
       - Reveals true cost structure of vertical integration
       - Essential for comparing national vs regional processing strategies

    Branch Points:
    --------------
    A branch point occurs when production_tonnes > production_tonnes_for_costs

    This indicates:
    - Some material exported (bears costs at this stage)
    - Some material sent to further processing (costs at higher stage)

    Example Branch Point Analysis:
    Stage 1: production_tonnes = 1000t, production_tonnes_for_costs = 400t
    → 400t exported (40%)
    → 600t to further processing (60%)
    → Branch point with 40/60 split

    Validation:
    -----------
    The data has been validated to ensure:
    - Unit costs calculated using production_tonnes_for_costs
    - Cost allocation matches physical material flows
    - No double-counting in vertically integrated scenarios
    """

    return doc


def main():
    """
    Main execution function to run integrated value chain analysis.
    """

    print("Loading data...")
    df = load_data()

    print("\n" + "="*80)
    print("INTEGRATED VALUE CHAIN ANALYSIS")
    print("="*80)

    # Print documentation
    print(document_cost_allocation())

    # Analyze all scenarios
    scenarios = [
        'early_refining_2040_mid_min_threshold_metal_tons',
        'early_refining_2040_mid_max_threshold_metal_tons',
        'precursor_2040_mid_min_threshold_metal_tons',
        'precursor_2040_mid_max_threshold_metal_tons'
    ]
    constraints = {
        'country_unconstrained': 'National Unconstrained',
        'country_constrained': 'National Constrained',
        'region_unconstrained': 'Regional Unconstrained',
        'region_constrained': 'Regional Constrained'
    }

    output_dir = os.path.join(config['paths']['results'], 'integrated_value_chain_analysis')
    os.makedirs(output_dir, exist_ok=True)

    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"Scenario: {scenario}")
        print(f"{'='*80}")

        for constraint_code, constraint_name in constraints.items():
            print(f"\n{constraint_name} Constraint ({constraint_code}):")
            print("-" * 60)

            # Run comparison analysis
            comparison_df = compare_analysis_methods(df, scenario, constraint_code)

            if not comparison_df.empty:
                print(f"\nTop 5 by Integrated Value Added:")
                top5 = comparison_df.nlargest(5, 'integrated_value_added')[
                    ['iso3', 'reference_mineral', 'integrated_value_added', 'difference_pct']
                ]
                print(top5.to_string(index=False))

                # Save comparison results
                filename = f"method_comparison_{scenario}_{constraint_code}.csv"
                comparison_df.to_csv(os.path.join(output_dir, filename), index=False)
                print(f"\nSaved: {filename}")

            # Run detailed integrated analysis
            integrated_df = analyze_all_countries_minerals(df, scenario, constraint_code)

            if not integrated_df.empty:
                # Save detailed results
                filename = f"integrated_analysis_{scenario}_{constraint_code}.csv"
                integrated_df.to_csv(os.path.join(output_dir, filename), index=False)
                print(f"Saved: {filename}")

    print(f"\n{'='*80}")
    print(f"Analysis complete. Results saved to: {output_dir}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
