import pandas as pd
import os
from pandas import ExcelWriter
import json
import sys

# Add the automated_plot directory to the path to import plot_config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'automated_plot'))
from plot_config import get_target_stage_for_goal, mineral_processing_stages
from plot_emissions_water_all_countries import calc_value_added_simple

# Define the policy pair mapping: country -> region
POLICY_MATCHES = {
    'mid_min': 'mid_max',
    'low_min': 'low_max',
    'high_min': 'high_max'
}

def pct_change_between_both(df, constraint_1, constraint_2, value_cols):
    df1 = df[df['constraint'] == constraint_1].copy()
    df2 = df[df['constraint'] == constraint_2].copy()

    def extract_tag_year(scenario: str):
        parts = scenario.split('_')
        year = parts[0] if parts[0].isdigit() else None
        tag = None
        for ptag in list(POLICY_MATCHES.keys()) + list(POLICY_MATCHES.values()):
            if ptag in scenario:
                tag = ptag
                break
        return pd.Series([year, tag])

    df1[['year', 'tag']] = df1['scenario'].apply(extract_tag_year)
    df2[['year', 'tag']] = df2['scenario'].apply(extract_tag_year)

    rows = []

    for base_tag, comp_tag in POLICY_MATCHES.items():
        # --- Same-year comparisons ---
        common_years = sorted(set(df1['year'].dropna()) & set(df2['year'].dropna()))
        for year in common_years:
            r1 = df1[(df1['year'] == year) & (df1['tag'] == base_tag)]
            r2 = df2[(df2['year'] == year) & (df2['tag'] == comp_tag)]

            for _, row1 in r1.iterrows():
                for _, row2 in r2.iterrows():
                    result = {
                        'scenario': f"{row1['scenario']}_vs_{row2['scenario']}",
                        'constraint': f"pct_change_{constraint_1.split('_')[0]}"
                    }
                    for col in value_cols:
                        val1 = row1.get(col, 0)
                        val2 = row2.get(col, 0)
                        result[col] = ((val2 / val1) * 100) - 100 if val1 else None
                    rows.append(result)


        # --- Cross-year comparisons (2030 → 2040) ---
        for year in sorted(df1['year'].dropna().unique()):
            y1 = year
            y2 = str(int(year) + 10)
            r1 = df1[(df1['year'] == y1) & (df1['tag'] == base_tag)]
            r2 = df2[(df2['year'] == y2) & (df2['tag'] == comp_tag)]

            for _, row1 in r1.iterrows():
                for _, row2 in r2.iterrows():
                    result = {
                        'scenario': f"{row1['scenario']}_vs_{row2['scenario']}",
                        'constraint': f"pct_change_{constraint_1.split('_')[0]}"
                    }
                    for col in value_cols:
                        val1 = row1.get(col, 0)
                        val2 = row2.get(col, 0)
                        result[col] = ((val2 / val1) * 100) - 100 if val1 else None
                    rows.append(result)

    return pd.DataFrame(rows)

def create_pivot_with_pct_change(df, value_column, unit_label, conversion_factor=1.0, to_kt=False):
    import pandas as pd

    df = df.copy()
    col_converted = f"{value_column}_converted"
    factor = 1e3 if to_kt else conversion_factor
    df.loc[:, col_converted] = df[value_column] / factor

    # Create the pivot table
    pivot = df.pivot_table(
        index=['scenario', 'constraint'],
        columns='reference_mineral',
        values=col_converted,
        aggfunc='sum',
        fill_value=0
    )

    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.reset_index()

    # Filter only numeric columns to compute percentage change safely
    value_cols = [
        col for col in pivot.columns
        if col not in ['scenario', 'constraint']
        and pd.api.types.is_numeric_dtype(pivot[col])
    ]

    # Compute percentage change between valid policy-tagged pairs
    pct_constrained = pct_change_between_both(pivot, 'country_constrained', 'region_constrained', value_cols)
    pct_unconstrained = pct_change_between_both(pivot, 'country_unconstrained', 'region_unconstrained', value_cols)

    # DEBUG: Confirm rows are returned
    # print("\n✅ % Change (Constrained):")
    # print(pct_constrained.head())
    # print("\n✅ % Change (Unconstrained):")
    # print(pct_unconstrained.head())

    # Combine all rows
    result = pd.concat([pivot, pct_constrained, pct_unconstrained], ignore_index=True)

    # DEBUG: Final preview
    # print("\n✅ Final combined result (first 5 rows):")
    # print(result.head())

    return result

# Specialized pivot creators using the generic logic
def create_total_costs_by_mineral(df, to_kt=False):
    return create_pivot_with_pct_change(df, 'all_cost_usd', 'total_costs_musd', conversion_factor=1e6, to_kt=to_kt)

def create_revenue_by_mineral(df, to_kt=False):
    return create_pivot_with_pct_change(df, 'revenue_usd', 'revenue_musd', conversion_factor=1e6, to_kt=to_kt)

def create_value_added_by_mineral(df, to_kt=False):
    df_filtered = df[df["processing_stage"] > 0].copy()

    if to_kt:
        df_filtered["production_tonnes"] = df_filtered["production_tonnes"] / 1e3

    # Import route-based calculation
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'automated_plot'))
    from plot_emissions_water_all_countries import calc_value_added_with_routes, calc_value_added_simple
    
    # Route-based value addition calculation
    df_va = df_filtered.groupby(
        ['scenario', 'constraint', 'iso3', 'reference_mineral']
    ).apply(calc_value_added_with_routes).reset_index(drop=True)

    df_va['value_added_musd'] = df_va['value_added'] / 1e6

    # Simple value addition calculation
    df_va_simple = df_filtered.groupby(
        ['scenario', 'constraint', 'iso3', 'reference_mineral']
    ).apply(calc_value_added_simple).reset_index(drop=True)

    df_va_simple['value_added_simple_musd'] = df_va_simple['value_added_simple'] / 1e6

    # Merge both calculations
    df_va = df_va.merge(
        df_va_simple[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 'value_added_simple', 'value_added_simple_musd']],
        on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage'],
        how='outer'
    )

    # Return route-based value addition (keeping existing behavior)
    return create_pivot_with_pct_change(df_va, 'value_added', 'value_added_musd', conversion_factor=1e6, to_kt=to_kt)

def create_value_added_simple_by_mineral(df, to_kt=False):
    # Don't filter out stage 0 - the calc_value_added_simple function needs all stages
    df_copy = df.copy()
    if to_kt:
        df_copy["production_tonnes"] = df_copy["production_tonnes"] / 1e3

    # Import simple value addition calculation
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'automated_plot'))
    from plot_emissions_water_all_countries import calc_value_added_simple
    
    # Simple value addition calculation - use full dataset
    df_va_simple = df_copy.groupby(
        ['scenario', 'constraint', 'iso3', 'reference_mineral']
    ).apply(calc_value_added_simple).reset_index(drop=True)

    # Filter to only non-stage-0 results for the pivot (since stage 0 has no value addition)
    df_filtered = df_va_simple[df_va_simple["processing_stage"] > 0].copy()
    df_filtered['value_added_simple_musd'] = df_filtered['value_added_simple'] / 1e6

    return create_pivot_with_pct_change(df_filtered, 'value_added_simple', 'value_added_simple_musd', conversion_factor=1e6, to_kt=to_kt)

def create_transport_emissions_by_mineral(df, to_kt=False):
    return create_pivot_with_pct_change(df, 'transport_total_tonsCO2eq', 'transport_emissions_MtCO2e', conversion_factor=1e6, to_kt=to_kt)

def create_energy_emissions_by_mineral(df, to_kt=False):
    return create_pivot_with_pct_change(df, 'energy_tonsCO2eq', 'energy_emissions_MtCO2e', conversion_factor=1e6, to_kt=to_kt)

def create_transport_volume_by_mineral(df, to_kt=False):
    return create_pivot_with_pct_change(df, 'transport_total_tonkm', 'transport_volume_million_ton_km', conversion_factor=1e6, to_kt=to_kt)

def create_energy_capacity_by_mineral(df, to_kt=False):
    return create_pivot_with_pct_change(df, 'energy_req_capacity_kW', 'energy_capacity_GW', conversion_factor=1e6, to_kt=to_kt)

def create_water_use_by_mineral(df, to_kt=False):
    return create_pivot_with_pct_change(df, 'water_usage_m3', 'water_use_million_m3', conversion_factor=1e6, to_kt=to_kt)

# Existing table generators for non-mineral-pivoted outputs
def create_metal_content_table(df, to_kt=False):
    df_stage0 = df[df['processing_stage'] == 0].copy()
    factor = 1e3 if to_kt else 1e6
    df_stage0['metal_content'] = df_stage0['production_tonnes'] / factor

    pivot = df_stage0.pivot_table(
        index=['scenario', 'constraint'],
        columns='reference_mineral',
        values='metal_content',
        aggfunc='sum',
        fill_value=0
    )
    pivot['Total'] = pivot.sum(axis=1)
    pivot_reset = pivot.reset_index()

    value_cols = [col for col in pivot_reset.columns if col not in ['scenario', 'constraint']]

    try:
        pct_c = pct_change_between_both(pivot_reset, 'country_constrained', 'region_constrained', value_cols)
        pct_u = pct_change_between_both(pivot_reset, 'country_unconstrained', 'region_unconstrained', value_cols)
        result = pd.concat([pivot_reset, pct_c, pct_u], ignore_index=True)
    except Exception as e:
        print("Failed to compute % change in metal content:", e)
        result = pivot_reset.copy()
        result['error'] = str(e)

    return result


def create_unit_cost_table(df):
    df = df[df['processing_stage'] != 0].copy()

    # Base: cost per processing type
    base = df.pivot_table(
        index=['scenario', 'constraint', 'processing_type'],
        columns='reference_mineral',
        values='production_transport_energy_unit_cost_usd_per_tonne',
        aggfunc='mean',
        fill_value=0
    ).reset_index()
    base['Total'] = base.drop(columns=['scenario', 'constraint', 'processing_type']).mean(axis=1)

    # All processing types combined
    all_types = df.pivot_table(
        index=['scenario', 'constraint'],
        columns='reference_mineral',
        values='production_transport_energy_unit_cost_usd_per_tonne',
        aggfunc='mean',
        fill_value=0
    ).reset_index()
    all_types['processing_type'] = 'all'
    all_types['Total'] = all_types.drop(columns=['scenario', 'constraint', 'processing_type']).mean(axis=1)

    # Combine and compute % change
    combined = pd.concat([base, all_types], ignore_index=True)

    value_cols = [col for col in combined.columns if col not in ['scenario', 'constraint', 'processing_type']]

    try:
        pct_c = pct_change_between_both(combined, 'country_constrained', 'region_constrained', value_cols)
        pct_u = pct_change_between_both(combined, 'country_unconstrained', 'region_unconstrained', value_cols)
        result = pd.concat([combined, pct_c, pct_u], ignore_index=True)
    except Exception as e:
        print("Failed to compute % change in unit costs:", e)
        result = combined.copy()
        result['error'] = str(e)

    return result


def create_production_table(df, to_kt=False):
    df = df[df['processing_stage'] != 0].copy()
    factor = 1e3 if to_kt else 1e6
    df['production'] = df['production_tonnes'] / factor
    pivot = df.pivot_table(
        index=['scenario', 'constraint', 'processing_stage', 'year'],
        columns='reference_mineral',
        values='production',
        aggfunc='sum',
        fill_value=0
    )
    pivot['Total'] = pivot.sum(axis=1)
    return pivot.reset_index()

def create_production_by_type_table(df, to_kt=False):
    df = df[df['processing_stage'] != 0].copy()
    factor = 1e3 if to_kt else 1e6
    df['production'] = df['production_tonnes'] / factor
    pivot = df.pivot_table(
        index=['scenario', 'constraint', 'processing_type', 'year'],
        columns='reference_mineral',
        values='production',
        aggfunc='sum',
        fill_value=0
    )
    pivot['Total'] = pivot.sum(axis=1)
    return pivot.reset_index()

def create_revenue_tables(df, to_kt=False):
    df = df.copy()
    factor = 1e3 if to_kt else 1e6
    df['revenue_musd'] = df['revenue_usd'] / factor

    # Create flat summary
    pivot = df.pivot_table(index=['scenario', 'constraint'], values='revenue_musd', aggfunc='sum').reset_index()
    main = pivot.pivot(index='scenario', columns='constraint', values='revenue_musd').fillna(0)

    def safe_pct_change(region, country):
        if country == 0 and region == 0:
            return 0
        elif country == 0:
            return None  # or np.nan
        else:
            return round((region / country * 100) - 100, 2)

    main['pct_change_constrained'] = main.apply(
        lambda row: safe_pct_change(row.get('region_constrained', 0), row.get('country_constrained', 0)), axis=1
    )
    main['pct_change_unconstrained'] = main.apply(
        lambda row: safe_pct_change(row.get('region_unconstrained', 0), row.get('country_unconstrained', 0)), axis=1
    )

    # Create breakdown by processing type
    by_type = df.pivot_table(index=['scenario', 'processing_type'], values='revenue_musd', aggfunc='sum').reset_index()

    return main.reset_index(), by_type


def calc_value_added(group):
    group = group.sort_values(by='processing_stage').copy()
    group["value_added"] = 0.0
    for i in range(1, len(group)):
        prev = group.iloc[i - 1]
        curr = group.iloc[i]
        # Use production_tonnes for value addition calculations (total domestic economic impact)
        if prev["production_tonnes"] > 0:
            group.at[curr.name, "value_added"] = (
                (curr["price_usd_per_tonne"] * curr["production_tonnes"]) -
                (prev["production_cost_usd_per_tonne"] * prev["production_tonnes"])
            )
    return group

def create_value_added_totals_legacy(df, to_kt=False):
    # Filter out processing_stage 0
    df = df[df["processing_stage"] > 0].copy()

    if to_kt:
        df["production_tonnes"] = df["production_tonnes"] / 1e3

    df["value_added"] = 0.0

    # Import route-based calculation
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'automated_plot'))
    from plot_emissions_water_all_countries import calc_value_added_with_routes, calc_value_added_simple
    
    # Apply route-based value addition calculation
    df_route = df.groupby(["scenario", "constraint", "iso3", "reference_mineral"]) \
           .apply(calc_value_added_with_routes).reset_index(drop=True)

    # Apply simple value addition calculation
    df_simple = df.groupby(["scenario", "constraint", "iso3", "reference_mineral"]) \
           .apply(calc_value_added_simple).reset_index(drop=True)

    # Merge both calculations
    df = df_route.merge(
        df_simple[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 'value_added_simple']],
        on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage'],
        how='outer'
    )

    # Convert to million USD
    df["value_added_musd"] = df["value_added"] / 1e6
    df["value_added_simple_musd"] = df["value_added_simple"] / 1e6

    # Aggregate total value added per scenario + constraint
    summary = df.groupby(["scenario", "constraint"])["value_added_musd"].sum().reset_index()

    # Pivot to wide format
    main = summary.pivot(index="scenario", columns="constraint", values="value_added_musd").fillna(0)

    # Calculate percentage changes
    main["pct_change_constrained"] = (
        (main.get("region_constrained", 0) / main.get("country_constrained", 1)) * 100 - 100
    )
    main["pct_change_unconstrained"] = (
        (main.get("region_unconstrained", 0) / main.get("country_unconstrained", 1)) * 100 - 100
    )

    return main.reset_index()

def create_value_added_tables(df, to_kt=False):
    # Only consider rows with processing_stage > 0
    df = df[df["processing_stage"] > 0].copy()

    # Handle unit conversion for production if needed
    df['production_tonnes'] = df['production_tonnes'] / (1e3 if to_kt else 1)
    df['value_added'] = 0.0

    # Import route-based calculation
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'automated_plot'))
    from plot_emissions_water_all_countries import calc_value_added_with_routes, calc_value_added_simple
    
    # Apply route-based value addition calculation
    df_route = df.groupby(
        ['scenario', 'constraint', 'iso3', 'reference_mineral']
    ).apply(calc_value_added_with_routes).reset_index(drop=True)

    # Apply simple value addition calculation  
    df_simple = df.groupby(
        ['scenario', 'constraint', 'iso3', 'reference_mineral']
    ).apply(calc_value_added_simple).reset_index(drop=True)

    # Merge both calculations
    df = df_route.merge(
        df_simple[['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage', 'value_added_simple']],
        on=['scenario', 'constraint', 'iso3', 'reference_mineral', 'processing_stage'],
        how='outer'
    )

    # Convert to million USD
    df['value_added_musd'] = df['value_added'] / 1e6
    df['value_added_simple_musd'] = df['value_added_simple'] / 1e6

    # Create main summary: total value added per scenario + constraint
    pivot = df.pivot_table(
        index=['scenario', 'constraint'],
        values='value_added_musd',
        aggfunc='sum'
    ).reset_index()

    # Pivot to wide format
    main = pivot.pivot(
        index='scenario',
        columns='constraint',
        values='value_added_musd'
    ).fillna(0)

    # Add percentage changes
    main['pct_change_constrained'] = (
        (main.get('region_constrained', 0) / main.get('country_constrained', 1)) * 100 - 100
    )
    main['pct_change_unconstrained'] = (
        (main.get('region_unconstrained', 0) / main.get('country_unconstrained', 1)) * 100 - 100
    )

    # By processing_type
    by_type = df.pivot_table(
        index=['scenario', 'processing_type'],
        values='value_added_musd',
        aggfunc='sum'
    ).reset_index()

    return main.reset_index(), by_type

def create_single_metric_table(df, col, unit_label):
    df = df.copy()
    new_col = f'{col}_converted'
    conversions = {
        'transport_total_tonsCO2eq': 1e6,
        'energy_tonsCO2eq': 1e6,
        'transport_total_tonkm': 1e6,
        'energy_req_capacity_kW': 1e6,
        'water_usage_m3': 1e6
    }
    df[new_col] = df[col] / conversions[col]
    pivot = df.pivot_table(index=['scenario', 'constraint'], values=new_col, aggfunc='sum').reset_index()
    pivot.columns = ['scenario', 'constraint', unit_label]
    return pivot

def create_normalized_revenue_table_by_stage_and_type(df, to_kt=False):
    df = df.copy()
    # Filter for processing stages > 0 AND production_tonnes_for_costs > 0 (economically viable production)
    df = df[(df["processing_stage"] > 0) & (df["production_tonnes_for_costs"] > 0)]

    group_cols = [
        "scenario", "constraint", "processing_stage", "processing_type", "reference_mineral"
    ]

    grouped = df.groupby(group_cols).agg({
        "revenue_usd": "sum",
        "production_tonnes_for_costs": "sum"  # CORRECTED: Use production_tonnes_for_costs
    }).reset_index()

    # CORRECTED: Normalize by economically viable production, not total production capacity
    grouped["norm_revenue"] = grouped["revenue_usd"] / grouped["production_tonnes_for_costs"]

    # CORRECTED: Use production-weighted aggregation instead of simple mean
    # Group by processing_type (not stage) and calculate weighted average across stages
    final_grouped = grouped.groupby(["processing_type", "scenario", "constraint", "reference_mineral"]).apply(
        lambda x: (x["revenue_usd"].sum() / x["production_tonnes_for_costs"].sum()) if x["production_tonnes_for_costs"].sum() > 0 else 0
    ).reset_index(name="norm_revenue_weighted")

    pivot = final_grouped.pivot_table(
        index=["processing_type", "scenario", "constraint"],
        columns="reference_mineral", 
        values="norm_revenue_weighted",
        fill_value=0
    ).reset_index()

    # Calculate total as sum (weighted by mineral production within each processing type)
    mineral_cols = [col for col in pivot.columns if col not in ["processing_type", "scenario", "constraint"]]
    pivot["Total"] = pivot[mineral_cols].sum(axis=1)

    return pivot

def create_normalized_value_added_table_by_stage_and_type(df, to_kt=False):
    df = df.copy()
    # Filter for processing stages > 0 AND production_tonnes > 0 (total domestic production)
    df = df[(df["processing_stage"] > 0) & (df["production_tonnes"] > 0)]

    if "value_added" not in df.columns:
        # Calculate value added using production_tonnes (total domestic production)
        df["value_added"] = (
            df["price_usd_per_tonne"] * df["production_tonnes"]
            - df["production_cost_usd_per_tonne"] * df["production_tonnes"]
        )

    group_cols = [
        "scenario", "constraint", "processing_stage", "processing_type", "reference_mineral"
    ]

    grouped = df.groupby(group_cols).agg({
        "value_added": "sum",
        "production_tonnes": "sum"  # Use production_tonnes for normalization
    }).reset_index()

    # Normalize by total domestic production (value added per tonne of total production)
    grouped["norm_value_added"] = grouped["value_added"] / grouped["production_tonnes"]

    # Production-weighted aggregation
    # Group by processing_type (not stage) and calculate weighted average across stages
    final_grouped = grouped.groupby(["processing_type", "scenario", "constraint", "reference_mineral"]).apply(
        lambda x: (x["value_added"].sum() / x["production_tonnes"].sum()) if x["production_tonnes"].sum() > 0 else 0
    ).reset_index(name="norm_value_added_weighted")

    pivot = final_grouped.pivot_table(
        index=["processing_type", "scenario", "constraint"],
        columns="reference_mineral",
        values="norm_value_added_weighted", 
        fill_value=0
    ).reset_index()

    # Calculate total as sum (weighted by mineral production within each processing type)
    mineral_cols = [col for col in pivot.columns if col not in ["processing_type", "scenario", "constraint"]]
    pivot["Total"] = pivot[mineral_cols].sum(axis=1)

    return pivot

def create_normalized_revenue_summary(df):
    # Use validated, consistent logic
    by_type = create_normalized_revenue_table_by_stage_and_type(df)

    # Group by scenario and constraint, then sum across minerals
    value_cols = [
        col for col in by_type.columns
        if col not in ['scenario', 'constraint', 'processing_type']
    ]

    summary = by_type.groupby(['scenario', 'constraint'])[value_cols].sum().reset_index()

    # Extract year for display
    summary['year'] = summary['scenario'].str.extract(r'(\d{4})')
    cols = ['year', 'scenario', 'constraint'] + value_cols
    return summary[cols]


def create_summary_mid_demand_unconstrained(df):
    """
    Create summary table with 2040 scenario comparisons between country and regional constraints
    Now handles BAU, Early Processing, and Product Manufacturing scenarios
    """
    # Ensure simple value addition is calculated - must be applied per group
    if 'value_added_simple' not in df.columns:
        df = df.groupby(['scenario', 'constraint', 'iso3', 'reference_mineral']).apply(calc_value_added_simple).reset_index(drop=True)
    # Define the 2040 scenarios we want to compare
    scenario_2040_patterns = ['bau_2040', 'early_refining_2040', 'precursor_2040']
    
    # Filter for relevant constraints and 2040 scenarios + baseline
    # Use boolean OR instead of problematic regex pattern
    scenario_mask = (
        df['scenario'].str.contains('bau_2040', na=False) |
        df['scenario'].str.contains('early_refining_2040', na=False) |
        df['scenario'].str.contains('precursor_2040', na=False) |
        df['scenario'].str.contains('2022_baseline', na=False)
    )
    df_filtered = df[
        df['constraint'].isin(['country_unconstrained', 'region_unconstrained', 'country_constrained', 'region_constrained']) &
        scenario_mask
    ].copy()
    
    # Extract goal type from scenario
    def get_goal_type(scenario):
        if 'bau_2040' in scenario:
            return 'BAU_2040'
        elif 'early_refining_2040' in scenario:
            return 'Early_Processing_2040'
        elif 'precursor_2040' in scenario:
            return 'Product_Manufacturing_2040'
        elif '2022_baseline' in scenario:
            return 'Baseline_2022'
        else:
            return 'Other'
    
    df_filtered['goal_type'] = df_filtered['scenario'].apply(get_goal_type)
    df_filtered['year'] = df_filtered['scenario'].str.extract(r'(\d{4})').fillna('2040')
    
    # Filter for mid-demand scenarios (to maintain consistency with original logic)
    mid_scenarios = df_filtered[
        df_filtered['scenario'].str.contains('mid_min|mid_max|2022_baseline', na=False)
    ].copy()

    # Restrict production to stage 0 (metal content) for production metrics
    prod_stage0 = mid_scenarios[mid_scenarios['processing_stage'] == 0].copy()

    # Create comprehensive summary by goal_type and constraint
    summary_data = []
    
    for goal in mid_scenarios['goal_type'].unique():
        goal_data = mid_scenarios[mid_scenarios['goal_type'] == goal]
        
        if goal_data.empty:
            continue
            
        # Get year for this goal
        year = goal_data['year'].iloc[0]
        
        # Map goal type to processing type for stage targeting
        goal_processing_type_map = {
            'BAU_2040': 'Beneficiation',
            'Early_Refining_2040': 'Early refining', 
            'Early_Processing_2040': 'Early refining',  # Alternative name
            'Precursor_2040': 'Precursor related product',
            'Product_Manufacturing_2040': 'Precursor related product',  # Alternative name
            'Baseline_2022': 'Beneficiation'  # Default to beneficiation for baseline
        }
        
        for constraint in ['country_unconstrained', 'region_unconstrained', 'country_constrained', 'region_constrained']:
            constraint_data = goal_data[goal_data['constraint'] == constraint]
            
            if constraint_data.empty:
                continue
            
            # METAL CONTENT PRODUCTION: Always stage 0
            metal_content_data = constraint_data[constraint_data['processing_stage'] == 0]
            production_metal_content_mt = metal_content_data['production_tonnes'].sum() / 1e6 if not metal_content_data.empty else 0
            
            # PRODUCT PRODUCTION: Use scenario-specific target stages
            processing_type = goal_processing_type_map.get(goal, 'Beneficiation')
            production_products_mt = 0
            
            # Calculate product production by mineral using target stages
            for mineral in constraint_data['reference_mineral'].unique():
                mineral_data = constraint_data[constraint_data['reference_mineral'] == mineral]
                target_stage = get_target_stage_for_goal(mineral, processing_type)
                
                if target_stage is not None:
                    target_data = mineral_data[mineral_data['processing_stage'] == target_stage]
                    production_products_mt += target_data['production_tonnes'].sum() / 1e6
            
            # TOTAL PRODUCTION (all stages) - for backwards compatibility
            production_mt = constraint_data['production_tonnes'].sum() / 1e6
            
            # COSTS AND REVENUE (all stages)
            total_cost_musd = constraint_data['all_cost_usd'].sum() / 1e6
            total_revenue_musd = constraint_data['revenue_usd'].sum() / 1e6
            
            # VALUE ADDITION: Revenue from target stages minus revenue from stage 0
            stage_0_revenue_musd = metal_content_data['revenue_usd'].sum() / 1e6 if not metal_content_data.empty else 0
            value_addition_musd = 0
            
            # Calculate value addition by mineral using target stages
            for mineral in constraint_data['reference_mineral'].unique():
                mineral_data = constraint_data[constraint_data['reference_mineral'] == mineral]
                target_stage = get_target_stage_for_goal(mineral, processing_type)
                
                if target_stage is not None:
                    target_data = mineral_data[mineral_data['processing_stage'] == target_stage]
                    target_revenue = target_data['revenue_usd'].sum() / 1e6
                    mineral_stage_0 = mineral_data[mineral_data['processing_stage'] == 0]
                    stage_0_revenue = mineral_stage_0['revenue_usd'].sum() / 1e6 if not mineral_stage_0.empty else 0
                    value_addition_musd += (target_revenue - stage_0_revenue)
            
            # VALUE ADDITION SIMPLE: Stage revenue - Stage 1 costs
            value_addition_simple_musd = 0
            if 'value_added_simple' in constraint_data.columns:
                value_addition_simple_musd = constraint_data['value_added_simple'].sum() / 1e6
            else:
                # Calculate simple value addition if not already in data
                stage_1_data = constraint_data[constraint_data['processing_stage'] == 1.0]
                if not stage_1_data.empty:
                    stage_1_costs_musd = (stage_1_data['production_tonnes'] * stage_1_data['production_cost_usd_per_tonne']).sum() / 1e6
                    stage_revenue_musd = (constraint_data['production_tonnes_for_costs'] * constraint_data['price_usd_per_tonne']).sum() / 1e6
                    value_addition_simple_musd = stage_revenue_musd - stage_1_costs_musd
            
            # Water, energy, transport and emissions
            water_mcm = constraint_data['water_usage_m3'].sum() / 1e6
            transport_co2_kt = constraint_data['transport_total_tonsCO2eq'].sum() / 1e3
            # TODO: Restore when energy results are ready
            # energy_co2_kt = constraint_data['energy_tonsCO2eq'].sum() / 1e3
            energy_co2_kt = 0  # Placeholder until energy data available
            transport_volume_mtkm = constraint_data['transport_total_tonkm'].sum() / 1e6  # Convert to million tonne-km
            # TODO: Restore when energy results are ready  
            # energy_capacity_gw = constraint_data['energy_req_capacity_kW'].sum() / 1e6  # Convert kW to GW
            energy_capacity_gw = 0  # Placeholder until energy data available
            
            summary_data.append({
                'goal_type': goal,
                'year': year,
                'constraint': constraint,
                'production_Mt': round(production_mt, 3),
                'production_metal_content_Mt': round(production_metal_content_mt, 3),
                'production_products_Mt': round(production_products_mt, 3),
                'total_cost_MUSD': round(total_cost_musd, 2),
                'total_revenue_MUSD': round(total_revenue_musd, 2),
                'value_addition_MUSD': round(value_addition_musd, 2),
                'value_addition_simple_MUSD': round(value_addition_simple_musd, 2),
                'water_use_MCM': round(water_mcm, 2),
                'transport_volume_Mtkm': round(transport_volume_mtkm, 2),
                'energy_capacity_GW': round(energy_capacity_gw, 2),
                'transport_co2_kt': round(transport_co2_kt, 1),
                'energy_co2_kt': round(energy_co2_kt, 1),
                'total_co2_kt': round(transport_co2_kt + energy_co2_kt, 1)
            })
    
    summary_df = pd.DataFrame(summary_data)
    
    if summary_df.empty:
        return summary_df
    
    # Create comparison table with country vs regional analysis
    comparison_data = []
    
    for goal in summary_df['goal_type'].unique():
        goal_summary = summary_df[summary_df['goal_type'] == goal]
        year = goal_summary['year'].iloc[0]
        
        # Get data for each constraint type
        country_unc = goal_summary[goal_summary['constraint'] == 'country_unconstrained']
        region_unc = goal_summary[goal_summary['constraint'] == 'region_unconstrained']
        country_con = goal_summary[goal_summary['constraint'] == 'country_constrained']
        region_con = goal_summary[goal_summary['constraint'] == 'region_constrained']
        
        # Create comparison rows for unconstrained scenarios
        if not country_unc.empty and not region_unc.empty:
            country_val = country_unc.iloc[0]
            region_val = region_unc.iloc[0]
            
            comparison_data.append({
                'goal_type': goal,
                'year': year,
                'constraint_comparison': 'Country_vs_Regional_Unconstrained',
                'production_Mt_country': country_val['production_Mt'],
                'production_Mt_region': region_val['production_Mt'],
                'production_pct_change': round(((region_val['production_Mt'] / country_val['production_Mt']) * 100 - 100) if country_val['production_Mt'] > 0 else 0, 2),
                'production_metal_content_Mt_country': country_val['production_metal_content_Mt'],
                'production_metal_content_Mt_region': region_val['production_metal_content_Mt'],
                'production_metal_content_pct_change': round(((region_val['production_metal_content_Mt'] / country_val['production_metal_content_Mt']) * 100 - 100) if country_val['production_metal_content_Mt'] > 0 else 0, 2),
                'production_products_Mt_country': country_val['production_products_Mt'],
                'production_products_Mt_region': region_val['production_products_Mt'],
                'production_products_pct_change': round(((region_val['production_products_Mt'] / country_val['production_products_Mt']) * 100 - 100) if country_val['production_products_Mt'] > 0 else 0, 2),
                'cost_MUSD_country': country_val['total_cost_MUSD'],
                'cost_MUSD_region': region_val['total_cost_MUSD'],
                'cost_pct_change': round(((region_val['total_cost_MUSD'] / country_val['total_cost_MUSD']) * 100 - 100) if country_val['total_cost_MUSD'] > 0 else 0, 2),
                'revenue_MUSD_country': country_val['total_revenue_MUSD'],
                'revenue_MUSD_region': region_val['total_revenue_MUSD'],
                'revenue_pct_change': round(((region_val['total_revenue_MUSD'] / country_val['total_revenue_MUSD']) * 100 - 100) if country_val['total_revenue_MUSD'] > 0 else 0, 2),
                'value_addition_MUSD_country': country_val['value_addition_MUSD'],
                'value_addition_MUSD_region': region_val['value_addition_MUSD'],
                'value_addition_pct_change': round(((region_val['value_addition_MUSD'] / country_val['value_addition_MUSD']) * 100 - 100) if country_val['value_addition_MUSD'] > 0 else 0, 2),
                'value_addition_simple_MUSD_country': country_val['value_addition_simple_MUSD'],
                'value_addition_simple_MUSD_region': region_val['value_addition_simple_MUSD'],
                'value_addition_simple_pct_change': round(((region_val['value_addition_simple_MUSD'] / country_val['value_addition_simple_MUSD']) * 100 - 100) if country_val['value_addition_simple_MUSD'] != 0 else 0, 2),
                'water_MCM_country': country_val['water_use_MCM'],
                'water_MCM_region': region_val['water_use_MCM'],
                'water_pct_change': round(((region_val['water_use_MCM'] / country_val['water_use_MCM']) * 100 - 100) if country_val['water_use_MCM'] > 0 else 0, 2),
                'transport_volume_Mtkm_country': country_val['transport_volume_Mtkm'],
                'transport_volume_Mtkm_region': region_val['transport_volume_Mtkm'],
                'transport_volume_pct_change': round(((region_val['transport_volume_Mtkm'] / country_val['transport_volume_Mtkm']) * 100 - 100) if country_val['transport_volume_Mtkm'] > 0 else 0, 2),
                'energy_capacity_GW_country': country_val['energy_capacity_GW'],
                'energy_capacity_GW_region': region_val['energy_capacity_GW'],
                'energy_capacity_pct_change': round(((region_val['energy_capacity_GW'] / country_val['energy_capacity_GW']) * 100 - 100) if country_val['energy_capacity_GW'] > 0 else 0, 2),
                'total_co2_kt_country': country_val['total_co2_kt'],
                'total_co2_kt_region': region_val['total_co2_kt'],
                'total_co2_pct_change': round(((region_val['total_co2_kt'] / country_val['total_co2_kt']) * 100 - 100) if country_val['total_co2_kt'] > 0 else 0, 2)
            })
        
        # Create comparison rows for constrained scenarios
        if not country_con.empty and not region_con.empty:
            country_val = country_con.iloc[0]
            region_val = region_con.iloc[0]
            
            comparison_data.append({
                'goal_type': goal,
                'year': year,
                'constraint_comparison': 'Country_vs_Regional_Constrained',
                'production_Mt_country': country_val['production_Mt'],
                'production_Mt_region': region_val['production_Mt'],
                'production_pct_change': round(((region_val['production_Mt'] / country_val['production_Mt']) * 100 - 100) if country_val['production_Mt'] > 0 else 0, 2),
                'production_metal_content_Mt_country': country_val['production_metal_content_Mt'],
                'production_metal_content_Mt_region': region_val['production_metal_content_Mt'],
                'production_metal_content_pct_change': round(((region_val['production_metal_content_Mt'] / country_val['production_metal_content_Mt']) * 100 - 100) if country_val['production_metal_content_Mt'] > 0 else 0, 2),
                'production_products_Mt_country': country_val['production_products_Mt'],
                'production_products_Mt_region': region_val['production_products_Mt'],
                'production_products_pct_change': round(((region_val['production_products_Mt'] / country_val['production_products_Mt']) * 100 - 100) if country_val['production_products_Mt'] > 0 else 0, 2),
                'cost_MUSD_country': country_val['total_cost_MUSD'],
                'cost_MUSD_region': region_val['total_cost_MUSD'],
                'cost_pct_change': round(((region_val['total_cost_MUSD'] / country_val['total_cost_MUSD']) * 100 - 100) if country_val['total_cost_MUSD'] > 0 else 0, 2),
                'revenue_MUSD_country': country_val['total_revenue_MUSD'],
                'revenue_MUSD_region': region_val['total_revenue_MUSD'],
                'revenue_pct_change': round(((region_val['total_revenue_MUSD'] / country_val['total_revenue_MUSD']) * 100 - 100) if country_val['total_revenue_MUSD'] > 0 else 0, 2),
                'value_addition_MUSD_country': country_val['value_addition_MUSD'],
                'value_addition_MUSD_region': region_val['value_addition_MUSD'],
                'value_addition_pct_change': round(((region_val['value_addition_MUSD'] / country_val['value_addition_MUSD']) * 100 - 100) if country_val['value_addition_MUSD'] > 0 else 0, 2),
                'value_addition_simple_MUSD_country': country_val['value_addition_simple_MUSD'],
                'value_addition_simple_MUSD_region': region_val['value_addition_simple_MUSD'],
                'value_addition_simple_pct_change': round(((region_val['value_addition_simple_MUSD'] / country_val['value_addition_simple_MUSD']) * 100 - 100) if country_val['value_addition_simple_MUSD'] != 0 else 0, 2),
                'water_MCM_country': country_val['water_use_MCM'],
                'water_MCM_region': region_val['water_use_MCM'],
                'water_pct_change': round(((region_val['water_use_MCM'] / country_val['water_use_MCM']) * 100 - 100) if country_val['water_use_MCM'] > 0 else 0, 2),
                'transport_volume_Mtkm_country': country_val['transport_volume_Mtkm'],
                'transport_volume_Mtkm_region': region_val['transport_volume_Mtkm'],
                'transport_volume_pct_change': round(((region_val['transport_volume_Mtkm'] / country_val['transport_volume_Mtkm']) * 100 - 100) if country_val['transport_volume_Mtkm'] > 0 else 0, 2),
                'energy_capacity_GW_country': country_val['energy_capacity_GW'],
                'energy_capacity_GW_region': region_val['energy_capacity_GW'],
                'energy_capacity_pct_change': round(((region_val['energy_capacity_GW'] / country_val['energy_capacity_GW']) * 100 - 100) if country_val['energy_capacity_GW'] > 0 else 0, 2),
                'total_co2_kt_country': country_val['total_co2_kt'],
                'total_co2_kt_region': region_val['total_co2_kt'],
                'total_co2_pct_change': round(((region_val['total_co2_kt'] / country_val['total_co2_kt']) * 100 - 100) if country_val['total_co2_kt'] > 0 else 0, 2)
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # IMPORTANT: Transform to required format: scenario, constraint_comparison, indicator, national, regional, percentage_change
    # DO NOT CHANGE THIS FORMAT - USER REQUIREMENT 
    if not comparison_df.empty:
        # Reshape from wide to long format
        long_format_data = []
        
        for _, row in comparison_df.iterrows():
            scenario = row['goal_type']
            constraint_comparison = row['constraint_comparison']
            
            # Define indicators and their values
            indicators = [
                ('Production_Mt', row['production_Mt_country'], row['production_Mt_region'], row['production_pct_change']),
                ('Production_Metal_Content_Mt', row['production_metal_content_Mt_country'], row['production_metal_content_Mt_region'], row['production_metal_content_pct_change']),
                ('Production_Products_Mt', row['production_products_Mt_country'], row['production_products_Mt_region'], row['production_products_pct_change']),
                ('Value_Addition_Million_USD', row['value_addition_MUSD_country'], row['value_addition_MUSD_region'], row['value_addition_pct_change']),
                ('Value_Addition_Simple_Million_USD', row['value_addition_simple_MUSD_country'], row['value_addition_simple_MUSD_region'], row['value_addition_simple_pct_change']),
                ('Transport_Volume_Million_tonkm', row['transport_volume_Mtkm_country'], row['transport_volume_Mtkm_region'], row['transport_volume_pct_change']),
                ('cost_MUSD', row['cost_MUSD_country'], row['cost_MUSD_region'], row['cost_pct_change']),
                ('revenue_MUSD', row['revenue_MUSD_country'], row['revenue_MUSD_region'], row['revenue_pct_change']),
                ('water_MCM', row['water_MCM_country'], row['water_MCM_region'], row['water_pct_change']),
                ('energy_capacity_GW', row['energy_capacity_GW_country'], row['energy_capacity_GW_region'], row['energy_capacity_pct_change']),
                ('total_co2_kt', row['total_co2_kt_country'], row['total_co2_kt_region'], row['total_co2_pct_change'])
            ]
            
            for indicator, national, regional, pct_change in indicators:
                long_format_data.append({
                    'scenario': scenario,
                    'constraint_comparison': constraint_comparison,
                    'indicator': indicator,
                    'national': national,
                    'regional': regional,
                    'percentage_change': pct_change
                })
        
        return pd.DataFrame(long_format_data)
    else:
        return summary_df



def generate_pivot_excel_files(df: pd.DataFrame, global_output_path: str, country_output_folder: str):
    df = df.copy()
    os.makedirs(country_output_folder, exist_ok=True)

    # ---- Global Pivot File ----
    with ExcelWriter(global_output_path, engine='openpyxl') as writer:
        create_metal_content_table(df, to_kt=False).to_excel(writer, sheet_name="metal_content_global_Mt", index=False)
        create_unit_cost_table(df).to_excel(writer, sheet_name="unit_costs_usd_per_tonne", index=False)
        create_total_costs_by_mineral(df).to_excel(writer, sheet_name="total_costs_million_usd", index=False)
        create_revenue_by_mineral(df).to_excel(writer, sheet_name="revenue_million_usd", index=False)
        create_transport_emissions_by_mineral(df).to_excel(writer, sheet_name="transport_emissions_MtCO2e", index=False)
        # TODO: Restore when energy results are ready
        # create_energy_emissions_by_mineral(df).to_excel(writer, sheet_name="energy_emissions_MtCO2e", index=False)
        create_transport_volume_by_mineral(df).to_excel(writer, sheet_name="transport_volume_mtkm", index=False)
        # TODO: Restore when energy results are ready
        # create_energy_capacity_by_mineral(df).to_excel(writer, sheet_name="energy_capacity_GW", index=False)
        create_water_use_by_mineral(df).to_excel(writer, sheet_name="water_use_million_m3", index=False)
        create_value_added_by_mineral(df).to_excel(writer, sheet_name="value_added_million_usd", index=False)
        create_value_added_simple_by_mineral(df).to_excel(writer, sheet_name="value_added_simple_million_usd", index=False)
        create_production_table(df, to_kt=False).to_excel(writer, sheet_name="production_Mt", index=False)
        create_production_by_type_table(df, to_kt=False).to_excel(writer, sheet_name="production_by_type_Mt", index=False)

        rev_summary, rev_by_type = create_revenue_tables(df, to_kt=False)
        val_add_summary, val_add_by_type = create_value_added_tables(df, to_kt=False)
        rev_summary.to_excel(writer, sheet_name="revenue_summary_million_usd", index=False)
        rev_by_type.to_excel(writer, sheet_name="revenue_by_type_million_usd", index=False)
        val_add_summary.to_excel(writer, sheet_name="value_added_summary_million_usd", index=False)
        val_add_by_type.to_excel(writer, sheet_name="value_added_by_type_million_usd", index=False)

        # Normalized revenue and value addition by stage and type
        norm_rev = create_normalized_revenue_table_by_stage_and_type(df)
        norm_val_add = create_normalized_value_added_table_by_stage_and_type(df)

        norm_rev.to_excel(writer, sheet_name="norm_revenue_by_type_usdpt", index=False)
        norm_val_add.to_excel(writer, sheet_name="norm_value_added_by_type_usdpt", index=False)
        
        # Normalized revenue summary
        norm_summary = create_normalized_revenue_summary(df)
        norm_summary.to_excel(writer, sheet_name="norm_revenue_summary_usdpt", index=False)


        # Add long-format summary table
        summary_df = create_summary_mid_demand_unconstrained(df)
        summary_df.to_excel(writer, sheet_name="summary_table", index=False)
        

    # ---- Country-Specific Pivot Files ----
    for iso3 in df['iso3'].dropna().unique():
        df_country = df[df['iso3'] == iso3].copy()
        country_file_path = os.path.join(country_output_folder, f"all_data_pivots_{iso3}.xlsx")

        try:
            with ExcelWriter(country_file_path, engine='openpyxl') as writer:
                create_metal_content_table(df_country, to_kt=True).to_excel(writer, sheet_name="metal_content_kt", index=False)
                create_unit_cost_table(df_country).to_excel(writer, sheet_name="unit_costs_usd_per_tonne", index=False)
                create_total_costs_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="total_costs_musd", index=False)
                create_revenue_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="revenue_musd", index=False)
                create_transport_emissions_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="transport_emissions_ktCO2e", index=False)
                # TODO: Restore when energy results are ready
                # create_energy_emissions_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="energy_emissions_ktCO2e", index=False)
                create_transport_volume_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="transport_volume_mtkm", index=False)
                # TODO: Restore when energy results are ready
                # create_energy_capacity_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="energy_capacity_GW", index=False)
                create_water_use_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="water_use_mcm", index=False)
                create_value_added_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="value_added_musd", index=False)
                create_production_table(df_country, to_kt=True).to_excel(writer, sheet_name="production_kt", index=False)
                create_production_by_type_table(df_country, to_kt=True).to_excel(writer, sheet_name="production_by_type_kt", index=False)

                rev_summary, rev_by_type = create_revenue_tables(df_country, to_kt=True)
                val_add_summary, val_add_by_type = create_value_added_tables(df_country, to_kt=True)
                rev_summary.to_excel(writer, sheet_name="revenue_summary_musd", index=False)
                rev_by_type.to_excel(writer, sheet_name="revenue_by_type_musd", index=False)
                val_add_summary.to_excel(writer, sheet_name="value_added_summary_musd", index=False)
                val_add_by_type.to_excel(writer, sheet_name="value_added_by_type_musd", index=False)

                # Normalized revenue and value addition by stage and type
                norm_rev = create_normalized_revenue_table_by_stage_and_type(df_country)
                norm_val_add = create_normalized_value_added_table_by_stage_and_type(df_country)

                norm_rev.to_excel(writer, sheet_name="norm_revenue_by_type_usdpt", index=False)
                norm_val_add.to_excel(writer, sheet_name="norm_value_added_by_type_usdpt", index=False)

                norm_summary = create_normalized_revenue_summary(df_country)
                norm_summary.to_excel(writer, sheet_name="norm_revenue_summary_usdpt", index=False)

                # Add long-format summary for country
                summary_df = create_summary_mid_demand_unconstrained(df_country)
                summary_df.to_excel(writer, sheet_name="summary_table", index=False)
                

        except Exception as e:
            print(f"Error generating pivot file for {iso3}: {e}")

    return global_output_path, country_output_folder




if __name__ == "__main__":
    # Load configuration from JSON relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config.json")

    with open(config_path, "r") as f:
        config = json.load(f)

    processed_data_path = config['paths']['data']
    output_data_path = config['paths']['results']
    pivot_data_path = config['paths']['pivot_tables']
    figure_path = config['paths']['figures']

    all_data_file = os.path.join(output_data_path, "all_data.xlsx")
    if not os.path.exists(all_data_file):
        print("Generating all_data.xlsx...")
        agg_data_excel(output_data_path)
        # Make the add_data_excel function and get it to include revenue and value addition shares of GDP
        
    df = pd.read_excel(all_data_file)
    # Set output paths
    global_output = os.path.join(pivot_data_path, "all_data_pivots_global.xlsx")
    country_output = os.path.join(pivot_data_path)

    # Generate pivot files
    generate_pivot_excel_files(df, global_output, country_output)
    print("Pivot tables created successfully.")
    
