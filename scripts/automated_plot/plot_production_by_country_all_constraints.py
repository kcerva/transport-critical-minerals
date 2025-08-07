
import os
import pandas as pd
import matplotlib.pyplot as plt
import re
from plot_utils import annotate_stacked_bars, format_legend
from plot_config import (
    reference_minerals,
    reference_minerals_short,
    reference_mineral_colors,
    reference_mineral_colormap,
    reference_mineral_namemap,
    allowed_mineral_processing
)

def plot_production_by_country_all_constraints(df, output_dir, goal_by_scenario):
    os.makedirs(output_dir, exist_ok=True)
    df["production_million_tonnes"] = df["production_tonnes"] / 1e6

    def get_goal_from_scenario(scenario):
        """Extract goal type from scenario name"""
        if 'bau_2040' in scenario:
            return "Business as Usual"
        elif 'early_refining_2040' in scenario:
            return "Early Processing"
        elif 'precursor_2040' in scenario:
            return "Product Manufacturing"
        elif '2022_baseline' in scenario:
            return "Baseline"
        else:
            return "Unknown"
    
    def get_processing_type_for_goal(goal):
        """Map goal to expected processing_type"""
        goal_processing_map = {
            'Business as Usual': 'Beneficiation',
            'Early Processing': 'Early refining', 
            'Product Manufacturing': 'Precursor related product',
            'Baseline': None  # For baseline, show all processing types
        }
        return goal_processing_map.get(goal)

    df["goal_type"] = df["scenario"].apply(get_goal_from_scenario)
    df["scenario_general"] = df["scenario"].apply(lambda s: re.sub(r'^\d{4}_', '', s))

    # Filter for relevant scenarios (mid demand scenarios)
    df_filtered = df[
        (df["processing_stage"] > 0) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max"))) |
            (df["scenario"] == "2022_baseline")  # Include baseline
        )
    ]

    # Apply goal-based processing type filtering (this is the key change)
    def should_include_row(row):
        goal = row["goal_type"]
        expected_processing_type = get_processing_type_for_goal(goal)
        
        # For baseline, include all processing types
        if goal == "Baseline":
            return True
        # For other goals, filter to specific processing type
        elif expected_processing_type:
            return row["processing_type"] == expected_processing_type
        else:
            return True
    
    df_filtered = df_filtered[df_filtered.apply(should_include_row, axis=1)]

    saved_paths = []
    for (constraint, scenario_general), group_g in df_filtered.groupby(["constraint", "scenario_general"]):
        scenario_clean = scenario_general.replace("_threshold_metal_tons", "")
        years = sorted(group_g["year"].unique())
        fig, axes = plt.subplots(len(years), 1, figsize=(14, 6 * len(years)), sharex=True)
        if len(years) == 1:
            axes = [axes]

        constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
        constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
        figure_title = f"{constraint_type} {constraint_status} ({scenario_clean})"

        for ax, year_val in zip(axes, years):
            # Since we already filtered by goal-specific processing types, 
            # we just need to filter by year
            group_y = group_g[group_g["year"] == year_val]
            grouped = group_y.groupby(["iso3", "reference_mineral"])["production_million_tonnes"].sum().reset_index()

            pivot = grouped.pivot_table(
                index="iso3",
                columns="reference_mineral",
                values="production_million_tonnes",
                fill_value=0
            )

            if pivot.empty:
                continue

            pivot["total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")

            colors = [reference_mineral_colormap.get(col, "#999999") for col in pivot.columns]
            bars = pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)

            # Get goal type for this scenario group
            goal_type = group_g["goal_type"].iloc[0] if not group_g.empty else "Unknown"
            ax.set_title(f"{year_val} - {goal_type}", fontsize=18, fontweight="bold")
            ax.set_ylabel("Country", fontsize=14)
            ax.set_xlabel("Production (million tonnes)", fontsize=14)
            ax.tick_params(labelsize=12)
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)

            for i, row in enumerate(pivot.index):
                cumulative_left = 0
                for mineral in pivot.columns:
                    width = pivot.loc[row, mineral]
                    if width > 0.05:
                        ax.text(
                            cumulative_left + width / 2,
                            i,
                            reference_mineral_namemap.get(mineral, ""),
                            ha="center", va="center",
                            fontsize=10, color="white", fontweight="bold"
                        )
                    cumulative_left += width

            ax.legend(
                title="Mineral",
                loc="upper left",
                bbox_to_anchor=(1.01, 1),
                fontsize=11,
                title_fontsize=12
            )

        fig.suptitle(figure_title, fontsize=20, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 0.88, 0.97])

        filename = f"production_{scenario_clean}_{constraint}_by_year_subplots.png".replace(" ", "_")
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)

    return saved_paths

def plot_production_scenario_comparison_subplots(df, output_dir):
    """Create proper scenario comparison subplots with 3 rows (BAU, Early Refining, Precursor)"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter for 2040 scenarios only and mid demand levels
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
    
    # Define scenario mapping
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Processing', 
        'precursor_2040': 'Product Manufacturing'
    }
    
    # Apply scenario processing type filtering like in the main function
    def get_processing_type_for_scenario(scenario):
        if 'bau_2040' in scenario:
            return 'Beneficiation'
        elif 'early_refining_2040' in scenario:
            return 'Early refining'
        elif 'precursor_2040' in scenario:
            return 'Precursor related product'
        return None
    
    # Filter by goal-specific processing types
    def should_include_row(row):
        expected_processing_type = get_processing_type_for_scenario(row["scenario"])
        return expected_processing_type and row["processing_type"] == expected_processing_type
    
    df_filtered = df_filtered[df_filtered.apply(should_include_row, axis=1)]
    
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
        
        figure_title = f"Scenario Comparison — {constraint_type} {constraint_status}"
        
        for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
            ax = axes[i]
            group_data = scenario_data[scenario_key]
            
            # Aggregate by country and mineral
            grouped = group_data.groupby(["iso3", "reference_mineral"])["production_tonnes"].sum().reset_index()
            grouped["production_million_tonnes"] = grouped["production_tonnes"] / 1e6
            
            # Create pivot for stacked bar chart
            pivot = grouped.pivot_table(
                index="iso3",
                columns="reference_mineral", 
                values="production_million_tonnes",
                fill_value=0
            )
            
            if not pivot.empty:
                pivot["total"] = pivot.sum(axis=1)
                pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
                
                # Plot stacked horizontal bar chart
                colors = [reference_mineral_colormap.get(col, "#999999") for col in pivot.columns]
                pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
                
                # Styling
                ax.set_title(f"{scenario_name}", fontsize=18, fontweight="bold")
                ax.set_ylabel("Country", fontsize=14)
                if i == len(available_scenarios) - 1:  # Only bottom subplot gets x-label
                    ax.set_xlabel("Production (million tonnes)", fontsize=14)
                ax.tick_params(labelsize=12)
                ax.grid(axis="x", linestyle="--", alpha=0.6)
                ax.set_axisbelow(True)
                
                # Add mineral labels on bars
                for j, country in enumerate(pivot.index):
                    cumulative_left = 0
                    for mineral in pivot.columns:
                        width = pivot.loc[country, mineral] 
                        if width > 0.05:  # Only label significant segments
                            ax.text(
                                cumulative_left + width / 2,
                                j,
                                reference_mineral_namemap.get(mineral, ""),
                                ha="center", va="center",
                                fontsize=10, color="white", fontweight="bold"
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
        filename = f"production_scenario_comparison_{constraint}_subplots.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths
