#!/usr/bin/env python3
"""
Merge Price and Cost Data with Tonnage Flows

This script merges price_usd_per_tonne and production_cost_usd_per_tonne from
all_data.xlsx with tonnage_flows_comprehensive.xlsx to calculate net export revenues.

Formula (CORRECTED):
- Export revenue = final_stage_production_tons × price_usd_per_tonne (from final stage)
- Import cost = final_stage_production_tons × unit_cost (from final stage)
  where unit_cost can be either production_cost_usd_per_tonne or price_usd_per_tonne
- Net export revenue = Export revenue - Import cost

Both production cost and price are provided for final stage to allow flexibility in analysis.

Usage:
    python merge_prices_with_flows.py
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


def merge_prices_with_flows():
    """
    Merge price and cost data from all_data.xlsx with tonnage flows.
    Calculate export revenues and import costs.
    """
    print("="*80)
    print("MERGING PRICES/COSTS WITH TONNAGE FLOWS")
    print("="*80)
    print()

    # Load config
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / 'config.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])

    # Load data
    print("Loading data files...")
    all_data_path = results_path / 'all_data_filled_costs.xlsx'
    tonnage_flows_path = results_path / 'tonnage_flows_comprehensive.xlsx'
    output_path = results_path / 'tonnage_flows_with_revenues.xlsx'

    df_all = pd.read_excel(all_data_path)
    df_flows = pd.read_excel(tonnage_flows_path, sheet_name='All_Data')

    print(f"  ✓ all_data_filled_costs.xlsx: {len(df_all)} rows")
    print(f"  ✓ tonnage_flows: {len(df_flows)} rows")
    print()

    # Prepare price/cost lookup from all_data
    print("="*80)
    print("STEP 1: Merging Price Data (for final stage)")
    print("="*80)
    print()

    # Merge price for final stage
    df_merged = df_flows.merge(
        df_all[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 'price_usd_per_tonne']],
        left_on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'final_processing_stage'],
        right_on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage'],
        how='left',
        suffixes=('', '_price_merge')
    )
    df_merged = df_merged.drop('processing_stage', axis=1)

    # Rename to be explicit about final stage
    df_merged = df_merged.rename(columns={'price_usd_per_tonne': 'final_stage_price_usd_per_tonne'})

    # Check merge success
    rows_with_price = df_merged['final_stage_price_usd_per_tonne'].notna().sum()
    print(f"Rows with price data: {rows_with_price} / {len(df_merged)} ({rows_with_price/len(df_merged)*100:.1f}%)")
    print()

    print("="*80)
    print("STEP 2: Merging Production Cost Data (for final stage)")
    print("="*80)
    print()

    # Merge production cost for final stage (NOT initial)
    df_merged = df_merged.merge(
        df_all[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 'production_cost_usd_per_tonne']],
        left_on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'final_processing_stage'],
        right_on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage'],
        how='left',
        suffixes=('', '_cost_merge')
    )
    df_merged = df_merged.drop('processing_stage', axis=1)

    # Rename to be explicit about final stage
    df_merged = df_merged.rename(columns={'production_cost_usd_per_tonne': 'final_stage_production_cost_usd_per_tonne'})

    # Check merge success
    rows_with_cost = df_merged['final_stage_production_cost_usd_per_tonne'].notna().sum()
    print(f"Rows with cost data: {rows_with_cost} / {len(df_merged)} ({rows_with_cost/len(df_merged)*100:.1f}%)")
    print()

    print("="*80)
    print("STEP 3: Checking for Missing Data and Filling")
    print("="*80)
    print()

    # Check for missing data before filling
    missing_price = df_merged['final_stage_price_usd_per_tonne'].isna().sum()
    missing_cost = df_merged['final_stage_production_cost_usd_per_tonne'].isna().sum()

    print(f"Missing final_stage_price_usd_per_tonne: {missing_price} rows ({missing_price/len(df_merged)*100:.1f}%)")
    print(f"Missing final_stage_production_cost_usd_per_tonne: {missing_cost} rows ({missing_cost/len(df_merged)*100:.1f}%)")
    print()

    # Check zeros (which might indicate missing data)
    zero_price = (df_merged['final_stage_price_usd_per_tonne'] == 0).sum()
    zero_cost = (df_merged['final_stage_production_cost_usd_per_tonne'] == 0).sum()

    print(f"Zero final_stage_price_usd_per_tonne: {zero_price} rows ({zero_price/len(df_merged)*100:.1f}%)")
    print(f"Zero final_stage_production_cost_usd_per_tonne: {zero_cost} rows ({zero_cost/len(df_merged)*100:.1f}%)")
    print()

    # Fill NaN with 0 for calculations
    df_merged['final_stage_price_usd_per_tonne'] = df_merged['final_stage_price_usd_per_tonne'].fillna(0)
    df_merged['final_stage_production_cost_usd_per_tonne'] = df_merged['final_stage_production_cost_usd_per_tonne'].fillna(0)

    print("="*80)
    print("STEP 4: Calculating Revenues and Costs (CORRECTED)")
    print("="*80)
    print()

    print("IMPORTANT: Now using final_stage_production_tons for BOTH exports and imports")
    print()

    # Calculate export revenue (for Export flows only)
    # Uses: final_stage_production_tons × final_stage_price_usd_per_tonne
    df_merged['export_revenue_usd'] = 0.0
    export_mask = df_merged['trade_type'] == 'Export'
    df_merged.loc[export_mask, 'export_revenue_usd'] = (
        df_merged.loc[export_mask, 'final_stage_production_tons'] *
        df_merged.loc[export_mask, 'final_stage_price_usd_per_tonne']
    )

    total_export_revenue = df_merged['export_revenue_usd'].sum() / 1e9
    print(f"Total export revenue: ${total_export_revenue:.2f} billion")
    print(f"  (final_stage_production_tons × final_stage_price)")

    # Calculate import cost using PRODUCTION COST (for Import flows only)
    # Uses: final_stage_production_tons × final_stage_production_cost_usd_per_tonne
    df_merged['import_cost_usd'] = 0.0
    import_mask = df_merged['trade_type'].str.contains('Import', na=False)
    df_merged.loc[import_mask, 'import_cost_usd'] = (
        df_merged.loc[import_mask, 'final_stage_production_tons'] *
        df_merged.loc[import_mask, 'final_stage_production_cost_usd_per_tonne']
    )

    total_import_cost = df_merged['import_cost_usd'].sum() / 1e9
    print(f"Total import cost (production cost basis): ${total_import_cost:.2f} billion")
    print(f"  (final_stage_production_tons × final_stage_production_cost)")

    # ALSO calculate import cost using MARKET PRICE for comparison
    # Uses: final_stage_production_tons × final_stage_price_usd_per_tonne
    df_merged['import_cost_at_price_usd'] = 0.0
    df_merged.loc[import_mask, 'import_cost_at_price_usd'] = (
        df_merged.loc[import_mask, 'final_stage_production_tons'] *
        df_merged.loc[import_mask, 'final_stage_price_usd_per_tonne']
    )

    total_import_cost_price = df_merged['import_cost_at_price_usd'].sum() / 1e9
    print(f"Total import cost (market price basis): ${total_import_cost_price:.2f} billion")
    print(f"  (final_stage_production_tons × final_stage_price)")

    # Calculate net export revenue (both approaches)
    net_export_revenue_cost = total_export_revenue - total_import_cost
    net_export_revenue_price = total_export_revenue - total_import_cost_price

    print()
    print(f"Net export revenue (production cost basis): ${net_export_revenue_cost:.2f} billion")
    print(f"Net export revenue (market price basis): ${net_export_revenue_price:.2f} billion")
    print(f"Difference: ${net_export_revenue_cost - net_export_revenue_price:.2f} billion")
    print()

    print("="*80)
    print("STEP 5: Creating Summary Tables")
    print("="*80)
    print()

    # Country-level summary
    print("Creating country-level summary...")

    # Create separate aggregations for exports and imports
    export_agg = df_merged[df_merged['trade_type'] == 'Export'].groupby(['scenario', 'constraint', 'iso3']).agg({
        'export_revenue_usd': 'sum',
        'final_stage_production_tons': 'sum'
    }).rename(columns={'final_stage_production_tons': 'export_tonnes'})

    import_agg = df_merged[df_merged['trade_type'].str.contains('Import', na=False)].groupby(['scenario', 'constraint', 'iso3']).agg({
        'import_cost_usd': 'sum',
        'import_cost_at_price_usd': 'sum',
        'final_stage_production_tons': 'sum'
    }).rename(columns={'final_stage_production_tons': 'import_tonnes'})

    # Merge export and import summaries
    country_summary = export_agg.join(import_agg, how='outer').fillna(0).reset_index()

    country_summary['net_export_revenue_usd'] = (
        country_summary['export_revenue_usd'] - country_summary['import_cost_usd']
    )
    country_summary['net_export_revenue_at_price_usd'] = (
        country_summary['export_revenue_usd'] - country_summary['import_cost_at_price_usd']
    )

    # Convert to millions for readability
    country_summary['export_revenue_million_usd'] = country_summary['export_revenue_usd'] / 1e6
    country_summary['import_cost_million_usd'] = country_summary['import_cost_usd'] / 1e6
    country_summary['import_cost_at_price_million_usd'] = country_summary['import_cost_at_price_usd'] / 1e6
    country_summary['net_export_revenue_million_usd'] = country_summary['net_export_revenue_usd'] / 1e6
    country_summary['net_export_revenue_at_price_million_usd'] = country_summary['net_export_revenue_at_price_usd'] / 1e6

    # Reorder columns
    country_summary = country_summary[['scenario', 'constraint', 'iso3',
                                       'export_tonnes', 'export_revenue_million_usd',
                                       'import_tonnes', 'import_cost_million_usd', 'import_cost_at_price_million_usd',
                                       'net_export_revenue_million_usd', 'net_export_revenue_at_price_million_usd']]

    print(f"  ✓ Country summary: {len(country_summary)} rows")

    # Scenario-level summary
    print("Creating scenario-level summary...")

    export_agg_scenario = df_merged[df_merged['trade_type'] == 'Export'].groupby(['scenario', 'constraint']).agg({
        'export_revenue_usd': 'sum',
        'final_stage_production_tons': 'sum'
    }).rename(columns={'final_stage_production_tons': 'export_tonnes'})

    import_agg_scenario = df_merged[df_merged['trade_type'].str.contains('Import', na=False)].groupby(['scenario', 'constraint']).agg({
        'import_cost_usd': 'sum',
        'import_cost_at_price_usd': 'sum',
        'final_stage_production_tons': 'sum'
    }).rename(columns={'final_stage_production_tons': 'import_tonnes'})

    scenario_summary = export_agg_scenario.join(import_agg_scenario, how='outer').fillna(0).reset_index()

    scenario_summary['net_export_revenue_usd'] = (
        scenario_summary['export_revenue_usd'] - scenario_summary['import_cost_usd']
    )
    scenario_summary['net_export_revenue_at_price_usd'] = (
        scenario_summary['export_revenue_usd'] - scenario_summary['import_cost_at_price_usd']
    )

    # Convert to billions for readability
    scenario_summary['export_revenue_billion_usd'] = scenario_summary['export_revenue_usd'] / 1e9
    scenario_summary['import_cost_billion_usd'] = scenario_summary['import_cost_usd'] / 1e9
    scenario_summary['import_cost_at_price_billion_usd'] = scenario_summary['import_cost_at_price_usd'] / 1e9
    scenario_summary['net_export_revenue_billion_usd'] = scenario_summary['net_export_revenue_usd'] / 1e9
    scenario_summary['net_export_revenue_at_price_billion_usd'] = scenario_summary['net_export_revenue_at_price_usd'] / 1e9

    # Reorder columns
    scenario_summary = scenario_summary[['scenario', 'constraint',
                                         'export_tonnes', 'export_revenue_billion_usd',
                                         'import_tonnes', 'import_cost_billion_usd', 'import_cost_at_price_billion_usd',
                                         'net_export_revenue_billion_usd', 'net_export_revenue_at_price_billion_usd']]

    print(f"  ✓ Scenario summary: {len(scenario_summary)} rows")
    print()

    print("="*80)
    print("STEP 6: Writing Output File")
    print("="*80)
    print()

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Write main flow data
        df_merged.to_excel(writer, sheet_name='All_Flows', index=False)
        print(f"  ✓ All_Flows sheet: {len(df_merged)} rows, {len(df_merged.columns)} columns")

        # Write country summary
        country_summary.to_excel(writer, sheet_name='Country_Summary', index=False)
        print(f"  ✓ Country_Summary sheet: {len(country_summary)} rows")

        # Write scenario summary
        scenario_summary.to_excel(writer, sheet_name='Scenario_Summary', index=False)
        print(f"  ✓ Scenario_Summary sheet: {len(scenario_summary)} rows")

    print()
    print("="*80)
    print("MERGE COMPLETE")
    print("="*80)
    print(f"Output file: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()

    # Show top countries by net export revenue (both methods)
    print("Top 5 Countries by Net Export Revenue (Mid Demand, Precursor_2040, Region Unconstrained):")
    prec_mid = country_summary[
        (country_summary['scenario'].str.contains('precursor_2040_mid_max')) &
        (country_summary['constraint'].str.contains('unconstrained'))
    ].sort_values('net_export_revenue_million_usd', ascending=False).head(5)

    for _, row in prec_mid.iterrows():
        print(f"  {row['iso3']}: ")
        print(f"    Production cost basis: ${row['net_export_revenue_million_usd']:.0f}M "
              f"(exports ${row['export_revenue_million_usd']:.0f}M - imports ${row['import_cost_million_usd']:.0f}M)")
        print(f"    Market price basis:    ${row['net_export_revenue_at_price_million_usd']:.0f}M "
              f"(exports ${row['export_revenue_million_usd']:.0f}M - imports ${row['import_cost_at_price_million_usd']:.0f}M)")
    print()

    print("="*80)
    print("CALCULATION SUMMARY")
    print("="*80)
    print()
    print("✓ Both exports and imports now use final_stage_production_tons")
    print("✓ Both production cost and market price calculations provided")
    print("✓ import_cost_usd = production cost basis (default)")
    print("✓ import_cost_at_price_usd = market price basis (alternative)")
    print()
    print("Choose which approach to use in your analysis based on:")
    print("  - Production cost: Shows value creation potential")
    print("  - Market price: Shows actual cash flows/trade balance")
    print()
    print("✓ Merge successful!")

    return output_path


if __name__ == '__main__':
    try:
        output_file = merge_prices_with_flows()
        exit(0)
    except Exception as e:
        print(f"✗ Error during merge: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
