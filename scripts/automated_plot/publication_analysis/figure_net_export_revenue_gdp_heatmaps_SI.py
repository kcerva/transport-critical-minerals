"""
Net Export Revenue GDP Share Heatmaps - Supplementary Information Figure

Creates comprehensive heatmaps showing net export revenue as % of GDP
for all countries and scenarios in a 2-row layout:
- Top row: Net export revenue (% of GDP) values (mid-demand)
- Bottom row: Uncertainty range (high - low demand)

Layout: 2 rows × 1 column (wide format)
Scenarios: Baseline, BAU, Precursor (no Early Refining for publication)

Data sources:
- tonnage_flows_with_revenues.xlsx (for net export revenues)
- all_data.xlsx (for GDP data)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import json
from pathlib import Path

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publication_analysis.config import (
    FIGURE_SIZES, DPI_PUBLICATION, DPI_SCREEN,
    PUBLICATION_STYLE
)

# GDP inflation factors
GDP_INFLATION_FACTORS = {
    '2022': 1.0,
    '2030': 1.22,
    '2040': 1.56
}


def adjust_gdp_for_inflation(df):
    """Adjust GDP for inflation based on year"""
    df["gdp_usd"] = df.apply(
        lambda row: row["gdp_usd"] * 1.22 if "2030" in row["scenario"]
        else row["gdp_usd"] * 1.56 if "2040" in row["scenario"]
        else row["gdp_usd"],
        axis=1
    )
    return df


def prepare_country_net_export_revenue_gdp_data(df):
    """
    Prepare country-level net export revenue as % of GDP data for all scenarios

    Args:
        df: Main data DataFrame (for GDP data)

    Returns:
        dict: {scenario_label: {demand: {country: net_revenue_gdp_pct}}}
    """
    # Load config to get paths
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'

    # Load tonnage flows data
    print("    Loading tonnage flows data...")
    df_flows = pd.read_excel(flows_path, sheet_name='All_Flows')

    # Get GDP data
    print("    Preparing GDP data...")
    df_gdp = adjust_gdp_for_inflation(df.copy())
    # NOTE: GDP is repeated on each row for same country/scenario, so take max (unique non-zero value)
    # Using .first() can pick a row with GDP=0 if that row has no export revenue
    # Scenario names include year (e.g., '2022_baseline', 'bau_2040_mid_min_threshold_metal_tons')
    # so grouping by ['iso3', 'scenario'] already separates years - .max() is safe
    gdp_by_country_scenario = df_gdp.groupby(['iso3', 'scenario'])['gdp_usd'].max().to_dict()

    # Scenario configuration matching GDP heatmaps
    scenario_configs = [
        ('baseline', None, None, 'Baseline'),
        ('bau', 'min', 'constrained', 'BAU_C'),
        ('bau', 'min', 'unconstrained', 'BAU_U'),
        ('precursor', 'min', 'constrained', 'Prec_C_N'),
        ('precursor', 'min', 'unconstrained', 'Prec_U_N'),
        ('precursor', 'max', 'constrained', 'Prec_C_R'),
        ('precursor', 'max', 'unconstrained', 'Prec_U_R'),
    ]

    country_net_revenue_data = {}

    print("    Processing scenarios...")
    for goal, policy, constraint, label in scenario_configs:
        country_net_revenue_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants)
        if goal == 'baseline':
            scenario_name = '2022_baseline'
            constraint_col = 'country_unconstrained'

            # Filter for baseline
            df_scenario = df_flows[
                (df_flows['scenario'] == scenario_name) &
                (df_flows['constraint'] == constraint_col)
            ].copy()

            if df_scenario.empty:
                print(f"      Warning: No data for {label}")
                continue

            # Calculate net export revenue by country
            exports = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('iso3')['export_revenue_usd'].sum()
            imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('iso3')['import_cost_at_price_usd'].sum()

            # Calculate net revenue for each country
            all_countries = set(exports.index) | set(imports.index)
            for country in all_countries:
                export_rev = exports.get(country, 0)
                import_cost = imports.get(country, 0)
                net_revenue = export_rev - import_cost

                # Get GDP for this country/scenario
                gdp = gdp_by_country_scenario.get((country, scenario_name), 0)

                if gdp > 0:
                    gdp_pct = (net_revenue / gdp) * 100
                else:
                    gdp_pct = 0

                # Same data for low/mid/high (no demand uncertainty for baseline)
                for demand in ['low', 'mid', 'high']:
                    country_net_revenue_data[label][demand][country] = gdp_pct

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                # Build scenario name
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'

                # Build constraint column name
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                # Filter data
                df_scenario = df_flows[
                    (df_flows['scenario'] == scenario_name) &
                    (df_flows['constraint'] == constraint_col)
                ].copy()

                if df_scenario.empty:
                    print(f"      Warning: No data for {label} ({scenario_name} / {constraint_col}) / {demand}")
                    continue

                # Debug: Check if we have export data
                n_exports = len(df_scenario[df_scenario['trade_type'] == 'Export'])
                if n_exports == 0:
                    print(f"      Warning: {label} / {demand} has {len(df_scenario)} flows but ZERO exports!")

                # Calculate net export revenue by country
                exports = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('iso3')['export_revenue_usd'].sum()
                imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('iso3')['import_cost_at_price_usd'].sum()

                # Debug for Precursor mid scenarios
                if label in ['Prec_U_N', 'Prec_C_N'] and demand == 'mid':
                    print(f"      DEBUG {label}/{demand}: Found {len(exports)} countries with exports")
                    problem_countries = ['BDI', 'COD', 'NAM']
                    for pc in problem_countries:
                        if pc in exports.index:
                            print(f"        {pc}: Exports=${exports[pc]/1e9:.2f}B")

                # Calculate net revenue for each country
                all_countries = set(exports.index) | set(imports.index)
                for country in all_countries:
                    export_rev = exports.get(country, 0)
                    import_cost = imports.get(country, 0)
                    net_revenue = export_rev - import_cost

                    # Get GDP for this country/scenario
                    gdp = gdp_by_country_scenario.get((country, scenario_name), 0)

                    if gdp > 0:
                        gdp_pct = (net_revenue / gdp) * 100
                    else:
                        gdp_pct = 0

                    # Debug for problem countries
                    if label in ['Prec_U_N', 'Prec_C_N'] and demand == 'mid' and country in ['BDI', 'COD', 'NAM']:
                        print(f"        {country}: NetRev=${net_revenue/1e9:.2f}B, GDP=${gdp/1e9:.2f}B, %={gdp_pct:.2f}%")

                    country_net_revenue_data[label][demand][country] = gdp_pct

    return country_net_revenue_data


def create_net_revenue_heatmap_stacked(fig, country_data, countries_sorted):
    """
    Create stacked 2-row heatmap: Net export revenue (% GDP) values (top) + Uncertainty (bottom)

    Args:
        fig: Figure object
        country_data: dict {scenario_label: {demand: {country: net_revenue_gdp_pct}}}
        countries_sorted: list of country ISO3 codes
    """
    # Define scenario structure (7 columns total)
    scenarios = [
        ('Baseline', 'Baseline', 0),
        ('BAU_C', 'BAU\nC', 1),
        ('BAU_U', 'BAU\nU', 1),
        ('Prec_C_N', 'Prec\nC_Nat', 2),
        ('Prec_U_N', 'Prec\nU_Nat', 2),
        ('Prec_C_R', 'Prec\nC_Reg', 2),
        ('Prec_U_R', 'Prec\nU_Reg', 2),
    ]

    n_countries = len(countries_sorted)
    n_scenarios = len(scenarios)

    # Create matrices for both panels
    matrix_mid = np.zeros((n_countries, n_scenarios))
    matrix_low = np.zeros((n_countries, n_scenarios))
    matrix_high = np.zeros((n_countries, n_scenarios))
    matrix_uncertainty = np.zeros((n_countries, n_scenarios))

    # Fill matrices
    for i, country in enumerate(countries_sorted):
        for j, (label, _, _) in enumerate(scenarios):
            if label in country_data:
                mid_val = country_data[label]['mid'].get(country, 0)
                low_val = country_data[label]['low'].get(country, 0)
                high_val = country_data[label]['high'].get(country, 0)

                # Handle NaN values - replace with 0
                if np.isnan(mid_val) or np.isinf(mid_val):
                    mid_val = 0
                if np.isnan(low_val) or np.isinf(low_val):
                    low_val = 0
                if np.isnan(high_val) or np.isinf(high_val):
                    high_val = 0

                matrix_mid[i, j] = mid_val
                matrix_low[i, j] = low_val
                matrix_high[i, j] = high_val
                matrix_uncertainty[i, j] = high_val - low_val

    # Create two subplots (stacked vertically)
    gs = fig.add_gridspec(2, 1, hspace=0.35, left=0.08, right=0.92, top=0.94, bottom=0.06)
    ax_values = fig.add_subplot(gs[0, 0])
    ax_uncertainty = fig.add_subplot(gs[1, 0])

    # ========================================================================
    # Panel A: Net Export Revenue (% GDP) Values (White to Green, continuous scale)
    # ========================================================================
    # Use fixed scale 0-100% for consistent comparison across all scenarios
    vmax_values = 100.0
    data_max = np.nanmax(matrix_mid)
    print(f"    Debug: Panel A - Data max = {data_max:.2f}%, Using vmax = {vmax_values:.0f}%")

    # Create custom white-to-green colormap (pure white at 0, dark green at max)
    from matplotlib.colors import LinearSegmentedColormap
    colors_values = ['#FFFFFF', '#d9f0d3', '#a6dba0', '#5aae61', '#1b7837', '#00441b']
    cmap_values = LinearSegmentedColormap.from_list('WhiteGreen', colors_values, N=256)

    im_values = ax_values.imshow(matrix_mid, cmap=cmap_values,
                                  vmin=0, vmax=vmax_values, aspect='auto')

    # Add cell annotations for values
    for i in range(n_countries):
        for j in range(n_scenarios):
            mid_val = matrix_mid[i, j]
            # Adjust text color based on background
            text_color = 'white' if mid_val > vmax_values * 0.5 else 'black'
            weight = 'bold' if mid_val > 15.0 else 'normal'  # Bold for >15% GDP share

            # Handle NaN/inf values
            if np.isnan(mid_val) or np.isinf(mid_val):
                text = '-'
            elif mid_val < 0.1:
                text = '0'
            else:
                text = f'{mid_val:.1f}'

            ax_values.text(j, i, text, ha='center', va='center',
                          color=text_color, fontsize=9, weight=weight)

    # ========================================================================
    # Panel B: Uncertainty Range (White to Blue, continuous scale)
    # ========================================================================
    vmax_uncertainty = 20.0
    data_max_uncertainty = np.nanmax(matrix_uncertainty)
    print(f"    Debug: Panel B - Data max = {data_max_uncertainty:.2f}pp, Using vmax = {vmax_uncertainty:.0f}pp")

    # Create custom white-to-blue colormap
    colors_uncertainty = ['#FFFFFF', '#deebf7', '#9ecae1', '#4292c6', '#2171b5', '#08519c', '#08306b']
    cmap_uncertainty = LinearSegmentedColormap.from_list('WhiteBlue', colors_uncertainty, N=256)

    im_uncertainty = ax_uncertainty.imshow(matrix_uncertainty, cmap=cmap_uncertainty,
                                           vmin=0, vmax=vmax_uncertainty, aspect='auto')

    # Add cell annotations for uncertainty
    for i in range(n_countries):
        for j in range(n_scenarios):
            unc_val = matrix_uncertainty[i, j]
            # Adjust text color based on background
            text_color = 'white' if unc_val > vmax_uncertainty * 0.5 else 'black'
            weight = 'bold' if unc_val > 2.0 else 'normal'  # Bold for >2pp uncertainty

            # Handle NaN/inf values
            if np.isnan(unc_val) or np.isinf(unc_val):
                text = '-'
            elif unc_val < 0.05:
                text = '0'
            else:
                text = f'{unc_val:.1f}'

            ax_uncertainty.text(j, i, text, ha='center', va='center',
                               color=text_color, fontsize=9, weight=weight)

    # ========================================================================
    # Configure both axes
    # ========================================================================
    scenario_labels = [label for _, label, _ in scenarios]

    for ax in [ax_values, ax_uncertainty]:
        ax.set_xticks(np.arange(n_scenarios))
        ax.set_yticks(np.arange(n_countries))
        ax.set_xticklabels(scenario_labels, fontsize=10)
        ax.set_yticklabels(countries_sorted, fontsize=10)

        # Grid lines between cells
        ax.set_xticks(np.arange(n_scenarios + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(n_countries + 1) - 0.5, minor=True)
        ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)
        ax.tick_params(which='minor', size=0)

        # Add visual separators between scenario groups
        # After Baseline (index 0.5), After BAU (index 2.5)
        for separator_x in [0.5, 2.5]:
            ax.axvline(separator_x, color='black', linestyle='-', linewidth=2, zorder=10)

    # Titles
    ax_values.set_title('A) Net Export Revenue as Share of GDP by Country (Mid-demand, %)',
                       fontsize=13, fontweight='bold', pad=15)
    ax_uncertainty.set_title('B) Uncertainty Range (High - Low Demand, percentage points)',
                            fontsize=13, fontweight='bold', pad=15)

    # Add secondary x-axis labels for scenario groups
    # Panel A
    ax_values_sec = ax_values.secondary_xaxis('top')
    ax_values_sec.set_xticks([0, 1.5, 4.5])  # Centers of groups
    ax_values_sec.set_xticklabels(['Baseline\n(2022)', 'BAU\n(2040)', 'Precursor Product\n(2040)'],
                                   fontsize=11, fontweight='bold')
    ax_values_sec.tick_params(length=0)

    # Panel B
    ax_uncertainty_sec = ax_uncertainty.secondary_xaxis('top')
    ax_uncertainty_sec.set_xticks([0, 1.5, 4.5])
    ax_uncertainty_sec.set_xticklabels(['Baseline\n(2022)', 'BAU\n(2040)', 'Precursor Product\n(2040)'],
                                       fontsize=11, fontweight='bold')
    ax_uncertainty_sec.tick_params(length=0)

    # ========================================================================
    # Colorbars
    # ========================================================================
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    # Colorbar for Panel A (Net Export Revenue % GDP)
    divider_values = make_axes_locatable(ax_values)
    cax_values = divider_values.append_axes("right", size="2%", pad=0.15)
    cbar_values = fig.colorbar(im_values, cax=cax_values)
    cbar_values.set_label('Net Export Revenue\n(% of GDP)', fontsize=10, rotation=270, labelpad=25)
    cbar_values.ax.tick_params(labelsize=9)
    cbar_values.set_ticks([0, 25, 50, 75, 100])
    cbar_values.set_ticklabels(['0', '25', '50', '75', '100'])

    # Colorbar for Panel B (Uncertainty)
    divider_uncertainty = make_axes_locatable(ax_uncertainty)
    cax_uncertainty = divider_uncertainty.append_axes("right", size="2%", pad=0.15)
    cbar_uncertainty = fig.colorbar(im_uncertainty, cax=cax_uncertainty)
    cbar_uncertainty.set_label('Uncertainty (pp)', fontsize=10, rotation=270, labelpad=20)
    cbar_uncertainty.ax.tick_params(labelsize=9)
    cbar_uncertainty.set_ticks([0, vmax_uncertainty*0.25, vmax_uncertainty*0.5, vmax_uncertainty*0.75, vmax_uncertainty])
    cbar_uncertainty.set_ticklabels([f'{v:.1f}' for v in [0, vmax_uncertainty*0.25, vmax_uncertainty*0.5, vmax_uncertainty*0.75, vmax_uncertainty]])

    return im_values, im_uncertainty


def generate_net_export_revenue_gdp_heatmaps_SI(df, output_dir):
    """
    Generate supplementary information figure with net export revenue (% GDP) heatmaps

    Args:
        df: Main data DataFrame
        output_dir: Directory to save figures

    Returns:
        list: Paths to saved figures
    """
    print("  Generating SI net export revenue (% GDP) heatmaps...")

    os.makedirs(output_dir, exist_ok=True)

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Prepare country-level net export revenue data
    country_data = prepare_country_net_export_revenue_gdp_data(df)

    # Get all countries and sort by total net export revenue across all scenarios
    all_countries = set()
    for label_data in country_data.values():
        for demand_data in label_data.values():
            all_countries.update(demand_data.keys())

    # Calculate total net export revenue (% GDP) across all scenarios for sorting
    country_totals = {}
    for country in all_countries:
        total = 0
        for label in country_data.keys():
            total += country_data[label]['mid'].get(country, 0)
        country_totals[country] = total

    countries_sorted = sorted(country_totals.keys(),
                             key=lambda x: country_totals[x],
                             reverse=True)

    # Create figure with 2 rows (Values, Uncertainty) × 1 column
    fig = plt.figure(figsize=(14, 10))

    # Create heatmaps
    create_net_revenue_heatmap_stacked(fig, country_data, countries_sorted)

    # Save figure
    saved_paths = []

    # High-res PNG
    png_path = os.path.join(output_dir, 'net_export_revenue_gdp_heatmaps_SI.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight', facecolor='white')
    saved_paths.append(png_path)
    print(f"    ✓ Saved: {os.path.basename(png_path)}")

    # PDF
    pdf_path = os.path.join(output_dir, 'net_export_revenue_gdp_heatmaps_SI.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    ✓ Saved: {os.path.basename(pdf_path)}")

    # Preview PNG (lower resolution)
    preview_path = os.path.join(output_dir, 'net_export_revenue_gdp_heatmaps_SI_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight', facecolor='white')
    saved_paths.append(preview_path)
    print(f"    ✓ Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


if __name__ == '__main__':
    """Test the net export revenue GDP heatmaps SI figure generation"""
    import json

    print("Testing net export revenue GDP heatmaps SI figure generation...")

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    df = pd.read_excel(data_path)

    # Generate figure
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'publication', 'economic_indicators')
    paths = generate_net_export_revenue_gdp_heatmaps_SI(df, output_dir)

    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
