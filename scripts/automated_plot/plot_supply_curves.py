#!/usr/bin/env python3
"""
Supply Curve Plots for Automated Analysis

This script creates supply curve visualizations using the standardized all_data.xlsx
structure and automated plot configuration system. Adapts the supply curve logic
from new_bar_charts.py to work with the modern automated plotting framework.

Supply curves show the relationship between cumulative production capacity and
unit costs, helping visualize the cost structure across different countries
and processing scenarios.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from plot_config import (
    reference_minerals,
    reference_mineral_colors,
    reference_mineral_colormap,
    get_goal_from_scenario,
    mineral_processing_stages
)
from plot_utils import format_legend


def create_country_color_map(countries):
    """
    Create a consistent country color map using the same approach as new_bar_charts.py
    
    Parameters:
    -----------
    countries : list
        List of country ISO3 codes
        
    Returns:
    --------
    dict
        Mapping of country codes to hex colors
    """
    num_countries = len(countries)
    # Use the same colormap as new_bar_charts.py for consistency
    colormap = plt.colormaps['tab20']  # Get the 'tab20' colormap
    colors = colormap(np.linspace(0, 1, num_countries))  # Sample colors
    
    # Convert colors to hex format (same as original script)
    country_colors = [plt.matplotlib.colors.rgb2hex(color) for color in colors]
    country_color_map = dict(zip(sorted(countries), country_colors))
    
    return country_color_map


def plot_supply_curve_bars(df, tons_column, unit_cost_column, ax=None, sort=True, 
                          colors=None, color_map=None, hide_small_labels=True, 
                          min_label_threshold=0.03, price_line=None, **kwargs):
    """
    Create a supply curve plot using bars instead of a step-line.
    
    Adapted from new_bar_charts.py to work with automated plot configuration.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with country data (indexed by ISO3 codes)
    tons_column : str
        Column name for production tonnage
    unit_cost_column : str
        Column name for unit costs (USD/tonne)
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. If None, creates new figure
    sort : bool, default True
        Whether to sort countries by unit cost
    color_map : dict, optional
        Country to color mapping
    hide_small_labels : bool, default True
        Whether to hide labels for small production volumes
    min_label_threshold : float, default 0.03
        Minimum fraction of total production to show label
    
    Returns:
    --------
    matplotlib.axes.Axes
        The axes object containing the plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    
    # Clean and prepare data
    df_clean = df[[tons_column, unit_cost_column]].copy()
    df_clean = df_clean.dropna()
    
    if len(df_clean) == 0:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        return ax
    
    # Sort by unit cost if requested
    if sort:
        df_clean = df_clean.sort_values(unit_cost_column)
    
    # Calculate cumulative production
    df_clean['cumulative_tons'] = df_clean[tons_column].cumsum()
    total_production = df_clean[tons_column].sum()
    
    # Set up colors - use consistent country color map
    if color_map is None and colors is None:
        countries = df_clean.index.tolist()
        color_map = create_country_color_map(countries)
    
    # Create bars
    bars = []
    x_positions = []
    widths = []
    heights = []
    bar_colors = []
    
    cumulative_width = 0
    for idx, (country, row) in enumerate(df_clean.iterrows()):
        width = row[tons_column]
        height = row[unit_cost_column]
        
        # Use color map if available
        if color_map and country in color_map:
            color = color_map[country]
        elif colors and idx < len(colors):
            color = colors[idx]
        else:
            color = f'C{idx % 10}'  # Default matplotlib colors
        
        x_positions.append(cumulative_width)
        widths.append(width)
        heights.append(height)
        bar_colors.append(color)
        
        cumulative_width += width
    
    # Plot bars
    bars = ax.bar(x_positions, heights, width=widths, color=bar_colors, 
                  align='edge', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Add country labels on bars (if not too small and wide enough)
    for i, (country, row) in enumerate(df_clean.iterrows()):
        production_fraction = row[tons_column] / total_production
        bar_width = widths[i]
        
        # Only show label if bar meets both percentage AND minimum width thresholds
        meets_percentage = production_fraction >= min_label_threshold
        meets_width = bar_width >= (total_production * 0.02)  # At least 2% of total width
        bar_height = heights[i]
        meets_height = bar_height >= 500  # Minimum height of 500 USD/tonne for visibility
        
        if meets_percentage and meets_width and meets_height:
            x_center = x_positions[i] + widths[i] / 2
            y_center = heights[i] / 2
            
            # Use smaller font for smaller bars to reduce overlap
            if production_fraction < 0.08:  # Less than 8% of total
                fontsize = 7
            else:
                fontsize = 8
                
            ax.text(x_center, y_center, country, ha='center', va='center', 
                   fontsize=fontsize, fontweight='bold', color='white')
    
    # Format axes
    ax.set_xlabel('Cumulative Export Production (tonnes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Energy, transp and prod unit costs (USD/t)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Set x-axis to show cumulative production
    ax.set_xlim(0, total_production)
    
    # Add price line if provided
    if price_line is not None:
        ax.axhline(y=price_line, color='red', linestyle='--', linewidth=2, 
                  label=f'Market Price: ${price_line:,.0f}/tonne')
    
    return ax


def load_price_data():
    """
    Load current price data from Final_Price_and_Costs_RP.xlsx
    
    Returns:
    --------
    dict
        Mapping of mineral -> stage -> year -> price
    """
    file_path = Path("/home/karlac/critical_minerals_Africa/transport-outputs/data/Final_Price_and_Costs_RP.xlsx")
    
    if not file_path.exists():
        print(f"Warning: Price file not found at {file_path}")
        return {}
    
    # Load price data
    prices_df = pd.read_excel(file_path, sheet_name='Price_final')
    
    # Clean up the dataframe
    prices_df['reference_mineral'] = prices_df['reference_mineral'].ffill()
    
    # Build price dictionary: mineral -> stage -> year -> price
    price_dict = {}
    
    for mineral in prices_df['reference_mineral'].unique():
        if pd.isna(mineral):
            continue
        
        mineral_lower = mineral.lower()
        price_dict[mineral_lower] = {}
        
        mineral_data = prices_df[prices_df['reference_mineral'] == mineral]
        
        for _, row in mineral_data.iterrows():
            stage = row.get('processing_stage', row.get('stage', ''))
            if pd.isna(stage) or stage == '':
                continue
                
            stage_str = f"Stage {stage}" if isinstance(stage, (int, float)) else str(stage)
            
            if stage_str not in price_dict[mineral_lower]:
                price_dict[mineral_lower][stage_str] = {}
            
            # Extract year columns (2022, 2040, etc.)
            for col in mineral_data.columns:
                if str(col).isdigit() and len(str(col)) == 4:  # Year column
                    year = int(col)
                    price = row[col]
                    if not pd.isna(price) and price > 0:
                        price_dict[mineral_lower][stage_str][year] = price
    
    return price_dict


def get_price_for_mineral_stage_year(price_dict, mineral, stage, year):
    """
    Get price for a specific mineral, stage, and year
    
    Parameters:
    -----------
    price_dict : dict
        Price dictionary from load_price_data()
    mineral : str
        Mineral name
    stage : float
        Processing stage number
    year : int
        Year
    
    Returns:
    --------
    float or None
        Price value or None if not found
    """
    mineral_lower = mineral.lower()
    if mineral_lower not in price_dict:
        return None
    
    # Try different stage formats
    stage_keys = [f"Stage {stage}", f"Stage {int(stage)}", f"Stage {stage:.1f}"]
    
    for stage_key in stage_keys:
        if stage_key in price_dict[mineral_lower]:
            if year in price_dict[mineral_lower][stage_key]:
                return price_dict[mineral_lower][stage_key][year]
    
    return None


def create_supply_curves(df, output_dir):
    """
    Create supply curve plots for different scenarios and constraints.
    
    Parameters:
    -----------
    df : pd.DataFrame
        The main dataset from all_data.xlsx
    output_dir : str
        Directory to save the plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter for relevant data and mid demand scenarios only
    # Use mid_min for country constraints, mid_max for region constraints
    df_filtered = df[
        (df["processing_stage"] > 0) &  # Only processed stages
        (df["production_tonnes"] > 0) &  # Only countries with production
        (df["production_transport_energy_unit_cost_usd_per_tonne"] > 0) &  # Only with cost data
        (
            (df["scenario"] == "2022_baseline") |
            ((df["scenario"].str.contains("mid_min")) & (df["constraint"].str.contains("country"))) |
            ((df["scenario"].str.contains("mid_max")) & (df["constraint"].str.contains("region")))
        )
    ].copy()
    
    if len(df_filtered) == 0:
        print("Warning: No data available for supply curve generation")
        return []
    
    saved_paths = []
    
    # Load price data from Excel file
    price_dict = load_price_data()
    
    # Get unique countries across all data for consistent coloring
    all_countries = sorted(df_filtered["iso3"].unique())
    global_country_color_map = create_country_color_map(all_countries)
    
    # Group by mineral, constraint, and scenario
    for mineral in reference_minerals:
        mineral_data = df_filtered[df_filtered["reference_mineral"] == mineral]
        
        if len(mineral_data) == 0:
            print(f"No data available for {mineral}")
            continue
            
        for constraint in mineral_data["constraint"].unique():
            constraint_data = mineral_data[mineral_data["constraint"] == constraint]
            
            # Group scenarios by goal type for meaningful comparison
            scenarios_by_goal = {}
            for scenario in constraint_data["scenario"].unique():
                goal = get_goal_from_scenario(scenario)
                if goal not in scenarios_by_goal:
                    scenarios_by_goal[goal] = []
                scenarios_by_goal[goal].append(scenario)
            
            # Create plots for each meaningful scenario group
            for goal_type, scenarios in scenarios_by_goal.items():
                if goal_type == "unknown":
                    continue
                    
                # Filter for target processing stages based on goal
                goal_data = constraint_data[constraint_data["scenario"].isin(scenarios)]
                
                # Get years available (only 2022 and 2040 now)
                years = sorted(goal_data["year"].unique())
                
                if len(years) == 0:
                    continue
                
                # Create subplot for each year
                fig, axes = plt.subplots(len(years), 1, figsize=(14, 6 * len(years)), 
                                       sharex=False)
                if len(years) == 1:
                    axes = [axes]
                
                constraint_clean = constraint.replace("_", " ").title()
                # Special handling for BAU to keep it uppercase
                if goal_type == "bau":
                    goal_clean = "BAU"
                else:
                    goal_clean = goal_type.replace("_", " ").title()
                
                fig.suptitle(f"{mineral.title()} Supply Curves - {constraint_clean} - {goal_clean}", 
                           fontsize=16, fontweight='bold')
                
                for i, year in enumerate(years):
                    year_data = goal_data[goal_data["year"] == year]
                    
                    if len(year_data) == 0:
                        axes[i].text(0.5, 0.5, f'No data for {year}', 
                                   ha='center', va='center', transform=axes[i].transAxes)
                        continue
                    
                    # Group by country and aggregate if needed
                    country_data = year_data.groupby("iso3").agg({
                        "production_tonnes": "sum",
                        "production_transport_energy_unit_cost_usd_per_tonne": "mean"  # Average cost per country
                    }).reset_index()
                    
                    country_data.set_index("iso3", inplace=True)
                    
                    # Get price from the Excel file for this year/mineral/stage
                    # Get the most common processing stage for this data
                    stages = year_data["processing_stage"].value_counts()
                    if not stages.empty:
                        most_common_stage = stages.index[0]
                        excel_price = get_price_for_mineral_stage_year(price_dict, mineral, most_common_stage, year)
                    else:
                        excel_price = None
                    
                    # Use Excel price if available, otherwise fall back to data average
                    if excel_price is not None:
                        avg_price = excel_price
                    else:
                        price_data = year_data[year_data["price_usd_per_tonne"] > 0]
                        avg_price = price_data["price_usd_per_tonne"].mean() if not price_data.empty else None
                    
                    # Create supply curve
                    plot_supply_curve_bars(
                        country_data, 
                        "production_tonnes", 
                        "production_transport_energy_unit_cost_usd_per_tonne",
                        ax=axes[i], 
                        sort=True, 
                        color_map=global_country_color_map
                    )
                    
                    # Add processing type and scenario info to title
                    processing_types = year_data["processing_type"].unique()
                    processing_info = ", ".join(processing_types)
                    
                    # Get the specific scenario used
                    scenario_used = year_data["scenario"].iloc[0]
                    if "mid_min" in scenario_used:
                        demand_level = "Mid Demand (Min)"
                    elif "mid_max" in scenario_used:
                        demand_level = "Mid Demand (Max)"
                    else:
                        demand_level = "Baseline"
                    
                    axes[i].set_title(f"{year} - {processing_info} - {demand_level}", fontsize=14)
                    
                    # Add legend for all countries in the plot
                    legend_elements = []
                    for country in country_data.index:
                        if country in global_country_color_map:
                            from matplotlib.patches import Rectangle
                            legend_elements.append(
                                Rectangle((0, 0), 1, 1, facecolor=global_country_color_map[country], 
                                        label=country)
                            )
                    
                    # Price line removed per user request
                    
                    if legend_elements:
                        axes[i].legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), 
                                     loc='upper left', title='Countries')
                
                plt.tight_layout()
                
                # Save the figure
                filename = f"{mineral}_{constraint}_{goal_type}_supply_curves.png"
                filepath = os.path.join(output_dir, filename)
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                plt.close()
                
                saved_paths.append(filepath)
                print(f"✓ Saved supply curve: {filename}")
    
    return saved_paths


def create_supply_curves_by_scenario(df, output_dir):
    """
    Create supply curve plots with subplots for each scenario.
    
    This follows the new_bar_charts.py approach of showing different scenarios
    (baseline, BAU, early refining, precursor) as separate subplots within each figure.
    
    Parameters:
    -----------
    df : pd.DataFrame
        The main dataset from all_data.xlsx
    output_dir : str
        Directory to save the plots
    """
    # Create a subdirectory for scenario-based plots
    scenario_output_dir = os.path.join(output_dir, 'by_scenario')
    os.makedirs(scenario_output_dir, exist_ok=True)
    
    # Filter for relevant data and mid demand scenarios only
    df_filtered = df[
        (df["processing_stage"] > 0) &  # Only processed stages
        (df["production_tonnes"] > 0) &  # Only countries with production
        (df["production_transport_energy_unit_cost_usd_per_tonne"] > 0) &  # Only with cost data
        (
            (df["scenario"] == "2022_baseline") |
            ((df["scenario"].str.contains("mid_min")) & (df["constraint"].str.contains("country"))) |
            ((df["scenario"].str.contains("mid_max")) & (df["constraint"].str.contains("region")))
        )
    ].copy()
    
    if len(df_filtered) == 0:
        print("Warning: No data available for stage-specific supply curve generation")
        return []
    
    saved_paths = []
    
    # Load price data from Excel file
    price_dict = load_price_data()
    
    # Get unique countries across all data for consistent coloring
    all_countries = sorted(df_filtered["iso3"].unique())
    global_country_color_map = create_country_color_map(all_countries)
    
    # Define TARGET stage for each goal type (only the main target stage)
    goal_stage_mapping = {
        'baseline': {
            'nickel': 1.0,  # Beneficiation
            'copper': 1.0,
            'cobalt': 1.0,
            'graphite': 1.0,
            'manganese': 1.0,
            'lithium': 1.0
        },
        'bau': {
            'nickel': 1.0,  # Beneficiation
            'copper': 1.0,
            'cobalt': 1.0,
            'graphite': 1.0,
            'manganese': 1.0,
            'lithium': 1.0
        },
        'early_refining': {
            'nickel': 3.0,  # Target stage only
            'copper': 3.0,  # Target stage only
            'cobalt': 4.1,
            'graphite': 3.0,
            'manganese': 3.1,
            'lithium': 3.0
        },
        'precursor': {
            'nickel': 5.0,
            'copper': 5.0,  # Target stage only
            'cobalt': 5.0,
            'graphite': 4.0,
            'manganese': 4.1,
            'lithium': 4.2
        }
    }
    
    # Group by mineral and constraint
    for mineral in reference_minerals:
        mineral_data = df_filtered[df_filtered["reference_mineral"] == mineral]
        
        if len(mineral_data) == 0:
            print(f"No data available for {mineral}")
            continue
            
        for constraint in mineral_data["constraint"].unique():
            constraint_data = mineral_data[mineral_data["constraint"] == constraint]
            
            # Get all scenarios for this constraint
            scenarios_by_goal = {}
            for scenario in constraint_data["scenario"].unique():
                goal = get_goal_from_scenario(scenario)
                if goal not in scenarios_by_goal:
                    scenarios_by_goal[goal] = []
                scenarios_by_goal[goal].append(scenario)
            
            # Determine which scenarios to plot
            scenarios_to_plot = []
            
            # For regional and country_constrained cases, use baseline from country_unconstrained
            if ('region' in constraint or constraint == 'country_constrained') and 'baseline' not in scenarios_by_goal:
                # Get baseline data from country_unconstrained
                baseline_data = df_filtered[
                    (df_filtered["reference_mineral"] == mineral) &
                    (df_filtered["constraint"] == "country_unconstrained") &
                    (df_filtered["scenario"] == "2022_baseline")
                ]
                if not baseline_data.empty:
                    scenarios_to_plot.append(('baseline', ["2022_baseline"], 2022))
            elif 'baseline' in scenarios_by_goal:
                scenarios_to_plot.append(('baseline', scenarios_by_goal['baseline'], 2022))
                
            if 'bau' in scenarios_by_goal:
                scenarios_to_plot.append(('bau', scenarios_by_goal['bau'], 2040))
            if 'early_refining' in scenarios_by_goal:
                scenarios_to_plot.append(('early_refining', scenarios_by_goal['early_refining'], 2040))
            if 'precursor' in scenarios_by_goal:
                scenarios_to_plot.append(('precursor', scenarios_by_goal['precursor'], 2040))
            
            if len(scenarios_to_plot) == 0:
                continue
            
            # Create figure with subplots for each scenario
            n_scenarios = len(scenarios_to_plot)
            fig, axes = plt.subplots(n_scenarios, 1, figsize=(14, 6 * n_scenarios), sharex=False)
            if n_scenarios == 1:
                axes = [axes]
            
            constraint_clean = constraint.replace("_", " ").title()
            
            fig.suptitle(f"{mineral.title()} Supply Curves by Scenario - {constraint_clean}", 
                       fontsize=16, fontweight='bold')
            
            # Plot each scenario
            for i, (goal_type, goal_scenarios, year) in enumerate(scenarios_to_plot):
                # Get the target stage for this goal and mineral
                if goal_type in goal_stage_mapping and mineral in goal_stage_mapping[goal_type]:
                    target_stage = goal_stage_mapping[goal_type][mineral]
                else:
                    axes[i].text(0.5, 0.5, f'No stage mapping for {goal_type}', 
                               ha='center', va='center', transform=axes[i].transAxes)
                    continue
                
                # Filter for this scenario and stage
                # Special handling for regional and country_constrained baseline - get from country_unconstrained
                if ('region' in constraint or constraint == 'country_constrained') and goal_type == 'baseline':
                    scenario_data = df_filtered[
                        (df_filtered["reference_mineral"] == mineral) &
                        (df_filtered["constraint"] == "country_unconstrained") &
                        (df_filtered["scenario"].isin(goal_scenarios)) &
                        (df_filtered["processing_stage"] == target_stage)
                    ]
                else:
                    scenario_data = constraint_data[
                        (constraint_data["scenario"].isin(goal_scenarios)) &
                        (constraint_data["processing_stage"] == target_stage)
                    ]
                
                if len(scenario_data) == 0:
                    axes[i].text(0.5, 0.5, f'No data for {goal_type} - Stage {target_stage}', 
                               ha='center', va='center', transform=axes[i].transAxes)
                    continue
                
                # Group by country
                country_data = scenario_data.groupby("iso3").agg({
                    "production_tonnes": "sum",
                    "production_transport_energy_unit_cost_usd_per_tonne": "mean"
                }).reset_index()
                
                country_data.set_index("iso3", inplace=True)
                
                # Get price for this specific stage
                excel_price = get_price_for_mineral_stage_year(price_dict, mineral, target_stage, year)
                
                # Create supply curve
                plot_supply_curve_bars(
                    country_data, 
                    "production_tonnes", 
                    "production_transport_energy_unit_cost_usd_per_tonne",
                    ax=axes[i], 
                    sort=True, 
                    color_map=global_country_color_map
                )
                
                # Get processing type for this stage
                processing_type = scenario_data["processing_type"].iloc[0] if not scenario_data.empty else ""
                
                # Format scenario title
                if goal_type == 'baseline':
                    scenario_title = f"{year} Baseline"
                elif goal_type == 'bau':
                    scenario_title = f"{year} BAU"
                else:
                    scenario_title = f"{year} {goal_type.replace('_', ' ').title()}"
                
                # Add scenario-specific title with stage info
                stage_str = f"Stage {int(target_stage)}" if target_stage % 1 == 0 else f"Stage {target_stage:.1f}"
                axes[i].set_title(f"{scenario_title} - {stage_str} ({processing_type})", fontsize=14)
                
                # Add legend for all countries
                legend_elements = []
                for country in country_data.index:
                    if country in global_country_color_map:
                        from matplotlib.patches import Rectangle
                        legend_elements.append(
                            Rectangle((0, 0), 1, 1, facecolor=global_country_color_map[country], 
                                    label=country)
                        )
                
                # Price line removed per user request
                
                if legend_elements:
                    axes[i].legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), 
                                 loc='upper left', title='Countries')
            
            plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space at top for suptitle
            
            # Save the figure
            filename = f"{mineral}_{constraint}_supply_curves_by_scenario.png"
            filepath = os.path.join(scenario_output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            saved_paths.append(filepath)
            print(f"✓ Saved scenario-based supply curve: {filename}")
    
    return saved_paths


def create_supply_curve_scenario_subplots(df, output_dir):
    """
    Create supply curve plots with subplots comparing BAU, Early Refining, and Precursor scenarios.
    
    This creates one figure per mineral/constraint combination with 3 horizontal subplots
    showing the different scenarios side by side for easy comparison.
    
    Parameters:
    -----------
    df : pd.DataFrame
        The main dataset from all_data.xlsx
    output_dir : str
        Directory to save the plots
    """
    # Create a subdirectory for scenario comparison plots
    scenario_output_dir = os.path.join(output_dir, 'scenario_comparison')
    os.makedirs(scenario_output_dir, exist_ok=True)
    
    # Filter for relevant data using same approach as emissions plots
    df_filtered = df[
        (df["processing_stage"] > 0) &  # Only processed stages
        (df["production_tonnes"] > 0) &  # Only countries with production
        (df["production_transport_energy_unit_cost_usd_per_tonne"] > 0) &  # Only with cost data
        (df["scenario"].str.contains("2040")) &  # Only 2040 scenarios
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ].copy()
    
    if len(df_filtered) == 0:
        print("Warning: No data available for supply curve scenario comparison")
        return []
    
    saved_paths = []
    
    # Define scenario mapping with descriptive names showing all stages are aggregated
    scenario_mapping = {
        'bau_2040': 'Business as Usual',
        'early_refining_2040': 'Early Refining', 
        'precursor_2040': 'Precursor Product'
    }
    
    # Get unique countries across all data for consistent coloring
    all_countries = sorted(df_filtered["iso3"].unique())
    global_country_color_map = create_country_color_map(all_countries)
    
    # Group by mineral and constraint
    for mineral in reference_minerals:
        mineral_data = df_filtered[df_filtered["reference_mineral"] == mineral]
        
        if len(mineral_data) == 0:
            print(f"No data available for {mineral} supply curve scenarios")
            continue
            
        for constraint in mineral_data["constraint"].unique():
            constraint_data = mineral_data[mineral_data["constraint"] == constraint]
            
            # Get scenarios present in this constraint group
            available_scenarios = []
            scenario_data = {}
            
            for scenario_key, scenario_name in scenario_mapping.items():
                scenario_data_filtered = constraint_data[constraint_data["scenario"].str.contains(scenario_key)]
                if not scenario_data_filtered.empty:
                    available_scenarios.append((scenario_key, scenario_name))
                    scenario_data[scenario_key] = scenario_data_filtered
            
            if len(available_scenarios) < 1:  # Need at least 1 scenario to plot
                continue
            
            # Create subplot figure with horizontal layout (1 row, n columns) with shared y-axis
            fig, axes = plt.subplots(1, len(available_scenarios), figsize=(6 * len(available_scenarios), 8), sharex=False, sharey=True)
            if len(available_scenarios) == 1:
                axes = [axes]
            
            constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
            constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
            figure_title = f"{mineral.title()} Supply Curve Scenario Comparison — {constraint_type} {constraint_status}"
            
            # First pass: find maximum values across all scenarios for consistent scaling
            max_production = 0
            max_cost = 0
            
            for scenario_key, scenario_name in available_scenarios:
                scenario_group = scenario_data[scenario_key]
                
                # Aggregate all stages for this scenario
                country_data = scenario_group.groupby("iso3").agg({
                    "production_tonnes": "sum",
                    "production_transport_energy_unit_cost_usd_per_tonne": "mean"
                }).reset_index()
                
                if not country_data.empty:
                    max_production = max(max_production, country_data["production_tonnes"].sum())
                    max_cost = max(max_cost, country_data["production_transport_energy_unit_cost_usd_per_tonne"].max())
            
            # Add padding to max values for better visualization
            max_production = max_production * 1.1
            max_cost = max_cost * 1.1
            
            # Plot each scenario
            for i, (scenario_key, scenario_name) in enumerate(available_scenarios):
                ax = axes[i]
                scenario_group = scenario_data[scenario_key]
                
                # Group by country and aggregate all stages
                country_data = scenario_group.groupby("iso3").agg({
                    "production_tonnes": "sum",
                    "production_transport_energy_unit_cost_usd_per_tonne": "mean"
                }).reset_index()
                
                country_data.set_index("iso3", inplace=True)
                
                if country_data.empty:
                    ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                           transform=ax.transAxes, fontsize=14)
                    ax.set_title(scenario_name, fontsize=14, fontweight='bold')
                    continue
                
                # Create supply curve with higher threshold to reduce label overlap
                plot_supply_curve_bars(
                    country_data, 
                    "production_tonnes", 
                    "production_transport_energy_unit_cost_usd_per_tonne",
                    ax=ax, 
                    sort=True, 
                    color_map=global_country_color_map,
                    min_label_threshold=0.05  # Increase from 3% to 5% to reduce overlaps
                )
                
                # Set consistent scales
                ax.set_xlim(0, max_production)
                ax.set_ylim(0, max_cost)
                
                # Get unique stages in this scenario data for subtitle
                stages_in_scenario = sorted(scenario_group['processing_stage'].unique())
                stages_str = ', '.join([f'{int(s)}' if s % 1 == 0 else f'{s:.1f}' for s in stages_in_scenario])
                
                # Format subplot with stage information - use two lines for better readability
                ax.set_title(f'{scenario_name}\n(All Stages: {stages_str})', fontsize=12, fontweight='bold', pad=10, linespacing=1.5)
                # Format x-axis with better number formatting
                ax.set_xlabel('Cumulative Export Production (tonnes)', fontsize=11)
                
                # Format x-axis tick labels to avoid congestion
                from matplotlib.ticker import FuncFormatter
                def format_large_numbers(x, pos):
                    if x >= 1e6:
                        return f'{x/1e6:.1f}M'
                    elif x >= 1e3:
                        return f'{x/1e3:.0f}k'
                    else:
                        return f'{x:.0f}'
                ax.xaxis.set_major_formatter(FuncFormatter(format_large_numbers))
                if i == 0:  # Only first subplot gets y-label
                    ax.set_ylabel('Energy, transp and prod unit costs (USD/t)', fontsize=12, fontweight='bold')
                
                # Add legend only to the last subplot
                if i == len(available_scenarios) - 1:
                    # Create country legend
                    countries = sorted(country_data.index)
                    legend_elements = []
                    for country in countries:
                        legend_elements.append(
                            plt.Rectangle((0, 0), 1, 1, facecolor=global_country_color_map[country], 
                                        label=country)
                        )
                    
                    if legend_elements:
                        ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), 
                                loc='upper left', title='Countries', fontsize=10, title_fontsize=11)
            
            # Add main title with better positioning
            fig.suptitle(figure_title, fontsize=16, fontweight='bold', y=0.95)
            
            # Adjust layout to provide space for legend and better title positioning
            plt.tight_layout(rect=[0, 0.02, 0.85, 0.93])
            
            # Save figure
            filename = f"{mineral}_{constraint}_scenario_comparison_supply_curves.png"
            filepath = os.path.join(scenario_output_dir, filename)
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_paths.append(filepath)
            
            print(f"✓ Saved supply curve scenario comparison: {filename}")
    
    return saved_paths


def get_valid_cost_stages_for_supply_curves(df_country_mineral, scenario_config):
    """
    Determine which stages should contribute costs using production chain validation.

    Identical to the function in plot_competitiveness_summary.py - validates production chain
    to include intermediate stages with costs but zero production (consumed internally).

    Parameters:
    -----------
    df_country_mineral : pd.DataFrame
        Data for single country-mineral-scenario combination
    scenario_config : dict
        Scenario configuration with included_types

    Returns:
    --------
    list of float
        Processing stage numbers to include in cumulative cost calculation
    """
    # Find all stages with actual production
    production_stages = df_country_mineral[
        df_country_mineral['production_tonnes'] > 0
    ]['processing_stage'].unique()

    if len(production_stages) == 0:
        return []

    max_production_stage = max(production_stages)

    # Build list of valid cost stages (by stage number, not type)
    valid_stages = []

    # Filter to only included processing types
    included_data = df_country_mineral[
        df_country_mineral['processing_type'].isin(scenario_config['included_types'])
    ]

    for _, row in included_data.iterrows():
        stage_num = row['processing_stage']
        has_production = row['production_tonnes'] > 0
        has_cost = row['production_transport_energy_unit_cost_usd_per_tonne'] > 0

        if not has_cost:
            continue

        # Include if:
        # A) Stage has production, OR
        # B) Stage is intermediate (< max production stage) with costs
        if has_production or (stage_num < max_production_stage):
            valid_stages.append(stage_num)

    return valid_stages


def create_supply_curve_cumulative_costs(df, output_dir):
    """
    Create supply curve plots with cumulative costs through the processing chain.

    This creates one figure per mineral/constraint combination with 3 horizontal subplots:
    - BAU: Beneficiation stage only
    - Early Refining: Cumulative costs up to Early refining stages
    - Precursor: Cumulative costs through all stages

    Uses production chain validation to correctly handle intermediate stages.

    Parameters:
    -----------
    df : pd.DataFrame
        The main dataset from all_data.xlsx
    output_dir : str
        Directory to save the plots
    """
    # Use the output directory directly (caller should provide cumulative_costs path if needed)
    cumulative_output_dir = output_dir
    os.makedirs(cumulative_output_dir, exist_ok=True)

    # Filter for relevant data - relaxed to include intermediate stages with zero production
    df_filtered = df[
        (df["processing_stage"] > 0) &  # Only processed stages
        (df["production_transport_energy_unit_cost_usd_per_tonne"] > 0) &  # Only with cost data
        (df["scenario"].str.contains("2040")) &  # Only 2040 scenarios
        (
            ((df["constraint"].str.contains("country")) & (df["scenario"].str.contains("mid_min"))) |
            ((df["constraint"].str.contains("region")) & (df["scenario"].str.contains("mid_max")))
        )
    ].copy()
    
    if len(df_filtered) == 0:
        print("Warning: No data available for cumulative cost supply curves")
        return []
    
    saved_paths = []
    
    # Define scenario mapping and processing type inclusion
    scenario_config = {
        'bau_2040': {
            'title': 'Business as Usual\n(Beneficiation stage)',
            'included_types': ['Beneficiation'],
            'target_type': 'Beneficiation'
        },
        'early_refining_2040': {
            'title': 'Early Refining\n(Up to Early Refining stage)',
            'included_types': ['Beneficiation', 'Early refining'],
            'target_type': 'Early refining'
        },
        'precursor_2040': {
            'title': 'Precursor Product\n(All stages)',
            'included_types': ['Beneficiation', 'Early refining', 'Precursor related product'],
            'target_type': 'Precursor related product'
        }
    }
    
    # Get unique countries for consistent coloring
    all_countries = sorted(df_filtered["iso3"].unique())
    global_country_color_map = create_country_color_map(all_countries)
    
    # Group by mineral and constraint
    for mineral in reference_minerals:
        mineral_data = df_filtered[df_filtered["reference_mineral"] == mineral]
        
        if len(mineral_data) == 0:
            print(f"No data available for {mineral} cumulative cost curves")
            continue
            
        for constraint in mineral_data["constraint"].unique():
            constraint_data = mineral_data[mineral_data["constraint"] == constraint]
            
            # Check which scenarios are available
            available_scenarios = []
            for scenario_key in scenario_config.keys():
                if not constraint_data[constraint_data["scenario"].str.contains(scenario_key)].empty:
                    available_scenarios.append(scenario_key)
            
            if len(available_scenarios) < 1:
                continue
            
            # Create subplot figure (1 row, 3 columns) with shared y-axes for easy comparison
            fig, axes = plt.subplots(1, len(available_scenarios), 
                                    figsize=(6 * len(available_scenarios), 8), 
                                    sharex=False, sharey=True)
            if len(available_scenarios) == 1:
                axes = [axes]
            
            constraint_type = "National Focus" if "country" in constraint else "Regional Integration"
            constraint_status = "Environmentally Unconstrained" if "unconstrained" in constraint else "Environmentally Constrained"
            figure_title = f"{mineral.title()} - {constraint_type} {constraint_status}"
            
            # Plot each scenario
            for i, scenario_key in enumerate(available_scenarios):
                ax = axes[i]
                config = scenario_config[scenario_key]
                
                # Get scenario data
                scenario_data = constraint_data[constraint_data["scenario"].str.contains(scenario_key)]
                
                # Calculate cumulative costs for each country
                country_cumulative_data = []

                for country in scenario_data["iso3"].unique():
                    country_scenario_data = scenario_data[scenario_data["iso3"] == country]

                    # Get production from the target processing type (use production_tonnes_for_costs)
                    target_production = country_scenario_data[
                        country_scenario_data["processing_type"] == config['target_type']
                    ]["production_tonnes_for_costs"].sum()

                    # Skip if no production at target stage
                    if target_production == 0:
                        continue

                    # Get valid stages using production chain validation
                    valid_stages = get_valid_cost_stages_for_supply_curves(country_scenario_data, config)

                    if not valid_stages:
                        continue

                    # Calculate cumulative costs from valid stages only
                    cumulative_unit_cost = 0
                    for stage_num in valid_stages:
                        stage_data = country_scenario_data[country_scenario_data["processing_stage"] == stage_num]
                        if not stage_data.empty:
                            stage_cost = stage_data["production_transport_energy_unit_cost_usd_per_tonne"].iloc[0]
                            cumulative_unit_cost += stage_cost
                    
                    country_cumulative_data.append({
                        'iso3': country,
                        'production_tonnes_for_costs': target_production,
                        'cumulative_unit_cost': cumulative_unit_cost
                    })
                
                if country_cumulative_data:
                    # Create DataFrame for plotting
                    plot_df = pd.DataFrame(country_cumulative_data)
                    plot_df.set_index('iso3', inplace=True)
                    
                    # Create supply curve
                    plot_supply_curve_bars(
                        plot_df,
                        "production_tonnes_for_costs",
                        "cumulative_unit_cost",
                        ax=ax,
                        sort=True,
                        color_map=global_country_color_map,
                        min_label_threshold=0.05
                    )
                    
                    # Set subplot title with two lines for better readability
                    ax.set_title(config['title'], fontsize=12, fontweight='bold', pad=10, linespacing=1.5)
                    
                    # Format x-axis with better number formatting
                    ax.set_xlabel('Cumulative Export Production (tonnes)', fontsize=11)
                    
                    # Format x-axis tick labels to avoid congestion
                    from matplotlib.ticker import FuncFormatter
                    def format_large_numbers(x, pos):
                        if x >= 1e6:
                            return f'{x/1e6:.1f}M'
                        elif x >= 1e3:
                            return f'{x/1e3:.0f}k'
                        else:
                            return f'{x:.0f}'
                    ax.xaxis.set_major_formatter(FuncFormatter(format_large_numbers))
                    
                    if i == 0:  # Only first subplot gets y-label
                        ax.set_ylabel('Energy, transp and prod unit costs (USD/t)', fontsize=12, fontweight='bold')
                    
                    # Let y-axis scale naturally to show all data
                        
                else:
                    # Handle empty subplot with clear message
                    ax.text(0.5, 0.5, 'No data available\nfor this scenario', ha='center', va='center',
                           transform=ax.transAxes, fontsize=14, color='gray')
                    ax.set_title(config['title'], fontsize=12, fontweight='bold', pad=10, linespacing=1.5)
                    ax.set_xlabel('Cumulative Export Production (tonnes)', fontsize=11)
                    if i == 0:
                        ax.set_ylabel('Energy, transp and prod unit costs (USD/t)', fontsize=12, fontweight='bold')
                    # Empty subplot - no y-axis limit needed
                    ax.set_xticks([])
                    ax.set_yticks([])
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['bottom'].set_visible(False)
                    ax.spines['left'].set_visible(False)
                
                # Add legend only to the last subplot
                if i == len(available_scenarios) - 1:
                    if country_cumulative_data:
                        countries = sorted([d['iso3'] for d in country_cumulative_data])
                        legend_elements = []
                        for country in countries:
                            if country in global_country_color_map:
                                legend_elements.append(
                                    plt.Rectangle((0, 0), 1, 1, 
                                                facecolor=global_country_color_map[country],
                                                label=country)
                                )
                        
                        if legend_elements:
                            ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1),
                                    loc='upper left', title='Countries', fontsize=10, title_fontsize=11)
            
            # Add main title
            fig.suptitle(figure_title, fontsize=16, fontweight='bold', y=0.95)
            
            # Adjust layout
            plt.tight_layout(rect=[0, 0.02, 0.85, 0.93])
            
            # Save figure
            filename = f"{mineral}_{constraint}_cumulative_cost_supply_curves.png"
            filepath = os.path.join(cumulative_output_dir, filename)
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_paths.append(filepath)
            
            print(f"✓ Saved cumulative cost supply curve: {filename}")
    
    return saved_paths


def main():
    """Main function to generate all supply curves"""
    # Load configuration
    import json
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"Loading data from: {data_path}")
    
    df = pd.read_excel(data_path)
    print(f"Loaded {len(df)} rows of data")
    
    # Set up output directory
    output_dir = os.path.join(config['paths']['figures'], 'supply_curves')
    print(f"Output directory: {output_dir}")
    
    # Generate supply curves
    print("\n=== Generating combined supply curves ===")
    saved_paths = create_supply_curves(df, output_dir)
    
    print(f"\n=== Generating scenario-based supply curves ===")
    scenario_paths = create_supply_curves_by_scenario(df, output_dir)
    
    total_paths = saved_paths + scenario_paths
    
    print(f"\n✅ Supply curve generation complete!")
    print(f"Generated {len(saved_paths)} combined supply curve plots")
    print(f"Generated {len(scenario_paths)} scenario-based supply curve plots")
    print(f"Total: {len(total_paths)} plots")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()