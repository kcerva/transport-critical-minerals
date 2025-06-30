
import pandas as pd
import matplotlib.pyplot as plt
import os
import re


from plot_config import (
    reference_minerals,
    reference_minerals_short,
    reference_mineral_colors,
    reference_mineral_colormap,
    reference_mineral_namemap,
    allowed_mineral_processing
)


def plot_production_by_country_all_constraints(df, output_dir, goal_by_year):
    os.makedirs(output_dir, exist_ok=True)
    df["production_million_tonnes"] = df["production_tonnes"] / 1e6

    def clean_scenario_name(s):
        return re.sub(r'^\d{4}_', '', s)

    df["scenario_general"] = df["scenario"].apply(clean_scenario_name)

    df_filtered = df[
        (df["processing_stage"] > 0) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ]


    # Define valid processing rules (moved to shared config)
    allowed_mineral_processing = {
        "nickel": {
            "processing_stage": [1, 2, 5],
            "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
            "processing_year": [2022, 2030, 2040]
        },
        "copper": {
            "processing_stage": [1, 3, 5],
            "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
            "processing_year": [2022, 2030, 2040]
        },
        "cobalt": {
            "processing_stage": [1, 4.1, 5],
            "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
            "processing_year": [2022, 2030, 2040]
        },
        "graphite": {
            "processing_stage": [1, 3, 4],
            "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
            "processing_year": [2022, 2030, 2040]
        },
        "manganese": {
            "processing_stage": [1, 3.1, 4.1],
            "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
            "processing_year": [2022, 2030, 2040]
        },
        "lithium": {
            "processing_stage": [1, 3, 4.2],
            "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
            "processing_year": [2022, 2030, 2040]
        }
    }

    # Apply filtering
    df_filtered = df_filtered[df_filtered.apply(
        lambda row: row["reference_mineral"] in allowed_mineral_processing and
                    row["processing_stage"] in allowed_mineral_processing[row["reference_mineral"]]["processing_stage"] and
                    row["processing_type"] in allowed_mineral_processing[row["reference_mineral"]]["processing_type"] and
                    row["year"] in allowed_mineral_processing[row["reference_mineral"]]["processing_year"],
        axis=1
    )]

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
            processing_goal = goal_by_year.get(year_val, "")
            group_y = group_g[
                (group_g["year"] == year_val) &
                (group_g["processing_type"] == processing_goal)
            ]
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

            ax.set_title(f"{year_val} - {processing_goal}", fontsize=18, fontweight="bold")
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