import pandas as pd
import matplotlib.pyplot as plt
import os
import re

from plot_config import (
    reference_mineral_colors,
    reference_mineral_namemap,
    reference_mineral_colormapshort
)

from plot_utils import format_legend, annotate_stacked_bars

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

    df_filtered = df[
        (df["processing_stage"] > 0) &
        (df[value_column] > 0) &
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

        constraint_type = "Nationalist" if "country" in constraint else "Regionalist"
        constraint_status = "Unconstrained" if "unconstrained" in constraint else "Constrained"
        figure_title = f"{title_prefix} — {constraint_type} {constraint_status} ({scenario_clean})"

        for ax, year_val in zip(axes, years):
            group_y = group_g[group_g["year"] == year_val]
            grouped = group_y.groupby(["iso3", "reference_mineral_short"])[value_column].sum().reset_index()

            pivot = grouped.pivot_table(
                index="iso3",
                columns="reference_mineral_short",
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
    return df[["country", "year", "reference_mineral", "variable", "value"]]

def compute_revenue_share(df):
    df = adjust_gdp_for_inflation(df.copy())
    df = df[df["processing_stage"] > 0]
    df["value"] = df["revenue_usd"] / df["gdp_usd"] * 100
    df["variable"] = "revenue"
    df.rename(columns={"iso3": "country"}, inplace=True)
    return df[["country", "year", "reference_mineral", "variable", "value"]]
