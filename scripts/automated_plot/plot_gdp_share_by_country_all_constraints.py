import pandas as pd
import matplotlib.pyplot as plt
import os
import re

from plot_config import (
    reference_mineral_colors,
    reference_mineral_namemap,
    reference_mineral_colormapshort
)

from plot_utils import format_legend, annotate_stacked_bars, annotate_bar_labels

def adjust_gdp_for_inflation(df):
    df["gdp_usd"] = df.apply(lambda row: row["gdp_usd"] * 1.22 if "2030" in row["scenario"] else
                                       row["gdp_usd"] * 1.56 if "2040" in row["scenario"] else row["gdp_usd"], axis=1)
    return df

def calculate_value_added(group):
    group = group.sort_values(by="processing_stage", ascending=True)
    group["processing_stage"] = group["processing_stage"].astype(float)
    group["value_added"] = 0.0

    for i in range(1, len(group)):
        prev_stage = group.iloc[i - 1]
        current_stage = group.iloc[i]

        if prev_stage["production_tonnes"] > 0:
            group.at[current_stage.name, "value_added"] = (
                (current_stage["price_usd_per_tonne"] * current_stage["production_tonnes"]) -
                (prev_stage["production_cost_usd_per_tonne"] * prev_stage["production_tonnes"])
            )

    return group

def plot_gdp_share_by_country_all_constraints(df, output_dir, value_column, title_prefix, ylabel):
    os.makedirs(output_dir, exist_ok=True)

    df["scenario_general"] = df["scenario"].apply(lambda s: re.sub(r'^\d{4}_', '', s))

    if "reference_mineral_short" not in df.columns:
        df["reference_mineral_short"] = df["reference_mineral"].map(reference_mineral_namemap)

    # Handle both original data format (with processing_stage) and computed data format (without processing_stage)
    processing_stage_filter = (df["processing_stage"] > 0) if "processing_stage" in df.columns else True
    
    df_filtered = df[
        processing_stage_filter &
        (df[value_column] > 0) &
        (df[value_column].notna()) &  # Filter out NaN values
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ].copy()

    saved_paths = []
    for (constraint, scenario_general), group_g in df_filtered.groupby(["constraint", "scenario_general"]):
        scenario_clean = scenario_general.replace("_threshold_metal_tons", "")
        years = sorted(group_g["year"].unique())
        fig, axes = plt.subplots(len(years), 1, figsize=(14, 5 * len(years)), sharex=True)
        if len(years) == 1:
            axes = [axes]

        constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
        constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
        figure_title = f"{title_prefix} — {constraint_type} {constraint_status} ({scenario_clean})"

        for ax, year_val in zip(axes, years):
            group_y = group_g[group_g["year"] == year_val]
            
            # Handle both 'country' and 'iso3' column names
            country_col = 'country' if 'country' in group_y.columns else 'iso3'
            
            # Add reference_mineral_short if missing
            if 'reference_mineral_short' not in group_y.columns and 'reference_mineral' in group_y.columns:
                group_y = group_y.copy()
                group_y['reference_mineral_short'] = group_y['reference_mineral'].map(reference_mineral_namemap)
            
            mineral_col = 'reference_mineral_short' if 'reference_mineral_short' in group_y.columns else 'reference_mineral'
            
            grouped = group_y.groupby([country_col, mineral_col])[value_column].sum().reset_index()

            pivot = grouped.pivot_table(
                index=country_col,
                columns=mineral_col,
                values=value_column,
                fill_value=0
            )

            if pivot.empty:
                continue

            pivot["total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")

            colors = [reference_mineral_colormapshort.get(col, "#999999") for col in pivot.columns]
            bars = pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)

            ax.set_title(f"{year_val}", fontsize=18, fontweight="bold")
            ax.set_ylabel("Country", fontsize=14)
            ax.set_xlabel(f"{ylabel}", fontsize=14)
            ax.tick_params(labelsize=12)
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)

            annotate_bar_labels(ax, pivot, orientation="horizontal")
            format_legend(ax, title="Mineral")

        fig.suptitle(figure_title, fontsize=20, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 0.88, 0.97])

        filename = f"{title_prefix.lower().replace(' ', '_')}_{scenario_clean}_{constraint}_by_year_subplots.png".replace(" ", "_")
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)

    return saved_paths

# === Value Addition and Revenue Computation ===
def adjust_gdp_for_inflation(df):
    df["gdp_usd"] = df.apply(lambda row: row["gdp_usd"] * 1.22 if "2030" in row["scenario"] else
                                       row["gdp_usd"] * 1.56 if "2040" in row["scenario"] else row["gdp_usd"], axis=1)
    return df
    
def compute_value_addition_share(df):
    df = adjust_gdp_for_inflation(df.copy())
    df = df[df["processing_stage"] > 0]
    df = df[df["gdp_usd"] > 0]  # Filter out zero GDP values
    df = df.sort_values(by=["iso3", "reference_mineral", "scenario", "processing_stage"])
    df["value_added"] = 0.0

    def calc_value_added(group):
        for i in range(1, len(group)):
            prev = group.iloc[i - 1]
            curr = group.iloc[i]
            if prev["production_tonnes"] > 0:
                group.at[curr.name, "value_added"] = (
                    (curr["price_usd_per_tonne"] * curr["production_tonnes"]) -
                    (prev["production_cost_usd_per_tonne"] * prev["production_tonnes"])
                )
        return group

    df = df.groupby(["iso3", "reference_mineral", "scenario"]).apply(calc_value_added).reset_index(drop=True)
    df["value"] = df["value_added"] / df["gdp_usd"] * 100
    df["variable"] = "value_addition"
    df.rename(columns={"iso3": "country"}, inplace=True)
    # Keep all essential columns for plotting
    return df[["country", "year", "reference_mineral", "scenario", "constraint", "variable", "value"]]

def plot_gdp_share_scenario_comparison_subplots(df, output_dir, compute_function, value_column, title_prefix, ylabel):
    """Create scenario comparison subplots for GDP share metrics with 3 rows (BAU, Early Refining, Precursor)"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Compute the GDP share data using the provided function
    computed_df = compute_function(df)
    
    if computed_df.empty:
        return []
    
    # Filter for mid scenarios only
    computed_df_filtered = computed_df[
        (computed_df[value_column] > 0) &
        (computed_df[value_column].notna()) &
        (
            ((computed_df["constraint"].str.contains("country")) & (computed_df["scenario"].str.contains("mid_min"))) |
            ((computed_df["constraint"].str.contains("region")) & (computed_df["scenario"].str.contains("mid_max")))
        )
    ].copy()
    
    if computed_df_filtered.empty:
        return []
    
    # Add scenario_general column
    computed_df_filtered["scenario_general"] = computed_df_filtered["scenario"].apply(lambda s: re.sub(r'^\\d{4}_', '', s))
    
    # Define scenario mapping  
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Processing',
        'precursor_2040': 'Product Manufacturing'
    }
    
    # Add reference_mineral_short if missing
    if 'reference_mineral_short' not in computed_df_filtered.columns and 'reference_mineral' in computed_df_filtered.columns:
        computed_df_filtered['reference_mineral_short'] = computed_df_filtered['reference_mineral'].map(reference_mineral_namemap)
    
    saved_paths = []
    
    # Group by constraint only to compare scenarios within each constraint
    for constraint, constraint_group in computed_df_filtered.groupby("constraint"):
        constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
        constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
        
        # Get scenarios present in this constraint group
        available_scenarios = []
        scenario_data = {}
        
        for scenario_key, scenario_name in scenario_mapping.items():
            scenario_data_filtered = constraint_group[constraint_group["scenario"].str.contains(scenario_key)]
            if not scenario_data_filtered.empty:
                available_scenarios.append((scenario_key, scenario_name))
                scenario_data[scenario_key] = scenario_data_filtered
        
        if len(available_scenarios) < 2:  # Need at least 2 scenarios to compare
            continue
        
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 8 * len(available_scenarios)), sharex=True)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"{title_prefix} Scenario Comparison — {constraint_type} {constraint_status}"
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Handle both 'country' and 'iso3' column names
            country_col = 'country' if 'country' in group_data.columns else 'iso3'
            mineral_col = 'reference_mineral_short' if 'reference_mineral_short' in group_data.columns else 'reference_mineral'
            
            # Aggregate by country and mineral
            grouped = group_data.groupby([country_col, mineral_col])[value_column].sum().reset_index()
            
            # Create pivot for stacked bar chart
            pivot = grouped.pivot_table(
                index=country_col,
                columns=mineral_col,
                values=value_column,
                fill_value=0
            )
            
            if not pivot.empty:
                pivot["total"] = pivot.sum(axis=1)
                pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
                
                # Plot stacked horizontal bar chart
                colors = [reference_mineral_colormapshort.get(col, "#999999") for col in pivot.columns]
                pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
                
                # Styling
                ax.set_title(f"{scenario_name}", fontsize=18, fontweight="bold")
                ax.set_ylabel("Country", fontsize=14)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel(f"{ylabel}", fontsize=14)
                ax.tick_params(labelsize=12)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Add mineral labels on bars (abbreviated for space)
                for j, country in enumerate(pivot.index):
                    cumulative_left = 0
                    for mineral in pivot.columns:
                        width = pivot.loc[country, mineral]
                        if width > max(pivot.max().max() * 0.05, 0.1):  # Label significant segments
                            ax.text(
                                cumulative_left + width / 2,
                                j,
                                reference_mineral_namemap.get(mineral, mineral)[:2],  # Short labels
                                ha="center", va="center",
                                fontsize=9, color="white", fontweight="bold"
                            )
                        cumulative_left += width
                
                # Legend only on top subplot
                if i == 0:
                    ax.legend(
                        title="Mineral",
                        loc="upper left",
                        bbox_to_anchor=(1.01, 1),
                        fontsize=11,
                        title_fontsize=12
                    )
                else:
                    ax.legend().set_visible(False)
        
        # Overall figure styling
        fig.suptitle(figure_title, fontsize=20, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 0.88, 0.97])
        
        # Save figure
        filename = f"{title_prefix.lower().replace(' ', '_')}_scenario_comparison_{constraint}_subplots.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths

def compute_revenue_share(df):
    df = adjust_gdp_for_inflation(df.copy())
    df = df[df["processing_stage"] > 0]
    df = df[df["gdp_usd"] > 0]  # Filter out zero GDP values
    df["value"] = df["revenue_usd"] / df["gdp_usd"] * 100
    df["variable"] = "revenue"
    df.rename(columns={"iso3": "country"}, inplace=True)
    # Keep all essential columns for plotting
    return df[["country", "year", "reference_mineral", "scenario", "constraint", "variable", "value"]]
