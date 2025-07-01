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

# === Value Addition and Revenue Computation ===
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
