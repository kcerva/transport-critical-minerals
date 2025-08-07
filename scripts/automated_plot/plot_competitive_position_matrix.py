#!/usr/bin/env python3
"""
Stage-Stratified Competitive Position Matrix Visualization

This script creates a comprehensive matrix visualization showing the competitive position
of countries across different processing stages, scenarios, and constraints for critical minerals.

The visualization displays:
- X-axis: Countries sorted by total production volume
- Y-axis: Nested hierarchy of Stage → Scenario → Constraint
- Color: Competitiveness ratio (Unit Cost / Stage-specific Price)
- Size: Production volume circles
- Markers: Stars for goal stages, circles for intermediate stages
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.collections import PatchCollection
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap, Normalize
from pathlib import Path

from plot_config import (
    reference_minerals,
    reference_mineral_colors,
    reference_mineral_colormap,
    get_goal_from_scenario,
    mineral_processing_stages,
    get_target_stage_for_goal,
    get_stages_for_processing_type
)

# Define competitiveness color map (Green to Yellow to Red)
colors = ['#2E7D32', '#66BB6A', '#A5D6A7', '#FFF59D', '#FFD54F', '#FF8A65', '#E53935']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('competitiveness', colors, N=n_bins)


def load_price_data():
    """
    Load current price data from Final_Price_and_Costs_RP.xlsx
    Returns dict of mineral -> stage -> year -> price
    """
    file_path = Path("/home/karlac/critical_minerals_Africa/transport-outputs/data/Final_Price_and_Costs_RP.xlsx")
    
    if not file_path.exists():
        print(f"Warning: Price file not found at {file_path}")
        return {}
    
    # Load price data
    prices_df = pd.read_excel(file_path, sheet_name='Price_final')
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
                
            stage_float = float(stage) if isinstance(stage, (int, float, str)) and str(stage).replace('.', '').isdigit() else None
            if stage_float is None:
                continue
                
            if stage_float not in price_dict[mineral_lower]:
                price_dict[mineral_lower][stage_float] = {}
            
            # Extract year columns (2022, 2040, etc.)
            for col in mineral_data.columns:
                if str(col).isdigit() and len(str(col)) == 4:
                    year = int(col)
                    price = row[col]
                    if not pd.isna(price) and price > 0:
                        price_dict[mineral_lower][stage_float][year] = price
    
    return price_dict


def get_price_for_mineral_stage_year(price_dict, mineral, stage, year):
    """Get price for specific mineral, stage, and year"""
    mineral_lower = mineral.lower()
    if mineral_lower not in price_dict:
        return None
    
    if stage in price_dict[mineral_lower]:
        if year in price_dict[mineral_lower][stage]:
            return price_dict[mineral_lower][stage][year]
    
    return None


def create_competitive_position_matrix(df, mineral, output_dir):
    """
    Create the competitive position matrix for a specific mineral
    Focuses on comparing country_unconstrained vs region_unconstrained scenarios
    
    Parameters:
    -----------
    df : pd.DataFrame
        The main dataset from all_data.xlsx
    mineral : str
        Mineral name
    output_dir : str
        Directory to save the plots
    """
    # Filter data for this mineral
    mineral_data = df[
        (df["reference_mineral"] == mineral) &
        (df["processing_stage"] > 0) &
        (df["production_tonnes"] > 0)
    ].copy()
    
    if len(mineral_data) == 0:
        print(f"No data available for {mineral}")
        return
    
    # Load price data
    price_dict = load_price_data()
    
    # Get unique countries sorted by total production
    country_production = mineral_data.groupby("iso3")["production_tonnes"].sum().sort_values(ascending=False)
    countries = country_production.index.tolist()
    
    # Define scenarios and constraints - SIMPLIFIED to focus on key comparison
    scenarios = ['2022_baseline', 'bau_2040', 'early_refining_2040', 'precursor_2040']
    scenario_labels = ['Baseline 2022', 'BAU 2040', 'Early Refining 2040', 'Precursor 2040']
    # Focus only on the two key constraints for comparison
    constraints = ['country_unconstrained', 'region_unconstrained']
    constraint_labels = ['Country Unconstrained', 'Region Unconstrained']
    
    # Get all stages for this mineral
    stages = sorted(mineral_data["processing_stage"].unique())
    
    # Determine goal stages for each scenario
    goal_stages = {}
    if mineral in mineral_processing_stages:
        goal_stages['bau'] = mineral_processing_stages[mineral]["target_stages"].get("Beneficiation", 1.0)
        goal_stages['early_refining'] = mineral_processing_stages[mineral]["target_stages"].get("Early refining", 3.0)
        goal_stages['precursor'] = mineral_processing_stages[mineral]["target_stages"].get("Precursor related product", 5.0)
    
    # Create figure - reduced height due to fewer constraints
    fig_width = max(14, len(countries) * 0.6)
    fig_height = max(8, len(stages) * len(scenarios) * len(constraints) * 0.4)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Plot data
    y_position = 0
    y_labels = []
    y_positions = []
    
    # Maximum circle size
    max_production = mineral_data["production_tonnes"].max()
    max_circle_size = 400  # Slightly smaller for cleaner look
    
    for stage_idx, stage in enumerate(stages):
        stage_data = mineral_data[mineral_data["processing_stage"] == stage]
        
        # Add stage separator with better styling
        if stage_idx > 0:
            ax.axhline(y=y_position - 0.5, color='navy', linewidth=1.5, alpha=0.4)
        
        stage_label = f"Stage {int(stage)}" if stage % 1 == 0 else f"Stage {stage:.1f}"
        processing_types = stage_data["processing_type"].unique()
        if len(processing_types) > 0:
            stage_label += f" ({processing_types[0]})"
        
        for scenario_idx, scenario in enumerate(scenarios):
            # Check if this scenario exists in the data
            scenario_patterns = {
                '2022_baseline': '2022_baseline',
                'bau_2040': 'bau_2040.*mid_',
                'early_refining_2040': 'early_refining_2040.*mid_',
                'precursor_2040': 'precursor_2040.*mid_'
            }
            
            scenario_data = stage_data[stage_data["scenario"].str.contains(scenario_patterns[scenario], regex=True)]
            
            for constraint_idx, constraint in enumerate(constraints):
                # For baseline, only use country_unconstrained
                if scenario == '2022_baseline' and constraint != 'country_unconstrained':
                    continue
                
                # Simplified data filtering
                if constraint == 'country_unconstrained':
                    data = scenario_data[
                        (scenario_data["constraint"] == constraint) &
                        (scenario_data["scenario"].str.contains("min"))
                    ]
                else:  # region_unconstrained
                    data = scenario_data[
                        (scenario_data["constraint"] == constraint) &
                        (scenario_data["scenario"].str.contains("max"))
                    ]
                
                # Create cleaner y-labels
                if constraint_idx == 0:
                    if scenario_idx == 0:
                        y_label = f"{stage_label}\n{scenario_labels[scenario_idx]}"
                    else:
                        y_label = f"{scenario_labels[scenario_idx]}"
                else:
                    y_label = ""
                
                # Add constraint label - simplified
                if scenario == '2022_baseline':
                    y_label += f"\n{constraint_labels[0]}"
                else:
                    y_label += f"\n{constraint_labels[constraint_idx]}"
                
                y_labels.append(y_label)
                y_positions.append(y_position)
                
                # Plot circles for each country
                for country_idx, country in enumerate(countries):
                    country_data = data[data["iso3"] == country]
                    
                    if len(country_data) > 0:
                        # Calculate metrics
                        production = country_data["production_tonnes"].sum()
                        unit_cost = country_data["production_transport_energy_unit_cost_usd_per_tonne"].mean()
                        
                        # Get price for this stage and year
                        year = 2022 if scenario == '2022_baseline' else 2040
                        price = get_price_for_mineral_stage_year(price_dict, mineral, stage, year)
                        
                        if price and price > 0 and unit_cost > 0:
                            competitiveness_ratio = unit_cost / price
                            
                            # Determine circle size
                            circle_size = np.sqrt(production / max_production) * max_circle_size
                            
                            # Determine if this is a goal stage
                            is_goal = False
                            if scenario == 'bau_2040' and stage == goal_stages.get('bau', -1):
                                is_goal = True
                            elif scenario == 'early_refining_2040' and stage == goal_stages.get('early_refining', -1):
                                is_goal = True
                            elif scenario == 'precursor_2040' and stage == goal_stages.get('precursor', -1):
                                is_goal = True
                            
                            # Create shape
                            if is_goal:
                                # Star for goal stages
                                marker = RegularPolygon((country_idx, y_position), 5, 
                                                       radius=circle_size/100, 
                                                       orientation=np.pi/2)
                                marker.set_edgecolor('black')
                                marker.set_linewidth(2)
                            else:
                                # Circle for other stages
                                marker = Circle((country_idx, y_position), 
                                              radius=circle_size/200)
                                marker.set_edgecolor('gray')
                                marker.set_linewidth(1)
                            
                            # Set color based on competitiveness
                            color_value = np.clip(competitiveness_ratio, 0, 2) / 2  # Normalize to 0-1
                            marker.set_facecolor(cmap(1 - color_value))  # Invert so green is good
                            ax.add_patch(marker)
                
                y_position += 1
    
    # Set axis properties
    ax.set_xlim(-0.8, len(countries) - 0.2)
    ax.set_ylim(-0.5, y_position)
    ax.set_xticks(range(len(countries)))
    ax.set_xticklabels(countries, rotation=45, ha='right', fontsize=10)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=9)
    
    # Add cleaner grid
    ax.grid(True, axis='x', alpha=0.2, linestyle='-', color='gray')
    ax.set_axisbelow(True)
    
    # Improved title with clearer explanation
    ax.set_title(f"{mineral.title()} - Competitive Position Matrix\n" +
                "Comparison: Country vs Region Unconstrained Scenarios\n" +
                "Size: Production Volume | Color: Cost/Price Ratio (Green=Competitive) | *=Goal Stage",
                fontsize=13, fontweight='bold', pad=20)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(vmin=0, vmax=2))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.02)
    cbar.set_label('Unit Cost / Market Price Ratio', fontsize=10)
    cbar.set_ticks([0, 0.5, 1, 1.5, 2])
    cbar.set_ticklabels(['0', '0.5', '1.0', '1.5', '≥2.0'])
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                   markersize=10, label='Production (size ∝ volume)'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='gray', 
                   markersize=15, label='Goal Stage', markeredgecolor='black', markeredgewidth=2)
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    
    # Save figure
    filename = f"competitive_matrix_{mineral}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved competitive position matrix: {filename}")
    
    # Create summary statistics
    create_summary_statistics(mineral_data, mineral, price_dict, output_dir)


def create_summary_statistics(df, mineral, price_dict, output_dir):
    """Create a summary statistics panel comparing country_unconstrained vs region_unconstrained scenarios"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"{mineral.title()} - Scenario Comparison Summary\n" +
                "Country Unconstrained vs Region Unconstrained", fontsize=16, fontweight='bold')
    
    # Filter data for the two key scenarios (2040 data)
    country_data = df[
        (df["constraint"] == "country_unconstrained") &
        (df["scenario"].str.contains("2040.*mid_min", regex=True))
    ]
    region_data = df[
        (df["constraint"] == "region_unconstrained") &
        (df["scenario"].str.contains("2040.*mid_max", regex=True))
    ]
    
    # 1. Production comparison by stage
    ax = axes[0, 0]
    country_production = country_data.groupby("processing_stage")["production_tonnes"].sum().sort_index()
    region_production = region_data.groupby("processing_stage")["production_tonnes"].sum().sort_index()
    
    # Align stages
    all_stages = sorted(set(country_production.index) | set(region_production.index))
    country_aligned = [country_production.get(stage, 0) for stage in all_stages]
    region_aligned = [region_production.get(stage, 0) for stage in all_stages]
    
    x = np.arange(len(all_stages))
    width = 0.35
    
    ax.bar(x - width/2, country_aligned, width, label='Country Unconstrained', 
           color='steelblue', alpha=0.8)
    ax.bar(x + width/2, region_aligned, width, label='Region Unconstrained', 
           color='darkorange', alpha=0.8)
    
    ax.set_title("Production by Stage (2040 Scenarios)")
    ax.set_xlabel("Processing Stage")
    ax.set_ylabel("Production (tonnes)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Stage {int(s)}" if s % 1 == 0 else f"Stage {s:.1f}" for s in all_stages])
    ax.legend()
    ax.tick_params(axis='x', rotation=0)
    
    # 2. Competitive producers comparison
    ax = axes[0, 1]
    country_competitive = []
    region_competitive = []
    
    for stage in all_stages:
        year = 2040  # Use 2040 prices for competitiveness
        price = get_price_for_mineral_stage_year(price_dict, mineral, stage, year)
        
        if price:
            # Count competitive producers for country scenario
            country_stage = country_data[country_data["processing_stage"] == stage]
            country_comp = country_stage[
                country_stage["production_transport_energy_unit_cost_usd_per_tonne"] < price
            ]
            country_competitive.append(len(country_comp["iso3"].unique()))
            
            # Count competitive producers for region scenario
            region_stage = region_data[region_data["processing_stage"] == stage]
            region_comp = region_stage[
                region_stage["production_transport_energy_unit_cost_usd_per_tonne"] < price
            ]
            region_competitive.append(len(region_comp["iso3"].unique()))
        else:
            country_competitive.append(0)
            region_competitive.append(0)
    
    ax.bar(x - width/2, country_competitive, width, label='Country Unconstrained', 
           color='steelblue', alpha=0.8)
    ax.bar(x + width/2, region_competitive, width, label='Region Unconstrained', 
           color='darkorange', alpha=0.8)
    
    ax.set_xticks(x)
    ax.set_xticklabels([f"Stage {int(s)}" if s % 1 == 0 else f"Stage {s:.1f}" for s in all_stages])
    ax.set_title("Competitive Countries by Stage")
    ax.set_xlabel("Processing Stage")
    ax.set_ylabel("Number of Countries")
    ax.legend()
    
    # 3. Top producers comparison by scenario
    ax = axes[1, 0]
    country_producers = country_data.groupby("iso3")["production_tonnes"].sum().nlargest(8)
    region_producers = region_data.groupby("iso3")["production_tonnes"].sum().nlargest(8)
    
    # Get union of top countries from both scenarios
    top_countries = list(set(country_producers.index) | set(region_producers.index))
    country_values = [country_producers.get(country, 0) for country in top_countries]
    region_values = [region_producers.get(country, 0) for country in top_countries]
    
    y_pos = np.arange(len(top_countries))
    ax.barh(y_pos - 0.2, country_values, 0.4, label='Country Unconstrained', 
            color='steelblue', alpha=0.8)
    ax.barh(y_pos + 0.2, region_values, 0.4, label='Region Unconstrained', 
            color='darkorange', alpha=0.8)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_countries)
    ax.set_title("Top Producers by Scenario (2040)")
    ax.set_xlabel("Production (tonnes)")
    ax.legend()
    
    # 4. Average cost competitiveness comparison
    ax = axes[1, 1]
    
    # Calculate average competitiveness by scenario
    country_competitiveness = []
    region_competitiveness = []
    stage_labels = []
    
    for stage in all_stages:
        year = 2040
        price = get_price_for_mineral_stage_year(price_dict, mineral, stage, year)
        
        if price:
            # Country scenario avg competitiveness
            country_stage = country_data[country_data["processing_stage"] == stage]
            if len(country_stage) > 0:
                country_avg_cost = country_stage["production_transport_energy_unit_cost_usd_per_tonne"].mean()
                country_competitiveness.append(country_avg_cost / price if price > 0 else 2)
            else:
                country_competitiveness.append(0)
            
            # Region scenario avg competitiveness
            region_stage = region_data[region_data["processing_stage"] == stage]
            if len(region_stage) > 0:
                region_avg_cost = region_stage["production_transport_energy_unit_cost_usd_per_tonne"].mean()
                region_competitiveness.append(region_avg_cost / price if price > 0 else 2)
            else:
                region_competitiveness.append(0)
                
            stage_labels.append(f"Stage {int(stage)}" if stage % 1 == 0 else f"Stage {stage:.1f}")
        
    if country_competitiveness and region_competitiveness:
        x_comp = np.arange(len(stage_labels))
        ax.bar(x_comp - 0.2, country_competitiveness, 0.4, label='Country Unconstrained', 
               color='steelblue', alpha=0.8)
        ax.bar(x_comp + 0.2, region_competitiveness, 0.4, label='Region Unconstrained', 
               color='darkorange', alpha=0.8)
        
        ax.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='Break-even (Cost = Price)')
        ax.set_xticks(x_comp)
        ax.set_xticklabels(stage_labels)
        ax.set_title("Average Cost/Price Ratio by Stage")
        ax.set_ylabel("Cost/Price Ratio")
        ax.set_xlabel("Processing Stage")
        ax.legend()
    else:
        ax.text(0.5, 0.5, "No competitiveness data available", 
                ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    
    # Save figure
    filename = f"competitive_matrix_{mineral}_stats.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved competitive position statistics: {filename}")


def main():
    """Main function to generate competitive position matrices"""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"Loading data from: {data_path}")
    
    df = pd.read_excel(data_path)
    print(f"Loaded {len(df)} rows of data")
    
    # Filter for simplified scenarios - focus on key comparison
    df_filtered = df[
        (
            (df["scenario"] == "2022_baseline") |
            ((df["scenario"].str.contains("mid_min")) & (df["constraint"] == "country_unconstrained")) |
            ((df["scenario"].str.contains("mid_max")) & (df["constraint"] == "region_unconstrained"))
        )
    ].copy()
    
    # Set up output directory
    output_dir = os.path.join(config['paths']['figures'], 'competitive_position_matrices')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Generate matrices for each mineral
    for mineral in reference_minerals:
        print(f"\nProcessing {mineral}...")
        create_competitive_position_matrix(df_filtered, mineral, output_dir)
    
    print(f"\n✅ Competitive position matrix generation complete!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()