
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
            return "Early Refining"
        elif 'precursor_2040' in scenario:
            return "Precursor related product"
        elif '2022_baseline' in scenario:
            return "Baseline"
        else:
            return "Unknown"
    
    def get_processing_type_for_goal(goal):
        """Map goal to expected processing_type"""
        goal_processing_map = {
            'Business as Usual': 'Beneficiation',
            'Early Refining': 'Early refining', 
            'Precursor related product': 'Precursor related product',
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

        constraint_type = "Nationalist" if "country" in constraint else "Regionalist"
        constraint_status = "Unconstrained" if "unconstrained" in constraint else "Constrained"
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
