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

        constraint_type = "Nationalist" if "country" in constraint else "Regionalist"
        constraint_status = "Unconstrained" if "unconstrained" in constraint else "Constrained"
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

            ax.set_title(f"{year_val}", fontsize=18, fontweight="bold")
            ax.set_ylabel("Mineral", fontsize=14)
            ax.set_xlabel("Emissions (Mt CO₂eq)", fontsize=14)
            ax.tick_params(labelsize=12)
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)

            annotate_bar_labels(ax, pivot, orientation="horizontal")
            format_legend(ax, title="Country")

        fig.suptitle(figure_title, fontsize=20, fontweight="bold")
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

        constraint_type = "Nationalist" if "country" in constraint else "Regionalist"
        constraint_status = "Unconstrained" if "unconstrained" in constraint else "Constrained"
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

            ax.set_title(f"{year_val}", fontsize=18, fontweight="bold")
            ax.set_ylabel("Mineral", fontsize=14)
            ax.set_xlabel("Water Use (million m³)", fontsize=14)
            ax.tick_params(labelsize=12)
            annotate_bar_labels(ax, pivot, orientation="horizontal")
            format_legend(ax, title="Country")

        fig.suptitle(figure_title, fontsize=20, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 0.88, 0.97])

        filename = f"water_{scenario_clean}_{constraint}_by_year_subplots.png".replace(" ", "_")
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




