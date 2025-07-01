import os
import pandas as pd
import json
import argparse

from plot_production_by_country_all_constraints import plot_production_by_country_all_constraints
from plot_gdp_share_by_country_all_constraints import (
    compute_value_addition_share,
    compute_revenue_share
)
from plot_emissions_water_all_countries import (
    compute_emissions_by_country,
    compute_water_by_country
)
from plot_country_differences import generate_country_difference_plots
from plot_all_countries_comparison import generate_all_country_comparison_plots

def run_plot_production(df, output_dir, config):
    goal_by_year = {
        2030: "Early refining",
        2040: "Precursor related product"
    }
    return plot_production_by_country_all_constraints(df, output_dir, goal_by_year)

def run_plot_revenue(df, output_dir, config):
    df_rev = compute_revenue_share(df)
    rev_path = os.path.join(output_dir, 'revenue_by_country.csv')
    df_rev.to_csv(rev_path, index=False)
    print(f"Saved: {rev_path}")

def run_plot_value_addition(df, output_dir, config):
    df_val = compute_value_addition_share(df)
    val_path = os.path.join(output_dir, 'value_addition_by_country.csv')
    df_val.to_csv(val_path, index=False)
    print(f"Saved: {val_path}")

def run_plot_emissions(df, output_dir, config):
    df_co2 = compute_emissions_by_country(df)
    co2_path = os.path.join(output_dir, 'emissions_by_country.csv')
    df_co2.to_csv(co2_path, index=False)
    print(f"Saved: {co2_path}")

def run_plot_water(df, output_dir, config):
    df_water = compute_water_by_country(df)
    water_path = os.path.join(output_dir, 'water_by_country.csv')
    df_water.to_csv(water_path, index=False)
    print(f"Saved: {water_path}")

def generate_single_country_plots(df, country, output_dir):
    from plot_utils import get_processing_type_colors, save_plot, apply_plot_layout
    import plotly.graph_objects as go

    colors = get_processing_type_colors()
    from plot_gdp_share_by_country_all_constraints import calculate_value_added
    country_df = df[(df['iso3'] == country) & (df['processing_stage'] > 0)]

    if ('value_added' not in df.columns or 'revenue_usd' not in df.columns or 'gdp_usd' not in df.columns) and all(col in df.columns for col in ["price_usd_per_tonne", "production_cost_usd_per_tonne", "production_tonnes", "gdp_usd"]):
        country_df = country_df.groupby(['iso3', 'reference_mineral', 'scenario']).apply(calculate_value_added).reset_index(drop=True)
        country_df['revenue_share_gdp'] = country_df['revenue_usd'] / country_df['gdp_usd'] * 100
        country_df['value_added_share_gdp'] = country_df['value_added'] / country_df['gdp_usd'] * 100

    if country_df.empty:
        print(f"No data for {country}, skipping...")
        return

    metrics = [
        ('production_tonnes', 'Production (t)'),
        ('energy_tonsCO2eq', 'CO₂ Emissions (t)'),
        ('water_usage_m3', 'Water Usage (m³)'),
        ('revenue_usd', 'Revenue (USD)'),
        ('value_added', 'Value Added (USD)'),
        ('revenue_share_gdp', 'Revenue Share of GDP (%)'),
        ('value_added_share_gdp', 'Value Added Share of GDP (%)')
    ]

    for metric_col, y_title in metrics:
        fig = go.Figure()
        subset = country_df[country_df[metric_col] > 0]

        for proc_type in subset['processing_type'].unique():
            filtered = subset[subset['processing_type'] == proc_type]
            grouped = filtered.groupby('year')[metric_col].sum().reset_index()

            fig.add_trace(go.Bar(
                x=grouped['year'],
                y=grouped[metric_col],
                name=proc_type,
                marker_color=colors.get(proc_type, '#999')
            ))

        fig.update_layout(
            barmode='group',
            title=f"{country}: {y_title}",
            xaxis_title='Year',
            yaxis_title=y_title
        )

        file_name = f"{metric_col}_{country}.png"
        save_path = os.path.join(output_dir, 'country_figures', country, 'single')
        os.makedirs(save_path, exist_ok=True)
        save_plot(fig, os.path.join(save_path, file_name))

def run_single_country_all(df, output_dir, config):
    countries = [c for c in df['iso3'].unique() if c != 'region']
    for country in countries:
        generate_single_country_plots(df, country, output_dir)

def run_country_differences_all(df, output_dir, config):
    df = df.copy()
    df = df[df['processing_stage'] > 0]  # Remove stage 0 as in original new_bar_charts.py
    df['value'] = df['production_tonnes']  # Define value column explicitly for difference plots

    countries = [c for c in df['iso3'].unique() if c != 'region']
    for country in countries:
        from plot_country_differences import generate_country_difference_plots

        # Group by processing_type and constraint to avoid duplicate rows before pivot
        df_grouped = (
            df[df['iso3'] == country]
            .groupby(['iso3', 'processing_type', 'constraint', 'year', 'reference_mineral'], as_index=False)['value']
            .sum()
        )
        generate_country_difference_plots(df_grouped, country, output_dir)

def run_all_country_comparisons(df, output_dir, config):
    generate_all_country_comparison_plots(df, output_dir)

AVAILABLE_PLOTS = {
    "revenue_gdp_share": run_plot_revenue,
    "value_addition_gdp_share": run_plot_value_addition,
    "production_all_countries": run_plot_production,
    "emissions_all_countries": run_plot_emissions,
    "water_all_countries": run_plot_water,
    "single_country_all": run_single_country_all,
    "country_differences": run_country_differences_all,
    "all_country_comparisons": run_all_country_comparisons
}

PLOT_GROUPS = {
    "all_countries": [
        "production_all_countries", "emissions_all_countries", "water_all_countries",
        "revenue_gdp_share", "value_addition_gdp_share", "all_country_comparisons"
    ],
    "single_countries": ["single_country_all", "country_differences"],
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
    figure_path = os.path.join(config["paths"]["figures"], "automated_plots")
    os.makedirs(figure_path, exist_ok=True)

    df = pd.read_excel(data_file)

    for name in sorted(selected_plots):
        print(f"Running: {name}")
        func = AVAILABLE_PLOTS[name]
        func(df, figure_path, config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run selected figure generators")
    parser.add_argument("--plots", nargs="*", help="Specific plot keys to run")
    parser.add_argument("--group", nargs="*", help="Plot groups to run (e.g. all_countries, single_countries, core)")

    args = parser.parse_args()
    run_selected_plots(selected=args.plots, group=args.group)
