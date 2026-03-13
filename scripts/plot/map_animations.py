#!/usr/bin/env python
# coding: utf-8
"""
Map Animations Generator

Creates animated GIFs showing transitions between different time periods and scenarios
for mineral production maps. Supports crossfade transitions and clear scenario labeling.

This script is separate from the main mapping scripts to avoid modifying existing functionality.

Usage:
    python map_animations.py [--animation-type TYPE] [--output-dir DIR]

Animation Types:
    - metal_content: Mine metal content maps (stage 0 production)
    - processing_locations: Processing facility locations
    - flow_maps: Transport network flow intensity (TODO)

Examples:
    # Generate all metal content animations
    python map_animations.py --animation-type metal_content

    # Generate specific animation with custom output
    python map_animations.py --animation-type metal_content --output-dir ./custom_output
"""

import os
import sys
import argparse
import tempfile
import shutil
from collections import OrderedDict
from io import BytesIO

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# Import utilities from the same directory
from map_plotting_utils import load_config, map_background_and_bounds, plot_ccg_basemap, generate_weight_bins

# Configuration
config = load_config()
processed_data_path = config['paths']['data']
output_path = config['paths']['results']
figure_path = config['paths']['figures']

# Mineral definitions (consistent with publication scripts - plot_config.py Jan 2025)
# OPTIMAL COLOR REASSIGNMENT - solves copper-cobalt and cobalt-nickel overlap issues
REFERENCE_MINERALS = ["cobalt", "copper", "graphite", "lithium", "manganese", "nickel"]
REFERENCE_MINERAL_COLORS = ["#3288bd", "#fee08b", "#66c2a5", "#c2a5cf", "#fdae61", "#f46d43"]
# Cobalt: blue, Copper: yellow, Graphite: teal, Lithium: purple, Manganese: orange, Nickel: orange-red


class AnimationFrame:
    """Represents a single frame in an animation with metadata."""

    def __init__(self, year, scenario, constraint, title, data=None,
                 title_highlight=None, subtitle=None):
        """
        Initialize an animation frame.

        Args:
            year: The year (e.g., 2022, 2040)
            scenario: Scenario type ('baseline', 'bau', 'early_refining', 'precursor')
            constraint: Constraint type ('unconstrained', 'constrained')
            title: Display title for the frame (or prefix if highlight is used)
            data: Optional GeoDataFrame with the frame data
            title_highlight: Text to highlight in a distinctive color (appears after title)
            subtitle: Second line of title (optional)
        """
        self.year = year
        self.scenario = scenario
        self.constraint = constraint
        self.title = title
        self.title_highlight = title_highlight
        self.subtitle = subtitle
        self.data = data
        self.image = None  # Will hold the rendered PIL Image


class MapAnimationGenerator:
    """
    Generates animated GIF maps showing transitions between scenarios.

    Supports:
    - Metal content maps (mine output)
    - Processing location maps
    - Flow maps (transport network intensity)
    """

    def __init__(self, output_dir=None):
        """
        Initialize the animation generator.

        Args:
            output_dir: Output directory for animations. Defaults to figures/regional_figures/animations
        """
        if output_dir is None:
            self.output_dir = os.path.join(figure_path, "regional_figures", "animations")
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Load CCG country codes for basemap
        ccg_countries = pd.read_csv(
            os.path.join(processed_data_path, "admin_boundaries", "ccg_country_codes.csv")
        )
        self.ccg_isos = ccg_countries[
            ccg_countries["ccg_country"] == 1
        ]["iso_3digit_alpha"].values.tolist()

        # Get map bounds
        _, _, self.xl, self.yl = map_background_and_bounds(include_countries=self.ccg_isos)
        self.dxl = abs(np.diff(self.xl))[0]
        self.dyl = abs(np.diff(self.yl))[0]

        # Default settings
        self.marker_size_max = 600
        self.figwidth = 10
        self.dpi = 150
        self.frame_duration_ms = 3500  # How long each main frame is shown (longer for clarity)
        self.transition_frames = 10     # Number of frames for crossfade
        self.transition_duration_ms = 100  # Duration per transition frame

    def load_metal_content_data(self, scenario, layer):
        """
        Load metal content data from GPKG file.

        Uses the 'combined_' prefixed GPKG files to match the existing static maps.

        Args:
            scenario: Scenario name (e.g., 'country_unconstrained')
            layer: Layer name (e.g., '2022_baseline', 'bau_2040_mid_min_threshold_metal_tons')

        Returns:
            GeoDataFrame with total_tons and geometry columns for each mineral
        """
        # Determine the file naming pattern
        if "region" in scenario:
            sc_nm = "region"
        else:
            sc_nm = "country"

        # Use combined file to match existing static maps
        fname = f"combined_node_locations_for_energy_conversion_{scenario}.gpkg"
        fpath = os.path.join(output_path, "optimised_processing_locations", fname)

        if not os.path.exists(fpath):
            raise FileNotFoundError(f"GPKG file not found: {fpath}")

        mine_sites_df = gpd.read_file(fpath, layer=layer)

        # Extract metal content (stage 0 production) for each mineral
        dfs = []
        for rf, rc in zip(REFERENCE_MINERALS, REFERENCE_MINERAL_COLORS):
            col = f"{rf}_initial_stage_production_tons_0.0_in_{sc_nm}"
            if col in mine_sites_df.columns:
                mine_sites_df["total_tons"] = mine_sites_df[col]
                df = mine_sites_df[mine_sites_df["total_tons"] > 0].copy()
                df = df[["total_tons", "geometry"]]
                df["reference_mineral"] = rf
                df["color"] = rc
                dfs.append(df)

        if not dfs:
            return gpd.GeoDataFrame()

        result = pd.concat(dfs, axis=0, ignore_index=True)
        return gpd.GeoDataFrame(result, geometry="geometry")

    def render_multicolor_title(self, fig, frame, highlight_color='#d62728'):
        """
        Render a title with highlighted text in a distinctive color.

        Args:
            fig: Matplotlib figure
            frame: AnimationFrame with title, title_highlight, and subtitle
            highlight_color: Color for highlighted text (default: red)
        """
        y_pos = 0.97
        fontsize = 16

        if frame.title_highlight:
            # Two-part title: prefix + highlighted text
            # Calculate approximate positions for centering
            fig.text(0.42, y_pos, frame.title, fontsize=fontsize, fontweight='bold',
                    ha='right', va='top', color='black')
            fig.text(0.43, y_pos, frame.title_highlight, fontsize=fontsize, fontweight='bold',
                    ha='left', va='top', color=highlight_color)
        else:
            # Simple single title
            fig.text(0.5, y_pos, frame.title, fontsize=fontsize, fontweight='bold',
                    ha='center', va='top', color='black')

        # Add subtitle if present
        if frame.subtitle:
            fig.text(0.5, y_pos - 0.04, frame.subtitle, fontsize=14, fontweight='normal',
                    ha='center', va='top', color='black')

    def render_frame_to_image(self, frame, tmax, show_legend=True, total_override=None):
        """
        Render a single animation frame to a PIL Image.

        Uses a side-panel layout (like the working static maps in location_maps.py)
        to ensure the legend is always fully visible and doesn't cover map data.

        Args:
            frame: AnimationFrame object with data loaded
            tmax: Maximum tonnage value for consistent marker sizing
            show_legend: Whether to show the legend panel
            total_override: Optional custom total value to display (in million tonnes)

        Returns:
            PIL Image of the rendered frame
        """
        import matplotlib.gridspec as gridspec

        # Use side-panel layout: map on left (wider), legend on right
        # Reduced height for tighter layout
        figwidth = 14
        figheight = 8

        fig = plt.figure(figsize=(figwidth, figheight), facecolor='white')

        # Add main title with optional highlighting
        self.render_multicolor_title(fig, frame)

        if show_legend:
            # GridSpec: map takes ~80% width, legend panel takes ~20%
            gs = gridspec.GridSpec(1, 2, width_ratios=[4, 1], wspace=0.02,
                                   left=0.01, right=0.99, top=0.92, bottom=0.01)

            # Map panel (left - wider)
            ax_map = fig.add_subplot(gs[0, 0])

            # Legend panel (right - narrower)
            ax_legend = fig.add_subplot(gs[0, 1])
        else:
            # No legend - map takes full width
            ax_map = fig.add_subplot(111)
            fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.01)
            ax_legend = None

        # Configure map axis
        ax_map.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        ax_map.set_aspect('equal')
        ax_map.set_xticks([])
        ax_map.set_yticks([])

        # Plot basemap with tighter bounds (reduced ocean space)
        ax_map = plot_ccg_basemap(
            ax_map,
            include_continents=["Africa"],
            include_countries=self.ccg_isos,
            include_labels=True,
            xmin_offset=-0.5,
            xmax_offset=2.0,      # Reduced from 3.5
            ymin_offset=2.0,      # Reduced from 6.5 - less ocean at bottom
            ymax_offset=0.5
        )

        # Plot mineral data if available
        df = frame.data
        total_mt = 0
        if df is not None and len(df) > 0:
            df["markersize"] = self.marker_size_max * (df["total_tons"] / tmax) ** 0.5
            df = df.sort_values(by="total_tons", ascending=False)
            df.geometry.plot(
                ax=ax_map,
                color=df["color"],
                edgecolor='none',
                markersize=df["markersize"],
                alpha=0.7
            )
            total_mt = df["total_tons"].sum() / 1e6

        # Use override total if provided, otherwise use calculated total
        display_total = total_override if total_override is not None else total_mt

        # Add total annotation at bottom of map - positioned relative to actual axis limits
        ax_xlim = ax_map.get_xlim()
        ax_ylim = ax_map.get_ylim()
        ax_map.text(
            (ax_xlim[0] + ax_xlim[1]) / 2,  # Center horizontally
            ax_ylim[0] + 0.02 * (ax_ylim[1] - ax_ylim[0]),  # Near bottom edge
            f'Total = {display_total:.1f} million tonnes',
            fontsize=16, weight='bold', ha='center', va='bottom'
        )

        # Draw legend in the side panel
        if show_legend and ax_legend is not None:
            # Configure legend axis - use normalized coordinates (0-1)
            ax_legend.set_xlim(0, 1)
            ax_legend.set_ylim(0, 1)
            ax_legend.set_xticks([])
            ax_legend.set_yticks([])
            ax_legend.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
            ax_legend.patch.set_facecolor('white')

            # Mineral color legend (top section of legend panel)
            legend_x = 0.1
            mineral_y_start = 0.86
            mineral_y_spacing = 0.07

            ax_legend.text(legend_x, 0.95, 'Mineral produced',
                          weight='bold', va='top', ha='left', fontsize=16)

            Nk_minerals = len(REFERENCE_MINERALS)
            for k in range(Nk_minerals):
                y_pos = mineral_y_start - k * mineral_y_spacing
                ax_legend.plot(legend_x, y_pos, 's',
                              mfc=REFERENCE_MINERAL_COLORS[k],
                              mec=REFERENCE_MINERAL_COLORS[k],
                              ms=16, clip_on=False)
                ax_legend.text(legend_x + 0.14, y_pos,
                              REFERENCE_MINERALS[k].capitalize(),
                              va='center', ha='left', fontsize=15)

            # Tonnage legend (bottom section of legend panel)
            tonnage_key = 10 ** np.arange(1, np.ceil(np.log10(tmax)), 1)[::-1]
            Nk = min(tonnage_key.size, 6)  # Limit to 6 entries max
            tonnage_y_start = 0.38
            tonnage_y_spacing = 0.08

            ax_legend.text(legend_x, 0.46, 'Mine output (tonnes)',
                          weight='bold', va='top', ha='left', fontsize=16)

            for k in range(Nk):
                y_pos = tonnage_y_start - k * tonnage_y_spacing
                # Graduated marker sizes (large to small)
                marker_size = 18 - 2 * k
                ax_legend.plot(legend_x, y_pos, 'o', color='black',
                              markersize=marker_size, clip_on=False)
                ax_legend.text(legend_x + 0.14, y_pos,
                              '{:,.0f}'.format(tonnage_key[k]),
                              va='center', ha='left', fontsize=15)

        # Convert to PIL Image using bbox_inches='tight' for clean output
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=self.dpi,
                   facecolor='white', edgecolor='none',
                   bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        img = Image.open(buf).convert('RGBA')
        plt.close(fig)

        return img

    def create_crossfade_frames(self, img1, img2, n_frames=10):
        """
        Create crossfade transition frames between two images.

        Args:
            img1: First PIL Image
            img2: Second PIL Image
            n_frames: Number of transition frames

        Returns:
            List of PIL Images for the transition
        """
        # Ensure images are same size
        if img1.size != img2.size:
            # Resize to larger dimensions
            max_width = max(img1.width, img2.width)
            max_height = max(img1.height, img2.height)
            img1 = img1.resize((max_width, max_height), Image.Resampling.LANCZOS)
            img2 = img2.resize((max_width, max_height), Image.Resampling.LANCZOS)

        frames = []
        for i in range(n_frames):
            alpha = i / (n_frames - 1) if n_frames > 1 else 1.0
            blended = Image.blend(img1, img2, alpha)
            frames.append(blended.convert('P', palette=Image.ADAPTIVE, colors=256))

        return frames

    def create_animation(self, frames, output_filename, include_transitions=True):
        """
        Create an animated GIF from a list of frames.

        Args:
            frames: List of AnimationFrame objects with rendered images
            output_filename: Output filename (without path)
            include_transitions: Whether to include crossfade transitions

        Returns:
            Path to the created GIF
        """
        if not frames:
            raise ValueError("No frames to create animation")

        all_frames = []
        durations = []

        for i, frame in enumerate(frames):
            if frame.image is None:
                raise ValueError(f"Frame {i} has no rendered image")

            # Convert main frame to palette mode for GIF
            main_frame = frame.image.convert('P', palette=Image.ADAPTIVE, colors=256)
            all_frames.append(main_frame)
            durations.append(self.frame_duration_ms)

            # Add transition to next frame if not last and transitions enabled
            if include_transitions and i < len(frames) - 1:
                next_frame = frames[i + 1]
                if next_frame.image is not None:
                    transition_frames = self.create_crossfade_frames(
                        frame.image, next_frame.image, self.transition_frames
                    )
                    all_frames.extend(transition_frames)
                    durations.extend([self.transition_duration_ms] * len(transition_frames))

        # Save GIF
        output_path = os.path.join(self.output_dir, output_filename)
        all_frames[0].save(
            output_path,
            save_all=True,
            append_images=all_frames[1:],
            duration=durations,
            loop=0  # Infinite loop
        )

        print(f"Created animation: {output_path}")
        return output_path

    def generate_metal_content_animation_simple(self):
        """
        Generate simple metal content animation: 2022 baseline -> 2040 BAU unconstrained

        Returns:
            Path to the created GIF
        """
        print("\n=== Generating Metal Content Animation (2022 -> 2040 Unconstrained) ===")

        # Define frames - using combined file layer names
        # Note: 2022_baseline only exists in unconstrained file
        frame_configs = [
            {
                "year": 2022,
                "scenario": "country_unconstrained",
                "constraint": "baseline",
                "layer": "2022_baseline",
                "title": "Mine Sites - ",
                "title_highlight": "2022",
                "subtitle": None
            },
            {
                "year": 2040,
                "scenario": "country_unconstrained",
                "constraint": "unconstrained",
                "layer": "bau_2040_mid_min_threshold_metal_tons",
                "title": "Mine Sites - ",
                "title_highlight": "2040",
                "subtitle": None
            }
        ]

        # Load data and create frames
        frames = []
        all_tonnages = []

        for cfg in frame_configs:
            print(f"  Loading data for {cfg['year']} {cfg['constraint']}...")
            data = self.load_metal_content_data(cfg["scenario"], cfg["layer"])
            frame = AnimationFrame(
                year=cfg["year"],
                scenario=cfg["scenario"],
                constraint=cfg["constraint"],
                title=cfg["title"],
                title_highlight=cfg.get("title_highlight"),
                subtitle=cfg.get("subtitle"),
                data=data
            )
            frames.append(frame)
            if len(data) > 0:
                all_tonnages.extend(data["total_tons"].values.tolist())

        # Calculate global max for consistent scaling
        tmax = max(all_tonnages) if all_tonnages else 1

        # Render frames
        print("  Rendering frames...")
        for frame in frames:
            frame.image = self.render_frame_to_image(frame, tmax)

        # Create animation
        return self.create_animation(
            frames,
            "metal_content_2022_to_2040_unconstrained.gif"
        )

    def generate_metal_content_animation_with_constraints(self):
        """
        Generate metal content animation with constraint comparison:
        2040 BAU unconstrained -> 2040 BAU constrained

        Returns:
            Path to the created GIF
        """
        print("\n=== Generating Metal Content Animation (2040 Unconstrained -> 2040 Constrained) ===")

        # Define frames - using combined file layer names
        # Comparing unconstrained vs constrained at 2040
        frame_configs = [
            {
                "year": 2040,
                "scenario": "country_unconstrained",
                "constraint": "unconstrained",
                "layer": "bau_2040_mid_min_threshold_metal_tons",
                "title": "Mine Sites 2040 - ",
                "title_highlight": "No Environmental Constraints",
                "subtitle": None
            },
            {
                "year": 2040,
                "scenario": "country_constrained",
                "constraint": "constrained",
                "layer": "bau_2040_mid_min_threshold_metal_tons",
                "title": "Mine Sites 2040 - ",
                "title_highlight": "With Environmental Constraints",
                "subtitle": None
            }
        ]

        # Load data and create frames
        frames = []
        all_tonnages = []

        for cfg in frame_configs:
            print(f"  Loading data for {cfg['year']} {cfg['constraint']}...")
            data = self.load_metal_content_data(cfg["scenario"], cfg["layer"])
            frame = AnimationFrame(
                year=cfg["year"],
                scenario=cfg["scenario"],
                constraint=cfg["constraint"],
                title=cfg["title"],
                title_highlight=cfg.get("title_highlight"),
                subtitle=cfg.get("subtitle"),
                data=data
            )
            frames.append(frame)
            if len(data) > 0:
                all_tonnages.extend(data["total_tons"].values.tolist())

        # Calculate global max for consistent scaling
        tmax = max(all_tonnages) if all_tonnages else 1

        # Render frames
        print("  Rendering frames...")
        for frame in frames:
            frame.image = self.render_frame_to_image(frame, tmax)

        # Create animation
        return self.create_animation(
            frames,
            "metal_content_2040_unconstrained_vs_constrained.gif"
        )

    def generate_metal_content_animation_brief_match(self):
        """
        Generate metal content animation with custom totals for brief matching.

        Shows 2022 baseline -> 2040 BAU unconstrained with specific totals:
        - 2022: 15.0 million tonnes
        - 2040: 14.1 million tonnes

        Returns:
            Path to the created GIF
        """
        print("\n=== Generating Metal Content Animation (Brief Match - Custom Totals) ===")

        # Define frames with custom totals
        frame_configs = [
            {
                "year": 2022,
                "scenario": "country_unconstrained",
                "constraint": "baseline",
                "layer": "2022_baseline",
                "title": "Mine Sites - ",
                "title_highlight": "2022",
                "subtitle": None,
                "total_override": 15.0  # Custom total for 2022
            },
            {
                "year": 2040,
                "scenario": "country_unconstrained",
                "constraint": "unconstrained",
                "layer": "bau_2040_mid_min_threshold_metal_tons",
                "title": "Mine Sites - ",
                "title_highlight": "2040",
                "subtitle": None,
                "total_override": 14.1  # Custom total for 2040
            }
        ]

        # Load data and create frames
        frames = []
        all_tonnages = []

        for cfg in frame_configs:
            print(f"  Loading data for {cfg['year']} {cfg['constraint']}...")
            data = self.load_metal_content_data(cfg["scenario"], cfg["layer"])
            frame = AnimationFrame(
                year=cfg["year"],
                scenario=cfg["scenario"],
                constraint=cfg["constraint"],
                title=cfg["title"],
                title_highlight=cfg.get("title_highlight"),
                subtitle=cfg.get("subtitle"),
                data=data
            )
            # Store the custom total in the frame for later use
            frame.total_override = cfg.get("total_override")
            frames.append(frame)
            if len(data) > 0:
                all_tonnages.extend(data["total_tons"].values.tolist())

        # Calculate global max for consistent scaling
        tmax = max(all_tonnages) if all_tonnages else 1

        # Render frames with custom totals
        print("  Rendering frames with custom totals...")
        for frame in frames:
            print(f"    {frame.year}: displaying total = {frame.total_override} Mt")
            frame.image = self.render_frame_to_image(
                frame, tmax, total_override=frame.total_override
            )

        # Create animation
        return self.create_animation(
            frames,
            "metal_content_2022_to_2040_unconstrained_brief_match.gif"
        )

    def generate_metal_content_animation_constraints_brief_match(self):
        """
        Generate metal content animation comparing unconstrained vs constrained
        with custom totals for brief matching.

        Shows 2040 BAU unconstrained -> 2040 BAU constrained with specific totals:
        - Unconstrained: 14.1 million tonnes
        - Constrained: 11.6 million tonnes

        Returns:
            Path to the created GIF
        """
        print("\n=== Generating Metal Content Animation (Constraints Brief Match - Custom Totals) ===")

        # Define frames with custom totals
        frame_configs = [
            {
                "year": 2040,
                "scenario": "country_unconstrained",
                "constraint": "unconstrained",
                "layer": "bau_2040_mid_min_threshold_metal_tons",
                "title": "Mine Sites 2040 - ",
                "title_highlight": "No Environmental Constraints",
                "subtitle": None,
                "total_override": 14.1  # Custom total for unconstrained
            },
            {
                "year": 2040,
                "scenario": "country_constrained",
                "constraint": "constrained",
                "layer": "bau_2040_mid_min_threshold_metal_tons",
                "title": "Mine Sites 2040 - ",
                "title_highlight": "With Environmental Constraints",
                "subtitle": None,
                "total_override": 11.6  # Custom total for constrained
            }
        ]

        # Load data and create frames
        frames = []
        all_tonnages = []

        for cfg in frame_configs:
            print(f"  Loading data for {cfg['year']} {cfg['constraint']}...")
            data = self.load_metal_content_data(cfg["scenario"], cfg["layer"])
            frame = AnimationFrame(
                year=cfg["year"],
                scenario=cfg["scenario"],
                constraint=cfg["constraint"],
                title=cfg["title"],
                title_highlight=cfg.get("title_highlight"),
                subtitle=cfg.get("subtitle"),
                data=data
            )
            # Store the custom total in the frame for later use
            frame.total_override = cfg.get("total_override")
            frames.append(frame)
            if len(data) > 0:
                all_tonnages.extend(data["total_tons"].values.tolist())

        # Calculate global max for consistent scaling
        tmax = max(all_tonnages) if all_tonnages else 1

        # Render frames with custom totals
        print("  Rendering frames with custom totals...")
        for frame in frames:
            print(f"    {frame.constraint}: displaying total = {frame.total_override} Mt")
            frame.image = self.render_frame_to_image(
                frame, tmax, total_override=frame.total_override
            )

        # Create animation
        return self.create_animation(
            frames,
            "metal_content_2040_unconstrained_vs_constrained_brief_match.gif"
        )

    def generate_all_metal_content_animations(self):
        """Generate all metal content animations."""
        results = []
        results.append(self.generate_metal_content_animation_simple())
        results.append(self.generate_metal_content_animation_with_constraints())
        return results

    # =========================================================================
    # PROCESSING LOCATIONS ANIMATIONS
    # =========================================================================

    # Precursor stages for each mineral (highest processing stage)
    PRECURSOR_STAGES = {
        "copper": 5.0,
        "cobalt": 5.0,
        "manganese": 4.1,
        "lithium": 4.2,
        "graphite": 4.0,
        "nickel": 5.0
    }

    def load_processing_locations_data(self, scenario, layer, policy_name):
        """
        Load processing locations data from GPKG file.

        Args:
            scenario: Full scenario name (e.g., 'country_unconstrained', 'region_unconstrained')
            layer: Layer name (e.g., 'precursor_2040_mid_min_threshold_metal_tons')
            policy_name: Policy name for column lookup ('country' or 'region')

        Returns:
            GeoDataFrame with total_tons and geometry columns for each mineral
        """
        fname = f"combined_node_locations_for_energy_conversion_{scenario}.gpkg"
        fpath = os.path.join(output_path, "optimised_processing_locations", fname)

        if not os.path.exists(fpath):
            raise FileNotFoundError(f"GPKG file not found: {fpath}")

        print(f"    Loading: {fname} / {layer}")
        df = gpd.read_file(fpath, layer=layer)

        # Extract processing output for each mineral at precursor stage
        dfs = []
        for rf, rc in zip(REFERENCE_MINERALS, REFERENCE_MINERAL_COLORS):
            stage = self.PRECURSOR_STAGES[rf]
            col = f"{rf}_final_stage_production_tons_{stage}_in_{policy_name}"

            if col in df.columns:
                df["total_tons"] = df[col]
                mineral_df = df[df["total_tons"] > 0].copy()
                mineral_df = mineral_df[["total_tons", "geometry"]]
                mineral_df["reference_mineral"] = rf
                mineral_df["color"] = rc
                dfs.append(mineral_df)

        if not dfs:
            return gpd.GeoDataFrame()

        result = pd.concat(dfs, axis=0, ignore_index=True)
        return gpd.GeoDataFrame(result, geometry="geometry")

    def render_processing_frame_to_image(self, frame, tmax, show_legend=True):
        """
        Render a single processing locations frame to a PIL Image.

        Uses the same layout as metal content maps but with processing-specific legend.

        Args:
            frame: AnimationFrame object with data loaded
            tmax: Maximum tonnage value for consistent marker sizing
            show_legend: Whether to show the legend panel

        Returns:
            PIL Image of the rendered frame
        """
        import matplotlib.gridspec as gridspec

        # Figure setup - same as metal content
        figwidth = 14
        figheight = 8

        fig = plt.figure(figsize=(figwidth, figheight), facecolor='white')

        # Add main title with optional highlighting
        self.render_multicolor_title(fig, frame)

        if show_legend:
            gs = gridspec.GridSpec(1, 2, width_ratios=[4, 1], wspace=0.02,
                                   left=0.01, right=0.99, top=0.92, bottom=0.01)
            ax_map = fig.add_subplot(gs[0, 0])
            ax_legend = fig.add_subplot(gs[0, 1])
        else:
            ax_map = fig.add_subplot(111)
            fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.01)
            ax_legend = None

        # Configure map axis
        ax_map.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        ax_map.set_aspect('equal')
        ax_map.set_xticks([])
        ax_map.set_yticks([])

        # Plot basemap with tighter bounds
        ax_map = plot_ccg_basemap(
            ax_map,
            include_continents=["Africa"],
            include_countries=self.ccg_isos,
            include_labels=True,
            xmin_offset=-0.5,
            xmax_offset=2.0,
            ymin_offset=2.0,
            ymax_offset=0.5
        )

        # Plot processing location data
        df = frame.data
        total_mt = 0
        if df is not None and len(df) > 0:
            df["markersize"] = self.marker_size_max * (df["total_tons"] / tmax) ** 0.5
            df = df.sort_values(by="total_tons", ascending=False)
            df.geometry.plot(
                ax=ax_map,
                color=df["color"],
                edgecolor='none',
                markersize=df["markersize"],
                alpha=0.7
            )
            total_mt = df["total_tons"].sum() / 1e6

        # Draw legend
        if show_legend and ax_legend is not None:
            ax_legend.set_xlim(0, 1)
            ax_legend.set_ylim(0, 1)
            ax_legend.set_xticks([])
            ax_legend.set_yticks([])
            ax_legend.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
            ax_legend.patch.set_facecolor('white')

            legend_x = 0.1
            mineral_y_start = 0.86
            mineral_y_spacing = 0.07

            ax_legend.text(legend_x, 0.95, 'Mineral processed',
                          weight='bold', va='top', ha='left', fontsize=16)

            Nk_minerals = len(REFERENCE_MINERALS)
            for k in range(Nk_minerals):
                y_pos = mineral_y_start - k * mineral_y_spacing
                ax_legend.plot(legend_x, y_pos, 's',
                              mfc=REFERENCE_MINERAL_COLORS[k],
                              mec=REFERENCE_MINERAL_COLORS[k],
                              ms=16, clip_on=False)
                ax_legend.text(legend_x + 0.14, y_pos,
                              REFERENCE_MINERALS[k].capitalize(),
                              va='center', ha='left', fontsize=15)

            # Tonnage legend
            tonnage_key = 10 ** np.arange(1, np.ceil(np.log10(tmax)), 1)[::-1]
            Nk = min(tonnage_key.size, 6)
            tonnage_y_start = 0.38
            tonnage_y_spacing = 0.08

            ax_legend.text(legend_x, 0.46, 'Processing output (tonnes)',
                          weight='bold', va='top', ha='left', fontsize=16)

            for k in range(Nk):
                y_pos = tonnage_y_start - k * tonnage_y_spacing
                marker_size = 18 - 2 * k
                ax_legend.plot(legend_x, y_pos, 'o', color='black',
                              markersize=marker_size, clip_on=False)
                ax_legend.text(legend_x + 0.14, y_pos,
                              '{:,.0f}'.format(tonnage_key[k]),
                              va='center', ha='left', fontsize=15)

        # Convert to PIL Image
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=self.dpi,
                   facecolor='white', edgecolor='none',
                   bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        img = Image.open(buf).convert('RGBA')
        plt.close(fig)

        return img

    def generate_processing_locations_animation_policy_comparison(
        self,
        scenario="precursor",
        year=2040,
        percentile="mid"
    ):
        """
        Generate processing locations animation comparing National vs Regional policy.

        Sequence: National Policy -> Regional Policy

        Args:
            scenario: Scenario name ('bau', 'early_refining', 'precursor')
            year: Year (2040)
            percentile: Demand percentile ('low', 'mid', 'high')

        Returns:
            Path to the created GIF
        """
        scenario_title = scenario.replace("_", " ").title()
        print(f"\n=== Generating Processing Locations Animation ({scenario_title} {year} - National vs Regional) ===")

        # Define frame configurations
        frame_configs = [
            {
                "full_scenario": "country_unconstrained",
                "layer": f"{scenario}_{year}_{percentile}_min_threshold_metal_tons",
                "policy_name": "country",
                "title": f"Processing Locations {year} - ",
                "title_highlight": "National Policy",
                "subtitle": None
            },
            {
                "full_scenario": "region_unconstrained",
                "layer": f"{scenario}_{year}_{percentile}_max_threshold_metal_tons",
                "policy_name": "region",
                "title": f"Processing Locations {year} - ",
                "title_highlight": "Regional Policy",
                "subtitle": None
            }
        ]

        # Load data and create frames
        frames = []
        all_tonnages = []

        print("  Loading processing location data...")
        for cfg in frame_configs:
            print(f"    {cfg['policy_name']}...")
            try:
                data = self.load_processing_locations_data(
                    scenario=cfg["full_scenario"],
                    layer=cfg["layer"],
                    policy_name=cfg["policy_name"]
                )
                frame = AnimationFrame(
                    year=year,
                    scenario=scenario,
                    constraint=cfg["policy_name"],
                    title=cfg["title"],
                    title_highlight=cfg.get("title_highlight"),
                    subtitle=cfg.get("subtitle"),
                    data=data
                )
                frames.append(frame)
                if len(data) > 0:
                    all_tonnages.extend(data["total_tons"].values.tolist())
            except FileNotFoundError as e:
                print(f"    Warning: {e}")
                continue

        if not frames:
            raise ValueError("No valid frames could be created")

        # Calculate global max for consistent scaling
        tmax = max(all_tonnages) if all_tonnages else 1

        # Render frames
        print("  Rendering frames...")
        for i, frame in enumerate(frames):
            print(f"    Frame {i+1}/{len(frames)}: {frame.constraint}")
            frame.image = self.render_processing_frame_to_image(frame, tmax)

        # Create animation
        output_filename = f"processing_locations_{scenario}_{year}_{percentile}_unconstrained_national_vs_regional.gif"
        return self.create_animation(frames, output_filename)

    def generate_all_processing_locations_animations(self):
        """Generate all processing locations animations."""
        results = []
        # Precursor scenario - National vs Regional
        results.append(
            self.generate_processing_locations_animation_policy_comparison(
                scenario="precursor",
                year=2040,
                percentile="mid"
            )
        )
        return results

    # =========================================================================
    # AGGREGATED FLOW MAP ANIMATIONS
    # =========================================================================

    def load_aggregated_flow_data(self, scenario, year, percentile, threshold, policy, constraint):
        """
        Load aggregated flow data from GeoParquet file.

        Args:
            scenario: Scenario name ('bau', 'early_refining', 'precursor')
            year: Year (2022, 2030, 2040)
            percentile: Demand percentile ('baseline', 'low', 'mid', 'high')
            threshold: Threshold type ('min_threshold_metal_tons', 'max_threshold_metal_tons')
            policy: Policy case ('country', 'region')
            constraint: Constraint type ('unconstrained', 'constrained')

        Returns:
            GeoDataFrame with flow data for roads and rails
        """
        flow_data_folder = os.path.join(output_path, "aggregated_node_edge_flows")

        # Build filename based on scenario parameters
        if year == 2022:
            # Baseline only
            filename = f"edges_combined_flows_baseline_2022_{policy}_{constraint}.geoparquet"
        else:
            # 2030/2040 scenarios
            scenario_name = scenario.replace(" ", "_")
            filename = f"edges_combined_flows_{percentile}_{threshold}_{scenario_name}_{year}_{policy}_{constraint}.geoparquet"

        filepath = os.path.join(flow_data_folder, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Flow data file not found: {filepath}")

        print(f"    Loading: {filename}")
        edges_df = gpd.read_parquet(filepath)

        # Filter out invalid geometries
        edges_df = edges_df[~edges_df.geometry.isna()]

        # Load nodes to filter edges to CCG countries
        nodes_filename = filename.replace("edges_", "nodes_")
        nodes_filepath = os.path.join(flow_data_folder, nodes_filename)

        if os.path.exists(nodes_filepath):
            nodes_df = gpd.read_parquet(nodes_filepath)
            # Get nodes within CCG countries that are road/rail
            ccg_nodes = nodes_df[
                (nodes_df["iso3"].isin(self.ccg_isos)) &
                (nodes_df["mode"].isin(["road", "rail"]))
            ]["id"].values.tolist()
            del nodes_df

            # Filter edges to only those connected to CCG nodes
            edges_df = edges_df[
                (edges_df["from_id"].isin(ccg_nodes)) |
                (edges_df["to_id"].isin(ccg_nodes))
            ]
            del ccg_nodes

        # Calculate total flow (export + inter-country)
        flow_column = "final_stage_production_tons"
        edges_df[flow_column] = (
            edges_df[f"{flow_column}_export"] +
            edges_df[f"{flow_column}_inter"]
        )

        # Filter to positive flows only
        edges_df = edges_df[edges_df[flow_column] > 0]

        # Filter to road and rail modes only
        edges_df = edges_df[edges_df["mode"].isin(["road", "rail"])]

        return edges_df

    def render_flow_frame_to_image(self, frame, weight_bins, show_legend=True):
        """
        Render a single flow map frame to a PIL Image.

        Args:
            frame: AnimationFrame object with flow data loaded
            weight_bins: Pre-calculated weight bins for consistent line widths
            show_legend: Whether to show the legend panel

        Returns:
            PIL Image of the rendered frame
        """
        import matplotlib.gridspec as gridspec
        from shapely.geometry import LineString

        # Mode colors (matching agg_flow_maps.py)
        modes = ["road", "rail"]
        mode_colors = {"road": "#543005", "rail": "#003c30"}
        mode_labels = {"road": "Roads", "rail": "Railways"}

        # Figure setup with side-panel layout - reduced height for tighter layout
        figwidth = 14
        figheight = 8

        fig = plt.figure(figsize=(figwidth, figheight), facecolor='white')

        # Add main title with optional highlighting (same as other animations)
        self.render_multicolor_title(fig, frame)

        if show_legend:
            gs = gridspec.GridSpec(1, 2, width_ratios=[4, 1], wspace=0.02,
                                   left=0.01, right=0.99, top=0.92, bottom=0.01)
            ax_map = fig.add_subplot(gs[0, 0])
            ax_legend = fig.add_subplot(gs[0, 1])
        else:
            ax_map = fig.add_subplot(111)
            fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.01)
            ax_legend = None

        # Configure map axis
        ax_map.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        ax_map.set_aspect('equal')
        ax_map.set_xticks([])
        ax_map.set_yticks([])

        # Plot basemap with tighter bounds (reduced ocean space)
        ax_map = plot_ccg_basemap(
            ax_map,
            include_continents=["Africa"],
            include_countries=self.ccg_isos,
            include_labels=True,
            xmin_offset=-0.5,
            xmax_offset=2.0,      # Reduced from 3.5
            ymin_offset=2.0,      # Reduced from 6.5 - less ocean at bottom
            ymax_offset=0.5
        )

        # Plot flow data if available
        df = frame.data
        total_mt = 0
        flow_column = "final_stage_production_tons"

        if df is not None and len(df) > 0:
            # Calculate line widths based on weight bins
            def get_line_width(val):
                for (nmin, nmax), width in weight_bins.items():
                    if nmin <= val < nmax:
                        return width
                # Default to smallest width if outside range
                return list(weight_bins.values())[0]

            df = df.copy()
            df["linewidth"] = df[flow_column].apply(get_line_width)

            # Buffer geometries for visualization
            df["geometry"] = df.apply(
                lambda x: x.geometry.buffer(x.linewidth), axis=1
            )
            df = gpd.GeoDataFrame(df, geometry="geometry")

            # Sort by flow value (largest on bottom for better visibility)
            df = df.sort_values(by=flow_column, ascending=False)

            # Plot by mode
            for mode in modes:
                mode_df = df[df["mode"] == mode]
                if len(mode_df) > 0:
                    mode_df.geometry.plot(
                        ax=ax_map,
                        facecolor=mode_colors[mode],
                        edgecolor='none',
                        linewidth=0,
                        alpha=0.7
                    )

            total_mt = df[flow_column].sum() / 1e6

        # Add total annotation (in gigatonnes) - positioned relative to actual axis limits
        total_gt = total_mt / 1000  # Convert million tonnes to gigatonnes
        ax_xlim = ax_map.get_xlim()
        ax_ylim = ax_map.get_ylim()
        ax_map.text(
            (ax_xlim[0] + ax_xlim[1]) / 2,  # Center horizontally
            ax_ylim[0] + 0.02 * (ax_ylim[1] - ax_ylim[0]),  # Near bottom edge
            f'Total Flow = {total_gt:.1f} Gt',
            fontsize=16, weight='bold', ha='center', va='bottom'
        )

        # Draw legend in the side panel
        if show_legend and ax_legend is not None:
            ax_legend.set_xlim(0, 1)
            ax_legend.set_ylim(0, 1)
            ax_legend.set_xticks([])
            ax_legend.set_yticks([])
            ax_legend.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
            ax_legend.patch.set_facecolor('white')

            legend_x = 0.1

            # Mode type legend (top section)
            ax_legend.text(legend_x, 0.95, 'Transport Mode',
                          weight='bold', va='top', ha='left', fontsize=16)

            mode_y_start = 0.84
            mode_y_spacing = 0.08
            for k, mode in enumerate(modes):
                y_pos = mode_y_start - k * mode_y_spacing
                ax_legend.plot(legend_x, y_pos, 's',
                              mfc=mode_colors[mode],
                              mec=mode_colors[mode],
                              ms=16, clip_on=False)
                ax_legend.text(legend_x + 0.14, y_pos,
                              mode_labels[mode],
                              va='center', ha='left', fontsize=15)

            # Flow volume legend (bottom section)
            ax_legend.text(legend_x, 0.64, 'Annual Flow (tonnes)',
                          weight='bold', va='top', ha='left', fontsize=16)

            # Get weight bin ranges for legend
            weight_items = list(weight_bins.items())
            Nk = min(len(weight_items), 6)
            flow_y_start = 0.54
            flow_y_spacing = 0.10

            for k in range(Nk):
                (nmin, nmax), width = weight_items[-(k+1)]  # Reverse order (large to small)
                y_pos = flow_y_start - k * flow_y_spacing

                # Draw line segment
                line_x = [legend_x - 0.02, legend_x + 0.06]
                line_y = [y_pos, y_pos]
                # Scale width for visibility in legend
                legend_line_width = 2 + k * 1.5
                ax_legend.plot(line_x, line_y, '-', color='black',
                              linewidth=legend_line_width, solid_capstyle='butt')

                # Format numbers
                if nmax >= 1e6:
                    label = f'{nmin/1e6:.1f}M - {nmax/1e6:.1f}M'
                elif nmax >= 1e3:
                    label = f'{nmin/1e3:.0f}k - {nmax/1e3:.0f}k'
                else:
                    label = f'{nmin:.0f} - {nmax:.0f}'

                ax_legend.text(legend_x + 0.14, y_pos, label,
                              va='center', ha='left', fontsize=15)

        # Convert to PIL Image
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=self.dpi,
                   facecolor='white', edgecolor='none',
                   bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        img = Image.open(buf).convert('RGBA')
        plt.close(fig)

        return img

    def generate_aggregated_flow_animation_policy_comparison(
        self,
        scenario="precursor",
        year=2040,
        percentile="mid"
    ):
        """
        Generate aggregated flow animation comparing all policy combinations.

        Sequence: Country Unconstrained -> Region Unconstrained ->
                  Country Constrained -> Region Constrained

        Args:
            scenario: Scenario name ('bau', 'early_refining', 'precursor')
            year: Year (2040)
            percentile: Demand percentile ('low', 'mid', 'high')

        Returns:
            Path to the created GIF
        """
        scenario_title = scenario.replace("_", " ").title()
        print(f"\n=== Generating Aggregated Flow Animation ({scenario_title} {year} - Policy Comparison) ===")

        # Define frame configurations
        # Note: country uses min_threshold, region uses max_threshold
        frame_configs = [
            {
                "policy": "country",
                "constraint": "unconstrained",
                "threshold": "min_threshold_metal_tons",
                "title": f"{scenario_title} {year} - National Policy\nNo Environmental Constraints"
            },
            {
                "policy": "region",
                "constraint": "unconstrained",
                "threshold": "max_threshold_metal_tons",
                "title": f"{scenario_title} {year} - Regional Policy\nNo Environmental Constraints"
            },
            {
                "policy": "country",
                "constraint": "constrained",
                "threshold": "min_threshold_metal_tons",
                "title": f"{scenario_title} {year} - National Policy\nWith Environmental Constraints"
            },
            {
                "policy": "region",
                "constraint": "constrained",
                "threshold": "max_threshold_metal_tons",
                "title": f"{scenario_title} {year} - Regional Policy\nWith Environmental Constraints"
            }
        ]

        # Load data and create frames
        frames = []
        all_flows = []
        flow_column = "final_stage_production_tons"

        print("  Loading flow data...")
        for cfg in frame_configs:
            print(f"    {cfg['policy']} + {cfg['constraint']}...")
            try:
                data = self.load_aggregated_flow_data(
                    scenario=scenario,
                    year=year,
                    percentile=percentile,
                    threshold=cfg["threshold"],
                    policy=cfg["policy"],
                    constraint=cfg["constraint"]
                )
                frame = AnimationFrame(
                    year=year,
                    scenario=scenario,
                    constraint=f"{cfg['policy']}_{cfg['constraint']}",
                    title=cfg["title"],
                    data=data
                )
                frames.append(frame)
                if len(data) > 0:
                    all_flows.extend(data[flow_column].values.tolist())
            except FileNotFoundError as e:
                print(f"    Warning: {e}")
                continue

        if not frames:
            raise ValueError("No valid frames could be created")

        # Calculate global weight bins for consistent scaling
        print("  Calculating weight bins...")
        # Use fixed ranges similar to agg_flow_maps.py for consistency
        min_flow = 0.03
        max_flow = 12000000.00
        all_flows = [min_flow, 2e5, 1e6, 4e6, 8e6, max_flow]

        weight_bins = generate_weight_bins(
            all_flows,
            width_step=0.08,
            n_steps=6,
            interpolation='fisher-jenks'
        )

        # Render frames
        print("  Rendering frames...")
        for i, frame in enumerate(frames):
            print(f"    Frame {i+1}/{len(frames)}: {frame.constraint}")
            frame.image = self.render_flow_frame_to_image(frame, weight_bins)

        # Create animation
        output_filename = f"aggregated_flows_{scenario}_{year}_{percentile}_policy_comparison.gif"
        return self.create_animation(frames, output_filename)

    def generate_aggregated_flow_animation_unconstrained_only(
        self,
        scenario="precursor",
        year=2040,
        percentile="mid"
    ):
        """
        Generate aggregated flow animation comparing National vs Regional policy
        (unconstrained scenarios only).

        Sequence: National Policy -> Regional Policy

        Args:
            scenario: Scenario name ('bau', 'early_refining', 'precursor')
            year: Year (2040)
            percentile: Demand percentile ('low', 'mid', 'high')

        Returns:
            Path to the created GIF
        """
        scenario_title = scenario.replace("_", " ").title()
        print(f"\n=== Generating Aggregated Flow Animation ({scenario_title} {year} - National vs Regional) ===")

        # Define frame configurations (unconstrained only)
        frame_configs = [
            {
                "policy": "country",
                "constraint": "unconstrained",
                "threshold": "min_threshold_metal_tons",
                "title": f"Transport Flows {year} - ",
                "title_highlight": "National Policy",
                "subtitle": None
            },
            {
                "policy": "region",
                "constraint": "unconstrained",
                "threshold": "max_threshold_metal_tons",
                "title": f"Transport Flows {year} - ",
                "title_highlight": "Regional Policy",
                "subtitle": None
            }
        ]

        # Load data and create frames
        frames = []
        all_flows = []
        flow_column = "final_stage_production_tons"

        print("  Loading flow data...")
        for cfg in frame_configs:
            print(f"    {cfg['policy']}...")
            try:
                data = self.load_aggregated_flow_data(
                    scenario=scenario,
                    year=year,
                    percentile=percentile,
                    threshold=cfg["threshold"],
                    policy=cfg["policy"],
                    constraint=cfg["constraint"]
                )
                frame = AnimationFrame(
                    year=year,
                    scenario=scenario,
                    constraint=f"{cfg['policy']}_{cfg['constraint']}",
                    title=cfg["title"],
                    title_highlight=cfg.get("title_highlight"),
                    subtitle=cfg.get("subtitle"),
                    data=data
                )
                frames.append(frame)
                if len(data) > 0:
                    all_flows.extend(data[flow_column].values.tolist())
            except FileNotFoundError as e:
                print(f"    Warning: {e}")
                continue

        if not frames:
            raise ValueError("No valid frames could be created")

        # Calculate global weight bins for consistent scaling
        print("  Calculating weight bins...")
        min_flow = 0.03
        max_flow = 12000000.00
        all_flows = [min_flow, 2e5, 1e6, 4e6, 8e6, max_flow]

        weight_bins = generate_weight_bins(
            all_flows,
            width_step=0.08,
            n_steps=6,
            interpolation='fisher-jenks'
        )

        # Render frames
        print("  Rendering frames...")
        for i, frame in enumerate(frames):
            print(f"    Frame {i+1}/{len(frames)}: {frame.constraint}")
            frame.image = self.render_flow_frame_to_image(frame, weight_bins)

        # Create animation
        output_filename = f"aggregated_flows_{scenario}_{year}_{percentile}_national_vs_regional.gif"
        return self.create_animation(frames, output_filename)

    def generate_aggregated_flow_animation_baseline_vs_regional(
        self,
        scenario="precursor",
        year=2040,
        percentile="mid"
    ):
        """
        Generate aggregated flow animation comparing 2022 baseline with 2040 Regional policy.

        Sequence: 2022 Baseline -> 2040 Regional Unconstrained

        Args:
            scenario: Scenario name ('bau', 'early_refining', 'precursor')
            year: Year (2040)
            percentile: Demand percentile ('low', 'mid', 'high')

        Returns:
            Path to the created GIF
        """
        scenario_title = scenario.replace("_", " ").title()
        print(f"\n=== Generating Aggregated Flow Animation (2022 Baseline vs {year} Regional) ===")

        # Define frame configurations
        frame_configs = [
            {
                "scenario": "baseline",
                "year": 2022,
                "percentile": "baseline",
                "policy": "country",
                "constraint": "unconstrained",
                "threshold": "min_threshold_metal_tons",
                "title": "Transport Flows - ",
                "title_highlight": "2022 Baseline",
            },
            {
                "scenario": scenario,
                "year": year,
                "percentile": percentile,
                "policy": "region",
                "constraint": "unconstrained",
                "threshold": "max_threshold_metal_tons",
                "title": f"Transport Flows - ",
                "title_highlight": f"{year} Regional {scenario_title}",
            }
        ]

        # Load data and create frames
        frames = []
        all_flows = []
        flow_column = "final_stage_production_tons"

        print("  Loading flow data...")
        for cfg in frame_configs:
            print(f"    {cfg['year']} {cfg['policy']}...")
            try:
                data = self.load_aggregated_flow_data(
                    scenario=cfg["scenario"],
                    year=cfg["year"],
                    percentile=cfg["percentile"],
                    threshold=cfg["threshold"],
                    policy=cfg["policy"],
                    constraint=cfg["constraint"]
                )
                frame = AnimationFrame(
                    year=cfg["year"],
                    scenario=cfg["scenario"],
                    constraint=f"{cfg['policy']}_{cfg['constraint']}",
                    title=cfg["title"],
                    title_highlight=cfg.get("title_highlight"),
                    subtitle=cfg.get("subtitle"),
                    data=data
                )
                frames.append(frame)
                if len(data) > 0:
                    all_flows.extend(data[flow_column].values.tolist())
            except FileNotFoundError as e:
                print(f"    Warning: {e}")
                continue

        if not frames:
            raise ValueError("No valid frames could be created")

        # Calculate global weight bins for consistent scaling
        print("  Calculating weight bins...")
        min_flow = 0.03
        max_flow = 12000000.00
        all_flows = [min_flow, 2e5, 1e6, 4e6, 8e6, max_flow]

        weight_bins = generate_weight_bins(
            all_flows,
            width_step=0.08,
            n_steps=6,
            interpolation='fisher-jenks'
        )

        # Render frames
        print("  Rendering frames...")
        for i, frame in enumerate(frames):
            print(f"    Frame {i+1}/{len(frames)}: {frame.year} {frame.constraint}")
            frame.image = self.render_flow_frame_to_image(frame, weight_bins)

        # Create animation
        output_filename = f"aggregated_flows_2022_vs_{scenario}_{year}_{percentile}_regional.gif"
        return self.create_animation(frames, output_filename)

    def generate_all_aggregated_flow_animations(self):
        """Generate all aggregated flow animations."""
        results = []
        # Precursor scenario - National vs Regional (unconstrained only)
        results.append(
            self.generate_aggregated_flow_animation_unconstrained_only(
                scenario="precursor",
                year=2040,
                percentile="mid"
            )
        )
        # Precursor scenario - full policy comparison (all 4 combinations)
        results.append(
            self.generate_aggregated_flow_animation_policy_comparison(
                scenario="precursor",
                year=2040,
                percentile="mid"
            )
        )
        # 2022 baseline vs 2040 Regional
        results.append(
            self.generate_aggregated_flow_animation_baseline_vs_regional(
                scenario="precursor",
                year=2040,
                percentile="mid"
            )
        )
        return results


def main():
    """Main entry point for the animation generator."""
    parser = argparse.ArgumentParser(
        description="Generate animated map GIFs for mineral production scenarios"
    )
    parser.add_argument(
        "--animation-type",
        choices=["metal_content", "processing_locations", "flow_maps", "all"],
        default="metal_content",
        help="Type of animation to generate"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for animations"
    )
    parser.add_argument(
        "--frame-duration",
        type=int,
        default=2000,
        help="Duration of each main frame in milliseconds (default: 2000)"
    )
    parser.add_argument(
        "--transition-frames",
        type=int,
        default=10,
        help="Number of crossfade transition frames (default: 10)"
    )

    args = parser.parse_args()

    # Create generator
    generator = MapAnimationGenerator(output_dir=args.output_dir)
    generator.frame_duration_ms = args.frame_duration
    generator.transition_frames = args.transition_frames

    # Generate animations based on type
    if args.animation_type == "metal_content" or args.animation_type == "all":
        generator.generate_all_metal_content_animations()

    if args.animation_type == "processing_locations" or args.animation_type == "all":
        generator.generate_all_processing_locations_animations()

    if args.animation_type == "flow_maps" or args.animation_type == "all":
        generator.generate_all_aggregated_flow_animations()

    print("\nAnimation generation complete!")


if __name__ == "__main__":
    main()
