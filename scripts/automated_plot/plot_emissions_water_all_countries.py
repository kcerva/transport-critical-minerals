import pandas as pd
import matplotlib.pyplot as plt
import os
import re

from plot_config import (
    reference_mineral_colors,
    reference_mineral_namemap,
    reference_mineral_colormapshort
)

from plot_utils import format_legend, annotate_stacked_bars, annotate_bar_labels, generate_country_colormap


def plot_emissions_by_country_all_constraints(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df["emissions_mt"] = df["energy_tonsCO2eq"] / 1e6

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

        fig.suptitle(figure_title, fontsize=16, fontweight="bold")
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

        fig.suptitle(figure_title, fontsize=16, fontweight="bold")
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
    
    # Note: This function requires energy_tonsCO2eq column which is currently not available
    # Commenting out the implementation until energy data is available
    # When energy results are ready, uncomment and modify as needed
    
    print("⚠️  Emissions scenario comparison subplots skipped - energy_tonsCO2eq column not available")
    print("    This will be implemented when energy results are available")
    return []
    
    # TODO: Uncomment and modify when energy results are available
    # df = df.copy()
    # df["emissions_mt"] = df["energy_tonsCO2eq"] / 1e6
    # 
    # # Filter for 2040 scenarios only and mid demand levels  
    # df_filtered = df[
    #     (df["processing_stage"] > 0) &
    #     (df["emissions_mt"] > 0) &
    #     (df["scenario"].str.contains("2040")) &
    #     (
    #         ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
    #         ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
    #     )
    # ]
    # 
    # [Rest of implementation following the same pattern as production subplots]

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
        'early_refining_2040': 'Early Processing',
        'precursor_2040': 'Product Manufacturing'
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
        
        if len(available_scenarios) < 2:  # Need at least 2 scenarios to compare
            continue
            
        # Create subplot figure with one column, multiple rows
        fig, axes = plt.subplots(len(available_scenarios), 1, figsize=(14, 8 * len(available_scenarios)), sharex=True)
        if len(available_scenarios) == 1:
            axes = [axes]
        
        figure_title = f"Water Usage Scenario Comparison — {constraint_type} {constraint_status}"
        
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
                ax.set_title(f"{scenario_name}", fontsize=14, fontweight="bold")
                ax.set_ylabel("Mineral", fontsize=12)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel("Water Usage (million m³)", fontsize=12)
                ax.tick_params(labelsize=11)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Add country labels on bars
                annotate_bar_labels(ax, pivot, orientation="horizontal")
                
                # Legend only on top subplot
                if i == 0:
                    format_legend(ax, title="Country")
                else:
                    ax.legend().set_visible(False)
        
        # Overall figure styling
        fig.suptitle(figure_title, fontsize=16, fontweight="bold")
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




