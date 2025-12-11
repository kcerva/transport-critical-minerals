"""
Utility functions for scenario filtering and demand range calculations

Provides reusable functions for:
- Filtering dataframes by goal, demand, policy, and constraint
- Calculating demand ranges (low/mid/high)
- Comparing scenarios with uncertainty bounds
- Parsing scenario names into components
"""

import pandas as pd
import numpy as np
from .config import PUBLICATION_SCENARIOS, DEMAND_PATTERNS, POLICY_PATTERNS, CONSTRAINT_PATTERNS


def filter_scenarios_by_goal(df, goal, include_all_demands=True, include_all_policies=True,
                              constraint=None):
    """
    Filter dataframe to specific goal(s) with optional demand/policy filtering

    Args:
        df: Input dataframe with 'scenario' column
        goal: 'baseline', 'bau', 'early_refining', 'precursor', or list of goals
        include_all_demands: If True, include low/mid/high. If False, only mid
        include_all_policies: If True, include both national and regional. If False, only national
        constraint: If specified, filter to 'constrained' or 'unconstrained'

    Returns:
        Filtered dataframe

    Examples:
        # Get all BAU scenarios
        df_bau = filter_scenarios_by_goal(df, 'bau')

        # Get only mid-demand, national policy Precursor scenarios
        df_precursor_mid_nat = filter_scenarios_by_goal(
            df, 'precursor',
            include_all_demands=False,
            include_all_policies=False
        )

        # Get BAU and Precursor, all variations
        df_comparison = filter_scenarios_by_goal(df, ['bau', 'precursor'])
    """
    if isinstance(goal, str):
        goal = [goal]

    # Collect all scenarios for requested goals
    scenarios = []
    for g in goal:
        if g not in PUBLICATION_SCENARIOS:
            print(f"Warning: Unknown goal '{g}'. Valid goals: {list(PUBLICATION_SCENARIOS.keys())}")
            continue
        scenarios.extend(PUBLICATION_SCENARIOS[g]['scenarios'])

    if not scenarios:
        return pd.DataFrame()  # Return empty if no valid scenarios

    # Filter to requested scenarios
    df_filtered = df[df['scenario'].isin(scenarios)].copy()

    # Further filter by demand if requested
    if not include_all_demands:
        # Default to mid-demand only
        df_filtered = df_filtered[df_filtered['scenario'].str.contains('_mid_')]

    # Further filter by policy if requested
    if not include_all_policies:
        # Default to national only (_min_)
        df_filtered = df_filtered[df_filtered['scenario'].str.contains('_min_')]

    # Filter by constraint if specified
    if constraint is not None:
        if constraint in CONSTRAINT_PATTERNS:
            constraint_pattern = CONSTRAINT_PATTERNS[constraint]
            df_filtered = df_filtered[df_filtered['constraint'].str.contains(constraint_pattern)]
        else:
            print(f"Warning: Unknown constraint '{constraint}'. Valid: {list(CONSTRAINT_PATTERNS.keys())}")

    return df_filtered


def calculate_demand_ranges(df, goal, metric, groupby_cols=['iso3'],
                            constraint='unconstrained', policy='both'):
    """
    Calculate low/mid/high demand ranges for a given metric

    Args:
        df: Input dataframe
        goal: 'bau', 'early_refining', or 'precursor'
        metric: Column name to aggregate (e.g., 'production_tonnes', 'revenue_usd')
        groupby_cols: Columns to group by (default: by country)
        constraint: 'constrained', 'unconstrained', or 'both'
        policy: 'national', 'regional', or 'both' (aggregate across if 'both')

    Returns:
        DataFrame with columns: groupby_cols + [low, mid, high, range_abs, range_pct]

    Examples:
        # Get production ranges by country for Precursor scenarios
        ranges = calculate_demand_ranges(
            df, 'precursor', 'production_tonnes',
            groupby_cols=['iso3']
        )

        # Get revenue ranges by mineral
        ranges = calculate_demand_ranges(
            df, 'bau', 'revenue_usd',
            groupby_cols=['reference_mineral']
        )
    """
    # Filter to goal and constraint
    df_goal = filter_scenarios_by_goal(df, goal, constraint=constraint)

    if df_goal.empty:
        print(f"Warning: No data for goal='{goal}', constraint='{constraint}'")
        return pd.DataFrame()

    # Further filter by policy if specified
    if policy != 'both':
        if policy == 'national':
            df_goal = df_goal[df_goal['scenario'].str.contains('_min_')]
        elif policy == 'regional':
            df_goal = df_goal[df_goal['scenario'].str.contains('_max_')]

    # Calculate ranges for each demand level
    results = []
    for demand in ['low', 'mid', 'high']:
        df_demand = df_goal[df_goal['scenario'].str.contains(f'_{demand}_')]

        if df_demand.empty:
            continue

        # Aggregate by grouping columns
        agg_data = df_demand.groupby(groupby_cols)[metric].sum().reset_index()
        agg_data.rename(columns={metric: demand}, inplace=True)

        if not results:
            results.append(agg_data)
        else:
            results[0] = results[0].merge(agg_data, on=groupby_cols, how='outer')

    if not results:
        return pd.DataFrame()

    result_df = results[0].fillna(0)

    # Calculate ranges
    result_df['range_abs'] = result_df['high'] - result_df['low']
    result_df['range_pct'] = np.where(
        result_df['mid'] != 0,
        (result_df['range_abs'] / result_df['mid']) * 100,
        0
    )

    return result_df


def extract_scenario_attributes(scenario_name):
    """
    Parse scenario name into components

    Args:
        scenario_name: Scenario string (e.g., 'precursor_2040_mid_min_threshold_metal_tons')

    Returns:
        dict: {'goal': str, 'year': int, 'demand': str, 'policy': str}

    Examples:
        >>> extract_scenario_attributes('precursor_2040_mid_min_threshold_metal_tons')
        {'goal': 'precursor', 'year': 2040, 'demand': 'mid', 'policy': 'national'}

        >>> extract_scenario_attributes('2022_baseline')
        {'goal': 'baseline', 'year': 2022, 'demand': None, 'policy': None}
    """
    # Handle baseline case
    if '2022' in scenario_name or 'baseline' in scenario_name:
        return {'goal': 'baseline', 'year': 2022, 'demand': None, 'policy': None}

    # Parse goal
    if scenario_name.startswith('bau_'):
        goal = 'bau'
    elif scenario_name.startswith('early_refining_'):
        goal = 'early_refining'
    elif scenario_name.startswith('precursor_'):
        goal = 'precursor'
    else:
        goal = 'unknown'

    # Parse year
    year = 2040  # Default
    if '2030' in scenario_name:
        year = 2030
    elif '2040' in scenario_name:
        year = 2040

    # Parse demand
    demand = None
    for d in ['low', 'mid', 'high']:
        if f'_{d}_' in scenario_name:
            demand = d
            break

    # Parse policy
    policy = None
    if '_min_' in scenario_name:
        policy = 'national'
    elif '_max_' in scenario_name:
        policy = 'regional'

    return {
        'goal': goal,
        'year': year,
        'demand': demand,
        'policy': policy
    }


def compare_goals_with_ranges(df, goals, metric, constraint='unconstrained',
                               policy='both', groupby_cols=['iso3', 'reference_mineral']):
    """
    Compare multiple goals showing demand ranges (low/mid/high)

    Args:
        df: Input dataframe
        goals: List of goals to compare (e.g., ['bau', 'precursor'])
        metric: Metric to compare
        constraint: 'constrained', 'unconstrained', or 'both'
        policy: 'national', 'regional', or 'both'
        groupby_cols: Columns to group by

    Returns:
        DataFrame ready for plotting with error bars
        Columns: groupby_cols + [goal1_mid, goal1_low, goal1_high, goal2_mid, ...]

    Examples:
        # Compare BAU vs Precursor production with demand ranges
        comparison = compare_goals_with_ranges(
            df, ['bau', 'precursor'], 'production_tonnes',
            groupby_cols=['iso3']
        )

        # Compare all three goals for revenue
        comparison = compare_goals_with_ranges(
            df, ['bau', 'early_refining', 'precursor'], 'revenue_usd',
            groupby_cols=['reference_mineral']
        )
    """
    combined_results = None

    for goal in goals:
        # Calculate ranges for this goal
        ranges = calculate_demand_ranges(
            df, goal, metric,
            groupby_cols=groupby_cols,
            constraint=constraint,
            policy=policy
        )

        if ranges.empty:
            print(f"Warning: No ranges calculated for goal='{goal}'")
            continue

        # Rename columns to include goal name
        ranges = ranges.rename(columns={
            'low': f'{goal}_low',
            'mid': f'{goal}_mid',
            'high': f'{goal}_high',
            'range_abs': f'{goal}_range_abs',
            'range_pct': f'{goal}_range_pct'
        })

        # Merge with combined results
        if combined_results is None:
            combined_results = ranges
        else:
            combined_results = combined_results.merge(
                ranges, on=groupby_cols, how='outer'
            )

    if combined_results is None:
        return pd.DataFrame()

    return combined_results.fillna(0)


def get_policy_comparison(df, goal, metric, demand='mid', groupby_cols=['iso3']):
    """
    Compare national vs regional policy for a specific goal and demand level

    Args:
        df: Input dataframe
        goal: Goal to analyze ('bau', 'early_refining', 'precursor')
        metric: Metric to compare
        demand: 'low', 'mid', or 'high'
        groupby_cols: Columns to group by

    Returns:
        DataFrame with columns: groupby_cols + [national_constrained, national_unconstrained,
                                                  regional_constrained, regional_unconstrained]

    Examples:
        # Compare national vs regional for mid-demand Precursor
        policy_comp = get_policy_comparison(
            df, 'precursor', 'production_tonnes', demand='mid'
        )
    """
    df_goal = filter_scenarios_by_goal(df, goal)
    df_goal = df_goal[df_goal['scenario'].str.contains(f'_{demand}_')]

    results = {}

    for policy_label, policy_pattern in [('national', '_min_'), ('regional', '_max_')]:
        df_policy = df_goal[df_goal['scenario'].str.contains(policy_pattern)]

        for constraint_label in ['constrained', 'unconstrained']:
            df_constraint = df_policy[df_policy['constraint'].str.contains(constraint_label)]

            if df_constraint.empty:
                continue

            agg_data = df_constraint.groupby(groupby_cols)[metric].sum().reset_index()
            col_name = f'{policy_label}_{constraint_label}'
            agg_data.rename(columns={metric: col_name}, inplace=True)

            if not results:
                results = agg_data
            else:
                results = results.merge(agg_data, on=groupby_cols, how='outer')

    return results.fillna(0) if isinstance(results, pd.DataFrame) else pd.DataFrame()


def filter_by_processing_stage(df, stage_type=None, exclude_stage_zero=True):
    """
    Filter dataframe by processing stage type

    Args:
        df: Input dataframe
        stage_type: 'Beneficiation', 'Early refining', 'Precursor related product', or None for all
        exclude_stage_zero: If True, exclude stage 0 (metal content)

    Returns:
        Filtered dataframe
    """
    df_filtered = df.copy()

    if exclude_stage_zero:
        df_filtered = df_filtered[df_filtered['processing_stage'] > 0]

    if stage_type is not None:
        df_filtered = df_filtered[df_filtered['processing_type'] == stage_type]

    return df_filtered


def get_aggregated_global_totals(df, goal, metric, include_all_demands=True):
    """
    Get global totals (sum across all countries) for a goal

    Args:
        df: Input dataframe
        goal: Goal to analyze
        metric: Metric to sum
        include_all_demands: If True, return separate totals for low/mid/high

    Returns:
        If include_all_demands=True: dict with keys 'low', 'mid', 'high'
        If include_all_demands=False: float (mid-demand total)
    """
    df_goal = filter_scenarios_by_goal(df, goal)

    if not include_all_demands:
        df_goal = df_goal[df_goal['scenario'].str.contains('_mid_')]
        return df_goal[metric].sum()

    totals = {}
    for demand in ['low', 'mid', 'high']:
        df_demand = df_goal[df_goal['scenario'].str.contains(f'_{demand}_')]
        totals[demand] = df_demand[metric].sum()

    return totals
