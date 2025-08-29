import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

from plot_config import (
    reference_mineral_colors,
    reference_mineral_namemap,
    reference_mineral_colormapshort
)

from plot_utils import format_legend, annotate_stacked_bars, annotate_bar_labels, generate_country_colormap
from plot_config import (
    get_mineral_processing_routes, 
    get_invalid_mineral_routes, 
    get_route_flag_message,
    find_matching_route, 
    validate_route_sequence
)


def plot_emissions_by_country_all_constraints(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df["emissions_mt"] = (df["transport_total_tonsCO2eq"] + df["energy_tonsCO2eq"]) / 1e6

    df["scenario_general"] = df["scenario"].apply(lambda s: re.sub(r'^\d{4}_', '', s))

    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["emissions_mt"] > 0) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ].copy()

    df_filtered["reference_mineral_short"] = df_filtered["reference_mineral"].map(reference_mineral_namemap)

    saved_paths = []
    for (constraint, scenario_general), group_g in df_filtered.groupby(["constraint", "scenario_general"]):
        scenario_clean = scenario_general.replace("_threshold_metal_tons", "")
        years = sorted(group_g["year"].unique())
        fig, axes = plt.subplots(len(years), 1, figsize=(14, 5 * len(years)), sharex=True)
        if len(years) == 1:
            axes = [axes]

        constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
        constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
        figure_title = f"Emissions — {constraint_type} {constraint_status} ({scenario_clean})"

        for ax, year_val in zip(axes, years):
            group_y = group_g[group_g["year"] == year_val]
            grouped = group_y.groupby(["reference_mineral_short", "iso3"])["emissions_mt"].sum().reset_index()
            pivot = grouped.pivot_table(
                index="reference_mineral_short",
                columns="iso3",
                values="emissions_mt",
                fill_value=0
            )

            if pivot.empty:
                continue

            pivot["total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")

            colors = [reference_mineral_colormapshort.get(mineral, "#999999") for mineral in pivot.index]
            pivot.plot(
                kind="barh", stacked=True, color=colors, ax=ax
            )

            ax.set_title(f"{year_val}", fontsize=14, fontweight="bold")
            ax.set_ylabel("Mineral", fontsize=12)
            ax.set_xlabel("Emissions (Mt CO₂eq)", fontsize=12)
            ax.tick_params(labelsize=11)
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)

            annotate_bar_labels(ax, pivot, orientation="horizontal")
            format_legend(ax, title="Country")

        fig.suptitle(figure_title, fontsize=18, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 0.88, 0.97])

        filename = f"emissions_{scenario_clean}_{constraint}_by_year_subplots.png".replace(" ", "_")
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)

    return saved_paths

def plot_water_by_country_all_constraints(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df["water_million_m3"] = df["water_usage_m3"] / 1e6

    df["scenario_general"] = df["scenario"].apply(lambda s: re.sub(r'^\d{4}_', '', s))

    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["water_million_m3"] > 0) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ].copy()

    df_filtered["reference_mineral_short"] = df_filtered["reference_mineral"].map(reference_mineral_namemap)

    saved_paths = []
    for (constraint, scenario_general), group_g in df_filtered.groupby(["constraint", "scenario_general"]):
        scenario_clean = scenario_general.replace("_threshold_metal_tons", "")
        years = sorted(group_g["year"].unique())
        fig, axes = plt.subplots(len(years), 1, figsize=(14, 5 * len(years)), sharex=True)
        if len(years) == 1:
            axes = [axes]

        constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
        constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
        figure_title = f"Water Use — {constraint_type} {constraint_status} ({scenario_clean})"

        for ax, year_val in zip(axes, years):
            group_y = group_g[group_g["year"] == year_val]
            grouped = group_y.groupby(["reference_mineral_short", "iso3"])["water_million_m3"].sum().reset_index()
            pivot = grouped.pivot_table(
                index="reference_mineral_short",
                columns="iso3",
                values="water_million_m3",
                fill_value=0
            )

            if pivot.empty:
                continue

            pivot["total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")

            colors = [reference_mineral_colormapshort.get(col, "#999999") for col in pivot.columns]
            pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.grid(axis="x", linestyle="--", linewidth=0.7, alpha=0.6)
            ax.set_axisbelow(True)

            ax.set_title(f"{year_val}", fontsize=14, fontweight="bold")
            ax.set_ylabel("Mineral", fontsize=12)
            ax.set_xlabel("Water Use (million m³)", fontsize=12)
            ax.tick_params(labelsize=11)
            annotate_bar_labels(ax, pivot, orientation="horizontal")
            format_legend(ax, title="Country")

        fig.suptitle(figure_title, fontsize=18, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 0.88, 0.97])

        filename = f"water_{scenario_clean}_{constraint}_by_year_subplots.png".replace(" ", "_")
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)

    return saved_paths

def plot_emissions_scenario_comparison_subplots(df, output_dir):
    """Create proper scenario comparison subplots for emissions with 3 rows (BAU, Early Refining, Precursor)"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Now using the available energy_tonsCO2eq column
    df = df.copy()
    df["emissions_mt"] = (df["transport_total_tonsCO2eq"] + df["energy_tonsCO2eq"]) / 1e6
    
    # Filter for 2040 scenarios only and mid demand levels  
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["emissions_mt"] > 0) &
        (df["scenario"].str.contains("2040")) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ]
    
    if df_filtered.empty:
        print("Warning: No emissions data available for plotting")
        return []
    
    # Define scenario mapping
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining',
        'precursor_2040': 'Precursor Product'
    }
    
    df_filtered = df_filtered.copy()
    df_filtered["reference_mineral_short"] = df_filtered["reference_mineral"].map(reference_mineral_namemap)
    
    saved_paths = []
    
    # Group by constraint only (not scenario) to compare scenarios within each constraint
    for constraint, constraint_group in df_filtered.groupby("constraint"):
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
        
        if len(available_scenarios) < 1:  # Need at least 1 scenario to plot
            continue
            
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 5.5 * len(available_scenarios)), sharex=False)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"CO₂eq Emissions Scenario Comparison — {constraint_type} {constraint_status}"
        
        # First pass: find maximum x-value across all scenarios for consistent scaling
        max_x_value = 0
        for scenario_key, scenario_name in scenario_mapping.items():
            if scenario_key in [s[0] for s in available_scenarios]:
                scenario_data_temp = scenario_data[scenario_key]
                temp_grouped = scenario_data_temp.groupby(["reference_mineral_short", "iso3"])["emissions_mt"].sum().reset_index()
                if not temp_grouped.empty:
                    temp_pivot = temp_grouped.pivot_table(
                        index="reference_mineral_short",
                        columns="iso3",
                        values="emissions_mt",
                        fill_value=0
                    )
                    if not temp_pivot.empty:
                        row_totals = temp_pivot.sum(axis=1)
                        if len(row_totals) > 0:
                            max_x_value = max(max_x_value, row_totals.max())
        
        # Add 10% padding to max value for better visualization
        if max_x_value > 0:
            max_x_value = max_x_value * 1.1
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Group by mineral and country
            grouped = group_data.groupby(["reference_mineral_short", "iso3"])["emissions_mt"].sum().reset_index()
            
            if grouped.empty:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(scenario_name)
                continue
            
            # Pivot to get minerals as rows and countries as columns
            pivot_data = grouped.pivot_table(
                index="reference_mineral_short",
                columns="iso3",
                values="emissions_mt",
                fill_value=0
            )
            
            # Sort by total emissions
            row_totals = pivot_data.sum(axis=1).sort_values(ascending=True)
            pivot_data = pivot_data.loc[row_totals.index]
            
            # Create horizontal stacked bar chart
            y_pos = np.arange(len(pivot_data.index))
            left = np.zeros(len(pivot_data.index))
            
            # Create a color map for countries using project standard colors
            countries = sorted(pivot_data.columns)
            from plot_utils import generate_country_colormap
            color_map = generate_country_colormap(countries)
            
            # Track positions for country labels
            bar_positions = {}
            for country in countries:
                values = pivot_data[country].values
                bars = ax.barh(y_pos, values, left=left, label=country, 
                              color=color_map[country], alpha=0.8)
                
                # Store bar positions for labeling
                for j, (bar, value) in enumerate(zip(bars, values)):
                    if value > 0:  # Only store if there's actual data
                        bar_positions[(j, country)] = {
                            'left': left[j],
                            'width': value,
                            'center': left[j] + value/2
                        }
                
                left += values
            
            # Add country ISO3 labels to bars that are large enough
            for (mineral_idx, country), pos_info in bar_positions.items():
                bar_width = pos_info['width']
                # Only add label if bar is wide enough (relative to max value)
                if bar_width > max_x_value * 0.03:  # At least 3% of max width
                    ax.text(pos_info['center'], mineral_idx, country, 
                           ha='center', va='center', fontweight='bold',
                           fontsize=10, color='white')
            
            # Formatting with larger fonts
            ax.set_yticks(y_pos)
            ax.set_yticklabels(pivot_data.index, fontsize=12)
            ax.set_xlabel('CO₂eq Emissions (Million Tonnes)', fontsize=14, fontweight='bold')
            ax.set_title(scenario_name, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlim(0, max_x_value)
            
            # Improve tick formatting
            ax.tick_params(axis='x', labelsize=11)
            ax.tick_params(axis='y', labelsize=12)
            
            # Add grid
            ax.grid(True, axis='x', alpha=0.3)
            
            # Add legend only to the last subplot with improved formatting
            if i == len(available_scenarios) - 1:
                ax.legend(title='Country', bbox_to_anchor=(1.05, 1), loc='upper left', 
                         fontsize=12, title_fontsize=13, frameon=True, 
                         fancybox=True, shadow=True, ncol=1, 
                         borderaxespad=0, columnspacing=1.0, handletextpad=0.5)
        
        # Add main title with better positioning
        fig.suptitle(figure_title, fontsize=18, fontweight='bold', y=0.95)
        
        # Adjust layout to provide space for legend and better title positioning
        plt.tight_layout(rect=[0, 0.02, 0.85, 0.93])  # Better spacing top/bottom and right for legend
        
        # Save figure to emissions_scenario_comparison subdirectory
        emissions_output_dir = os.path.join(output_dir, "emissions_scenario_comparison")
        os.makedirs(emissions_output_dir, exist_ok=True)
        filename = f"emissions_scenario_comparison_{constraint.replace('_', '_')}.png"
        filepath = os.path.join(emissions_output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        saved_paths.append(filepath)
        print(f"Saved emissions scenario comparison plot: {filename}")
    
    return saved_paths

def plot_water_scenario_comparison_subplots(df, output_dir):
    """Create proper scenario comparison subplots for water usage with 3 rows (BAU, Early Refining, Precursor)"""
    os.makedirs(output_dir, exist_ok=True)
    
    df = df.copy()
    df["water_million_m3"] = df["water_usage_m3"] / 1e6
    
    # Filter for 2040 scenarios only and mid demand levels
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["water_million_m3"] > 0) &
        (df["scenario"].str.contains("2040")) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ]
    
    if df_filtered.empty:
        return []
    
    # Define scenario mapping
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining',
        'precursor_2040': 'Precursor Product'
    }
    
    df_filtered = df_filtered.copy()
    df_filtered["reference_mineral_short"] = df_filtered["reference_mineral"].map(reference_mineral_namemap)
    
    saved_paths = []
    
    # Group by constraint only (not scenario) to compare scenarios within each constraint
    for constraint, constraint_group in df_filtered.groupby("constraint"):
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
        
        if len(available_scenarios) < 1:  # Need at least 1 scenario to plot
            continue
            
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 5.5 * len(available_scenarios)), sharex=False)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"Water Usage Scenario Comparison — {constraint_type} {constraint_status}"
        
        # First pass: find maximum x-value across all scenarios for consistent scaling
        max_x_value = 0
        for scenario_key, scenario_name in scenario_mapping.items():
            if scenario_key in [s[0] for s in available_scenarios]:
                scenario_data_temp = scenario_data[scenario_key]
                temp_grouped = scenario_data_temp.groupby(["reference_mineral_short", "iso3"])["water_million_m3"].sum().reset_index()
                if not temp_grouped.empty:
                    temp_pivot = temp_grouped.pivot_table(
                        index="reference_mineral_short",
                        columns="iso3",
                        values="water_million_m3",
                        fill_value=0
                    )
                    if not temp_pivot.empty:
                        row_totals = temp_pivot.sum(axis=1)
                        if len(row_totals) > 0:
                            max_x_value = max(max_x_value, row_totals.max())
        
        # Add 10% padding to max value for better visualization
        if max_x_value > 0:
            max_x_value = max_x_value * 1.1
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Aggregate by mineral and country (like production subplots)
            grouped = group_data.groupby(["reference_mineral_short", "iso3"])["water_million_m3"].sum().reset_index()
            
            if not grouped.empty:
                # Create pivot table for stacked bars
                pivot = grouped.pivot_table(
                    index="reference_mineral_short",
                    columns="iso3", 
                    values="water_million_m3",
                    fill_value=0
                )
                
                # Sort by total water usage for consistent ordering
                pivot["total"] = pivot.sum(axis=1)
                pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
                
                # Generate country color mapping
                countries = list(pivot.columns)
                country_colors = generate_country_colormap(countries)
                colors = [country_colors.get(country, "#999999") for country in countries]
                
                # Create stacked horizontal bar chart
                pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
                
                # Styling
                ax.set_title(f"{scenario_name}", fontsize=16, fontweight="bold")
                ax.set_ylabel("Mineral", fontsize=14)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel("Water Usage (million m³)", fontsize=14)
                ax.tick_params(labelsize=12)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Set consistent x-axis limits across all subplots
                if max_x_value > 0:
                    ax.set_xlim(0, max_x_value)
                
                # Add country labels on bars
                annotate_bar_labels(ax, pivot, orientation="horizontal")
                
                # Legend only on top subplot
                if i == 0:
                    format_legend(ax, title="Country")
                else:
                    ax.legend().set_visible(False)
        
        # Overall figure styling
        fig.suptitle(figure_title, fontsize=18, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save figure
        filename = f"water_usage_scenario_comparison_{constraint}_subplots.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths


# === Emissions and Water Share Computation ===
def compute_emissions_by_country(df):
    df = df.copy()
    df = df[df["processing_stage"] > 0]
    df = df[df["energy_tonsCO2eq"].notna()]
    df = df.rename(columns={"energy_tonsCO2eq": "value"})
    df["variable"] = "co2"
    df.rename(columns={"iso3": "country"}, inplace=True)
    return df[["country", "year", "reference_mineral", "variable", "value"]]

def compute_water_by_country(df):
    df = df.copy()
    df = df[df["processing_stage"] > 0]
    df = df[df["water_usage_m3"].notna()]
    df = df.rename(columns={"water_usage_m3": "value"})
    df["variable"] = "water"
    df.rename(columns={"iso3": "country"}, inplace=True)
    return df[["country", "year", "reference_mineral", "variable", "value"]]

def calc_value_added_with_routes(group):
    """
    Calculate value addition following mineral-specific processing routes
    
    Args:
        group: DataFrame group for one country-mineral-scenario combination
        
    Returns:
        DataFrame: Group with value_added column calculated using valid routes
    """
    group = group.sort_values(by='processing_stage').copy()
    group["value_added"] = 0.0
    
    if len(group) < 2:
        return group  # Need at least 2 stages for value addition
    
    mineral = group['reference_mineral'].iloc[0]
    country = group['iso3'].iloc[0]
    scenario = group['scenario'].iloc[0]
    
    # Get processing routes for this mineral
    valid_routes = get_mineral_processing_routes(mineral)
    invalid_routes = get_invalid_mineral_routes(mineral)
    
    # Get stages present in this country's data
    country_stages = sorted(group['processing_stage'].unique())
    
    # Validate for invalid routes first - STRICT ENFORCEMENT
    is_invalid, invalid_route = validate_route_sequence(country_stages, invalid_routes)
    if is_invalid:
        flag_message = get_route_flag_message(mineral)
        if flag_message:
            print(f"⚠️  {flag_message}: {mineral} in {country} ({scenario})")
            print(f"    Invalid route detected: {invalid_route}")
            print(f"    🚫 ZERO VALUE ADDITION - Invalid processing pathway")
        # Return group with zero value addition for invalid routes
        return group
    
    # If no valid routes defined for this mineral, fall back to sequential calculation
    if not valid_routes:
        # Fallback: sequential stage calculation (old method)
        for i in range(1, len(group)):
            prev = group.iloc[i - 1]
            curr = group.iloc[i]
            if prev["production_tonnes"] > 0:
                group.at[curr.name, "value_added"] = (
                    (curr["price_usd_per_tonne"] * curr["production_tonnes"]) -
                    (prev["production_cost_usd_per_tonne"] * prev["production_tonnes"])
                )
        return group
    
    # Find the best matching valid route
    matching_route = find_matching_route(country_stages, valid_routes)
    
    if not matching_route:
        print(f"⚠️  No valid route found for {mineral} in {country} ({scenario})")
        print(f"    Available stages: {country_stages}")
        print(f"    Valid routes: {valid_routes}")
        return group  # Return with zero value addition
    
    # Calculate value addition along the matching route
    route_stages_in_data = [stage for stage in matching_route if stage in country_stages]
    
    # Create a mapping from stage to group row index
    stage_to_index = {}
    for idx, row in group.iterrows():
        stage_to_index[row['processing_stage']] = idx
    
    # Calculate value addition for each step in the route
    for i in range(1, len(route_stages_in_data)):
        prev_stage = route_stages_in_data[i-1]
        curr_stage = route_stages_in_data[i]
        
        if prev_stage in stage_to_index and curr_stage in stage_to_index:
            prev_idx = stage_to_index[prev_stage]
            curr_idx = stage_to_index[curr_stage]
            
            prev_row = group.loc[prev_idx]
            curr_row = group.loc[curr_idx]
            
            if prev_row["production_tonnes"] > 0:
                value_added = (
                    (curr_row["price_usd_per_tonne"] * curr_row["production_tonnes"]) -
                    (prev_row["production_cost_usd_per_tonne"] * prev_row["production_tonnes"])
                )
                group.at[curr_idx, "value_added"] = value_added
    
    return group

def calc_value_added_simple(group):
    """
    Calculate simple value addition: Stage Revenue - Stage 1 Costs
    
    Formula: (production_tonnes_for_costs × price_usd_per_tonne) - (stage_1_production_tonnes × stage_1_production_cost_usd_per_tonne)
    
    Args:
        group: DataFrame group for one country-mineral-scenario combination
        
    Returns:
        DataFrame: Group with value_added_simple column calculated
    """
    group = group.sort_values(by='processing_stage').copy()
    group["value_added_simple"] = 0.0
    
    if len(group) < 2:
        return group  # Need at least 2 stages (including stage 1 as baseline)
    
    # Find stage 1 (beneficiation) row for baseline costs
    stage_1_rows = group[group['processing_stage'] == 1.0]
    if stage_1_rows.empty:
        return group  # No stage 1 baseline available
    
    stage_1_row = stage_1_rows.iloc[0]
    stage_1_costs = stage_1_row['production_tonnes'] * stage_1_row['production_cost_usd_per_tonne']
    
    # Calculate simple value addition for all stages > 0 (excluding stage 0 if present)
    for idx, row in group.iterrows():
        if row['processing_stage'] > 0:  # All processing stages except stage 0
            stage_revenue = row['production_tonnes_for_costs'] * row['price_usd_per_tonne']
            group.at[idx, 'value_added_simple'] = stage_revenue - stage_1_costs
    
    return group

def plot_value_addition_scenario_comparison_subplots(df, output_dir):
    """Create proper scenario comparison subplots for value addition with 3 rows (BAU, Early Refining, Precursor)"""
    os.makedirs(output_dir, exist_ok=True)
    
    df = df.copy()
    
    # Filter for 2040 scenarios only and mid demand levels, processing stages > 0
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["scenario"].str.contains("2040")) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ]
    
    if df_filtered.empty:
        return []
    
    # Calculate value addition using production_tonnes (total domestic economic impact)
    df_filtered = df_filtered.sort_values(by=["iso3", "reference_mineral", "scenario", "processing_stage"])
    df_filtered["value_added"] = 0.0
    
    df_filtered = df_filtered.groupby(["scenario", "constraint", "iso3", "reference_mineral"]).apply(
        calc_value_added_with_routes
    ).reset_index(drop=True)
    
    # Convert to million USD
    df_filtered["value_added_musd"] = df_filtered["value_added"] / 1e6
    
    # Filter for non-zero value addition
    df_filtered = df_filtered[df_filtered["value_added_musd"] > 0]
    
    if df_filtered.empty:
        return []
    
    # Define scenario mapping
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining',
        'precursor_2040': 'Precursor Product'
    }
    
    df_filtered = df_filtered.copy()
    df_filtered["reference_mineral_short"] = df_filtered["reference_mineral"].map(reference_mineral_namemap)
    
    saved_paths = []
    
    # Group by constraint only (not scenario) to compare scenarios within each constraint
    for constraint, constraint_group in df_filtered.groupby("constraint"):
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
        
        if len(available_scenarios) < 1:  # Need at least 1 scenario to plot
            continue
            
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 5.5 * len(available_scenarios)), sharex=False)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"Value Addition Scenario Comparison — {constraint_type} {constraint_status}"
        
        # First pass: find maximum x-value across all scenarios for consistent scaling
        max_x_value = 0
        for scenario_key, scenario_name in scenario_mapping.items():
            if scenario_key in [s[0] for s in available_scenarios]:
                scenario_data_temp = scenario_data[scenario_key]
                temp_grouped = scenario_data_temp.groupby([
                    "reference_mineral_short", "iso3"
                ])["value_added_musd"].sum().reset_index()
                if not temp_grouped.empty:
                    temp_pivot = temp_grouped.pivot_table(
                        index="reference_mineral_short",
                        columns="iso3",
                        values="value_added_musd",
                        fill_value=0
                    )
                    if not temp_pivot.empty:
                        row_totals = temp_pivot.sum(axis=1)
                        if len(row_totals) > 0:
                            max_x_value = max(max_x_value, row_totals.max())
        
        # Add 10% padding to max value for better visualization
        if max_x_value > 0:
            max_x_value = max_x_value * 1.1
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Aggregate by mineral and country (like production subplots)
            grouped = group_data.groupby([
                "reference_mineral_short", "iso3"
            ])["value_added_musd"].sum().reset_index()
            
            if not grouped.empty:
                # Create pivot table for stacked bars
                pivot = grouped.pivot_table(
                    index="reference_mineral_short",
                    columns="iso3", 
                    values="value_added_musd",
                    fill_value=0
                )
                
                # Sort by total value addition for consistent ordering
                pivot["total"] = pivot.sum(axis=1)
                pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
                
                # Generate country color mapping
                countries = list(pivot.columns)
                country_colors = generate_country_colormap(countries)
                colors = [country_colors.get(country, "#999999") for country in countries]
                
                # Create stacked horizontal bar chart
                pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
                
                # Styling
                ax.set_title(f"{scenario_name}", fontsize=16, fontweight="bold")
                ax.set_ylabel("Mineral", fontsize=14)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel("Value Addition (million USD)", fontsize=14)
                ax.tick_params(labelsize=12)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Set consistent x-axis limits across all subplots
                if max_x_value > 0:
                    ax.set_xlim(0, max_x_value)
                
                # Add country labels on bars
                annotate_bar_labels(ax, pivot, orientation="horizontal")
                
                # Legend only on top subplot
                if i == 0:
                    format_legend(ax, title="Country")
                else:
                    ax.legend().set_visible(False)
        
        # Overall figure styling
        fig.suptitle(figure_title, fontsize=18, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save figure
        filename = f"value_addition_scenario_comparison_{constraint}_subplots.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths

def plot_value_addition_gdp_share_scenario_comparison_subplots(df, output_dir):
    """Create scenario comparison subplots for value addition GDP share with 3 rows (BAU, Early Refining, Precursor)"""
    # Import the compute function from the GDP share plotting module
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from plot_gdp_share_by_country_all_constraints import compute_value_addition_share, adjust_gdp_for_inflation
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Compute the GDP share data using the existing function
    computed_df = compute_value_addition_share(df)
    
    if computed_df.empty:
        return []
    
    # Filter for 2040 scenarios only and mid demand levels
    computed_df_filtered = computed_df[
        (computed_df["value"] > 0) &
        (computed_df["value"].notna()) &
        (computed_df["scenario"].str.contains("2040")) &
        (
            ((computed_df["constraint"].str.contains("country")) & (computed_df["scenario"].str.contains("mid_min"))) |
            ((computed_df["constraint"].str.contains("region")) & (computed_df["scenario"].str.contains("mid_max")))
        )
    ].copy()
    
    if computed_df_filtered.empty:
        return []
    
    # Define scenario mapping
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining',
        'precursor_2040': 'Precursor Product'
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
        
        if len(available_scenarios) < 1:  # Need at least 1 scenario to plot
            continue
        
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 5.5 * len(available_scenarios)), sharex=False)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"Value Addition GDP Share Scenario Comparison — {constraint_type} {constraint_status}"
        
        # First pass: find maximum x-value across all scenarios for consistent scaling
        max_x_value = 0
        for scenario_key, scenario_name in scenario_mapping.items():
            if scenario_key in [s[0] for s in available_scenarios]:
                scenario_data_temp = scenario_data[scenario_key]
                # Handle both 'country' and 'iso3' column names
                country_col = 'country' if 'country' in scenario_data_temp.columns else 'iso3'
                mineral_col = 'reference_mineral_short' if 'reference_mineral_short' in scenario_data_temp.columns else 'reference_mineral'
                
                temp_grouped = scenario_data_temp.groupby([mineral_col, country_col])["value"].sum().reset_index()
                if not temp_grouped.empty:
                    temp_pivot = temp_grouped.pivot_table(
                        index=mineral_col,
                        columns=country_col,
                        values="value",
                        fill_value=0
                    )
                    if not temp_pivot.empty:
                        row_totals = temp_pivot.sum(axis=1)
                        if len(row_totals) > 0:
                            max_x_value = max(max_x_value, row_totals.max())
        
        # Add 10% padding to max value for better visualization
        if max_x_value > 0:
            max_x_value = max_x_value * 1.1
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Handle both 'country' and 'iso3' column names
            country_col = 'country' if 'country' in group_data.columns else 'iso3'
            mineral_col = 'reference_mineral_short' if 'reference_mineral_short' in group_data.columns else 'reference_mineral'
            
            # Aggregate by mineral and country
            grouped = group_data.groupby([mineral_col, country_col])["value"].sum().reset_index()
            
            if not grouped.empty:
                # Create pivot table for stacked bars
                pivot = grouped.pivot_table(
                    index=mineral_col,
                    columns=country_col,
                    values="value",
                    fill_value=0
                )
                
                # Sort by total GDP share for consistent ordering
                pivot["total"] = pivot.sum(axis=1)
                pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
                
                # Generate country color mapping
                countries = list(pivot.columns)
                country_colors = generate_country_colormap(countries)
                colors = [country_colors.get(country, "#999999") for country in countries]
                
                # Create stacked horizontal bar chart
                pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
                
                # Styling
                ax.set_title(f"{scenario_name}", fontsize=16, fontweight="bold")
                ax.set_ylabel("Mineral", fontsize=14)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel("Value Addition (% of GDP)", fontsize=14)
                ax.tick_params(labelsize=12)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Set consistent x-axis limits across all subplots
                if max_x_value > 0:
                    ax.set_xlim(0, max_x_value)
                
                # Add country labels on bars (abbreviated for space)
                for j, mineral in enumerate(pivot.index):
                    cumulative_left = 0
                    for country in pivot.columns:
                        width = pivot.loc[mineral, country]
                        if width > max(pivot.max().max() * 0.05, 0.01):  # Label significant segments
                            ax.text(
                                cumulative_left + width / 2,
                                j,
                                country,  # Country codes are already short
                                ha="center", va="center",
                                fontsize=9, color="white", fontweight="bold"
                            )
                        cumulative_left += width
                
                # Legend only on top subplot
                if i == 0:
                    format_legend(ax, title="Country")
                else:
                    ax.legend().set_visible(False)
        
        # Overall figure styling
        fig.suptitle(figure_title, fontsize=18, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save figure
        filename = f"value_addition_gdp_share_scenario_comparison_{constraint}_subplots.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths

def plot_value_addition_simple_scenario_comparison_subplots(df, output_dir):
    """Create scenario comparison subplots for simple value addition with 3 rows (BAU, Early Refining, Precursor)"""
    os.makedirs(output_dir, exist_ok=True)
    
    df = df.copy()
    
    # Filter for 2040 scenarios only and mid demand levels, processing stages > 0
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df["scenario"].str.contains("2040")) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ]
    
    if df_filtered.empty:
        return []
    
    # Calculate simple value addition 
    df_filtered = df_filtered.sort_values(by=["iso3", "reference_mineral", "scenario", "processing_stage"])
    df_filtered["value_added_simple"] = 0.0
    
    df_filtered = df_filtered.groupby(["scenario", "constraint", "iso3", "reference_mineral"]).apply(
        calc_value_added_simple
    ).reset_index(drop=True)
    
    # Convert to million USD
    df_filtered["value_added_simple_musd"] = df_filtered["value_added_simple"] / 1e6
    
    # Filter for non-zero value addition
    df_filtered = df_filtered[df_filtered["value_added_simple_musd"] > 0]
    
    if df_filtered.empty:
        return []
    
    # Define scenario mapping
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining',
        'precursor_2040': 'Precursor Product'
    }
    
    df_filtered = df_filtered.copy()
    df_filtered["reference_mineral_short"] = df_filtered["reference_mineral"].map(reference_mineral_namemap)
    
    saved_paths = []
    
    # Group by constraint only to compare scenarios within each constraint
    for constraint, constraint_group in df_filtered.groupby("constraint"):
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
        
        if len(available_scenarios) < 1:  # Need at least 1 scenario to plot
            continue
            
        # First pass: find maximum x-value across all scenarios for consistent scaling
        max_x_value = 0
        for scenario_key, scenario_name in scenario_mapping.items():
            if scenario_key in [s[0] for s in available_scenarios]:
                scenario_data_temp = scenario_data[scenario_key]
                temp_grouped = scenario_data_temp.groupby([
                    "reference_mineral_short", "iso3"
                ])["value_added_simple_musd"].sum().reset_index()
                if not temp_grouped.empty:
                    temp_pivot = temp_grouped.pivot_table(
                        index="reference_mineral_short",
                        columns="iso3",
                        values="value_added_simple_musd",
                        fill_value=0
                    )
                    if not temp_pivot.empty:
                        row_totals = temp_pivot.sum(axis=1)
                        if len(row_totals) > 0:
                            max_x_value = max(max_x_value, row_totals.max())
        
        # Add 10% padding to max value for better visualization
        if max_x_value > 0:
            max_x_value = max_x_value * 1.1
        
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 5.5 * len(available_scenarios)), sharex=False)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"Value Addition Simple Scenario Comparison — {constraint_type} {constraint_status}"
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Aggregate by mineral and country 
            grouped = group_data.groupby([
                "reference_mineral_short", "iso3"
            ])["value_added_simple_musd"].sum().reset_index()
            
            if not grouped.empty:
                # Create pivot table for stacked bars
                pivot = grouped.pivot_table(
                    index="reference_mineral_short",
                    columns="iso3", 
                    values="value_added_simple_musd",
                    fill_value=0
                )
                
                # Sort by total value addition for consistent ordering
                pivot["total"] = pivot.sum(axis=1)
                pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
                
                # Generate country color mapping
                countries = list(pivot.columns)
                country_colors = generate_country_colormap(countries)
                colors = [country_colors.get(country, "#999999") for country in countries]
                
                # Create stacked horizontal bar chart
                pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
                
                # Styling
                ax.set_title(f"{scenario_name}", fontsize=16, fontweight="bold")
                ax.set_ylabel("Mineral", fontsize=14)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel("Value Addition Simple (million USD)", fontsize=14)
                ax.tick_params(labelsize=12)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Set consistent x-axis limits across all subplots
                if max_x_value > 0:
                    ax.set_xlim(0, max_x_value)
                
                # Add country labels on bars
                annotate_bar_labels(ax, pivot, orientation="horizontal")
                
                # Legend only on top subplot
                if i == 0:
                    format_legend(ax, title="Country")
                else:
                    ax.legend().set_visible(False)
        
        # Overall figure styling
        fig.suptitle(figure_title, fontsize=18, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save figure
        filename = f"value_addition_simple_scenario_comparison_{constraint}_subplots.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths



def plot_value_addition_simple_gdp_share_scenario_comparison_subplots(df, output_dir):
    """Create scenario comparison subplots for simple value addition GDP share with 3 rows (BAU, Early Refining, Precursor)"""
    # Import the compute function from the GDP share plotting module
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from plot_gdp_share_by_country_all_constraints import compute_value_addition_simple_share, adjust_gdp_for_inflation
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Compute the GDP share data using the simple function
    computed_df = compute_value_addition_simple_share(df)
    
    if computed_df.empty:
        return []
    
    # Filter for 2040 scenarios only and mid demand levels
    computed_df_filtered = computed_df[
        (computed_df["value"] > 0) &
        (computed_df["value"].notna()) &
        (computed_df["scenario"].str.contains("2040")) &
        (
            ((computed_df["constraint"].str.contains("country")) & (computed_df["scenario"].str.contains("mid_min"))) |
            ((computed_df["constraint"].str.contains("region")) & (computed_df["scenario"].str.contains("mid_max")))
        )
    ].copy()
    
    if computed_df_filtered.empty:
        return []
    
    # Define scenario mapping
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining',
        'precursor_2040': 'Precursor Product'
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
        
        if len(available_scenarios) < 1:  # Need at least 1 scenario to plot
            continue
        
        # First pass: find maximum x-value across all scenarios for consistent scaling
        max_x_value = 0
        for scenario_key, scenario_name in scenario_mapping.items():
            if scenario_key in [s[0] for s in available_scenarios]:
                scenario_data_temp = scenario_data[scenario_key]
                # Handle both 'country' and 'iso3' column names
                country_col = 'country' if 'country' in scenario_data_temp.columns else 'iso3'
                mineral_col = 'reference_mineral_short' if 'reference_mineral_short' in scenario_data_temp.columns else 'reference_mineral'
                
                temp_grouped = scenario_data_temp.groupby([mineral_col, country_col])["value"].sum().reset_index()
                if not temp_grouped.empty:
                    temp_pivot = temp_grouped.pivot_table(
                        index=mineral_col,
                        columns=country_col,
                        values="value",
                        fill_value=0
                    )
                    if not temp_pivot.empty:
                        row_totals = temp_pivot.sum(axis=1)
                        if len(row_totals) > 0:
                            max_x_value = max(max_x_value, row_totals.max())
        
        # Add 10% padding to max value for better visualization
        if max_x_value > 0:
            max_x_value = max_x_value * 1.1
        
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 5.5 * len(available_scenarios)), sharex=False)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"Value Addition Simple GDP Share Scenario Comparison — {constraint_type} {constraint_status}"
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Handle both 'country' and 'iso3' column names
            country_col = 'country' if 'country' in group_data.columns else 'iso3'
            mineral_col = 'reference_mineral_short' if 'reference_mineral_short' in group_data.columns else 'reference_mineral'
            
            # Aggregate by mineral and country
            grouped = group_data.groupby([mineral_col, country_col])["value"].sum().reset_index()
            
            if not grouped.empty:
                # Create pivot table for stacked bars
                pivot = grouped.pivot_table(
                    index=mineral_col,
                    columns=country_col,
                    values="value",
                    fill_value=0
                )
                
                # Sort by total GDP share for consistent ordering
                pivot["total"] = pivot.sum(axis=1)
                pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
                
                # Generate country color mapping
                countries = list(pivot.columns)
                country_colors = generate_country_colormap(countries)
                colors = [country_colors.get(country, "#999999") for country in countries]
                
                # Create stacked horizontal bar chart
                pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
                
                # Styling
                ax.set_title(f"{scenario_name}", fontsize=16, fontweight="bold")
                ax.set_ylabel("Mineral", fontsize=14)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel("Value Addition Simple (% of GDP)", fontsize=14)
                ax.tick_params(labelsize=12)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Set consistent x-axis limits across all subplots
                if max_x_value > 0:
                    ax.set_xlim(0, max_x_value)
                
                # Add country labels on bars (abbreviated for space)
                for j, mineral in enumerate(pivot.index):
                    cumulative_left = 0
                    for country in pivot.columns:
                        width = pivot.loc[mineral, country]
                        if width > max(pivot.max().max() * 0.05, 0.01):  # Label significant segments
                            ax.text(
                                cumulative_left + width / 2,
                                j,
                                country,  # Country codes are already short
                                ha="center", va="center",
                                fontsize=9, color="white", fontweight="bold"
                            )
                        cumulative_left += width
                
                # Legend only on top subplot
                if i == 0:
                    format_legend(ax, title="Country")
                else:
                    ax.legend().set_visible(False)
        
        # Overall figure styling
        fig.suptitle(figure_title, fontsize=18, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save figure
        filename = f"value_addition_simple_gdp_share_scenario_comparison_{constraint}_subplots.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths
