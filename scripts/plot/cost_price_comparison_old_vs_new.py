"""
Compare old vs new cost and price data from Final_Price_and_Costs_RP.xlsx
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

def load_new_data():
    """Load new cost and price data from Final_Price_and_Costs_RP.xlsx"""
    
    # Find the file in transport-outputs/data
    project_root = Path(__file__).parent.parent.parent.parent
    file_path = project_root / "transport-outputs" / "data" / "Final_Price_and_Costs_RP.xlsx"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find {file_path}")
    
    # Load new data sheets
    new_prices = pd.read_excel(file_path, sheet_name='Price_final')
    old_prices = pd.read_excel(file_path, sheet_name='Price_final (low)')
    
    new_capex = pd.read_excel(file_path, sheet_name='CapEx_final')
    old_capex = pd.read_excel(file_path, sheet_name='CapEx_final (OLD)')
    
    new_opex = pd.read_excel(file_path, sheet_name='OpEx_final')
    old_opex = pd.read_excel(file_path, sheet_name='OpEx_final (OLD)')
    
    return {
        'new_prices': new_prices,
        'old_prices': old_prices,
        'new_capex': new_capex,
        'old_capex': old_capex,
        'new_opex': new_opex,
        'old_opex': old_opex
    }

def harmonize_stage_names(df):
    """Harmonize stage names to ensure consistent comparison between old and new data"""
    df_harmonized = df.copy()
    
    # Stage name mappings to standardize between old and new data
    stage_mappings = {
        'Stage 4.1 & 4.2': 'Stage 4.1',  # Cobalt: old data has combined name, new data uses Stage 4.1
        # Add other mappings as needed
    }
    
    # Apply mappings
    df_harmonized['stage'] = df_harmonized['stage'].replace(stage_mappings)
    
    return df_harmonized

def clean_data(df):
    """Clean data by forward-filling mineral names and formatting columns"""
    df_clean = df.copy()
    
    # Forward fill the reference_mineral column to handle merged cells
    df_clean['reference_mineral'] = df_clean['reference_mineral'].fillna(method='ffill')
    
    # Remove rows where reference_mineral is still NaN (header rows)
    df_clean = df_clean[df_clean['reference_mineral'].notna()].copy()
    
    # Remove rows where stage is NaN
    df_clean = df_clean[df_clean['stage'].notna()].copy()
    
    # Harmonize stage names for consistent comparison
    df_clean = harmonize_stage_names(df_clean)
    
    # Ensure year columns are numeric
    for year in [2022, 2030, 2040]:
        if year in df_clean.columns:
            df_clean[year] = pd.to_numeric(df_clean[year], errors='coerce')
    
    return df_clean

def create_comparison_structure(old_data, new_data, data_type):
    """Create structured comparison data"""
    
    old_clean = clean_data(old_data)
    new_clean = clean_data(new_data)
    
    comparison = {}
    
    # Get unique minerals
    minerals = sorted(set(old_clean['reference_mineral'].unique()) | 
                     set(new_clean['reference_mineral'].unique()))
    
    for mineral in minerals:
        old_mineral = old_clean[old_clean['reference_mineral'] == mineral]
        new_mineral = new_clean[new_clean['reference_mineral'] == mineral]
        
        if mineral not in comparison:
            comparison[mineral] = {'stages': [], 'old': {}, 'new': {}}
        
        # Get all stages for this mineral
        old_stages = old_mineral['stage'].unique() if not old_mineral.empty else []
        new_stages = new_mineral['stage'].unique() if not new_mineral.empty else []
        all_stages = sorted(set(old_stages) | set(new_stages))
        
        comparison[mineral]['stages'] = all_stages
        
        for stage in all_stages:
            old_stage_data = old_mineral[old_mineral['stage'] == stage]
            new_stage_data = new_mineral[new_mineral['stage'] == stage]
            
            # Extract values for 2022, 2030, 2040
            old_values = []
            new_values = []
            
            for year in [2022, 2030, 2040]:
                if not old_stage_data.empty and year in old_stage_data.columns:
                    old_val = old_stage_data[year].iloc[0] if not pd.isna(old_stage_data[year].iloc[0]) else 0
                else:
                    old_val = 0
                
                if not new_stage_data.empty and year in new_stage_data.columns:
                    new_val = new_stage_data[year].iloc[0] if not pd.isna(new_stage_data[year].iloc[0]) else 0
                else:
                    new_val = 0
                
                old_values.append(old_val)
                new_values.append(new_val)
            
            comparison[mineral]['old'][stage] = old_values
            comparison[mineral]['new'][stage] = new_values
    
    return comparison

def get_stage_colors():
    """Define colors for different stages"""
    return {
        'Stage 1': '#1f77b4',
        'Stage 2': '#ff7f0e', 
        'Stage 3': '#2ca02c',
        'Stage 3.1': '#2ca02c',
        'Stage 4': '#9467bd',
        'Stage 4.1': '#9467bd',
        'Stage 4.2': '#9467bd',
        'Stage 4.3': '#9467bd',
        'Stage 5': '#e377c2'
    }

def create_comparison_plots(price_comparison, capex_comparison, opex_comparison):
    """Create enhanced comparison plots focusing on 2022 vs 2040"""
    
    stage_colors = get_stage_colors()
    
    # Get all minerals with cost data (focus on costs since prices didn't change)
    all_minerals = sorted(set(capex_comparison.keys()) | set(opex_comparison.keys()))
    
    # Filter to minerals that have data
    minerals_with_data = []
    for mineral in all_minerals:
        has_capex = mineral in capex_comparison and capex_comparison[mineral]['stages']
        has_opex = mineral in opex_comparison and opex_comparison[mineral]['stages']
        if has_capex or has_opex:
            minerals_with_data.append(mineral)
    
    print(f"Creating enhanced plots for minerals: {minerals_with_data}")
    
    if minerals_with_data:
        create_multi_stage_comparison_plot(capex_comparison, opex_comparison, minerals_with_data, stage_colors)
        create_percentage_change_analysis(capex_comparison, opex_comparison, minerals_with_data, stage_colors)
        create_price_comparison_plots(price_comparison, minerals_with_data, stage_colors)
        create_price_percentage_change_analysis(price_comparison, minerals_with_data, stage_colors)

def create_multi_stage_comparison_plot(capex_comparison, opex_comparison, minerals, stage_colors):
    """Create separate multi-stage comparison plots for 2022 and 2040"""
    
    n_minerals = len(minerals)
    if n_minerals == 0:
        return
    
    # Get output directory
    output_dir = Path(__file__).parent.parent.parent.parent / "transport-outputs" / "figures" / "cost_price_comparisons"
    os.makedirs(output_dir, exist_ok=True)
    
    # Define colors
    capex_color = '#1f77b4'  # Blue for CAPEX
    opex_color = '#ff7f0e'   # Orange for OPEX
    
    # Create separate figures for 2022 and 2040
    for year_idx, year in enumerate(['2022', '2040']):
        # Create subplot grid (2x3 for 6 minerals)
        cols = 3
        rows = 2
        
        fig, axes = plt.subplots(rows, cols, figsize=(18, 10))
        axes = axes.flatten()
        
        for idx, mineral in enumerate(minerals):
            if idx >= len(axes):
                break
                
            ax = axes[idx]
            
            # Check if we have cost data for this mineral
            has_capex = mineral in capex_comparison and capex_comparison[mineral]['stages']
            has_opex = mineral in opex_comparison and opex_comparison[mineral]['stages']
            
            if not has_capex and not has_opex:
                ax.set_title(f'{mineral.title()} - No Cost Data')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                continue
            
            # Get all stages for this mineral
            all_stages = set()
            if has_capex:
                all_stages.update(capex_comparison[mineral]['stages'])
            if has_opex:
                all_stages.update(opex_comparison[mineral]['stages'])
            
            stages = sorted(all_stages)
            
            # Prepare data for selected year
            stage_data = []
            for stage in stages:
                stage_info = {'stage': stage}
                
                # Get old and new data for the year
                if year == '2022':
                    old_capex = capex_comparison[mineral]['old'].get(stage, [0,0,0])[0] if has_capex and stage in capex_comparison[mineral]['old'] else 0
                    new_capex = capex_comparison[mineral]['new'].get(stage, [0,0,0])[0] if has_capex and stage in capex_comparison[mineral]['new'] else 0
                    old_opex = opex_comparison[mineral]['old'].get(stage, [0,0,0])[0] if has_opex and stage in opex_comparison[mineral]['old'] else 0
                    new_opex = opex_comparison[mineral]['new'].get(stage, [0,0,0])[0] if has_opex and stage in opex_comparison[mineral]['new'] else 0
                else:  # 2040
                    old_capex = capex_comparison[mineral]['old'].get(stage, [0,0,0])[2] if has_capex and stage in capex_comparison[mineral]['old'] else 0
                    new_capex = capex_comparison[mineral]['new'].get(stage, [0,0,0])[2] if has_capex and stage in capex_comparison[mineral]['new'] else 0
                    old_opex = opex_comparison[mineral]['old'].get(stage, [0,0,0])[2] if has_opex and stage in opex_comparison[mineral]['old'] else 0
                    new_opex = opex_comparison[mineral]['new'].get(stage, [0,0,0])[2] if has_opex and stage in opex_comparison[mineral]['new'] else 0
                
                stage_info.update({
                    'old_capex': old_capex, 'new_capex': new_capex,
                    'old_opex': old_opex, 'new_opex': new_opex
                })
                stage_data.append(stage_info)
            
            # Create bars
            n_stages = len(stages)
            x_base = np.arange(n_stages) * 1.5  # Spacing between stages
            bar_width = 0.15
            
            # Plot bars: Old CAPEX, New CAPEX, Old OPEX, New OPEX
            for i, stage_info in enumerate(stage_data):
                # CAPEX bars
                ax.bar(x_base[i] - 1.5*bar_width, stage_info['old_capex'], bar_width, 
                       color=capex_color, alpha=0.5, label='CAPEX (Old)' if i == 0 else "")
                ax.bar(x_base[i] - 0.5*bar_width, stage_info['new_capex'], bar_width,
                       color=capex_color, alpha=0.8, edgecolor='black', linewidth=1.5, label='CAPEX (New)' if i == 0 else "")
                
                # OPEX bars
                ax.bar(x_base[i] + 0.5*bar_width, stage_info['old_opex'], bar_width,
                       color=opex_color, alpha=0.5, label='OPEX (Old)' if i == 0 else "")
                ax.bar(x_base[i] + 1.5*bar_width, stage_info['new_opex'], bar_width,
                       color=opex_color, alpha=0.8, edgecolor='black', linewidth=1.5, label='OPEX (New)' if i == 0 else "")
            
            ax.set_title(f'{mineral.title()} - {year}')
            ax.set_xlabel('Processing Stage')
            ax.set_ylabel('USD/tonne')
            ax.set_xticks(x_base)
            ax.set_xticklabels([s.replace('Stage ', '') for s in stages])
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add legend
            if idx == 0:  
                ax.legend(fontsize=8, loc='upper left')
            
            # Add labels below bars
            y_min = ax.get_ylim()[0]
            y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
            label_y = y_min - y_range * 0.06
            
            for i in range(n_stages):
                # Data source labels
                ax.text(x_base[i] - bar_width, label_y, 'Old|New', ha='center', va='top', fontsize=6)
                ax.text(x_base[i] + bar_width, label_y, 'Old|New', ha='center', va='top', fontsize=6)
                
                # Cost type labels
                ax.text(x_base[i] - bar_width, label_y - y_range * 0.04, 'CAPEX', ha='center', va='top', 
                       fontsize=7, weight='bold', color=capex_color)
                ax.text(x_base[i] + bar_width, label_y - y_range * 0.04, 'OPEX', ha='center', va='top', 
                       fontsize=7, weight='bold', color=opex_color)
        
        # Hide empty subplots
        for idx in range(len(minerals), len(axes)):
            axes[idx].set_visible(False)
        
        plt.suptitle(f'Cost Comparison: Old vs New Data ({year})\nSeparate bars for CAPEX and OPEX', fontsize=16)
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_dir / f"cost_comparison_{year}.png", dpi=300, bbox_inches='tight')
        print(f"✓ Saved cost comparison plot for {year}")
        plt.close()

def create_percentage_change_analysis(capex_comparison, opex_comparison, minerals, stage_colors):
    """Create percentage change analysis for both 2022 and 2040 changes"""
    
    # Collect percentage change data for both years
    change_data_2022 = []
    change_data_2040 = []
    
    for mineral in minerals:
        has_capex = mineral in capex_comparison and capex_comparison[mineral]['stages']
        has_opex = mineral in opex_comparison and opex_comparison[mineral]['stages']
        
        if not has_capex and not has_opex:
            continue
        
        # Get all stages for this mineral
        all_stages = set()
        if has_capex:
            all_stages.update(capex_comparison[mineral]['stages'])
        if has_opex:
            all_stages.update(opex_comparison[mineral]['stages'])
        
        for stage in sorted(all_stages):
            # Get data values
            old_capex_2022 = capex_comparison[mineral]['old'].get(stage, [0,0,0])[0] if has_capex and stage in capex_comparison[mineral]['old'] else 0
            old_capex_2040 = capex_comparison[mineral]['old'].get(stage, [0,0,0])[2] if has_capex and stage in capex_comparison[mineral]['old'] else 0
            new_capex_2022 = capex_comparison[mineral]['new'].get(stage, [0,0,0])[0] if has_capex and stage in capex_comparison[mineral]['new'] else 0
            new_capex_2040 = capex_comparison[mineral]['new'].get(stage, [0,0,0])[2] if has_capex and stage in capex_comparison[mineral]['new'] else 0
            
            old_opex_2022 = opex_comparison[mineral]['old'].get(stage, [0,0,0])[0] if has_opex and stage in opex_comparison[mineral]['old'] else 0
            old_opex_2040 = opex_comparison[mineral]['old'].get(stage, [0,0,0])[2] if has_opex and stage in opex_comparison[mineral]['old'] else 0
            new_opex_2022 = opex_comparison[mineral]['new'].get(stage, [0,0,0])[0] if has_opex and stage in opex_comparison[mineral]['new'] else 0
            new_opex_2040 = opex_comparison[mineral]['new'].get(stage, [0,0,0])[2] if has_opex and stage in opex_comparison[mineral]['new'] else 0
            
            # Calculate 2022 percentage changes
            capex_change_2022 = ((new_capex_2022 - old_capex_2022) / old_capex_2022 * 100) if old_capex_2022 > 0 else 0
            opex_change_2022 = ((new_opex_2022 - old_opex_2022) / old_opex_2022 * 100) if old_opex_2022 > 0 else 0
            
            old_total_2022 = old_capex_2022 + old_opex_2022
            new_total_2022 = new_capex_2022 + new_opex_2022
            total_change_2022 = ((new_total_2022 - old_total_2022) / old_total_2022 * 100) if old_total_2022 > 0 else 0
            
            # Calculate 2040 percentage changes
            capex_change_2040 = ((new_capex_2040 - old_capex_2040) / old_capex_2040 * 100) if old_capex_2040 > 0 else 0
            opex_change_2040 = ((new_opex_2040 - old_opex_2040) / old_opex_2040 * 100) if old_opex_2040 > 0 else 0
            
            old_total_2040 = old_capex_2040 + old_opex_2040
            new_total_2040 = new_capex_2040 + new_opex_2040
            total_change_2040 = ((new_total_2040 - old_total_2040) / old_total_2040 * 100) if old_total_2040 > 0 else 0
            
            # Add to data lists - only if there's a non-zero change
            if old_total_2022 > 0 and (abs(capex_change_2022) > 0.1 or abs(opex_change_2022) > 0.1 or abs(total_change_2022) > 0.1):
                change_data_2022.append({
                    'mineral': mineral, 'stage': stage,
                    'capex_change': capex_change_2022, 'opex_change': opex_change_2022,
                    'total_change': total_change_2022
                })
            
            if old_total_2040 > 0 and (abs(capex_change_2040) > 0.1 or abs(opex_change_2040) > 0.1 or abs(total_change_2040) > 0.1):
                change_data_2040.append({
                    'mineral': mineral, 'stage': stage,
                    'capex_change': capex_change_2040, 'opex_change': opex_change_2040,
                    'total_change': total_change_2040
                })
    
    if not change_data_2022 and not change_data_2040:
        print("No percentage change data available")
        return
    
    # Create figure with 2 rows: 2022 changes on top, 2040 changes on bottom
    fig, ((ax1_2022, ax2_2022), (ax1_2040, ax2_2040)) = plt.subplots(2, 2, figsize=(18, 12))
    
    # Function to plot percentage changes
    def plot_year_changes(ax1, ax2, change_data, year_label):
        # Sort by total change
        change_data.sort(key=lambda x: abs(x['total_change']), reverse=True)
        
        labels = [f"{item['mineral'].title()}\n{item['stage'].replace('Stage ', 'S')}" for item in change_data]
        capex_changes = [item['capex_change'] for item in change_data]
        opex_changes = [item['opex_change'] for item in change_data]
        total_changes = [item['total_change'] for item in change_data]
        
        # Plot 1: CAPEX vs OPEX
        x = np.arange(len(labels))
        width = 0.35
        
        # Use consistent colors: blue for CAPEX, orange for OPEX
        bars1 = ax1.bar(x - width/2, capex_changes, width, label='CAPEX Change %', 
                       color='#1f77b4', alpha=0.8, edgecolor='black', linewidth=0.5)
        bars2 = ax1.bar(x + width/2, opex_changes, width, label='OPEX Change %', 
                       color='#ff7f0e', alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title(f'CAPEX vs OPEX Changes ({year_label}: New vs Old)', fontsize=12)
        ax1.set_xlabel('Mineral - Stage', fontsize=10)
        ax1.set_ylabel('Percentage Change (%)', fontsize=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            if abs(height) > 1:
                ax1.text(bar.get_x() + bar.get_width()/2., height + (1 if height > 0 else -1),
                        f'{height:.1f}%', ha='center', va='bottom' if height > 0 else 'top', fontsize=7)
        
        for bar in bars2:
            height = bar.get_height()
            if abs(height) > 1:
                ax1.text(bar.get_x() + bar.get_width()/2., height + (1 if height > 0 else -1),
                        f'{height:.1f}%', ha='center', va='bottom' if height > 0 else 'top', fontsize=7)
        
        # Plot 2: Total changes
        bars3 = ax2.bar(x, total_changes, color='#2ca02c', alpha=0.7, edgecolor='black', linewidth=0.5)
        
        ax2.set_title(f'Total Cost Changes ({year_label}: New vs Old)', fontsize=12)
        ax2.set_xlabel('Mineral - Stage', fontsize=10)
        ax2.set_ylabel('Total Percentage Change (%)', fontsize=10)
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # Add value labels
        for bar, change in zip(bars3, total_changes):
            height = bar.get_height()
            if abs(height) > 1:
                ax2.text(bar.get_x() + bar.get_width()/2., height + (2 if height > 0 else -2),
                        f'{height:.1f}%', ha='center', va='bottom' if height > 0 else 'top', fontsize=8)
    
    # Plot 2022 changes
    if change_data_2022:
        plot_year_changes(ax1_2022, ax2_2022, change_data_2022, '2022')
    else:
        ax1_2022.text(0.5, 0.5, 'No 2022 data available', ha='center', va='center', transform=ax1_2022.transAxes)
        ax2_2022.text(0.5, 0.5, 'No 2022 data available', ha='center', va='center', transform=ax2_2022.transAxes)
    
    # Plot 2040 changes
    if change_data_2040:
        plot_year_changes(ax1_2040, ax2_2040, change_data_2040, '2040')
    else:
        ax1_2040.text(0.5, 0.5, 'No 2040 data available', ha='center', va='center', transform=ax1_2040.transAxes)
        ax2_2040.text(0.5, 0.5, 'No 2040 data available', ha='center', va='center', transform=ax2_2040.transAxes)
    
    plt.suptitle('Cost Change Analysis: New vs Old Data (2022 and 2040)\nRed = Increases, Green = Decreases', fontsize=16)
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(__file__).parent.parent.parent.parent / "transport-outputs" / "figures" / "cost_price_comparisons"
    plt.savefig(output_dir / "percentage_change_analysis_2022_2040.png", dpi=300, bbox_inches='tight')
    print("✓ Saved percentage change analysis plot")
    plt.close()

def create_price_comparison_plots(price_comparison, minerals, stage_colors):
    """Create separate multi-stage price comparison plots for 2022 and 2040"""
    
    n_minerals = len(minerals)
    if n_minerals == 0:
        return
    
    # Get output directory
    output_dir = Path(__file__).parent.parent.parent.parent / "transport-outputs" / "figures" / "cost_price_comparisons"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create separate figures for 2022 and 2040
    for year_idx, year in enumerate(['2022', '2040']):
        # Create subplot grid (2x3 for 6 minerals)
        cols = 3
        rows = 2
        
        fig, axes = plt.subplots(rows, cols, figsize=(18, 10))
        axes = axes.flatten()
        
        for idx, mineral in enumerate(minerals):
            if idx >= len(axes):
                break
                
            ax = axes[idx]
            
            # Check if we have price data for this mineral
            has_prices = mineral in price_comparison and price_comparison[mineral]['stages']
            
            if not has_prices:
                ax.set_title(f'{mineral.title()} - No Price Data')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                continue
            
            stages = sorted(price_comparison[mineral]['stages'])
            
            # Prepare data for selected year
            stage_data = []
            for stage in stages:
                stage_info = {'stage': stage}
                
                # Get old and new data for the year
                if year == '2022':
                    old_price = price_comparison[mineral]['old'].get(stage, [0,0,0])[0] if stage in price_comparison[mineral]['old'] else 0
                    new_price = price_comparison[mineral]['new'].get(stage, [0,0,0])[0] if stage in price_comparison[mineral]['new'] else 0
                else:  # 2040
                    old_price = price_comparison[mineral]['old'].get(stage, [0,0,0])[2] if stage in price_comparison[mineral]['old'] else 0
                    new_price = price_comparison[mineral]['new'].get(stage, [0,0,0])[2] if stage in price_comparison[mineral]['new'] else 0
                
                stage_info.update({
                    'old_price': old_price, 'new_price': new_price
                })
                stage_data.append(stage_info)
            
            # Create bars
            n_stages = len(stages)
            x_base = np.arange(n_stages) * 1.0  # Spacing between stages
            bar_width = 0.35
            
            # Plot bars: Old Price, New Price
            for i, stage_info in enumerate(stage_data):
                # Price bars
                ax.bar(x_base[i] - bar_width/2, stage_info['old_price'], bar_width, 
                       color='#9467bd', alpha=0.6, label='Price (Old)' if i == 0 else "")
                ax.bar(x_base[i] + bar_width/2, stage_info['new_price'], bar_width,
                       color='#9467bd', alpha=0.9, edgecolor='black', linewidth=1.5, label='Price (New)' if i == 0 else "")
            
            ax.set_title(f'{mineral.title()} Prices - {year}')
            ax.set_xlabel('Processing Stage')
            ax.set_ylabel('USD/tonne')
            ax.set_xticks(x_base)
            ax.set_xticklabels([s.replace('Stage ', '') for s in stages])
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_yscale('log')  # Use log scale due to wide range of price values
            
            # Add legend
            if idx == 0:  
                ax.legend(fontsize=8, loc='upper left')
            
            # Add labels below bars
            y_min = ax.get_ylim()[0]
            y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
            
            for i in range(n_stages):
                # Data source labels
                ax.text(x_base[i], y_min * 0.5, 'Old | New', ha='center', va='top', fontsize=7)
        
        # Hide empty subplots
        for idx in range(len(minerals), len(axes)):
            axes[idx].set_visible(False)
        
        plt.suptitle(f'Price Comparison: Old vs New Data ({year})', fontsize=16)
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_dir / f"price_comparison_{year}.png", dpi=300, bbox_inches='tight')
        print(f"✓ Saved price comparison plot for {year}")
        plt.close()

def create_price_percentage_change_analysis(price_comparison, minerals, stage_colors):
    """Create price percentage change analysis for both 2022 and 2040 changes"""
    
    # Collect percentage change data for both years
    change_data_2022 = []
    change_data_2040 = []
    
    for mineral in minerals:
        has_prices = mineral in price_comparison and price_comparison[mineral]['stages']
        
        if not has_prices:
            continue
        
        stages = sorted(price_comparison[mineral]['stages'])
        
        for stage in stages:
            # Get data values
            old_price_2022 = price_comparison[mineral]['old'].get(stage, [0,0,0])[0] if stage in price_comparison[mineral]['old'] else 0
            old_price_2040 = price_comparison[mineral]['old'].get(stage, [0,0,0])[2] if stage in price_comparison[mineral]['old'] else 0
            new_price_2022 = price_comparison[mineral]['new'].get(stage, [0,0,0])[0] if stage in price_comparison[mineral]['new'] else 0
            new_price_2040 = price_comparison[mineral]['new'].get(stage, [0,0,0])[2] if stage in price_comparison[mineral]['new'] else 0
            
            # Calculate 2022 percentage changes
            price_change_2022 = ((new_price_2022 - old_price_2022) / old_price_2022 * 100) if old_price_2022 > 0 else 0
            
            # Calculate 2040 percentage changes
            price_change_2040 = ((new_price_2040 - old_price_2040) / old_price_2040 * 100) if old_price_2040 > 0 else 0
            
            # Add to data lists - only if there's a non-zero change
            if old_price_2022 > 0 and abs(price_change_2022) > 0.1:
                change_data_2022.append({
                    'mineral': mineral, 'stage': stage, 'price_change': price_change_2022
                })
            
            if old_price_2040 > 0 and abs(price_change_2040) > 0.1:
                change_data_2040.append({
                    'mineral': mineral, 'stage': stage, 'price_change': price_change_2040
                })
    
    if not change_data_2022 and not change_data_2040:
        print("No price percentage change data available")
        return
    
    # Create figure with 1 row: 2022 and 2040 changes side by side
    fig, (ax_2022, ax_2040) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Function to plot percentage changes
    def plot_price_changes(ax, change_data, year_label):
        if not change_data:
            ax.text(0.5, 0.5, f'No {year_label} price changes', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Price Changes ({year_label}: New vs Old)')
            return
        
        # Sort by change magnitude
        change_data.sort(key=lambda x: abs(x['price_change']), reverse=True)
        
        labels = [f"{item['mineral'].title()}\n{item['stage'].replace('Stage ', 'S')}" for item in change_data]
        price_changes = [item['price_change'] for item in change_data]
        
        x = np.arange(len(labels))
        
        # Use purple color for prices (consistent with main plots)
        bars = ax.bar(x, price_changes, color='#9467bd', alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax.set_title(f'Price Changes ({year_label}: New vs Old)', fontsize=12)
        ax.set_xlabel('Mineral - Stage', fontsize=10)
        ax.set_ylabel('Price Change (%)', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # Add value labels
        for bar, change in zip(bars, price_changes):
            height = bar.get_height()
            if abs(height) > 1:
                ax.text(bar.get_x() + bar.get_width()/2., height + (1 if height > 0 else -1),
                        f'{height:.1f}%', ha='center', va='bottom' if height > 0 else 'top', fontsize=8)
    
    # Plot 2022 and 2040 changes
    plot_price_changes(ax_2022, change_data_2022, '2022')
    plot_price_changes(ax_2040, change_data_2040, '2040')
    
    plt.suptitle('Price Change Analysis: New vs Old Data\nPositive = Price Increases, Negative = Price Decreases', fontsize=16)
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(__file__).parent.parent.parent.parent / "transport-outputs" / "figures" / "cost_price_comparisons"
    plt.savefig(output_dir / "price_percentage_change_analysis_2022_2040.png", dpi=300, bbox_inches='tight')
    print("✓ Saved price percentage change analysis plot")
    plt.close()

def analyze_changes(price_comparison, capex_comparison, opex_comparison):
    """Analyze and print key changes between old and new data"""
    
    print("\n=== KEY INSIGHTS: OLD VS NEW DATA ===\n")
    
    for data_type, comparison in [('Prices', price_comparison), ('CAPEX', capex_comparison), ('OPEX', opex_comparison)]:
        print(f"{data_type.upper()} CHANGES:")
        print("-" * 40)
        
        for mineral in sorted(comparison.keys()):
            if not comparison[mineral]['stages']:
                continue
                
            print(f"\n{mineral.title()}:")
            
            for stage in comparison[mineral]['stages']:
                if stage in comparison[mineral]['old'] and stage in comparison[mineral]['new']:
                    old_vals = comparison[mineral]['old'][stage]
                    new_vals = comparison[mineral]['new'][stage]
                    
                    # Compare 2030 values
                    old_2030 = old_vals[1] if len(old_vals) > 1 else 0
                    new_2030 = new_vals[1] if len(new_vals) > 1 else 0
                    
                    if old_2030 > 0 and new_2030 > 0:
                        change_pct = ((new_2030 - old_2030) / old_2030) * 100
                        change_dir = "↑" if change_pct > 0 else "↓"
                        print(f"  {stage}: {old_2030:.0f} → {new_2030:.0f} ({change_dir}{abs(change_pct):.1f}%)")
                    elif old_2030 == 0 and new_2030 > 0:
                        print(f"  {stage}: NEW DATA → {new_2030:.0f}")
                    elif old_2030 > 0 and new_2030 == 0:
                        print(f"  {stage}: {old_2030:.0f} → REMOVED")
        
        print()

def main():
    """Main function to run the comparison analysis"""
    
    print("Loading cost and price data...")
    
    try:
        data = load_new_data()
        
        # Create comparison structures
        print("Processing price data...")
        price_comparison = create_comparison_structure(data['old_prices'], data['new_prices'], 'prices')
        
        print("Processing CAPEX data...")
        capex_comparison = create_comparison_structure(data['old_capex'], data['new_capex'], 'capex')
        
        print("Processing OPEX data...")
        opex_comparison = create_comparison_structure(data['old_opex'], data['new_opex'], 'opex')
        
        # Create comparison plots
        print("Creating comparison plots...")
        create_comparison_plots(price_comparison, capex_comparison, opex_comparison)
        
        # Analyze changes
        analyze_changes(price_comparison, capex_comparison, opex_comparison)
        
        print("\n✓ Enhanced cost comparison analysis completed!")
        print("✓ Cost comparison plots: cost_comparison_2022.png and cost_comparison_2040.png")
        print("✓ Percentage change analysis: percentage_change_analysis_2022_2040.png")
        print("✓ All plots saved to transport-outputs/figures/cost_price_comparisons/ directory")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def create_metal_content_price_comparison():
    """Create a comparison figure for metal content prices in 2022"""
    
    # Get project directories
    project_root = Path(__file__).parent.parent.parent.parent
    figure_dir = project_root / "transport-outputs" / "figures" / "cost_price_comparisons"
    figure_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the metal content price data
    file_path = project_root / "transport-outputs" / "data" / "Final_Price_and_Costs_RP.xlsx"
    df_metal = pd.read_excel(file_path, sheet_name='Price_final (metal cont)', nrows=26)
    
    # Clean the data
    df_metal['reference_mineral'] = df_metal['reference_mineral'].fillna(method='ffill')
    df_metal = df_metal[df_metal['stage'].notna()].copy()
    
    # Extract minerals and their 2022 prices
    minerals = df_metal['reference_mineral'].unique()
    
    # Create figure with subplots for each mineral
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Use consistent color for all bars
    bar_color = '#2E86AB'
    
    for i, mineral in enumerate(minerals):
        if i >= len(axes):
            break
            
        # Get data for this mineral
        mineral_data = df_metal[df_metal['reference_mineral'] == mineral].copy()
        stages = mineral_data['stage'].values
        prices_2022 = mineral_data[2022].values
        
        # Extract stage numbers for cleaner display
        stage_numbers = [s.replace('Stage ', '') for s in stages]
        
        # Create bar chart with consistent color
        bars = axes[i].bar(range(len(stages)), prices_2022, color=bar_color, 
                          edgecolor='black', linewidth=0.5)
        
        # Customize the subplot
        axes[i].set_title(f'{mineral.title()}', fontsize=14, fontweight='bold')
        axes[i].set_xlabel('Processing Stage', fontsize=12)
        axes[i].set_ylabel('Price (USD/tonne metal content)', fontsize=12)
        axes[i].set_xticks(range(len(stages)))
        axes[i].set_xticklabels(stage_numbers, fontsize=11, fontweight='bold')
        
        # Add value labels on bars
        for j, (bar, price) in enumerate(zip(bars, prices_2022)):
            if pd.notna(price) and price > 0:
                # Position label inside bar if there's space, otherwise above
                bar_height = bar.get_height()
                y_range = axes[i].get_ylim()[1] - axes[i].get_ylim()[0]
                
                # Format price for display
                if price >= 10000:
                    price_label = f'{price/1000:.0f}k'
                else:
                    price_label = f'{price:,.0f}'
                
                # Determine label position
                if axes[i].get_yscale() == 'log':
                    # For log scale, always put above
                    axes[i].text(bar.get_x() + bar.get_width()/2., bar_height * 1.1,
                               price_label, ha='center', va='bottom', fontsize=10, fontweight='bold')
                else:
                    # For linear scale, check if there's space
                    if bar_height > y_range * 0.1:
                        # Place inside if bar is tall enough
                        axes[i].text(bar.get_x() + bar.get_width()/2., bar_height * 0.5,
                                   price_label, ha='center', va='center', fontsize=10, 
                                   fontweight='bold', color='white')
                    else:
                        # Place above if bar is too short
                        axes[i].text(bar.get_x() + bar.get_width()/2., bar_height,
                                   price_label, ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Add grid for better readability
        axes[i].grid(axis='y', alpha=0.3)
        axes[i].set_axisbelow(True)
        
        # Use log scale if there's large variation
        if len(prices_2022[pd.notna(prices_2022)]) > 0:
            valid_prices = prices_2022[pd.notna(prices_2022) & (prices_2022 > 0)]
            if len(valid_prices) > 0:
                max_price = np.max(valid_prices)
                min_price = np.min(valid_prices)
                if max_price / min_price > 10:
                    axes[i].set_yscale('log')
                    axes[i].set_ylabel('Price (USD/tonne metal content) - Log Scale', fontsize=12)
    
    # Remove empty subplots
    for i in range(len(minerals), len(axes)):
        fig.delaxes(axes[i])
    
    plt.suptitle('Critical Minerals Metal Content Prices by Processing Stage (2022)\n(Comparable units: USD per tonne of metal content)', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # Save the figure
    output_path = figure_dir / "metal_content_prices_2022.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Metal content price comparison saved: {output_path}")
    
    # Create a summary comparison chart
    create_metal_content_summary_chart(df_metal, figure_dir)
    
def create_metal_content_summary_chart(df_metal, figure_dir):
    """Create a summary chart comparing metal content prices across minerals"""
    
    # Get unique minerals
    minerals = df_metal['reference_mineral'].unique()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Prepare data structure
    mineral_stage_data = {}
    for mineral in minerals:
        mineral_data = df_metal[df_metal['reference_mineral'] == mineral]
        stages_prices = []
        for _, row in mineral_data.iterrows():
            stage = row['stage']
            price = row[2022]
            if pd.notna(price) and price > 0:
                # Extract stage number for labeling
                stage_num = stage.replace('Stage ', '')
                stages_prices.append((stage_num, price))
        mineral_stage_data[mineral] = stages_prices
    
    # Create x positions for minerals
    x_positions = np.arange(len(minerals))
    bar_width = 0.7
    
    # Use a single color for all bars
    bar_color = '#2E86AB'
    
    # Plot bars for each mineral
    for i, mineral in enumerate(minerals):
        stages_prices = mineral_stage_data[mineral]
        
        if stages_prices:
            # Create sub-positions for stages within each mineral
            n_stages = len(stages_prices)
            stage_width = bar_width / n_stages
            stage_positions = x_positions[i] - bar_width/2 + stage_width/2 + np.arange(n_stages) * stage_width
            
            for j, (stage_num, price) in enumerate(stages_prices):
                bar = ax.bar(stage_positions[j], price, stage_width * 0.9, 
                            color=bar_color, edgecolor='black', linewidth=0.5)
                
                # Add stage number inside or above the bar
                if price > 0:
                    # Format price label
                    if price > 10000:
                        price_label = f'{price/1000:.0f}k'
                    elif price > 1000:
                        price_label = f'{price:.0f}'
                    else:
                        price_label = f'{price:.1f}'
                    
                    # Add stage number at base of bar
                    ax.text(stage_positions[j], 1, stage_num, 
                           ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
                    # Add price value above bar
                    ax.text(stage_positions[j], price * 1.05, price_label,
                           ha='center', va='bottom', fontsize=8, rotation=45)
    
    # Customize the chart
    ax.set_xlabel('Mineral', fontsize=14, fontweight='bold')
    ax.set_ylabel('Price (USD/tonne metal content) - Log Scale', fontsize=14, fontweight='bold')
    ax.set_title('Metal Content Prices by Mineral and Processing Stage (2022)\n(Stage numbers shown at bar base, prices above bars)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Set x-axis
    ax.set_xticks(x_positions)
    ax.set_xticklabels([m.title() for m in minerals], fontsize=12, fontweight='bold')
    
    # Use log scale
    ax.set_yscale('log')
    ax.set_ylim(bottom=0.5)  # Start slightly below 1 to show stage numbers
    
    # Add grid
    ax.grid(axis='y', alpha=0.3, which='both')
    ax.set_axisbelow(True)
    
    # Add explanatory notes
    ax.text(0.98, 0.02, 'Note: All prices normalized to metal content basis for direct comparison\nStage numbers shown at base of bars', 
            ha='right', va='bottom', transform=ax.transAxes, fontsize=10, style='italic',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Save the figure
    output_path = figure_dir / "metal_content_prices_summary_2022.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Metal content price summary saved: {output_path}")

def create_cumulative_cost_comparison():
    """Create cumulative cost comparison showing CAPEX and OPEX staggered by stage"""
    
    # Get project directories
    project_root = Path(__file__).parent.parent.parent.parent
    figure_dir = project_root / "transport-outputs" / "figures" / "cost_price_comparisons"
    figure_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the cost data (final versions only)
    file_path = project_root / "transport-outputs" / "data" / "Final_Price_and_Costs_RP.xlsx"
    
    new_capex = pd.read_excel(file_path, sheet_name='CapEx_final')
    new_opex = pd.read_excel(file_path, sheet_name='OpEx_final')
    
    # Clean the data
    new_capex['reference_mineral'] = new_capex['reference_mineral'].fillna(method='ffill')
    new_opex['reference_mineral'] = new_opex['reference_mineral'].fillna(method='ffill')
    
    # Harmonize stage names
    new_capex = harmonize_stage_names(new_capex)
    new_opex = harmonize_stage_names(new_opex)
    
    # Filter for 2022 data and clean
    capex_2022 = new_capex[new_capex['stage'].notna()].copy()
    opex_2022 = new_opex[new_opex['stage'].notna()].copy()
    
    # Get unique minerals
    minerals = capex_2022['reference_mineral'].unique()
    
    # Create figure with subplots for each mineral
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()
    
    # Colors for CAPEX and OPEX
    capex_color = '#1f77b4'  # Blue
    opex_color = '#ff7f0e'   # Orange
    
    for i, mineral in enumerate(minerals):
        if i >= len(axes):
            break
        
        # Get data for this mineral
        mineral_capex = capex_2022[capex_2022['reference_mineral'] == mineral].copy()
        mineral_opex = opex_2022[opex_2022['reference_mineral'] == mineral].copy()
        
        # Merge CAPEX and OPEX data
        cost_data = []
        for _, capex_row in mineral_capex.iterrows():
            stage = capex_row['stage']
            capex_val = capex_row[2022] if pd.notna(capex_row[2022]) else 0
            
            # Find corresponding OPEX
            opex_row = mineral_opex[mineral_opex['stage'] == stage]
            opex_val = opex_row[2022].iloc[0] if not opex_row.empty and pd.notna(opex_row[2022].iloc[0]) else 0
            
            cost_data.append({
                'stage': stage,
                'capex': capex_val,
                'opex': opex_val,
                'total': capex_val + opex_val
            })
        
        if not cost_data:
            axes[i].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[i].transAxes)
            axes[i].set_title(f'{mineral.title()}', fontsize=14, fontweight='bold')
            continue
        
        # Sort by stage order (assuming stages follow a logical sequence)
        cost_df = pd.DataFrame(cost_data)
        
        # Calculate cumulative positions (staggered bars)
        cumulative_bottom = 0
        stage_positions = []
        stage_labels = []
        
        for j, row in cost_df.iterrows():
            stage_num = row['stage'].replace('Stage ', '')
            stage_labels.append(stage_num)
            
            # CAPEX bar (bottom part)
            if row['capex'] > 0:
                axes[i].bar(j, row['capex'], bottom=cumulative_bottom, 
                           color=capex_color, alpha=0.8, label='CAPEX' if j == 0 else "", 
                           edgecolor='black', linewidth=0.5)
                
                # Add CAPEX label
                axes[i].text(j, cumulative_bottom + row['capex']/2, 
                           f'{row["capex"]:.0f}', ha='center', va='center', 
                           fontsize=9, fontweight='bold', color='white')
            
            # OPEX bar (top part)
            if row['opex'] > 0:
                axes[i].bar(j, row['opex'], bottom=cumulative_bottom + row['capex'], 
                           color=opex_color, alpha=0.8, label='OPEX' if j == 0 else "",
                           edgecolor='black', linewidth=0.5)
                
                # Add OPEX label
                axes[i].text(j, cumulative_bottom + row['capex'] + row['opex']/2, 
                           f'{row["opex"]:.0f}', ha='center', va='center', 
                           fontsize=9, fontweight='bold', color='white')
            
            # Update cumulative bottom for next stage
            cumulative_bottom += row['total']
            stage_positions.append(j)
        
        # Customize subplot
        axes[i].set_title(f'{mineral.title()} - Cumulative Processing Costs 2022', 
                         fontsize=14, fontweight='bold')
        axes[i].set_xlabel('Processing Stage', fontsize=12)
        axes[i].set_ylabel('Cumulative Cost (USD/tonne)', fontsize=12)
        axes[i].set_xticks(stage_positions)
        axes[i].set_xticklabels(stage_labels, fontsize=11, fontweight='bold')
        
        # Add total cost within the plot area (near the top)
        if cumulative_bottom > 0:
            # Position at 90% of the plot height to avoid overlapping with title
            y_position = cumulative_bottom * 0.9
            axes[i].text(len(cost_data)/2 - 0.5, y_position, 
                        f'Total: ${cumulative_bottom:,.0f}', ha='center', va='center', 
                        fontsize=12, fontweight='bold', 
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        # Add grid and legend
        axes[i].grid(axis='y', alpha=0.3)
        axes[i].set_axisbelow(True)
        if i == 0:  # Add legend only to first subplot
            axes[i].legend(loc='upper left')
    
    # Remove empty subplots
    for i in range(len(minerals), len(axes)):
        fig.delaxes(axes[i])
    
    plt.suptitle('Cumulative Processing Costs: CAPEX and OPEX Staggered by Stage (2022)\n(Each stage builds upon previous stages)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    # Save the figure
    output_path = figure_dir / "cumulative_costs_staggered_2022.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Cumulative cost comparison saved: {output_path}")
    
    # Create a summary comparison showing total costs
    create_total_cost_summary(minerals, capex_2022, opex_2022, figure_dir)

def create_total_cost_summary(minerals, capex_2022, opex_2022, figure_dir):
    """Create a summary showing total final costs for each mineral"""
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    mineral_totals = []
    for mineral in minerals:
        mineral_capex = capex_2022[capex_2022['reference_mineral'] == mineral]
        mineral_opex = opex_2022[opex_2022['reference_mineral'] == mineral]
        
        total_capex = mineral_capex[2022].sum()
        total_opex = mineral_opex[2022].sum()
        total_cost = total_capex + total_opex
        
        mineral_totals.append({
            'mineral': mineral,
            'capex': total_capex,
            'opex': total_opex,
            'total': total_cost
        })
    
    # Sort by total cost
    mineral_totals.sort(key=lambda x: x['total'], reverse=True)
    
    # Create stacked bar chart
    minerals_sorted = [item['mineral'] for item in mineral_totals]
    capex_values = [item['capex'] for item in mineral_totals]
    opex_values = [item['opex'] for item in mineral_totals]
    
    x_pos = np.arange(len(minerals_sorted))
    
    # Create stacked bars
    bars1 = ax.bar(x_pos, capex_values, label='CAPEX', color='#1f77b4', alpha=0.8)
    bars2 = ax.bar(x_pos, opex_values, bottom=capex_values, label='OPEX', color='#ff7f0e', alpha=0.8)
    
    # Add value labels
    for i, (capex, opex, total) in enumerate(zip(capex_values, opex_values, [item['total'] for item in mineral_totals])):
        if capex > 0:
            ax.text(i, capex/2, f'${capex:,.0f}', ha='center', va='center', 
                   fontweight='bold', color='white')
        if opex > 0:
            ax.text(i, capex + opex/2, f'${opex:,.0f}', ha='center', va='center', 
                   fontweight='bold', color='white')
        
        # Total at top
        ax.text(i, total * 1.02, f'${total:,.0f}', ha='center', va='bottom', 
               fontweight='bold', fontsize=11)
    
    # Customize the chart
    ax.set_xlabel('Mineral', fontsize=14, fontweight='bold')
    ax.set_ylabel('Total Processing Cost (USD/tonne)', fontsize=14, fontweight='bold')
    ax.set_title('Total Processing Costs by Mineral (2022)\nCAPEX + OPEX for Complete Processing Chain', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([m.title() for m in minerals_sorted], fontsize=12)
    
    # Add legend and grid
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # Save the figure
    output_path = figure_dir / "total_processing_costs_summary_2022.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Total cost summary saved: {output_path}")

if __name__ == "__main__":
    main()
    # Also create the metal content price comparison
    create_metal_content_price_comparison()
    # And create the cumulative cost comparison
    create_cumulative_cost_comparison()