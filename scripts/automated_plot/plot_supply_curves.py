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
    
    # Add country labels on bars (if not too small)
    for i, (country, row) in enumerate(df_clean.iterrows()):
        if row[tons_column] / total_production >= min_label_threshold:
            x_center = x_positions[i] + widths[i] / 2
            y_center = heights[i] / 2
            ax.text(x_center, y_center, country, ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='white')
    
    # Format axes
    ax.set_xlabel('Cumulative Production (tonnes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Unit Cost (USD/tonne)', fontsize=12, fontweight='bold')
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
                        color_map=global_country_color_map,
                        price_line=avg_price
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
                    
                    # If there's a price line, add it to legend
                    if avg_price is not None:
                        from matplotlib.lines import Line2D
                        legend_elements.append(
                            Line2D([0], [0], color='red', linestyle='--', linewidth=2,
                                   label=f'Market Price: ${avg_price:,.0f}/tonne')
                        )
                    
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
                    color_map=global_country_color_map,
                    price_line=excel_price
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
                
                # Add price line to legend if available
                if excel_price is not None:
                    from matplotlib.lines import Line2D
                    legend_elements.append(
                        Line2D([0], [0], color='red', linestyle='--', linewidth=2,
                               label=f'Market Price: ${excel_price:,.0f}/tonne')
                    )
                
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