
import pandas as pd
import matplotlib.pyplot as plt
import os
import re

from plot_config import (
    reference_minerals,
    reference_minerals_short,
    reference_mineral_colors,
    reference_mineral_colormap,
    reference_mineral_namemap
)

from plot_utils import generate_country_colormap, annotate_stacked_bars, format_legend

def plot_metric_by_mineral_all_countries(
        df,
        output_dir,
        value_column,
        ylabel,
        title_prefix,
        unit_divisor=1
    ):
    os.makedirs(output_dir, exist_ok=True)

    df["scenario_general"] = df["scenario"].apply(lambda s: re.sub(r'^\d{4}_', '', s))

    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df[value_column] > 0) &
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ].copy()

    df_filtered[value_column] = df_filtered[value_column] / unit_divisor

    country_colormap = generate_country_colormap(df["iso3"].unique())

    saved_paths = []
    for (constraint, scenario_general), group_g in df_filtered.groupby(["constraint", "scenario_general"]):
        scenario_clean = scenario_general.replace("_threshold_metal_tons", "")
        years = sorted(group_g["year"].unique())
        fig, axes = plt.subplots(len(years), 1, figsize=(14, 5 * len(years)), sharex=True)
        if len(years) == 1:
            axes = [axes]

        constraint_type = "Nationalist" if "country" in constraint else "Regionalist"
        constraint_status = "Unconstrained" if "unconstrained" in constraint else "Constrained"
        figure_title = f"{title_prefix} — {constraint_type} {constraint_status} ({scenario_clean})"

        for ax, year_val in zip(axes, years):
            group_y = group_g[group_g["year"] == year_val]
            grouped = group_y.groupby(["reference_mineral", "iso3"])[value_column].sum().reset_index()

            pivot = grouped.pivot_table(
                index="reference_mineral",
                columns="iso3",
                values=value_column,
                fill_value=0
            )

            pivot["total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")

            bars = pivot.plot(
                kind="barh",
                stacked=True,
                ax=ax,
                color=[country_colormap[c] for c in pivot.columns]
            )

            ax.set_title(f"{year_val}", fontsize=18, fontweight="bold")
            ax.set_ylabel("Mineral", fontsize=14)
            ax.set_xlabel(ylabel, fontsize=14)
            ax.tick_params(labelsize=12)
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)
            annotate_stacked_bars(ax, pivot, orientation="horizontal")
            format_legend(ax, title="Country")


        fig.suptitle(figure_title, fontsize=20, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 0.88, 0.97])

        filename = f"{title_prefix.lower().replace(' ', '_')}_{scenario_clean}_{constraint}_by_year_subplots.png".replace(" ", "_")
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        saved_paths.append(filepath)

    return saved_paths
