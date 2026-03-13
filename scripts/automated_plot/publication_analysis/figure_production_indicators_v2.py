"""
Production Indicators Figure V2

Adds Panel A (mine metal content maps) on top of the existing Panels B-F.

HYBRID DATA SOURCES (matches export flows version):
- Extraction panels (B, E): all_data.xlsx - TOTAL production (domestic + export)
- Processing panels (C, D, F): tonnage_flows_with_revenues.xlsx - EXPORT production only

Layout:
- Row 0: Panel A - Three mine location maps + key
    (2022 Baseline | 2040 No Env Constraints | 2040 Env Constraints with filters)
- Row 1: Panel B - Total extraction by mineral (vertical grouped bars)
- Row 2: Panel C - Total processed exports by mineral (horizontal stacked bars)
- Row 3: Panel D - Total processed exports by type (horizontal stacked bars)
- Row 4: Panels E & F - Extraction and Processed exports by country

Output: production_indicators_v2_*.png/pdf
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
    load_config as map_load_config
)

# Import from scripts/automated_plot/
from publication_analysis.config import (
    DPI_PUBLICATION, DPI_SCREEN, PUBLICATION_STYLE
)
from plot_config import reference_mineral_colormap
from plot_utils import PROCESSING_TYPE_COLORS, generate_country_colormap

# Import from export flows version (uses tonnage_flows for processing panels)
from publication_analysis.figure_production_indicators_export_flows import (
    prepare_extraction_data,
    prepare_processing_data,
    prepare_country_extraction_data,
    prepare_country_processing_data,
    plot_grouped_vertical_bars_by_mineral,
    plot_stacked_panel,
    create_comprehensive_legend,
    calculate_max_value_from_data,
    SCENARIO_CONFIG_EXTRACTION,
    SCENARIO_CONFIG_PROCESSING,
    MINERAL_ORDER,
    PROCESSING_ORDER
)

# ============================================================
# Mine map configuration
# ============================================================
REFERENCE_MINERALS = ["cobalt", "copper", "graphite", "lithium", "manganese", "nickel"]
REFERENCE_MINERAL_COLORS = ["#3288bd", "#fee08b", "#66c2a5", "#c2a5cf", "#fdae61", "#f46d43"]

MINE_MAP_CONFIGS = [
    {
        "scenario": "country_unconstrained",
        "scenario_name": "country",
        "year": 2022,
        "layer": "2022_baseline",
        "title": "2022 - Baseline",
        "show_filters": False
    },
    {
        "scenario": "country_unconstrained",
        "scenario_name": "country",
        "year": 2040,
        "layer": "bau_2040_mid_min_threshold_metal_tons",
        "title": "2040 - No Environmental Constraints",
        "show_filters": False
    },
    {
        "scenario": "country_constrained",
        "scenario_name": "country",
        "year": 2040,
        "layer": "bau_2040_mid_min_threshold_metal_tons",
        "title": "2040 - Environmental Constraints",
        "show_filters": True
    }
]


# ============================================================
# Mine map helper functions
# ============================================================

def load_mine_panel_data(config, map_config):
    """
    Load and process mine location data for a single map panel.

    Args:
        config: Configuration dictionary with paths
        map_config: Dict with scenario, layer, etc.

    Returns:
        GeoDataFrame with total_tons, env_filter, water_filter, total_filter,
        reference_mineral, color, geometry columns
    """
    output_path = config['paths']['results']
    fname = f"combined_node_locations_for_energy_conversion_{map_config['scenario']}.gpkg"
    sc_nm = map_config['scenario_name']

    mine_sites_df = gpd.read_file(
        os.path.join(output_path, "optimised_processing_locations", fname),
        layer=map_config['layer']
    )

    dfs = []
    for rf, rc in zip(REFERENCE_MINERALS, REFERENCE_MINERAL_COLORS):
        cols = [f"{rf}_initial_stage_production_tons_0.0_in_{sc_nm}"]
        mine_sites_df["total_tons"] = mine_sites_df[cols].sum(axis=1)
        df = mine_sites_df[mine_sites_df["total_tons"] > 0].copy()

        df["env_filter"] = np.where(
            ((df["distance_to_keybiodiversityareas_km"] == 0) |
             (df["distance_to_lastofwild_km"] == 0) |
             (df["distance_to_protectedareas_km"] == 0)), 1, 0
        )
        df["water_filter"] = np.where(
            df["distance_to_waterstress_km"] == 0, 1, 0
        )
        df["total_filter"] = np.where(
            (df["env_filter"] == 1) & (df["water_filter"] == 0), 1, 0
        )

        df = df[["total_tons", "env_filter", "water_filter", "total_filter", "geometry"]]
        df["reference_mineral"] = rf
        df["color"] = rc
        dfs.append(df)

    return pd.concat(dfs, axis=0, ignore_index=True)


def render_mine_panel(ax, df, title, ccg_isos, xl, yl, dxl, dyl,
                      show_filters=False, marker_size_max=600, tmax=2e6,
                      textfontsize=8, textfontsize_heading=9,
                      title_fontsize=11):
    """
    Render a single mine location map panel on the provided axis.

    Args:
        ax: Matplotlib axis
        df: GeoDataFrame from load_mine_panel_data
        title: Panel title string
        ccg_isos: List of CCG country ISO codes
        xl, yl: Map x/y limits
        dxl, dyl: Map x/y extents
        show_filters: Whether to show environmental filter hatching
        marker_size_max: Maximum marker size
        tmax: Maximum tonnage for scaling
        textfontsize: Font size for annotation text
        textfontsize_heading: Font size for heading text
        title_fontsize: Font size for panel title
    """
    ax = plot_ccg_basemap(
        ax,
        include_continents=["Africa"],
        include_countries=ccg_isos,
        include_labels=True
    )
    ax.set_title(title, fontsize=title_fontsize, fontweight="bold")

    df = df.copy()
    df["markersize"] = marker_size_max * (df["total_tons"] / tmax) ** 0.5
    df = df.sort_values(by="total_tons", ascending=False)

    # Production text annotations
    ax.text(xl[0] + 0.57 * dxl, yl[0] + 0.35 * dyl,
            'Annual Production (Mt)',
            fontsize=textfontsize_heading, weight='bold', ha='left')
    ax.text(xl[0] + 0.58 * dxl, yl[0] + 0.32 * dyl,
            'Total = {:.1f}'.format(df["total_tons"].sum() / 1e6),
            fontsize=textfontsize, weight='bold', ha='left')

    if show_filters:
        # Plot filtered mines with hatching - matches env_layers_with_mines.py
        # which passes full df color/markersize arrays for visual consistency
        total_filter_df = df[df["total_filter"] == 1]
        total_filter_df.geometry.plot(
            ax=ax,
            color=df["color"],
            edgecolor='none',
            markersize=df["markersize"],
            linewidth=0.5,
            hatch="xxxxxx",
            alpha=0.7)
        ax.text(xl[0] + 0.58 * dxl, yl[0] + 0.29 * dyl,
                'Protected and water stress areas = {:.1f}'.format(
                    total_filter_df["total_tons"].sum() / 1e6),
                fontsize=textfontsize, weight='bold', ha='left')

        env_filter_df = df[(df["total_filter"] != 1) & (df["env_filter"] == 1)]
        env_filter_df.geometry.plot(
            ax=ax,
            color=df["color"],
            edgecolor='none',
            markersize=df["markersize"],
            linewidth=0.5,
            hatch="||||||",
            alpha=0.7)
        ax.text(xl[0] + 0.58 * dxl, yl[0] + 0.26 * dyl,
                'Protected areas only = {:.1f}'.format(
                    env_filter_df["total_tons"].sum() / 1e6),
                fontsize=textfontsize, weight='bold', ha='left')

        water_filter_df = df[(df["total_filter"] != 1) & (df["water_filter"] == 1)]
        water_filter_df.geometry.plot(
            ax=ax,
            color=df["color"],
            edgecolor='none',
            markersize=df["markersize"],
            linewidth=0.5,
            hatch="++++++",
            alpha=0.7)
        ax.text(xl[0] + 0.58 * dxl, yl[0] + 0.23 * dyl,
                'Water stress areas only = {:.1f}'.format(
                    water_filter_df["total_tons"].sum() / 1e6),
                fontsize=textfontsize, weight='bold', ha='left')

        # Remove filtered points from main df
        df = df[(df["env_filter"] == 0) & (df["water_filter"] == 0)]

    # Plot remaining (or all) mines without hatching
    df.geometry.plot(
        ax=ax, color=df["color"], edgecolor='none',
        markersize=df["markersize"], alpha=0.7)


def render_mine_key(ax, xl, yl, dxl, dyl, tmax=2e6, marker_size_max=600,
                    any_filters=True, textfontsize=8, textfontsize_legend=8):
    """
    Render the legend/key for mine map panels.

    Args:
        ax: Matplotlib axis for the key panel
        xl, yl: Map x/y limits
        dxl, dyl: Map x/y extents
        tmax: Maximum tonnage for scale
        marker_size_max: Maximum marker size
        any_filters: Whether to include filter type legend
        textfontsize: Font size for text
        textfontsize_legend: Font size for legend items
    """
    ax.set_ylim(yl)
    ax.set_xlim(xl[0] + 0.58 * dxl, xl[1] + 0.10 * dxl)

    xk = xl[0] + 0.63 * dxl
    xt = xk - 0.04 * dxl

    keys = ['tonnage', 'filter_type', 'mineral'] if any_filters else ['tonnage', 'mineral']

    for ky in range(len(keys)):
        key = keys[ky]
        if key == 'tonnage':
            tonnage_key = 10 ** np.arange(1, np.ceil(np.log10(tmax)), 1)
            tonnage_key = tonnage_key[::-1]
            Nk = tonnage_key.size
            yk = yl[0] + np.linspace(0.15 * dyl, 0.45 * dyl, Nk) + 0.4 * ky * dyl
            yt = yk[-1] + np.diff(yk[-3:-1])
            size_key = marker_size_max * (tonnage_key / tmax) ** 0.5
            key_gdf = gpd.GeoDataFrame(
                geometry=gpd.points_from_xy(np.ones(Nk) * xk, yk))
            key_gdf.geometry.plot(ax=ax, markersize=size_key, color='k')
            ax.text(xt, yt, 'Mine annual output\n(tonnes)',
                    weight='bold', va='center', fontsize=textfontsize)
            for k in range(Nk):
                ax.text(xk, yk[k], '     {:,.0f}'.format(tonnage_key[k]),
                        fontsize=textfontsize_legend, va='center')

        elif key == 'filter_type':
            ftyp = ["Protected areas only",
                     "Water stress areas only",
                     "Protected and water stress"]
            htyp = ["||||||", "++++++", "xxxxxx"]
            Nk = len(ftyp)
            yk = yl[0] + np.linspace(0.15 * dyl, 0.25 * dyl, Nk) + 0.4 * ky * dyl
            yt = yk[-1] + np.diff(yk[-3:-1])
            ax.text(xt, yt, 'Mine and area overlaps',
                    weight='bold', va='center', fontsize=textfontsize)
            for k in range(Nk):
                ax.text(xk, yk[k], '   ' + ftyp[k],
                        fontsize=textfontsize_legend, va='center')
                ax.scatter(xk, yk[k], marker='s', facecolor='none',
                           edgecolor='k', hatch=htyp[k], s=100)

        else:  # mineral
            Nk = len(REFERENCE_MINERALS)
            yk = yl[0] + np.linspace(0.15 * dyl, 0.3 * dyl, Nk) + 0.3 * ky * dyl
            yt = yk[-1] + np.diff(yk[-3:-1])
            ax.text(xt, yt, 'Mineral produced',
                    weight='bold', va='center', fontsize=textfontsize)
            for k in range(Nk):
                ax.text(xk, yk[k], '   ' + REFERENCE_MINERALS[k].capitalize(),
                        fontsize=textfontsize_legend, va='center')
                ax.plot(xk, yk[k], 's',
                        mfc=REFERENCE_MINERAL_COLORS[k],
                        mec=REFERENCE_MINERAL_COLORS[k], ms=10)


# ============================================================
# Main figure creation
# ============================================================

def create_production_indicators_v2_figure(df_all, df_flows, output_dir, config):
    """
    Generate production indicators V2 figure with Panel A maps + Panels B-F charts.

    HYBRID approach:
    - Extraction panels (B, E): use df_all (all_data.xlsx) for total production
    - Processing panels (C, D, F): use df_flows (export flows only) for export production

    Args:
        df_all: all_data.xlsx DataFrame (for extraction panels)
        df_flows: tonnage_flows DataFrame (export flows only, for processing panels)
        output_dir: Output directory for figures
        config: Configuration dictionary with paths

    Returns:
        List of saved file paths
    """
    print("  Generating production indicators V2 figure (with mine maps)...")

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Set hatch linewidth AFTER style reset (default resets it to 1.0)
    matplotlib.rcParams['hatch.linewidth'] = 0.3

    # ----------------------------------------------------------
    # Load mine map data
    # ----------------------------------------------------------
    processed_data_path = config['paths']['data']
    ccg_countries = pd.read_csv(
        os.path.join(processed_data_path, "admin_boundaries", "ccg_country_codes.csv"))
    ccg_isos = ccg_countries[
        ccg_countries["ccg_country"] == 1]["iso_3digit_alpha"].values.tolist()

    _, _, xl, yl = map_background_and_bounds(include_countries=ccg_isos)
    dxl = abs(np.diff(xl))[0]
    dyl = abs(np.diff(yl))[0]

    print("    Loading mine location data...")
    mine_data = []
    for mc in MINE_MAP_CONFIGS:
        print(f"      Loading: {mc['title']}")
        panel_df = load_mine_panel_data(config, mc)
        mine_data.append((mc, panel_df))

    # ----------------------------------------------------------
    # Prepare chart data (reuse existing functions)
    # ----------------------------------------------------------
    print("    Preparing chart data...")
    # Extraction panels use all_data.xlsx (total production)
    panel_metal_data = prepare_extraction_data(df_all)
    country_extraction_data, top_extraction_countries = prepare_country_extraction_data(df_all)

    # Processing panels use export flows (export production only)
    panel_processing_data, panel_mineral_data = prepare_processing_data(df_flows, df_all)
    country_processing_data, top_processing_countries = prepare_country_processing_data(df_flows)

    # Country color mapping
    all_countries = sorted(
        set(top_extraction_countries) | set(top_processing_countries) | {'Other'})
    country_colormap = generate_country_colormap(all_countries)
    country_colormap['Other'] = '#999999'

    # Calculate unified x-axis maximum for all horizontal panels (C, D, E, F)
    max_c = calculate_max_value_from_data(panel_mineral_data, SCENARIO_CONFIG_PROCESSING)
    max_d = calculate_max_value_from_data(panel_processing_data, SCENARIO_CONFIG_PROCESSING)
    max_e = calculate_max_value_from_data(country_extraction_data, SCENARIO_CONFIG_EXTRACTION)
    max_f = calculate_max_value_from_data(country_processing_data, SCENARIO_CONFIG_PROCESSING)
    unified_xlim_max = max(max_c, max_d, max_e, max_f) * 1.10  # 10% buffer

    # ----------------------------------------------------------
    # Create figure with two gridspec regions
    # ----------------------------------------------------------
    fig = plt.figure(figsize=(18, 22))

    # Map section: top portion of figure (lowered top to leave room for Panel A title)
    map_gs = fig.add_gridspec(
        1, 4,
        width_ratios=[1, 1, 1, 0.6],
        left=0.02, right=0.98,
        top=0.94, bottom=0.70,
        wspace=0.005
    )

    # Chart section: bottom portion of figure
    # right expanded from 0.54 → 0.78 to use more available horizontal space.
    # wspace reduced from 0.53 → 0.40 to avoid a large absolute inter-column gap.
    # hspace reduced from 0.40 → 0.33 to tighten vertical spacing between rows.
    chart_gs = fig.add_gridspec(
        4, 2,
        height_ratios=[0.5, 0.85, 0.85, 0.7],
        left=0.08, right=0.78,
        top=0.67, bottom=0.02,
        hspace=0.33, wspace=0.40
    )

    # ----------------------------------------------------------
    # Render Panel A: Mine maps
    # ----------------------------------------------------------
    print("    Rendering Panel A maps...")

    # Panel A label
    panel_a_title = fig.text(0.02, 0.98, 'A) Total Extraction by Location',
                              fontsize=14, fontweight='bold', va='top', ha='left')

    map_textfontsize = 8
    map_heading_fontsize = 9
    map_title_fontsize = 12
    marker_size_max = 600
    tmax = 2e6

    any_filters = any(mc['show_filters'] for mc in MINE_MAP_CONFIGS)

    for idx, (mc, panel_df) in enumerate(mine_data):
        ax_map = fig.add_subplot(map_gs[0, idx])
        ax_map.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        ax_map.set_aspect('equal')
        ax_map.set_xticks([])
        ax_map.set_yticks([])

        render_mine_panel(
            ax_map, panel_df,
            title=mc['title'],
            ccg_isos=ccg_isos,
            xl=xl, yl=yl, dxl=dxl, dyl=dyl,
            show_filters=mc['show_filters'],
            marker_size_max=marker_size_max,
            tmax=tmax,
            textfontsize=map_textfontsize,
            textfontsize_heading=map_heading_fontsize,
            title_fontsize=map_title_fontsize
        )

    # Map key panel (no aspect='equal' - symbolic elements, not a map)
    ax_key = fig.add_subplot(map_gs[0, 3])
    ax_key.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
    ax_key.set_xticks([])
    ax_key.set_yticks([])

    render_mine_key(
        ax_key, xl, yl, dxl, dyl,
        tmax=tmax,
        marker_size_max=marker_size_max,
        any_filters=any_filters,
        textfontsize=map_textfontsize,
        textfontsize_legend=map_textfontsize
    )

    # ----------------------------------------------------------
    # Render Panels B-F: Charts (same as original)
    # ----------------------------------------------------------
    print("    Rendering chart panels B-F...")

    # Panel B spans both columns in row 0
    ax_metal = fig.add_subplot(chart_gs[0, :])

    # Panel C spans both columns in row 1
    ax_mineral = fig.add_subplot(chart_gs[1, :])

    # Panel D spans both columns in row 2
    ax_processing = fig.add_subplot(chart_gs[2, :])

    # Panel E & F in row 3
    ax_country_extraction = fig.add_subplot(chart_gs[3, 0])
    ax_country_processing = fig.add_subplot(chart_gs[3, 1])

    # Panel B: Metal Content - Vertical grouped bars by mineral
    plot_grouped_vertical_bars_by_mineral(
        ax_metal, panel_metal_data,
        title='B) Total Extraction by Mineral',
        ylabel='Metal Content (Mt)'
    )

    # Panel C: Processed Exports by Mineral - 7 bars
    plot_stacked_panel(
        ax_mineral, panel_mineral_data,
        stack_order=MINERAL_ORDER,
        colors=reference_mineral_colormap,
        title='C) Total Processed Exports by Mineral',
        xlabel='Production (Mt)',
        scenario_config=SCENARIO_CONFIG_PROCESSING,
        xlim_max=unified_xlim_max
    )

    # Panel D: Processed Exports by Type - 7 bars
    plot_stacked_panel(
        ax_processing, panel_processing_data,
        stack_order=PROCESSING_ORDER,
        colors=PROCESSING_TYPE_COLORS,
        title='D) Total Processed Exports by Processing Type',
        xlabel='Production (Mt)',
        scenario_config=SCENARIO_CONFIG_PROCESSING,
        xlim_max=unified_xlim_max
    )

    # Panel E: Extraction by Country - 3 scenarios
    country_order_extraction = top_extraction_countries + ['Other']
    country_colors_extraction = {
        c: country_colormap.get(c, '#999999') for c in country_order_extraction}

    plot_stacked_panel(
        ax_country_extraction, country_extraction_data,
        stack_order=country_order_extraction,
        colors=country_colors_extraction,
        title='E) Extraction by Country',
        xlabel='Metal Content (Mt)',
        scenario_config=SCENARIO_CONFIG_EXTRACTION,
        xlim_max=unified_xlim_max
    )

    # Panel F: Processed Exports by Country - 7 scenarios
    country_order_processing = top_processing_countries + ['Other']
    country_colors_processing = {
        c: country_colormap.get(c, '#999999') for c in country_order_processing}

    plot_stacked_panel(
        ax_country_processing, country_processing_data,
        stack_order=country_order_processing,
        colors=country_colors_processing,
        title='F) Processed Exports by Country',
        xlabel='Production (Mt)',
        scenario_config=SCENARIO_CONFIG_PROCESSING,
        xlim_max=unified_xlim_max
    )

    # Set y-axis labels
    y_labels_extraction = [label for _, _, _, label in SCENARIO_CONFIG_EXTRACTION]
    y_labels_processing = [label for _, _, _, label in SCENARIO_CONFIG_PROCESSING]

    ax_country_extraction.set_yticklabels(y_labels_extraction, fontsize=9)
    ax_country_processing.set_yticklabels(y_labels_processing, fontsize=9)
    ax_mineral.set_yticklabels(y_labels_processing, fontsize=9)
    ax_processing.set_yticklabels(y_labels_processing, fontsize=9)

    # ----------------------------------------------------------
    # Create legends
    # ----------------------------------------------------------
    print("    Adding legends...")
    all_legends = create_comprehensive_legend(
        fig, ax_metal, ax_country_extraction, ax_country_processing,
        ax_mineral, ax_processing, country_colormap,
        top_extraction_countries, top_processing_countries
    )

    # ----------------------------------------------------------
    # Save figure
    # ----------------------------------------------------------
    all_extra = list(all_legends) + [panel_a_title]
    saved_paths = []

    png_path = os.path.join(output_dir, 'production_indicators_v2.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight',
                bbox_extra_artists=all_extra, facecolor='white')
    saved_paths.append(png_path)
    print(f"    Saved: {os.path.basename(png_path)}")

    pdf_path = os.path.join(output_dir, 'production_indicators_v2.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight',
                bbox_extra_artists=all_extra, facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    Saved: {os.path.basename(pdf_path)}")

    preview_path = os.path.join(output_dir, 'production_indicators_v2_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight',
                bbox_extra_artists=all_extra, facecolor='white')
    saved_paths.append(preview_path)
    print(f"    Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


def generate_production_indicators_v2_figures(df_all, df_flows, output_dir, config):
    """
    Main entry point for generating production indicators V2 figures.

    Args:
        df_all: all_data.xlsx DataFrame (for extraction panels)
        df_flows: tonnage_flows DataFrame (export flows only, for processing panels)
        output_dir: Output directory
        config: Configuration dictionary with paths

    Returns:
        List of saved file paths
    """
    return create_production_indicators_v2_figure(df_all, df_flows, output_dir, config)


if __name__ == '__main__':
    """Test the figure generation"""

    # Load config
    config_path = os.path.join(_this_dir, '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load all_data.xlsx for extraction panels
    all_data_file = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"Loading all_data.xlsx from: {all_data_file}")
    df_all = pd.read_excel(all_data_file, index_col=[0, 1, 2, 3, 4]).reset_index()
    print(f"  Loaded: {len(df_all):,} rows")

    # Load tonnage flows for processing panels (export flows only)
    flows_file = os.path.join(config['paths']['results'], 'tonnage_flows_with_revenues.xlsx')
    print(f"Loading tonnage flows from: {flows_file}")
    df_flows = pd.read_excel(flows_file, sheet_name='All_Flows')
    print(f"  Loaded: {len(df_flows):,} rows")

    # Filter for export flows only
    df_flows = df_flows[df_flows['trade_type'] == 'Export'].copy()
    print(f"  Export flows: {len(df_flows):,} rows")

    # Create output directory
    output_dir = os.path.join(
        config['paths']['figures'], 'automated_plots', 'publication',
        'production_indicators_v2')
    os.makedirs(output_dir, exist_ok=True)

    # Generate figure
    print("\nTesting production indicators V2 figure generation...")
    paths = generate_production_indicators_v2_figures(df_all, df_flows, output_dir, config)
    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
