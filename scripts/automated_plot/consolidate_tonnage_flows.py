#!/usr/bin/env python3
"""
Consolidate tonnage_summaries CSVs into single Excel workbook

This script reads all combined_location_totals_*.csv files from the
tonnage_summaries folder and consolidates them into a single Excel file
with separate sheets per scenario.

Key features:
- Extracts scenario and constraint information from filenames
- Adds 'scenario' and 'constraint' columns to each dataframe
- Creates summary statistics sheet
- Handles all 37 scenario files

Usage:
    python consolidate_tonnage_flows.py
"""

import pandas as pd
import os
import json
from pathlib import Path
import re


def parse_filename(filename):
    """
    Parse filename to extract scenario and constraint.

    Filename format:
    combined_location_totals_{scenario}_{constraint}.csv

    Where constraint is one of:
    - country_unconstrained
    - country_constrained
    - region_unconstrained
    - region_constrained

    Args:
        filename: CSV filename

    Returns:
        tuple: (scenario_name, constraint_type)
    """
    # Remove prefix and extension
    name = filename.replace('combined_location_totals_', '').replace('.csv', '')

    # Extract constraint (last part after underscore)
    # Possible constraints: country_unconstrained, country_constrained,
    #                       region_unconstrained, region_constrained
    constraint_patterns = [
        'country_unconstrained',
        'country_constrained',
        'region_unconstrained',
        'region_constrained'
    ]

    constraint = None
    scenario = None

    for pattern in constraint_patterns:
        if name.endswith(pattern):
            constraint = pattern
            scenario = name[:-len(pattern)-1]  # Remove constraint and trailing underscore
            break

    if constraint is None:
        # Fallback if pattern doesn't match
        print(f"Warning: Could not parse constraint from {filename}")
        constraint = 'unknown'
        scenario = name

    return scenario, constraint


def consolidate_tonnage_flows():
    """
    Main consolidation function.

    Reads all combined_location_totals CSV files, adds scenario/constraint columns,
    and writes to a single Excel workbook with one sheet per scenario-constraint combo.
    """
    # Load config
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / 'config.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    input_path = Path(config['paths']['results']) / 'tonnage_summaries'
    output_file = Path(config['paths']['results']) / 'tonnage_flows_comprehensive.xlsx'

    print("="*80)
    print("TONNAGE FLOWS CONSOLIDATION")
    print("="*80)
    print(f"Input directory: {input_path}")
    print(f"Output file: {output_file}")
    print()

    # Find all combined_location_totals CSV files
    csv_files = sorted([f for f in os.listdir(input_path)
                       if f.startswith('combined_location_totals') and f.endswith('.csv')])

    print(f"Found {len(csv_files)} CSV files to process")
    print()

    # Storage for summary data
    all_data = []
    summary_stats = []

    # Process each CSV file
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for i, filename in enumerate(csv_files, 1):
            print(f"[{i}/{len(csv_files)}] Processing: {filename}")

            # Parse filename to get scenario and constraint
            scenario, constraint = parse_filename(filename)
            print(f"  Scenario: {scenario}")
            print(f"  Constraint: {constraint}")

            # Read CSV
            df = pd.read_csv(input_path / filename)

            # Add scenario and constraint columns at the beginning
            df.insert(0, 'scenario', scenario)
            df.insert(1, 'constraint', constraint)

            print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")

            # Store for combined sheet
            all_data.append(df)

            # Calculate summary statistics (absolute tonnages only)
            summary = {
                'scenario': scenario,
                'constraint': constraint,
                'total_rows': len(df),
                'total_initial_stage_tonnes': df['initial_stage_production_tons'].sum(),
                'total_final_stage_tonnes': df['final_stage_production_tons'].sum(),
                'export_tonnes': df[df['trade_type'] == 'Export']['initial_stage_production_tons'].sum() if 'Export' in df['trade_type'].values else 0,
                'domestic_tonnes': df[df['trade_type'] == 'Domestic']['initial_stage_production_tons'].sum() if 'Domestic' in df['trade_type'].values else 0,
                'import_CCG_tonnes': df[df['trade_type'] == 'Import_CCG']['initial_stage_production_tons'].sum() if 'Import_CCG' in df['trade_type'].values else 0,
                'import_NonCCG_tonnes': df[df['trade_type'] == 'Import_NonCCG']['initial_stage_production_tons'].sum() if 'Import_NonCCG' in df['trade_type'].values else 0,
                'other_tonnes': df[df['trade_type'] == 'Other']['initial_stage_production_tons'].sum() if 'Other' in df['trade_type'].values else 0,
                'unique_countries': df['iso3'].nunique(),
                'unique_minerals': df['reference_mineral'].nunique(),
                'unique_stage_transitions': len(df.groupby(['initial_processing_stage', 'final_processing_stage'])),
                'avg_cost_per_tonne': df['average_gcost_usd_per_tons'].mean(),
                'total_cost_usd': df['total_gcosts_usd'].sum()
            }
            summary_stats.append(summary)

            # Create sheet name (Excel limit: 31 characters)
            # Format: {scenario_short}_{constraint_short}
            sheet_name = f"{scenario[:20]}_{constraint[:8]}"

            # Truncate if still too long
            if len(sheet_name) > 31:
                sheet_name = sheet_name[:31]

            # Write to Excel sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  ✓ Written to sheet: {sheet_name}")
            print()

        # Create combined 'All_Data' sheet with all scenarios
        print("Creating combined 'All_Data' sheet...")
        df_all = pd.concat(all_data, ignore_index=True)
        print(f"  Total rows: {len(df_all)}")
        print(f"  Total columns: {len(df_all.columns)}")
        df_all.to_excel(writer, sheet_name='All_Data', index=False)
        print("  ✓ All_Data sheet created")
        print()

        # Create summary sheet
        print("Creating 'Summary' sheet...")
        df_summary = pd.DataFrame(summary_stats)

        # Reorder columns for clarity
        column_order = [
            'scenario', 'constraint', 'total_rows',
            'total_initial_stage_tonnes', 'total_final_stage_tonnes',
            'export_tonnes', 'domestic_tonnes',
            'import_CCG_tonnes', 'import_NonCCG_tonnes', 'other_tonnes',
            'unique_countries', 'unique_minerals', 'unique_stage_transitions',
            'avg_cost_per_tonne', 'total_cost_usd'
        ]
        df_summary = df_summary[column_order]

        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        print(f"  Summary rows: {len(df_summary)}")
        print("  ✓ Summary sheet created")
        print()

    print("="*80)
    print("CONSOLIDATION COMPLETE")
    print("="*80)
    print(f"Output file: {output_file}")
    print(f"Total sheets: {len(csv_files) + 2} (scenarios + All_Data + Summary)")
    print(f"Total rows in All_Data: {len(df_all)}")
    print(f"File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("Constraint types found:")
    for constraint in df_summary['constraint'].unique():
        count = (df_summary['constraint'] == constraint).sum()
        print(f"  - {constraint}: {count} scenarios")
    print()
    print("Trade type summary (All_Data):")
    trade_summary = df_all.groupby('trade_type')['initial_stage_production_tons'].sum() / 1e6
    for trade_type in sorted(trade_summary.index):
        print(f"  - {trade_type}: {trade_summary[trade_type]:.2f} Mt")
    print()
    print("✓ Consolidation successful!")

    return output_file


def main():
    """Entry point"""
    try:
        output_file = consolidate_tonnage_flows()
        return 0
    except Exception as e:
        print(f"✗ Error during consolidation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
