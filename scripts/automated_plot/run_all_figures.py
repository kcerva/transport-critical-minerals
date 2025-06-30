
import os
import pandas as pd
import json
import argparse

from plot_production_by_country_all_constraints import plot_production_by_country_all_constraints
from plot_emissions_water_all_countries import plot_metric_by_mineral_all_countries
from plot_gdp_share_by_country_all_constraints import plot_gdp_share_by_country_all_constraints

def run_plot_production(df, output_dir, config):
    goal_by_year = {
        2030: "Early refining",
        2040: "Precursor related product"
    }
    return plot_production_by_country_all_constraints(df, output_dir, goal_by_year)

def run_plot_emissions(df, output_dir, config):
    return plot_metric_by_mineral_all_countries(
        df=df,
        output_dir=output_dir,
        value_column="energy_tonsCO2eq",
        ylabel="CO₂e emissions (kt)",
        title_prefix="Emissions",
        unit_divisor=1000
    )


def run_plot_water(df, output_dir, config):
    return plot_metric_by_mineral_all_countries(
        df=df,
        output_dir=output_dir,
        value_column="water_usage_m3",
        ylabel="Water use (million m³)",
        title_prefix="Water Use",
        unit_divisor=1e6
    )

def run_plot_revenue(df, output_dir, config):
    return plot_gdp_share_by_country_all_constraints(
        df=df,
        output_dir=output_dir,
        value_column="revenue_gdp_share_usd",
        title_prefix="Revenue share of GDP",
        ylabel="Revenue share of GDP (%)"
    )

def run_plot_value_addition(df, output_dir, config):
    return plot_gdp_share_by_country_all_constraints(
        df=df,
        output_dir=output_dir,
        value_column="value_addition_gdp_share_usd",
        title_prefix="Value addition share of GDP",
        ylabel="Value addition share of GDP (%)"
    )

AVAILABLE_PLOTS = {
    "revenue_gdp_share": run_plot_revenue,
    "value_addition_gdp_share": run_plot_value_addition,
    "production_all_countries": run_plot_production,
    "emissions_all_countries": run_plot_emissions,
    "water_all_countries": run_plot_water
}

PLOT_GROUPS = {
    "all_countries": ["production_all_countries", "emissions_all_countries", "water_all_countries"],
    "core": ["production_all_countries", "emissions_all_countries"]
}

def run_selected_plots(selected=None, group=None):
    selected_plots = set()

    if group:
        for g in group:
            selected_plots.update(PLOT_GROUPS.get(g, []))

    if selected:
        selected_plots.update(selected)

    if not selected_plots:
        selected_plots = set(AVAILABLE_PLOTS.keys())

    # Load config and data
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "..", "..", "config.json")

    with open(config_path, "r") as f:
        config = json.load(f)

    data_file = os.path.join(config["paths"]["results"], "all_data.xlsx")
    figure_path = os.path.join(config["paths"]["figures"], "automated_plots", "all_countries")
    os.makedirs(figure_path, exist_ok=True)

    df = pd.read_excel(data_file)

    for name in sorted(selected_plots):
        print(f"Running: {name}")
        func = AVAILABLE_PLOTS[name]
        func(df, figure_path, config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run selected figure generators")
    parser.add_argument("--plots", nargs="*", help="Specific plot keys to run")
    parser.add_argument("--group", nargs="*", help="Plot groups to run (e.g. all_countries, core)")

    args = parser.parse_args()
    run_selected_plots(selected=args.plots, group=args.group)
