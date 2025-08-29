import os
import pandas as pd
import json
import argparse

# Helper utilities

def save_computed_df(df, compute_fn, output_dir, filename_prefix):
    result = compute_fn(df)
    path = os.path.join(output_dir, f"{filename_prefix}_by_country.csv")
    result.to_csv(path, index=False)
    print(f"Saved: {path}")

def get_country_output_path(base_path, country, subfolder='single'):
    path = os.path.join(base_path, 'country_figures', country, subfolder)
    os.makedirs(path, exist_ok=True)
    return path

def parse_constraint_label(constraint):
    c_type = "National Focus" if "country" in constraint else "Regional Integration"
    c_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
    return f"{c_type} ({c_status})"

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
from plot_goal_comparisons import plot_goal_comparisons_2040, plot_production_goal_comparison_by_processing_type
from plot_supply_curves import create_supply_curves, create_supply_curve_scenario_subplots, create_supply_curve_cumulative_costs
from plot_production_differences import generate_essential_difference_plots
from plot_revenue_differences import generate_essential_revenue_difference_plots

def run_plot_production(df, output_dir, config):
    # Updated for new scenario structure - goals are determined by scenario name, not year
    goal_by_scenario = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining', 
        'precursor_2040': 'Precursor Product',
        '2022_baseline': 'Baseline'
    }
    return plot_production_by_country_all_constraints(df, output_dir, goal_by_scenario)

def run_plot_revenue(df, output_dir, config):
    save_computed_df(df, compute_revenue_share, output_dir, "revenue")

def run_plot_value_addition(df, output_dir, config):
    save_computed_df(df, compute_value_addition_share, output_dir, "value_addition")

def run_plot_emissions(df, output_dir, config):
    save_computed_df(df, compute_emissions_by_country, output_dir, "emissions")

def run_plot_water(df, output_dir, config):
    save_computed_df(df, compute_water_by_country, output_dir, "water")

def generate_single_country_plots(df, country, output_dir):
    from plot_utils import get_processing_type_colors, save_plot, apply_plot_layout
    import plotly.graph_objects as go

    colors = get_processing_type_colors()
    from plot_gdp_share_by_country_all_constraints import calculate_value_added
    from plotly.subplots import make_subplots
    country_df = df[(df['iso3'] == country) & (df['processing_stage'] > 0)]

    if ('value_added' not in df.columns or 'revenue_usd' not in df.columns or 'gdp_usd' not in df.columns) and all(col in df.columns for col in ["price_usd_per_tonne", "production_cost_usd_per_tonne", "production_tonnes", "gdp_usd"]):
        country_df = country_df.groupby(['iso3', 'reference_mineral', 'scenario']).apply(calculate_value_added).reset_index(drop=True)
        country_df['revenue_share_gdp'] = country_df['revenue_usd'] / country_df['gdp_usd'] * 100
        country_df['value_added_share_gdp'] = country_df['value_added'] / country_df['gdp_usd'] * 100

    if country_df.empty:
        print(f"No data for {country}, skipping...")
        return

    is_single_country = df['iso3'].nunique() == 1
    metrics = [
    ('production_tonnes', 'Production', 'kt' if is_single_country else 'Mt', 1e-3 if is_single_country else 1e-6),
    ('energy_tonsCO2eq', 'CO₂ Emissions', 'kt CO₂eq' if is_single_country else 'Mt CO₂eq', 1e-3 if is_single_country else 1e-6),
    ('water_usage_m3', 'Water Use', 'thousand m³' if is_single_country else 'million m³', 1e-3 if is_single_country else 1e-6),
    ('revenue_usd', 'Revenue', 'million USD' if is_single_country else 'billion USD', 1e-6 if is_single_country else 1e-9),
    ('value_added', 'Value Added', 'million USD' if is_single_country else 'billion USD', 1e-6 if is_single_country else 1e-9),
    ('revenue_share_gdp', 'Revenue Share of GDP', '%', 1),
    ('value_added_share_gdp', 'Value Added Share of GDP', '%', 1)
]

    
    for metric_col, display_name, unit, scale in metrics:
        for (constraint, scenario_general), group_df in country_df.groupby(['constraint', 'scenario']):
            filtered_df = group_df[group_df[metric_col] > 0]
            if filtered_df.empty:
                continue

            years = sorted(filtered_df['year'].unique())
            fig = make_subplots(rows=len(years), cols=1, shared_xaxes=False, subplot_titles=[str(y) for y in years])

            for i, year in enumerate(years):
                year_data = filtered_df[filtered_df['year'] == year]
                grouped = year_data.groupby('processing_type')[metric_col].sum().reset_index()
                grouped[metric_col] *= scale

                fig.add_trace(go.Bar(
                    x=grouped['processing_type'],
                    y=grouped[metric_col],
                    name=str(year),
                    marker_color=[colors.get(pt, '#999') for pt in grouped['processing_type']]
                ), row=i+1, col=1)

            # Simplify scenario label for title
            constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
            constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
            scenario_clean = scenario_general.replace("_threshold_metal_tons", "")

            title = f"{display_name} — {constraint_type} {constraint_status} ({scenario_clean})"
            fig.update_layout(
                barmode='group',
                title=title,
                xaxis_title='Processing Type',
                yaxis_title=f"{display_name} ({unit})"
            )

            filename = f"{metric_col}_{country}_{constraint}_{scenario_clean}.png".replace(" ", "_")
            save_path = os.path.join(output_dir, 'country_figures', country, 'single')
            os.makedirs(save_path, exist_ok=True)
            save_plot(fig, os.path.join(save_path, filename))

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

def run_goal_comparisons_all_countries(df, output_dir, config):
    """Generate goal comparison charts for all countries"""
    countries = [c for c in df['iso3'].unique() if c != 'region' and pd.notna(c)]
    
    goal_comparison_dir = os.path.join(output_dir, 'goal_comparisons')
    os.makedirs(goal_comparison_dir, exist_ok=True)
    
    print(f"Generating goal comparison charts for {len(countries)} countries...")
    
    for country in countries:
        try:
            df_country = df[df['iso3'] == country].copy()
            if df_country.empty:
                continue
                
            country_output_dir = os.path.join(goal_comparison_dir, country)
            
            # Production goal comparison
            plot_goal_comparisons_2040(
                df_country,
                country_output_dir,
                metric_column="production_tonnes",
                metric_title="Production",
                metric_units="kt",
                country_iso3=country
            )
            
            # Revenue goal comparison
            plot_goal_comparisons_2040(
                df_country,
                country_output_dir,
                metric_column="revenue_usd",
                metric_title="Revenue",
                metric_units="Million USD",
                country_iso3=country
            )
            
            # Production by processing type goal comparison
            plot_production_goal_comparison_by_processing_type(
                df_country,
                country_output_dir,
                country_iso3=country
            )
            
        except Exception as e:
            print(f"Error generating goal comparisons for {country}: {e}")
    
    print(f"Goal comparison charts completed. Saved to: {goal_comparison_dir}")

def run_country_docx_reports(df, output_dir, config):
    from generate_country_docx import generate_all_country_docx_reports
    
    # Use results path for DOCX output as configured
    docx_output_dir = os.path.join(config['paths']['results'], 'country_reports')
    os.makedirs(docx_output_dir, exist_ok=True)
    
    print("Generating DOCX reports for all countries...")
    generate_all_country_docx_reports(df, docx_output_dir)
    print(f"DOCX reports completed. Saved to: {docx_output_dir}")

def run_supply_curves(df, output_dir, config):
    """Generate supply curve plots for all minerals and scenarios"""
    supply_curve_dir = os.path.join(output_dir, 'supply_curves')
    os.makedirs(supply_curve_dir, exist_ok=True)
    
    print("Generating supply curve plots...")
    saved_paths = create_supply_curves(df, supply_curve_dir)
    
    print("Generating scenario comparison supply curves...")
    scenario_comparison_paths = create_supply_curve_scenario_subplots(df, supply_curve_dir)
    
    print("Generating cumulative cost supply curves...")
    cumulative_cost_dir = os.path.join(supply_curve_dir, 'cumulative_costs')
    cumulative_cost_paths = create_supply_curve_cumulative_costs(df, cumulative_cost_dir)
    
    total_paths = saved_paths + scenario_comparison_paths + cumulative_cost_paths
    print(f"Supply curve plots completed. Generated {len(total_paths)} plots total:")
    print(f"  - {len(saved_paths)} standard supply curves")
    print(f"  - {len(scenario_comparison_paths)} scenario comparison plots (aggregated stages)")
    print(f"  - {len(cumulative_cost_paths)} cumulative cost plots")
    print(f"  - Saved in: {supply_curve_dir}")

def run_production_differences(df, output_dir, config):
    """Generate production difference plots (Regional vs National)"""
    production_diff_dir = os.path.join(output_dir, 'production_differences')
    os.makedirs(production_diff_dir, exist_ok=True)
    
    print("Generating production difference plots...")
    generate_essential_difference_plots(production_diff_dir)
    print(f"Production difference plots completed. Saved to: {production_diff_dir}")

def run_revenue_differences(df, output_dir, config):
    """Generate revenue difference plots comparing policy scenarios"""
    revenue_diff_dir = os.path.join(output_dir, 'revenue_differences')
    os.makedirs(revenue_diff_dir, exist_ok=True)
    
    print("Generating revenue difference plots...")
    generate_essential_revenue_difference_plots(revenue_diff_dir)
    print(f"Revenue difference plots completed. Saved to: {revenue_diff_dir}")

AVAILABLE_PLOTS = {
    "revenue_gdp_share": run_plot_revenue,
    "value_addition_gdp_share": run_plot_value_addition,
    "production_all_countries": run_plot_production,
    "emissions_all_countries": run_plot_emissions,
    "water_all_countries": run_plot_water,
    "single_country_all": run_single_country_all,
    "country_differences": run_country_differences_all,
    "all_country_comparisons": run_all_country_comparisons,
    "goal_comparisons_all_countries": run_goal_comparisons_all_countries,
    "country_docx_reports": run_country_docx_reports,
    "supply_curves": run_supply_curves,
    "production_differences": run_production_differences,
    "revenue_differences": run_revenue_differences
}

PLOT_GROUPS = {
    "all_countries": [
        "production_all_countries", "emissions_all_countries", "water_all_countries",
        "revenue_gdp_share", "value_addition_gdp_share", "all_country_comparisons",
        "goal_comparisons_all_countries", "supply_curves", "production_differences", "revenue_differences"
    ],
    "single_countries": ["single_country_all", "country_differences"],
    "core": ["production_all_countries", "emissions_all_countries", "goal_comparisons_all_countries"],
    "reports": ["country_docx_reports"],
    "goal_analysis": ["goal_comparisons_all_countries"],
    "supply_analysis": ["supply_curves"],
    "difference_analysis": ["production_differences", "revenue_differences"]
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

    df = pd.read_excel(data_file, index_col=[0,1,2,3,4])
    df = df.reset_index()  # Convert multi-level index to columns

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
