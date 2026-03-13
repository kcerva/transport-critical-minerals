"""
Infrastructure Indicators Figure V3

Adds Panel A (aggregated transport flow maps) on top of the existing Panels B-G
from figure_infrastructure_indicators_v2.py.

Layout:
- Row 0: Panel A - Three transport flow maps + key
    (2022 Baseline | BAU Mid No Env Constraints | Precursor Mid No Env Constraints)
- Row 1: Panels B & C (Transport Volume by Mineral | Electricity Capacity by Mineral)
- Row 2: Panels D & E (Transport Volume by Country | Electricity Capacity Change)
- Row 3: Panels F & G (Transport Costs | Energy Costs)

Output: infrastructure_indicators_v3_*.png/pdf
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import LineString
from collections import OrderedDict

# Add necessary directories to sys.path
_this_dir = os.path.dirname(os.path.abspath(__file__))
_auto_plot_dir = os.path.dirname(_this_dir)  # scripts/automated_plot
_scripts_dir = os.path.dirname(_auto_plot_dir)  # scripts/
_plot_dir = os.path.join(_scripts_dir, 'plot')  # scripts/plot

if _auto_plot_dir not in sys.path:
    sys.path.insert(0, _auto_plot_dir)
if _plot_dir not in sys.path:
    sys.path.insert(0, _plot_dir)

# Import from scripts/plot/ (map utilities)
from map_plotting_utils import (
    map_background_and_bounds,
    plot_ccg_basemap,
    generate_weight_bins,
    load_config as map_load_config
)

# Import from scripts/automated_plot/
from publication_analysis.config import (
    DPI_PUBLICATION, DPI_SCREEN, PUBLICATION_STYLE
)
from plot_config import reference_mineral_colormap
from plot_utils import generate_country_colormap

# Import existing infrastructure indicators functions
from publication_analysis.figure_infrastructure_indicators_v2 import (
    prepare_infrastructure_data,
    plot_stacked_panel,
    plot_electricity_capacity_change_panel,
    load_electricity_demand_data,
    SCENARIO_CONFIG,
    MINERAL_ORDER,
    ENERGY_COST_ORDER,
    ENERGY_COST_COLORS,
)

# ============================================================
# Flow map configuration
# ============================================================

# Transport modes and colors
MODES = ["road", "rail"]
MODE_TYPES = ["Roads", "Railways"]
MODE_COLORS = ["#543005", "#003c30"]

# Flow column
FLOW_COLUMN = "final_stage_production_tons"

# Flow map scenarios
FLOW_MAP_CONFIGS = [
    {
        "scenario": "bau",
        "year": 2022,
        "percentile": "baseline",
        "efficient_scale": "min_threshold_metal_tons",
        "country_case": "country",
        "constraint": "unconstrained",
        "combination": "combined",
        "title": "2022 Baseline",
    },
    {
        "scenario": "bau",
        "year": 2040,
        "percentile": "mid",
        "efficient_scale": "min_threshold_metal_tons",
        "country_case": "country",
        "constraint": "unconstrained",
        "combination": "combined",
        "title": "BAU_U",
    },
    {
        "scenario": "precursor",
        "year": 2040,
        "percentile": "mid",
        "efficient_scale": "max_threshold_metal_tons",
        "country_case": "region",
        "constraint": "unconstrained",
        "combination": "combined",
        "title": "Prec_U_R",
    },
]

# Flow weight bins (fixed ranges for consistency)
MIN_FLOW = 0.03
MAX_FLOW = 12000000.0
FLOW_RANGES = [MIN_FLOW, 2e5, 1e6, 4e6, 8e6, MAX_FLOW]
LINE_STEPS = 6
WIDTH_STEP = 0.08


# ============================================================
# Flow map helper functions
# ============================================================

def build_flow_filename(fc):
    """
    Build the geoparquet filename for a flow scenario.

    Args:
        fc: Flow config dict

    Returns:
        str: Filename string (without edges_/nodes_ prefix)
    """
    scn = fc['scenario'].replace(" ", "_")
    y = fc['year']
    p = fc['percentile']
    e = fc['efficient_scale']
    cnt = fc['country_case']
    con = fc['constraint']
    combination = fc['combination']

    if y == 2022:
        layer_name = f"{p}"
    else:
        layer_name = f"{p}_{e}_{scn}"

    if combination is not None:
        results_gpq = f"{combination}_flows_{layer_name}_{y}_{cnt}_{con}.geoparquet"
    else:
        results_gpq = f"flows_{layer_name}_{y}_{cnt}_{con}.geoparquet"

    return results_gpq


def load_flow_panel_data(config, fc, ccg_isos):
    """
    Load and process flow data for a single map panel.

    Args:
        config: Configuration dictionary with paths
        fc: Flow config dict
        ccg_isos: List of CCG country ISO codes

    Returns:
        GeoDataFrame with flow_column, mode, geometry, or None if file doesn't exist
    """
    output_data_path = config['paths']['results']
    flow_data_folder = os.path.join(output_data_path, "aggregated_node_edge_flows")

    results_gpq = build_flow_filename(fc)
    edge_file_path = os.path.join(flow_data_folder, f"edges_{results_gpq}")

    if not os.path.exists(edge_file_path):
        print(f"      Warning: Edge file not found: {edge_file_path}")
        return None

    edges_flows_df = gpd.read_parquet(edge_file_path)
    edges_flows_df = edges_flows_df[~edges_flows_df.geometry.isna()]

    nodes_flows_df = gpd.read_parquet(
        os.path.join(flow_data_folder, f"nodes_{results_gpq}"))

    # Filter to CCG country road/rail nodes
    nodes = nodes_flows_df[
        (nodes_flows_df["iso3"].isin(ccg_isos)) &
        (nodes_flows_df["mode"].isin(["road", "rail"]))
    ]["id"].values.tolist()
    del nodes_flows_df

    # Filter edges connected to CCG nodes
    edges_flows_df = edges_flows_df[
        (edges_flows_df["from_id"].isin(nodes)) |
        (edges_flows_df["to_id"].isin(nodes))
    ]
    del nodes

    # Calculate combined flow column
    edges_flows_df[FLOW_COLUMN] = (
        edges_flows_df[f"{FLOW_COLUMN}_export"] +
        edges_flows_df[f"{FLOW_COLUMN}_inter"]
    )
    edges_flows_df = edges_flows_df[edges_flows_df[FLOW_COLUMN] > 0]

    return edges_flows_df


def set_geometry_buffer(x, value_column, width_by_range):
    """Assign buffer width based on flow value and weight bins."""
    for (nmin, nmax), width in width_by_range.items():
        if nmin <= x[value_column] < nmax:
            return width
    return 0


def render_flow_panel(ax, edges_df, title, ccg_isos, tonnage_weights,
                      title_fontsize=12):
    """
    Render a single transport flow map panel on the provided axis.

    Args:
        ax: Matplotlib axis
        edges_df: GeoDataFrame with flow data
        title: Panel title string
        ccg_isos: List of CCG country ISO codes
        tonnage_weights: OrderedDict of weight bins from generate_weight_bins
        title_fontsize: Font size for panel title
    """
    ax = plot_ccg_basemap(
        ax,
        include_continents=["Africa"],
        include_countries=ccg_isos,
        include_labels=True
    )
    ax.set_title(title, fontsize=title_fontsize, fontweight="bold")

    edges_df = edges_df.copy()
    edges_df = edges_df.sort_values(by=FLOW_COLUMN, ascending=False)

    # Calculate linewidth from tonnage weights
    edges_df["linewidth"] = edges_df.apply(
        lambda x: set_geometry_buffer(x, FLOW_COLUMN, tonnage_weights),
        axis=1
    )

    # Buffer geometry by linewidth
    edges_df["geometry"] = edges_df.apply(
        lambda x: x.geometry.buffer(x.linewidth), axis=1
    )

    # Plot by mode with different colors
    for mt, mc in zip(MODES, MODE_COLORS):
        p_df = edges_df[edges_df["mode"] == mt]
        if not p_df.empty:
            p_df.geometry.plot(
                ax=ax, facecolor=mc, edgecolor='none',
                linewidth=0, alpha=0.7
            )


def render_flow_key(ax, xl, yl, dxl, dyl, tonnage_weights,
                    textfontsize=8):
    """
    Render the legend/key for flow map panels.

    Args:
        ax: Matplotlib axis for the key panel
        xl, yl: Map x/y limits
        dxl, dyl: Map x/y extents
        tonnage_weights: OrderedDict of weight bins
        textfontsize: Font size for text
    """
    ax.set_ylim(yl)
    ax.set_xlim(xl[0] + 0.5 * dxl, xl[1])

    xk = xl[0] + 0.60 * dxl
    xt = xk - 0.04 * dxl

    keys = ['edge_tonnage', 'mode']

    for ky in range(len(keys)):
        key = keys[ky]
        if key == "edge_tonnage":
            Nk = len(tonnage_weights)
            yk = yl[0] + np.linspace(0.15 * dyl, 0.4 * dyl, Nk)
            yt = yk[-1] + np.diff(yk[-3:-1])

            widths = []
            min_max_vals = []
            for (nmin, nmax), w in tonnage_weights.items():
                widths.append(w)
                min_max_vals.append((nmin, nmax))
            min_max_vals = min_max_vals[::-1]

            # Create key lines with varying widths
            key_1 = gpd.GeoDataFrame(
                geometry=gpd.points_from_xy(np.ones(Nk) * xk, yk))
            key_1["id"] = key_1.index.values.tolist()
            key_2 = gpd.GeoDataFrame(
                geometry=gpd.points_from_xy(1.03 * np.ones(Nk) * xk, yk))
            key_2["id"] = key_2.index.values.tolist()
            key_df = pd.concat([key_1, key_2], axis=0, ignore_index=False)
            key_df = key_df.groupby(['id'])['geometry'].apply(
                lambda x: LineString(x.tolist())).reset_index()
            key_df = gpd.GeoDataFrame(key_df, geometry='geometry')
            key_df["buffersize"] = widths[::-1]
            key_df["geometry"] = key_df.apply(
                lambda x: x.geometry.buffer(x.buffersize), axis=1)
            key_df = gpd.GeoDataFrame(key_df, geometry='geometry')
            key_df.geometry.plot(
                ax=ax, linewidth=0, facecolor='k', edgecolor='none')

            ax.text(xt, yt, 'Links annual output\n(Mt)',
                    weight='bold', fontsize=textfontsize, va='center')
            for k in range(Nk):
                nmin_mt = min_max_vals[k][0] / 1e6
                nmax_mt = min_max_vals[k][1] / 1e6
                ax.text(xk, yk[k],
                        '     {:.1f} - {:.1f}'.format(nmin_mt, nmax_mt),
                        fontsize=textfontsize, va='center')

        else:  # mode
            Nk = len(MODE_TYPES)
            yk = yl[0] + np.linspace(0.15 * dyl, 0.20 * dyl, Nk) + 0.4 * ky * dyl
            yt = yk[-1] + np.diff(yk)[0]
            ax.text(xt, yt, 'Mode type',
                    weight='bold', fontsize=textfontsize, va='center')
            for k in range(Nk):
                ax.text(xk, yk[k], '   ' + MODE_TYPES[k].capitalize(),
                        fontsize=textfontsize, va='center')
                ax.plot(xk, yk[k], 's',
                        mfc=MODE_COLORS[k],
                        mec=MODE_COLORS[k], ms=10)


# ============================================================
# Main figure creation
# ============================================================

def create_infrastructure_indicators_v3_figure(df, output_dir, config):
    """
    Generate infrastructure indicators V3 figure with Panel A flow maps + Panels B-G charts.

    Args:
        df: Main data DataFrame (all_data.xlsx)
        output_dir: Output directory for figures
        config: Configuration dictionary with paths

    Returns:
        List of saved file paths
    """
    print("  Generating infrastructure indicators V3 figure (with flow maps)...")

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # ----------------------------------------------------------
    # Load flow map data
    # ----------------------------------------------------------
    processed_data_path = config['paths']['data']
    ccg_countries = pd.read_csv(
        os.path.join(processed_data_path, "admin_boundaries", "ccg_country_codes.csv"))
    ccg_isos = ccg_countries[
        ccg_countries["ccg_country"] == 1]["iso_3digit_alpha"].values.tolist()

    _, _, xl, yl = map_background_and_bounds(include_countries=ccg_isos)
    dxl = abs(np.diff(xl))[0]
    dyl = abs(np.diff(yl))[0]

    print("    Loading flow data...")
    flow_data = []
    make_plot = True
    for fc in FLOW_MAP_CONFIGS:
        print(f"      Loading: {fc['title']}")
        edges_df = load_flow_panel_data(config, fc, ccg_isos)
        if edges_df is None:
            make_plot = False
            print(f"      SKIPPING: Data not found for {fc['title']}")
        else:
            flow_data.append((fc, edges_df))

    if not make_plot:
        print("    Warning: Some flow data missing, skipping Panel A maps")
        flow_data = []

    # Generate weight bins for flow line widths
    tonnage_weights = generate_weight_bins(
        FLOW_RANGES,
        width_step=WIDTH_STEP,
        n_steps=LINE_STEPS,
        interpolation='fisher-jenks'
    )

    # ----------------------------------------------------------
    # Load electricity demand data
    # ----------------------------------------------------------
    electricity_data = None
    electricity_data = load_electricity_demand_data(config)
    if electricity_data:
        print("    Loaded electricity demand data")
    else:
        print("    Warning: Could not load electricity demand data")

    # ----------------------------------------------------------
    # Prepare chart data (reuse existing functions)
    # ----------------------------------------------------------
    print("    Preparing chart data...")
    (transport_mineral_data, energy_mineral_data,
     transport_country_data, transport_cost_data, energy_cost_data,
     top_transport_countries, country_colormap) = prepare_infrastructure_data(df)

    # ----------------------------------------------------------
    # Create figure with two gridspec regions
    # ----------------------------------------------------------
    fig = plt.figure(figsize=(18, 18))

    # Map section: top portion of figure (lowered top to leave room for Panel A title)
    # bottom lowered from 0.68 → 0.64 to give each cell a squarer shape,
    # reducing the within-cell padding that equal-aspect axes produce.
    map_gs = fig.add_gridspec(
        1, 4,
        width_ratios=[1, 1, 1, 0.35],
        left=0.01, right=0.99,
        top=0.94, bottom=0.64,
        wspace=0.005
    )

    # Chart section: bottom portion of figure (3 rows × 2 columns)
    # right expanded from 0.62 → 0.78 to use more available horizontal space.
    # top set to 0.60 to keep a clear gap below the map section bottom (0.64).
    # hspace reduced from 0.55 → 0.38 to recover the vertical space from lowering top.
    # wspace reduced from 0.55 → 0.45 to avoid a large absolute inter-column gap.
    chart_gs = fig.add_gridspec(
        3, 2,
        left=0.06, right=0.78,
        top=0.60, bottom=0.03,
        hspace=0.38, wspace=0.45
    )

    # ----------------------------------------------------------
    # Render Panel A: Flow maps
    # ----------------------------------------------------------
    if flow_data:
        print("    Rendering Panel A flow maps...")

        # Panel A label
        panel_a_title = fig.text(0.02, 0.98, 'A) Transport Flows by Location',
                                  fontsize=14, fontweight='bold', va='top', ha='left')

        map_title_fontsize = 12
        map_textfontsize = 10

        for idx, (fc, edges_df) in enumerate(flow_data):
            ax_map = fig.add_subplot(map_gs[0, idx])
            ax_map.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
            # adjustable='datalim' forces the axis to fill its cell fully;
            # the data limits expand slightly rather than the axis shrinking,
            # which eliminates the inter-map white space caused by equal aspect.
            ax_map.set_aspect('equal', adjustable='datalim')
            ax_map.set_xticks([])
            ax_map.set_yticks([])

            render_flow_panel(
                ax_map, edges_df,
                title=fc['title'],
                ccg_isos=ccg_isos,
                tonnage_weights=tonnage_weights,
                title_fontsize=map_title_fontsize
            )

        # Flow map key panel (no aspect='equal' - symbolic elements, not a map)
        ax_key = fig.add_subplot(map_gs[0, 3])
        ax_key.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        ax_key.set_xticks([])
        ax_key.set_yticks([])

        render_flow_key(
            ax_key, xl, yl, dxl, dyl,
            tonnage_weights=tonnage_weights,
            textfontsize=map_textfontsize
        )

    # ----------------------------------------------------------
    # Render Panels B-G: Charts (same as infrastructure v2)
    # ----------------------------------------------------------
    print("    Rendering chart panels B-G...")

    ax_transport_mineral = fig.add_subplot(chart_gs[0, 0])
    ax_energy_mineral = fig.add_subplot(chart_gs[0, 1])
    ax_transport_country = fig.add_subplot(chart_gs[1, 0])
    ax_energy_country = fig.add_subplot(chart_gs[1, 1])
    ax_transport_cost = fig.add_subplot(chart_gs[2, 0])
    ax_energy_cost = fig.add_subplot(chart_gs[2, 1])

    # Row 1: By Mineral
    plot_stacked_panel(
        ax_transport_mineral, transport_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='B) Transport Volume by Mineral',
        xlabel='Transport Volume (Million tonne-km)'
    )

    plot_stacked_panel(
        ax_energy_mineral, energy_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='C) Installed Electricity Capacity by Mineral',
        xlabel='Capacity (GW)'
    )

    # Row 2: By Country + Electricity capacity change
    country_order_transport = top_transport_countries + ['Other']
    country_colors_transport = {
        c: country_colormap.get(c, '#999999') for c in top_transport_countries}
    country_colors_transport['Other'] = '#999999'

    plot_stacked_panel(
        ax_transport_country, transport_country_data,
        stack_order=country_order_transport,
        colors=country_colors_transport,
        title='D) Transport Volume by Country',
        xlabel='Transport Volume (Million tonne-km)'
    )

    # Panel E: Electricity capacity change
    legend_capacity_change = None
    if electricity_data is not None:
        legend_capacity_change = plot_electricity_capacity_change_panel(
            ax_energy_country, electricity_data)
        ax_energy_country.add_artist(legend_capacity_change)
    else:
        ax_energy_country.text(
            0.5, 0.5, 'Electricity data not available',
            transform=ax_energy_country.transAxes,
            ha='center', va='center', fontsize=12)
        ax_energy_country.set_title(
            'E) Electricity Capacity Change by Country',
            fontsize=12, fontweight='bold', pad=10)

    # Row 3: Costs
    plot_stacked_panel(
        ax_transport_cost, transport_cost_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='F) Transport Costs',
        xlabel='Cost (Billion USD)'
    )

    plot_stacked_panel(
        ax_energy_cost, energy_cost_data,
        stack_order=ENERGY_COST_ORDER,
        colors=ENERGY_COST_COLORS,
        title='G) Energy Costs',
        xlabel='Cost (Billion USD)'
    )

    # Set y-axis labels for chart panels
    y_labels = [label for _, _, _, label in SCENARIO_CONFIG]
    for ax in [ax_transport_mineral, ax_energy_mineral,
               ax_transport_country, ax_transport_cost, ax_energy_cost]:
        ax.set_yticklabels(y_labels, fontsize=9)

    # ----------------------------------------------------------
    # Create legends (same as infrastructure v2)
    # ----------------------------------------------------------
    print("    Adding legends...")

    # Mineral legend
    mineral_patches = []
    for mineral in MINERAL_ORDER:
        color = reference_mineral_colormap.get(mineral, '#999999')
        label = mineral.capitalize()
        patch = mpatches.Patch(
            facecolor=color, label=label, edgecolor='black', linewidth=0.8)
        mineral_patches.append(patch)

    legend_minerals = ax_energy_mineral.legend(
        handles=mineral_patches,
        title='Minerals',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=10, title_fontsize=11,
        framealpha=0.98, edgecolor='black')

    # Country legend for Panel D
    transport_country_patches = []
    for country in (top_transport_countries + ['Other']):
        color = country_colors_transport[country]
        patch = mpatches.Patch(
            facecolor=color, label=country, edgecolor='black', linewidth=0.8)
        transport_country_patches.append(patch)

    legend_transport_countries = ax_transport_country.legend(
        handles=transport_country_patches,
        title='Countries (Transport)',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=9, title_fontsize=10,
        framealpha=0.98, edgecolor='black', ncol=1)
    ax_transport_country.add_artist(legend_transport_countries)

    # Energy cost type legend
    energy_cost_patches = []
    for cost_type in ENERGY_COST_ORDER:
        color = ENERGY_COST_COLORS[cost_type]
        patch = mpatches.Patch(
            facecolor=color, label=cost_type, edgecolor='black', linewidth=0.8)
        energy_cost_patches.append(patch)

    legend_energy = ax_energy_cost.legend(
        handles=energy_cost_patches,
        title='Energy Cost\nComponents',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=10, title_fontsize=11,
        framealpha=0.98, edgecolor='black')

    # Constraint & Uncertainty legend
    constraint_patches = [
        mpatches.Patch(facecolor='white', hatch='////', edgecolor='black',
                       label='Constrained'),
        mpatches.Patch(facecolor='white', edgecolor='black',
                       label='Unconstrained')
    ]
    error_patch = mpatches.Patch(
        facecolor='none', edgecolor='none',
        label='Error bars: Low-High demand')

    legend_constraint = ax_energy_mineral.legend(
        handles=constraint_patches + [error_patch],
        title='Constraint &\nUncertainty',
        bbox_to_anchor=(1.02, 0.40),
        loc='upper left',
        fontsize=10, title_fontsize=11,
        framealpha=0.98, edgecolor='black')

    # Mineral legend for Panel F (Transport Costs)
    mineral_patches_f = []
    for mineral in MINERAL_ORDER:
        color = reference_mineral_colormap.get(mineral, '#999999')
        label = mineral.capitalize()
        patch = mpatches.Patch(
            facecolor=color, label=label, edgecolor='black', linewidth=0.8)
        mineral_patches_f.append(patch)

    legend_minerals_f = ax_transport_cost.legend(
        handles=mineral_patches_f,
        title='Minerals',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=10, title_fontsize=11,
        framealpha=0.98, edgecolor='black')

    # Keep legends
    ax_energy_mineral.add_artist(legend_minerals)
    ax_energy_mineral.add_artist(legend_constraint)
    ax_transport_cost.add_artist(legend_minerals_f)
    ax_energy_cost.add_artist(legend_energy)

    # Ensure consistent x-axis for cost panels
    max_cost_xlim = max(
        ax_transport_cost.get_xlim()[1], ax_energy_cost.get_xlim()[1])
    ax_transport_cost.set_xlim(0, max_cost_xlim)
    ax_energy_cost.set_xlim(0, max_cost_xlim)

    # ----------------------------------------------------------
    # Save figure
    # ----------------------------------------------------------
    all_artists = [
        legend_minerals, legend_constraint,
        legend_transport_countries, legend_capacity_change,
        legend_minerals_f, legend_energy
    ]
    if flow_data:
        all_artists.append(panel_a_title)
    all_artists = [a for a in all_artists if a is not None]

    saved_paths = []

    png_path = os.path.join(output_dir, 'infrastructure_indicators_v3.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight',
                bbox_extra_artists=all_artists, facecolor='white')
    saved_paths.append(png_path)
    print(f"    Saved: {os.path.basename(png_path)}")

    pdf_path = os.path.join(output_dir, 'infrastructure_indicators_v3.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight',
                bbox_extra_artists=all_artists, facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    Saved: {os.path.basename(pdf_path)}")

    preview_path = os.path.join(
        output_dir, 'infrastructure_indicators_v3_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight',
                bbox_extra_artists=all_artists, facecolor='white')
    saved_paths.append(preview_path)
    print(f"    Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


def generate_infrastructure_indicators_v3_figures(df, output_dir, config):
    """
    Main entry point for generating infrastructure indicators V3 figures.

    Args:
        df: Main data DataFrame
        output_dir: Output directory
        config: Configuration dictionary with paths

    Returns:
        List of saved file paths
    """
    return create_infrastructure_indicators_v3_figure(df, output_dir, config)


if __name__ == '__main__':
    """Test the figure generation"""

    # Load config
    config_path = os.path.join(_this_dir, '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load data
    data_file = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"Loading data from: {data_file}")
    df = pd.read_excel(data_file, index_col=[0, 1, 2, 3, 4]).reset_index()

    # Create output directory
    output_dir = os.path.join(
        config['paths']['figures'], 'automated_plots', 'publication',
        'infrastructure_indicators_v3')
    os.makedirs(output_dir, exist_ok=True)

    # Generate figure
    print("Testing infrastructure indicators V3 figure generation...")
    paths = generate_infrastructure_indicators_v3_figures(df, output_dir, config)
    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
