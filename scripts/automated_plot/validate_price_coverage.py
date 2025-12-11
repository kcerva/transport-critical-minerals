#!/usr/bin/env python3
"""
Validate Price Coverage for Tonnage Flows

This script checks whether tonnage flows can be matched with price/cost data
from all_data.xlsx before running the full merge.

Usage:
    python validate_price_coverage.py
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


def check_price_coverage():
    """
    Check what percentage of tonnage flows have matching price/cost data
    """
    print("="*80)
    print("PRICE/COST DATA COVERAGE VALIDATION")
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
    all_data_path = results_path / 'all_data.xlsx'
    tonnage_flows_path = results_path / 'tonnage_flows_comprehensive.xlsx'

    df_all = pd.read_excel(all_data_path)
    df_flows = pd.read_excel(tonnage_flows_path, sheet_name='All_Data')

    print(f"  ✓ all_data.xlsx: {len(df_all)} rows")
    print(f"  ✓ tonnage_flows: {len(df_flows)} rows")
    print()

    # Create lookup from all_data
    print("="*80)
    print("STEP 1: Analyze Price Availability in all_data.xlsx")
    print("="*80)
    print()

    # Check which stages have prices
    stages_with_prices = df_all[df_all['price_usd_per_tonne'] > 0].groupby(
        ['reference_mineral', 'processing_stage']
    )['price_usd_per_tonne'].first().reset_index()

    print("Stages with market prices by mineral:")
    for mineral in sorted(stages_with_prices['reference_mineral'].unique()):
        stages = sorted(stages_with_prices[stages_with_prices['reference_mineral'] == mineral]['processing_stage'].values)
        print(f"  {mineral.title()}: stages {stages}")
    print()

    # Check which stages have costs
    stages_with_costs = df_all[df_all['production_cost_usd_per_tonne'] > 0].groupby(
        ['reference_mineral', 'processing_stage']
    )['production_cost_usd_per_tonne'].first().reset_index()

    print("Stages with production costs by mineral:")
    for mineral in sorted(stages_with_costs['reference_mineral'].unique()):
        stages = sorted(stages_with_costs[stages_with_costs['reference_mineral'] == mineral]['processing_stage'].values)
        print(f"  {mineral.title()}: stages {stages}")
    print()

    # Create merge keys
    print("="*80)
    print("STEP 2: Test Merge - Check Match Rates")
    print("="*80)
    print()

    # Test merge for final stage (exports)
    print("Testing final stage price matching (for exports)...")
    df_test = df_flows.merge(
        df_all[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage',
                'price_usd_per_tonne', 'production_cost_usd_per_tonne']],
        left_on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'final_processing_stage'],
        right_on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage'],
        how='left',
        suffixes=('', '_final')
    )

    # Check exports with prices
    exports = df_test[df_test['trade_type'] == 'Export'].copy()
    exports_with_price = exports[exports['price_usd_per_tonne'] > 0]
    exports_without_price = exports[exports['price_usd_per_tonne'].isna() | (exports['price_usd_per_tonne'] == 0)]

    print(f"\nExport Flows:")
    print(f"  Total export flows: {len(exports)}")
    print(f"  With price (> 0): {len(exports_with_price)} ({len(exports_with_price)/len(exports)*100:.1f}%)")
    print(f"  Without price (0 or NaN): {len(exports_without_price)} ({len(exports_without_price)/len(exports)*100:.1f}%)")

    # Check tonnage coverage
    export_tonnes_with_price = exports_with_price['final_stage_production_tons'].sum()
    export_tonnes_total = exports['final_stage_production_tons'].sum()
    print(f"\nExport Tonnage:")
    print(f"  Total: {export_tonnes_total/1e6:.2f} Mt")
    print(f"  With price: {export_tonnes_with_price/1e6:.2f} Mt ({export_tonnes_with_price/export_tonnes_total*100:.1f}%)")
    print(f"  Without price: {(export_tonnes_total - export_tonnes_with_price)/1e6:.2f} Mt")

    # Show which stages are missing prices for exports
    if len(exports_without_price) > 0:
        print(f"\nExport stages WITHOUT prices:")
        missing_export_stages = exports_without_price.groupby(
            ['reference_mineral', 'final_processing_stage']
        )['final_stage_production_tons'].sum().reset_index()
        missing_export_stages = missing_export_stages.sort_values('final_stage_production_tons', ascending=False)
        for _, row in missing_export_stages.head(10).iterrows():
            print(f"  {row['reference_mineral'].title()} stage {row['final_processing_stage']}: "
                  f"{row['final_stage_production_tons']/1e6:.2f} Mt")

    # Test merge for initial stage (imports)
    print("\n" + "-"*80)
    print("Testing initial stage cost matching (for imports)...")

    imports = df_test[df_test['trade_type'].str.contains('Import', na=False)].copy()
    imports_with_cost = imports[imports['production_cost_usd_per_tonne'] > 0]
    imports_without_cost = imports[imports['production_cost_usd_per_tonne'].isna() | (imports['production_cost_usd_per_tonne'] == 0)]

    print(f"\nImport Flows:")
    print(f"  Total import flows: {len(imports)}")
    print(f"  With cost (> 0): {len(imports_with_cost)} ({len(imports_with_cost)/len(imports)*100:.1f}%)")
    print(f"  Without cost (0 or NaN): {len(imports_without_cost)} ({len(imports_without_cost)/len(imports)*100:.1f}%)")

    # Check tonnage coverage
    import_tonnes_with_cost = imports_with_cost['initial_stage_production_tons'].sum()
    import_tonnes_total = imports['initial_stage_production_tons'].sum()
    print(f"\nImport Tonnage:")
    print(f"  Total: {import_tonnes_total/1e6:.2f} Mt")
    print(f"  With cost: {import_tonnes_with_cost/1e6:.2f} Mt ({import_tonnes_with_cost/import_tonnes_total*100:.1f}%)")
    print(f"  Without cost: {(import_tonnes_total - import_tonnes_with_cost)/1e6:.2f} Mt")

    # Show which stages are missing costs for imports
    if len(imports_without_cost) > 0:
        print(f"\nImport stages WITHOUT costs:")
        missing_import_stages = imports_without_cost.groupby(
            ['reference_mineral', 'initial_processing_stage']
        )['initial_stage_production_tons'].sum().reset_index()
        missing_import_stages = missing_import_stages.sort_values('initial_stage_production_tons', ascending=False)
        for _, row in missing_import_stages.head(10).iterrows():
            print(f"  {row['reference_mineral'].title()} stage {row['initial_processing_stage']}: "
                  f"{row['initial_stage_production_tons']/1e6:.2f} Mt")

    # Overall assessment
    print("\n" + "="*80)
    print("STEP 3: Overall Assessment")
    print("="*80)
    print()

    # Calculate potential revenue coverage
    potential_export_revenue = (exports_with_price['final_stage_production_tons'] *
                                exports_with_price['price_usd_per_tonne']).sum() / 1e9

    potential_import_cost = (imports_with_cost['initial_stage_production_tons'] *
                            imports_with_cost['production_cost_usd_per_tonne']).sum() / 1e9

    print(f"If we proceed with the merge:")
    print(f"  Export revenue (calculable): ${potential_export_revenue:.2f} billion")
    print(f"  Import cost (calculable): ${potential_import_cost:.2f} billion")
    print(f"  Net export revenue: ${potential_export_revenue - potential_import_cost:.2f} billion")
    print()

    # Data quality score
    export_coverage = len(exports_with_price) / len(exports) * 100 if len(exports) > 0 else 0
    import_coverage = len(imports_with_cost) / len(imports) * 100 if len(imports) > 0 else 0
    export_tonnage_coverage = export_tonnes_with_price / export_tonnes_total * 100 if export_tonnes_total > 0 else 0
    import_tonnage_coverage = import_tonnes_with_cost / import_tonnes_total * 100 if import_tonnes_total > 0 else 0

    print("Data Quality Scores:")
    print(f"  Export flow coverage: {export_coverage:.1f}%")
    print(f"  Export tonnage coverage: {export_tonnage_coverage:.1f}%")
    print(f"  Import flow coverage: {import_coverage:.1f}%")
    print(f"  Import tonnage coverage: {import_tonnage_coverage:.1f}%")
    print()

    if export_tonnage_coverage > 90 and import_tonnage_coverage > 90:
        print("✓ EXCELLENT: >90% tonnage coverage for both exports and imports")
    elif export_tonnage_coverage > 70 and import_tonnage_coverage > 70:
        print("✓ GOOD: >70% tonnage coverage for both exports and imports")
    elif export_tonnage_coverage > 50 and import_tonnage_coverage > 50:
        print("⚠ FAIR: >50% tonnage coverage, but significant gaps exist")
    else:
        print("✗ POOR: <50% tonnage coverage, major data gaps")

    print()
    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print()

    if export_tonnage_coverage < 90 or import_tonnage_coverage < 90:
        print("Issues to address:")
        if export_tonnage_coverage < 90:
            print(f"  - {100-export_tonnage_coverage:.1f}% of export tonnage lacks prices")
            print(f"    Consider: Use revenue_usd from all_data.xlsx as fallback?")
        if import_tonnage_coverage < 90:
            print(f"  - {100-import_tonnage_coverage:.1f}% of import tonnage lacks costs")
            print(f"    Consider: Use price_usd_per_tonne as fallback for imports without costs?")
    else:
        print("✓ Data quality is sufficient to proceed with merge")

    print()
    print("="*80)

    return {
        'export_coverage': export_coverage,
        'import_coverage': import_coverage,
        'export_tonnage_coverage': export_tonnage_coverage,
        'import_tonnage_coverage': import_tonnage_coverage,
        'potential_export_revenue': potential_export_revenue,
        'potential_import_cost': potential_import_cost
    }


if __name__ == '__main__':
    try:
        results = check_price_coverage()
        print("\n✓ Validation complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
