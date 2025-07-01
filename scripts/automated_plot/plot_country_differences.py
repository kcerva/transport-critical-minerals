import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plot_utils import get_processing_type_colors, save_plot, apply_plot_layout

def plot_constraint_difference(df, country, output_path):
    colors = get_processing_type_colors()
    constraint_diff = df[(df['iso3'] == country) & (df['constraint'].isin(['country_constrained', 'country_unconstrained']))]

    diffs = []
    for year in sorted(constraint_diff['year'].unique()):
        grouped = (
            constraint_diff[constraint_diff['year'] == year]
            .groupby(['processing_type', 'constraint', 'reference_mineral'], as_index=False)['value']
            .sum()
        )
        pivoted = grouped.pivot(index=['processing_type', 'reference_mineral'], columns='constraint', values='value').fillna(0)
        if 'constrained' not in pivoted.columns or 'unconstrained' not in pivoted.columns:
            continue
        pivoted['diff'] = pivoted['constrained'] - pivoted['unconstrained']
        pivoted['year'] = year
        diffs.append(pivoted.reset_index())

    if not diffs:
        return

    all_diffs = pd.concat(diffs)
    years = all_diffs['year'].unique()
    fig = make_subplots(rows=len(years), cols=1, shared_xaxes=False, subplot_titles=[str(y) for y in years])

    for i, year in enumerate(years):
        subset = all_diffs[all_diffs['year'] == year]
        fig.add_trace(
            go.Bar(
                x=subset['processing_type'],
                y=subset['diff'],
                marker_color=[colors.get(pt, '#333') for pt in subset['processing_type']],
                name=str(year)
            ),
            row=i+1, col=1
        )

    apply_plot_layout(fig, title=f"{country}: Constrained - Unconstrained Differences", barmode='group')
    save_plot(fig, os.path.join(output_path, 'constrained_minus_unconstrained.png'))

def plot_region_difference(df, country, output_path):
    colors = get_processing_type_colors()
    diffs = []
    for constraint in df['constraint'].unique():
        sub = df[(df['constraint'] == constraint) & (df['iso3'].isin([country, 'region'])) & (df['constraint'].isin(['region_constrained', 'region_unconstrained']))]

        for year in sorted(df['year'].unique()):
            grouped = (
                sub[sub['year'] == year]
                .groupby(['processing_type', 'iso3', 'reference_mineral'], as_index=False)['value']
                .sum()
            )
            pivoted = grouped.pivot(index=['processing_type', 'reference_mineral'], columns='iso3', values='value').fillna(0)
            if 'region' not in pivoted.columns or country not in pivoted.columns:
                continue
            pivoted['diff'] = pivoted['region'] - pivoted[country]
            pivoted['year'] = year
            pivoted['constraint'] = constraint
            diffs.append(pivoted.reset_index())

    if not diffs:
        return

    all_diffs = pd.concat(diffs)

    for constraint in all_diffs['constraint'].unique():
        subset = all_diffs[all_diffs['constraint'] == constraint]
        years = subset['year'].unique()
        fig = make_subplots(rows=len(years), cols=1, shared_xaxes=False, subplot_titles=[str(y) for y in years])

        for i, year in enumerate(years):
            y_subset = subset[subset['year'] == year]
            for pt in y_subset['processing_type'].unique():
                pt_subset = y_subset[y_subset['processing_type'] == pt]
                fig.add_trace(
                    go.Bar(
                        x=[str(year)],
                        y=pt_subset['diff'],
                        name=pt,
                        marker_color=colors.get(pt, '#333')
                    ),
                    row=i+1, col=1
                )

        apply_plot_layout(fig, title=f"{country}: Region - Country ({constraint}) Differences", barmode='stack')
        filename = f"region_minus_country_{constraint}.png"
        save_plot(fig, os.path.join(output_path, filename))

def generate_country_difference_plots(df, country, base_output_path):
    output_path = os.path.join(base_output_path, 'country_figures', country, 'differences')
    os.makedirs(output_path, exist_ok=True)

    plot_constraint_difference(df, country, output_path)
    plot_region_difference(df, country, output_path)


# Example usage:
# df = pd.read_excel('all_data.xlsx')
# generate_country_difference_plots(df, 'USA', 'output')
