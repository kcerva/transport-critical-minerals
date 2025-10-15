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


def extract_emissions_water_data(df):
    """
    Extract water and CO2 emissions data for single-axis stacked bar charts.

    Returns:
        water_data: List of tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in million m³
        co2_data: List of tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in Mt CO2e
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # Bar 1: Baseline 2022
    baseline = df[(df['scenario'] == '2022_baseline') & (df['year'] == 2022)].copy()
    baseline['total_co2_kt'] = (baseline['transport_total_tonsCO2eq'] + baseline['energy_tonsCO2eq']) / 1000

    water_baseline = baseline.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
    co2_baseline = baseline.groupby('reference_mineral')['total_co2_kt'].sum() / 1000  # Mt

    baseline_water = [water_baseline.get(m, 0) for m in minerals]
    baseline_co2 = [co2_baseline.get(m, 0) for m in minerals]

    # Bar 2: BAU 2040 Unconstrained (mid_min = country, but for BAU country=region)
    bau = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
             (df['constraint'] == 'country_unconstrained') &
             (df['year'] == 2040)].copy()
    bau['total_co2_kt'] = (bau['transport_total_tonsCO2eq'] + bau['energy_tonsCO2eq']) / 1000

    water_bau = bau.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
    co2_bau = bau.groupby('reference_mineral')['total_co2_kt'].sum() / 1000

    bau_water = [water_bau.get(m, 0) for m in minerals]
    bau_co2 = [co2_bau.get(m, 0) for m in minerals]

    # Bar 3: Early Refining 2040 Country Unconstrained
    early_country = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                       (df['constraint'] == 'country_unconstrained') &
                       (df['year'] == 2040)].copy()
    early_country['total_co2_kt'] = (early_country['transport_total_tonsCO2eq'] + early_country['energy_tonsCO2eq']) / 1000

    water_early_country = early_country.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
    co2_early_country = early_country.groupby('reference_mineral')['total_co2_kt'].sum() / 1000

    early_country_water = [water_early_country.get(m, 0) for m in minerals]
    early_country_co2 = [co2_early_country.get(m, 0) for m in minerals]

    # Bar 4: Early Refining 2040 Region Unconstrained
    early_region = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                      (df['constraint'] == 'region_unconstrained') &
                      (df['year'] == 2040)].copy()
    early_region['total_co2_kt'] = (early_region['transport_total_tonsCO2eq'] + early_region['energy_tonsCO2eq']) / 1000

    water_early_region = early_region.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
    co2_early_region = early_region.groupby('reference_mineral')['total_co2_kt'].sum() / 1000

    early_region_water = [water_early_region.get(m, 0) for m in minerals]
    early_region_co2 = [co2_early_region.get(m, 0) for m in minerals]

    # Bar 5: Precursor 2040 Country Unconstrained
    precursor_country = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                          (df['constraint'] == 'country_unconstrained') &
                          (df['year'] == 2040)].copy()
    precursor_country['total_co2_kt'] = (precursor_country['transport_total_tonsCO2eq'] + precursor_country['energy_tonsCO2eq']) / 1000

    water_precursor_country = precursor_country.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
    co2_precursor_country = precursor_country.groupby('reference_mineral')['total_co2_kt'].sum() / 1000

    precursor_country_water = [water_precursor_country.get(m, 0) for m in minerals]
    precursor_country_co2 = [co2_precursor_country.get(m, 0) for m in minerals]

    # Bar 6: Precursor 2040 Region Unconstrained
    precursor_region = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                         (df['constraint'] == 'region_unconstrained') &
                         (df['year'] == 2040)].copy()
    precursor_region['total_co2_kt'] = (precursor_region['transport_total_tonsCO2eq'] + precursor_region['energy_tonsCO2eq']) / 1000

    water_precursor_region = precursor_region.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
    co2_precursor_region = precursor_region.groupby('reference_mineral')['total_co2_kt'].sum() / 1000

    precursor_region_water = [water_precursor_region.get(m, 0) for m in minerals]
    precursor_region_co2 = [co2_precursor_region.get(m, 0) for m in minerals]

    # Create bar data structures
    water_bars = [
        ("Baseline", baseline_water),
        ("Unconstrained", bau_water),
        ("Country Unconstrained", early_country_water),
        ("Region Unconstrained", early_region_water),
        ("Country Unconstrained", precursor_country_water),
        ("Region Unconstrained", precursor_region_water),
    ]

    co2_bars = [
        ("Baseline", baseline_co2),
        ("Unconstrained", bau_co2),
        ("Country Unconstrained", early_country_co2),
        ("Region Unconstrained", early_region_co2),
        ("Country Unconstrained", precursor_country_co2),
        ("Region Unconstrained", precursor_region_co2),
    ]

    return water_bars, co2_bars


def extract_transport_volume_data(df):
    """
    Extract transport volume data for single-axis stacked bar charts.

    Returns:
        transport_bars: List of tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in million tonne-km
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # Bar 1: Baseline 2022
    baseline = df[(df['scenario'] == '2022_baseline') & (df['year'] == 2022)].copy()
    transport_baseline = baseline.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
    baseline_transport = [transport_baseline.get(m, 0) for m in minerals]

    # Bar 2: BAU 2040 Unconstrained (mid_min = country, but for BAU country=region)
    bau = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
             (df['constraint'] == 'country_unconstrained') &
             (df['year'] == 2040)].copy()
    transport_bau = bau.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
    bau_transport = [transport_bau.get(m, 0) for m in minerals]

    # Bar 3: Early Refining 2040 Country Unconstrained
    early_country = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                       (df['constraint'] == 'country_unconstrained') &
                       (df['year'] == 2040)].copy()
    transport_early_country = early_country.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
    early_country_transport = [transport_early_country.get(m, 0) for m in minerals]

    # Bar 4: Early Refining 2040 Region Unconstrained
    early_region = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                      (df['constraint'] == 'region_unconstrained') &
                      (df['year'] == 2040)].copy()
    transport_early_region = early_region.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
    early_region_transport = [transport_early_region.get(m, 0) for m in minerals]

    # Bar 5: Precursor 2040 Country Unconstrained
    precursor_country = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                          (df['constraint'] == 'country_unconstrained') &
                          (df['year'] == 2040)].copy()
    transport_precursor_country = precursor_country.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
    precursor_country_transport = [transport_precursor_country.get(m, 0) for m in minerals]

    # Bar 6: Precursor 2040 Region Unconstrained
    precursor_region = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                         (df['constraint'] == 'region_unconstrained') &
                         (df['year'] == 2040)].copy()
    transport_precursor_region = precursor_region.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
    precursor_region_transport = [transport_precursor_region.get(m, 0) for m in minerals]

    # Create bar data structures
    transport_bars = [
        ("Baseline", baseline_transport),
        ("Unconstrained", bau_transport),
        ("Country Unconstrained", early_country_transport),
        ("Region Unconstrained", early_region_transport),
        ("Country Unconstrained", precursor_country_transport),
        ("Region Unconstrained", precursor_region_transport),
    ]

    return transport_bars


def plot_clean_stacks(bars, ylabel, total_fmt, seg_label_threshold, centers, headings, outfile):
    """Generalized stacked bar plot generator."""
    import matplotlib.pyplot as plt
    import numpy as np

    # Color scheme
    PALETTE = {
        "cobalt":   "#4682b4",
        "copper":   "#ffeb99",
        "graphite": "#66c2a5",
        "lithium":  "#cab2d6",
        "manganese":"#fdae61",
        "nickel":   "#f46d43",
    }
    ORDER  = ["cobalt","copper","graphite","lithium","manganese","nickel"]
    LABELS = ["Cobalt","Copper","Graphite","Lithium","Manganese","Nickel"]

    x = np.arange(len(bars))
    fig, ax = plt.subplots(figsize=(32, 14))
    totals = []

    # --- Draw stacked bars ---
    for xi, (_, vals) in enumerate(bars):
        bottom = 0
        for idx, k in enumerate(ORDER):
            v = vals[idx]
            ax.bar(xi, v, bottom=bottom, color=PALETTE[k], edgecolor="black")
            if v >= seg_label_threshold:
                ax.text(xi, bottom + v/2, total_fmt(v),
                        ha="center", va="center", fontsize=14, fontweight="bold")
            bottom += v
        totals.append(bottom)

    # --- Styling ---
    ax.set_ylabel(ylabel, fontsize=24, fontweight="bold")
    ax.tick_params(axis='y', labelsize=18)
    ax.set_xticks(x)

    def two_lines(lbl):
        """Split long labels over two lines for readability."""
        parts = lbl.split(" ")
        if len(parts) == 2: return parts[0] + "\n" + parts[1]
        if len(parts) == 3: return parts[0] + " " + parts[1] + "\n" + parts[2]
        return lbl

    ax.set_xticklabels([two_lines(lbl) for lbl,_ in bars], fontsize=18)

    # Scenario group headings
    ax2 = ax.secondary_xaxis('bottom')
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(centers)
    ax2.set_xticklabels(headings, fontsize=26, fontweight="bold")
    ax2.tick_params(axis='x', pad=60)

    # Totals on top with better padding calculation
    max_total = max(totals) if totals else 1
    for xi, total in enumerate(totals):
        if "CO₂" in ylabel or "Emissions" in ylabel or "Kilotonne" in ylabel:
            pad = max_total * 0.03  # 3% of max for CO2
        elif "USD" in ylabel or "Revenue" in ylabel or "Million USD" in ylabel:
            pad = max_total * 0.08  # 8% of max value for revenue (more room needed)
        elif "m³" in ylabel or "Water" in ylabel:
            pad = max_total * 0.06  # 6% of max for water
        elif "tonne" in ylabel or "Transport" in ylabel:
            pad = max_total * 0.06  # 6% for transport
        else:
            pad = max_total * 0.05  # 5% default
        ax.text(xi, total + pad, total_fmt(total),
                ha="center", va="bottom", fontsize=26, fontweight="bold")

    # Clean style
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    # Legend - positioned outside plot area to avoid obscuring data
    handles = [plt.Rectangle((0,0),1,1,color=PALETTE[k]) for k in ORDER]
    ax.legend(handles, LABELS, title="Minerals",
              fontsize=18, title_fontsize=20,
              loc="center left", bbox_to_anchor=(1.01, 0.5),
              frameon=True, fancybox=True, shadow=True)

    # Increase margins to prevent clipping - more room at top and left, reserve right for legend
    fig.subplots_adjust(left=0.06, right=0.88, top=0.91, bottom=0.22)
    plt.savefig(outfile, dpi=220)
    plt.close(fig)
    return outfile


def plot_water_single_axis_clean(df, output_dir):
    """Generate clean single-axis water usage stacked bar chart"""
    os.makedirs(output_dir, exist_ok=True)

    water_bars, _ = extract_emissions_water_data(df)

    centers = [0, 1, (2+3)/2, (4+5)/2]
    headings = ["2022 Baseline", "BAU (2040)",
                "Early Refining (2040)", "Precursor Product (2040)"]

    water_path = os.path.join(output_dir, "water_single_axis_clean.png")
    plot_clean_stacks(
        bars=water_bars,
        ylabel="Water use (million m³)",
        total_fmt=lambda v: f"{int(round(v,0))}",
        seg_label_threshold=28,
        centers=centers,
        headings=headings,
        outfile=water_path
    )

    return [water_path]


def plot_emissions_single_axis_clean(df, output_dir):
    """Generate clean single-axis CO2 emissions stacked bar chart"""
    os.makedirs(output_dir, exist_ok=True)

    _, co2_bars = extract_emissions_water_data(df)

    centers = [0, 1, (2+3)/2, (4+5)/2]
    headings = ["Baseline (2022)", "BAU (2040)",
                "Early Refining (2040)", "Precursor Product (2040)"]

    co2_path = os.path.join(output_dir, "co2_single_axis_clean.png")
    plot_clean_stacks(
        bars=co2_bars,
        ylabel="Megatonne CO₂e",
        total_fmt=lambda v: f"{v:.2f}",
        seg_label_threshold=0.03,
        centers=centers,
        headings=headings,
        outfile=co2_path
    )

    return [co2_path]


def plot_transport_volume_single_axis_clean(df, output_dir):
    """Generate clean single-axis transport volume stacked bar chart"""
    os.makedirs(output_dir, exist_ok=True)

    transport_bars = extract_transport_volume_data(df)

    centers = [0, 1, (2+3)/2, (4+5)/2]
    headings = ["Baseline (2022)", "BAU (2040)",
                "Early Refining (2040)", "Precursor Product (2040)"]

    transport_path = os.path.join(output_dir, "transport_volume_single_axis_clean.png")
    plot_clean_stacks(
        bars=transport_bars,
        ylabel="Transport Volume (Million tonne km)",
        total_fmt=lambda v: f"{int(round(v,0))}",
        seg_label_threshold=300,  # 300 million tonkm
        centers=centers,
        headings=headings,
        outfile=transport_path
    )

    return [transport_path]


def extract_emissions_water_data_comparison(df):
    """
    Extract both constrained and unconstrained data for 2040 scenarios (NO baseline).

    Returns 10 bars: BAU (C+U), Early Refining (CC+CU+RC+RU), Precursor (CC+CU+RC+RU)

    Returns:
        water_bars: List of 10 tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in million m³
        co2_bars: List of 10 tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in Mt CO2e
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # BAU 2040 - Constrained and Unconstrained
    bau_constrained = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
                         (df['constraint'] == 'country_constrained') &
                         (df['year'] == 2040)].copy()
    bau_constrained['total_co2_kt'] = (bau_constrained['transport_total_tonsCO2eq'] + bau_constrained['energy_tonsCO2eq']) / 1000

    bau_unconstrained = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
                           (df['constraint'] == 'country_unconstrained') &
                           (df['year'] == 2040)].copy()
    bau_unconstrained['total_co2_kt'] = (bau_unconstrained['transport_total_tonsCO2eq'] + bau_unconstrained['energy_tonsCO2eq']) / 1000

    # Early Refining 2040 - All 4 combinations
    early_country_constrained = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                                   (df['constraint'] == 'country_constrained') &
                                   (df['year'] == 2040)].copy()
    early_country_constrained['total_co2_kt'] = (early_country_constrained['transport_total_tonsCO2eq'] + early_country_constrained['energy_tonsCO2eq']) / 1000

    early_country_unconstrained = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                                     (df['constraint'] == 'country_unconstrained') &
                                     (df['year'] == 2040)].copy()
    early_country_unconstrained['total_co2_kt'] = (early_country_unconstrained['transport_total_tonsCO2eq'] + early_country_unconstrained['energy_tonsCO2eq']) / 1000

    early_region_constrained = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                                  (df['constraint'] == 'region_constrained') &
                                  (df['year'] == 2040)].copy()
    early_region_constrained['total_co2_kt'] = (early_region_constrained['transport_total_tonsCO2eq'] + early_region_constrained['energy_tonsCO2eq']) / 1000

    early_region_unconstrained = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                                    (df['constraint'] == 'region_unconstrained') &
                                    (df['year'] == 2040)].copy()
    early_region_unconstrained['total_co2_kt'] = (early_region_unconstrained['transport_total_tonsCO2eq'] + early_region_unconstrained['energy_tonsCO2eq']) / 1000

    # Precursor 2040 - All 4 combinations
    precursor_country_constrained = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                                       (df['constraint'] == 'country_constrained') &
                                       (df['year'] == 2040)].copy()
    precursor_country_constrained['total_co2_kt'] = (precursor_country_constrained['transport_total_tonsCO2eq'] + precursor_country_constrained['energy_tonsCO2eq']) / 1000

    precursor_country_unconstrained = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                                         (df['constraint'] == 'country_unconstrained') &
                                         (df['year'] == 2040)].copy()
    precursor_country_unconstrained['total_co2_kt'] = (precursor_country_unconstrained['transport_total_tonsCO2eq'] + precursor_country_unconstrained['energy_tonsCO2eq']) / 1000

    precursor_region_constrained = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                                      (df['constraint'] == 'region_constrained') &
                                      (df['year'] == 2040)].copy()
    precursor_region_constrained['total_co2_kt'] = (precursor_region_constrained['transport_total_tonsCO2eq'] + precursor_region_constrained['energy_tonsCO2eq']) / 1000

    precursor_region_unconstrained = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                                        (df['constraint'] == 'region_unconstrained') &
                                        (df['year'] == 2040)].copy()
    precursor_region_unconstrained['total_co2_kt'] = (precursor_region_unconstrained['transport_total_tonsCO2eq'] + precursor_region_unconstrained['energy_tonsCO2eq']) / 1000

    # Aggregate water and CO2 for each scenario
    def aggregate_data(data_frame):
        water = data_frame.groupby('reference_mineral')['water_usage_m3'].sum() / 1e6
        co2 = data_frame.groupby('reference_mineral')['total_co2_kt'].sum() / 1000
        return [water.get(m, 0) for m in minerals], [co2.get(m, 0) for m in minerals]

    bau_c_water, bau_c_co2 = aggregate_data(bau_constrained)
    bau_u_water, bau_u_co2 = aggregate_data(bau_unconstrained)
    early_cc_water, early_cc_co2 = aggregate_data(early_country_constrained)
    early_cu_water, early_cu_co2 = aggregate_data(early_country_unconstrained)
    early_rc_water, early_rc_co2 = aggregate_data(early_region_constrained)
    early_ru_water, early_ru_co2 = aggregate_data(early_region_unconstrained)
    prec_cc_water, prec_cc_co2 = aggregate_data(precursor_country_constrained)
    prec_cu_water, prec_cu_co2 = aggregate_data(precursor_country_unconstrained)
    prec_rc_water, prec_rc_co2 = aggregate_data(precursor_region_constrained)
    prec_ru_water, prec_ru_co2 = aggregate_data(precursor_region_unconstrained)

    # Create 10 bars (NO baseline)
    water_bars = [
        ("Constrained", bau_c_water),
        ("Unconstrained", bau_u_water),
        ("Country Constrained", early_cc_water),
        ("Country Unconstrained", early_cu_water),
        ("Region Constrained", early_rc_water),
        ("Region Unconstrained", early_ru_water),
        ("Country Constrained", prec_cc_water),
        ("Country Unconstrained", prec_cu_water),
        ("Region Constrained", prec_rc_water),
        ("Region Unconstrained", prec_ru_water),
    ]

    co2_bars = [
        ("Constrained", bau_c_co2),
        ("Unconstrained", bau_u_co2),
        ("Country Constrained", early_cc_co2),
        ("Country Unconstrained", early_cu_co2),
        ("Region Constrained", early_rc_co2),
        ("Region Unconstrained", early_ru_co2),
        ("Country Constrained", prec_cc_co2),
        ("Country Unconstrained", prec_cu_co2),
        ("Region Constrained", prec_rc_co2),
        ("Region Unconstrained", prec_ru_co2),
    ]

    return water_bars, co2_bars


def extract_transport_volume_data_comparison(df):
    """
    Extract both constrained and unconstrained transport volume data for 2040 scenarios (NO baseline).

    Returns 10 bars: BAU (C+U), Early Refining (CC+CU+RC+RU), Precursor (CC+CU+RC+RU)

    Returns:
        transport_bars: List of 10 tuples (label, [cobalt, copper, graphite, lithium, manganese, nickel]) in million tonne-km
    """
    minerals = ['cobalt', 'copper', 'graphite', 'lithium', 'manganese', 'nickel']

    # BAU 2040 - Constrained and Unconstrained
    bau_constrained = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
                         (df['constraint'] == 'country_constrained') &
                         (df['year'] == 2040)].copy()

    bau_unconstrained = df[(df['scenario'] == 'bau_2040_mid_min_threshold_metal_tons') &
                           (df['constraint'] == 'country_unconstrained') &
                           (df['year'] == 2040)].copy()

    # Early Refining 2040 - All 4 combinations
    early_country_constrained = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                                   (df['constraint'] == 'country_constrained') &
                                   (df['year'] == 2040)].copy()

    early_country_unconstrained = df[(df['scenario'] == 'early_refining_2040_mid_min_threshold_metal_tons') &
                                     (df['constraint'] == 'country_unconstrained') &
                                     (df['year'] == 2040)].copy()

    early_region_constrained = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                                  (df['constraint'] == 'region_constrained') &
                                  (df['year'] == 2040)].copy()

    early_region_unconstrained = df[(df['scenario'] == 'early_refining_2040_mid_max_threshold_metal_tons') &
                                    (df['constraint'] == 'region_unconstrained') &
                                    (df['year'] == 2040)].copy()

    # Precursor 2040 - All 4 combinations
    precursor_country_constrained = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                                       (df['constraint'] == 'country_constrained') &
                                       (df['year'] == 2040)].copy()

    precursor_country_unconstrained = df[(df['scenario'] == 'precursor_2040_mid_min_threshold_metal_tons') &
                                         (df['constraint'] == 'country_unconstrained') &
                                         (df['year'] == 2040)].copy()

    precursor_region_constrained = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                                      (df['constraint'] == 'region_constrained') &
                                      (df['year'] == 2040)].copy()

    precursor_region_unconstrained = df[(df['scenario'] == 'precursor_2040_mid_max_threshold_metal_tons') &
                                        (df['constraint'] == 'region_unconstrained') &
                                        (df['year'] == 2040)].copy()

    # Aggregate transport volume for each scenario
    def aggregate_transport(data_frame):
        transport = data_frame.groupby('reference_mineral')['transport_total_tonkm'].sum() / 1e6
        return [transport.get(m, 0) for m in minerals]

    bau_c_transport = aggregate_transport(bau_constrained)
    bau_u_transport = aggregate_transport(bau_unconstrained)
    early_cc_transport = aggregate_transport(early_country_constrained)
    early_cu_transport = aggregate_transport(early_country_unconstrained)
    early_rc_transport = aggregate_transport(early_region_constrained)
    early_ru_transport = aggregate_transport(early_region_unconstrained)
    prec_cc_transport = aggregate_transport(precursor_country_constrained)
    prec_cu_transport = aggregate_transport(precursor_country_unconstrained)
    prec_rc_transport = aggregate_transport(precursor_region_constrained)
    prec_ru_transport = aggregate_transport(precursor_region_unconstrained)

    # Create 10 bars (NO baseline)
    transport_bars = [
        ("Constrained", bau_c_transport),
        ("Unconstrained", bau_u_transport),
        ("Country Constrained", early_cc_transport),
        ("Country Unconstrained", early_cu_transport),
        ("Region Constrained", early_rc_transport),
        ("Region Unconstrained", early_ru_transport),
        ("Country Constrained", prec_cc_transport),
        ("Country Unconstrained", prec_cu_transport),
        ("Region Constrained", prec_rc_transport),
        ("Region Unconstrained", prec_ru_transport),
    ]

    return transport_bars


def plot_water_single_axis_comparison(df, output_dir):
    """Generate comparison chart with both constrained and unconstrained (10 bars, no baseline)"""
    os.makedirs(output_dir, exist_ok=True)

    water_bars, _ = extract_emissions_water_data_comparison(df)

    # Centers for 10 bars: [BAU×2] [Early×4] [Precursor×4]
    centers = [(0+1)/2, (2+3+4+5)/4, (6+7+8+9)/4]
    headings = ["BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    water_path = os.path.join(output_dir, "water_single_axis_constrained_vs_unconstrained.png")
    plot_clean_stacks(
        bars=water_bars,
        ylabel="Water use (million m³)",
        total_fmt=lambda v: f"{int(round(v,0))}",
        seg_label_threshold=28,
        centers=centers,
        headings=headings,
        outfile=water_path
    )

    return [water_path]


def plot_emissions_single_axis_comparison(df, output_dir):
    """Generate comparison chart with both constrained and unconstrained (10 bars, no baseline)"""
    os.makedirs(output_dir, exist_ok=True)

    _, co2_bars = extract_emissions_water_data_comparison(df)

    # Centers for 10 bars: [BAU×2] [Early×4] [Precursor×4]
    centers = [(0+1)/2, (2+3+4+5)/4, (6+7+8+9)/4]
    headings = ["BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    co2_path = os.path.join(output_dir, "co2_single_axis_constrained_vs_unconstrained.png")
    plot_clean_stacks(
        bars=co2_bars,
        ylabel="Megatonne CO₂e",
        total_fmt=lambda v: f"{v:.2f}",
        seg_label_threshold=0.03,
        centers=centers,
        headings=headings,
        outfile=co2_path
    )

    return [co2_path]


def plot_transport_volume_single_axis_comparison(df, output_dir):
    """Generate comparison chart with both constrained and unconstrained (10 bars, no baseline)"""
    os.makedirs(output_dir, exist_ok=True)

    transport_bars = extract_transport_volume_data_comparison(df)

    # Centers for 10 bars: [BAU×2] [Early×4] [Precursor×4]
    centers = [(0+1)/2, (2+3+4+5)/4, (6+7+8+9)/4]
    headings = ["BAU (2040)", "Early Refining (2040)", "Precursor Product (2040)"]

    transport_path = os.path.join(output_dir, "transport_volume_single_axis_constrained_vs_unconstrained.png")
    plot_clean_stacks(
        bars=transport_bars,
        ylabel="Transport Volume (Million tonne km)",
        total_fmt=lambda v: f"{int(round(v,0))}",
        seg_label_threshold=300,  # 300 million tonkm
        centers=centers,
        headings=headings,
        outfile=transport_path
    )

    return [transport_path]
