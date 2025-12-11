#!/usr/bin/env python3
"""
Update Water Data in all_data.xlsx

This script merges updated water usage data from the multi-sheet
combined_water_totals_by_stage.xlsx file into all_data.xlsx.

The water file has 4 sheets corresponding to constraint types:
- country_unconstrained
- country_constrained
- region_unconstrained
- region_constrained

Usage:
    python update_water_data.py

Or with custom paths:
    python update_water_data.py --water-file <path> --all-data <path> --output <path>
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path

# Load configuration
def load_config():
    """Load path configuration from config.json"""
    config_path = Path(__file__).parent.parent.parent / 'config.json'
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"config.json not found at {config_path}")


def merge_updated_water_data(water_file, all_data_file, output_file):
    """
    Merge updated water usage data from multi-sheet Excel file into all_data.xlsx

    Args:
        water_file: Path to combined_water_totals_by_stage.xlsx
        all_data_file: Path to all_data.xlsx
        output_file: Path to save updated all_data.xlsx

    Returns:
        pd.DataFrame: Updated all_data with new water values
    """

    print("="*60)
    print("WATER DATA UPDATE SCRIPT")
    print("="*60)

    # Step 1: Load all water sheets and add constraint column
    print("\nStep 1: Loading water data from all sheets...")
    sheets = {
        'country_unconstrained': 'country_unconstrained',
        'country_constrained': 'country_constrained',
        'region_unconstrained': 'region_unconstrained',
        'region_constrained': 'region_constrained'
    }

    water_dfs = []
    for sheet_name, constraint_value in sheets.items():
        df = pd.read_excel(water_file, sheet_name=sheet_name)

        # Forward fill hierarchical grouping columns
        # (water file has hierarchical structure where scenario/mineral/country
        # are listed once, then multiple processing stages follow)
        df[['year', 'scenario', 'reference_mineral', 'iso3']] = \
            df[['year', 'scenario', 'reference_mineral', 'iso3']].ffill()

        # Remove rows with missing processing_stage
        df = df.dropna(subset=['processing_stage'])

        # Add constraint column based on sheet name
        df['constraint'] = constraint_value

        water_dfs.append(df)
        print(f"  {sheet_name}: {len(df)} rows")

    # Combine all sheets
    df_water = pd.concat(water_dfs, ignore_index=True)
    print(f"\nTotal water rows: {len(df_water)}")
    print(f"Unique scenarios: {df_water['scenario'].nunique()}")
    print(f"Unique constraints: {sorted(df_water['constraint'].unique())}")

    # Step 2: Load all_data
    print("\nStep 2: Loading all_data.xlsx...")
    df_all = pd.read_excel(all_data_file)
    print(f"  Rows: {len(df_all)}, Columns: {len(df_all.columns)}")
    print(f"  Scenarios: {df_all['scenario'].nunique()}")
    print(f"  Constraints: {sorted(df_all['constraint'].unique())}")

    # Step 3: Define join keys and water columns to update
    # Include all identifying columns to avoid duplication with suffixes
    join_keys = [
        'scenario',
        'constraint',
        'iso3',
        'reference_mineral',
        'processing_stage',
        'processing_type',  # Important: prevents processing_type_old/_new
        'year'               # Important: prevents year_old/_new
    ]

    water_cols = [
        'water_usage_m3',
        'water_intensity_m3_per_kg',
        'production_tonnes_for_water'
    ]

    print(f"\nStep 3: Merge configuration")
    print(f"  Join keys ({len(join_keys)}): {join_keys}")
    print(f"  Columns to update: {water_cols}")

    # Step 4: Merge - LEFT JOIN to preserve all all_data rows
    print("\nStep 4: Merging data...")
    df_merged = pd.merge(
        df_all,
        df_water[join_keys + water_cols],
        on=join_keys,
        how='left',
        suffixes=('_old', '_new'),
        indicator=True
    )

    # Step 5: Report merge statistics
    print("\nStep 5: Merge statistics:")
    print(f"  Total rows after merge: {len(df_merged)}")

    matched_count = (df_merged['_merge'] == 'both').sum()
    left_only_count = (df_merged['_merge'] == 'left_only').sum()

    print(f"  Matched rows (will be updated): {matched_count}")
    print(f"  Unmatched rows (will remain unchanged): {left_only_count}")

    # Match rate by constraint
    print("\n  Match rate by constraint:")
    for constraint in sorted(df_all['constraint'].unique()):
        all_count = (df_all['constraint'] == constraint).sum()
        matched_constraint = ((df_merged['constraint'] == constraint) &
                             (df_merged['_merge'] == 'both')).sum()
        pct = matched_constraint/all_count*100 if all_count > 0 else 0
        print(f"    {constraint}: {matched_constraint}/{all_count} ({pct:.1f}%)")

    # Step 6: Update water columns
    print("\nStep 6: Updating water columns...")
    updates_applied = {}

    for col in water_cols:
        col_new = f'{col}_new'
        col_old = f'{col}_old' if f'{col}_old' in df_merged.columns else col

        # Count how many values will change
        if col_new in df_merged.columns:
            changes = df_merged[col_new].notna().sum()
            updates_applied[col] = changes

            # Use new value if available, otherwise keep old value
            df_merged[col] = df_merged[col_new].fillna(df_merged[col_old])

            # Drop the suffixed columns
            df_merged.drop(columns=[col_new], inplace=True)
            if col_old in df_merged.columns and col_old != col:
                df_merged.drop(columns=[col_old], inplace=True)

        print(f"  {col}: {updates_applied.get(col, 0)} values updated")

    # Step 7: Drop merge indicator
    df_merged.drop(columns=['_merge'], inplace=True)

    # Step 8: Determine final column order
    # Keep original columns in order, then add any new columns at the end
    existing_cols = [col for col in df_all.columns if col in df_merged.columns]
    new_cols = [col for col in df_merged.columns if col not in df_all.columns]
    final_col_order = existing_cols + new_cols
    df_final = df_merged[final_col_order]

    # Step 9: Validation
    print("\nStep 9: Validation checks:")

    # Check row count
    assert df_final.shape[0] == df_all.shape[0], \
        f"ERROR: Row count mismatch: {df_final.shape[0]} != {df_all.shape[0]}"
    print(f"  ✓ Row count preserved: {len(df_final)}")

    # Check column count
    expected_col_count = len(df_all.columns) + len([c for c in water_cols if c not in df_all.columns])
    if df_final.shape[1] != expected_col_count:
        print(f"  ℹ Column count changed: {len(df_all.columns)} → {df_final.shape[1]} (+{df_final.shape[1] - len(df_all.columns)} new columns)")
    else:
        print(f"  ✓ Column count: {len(df_final.columns)}")

    # Check that all original columns are present
    missing_cols = set(df_all.columns) - set(df_final.columns)
    if missing_cols:
        print(f"  ✗ ERROR: Missing columns: {missing_cols}")
    else:
        print(f"  ✓ All original columns preserved")

    # Check for unexpected NaN introduction (only for columns that existed before)
    nan_issues = []
    new_columns = []
    for col in water_cols:
        if col in df_all.columns:
            nan_before = df_all[col].isna().sum()
            nan_after = df_final[col].isna().sum()
            if nan_after > nan_before:
                nan_issues.append(f"    WARNING: {col} has {nan_after - nan_before} new NaN values")
        else:
            new_columns.append(col)

    if nan_issues:
        print("  ⚠ NaN value changes:")
        for issue in nan_issues:
            print(issue)
    else:
        print("  ✓ No unexpected NaN values introduced")

    if new_columns:
        print(f"  ℹ New columns added: {', '.join(new_columns)}")

    # Compare sample values
    print("\n  Sample value comparison (scenario=2022_baseline, iso3=COD, mineral=cobalt, stage=1.0):")
    sample_mask = (
        (df_all['scenario'] == '2022_baseline') &
        (df_all['iso3'] == 'COD') &
        (df_all['reference_mineral'] == 'cobalt') &
        (df_all['processing_stage'] == 1.0)
    )
    if sample_mask.any():
        old_val = df_all.loc[sample_mask, 'water_usage_m3'].values[0]
        new_val = df_final.loc[sample_mask, 'water_usage_m3'].values[0]
        print(f"    Old: {old_val:.2f}")
        print(f"    New: {new_val:.2f}")
        print(f"    Difference: {new_val - old_val:.2f} ({(new_val/old_val-1)*100:.2f}%)")

    # Step 10: Save updated file
    print(f"\nStep 10: Saving updated data...")
    print(f"  Output file: {output_file}")
    df_final.to_excel(output_file, index=False)
    print(f"  ✓ Saved successfully ({df_final.shape[0]} rows, {df_final.shape[1]} columns)")

    # Step 11: Summary report
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total rows in all_data: {len(df_all)}")
    print(f"Rows with updated water data: {matched_count}")
    print(f"Percentage updated: {matched_count/len(df_all)*100:.1f}%")
    print(f"Rows unchanged: {left_only_count}")
    print(f"\nOutput saved to: {output_file}")
    print("="*60)

    return df_final


def main():
    """Main execution function"""

    # Parse command line arguments (simple version)
    import argparse
    parser = argparse.ArgumentParser(
        description='Update water data in all_data.xlsx from combined_water_totals_by_stage.xlsx'
    )
    parser.add_argument(
        '--water-file',
        type=str,
        default=None,
        help='Path to combined_water_totals_by_stage.xlsx'
    )
    parser.add_argument(
        '--all-data',
        type=str,
        default=None,
        help='Path to all_data.xlsx'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path for output file (default: all_data_updated.xlsx in same directory as all_data)'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Using default paths relative to transport-outputs directory")
        config = {}

    # Determine file paths
    if args.water_file:
        water_file = args.water_file
    else:
        results_path = config.get('paths', {}).get('results', '../transport-outputs/results')
        water_file = os.path.join(results_path, 'water_usage_summaries', 'combined_water_totals_by_stage.xlsx')

    if args.all_data:
        all_data_file = args.all_data
    else:
        results_path = config.get('paths', {}).get('results', '../transport-outputs/results')
        all_data_file = os.path.join(results_path, 'all_data.xlsx')

    if args.output:
        output_file = args.output
    else:
        # Place output in same directory as all_data
        all_data_dir = os.path.dirname(all_data_file)
        output_file = os.path.join(all_data_dir, 'all_data_updated.xlsx')

    # Check input files exist
    if not os.path.exists(water_file):
        print(f"ERROR: Water file not found: {water_file}")
        sys.exit(1)

    if not os.path.exists(all_data_file):
        print(f"ERROR: all_data file not found: {all_data_file}")
        sys.exit(1)

    # Run the merge
    try:
        df_updated = merge_updated_water_data(water_file, all_data_file, output_file)
        print("\n✓ Water data update completed successfully!")
        return 0
    except Exception as e:
        print(f"\n✗ ERROR: Water data update failed!")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
