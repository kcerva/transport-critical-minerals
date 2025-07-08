import pandas as pd
import os
from pandas import ExcelWriter
import json

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

    df_va = df_filtered.groupby(
        ['scenario', 'constraint', 'iso3', 'reference_mineral']
    ).apply(calc_value_added).reset_index(drop=True)

    df_va['value_added_musd'] = df_va['value_added'] / 1e6

    return create_pivot_with_pct_change(df_va, 'value_added', 'value_added_musd', conversion_factor=1e6, to_kt=to_kt)

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
        index=['scenario', 'processing_type', 'year'],
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

    # Apply stage-wise value addition logic
    df = df.groupby(["scenario", "constraint", "iso3", "reference_mineral"]) \
           .apply(calc_value_added).reset_index(drop=True)

    # Convert to million USD
    df["value_added_musd"] = df["value_added"] / 1e6

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

    # Apply value added logic per group
    df = df.groupby(
        ['scenario', 'constraint', 'iso3', 'reference_mineral']
    ).apply(calc_value_added).reset_index(drop=True)

    # Convert to million USD
    df['value_added_musd'] = df['value_added'] / 1e6

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
    df = df[(df["processing_stage"] > 0) & (df["production_tonnes"] > 0)]

    group_cols = [
        "scenario", "constraint", "processing_stage", "processing_type", "reference_mineral"
    ]

    grouped = df.groupby(group_cols).agg({
        "revenue_usd": "sum",
        "production_tonnes": "sum"
    }).reset_index()

    grouped["norm_revenue"] = grouped["revenue_usd"] / grouped["production_tonnes"]

    pivot = grouped.pivot_table(
        index=["processing_type", "scenario", "constraint"],
        columns="reference_mineral",
        values="norm_revenue",
        aggfunc="mean"
    ).reset_index()

    pivot["Total"] = pivot[
        [col for col in pivot.columns if col not in ["processing_type", "scenario", "constraint"]]
    ].sum(axis=1)

    return pivot

def create_normalized_value_added_table_by_stage_and_type(df, to_kt=False): # wrong, need correct calc of value addition
    df = df.copy()
    df = df[(df["processing_stage"] > 0) & (df["production_tonnes"] > 0)]

    if "value_added" not in df.columns:
        df["value_added"] = (
            df["price_usd_per_tonne"] * df["production_tonnes"]
            - df["production_cost_usd_per_tonne"] * df["production_tonnes"]
        )

    group_cols = [
        "scenario", "constraint", "processing_stage", "processing_type", "reference_mineral"
    ]

    grouped = df.groupby(group_cols).agg({
        "value_added": "sum",
        "production_tonnes": "sum"
    }).reset_index()

    grouped["norm_value_added"] = grouped["value_added"] / grouped["production_tonnes"]

    pivot = grouped.pivot_table(
        index=["processing_type", "scenario", "constraint"],
        columns="reference_mineral",
        values="norm_value_added",
        aggfunc="mean"
    ).reset_index()

    pivot["Total"] = pivot[
        [col for col in pivot.columns if col not in ["processing_type", "scenario", "constraint"]]
    ].sum(axis=1)

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
    # Filter relevant constraints and scenarios
    df_filtered = df[
        df['constraint'].isin(['country_unconstrained', 'region_unconstrained']) &
        ((df['scenario'].str.contains('mid_min') & (df['constraint'] == 'country_unconstrained')) |
        (df['scenario'].str.contains('mid_max') & (df['constraint'] == 'region_unconstrained')))
        ]


    #  Restrict production to stage 0 (metal content)
    prod_stage0 = df_filtered[df_filtered['processing_stage'] == 0].copy()

    # Aggregate metrics
    prod_summary = prod_stage0.groupby(['year', 'constraint'])['production_tonnes'].sum().div(1e6).reset_index()  # Mt
    cost_rev_summary = df_filtered.groupby(['year', 'constraint']).agg({
        'all_cost_usd': lambda x: x.sum() / 1e6,       # USD million
        'revenue_usd': lambda x: x.sum() / 1e6         # USD million
    }).reset_index()

    # Merge
    summary = pd.merge(prod_summary, cost_rev_summary, on=['year', 'constraint'])

    # Split by constraint and merge
    country_df = summary[summary['constraint'] == 'country_unconstrained'].copy()
    region_df = summary[summary['constraint'] == 'region_unconstrained'].copy()
    merged = pd.merge(country_df, region_df, on='year', suffixes=('_country', '_region'))

    # Compute % changes
    merged['production_pct_change'] = ((merged['production_tonnes_region'] / merged['production_tonnes_country']) * 100 - 100).round(2)
    merged['cost_pct_change'] = ((merged['all_cost_usd_region'] / merged['all_cost_usd_country']) * 100 - 100).round(2)
    merged['revenue_pct_change'] = ((merged['revenue_usd_region'] / merged['revenue_usd_country']) * 100 - 100).round(2)

    # --- Value addition using same-year comparison ---
    main_va = create_value_added_totals_legacy(df)
    main_va = main_va[main_va['scenario'].str.contains('mid_')].copy()
    main_va['year'] = main_va['scenario'].str.extract(r'(\d{4})').astype(int)

    va_summary = []
    for year in main_va['year'].unique():
        same_year = main_va[main_va['year'] == year]
        row = {'year': year}
        try:
            country = same_year[same_year['scenario'].str.contains('mid_min')]['country_unconstrained'].values[0]
            region = same_year[same_year['scenario'].str.contains('mid_max')]['region_unconstrained'].values[0]
            row['country_unconstrained'] = country
            row['region_unconstrained'] = region
            row['pct_change_unconstrained'] = round((region / country) * 100 - 100, 2) if country else None
        except IndexError:
            continue
        va_summary.append(row)

    va_summary = pd.DataFrame(va_summary)

    # Final table
    records = []
    for _, row in merged.iterrows():
        year = row['year']
        records.extend([
            {
                'Year': year,
                'Variable': 'Production (Mt of metal content)',
                'Country': round(row['production_tonnes_country'], 2),
                'Region': round(row['production_tonnes_region'], 2),
                'Percentage Change': row['production_pct_change']
            },
            {
                'Year': year,
                'Variable': 'Total Cost (MUSD)',
                'Country': round(row['all_cost_usd_country'], 2),
                'Region': round(row['all_cost_usd_region'], 2),
                'Percentage Change': row['cost_pct_change']
            },
            {
                'Year': year,
                'Variable': 'Export Revenue (MUSD)',
                'Country': round(row['revenue_usd_country'], 2),
                'Region': round(row['revenue_usd_region'], 2),
                'Percentage Change': row['revenue_pct_change']
            }
        ])

        va_row = va_summary[va_summary['year'] == year]
        if not va_row.empty:
            va = va_row.iloc[0]
            records.append({
                'Year': year,
                'Variable': 'Value Addition (MUSD)',
                'Country': round(va['country_unconstrained'], 2),
                'Region': round(va['region_unconstrained'], 2),
                'Percentage Change': round(va['pct_change_unconstrained'], 2)
            })

    return pd.DataFrame(records)


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
        create_energy_emissions_by_mineral(df).to_excel(writer, sheet_name="energy_emissions_MtCO2e", index=False)
        create_transport_volume_by_mineral(df).to_excel(writer, sheet_name="transport_volume_million_ton_km", index=False)
        create_energy_capacity_by_mineral(df).to_excel(writer, sheet_name="energy_capacity_GW", index=False)
        create_water_use_by_mineral(df).to_excel(writer, sheet_name="water_use_million_m3", index=False)
        create_production_table(df, to_kt=False).to_excel(writer, sheet_name="production_Mt", index=False)
        create_production_by_type_table(df, to_kt=False).to_excel(writer, sheet_name="production_by_type_Mt", index=False)

        rev_summary, rev_by_type = create_revenue_tables(df, to_kt=False)
        rev_summary.to_excel(writer, sheet_name="revenue_summary_million_usd", index=False)
        rev_by_type.to_excel(writer, sheet_name="revenue_by_type_million_usd", index=False)

        # Normalized revenue and value addition by stage and type
        norm_rev = create_normalized_revenue_table_by_stage_and_type(df)
        # norm_val_add = create_normalized_value_added_table_by_stage_and_type(df)

        norm_rev.to_excel(writer, sheet_name="normalized_revenue_by_type_usdpt", index=False)
        
        # Normalized revenue summary
        norm_summary = create_normalized_revenue_summary(df)
        norm_summary.to_excel(writer, sheet_name="normalized_revenue_summary_usdpt", index=False)

        
        # norm_val_add.to_excel(writer, sheet_name="normalized_valadded_by_type_usdpt", index=False)


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
                create_energy_emissions_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="energy_emissions_ktCO2e", index=False)
                create_transport_volume_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="transport_volume_mtkm", index=False)
                create_energy_capacity_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="energy_capacity_GW", index=False)
                create_water_use_by_mineral(df_country, to_kt=True).to_excel(writer, sheet_name="water_use_mcm", index=False)
                create_production_table(df_country, to_kt=True).to_excel(writer, sheet_name="production_kt", index=False)
                create_production_by_type_table(df_country, to_kt=True).to_excel(writer, sheet_name="production_by_type_kt", index=False)

                rev_summary, rev_by_type = create_revenue_tables(df_country, to_kt=True)
                rev_summary.to_excel(writer, sheet_name="revenue_summary_musd", index=False)
                rev_by_type.to_excel(writer, sheet_name="revenue_by_type_musd", index=False)

                # Normalized revenue and value addition by stage and type
                norm_rev = create_normalized_revenue_table_by_stage_and_type(df_country)
                # norm_val_add = create_normalized_value_added_table_by_stage_and_type(df_country)

                norm_rev.to_excel(writer, sheet_name="normalized_revenue_by_type_usdpt", index=False)

                norm_summary = create_normalized_revenue_summary(df_country)
                norm_summary.to_excel(writer, sheet_name="normalized_revenue_summary_usdpt", index=False)

                # norm_val_add.to_excel(writer, sheet_name="normalized_valadded_by_type_usdpt", index=False)

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
    
