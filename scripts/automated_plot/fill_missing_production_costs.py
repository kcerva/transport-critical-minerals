#!/usr/bin/env python3
"""
Fill Missing Production Costs in all_data.xlsx

This script identifies missing production_cost_usd_per_tonne values in all_data.xlsx
and fills them using the most common (or mean) cost for the same mineral+stage combination.

Strategy:
- For each mineral+stage combination, find the most common non-zero cost
- If >70% of rows use the same cost, use that as fill value
- Otherwise, use the mean of non-zero costs
- Only fills rows where production_cost_usd_per_tonne == 0

Usage:
    python fill_missing_production_costs.py
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


def calculate_fill_values(df):
    """
    Calculate appropriate fill values for missing production costs

    Args:
        df: DataFrame with processing data

    Returns:
        dict: {(mineral, stage): fill_value}
    """
    fill_values = {}

    # Filter for processing stages only
    df_processing = df[df['processing_stage'] > 0].copy()

    # Get all mineral+stage combinations
    combinations = df_processing.groupby(['reference_mineral', 'processing_stage']).size().reset_index()[['reference_mineral', 'processing_stage']]

    print("Calculating fill values for each mineral+stage combination:")
    print("="*80)

    for _, row in combinations.iterrows():
        mineral = row['reference_mineral']
        stage = row['processing_stage']

        # Get data for this combination
        data = df_processing[
            (df_processing['reference_mineral'] == mineral) &
            (df_processing['processing_stage'] == stage)
        ]

        nonzero_costs = data[data['production_cost_usd_per_tonne'] > 0]['production_cost_usd_per_tonne']
        zero_cost_rows = len(data[data['production_cost_usd_per_tonne'] == 0])

        if len(nonzero_costs) == 0:
            # No non-zero costs available - skip
            continue

        if zero_cost_rows == 0:
            # No missing costs - skip
            continue

        # Check if single value dominates
        value_counts = nonzero_costs.value_counts()
        most_common_cost = value_counts.index[0]
        most_common_count = value_counts.iloc[0]
        most_common_pct = most_common_count / len(nonzero_costs) * 100

        mean_cost = nonzero_costs.mean()

        # Decision: use most common if >70%, otherwise use mean
        if most_common_pct > 70:
            fill_value = most_common_cost
            method = "most common"
        else:
            fill_value = mean_cost
            method = "mean"

        fill_values[(mineral, stage)] = fill_value

        print(f"{mineral.upper()} Stage {stage}:")
        print(f"  Rows to fill: {zero_cost_rows}")
        print(f"  Fill value: ${fill_value:.2f} ({method}, {most_common_pct:.1f}% use most common)")

    print()
    return fill_values


def fill_missing_costs(df, fill_values):
    """
    Fill missing production costs using calculated fill values

    Args:
        df: DataFrame to modify
        fill_values: dict of {(mineral, stage): fill_value}

    Returns:
        DataFrame with filled costs
    """
    df = df.copy()

    total_filled = 0

    print("Filling missing production costs:")
    print("="*80)

    for (mineral, stage), fill_value in fill_values.items():
        # Find rows to fill
        mask = (
            (df['reference_mineral'] == mineral) &
            (df['processing_stage'] == stage) &
            (df['production_cost_usd_per_tonne'] == 0)
        )

        rows_to_fill = mask.sum()

        if rows_to_fill > 0:
            df.loc[mask, 'production_cost_usd_per_tonne'] = fill_value
            total_filled += rows_to_fill
            print(f"  {mineral.upper()} Stage {stage}: Filled {rows_to_fill} rows with ${fill_value:.2f}")

    print()
    print(f"Total rows filled: {total_filled}")
    print()

    return df


def fill_remaining_import_costs(fill_values):
    """
    Fill remaining import costs in tonnage flows where countries don't produce
    that mineral/stage combination (so no match was found in all_data.xlsx)

    Currently only fills manganese imports as requested.

    Args:
        fill_values: dict of {(mineral, stage): fill_value} from calculate_fill_values
    """
    # Load config
    config_path = Path(__file__).parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'

    # Check if file exists
    if not flows_path.exists():
        print("  ⚠ tonnage_flows_with_revenues.xlsx not found - skipping import cost filling")
        print(f"    Run merge_prices_with_flows.py first")
        return

    print()
    print("="*80)
    print("FILLING REMAINING MANGANESE IMPORT COSTS")
    print("="*80)
    print(f"File: {flows_path}")
    print()

    # Load data
    print("Loading tonnage_flows_with_revenues.xlsx...")
    df = pd.read_excel(flows_path, sheet_name='All_Flows')
    print(f"  ✓ Loaded {len(df)} rows")
    print()

    # Only fill manganese (as requested)
    manganese_stages = [(mineral, stage) for mineral, stage in fill_values.keys() if mineral == 'manganese']

    print("Filling manganese import costs:")
    print("-"*80)

    filled_rows = 0
    total_additional_cost = 0

    for mineral, stage in manganese_stages:
        fill_value = fill_values[(mineral, stage)]

        # Find manganese imports at this stage that still have zero cost
        mask = (
            (df['reference_mineral'] == mineral) &
            (df['initial_processing_stage'] == stage) &
            (df['trade_type'].str.contains('Import', na=False)) &
            (df['production_cost_usd_per_tonne'] == 0)
        )

        rows_to_fill = mask.sum()

        if rows_to_fill > 0:
            # Calculate cost before filling
            tonnes = df.loc[mask, 'initial_stage_production_tons'].sum()
            additional_cost = tonnes * fill_value

            # Fill costs
            df.loc[mask, 'production_cost_usd_per_tonne'] = fill_value
            df.loc[mask, 'import_cost_usd'] = df.loc[mask, 'initial_stage_production_tons'] * fill_value

            filled_rows += rows_to_fill
            total_additional_cost += additional_cost

            print(f"  {mineral.upper()} stage {stage}: {rows_to_fill} rows, {tonnes/1e3:.1f}k tonnes → +${additional_cost/1e6:.2f}M")

    print()
    print(f"Total rows filled: {filled_rows}")
    print(f"Total additional cost: ${total_additional_cost/1e9:.3f} billion")
    print()

    if filled_rows == 0:
        print("  (No rows to fill - all manganese imports already have costs)")
        return

    # Recalculate summary tables
    print("Recalculating summary tables...")

    # Country-level summary
    country_summary = df.groupby(['scenario', 'constraint', 'iso3']).agg({
        'export_revenue_usd': 'sum',
        'import_cost_usd': 'sum',
        'final_stage_production_tons': lambda x: x[df.loc[x.index, 'trade_type'] == 'Export'].sum(),
        'initial_stage_production_tons': lambda x: x[df.loc[x.index, 'trade_type'].str.contains('Import', na=False)].sum()
    }).reset_index()

    country_summary.columns = ['scenario', 'constraint', 'iso3', 'export_revenue_usd',
                                'import_cost_usd', 'export_tonnes', 'import_tonnes']
    country_summary['net_export_revenue_usd'] = (
        country_summary['export_revenue_usd'] - country_summary['import_cost_usd']
    )

    # Convert to millions for readability
    country_summary['export_revenue_million_usd'] = country_summary['export_revenue_usd'] / 1e6
    country_summary['import_cost_million_usd'] = country_summary['import_cost_usd'] / 1e6
    country_summary['net_export_revenue_million_usd'] = country_summary['net_export_revenue_usd'] / 1e6

    # Reorder columns
    country_summary = country_summary[['scenario', 'constraint', 'iso3',
                                       'export_tonnes', 'export_revenue_million_usd',
                                       'import_tonnes', 'import_cost_million_usd',
                                       'net_export_revenue_million_usd']]

    # Scenario-level summary
    scenario_summary = df.groupby(['scenario', 'constraint']).agg({
        'export_revenue_usd': 'sum',
        'import_cost_usd': 'sum',
        'final_stage_production_tons': lambda x: x[df.loc[x.index, 'trade_type'] == 'Export'].sum(),
        'initial_stage_production_tons': lambda x: x[df.loc[x.index, 'trade_type'].str.contains('Import', na=False)].sum()
    }).reset_index()

    scenario_summary.columns = ['scenario', 'constraint', 'export_revenue_usd',
                                 'import_cost_usd', 'export_tonnes', 'import_tonnes']
    scenario_summary['net_export_revenue_usd'] = (
        scenario_summary['export_revenue_usd'] - scenario_summary['import_cost_usd']
    )

    # Convert to billions for readability
    scenario_summary['export_revenue_billion_usd'] = scenario_summary['export_revenue_usd'] / 1e9
    scenario_summary['import_cost_billion_usd'] = scenario_summary['import_cost_usd'] / 1e9
    scenario_summary['net_export_revenue_billion_usd'] = scenario_summary['net_export_revenue_usd'] / 1e9

    # Reorder columns
    scenario_summary = scenario_summary[['scenario', 'constraint',
                                         'export_tonnes', 'export_revenue_billion_usd',
                                         'import_tonnes', 'import_cost_billion_usd',
                                         'net_export_revenue_billion_usd']]

    print("  ✓ Summaries updated")

    # Save updated file
    print(f"Saving updated file...")
    with pd.ExcelWriter(flows_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All_Flows', index=False)
        country_summary.to_excel(writer, sheet_name='Country_Summary', index=False)
        scenario_summary.to_excel(writer, sheet_name='Scenario_Summary', index=False)

    print("  ✓ Saved")

    # Summary statistics
    total_import_cost = df['import_cost_usd'].sum() / 1e9
    total_export_revenue = df['export_revenue_usd'].sum() / 1e9
    net_revenue = total_export_revenue - total_import_cost

    print()
    print(f"Updated totals:")
    print(f"  Total import cost: ${total_import_cost:.2f} billion")
    print(f"  Net export revenue: ${net_revenue:.2f} billion")


def main():
    """Main function"""
    # Load config
    config_path = Path(__file__).parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    all_data_path = results_path / 'all_data.xlsx'
    all_data_filled_path = results_path / 'all_data_filled_costs.xlsx'

    print("="*80)
    print("FILLING MISSING PRODUCTION COSTS IN all_data.xlsx")
    print("="*80)
    print(f"Input: {all_data_path}")
    print(f"Output: {all_data_filled_path}")
    print()

    # Load data
    print("Loading all_data.xlsx...")
    df = pd.read_excel(all_data_path)
    print(f"  ✓ Loaded {len(df)} rows")
    print()

    # Calculate fill values
    fill_values = calculate_fill_values(df)
    print(f"Calculated {len(fill_values)} fill values")
    print()

    # Fill missing costs
    df_filled = fill_missing_costs(df, fill_values)

    # Verify
    print("Verification:")
    print("="*80)
    original_zeros = (df['production_cost_usd_per_tonne'] == 0).sum()
    filled_zeros = (df_filled['production_cost_usd_per_tonne'] == 0).sum()
    print(f"  Original rows with zero cost: {original_zeros}")
    print(f"  Remaining rows with zero cost: {filled_zeros}")
    print(f"  Rows filled: {original_zeros - filled_zeros}")
    print()

    # Save filled data
    print(f"Saving to {all_data_filled_path}...")
    df_filled.to_excel(all_data_filled_path, index=False)
    print("  ✓ Saved")

    # Also fill remaining manganese import costs (for countries that don't produce manganese)
    fill_remaining_import_costs(fill_values)

    print()
    print("="*80)
    print("FILLING COMPLETE")
    print("="*80)
    print()
    print("Next steps:")
    print("  1. Review all_data_filled_costs.xlsx")
    print("  2. If tonnage_flows_with_revenues.xlsx was updated, regenerate figures")

    return all_data_filled_path


if __name__ == '__main__':
    main()
