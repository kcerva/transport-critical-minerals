import os
import pandas as pd
import plotly.express as px
from plot_utils import get_mineral_colors, save_plot, apply_plot_layout
from plot_gdp_share_by_country_all_constraints import compute_value_addition_share, compute_revenue_share
from plot_emissions_water_all_countries import compute_emissions_by_country, compute_water_by_country

def plot_variable_by_country(df, variable, output_path):
    colors = get_mineral_colors()
    for year in sorted(df['year'].unique()):
        sub = df[(df['variable'] == variable) & (df['year'] == year)]
        if sub.empty:
            continue
        fig = px.bar(
            sub,
            x='country',
            y='value',
            color='reference_mineral',
            color_discrete_map=colors,
            title=f"{variable.upper()} by Country ({year})"
        )
        apply_plot_layout(fig, title=f"{variable.upper()} by Country ({year})")
        save_plot(fig, os.path.join(output_path, f"{variable}_{year}_by_country.png"))

def generate_all_country_comparison_plots(df, base_output_path):
    output_path = os.path.join(base_output_path, 'all_country_figures')
    os.makedirs(output_path, exist_ok=True)

    # Compute derived metrics if not present
    derived_frames = []

    derived_frames.append(compute_value_addition_share(df))
    derived_frames.append(compute_revenue_share(df))
    derived_frames.append(compute_emissions_by_country(df))
    derived_frames.append(compute_water_by_country(df))

    df_combined = pd.concat([df] + derived_frames, ignore_index=True)

    for variable in ['value', 'value_addition', 'revenue', 'co2', 'water']:
        plot_variable_by_country(df_combined, variable, output_path)


# Example usage:
# df = pd.read_excel('all_data.xlsx')
# generate_all_country_comparison_plots(df, 'output')

