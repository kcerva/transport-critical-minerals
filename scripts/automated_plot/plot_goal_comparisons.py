import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from plot_config import (
    reference_mineral_colors,
    reference_mineral_namemap,
    reference_mineral_colormapshort
)
from plot_utils import format_legend, annotate_stacked_bars, annotate_bar_labels

def plot_goal_comparisons_2040(df, output_dir, metric_column, metric_title, metric_units, country_iso3=None):
    """
    Create subplot comparisons of 2040 goals: BAU vs Early Refining vs Precursor
    Adapted from new_bar_charts.py subplot logic
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter for 2040 scenarios only
    df_2040 = df[df["year"] == 2040].copy()
    
    if df_2040.empty:
        print(f"No 2040 data available for {metric_title}")
        return []
    
    # Define goal mapping
    def get_goal_from_scenario(scenario):
        if 'bau_2040' in scenario:
            return "Business as Usual"
        elif 'early_refining_2040' in scenario:
            return "Early Refining"
        elif 'precursor_2040' in scenario:
            return "Precursor related product"
        else:
            return None
    
    df_2040["goal_type"] = df_2040["scenario"].apply(get_goal_from_scenario)
    df_2040 = df_2040.dropna(subset=['goal_type'])
    
    if df_2040.empty:
        print(f"No goal-specific 2040 data available for {metric_title}")
        return []
    
    # Convert metric to appropriate units
    if 'million' in metric_units.lower() or 'musd' in metric_units.lower():
        df_2040[f"{metric_column}_converted"] = df_2040[metric_column] / 1e6
    elif 'thousand' in metric_units.lower() or 'kt' in metric_units.lower():
        df_2040[f"{metric_column}_converted"] = df_2040[metric_column] / 1e3
    else:
        df_2040[f"{metric_column}_converted"] = df_2040[metric_column]
    
    converted_column = f"{metric_column}_converted"
    
    saved_paths = []
    
    # Group by constraint type for subplot creation
    for constraint in df_2040['constraint'].unique():
        df_constraint = df_2040[df_2040['constraint'] == constraint]
        
        if df_constraint.empty:
            continue
        
        # Create 3-subplot figure: BAU, Early Refining, Precursor
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
        
        goals = ["Business as Usual", "Early Refining", "Precursor related product"]
        
        for ax, goal in zip(axes, goals):
            df_goal = df_constraint[df_constraint['goal_type'] == goal]
            
            if df_goal.empty:
                ax.set_title(f"{goal}\n(No data)")
                continue
            
            # Filter for country if specified
            if country_iso3:
                df_goal = df_goal[df_goal['iso3'] == country_iso3]
                if df_goal.empty:
                    ax.set_title(f"{goal}\n(No data for {country_iso3})")
                    continue
            
            # Aggregate by reference mineral
            if country_iso3:
                # For single country, group by mineral
                grouped = df_goal.groupby("reference_mineral")[converted_column].sum().reset_index()
                pivot = grouped.set_index("reference_mineral")[converted_column].to_frame().T
                index_label = country_iso3
            else:
                # For multi-country, group by country and mineral
                grouped = df_goal.groupby(["iso3", "reference_mineral"])[converted_column].sum().reset_index()
                pivot = grouped.pivot_table(
                    index="iso3",
                    columns="reference_mineral", 
                    values=converted_column,
                    fill_value=0
                )
                index_label = "Country"
            
            if pivot.empty:
                ax.set_title(f"{goal}\n(No data)")
                continue
            
            # Sort by total for better visualization
            pivot["total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
            
            # Plot horizontal stacked bar
            colors = [reference_mineral_colormapshort.get(
                reference_mineral_namemap.get(col, col), "#999999"
            ) for col in pivot.columns]
            
            pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
            
            # Format axes
            ax.set_title(f"{goal}", fontsize=14, fontweight="bold")
            ax.set_xlabel(f"{metric_title} ({metric_units})", fontsize=12)
            if ax == axes[0]:  # Only label y-axis for first subplot
                ax.set_ylabel(index_label, fontsize=12)
            ax.tick_params(labelsize=10)
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)
            
            # Annotate bars if data is substantial
            if not pivot.empty and pivot.sum(axis=1).max() > 0:
                annotate_bar_labels(ax, pivot, orientation="horizontal", min_display_frac=0.1)
        
        # Overall figure formatting
        constraint_type = "Nationalist" if "country" in constraint else "Regionalist"
        constraint_status = "Unconstrained" if "unconstrained" in constraint else "Constrained"
        
        title_suffix = f" - {country_iso3}" if country_iso3 else ""
        fig.suptitle(f"2040 Goal Comparison: {metric_title} - {constraint_type} {constraint_status}{title_suffix}", 
                    fontsize=16, fontweight="bold")
        
        # Add single legend to the right
        handles, labels = axes[-1].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, title="Mineral", bbox_to_anchor=(0.98, 0.5), loc='center left')
            for ax in axes:
                legend = ax.get_legend()
                if legend:
                    legend.remove()
        
        plt.tight_layout(rect=[0, 0, 0.85, 0.95])
        
        # Save figure
        country_suffix = f"_{country_iso3}" if country_iso3 else "_all_countries"
        filename = f"goal_comparison_2040_{metric_column}_{constraint}{country_suffix}.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(filepath)
        
        print(f"Saved goal comparison chart: {filename}")
    
    return saved_paths

def plot_production_goal_comparison_by_processing_type(df, output_dir, country_iso3):
    """
    Create goal comparison specifically for production by processing type
    Shows what processing_type each goal focuses on
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter for 2040, processing_stage > 0, and specific country
    df_filtered = df[
        (df["year"] == 2040) & 
        (df["processing_stage"] > 0) & 
        (df["iso3"] == country_iso3)
    ].copy()
    
    if df_filtered.empty:
        print(f"No 2040 production data for {country_iso3}")
        return []
    
    def get_goal_from_scenario(scenario):
        if 'bau_2040' in scenario:
            return "Business as Usual"
        elif 'early_refining_2040' in scenario:
            return "Early Refining"  
        elif 'precursor_2040' in scenario:
            return "Precursor related product"
        else:
            return None
    
    df_filtered["goal_type"] = df_filtered["scenario"].apply(get_goal_from_scenario)
    df_filtered = df_filtered.dropna(subset=['goal_type'])
    
    df_filtered["production_kt"] = df_filtered["production_tonnes"] / 1000
    
    saved_paths = []
    
    for constraint in df_filtered['constraint'].unique():
        df_constraint = df_filtered[df_filtered['constraint'] == constraint]
        
        if df_constraint.empty:
            continue
        
        # Create figure with 3 subplots for goals
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
        goals = ["Business as Usual", "Early Refining", "Precursor related product"]
        
        for ax, goal in zip(axes, goals):
            df_goal = df_constraint[df_constraint['goal_type'] == goal]
            
            if df_goal.empty:
                ax.set_title(f"{goal}\n(No data)")
                continue
            
            # Group by processing_type and reference_mineral
            grouped = df_goal.groupby(["processing_type", "reference_mineral"])["production_kt"].sum().reset_index()
            
            pivot = grouped.pivot_table(
                index="processing_type",
                columns="reference_mineral",
                values="production_kt", 
                fill_value=0
            )
            
            if pivot.empty:
                ax.set_title(f"{goal}\n(No data)")
                continue
            
            # Sort by total for better visualization
            pivot["total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="total", ascending=True).drop(columns="total")
            
            # Plot horizontal stacked bar
            colors = [reference_mineral_colormapshort.get(
                reference_mineral_namemap.get(col, col), "#999999"
            ) for col in pivot.columns]
            
            pivot.plot(kind="barh", stacked=True, color=colors, ax=ax)
            
            # Format axes
            ax.set_title(f"{goal}", fontsize=14, fontweight="bold")
            ax.set_xlabel("Production (kt)", fontsize=12)
            if ax == axes[0]:
                ax.set_ylabel("Processing Type", fontsize=12)
            ax.tick_params(labelsize=10)
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            ax.set_axisbelow(True)
            
            # Annotate bars
            if not pivot.empty and pivot.sum(axis=1).max() > 0:
                annotate_bar_labels(ax, pivot, orientation="horizontal", min_display_frac=0.1)
        
        # Overall formatting
        constraint_type = "Nationalist" if "country" in constraint else "Regionalist"
        constraint_status = "Unconstrained" if "unconstrained" in constraint else "Constrained"
        
        fig.suptitle(f"2040 Production by Processing Type: Goal Comparison - {country_iso3} - {constraint_type} {constraint_status}", 
                    fontsize=16, fontweight="bold")
        
        # Add legend
        handles, labels = axes[-1].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, title="Mineral", bbox_to_anchor=(0.98, 0.5), loc='center left')
            for ax in axes:
                legend = ax.get_legend()
                if legend:
                    legend.remove()
        
        plt.tight_layout(rect=[0, 0, 0.85, 0.95])
        
        # Save
        filename = f"goal_comparison_production_by_type_{country_iso3}_{constraint}.png"
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(filepath)
    
    return saved_paths