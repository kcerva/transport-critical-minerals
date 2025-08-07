#!/usr/bin/env python3
"""
Alternative Competitive Position Visualizations

This script provides cleaner, more focused alternatives to the complex competitive position matrix.
These approaches prioritize clarity and user experience while maintaining analytical value.

Alternative approaches implemented:
1. Simplified 2x2 Scenario Matrix: Focus on key country vs region policy comparison
2. Faceted Goal Stage Analysis: Separate subplots for each processing goal
3. Interactive Bubble Dashboard: Unified view with hover details
4. Top Performers Ranking: Clear ranking approach for decision-making
5. Competitive Segmentation: Countries grouped by competitiveness levels
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, RegularPolygon
import seaborn as sns
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

def load_price_data():
    """Load price data from Final_Price_and_Costs_RP.xlsx"""
    file_path = Path("/home/karlac/critical_minerals_Africa/transport-outputs/data/Final_Price_and_Costs_RP.xlsx")
    
    if not file_path.exists():
        print(f"Warning: Price file not found at {file_path}")
        return {}
    
    prices_df = pd.read_excel(file_path, sheet_name='Price_final')
    prices_df['reference_mineral'] = prices_df['reference_mineral'].ffill()
    
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

def prepare_competitive_data(df, mineral, price_dict):
    """
    Prepare data for competitive analysis with key metrics calculated
    """
    # Filter data for this mineral
    mineral_data = df[
        (df["reference_mineral"] == mineral) &
        (df["processing_stage"] > 0) &
        (df["production_tonnes"] > 0)
    ].copy()
    
    if len(mineral_data) == 0:
        return pd.DataFrame()
    
    # Add competitiveness ratio
    results = []
    for _, row in mineral_data.iterrows():
        year = 2022 if row["scenario"] == "2022_baseline" else 2040
        price = get_price_for_mineral_stage_year(price_dict, mineral, row["processing_stage"], year)
        
        if price and price > 0 and row["production_transport_energy_unit_cost_usd_per_tonne"] > 0:
            competitiveness_ratio = row["production_transport_energy_unit_cost_usd_per_tonne"] / price
            
            # Determine goal stage status
            is_goal = False
            goal_type = get_goal_from_scenario(row["scenario"])
            if goal_type and mineral in mineral_processing_stages:
                target_stages = mineral_processing_stages[mineral]["target_stages"]
                if goal_type == 'bau' and row["processing_stage"] == target_stages.get("Beneficiation", 1.0):
                    is_goal = True
                elif goal_type == 'early_refining' and row["processing_stage"] == target_stages.get("Early refining", 3.0):
                    is_goal = True
                elif goal_type == 'precursor' and row["processing_stage"] == target_stages.get("Precursor related product", 5.0):
                    is_goal = True
            
            result = row.to_dict()
            result.update({
                'price': price,
                'competitiveness_ratio': competitiveness_ratio,
                'is_competitive': competitiveness_ratio < 1.0,
                'is_goal_stage': is_goal,
                'goal_type': goal_type,
                'year': year
            })
            results.append(result)
    
    return pd.DataFrame(results)

# ALTERNATIVE 1: Simplified 2x2 Scenario Matrix
def create_simplified_scenario_matrix(df, mineral, output_dir):
    """
    Focus only on the key policy comparison: Country vs Region, Unconstrained scenarios
    This reduces complexity from 50+ rows to just 2 key scenarios
    """
    price_dict = load_price_data()
    data = prepare_competitive_data(df, mineral, price_dict)
    
    if data.empty:
        print(f"No data for {mineral} simplified matrix")
        return
    
    # Focus on 2040 scenarios and unconstrained only
    focus_data = data[
        (data["year"] == 2040) &
        (data["constraint"].isin(["country_unconstrained", "region_unconstrained"])) &
        (data["goal_type"].isin(["early_refining", "precursor"])) &
        (data["is_goal_stage"] == True)
    ].copy()
    
    if focus_data.empty:
        print(f"No goal stage data for {mineral}")
        return
    
    # Create the 2x2 grid
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f'{mineral.title()} - Policy Comparison: Key Scenarios Only', 
                 fontsize=16, fontweight='bold')
    
    scenarios = ["early_refining", "precursor"]
    constraints = ["country_unconstrained", "region_unconstrained"]
    scenario_labels = ["Early Refining Goal", "Precursor Goal"]
    constraint_labels = ["National Policy", "Regional Integration"]
    
    for i, scenario in enumerate(scenarios):
        for j, constraint in enumerate(constraints):
            ax = axes[i, j]
            
            # Filter data for this combination
            subset = focus_data[
                (focus_data["goal_type"] == scenario) &
                (focus_data["constraint"] == constraint)
            ]
            
            if subset.empty:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14, alpha=0.7)
                ax.set_title(f"{scenario_labels[i]}\n{constraint_labels[j]}", fontweight='bold')
                continue
            
            # Group by country for cleaner visualization
            country_summary = subset.groupby("iso3").agg({
                "production_tonnes": "sum",
                "competitiveness_ratio": "mean",
                "is_competitive": "all"
            }).reset_index()
            
            # Sort by production volume
            country_summary = country_summary.sort_values("production_tonnes", ascending=True)
            
            # Create horizontal bar chart with color coding
            colors = ['#2E7D32' if comp else '#E53935' for comp in country_summary["is_competitive"]]
            bars = ax.barh(country_summary["iso3"], country_summary["production_tonnes"], 
                          color=colors, alpha=0.8)
            
            # Add competitiveness ratio as text on bars
            for bar, ratio in zip(bars, country_summary["competitiveness_ratio"]):
                width = bar.get_width()
                if width > 0:
                    ax.text(width/2, bar.get_y() + bar.get_height()/2, 
                           f'{ratio:.2f}', ha='center', va='center', 
                           fontweight='bold', fontsize=9)
            
            ax.set_title(f"{scenario_labels[i]}\n{constraint_labels[j]}", fontweight='bold')
            ax.set_xlabel("Production (tonnes)")
            ax.grid(axis='x', alpha=0.3)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(color='#2E7D32', label='Competitive (Cost < Price)'),
        mpatches.Patch(color='#E53935', label='Not Competitive (Cost > Price)')
    ]
    fig.legend(handles=legend_elements, loc='center', bbox_to_anchor=(0.5, 0.02), ncol=2)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    # Save
    filename = f"competitive_simplified_{mineral}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved simplified scenario matrix: {filename}")

# ALTERNATIVE 2: Faceted Goal Stage Analysis
def create_faceted_goal_analysis(df, mineral, output_dir):
    """
    Separate subplots for different processing goals with clear ranking
    Focus on what matters: "Which countries win in each processing strategy?"
    """
    price_dict = load_price_data()
    data = prepare_competitive_data(df, mineral, price_dict)
    
    if data.empty:
        print(f"No data for {mineral} faceted analysis")
        return
    
    # Focus on goal stages only
    goal_data = data[
        (data["is_goal_stage"] == True) &
        (data["year"] == 2040) &
        (data["constraint"] == "country_unconstrained")  # Use consistent constraint for comparison
    ].copy()
    
    if goal_data.empty:
        print(f"No goal stage data for {mineral}")
        return
    
    # Create faceted plot
    goals = goal_data["goal_type"].unique()
    n_goals = len(goals)
    
    fig, axes = plt.subplots(1, n_goals, figsize=(6*n_goals, 8))
    if n_goals == 1:
        axes = [axes]
    
    fig.suptitle(f'{mineral.title()} - Processing Strategy Comparison (Country Unconstrained)\nWhich Countries Win?', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    goal_labels = {
        'bau': 'Basic Processing\n(Beneficiation)',
        'early_refining': 'Early Refining\nStrategy',
        'precursor': 'Advanced Processing\n(Precursor Products)'
    }
    
    for i, goal in enumerate(sorted(goals)):
        ax = axes[i]
        goal_subset = goal_data[goal_data["goal_type"] == goal]
        
        if goal_subset.empty:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(goal_labels.get(goal, goal.title()), fontweight='bold')
            continue
        
        # Calculate competitive advantage score: (1/competitiveness_ratio) * production_weight
        goal_subset = goal_subset.copy()
        max_production = goal_subset["production_tonnes"].max()
        goal_subset["production_weight"] = goal_subset["production_tonnes"] / max_production
        goal_subset["advantage_score"] = (1 / goal_subset["competitiveness_ratio"]) * goal_subset["production_weight"]
        
        # Group by country and calculate total advantage
        country_advantage = goal_subset.groupby("iso3").agg({
            "production_tonnes": "sum",
            "competitiveness_ratio": "mean",
            "advantage_score": "sum",
            "is_competitive": "all"
        }).reset_index()
        
        # Sort by advantage score
        country_advantage = country_advantage.sort_values("advantage_score", ascending=True)
        
        # Color by competitiveness
        colors = ['#2E7D32' if comp else '#E53935' for comp in country_advantage["is_competitive"]]
        
        # Create horizontal bar chart
        bars = ax.barh(range(len(country_advantage)), country_advantage["advantage_score"],
                      color=colors, alpha=0.8)
        
        # Add labels
        ax.set_yticks(range(len(country_advantage)))
        ax.set_yticklabels(country_advantage["iso3"])
        ax.set_xlabel("Competitive Advantage Score")
        ax.set_title(goal_labels.get(goal, goal.title()), fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        # Add competitiveness ratio as text (positioned safely)
        for j, (bar, ratio, prod) in enumerate(zip(bars, 
                                                  country_advantage["competitiveness_ratio"],
                                                  country_advantage["production_tonnes"])):
            width = bar.get_width()
            x_max = ax.get_xlim()[1]
            
            # Position text inside bar if there's space, otherwise outside
            if width > x_max * 0.3:
                text_x = width * 0.5
                ha = 'center'
                color = 'white'
            else:
                text_x = width + x_max * 0.02
                ha = 'left'
                color = 'black'
                
            ax.text(text_x, bar.get_y() + bar.get_height()/2, 
                   f'{ratio:.2f}', 
                   ha=ha, va='center', fontsize=9, fontweight='bold', color=color)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(color='#2E7D32', label='Competitive'),
        mpatches.Patch(color='#E53935', label='Not Competitive')
    ]
    fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=2)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15, top=0.85, left=0.1, right=0.95)
    
    # Save
    filename = f"competitive_faceted_{mineral}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved faceted goal analysis: {filename}")

# ALTERNATIVE 3: Interactive-Style Bubble Dashboard
def create_bubble_dashboard(df, mineral, output_dir):
    """
    Unified bubble chart showing all key relationships in a single view
    X: Competitiveness Ratio, Y: Production Volume, Size: Revenue Potential, Color: Policy Type
    """
    price_dict = load_price_data()
    data = prepare_competitive_data(df, mineral, price_dict)
    
    if data.empty:
        print(f"No data for {mineral} bubble dashboard")
        return
    
    # Focus on 2040 goal stages
    bubble_data = data[
        (data["is_goal_stage"] == True) &
        (data["year"] == 2040) &
        (data["constraint"].isin(["country_unconstrained", "region_unconstrained"]))
    ].copy()
    
    if bubble_data.empty:
        print(f"No bubble data for {mineral}")
        return
    
    # Calculate revenue potential
    bubble_data["revenue_potential"] = bubble_data["production_tonnes"] * bubble_data["price"]
    
    # Create the bubble chart
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Color by policy type
    policy_colors = {"country_unconstrained": "#1f77b4", "region_unconstrained": "#ff7f0e"}
    goal_shapes = {"early_refining": "o", "precursor": "s"}
    
    for constraint in bubble_data["constraint"].unique():
        for goal in bubble_data["goal_type"].unique():
            subset = bubble_data[
                (bubble_data["constraint"] == constraint) &
                (bubble_data["goal_type"] == goal)
            ]
            
            if subset.empty:
                continue
            
            # Scale bubble size
            size_scale = 1000
            sizes = (subset["revenue_potential"] / subset["revenue_potential"].max()) * size_scale
            
            label = f"{constraint.replace('_unconstrained', '').title()} - {goal.replace('_', ' ').title()}"
            
            scatter = ax.scatter(subset["competitiveness_ratio"], 
                               subset["production_tonnes"],
                               s=sizes, 
                               c=policy_colors[constraint],
                               marker=goal_shapes.get(goal, 'o'),
                               alpha=0.7,
                               label=label,
                               edgecolors='black',
                               linewidths=0.5)
            
            # Add country labels for significant producers
            for _, row in subset.iterrows():
                if row["production_tonnes"] > subset["production_tonnes"].quantile(0.7):
                    ax.annotate(row["iso3"], 
                              (row["competitiveness_ratio"], row["production_tonnes"]),
                              xytext=(5, 5), textcoords='offset points',
                              fontsize=8, alpha=0.8)
    
    # Add reference lines
    ax.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='Competitiveness Threshold')
    median_production = bubble_data["production_tonnes"].median()
    ax.axhline(y=median_production, color='gray', 
               linestyle=':', alpha=0.5, label=f'Median Production ({median_production:.0f}t)')
    
    ax.set_xlabel('Competitiveness Ratio (Cost/Price per tonne)\n← More Competitive | Less Competitive →', fontsize=12)
    ax.set_ylabel('Production Volume (tonnes)', fontsize=12)
    ax.set_title(f'{mineral.title()} - Competitive Position Dashboard\n' +
                'Goal Stages Only | Cost/Price per Stage | Bubble Size: Revenue Potential', 
                fontsize=14, fontweight='bold')
    
    # Set competitive zone
    ax.fill_betweenx([0, ax.get_ylim()[1]], 0, 1, alpha=0.1, color='green', label='Competitive Zone')
    
    # Create legend with better spacing
    handles, labels = ax.get_legend_handles_labels()
    legend = ax.legend(handles, labels, bbox_to_anchor=(1.08, 1), loc='upper left', 
                      frameon=True, fancybox=True, shadow=True)
    # Increase spacing between legend items (commented out due to matplotlib API changes)
    # for item in legend.legend_handles:
    #     item.set_markersize(8)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    filename = f"competitive_bubble_{mineral}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved bubble dashboard: {filename}")

# ALTERNATIVE 4: Top Performers Ranking
def create_top_performers_ranking(df, mineral, output_dir):
    """
    Clear ranking approach: "Who are the top 10 competitive producers for each strategy?"
    Decision-maker focused visualization
    """
    price_dict = load_price_data()
    data = prepare_competitive_data(df, mineral, price_dict)
    
    if data.empty:
        print(f"No data for {mineral} ranking")
        return
    
    # Focus on competitive producers only
    competitive_data = data[
        (data["is_competitive"] == True) &
        (data["is_goal_stage"] == True) &
        (data["year"] == 2040) &
        (data["constraint"] == "country_unconstrained")  # Use consistent constraint
    ].copy()
    
    if competitive_data.empty:
        print(f"No competitive data for {mineral}")
        return
    
    # Create ranking dashboard
    goals = competitive_data["goal_type"].unique()
    n_goals = len(goals)
    
    fig, axes = plt.subplots(1, n_goals, figsize=(8*n_goals, 10))
    if n_goals == 1:
        axes = [axes]
    
    fig.suptitle(f'{mineral.title()} - Top Competitive Producers by Strategy', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    goal_labels = {
        'bau': 'Basic Processing',
        'early_refining': 'Early Refining', 
        'precursor': 'Advanced Processing'
    }
    
    for i, goal in enumerate(sorted(goals)):
        ax = axes[i]
        goal_subset = competitive_data[competitive_data["goal_type"] == goal]
        
        if goal_subset.empty:
            ax.text(0.5, 0.5, 'No Competitive\nProducers', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(goal_labels.get(goal, goal.title()), fontweight='bold')
            continue
        
        # Calculate competitiveness score
        goal_subset = goal_subset.copy()
        goal_subset["profit_margin"] = goal_subset["price"] - goal_subset["production_transport_energy_unit_cost_usd_per_tonne"]
        goal_subset["competitiveness_score"] = goal_subset["profit_margin"] * goal_subset["production_tonnes"] / 1e6  # Million USD potential
        
        # Get top 10
        top_10 = goal_subset.nlargest(10, "competitiveness_score")
        
        # Create ranking chart
        y_positions = range(len(top_10))
        bars = ax.barh(y_positions, top_10["competitiveness_score"],
                      color='#2E7D32', alpha=0.8)
        
        # Add details on bars
        for j, (bar, row) in enumerate(zip(bars, top_10.itertuples())):
            width = bar.get_width()
            # Add ranking number
            ax.text(-width*0.1, bar.get_y() + bar.get_height()/2, 
                   f'#{j+1}', ha='right', va='center', fontweight='bold', fontsize=10)
            # Add details
            ax.text(width/2, bar.get_y() + bar.get_height()/2, 
                   f'{row.iso3}\nCost/Price: {row.competitiveness_ratio:.2f}\nVolume: {row.production_tonnes:.0f}t', 
                   ha='center', va='center', fontsize=8, fontweight='bold')
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels([])  # Remove y-labels since info is on bars
        ax.set_xlabel('Competitive Value Potential (Million USD)')
        ax.set_title(f'Top {len(top_10)} - {goal_labels.get(goal, goal.title())}', fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        ax.invert_yaxis()  # Rank 1 at top
    
    plt.tight_layout()
    
    # Save
    filename = f"competitive_ranking_{mineral}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved top performers ranking: {filename}")

# ALTERNATIVE 5: Competitive Segmentation
def create_competitive_segmentation(df, mineral, output_dir):
    """
    Segment countries into clear categories: Leaders, Followers, Strugglers
    Easy-to-understand strategic categorization
    """
    price_dict = load_price_data()
    data = prepare_competitive_data(df, mineral, price_dict)
    
    if data.empty:
        print(f"No data for {mineral} segmentation")
        return
    
    # Focus on key scenarios
    segment_data = data[
        (data["year"] == 2040) &
        (data["constraint"] == "country_unconstrained") &
        (data["is_goal_stage"] == True)
    ].copy()
    
    if segment_data.empty:
        print(f"No segmentation data for {mineral}")
        return
    
    # Calculate overall competitiveness metrics
    country_metrics = segment_data.groupby("iso3").agg({
        "production_tonnes": "sum",
        "competitiveness_ratio": "mean",
        "is_competitive": "mean"  # Percentage of competitive stages
    }).reset_index()
    
    # Define segments
    def categorize_country(row):
        if row["is_competitive"] > 0.8 and row["production_tonnes"] > country_metrics["production_tonnes"].quantile(0.6):
            return "Market Leaders"
        elif row["is_competitive"] > 0.5 and row["production_tonnes"] > country_metrics["production_tonnes"].quantile(0.3):
            return "Strong Followers"
        elif row["is_competitive"] > 0.3:
            return "Emerging Players"
        else:
            return "Challenged Producers"
    
    country_metrics["segment"] = country_metrics.apply(categorize_country, axis=1)
    
    # Create segmentation visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(f'{mineral.title()} - Competitive Segmentation Analysis', 
                 fontsize=16, fontweight='bold')
    
    # Left plot: Segmentation scatter
    segment_colors = {
        "Market Leaders": "#2E7D32",
        "Strong Followers": "#66BB6A", 
        "Emerging Players": "#FFC107",
        "Challenged Producers": "#E53935"
    }
    
    for segment in segment_colors.keys():
        segment_subset = country_metrics[country_metrics["segment"] == segment]
        if not segment_subset.empty:
            ax1.scatter(segment_subset["competitiveness_ratio"], 
                       segment_subset["production_tonnes"],
                       c=segment_colors[segment],
                       label=segment,
                       s=100,
                       alpha=0.8,
                       edgecolors='black')
            
            # Add country labels
            for _, row in segment_subset.iterrows():
                ax1.annotate(row["iso3"], 
                           (row["competitiveness_ratio"], row["production_tonnes"]),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, fontweight='bold')
    
    ax1.axvline(x=1.0, color='red', linestyle='--', alpha=0.7)
    ax1.set_xlabel('Average Competitiveness Ratio (Cost/Price)')
    ax1.set_ylabel('Total Production Volume (tonnes)')
    ax1.set_title('Competitive Position Segments', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Right plot: Segment summary
    segment_summary = country_metrics.groupby("segment").agg({
        "iso3": "count",
        "production_tonnes": "sum",
        "competitiveness_ratio": "mean",
        "is_competitive": "mean"
    }).reset_index()
    
    segment_order = ["Market Leaders", "Strong Followers", "Emerging Players", "Challenged Producers"]
    segment_summary = segment_summary.set_index("segment").reindex(segment_order).reset_index()
    
    # Stacked bar showing production share
    bottom = 0
    for _, row in segment_summary.iterrows():
        ax2.bar(0.5, row["production_tonnes"], bottom=bottom, 
               color=segment_colors[row["segment"]], 
               label=f'{row["segment"]}\n{row["iso3"]} countries\n{row["production_tonnes"]:.0f}t',
               width=0.6, alpha=0.8, edgecolor='black')
        
        # Add text on segment
        ax2.text(0.5, bottom + row["production_tonnes"]/2, 
                f'{row["segment"]}\n{row["iso3"]} countries', 
                ha='center', va='center', fontweight='bold', fontsize=10)
        
        bottom += row["production_tonnes"]
    
    ax2.set_xlim(0, 1)
    ax2.set_ylabel('Total Production Volume (tonnes)')
    ax2.set_title('Market Structure', fontweight='bold')
    ax2.set_xticks([])
    
    plt.tight_layout()
    
    # Save
    filename = f"competitive_segmentation_{mineral}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved competitive segmentation: {filename}")

def create_all_alternatives(df, mineral, output_dir):
    """Create all alternative visualizations for a mineral"""
    print(f"\n=== Creating Alternative Visualizations for {mineral.title()} ===")
    
    create_simplified_scenario_matrix(df, mineral, output_dir)
    create_faceted_goal_analysis(df, mineral, output_dir)
    create_bubble_dashboard(df, mineral, output_dir)
    create_top_performers_ranking(df, mineral, output_dir)
    create_competitive_segmentation(df, mineral, output_dir)

def main():
    """Main function to test the alternative approaches"""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"Loading data from: {data_path}")
    
    df = pd.read_excel(data_path)
    print(f"Loaded {len(df)} rows of data")
    
    # Filter for mid demand scenarios (consistent with current approach)
    df_filtered = df[
        (
            (df["scenario"] == "2022_baseline") |
            ((df["scenario"].str.contains("mid_min")) & (df["constraint"].str.contains("country"))) |
            ((df["scenario"].str.contains("mid_max")) & (df["constraint"].str.contains("region")))
        )
    ].copy()
    
    # Set up output directory
    output_dir = os.path.join(config['paths']['figures'], 'competitive_alternatives')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Test with copper first (as it has good data coverage based on the image we saw)
    test_mineral = "copper"
    print(f"\n=== Testing Alternative Approaches with {test_mineral.title()} ===")
    
    create_all_alternatives(df_filtered, test_mineral, output_dir)
    
    print(f"\n✅ Alternative visualization generation complete!")
    print(f"Output directory: {output_dir}")
    print(f"\nAlternative approaches created:")
    print(f"1. Simplified 2x2 Scenario Matrix - Focus on key policy comparison only")
    print(f"2. Faceted Goal Analysis - Clear ranking by processing strategy")
    print(f"3. Bubble Dashboard - Unified view with multiple dimensions")
    print(f"4. Top Performers Ranking - Decision-maker focused top-10 lists")
    print(f"5. Competitive Segmentation - Strategic categorization of countries")

if __name__ == "__main__":
    main()