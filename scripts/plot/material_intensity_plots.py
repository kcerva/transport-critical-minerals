#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Material, Energy, and Water Intensity Plots

This script creates visualizations for material intensities from the 
mineral_extraction_country_intensities data, with support for future 
energy and water intensity visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import numpy as np
from mapping_properties import mineral_properties

# Get the mineral properties including colors
mineral_props = mineral_properties()

# Create mineral color mapping
MINERAL_COLORS = {
    'copper': '#f46d43',
    'cobalt': '#fdae61', 
    'manganese': '#fee08b',
    'lithium': '#c2a5cf',
    'graphite': '#66c2a5',
    'nickel': '#3288bd'
}

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def create_material_intensity_plot(excel_path=None, output_dir=None):
    """
    Create material intensity plot from the country material ratios data
    
    Parameters:
    -----------
    excel_path : str, optional
        Path to the Excel file. If None, uses default from config
    output_dir : str, optional
        Output directory for plots. If None, uses default from config
    """
    # Load configuration
    config = load_config()
    
    # Set paths
    if excel_path is None:
        excel_path = os.path.join(
            config['paths']['data'],
            'mineral_extraction_country_intensities (final units w Co edits).xlsx'
        )
    
    if output_dir is None:
        output_dir = os.path.join(config['paths']['figures'], 'intensities', 'material')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the data
    print(f"Reading data from: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='Country material ratios')
    
    # Filter for the aggregate_ratio column
    ratio_col = 'aggregate_ratio (metal content for stage 1 and mass of relevant output for the other stages)'
    
    # Group by mineral and stage to calculate mean across countries
    grouped = df.groupby(['reference_mineral', 'processing_stage'])[ratio_col].mean().reset_index()
    grouped.columns = ['mineral', 'stage', 'material_intensity']
    
    # Exclude Cobalt stage 2
    grouped = grouped[~((grouped['mineral'] == 'cobalt') & (grouped['stage'] == 2.0))]
    
    # Create simplified labels for the bars
    # Format stage numbers: integers for whole numbers, one decimal for others
    grouped['stage_formatted'] = grouped['stage'].apply(lambda x: str(int(x)) if x % 1 == 0 else f'{x:.1f}')
    grouped['label'] = grouped['mineral'].str.title() + ' - ' + grouped['stage_formatted']
    
    # Sort by mineral name and stage for consistent ordering
    grouped = grouped.sort_values(['mineral', 'stage'])
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # Create horizontal bars
    y_positions = np.arange(len(grouped))
    bars = ax.barh(y_positions, grouped['material_intensity'])
    
    # Color bars by mineral
    for i, (idx, row) in enumerate(grouped.iterrows()):
        mineral = row['mineral'].lower()
        color = MINERAL_COLORS.get(mineral, '#999999')
        bars[i].set_color(color)
        bars[i].set_alpha(0.8)
        
        # Add value labels at the end of each bar
        value = row['material_intensity']
        ax.text(value + 0.05 * value, i, f'{value:.1f}', 
                va='center', fontsize=9, fontweight='bold')
    
    # Customize the plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels(grouped['label'])
    ax.set_ylabel('Mineral and stage number', fontsize=12, fontweight='bold')
    ax.set_xlabel('Material Intensity (kg product/kg of metal or mineral in ore)', fontsize=12, fontweight='bold')
    ax.set_title('Material Intensity by Mineral and Processing Stage\n(Average across countries)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Add grid for better readability
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Adjust x-axis limits to ensure all text is visible
    current_xlim = ax.get_xlim()
    ax.set_xlim(0, current_xlim[1] * 1.1)  # Add 10% padding to the right
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'material_intensity_by_mineral_stage.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved material intensity plot: {output_path}")
    
    # Also save as PDF
    output_path_pdf = os.path.join(output_dir, 'material_intensity_by_mineral_stage.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"✓ Saved material intensity plot (PDF): {output_path_pdf}")
    
    plt.close()
    
    # Create a summary table
    create_intensity_summary_table(grouped, output_dir, 'material')
    
    return grouped

def create_intensity_summary_table(data, output_dir, intensity_type='material'):
    """
    Create a summary table of intensities by mineral
    
    Parameters:
    -----------
    data : DataFrame
        Grouped data with mineral, stage, and intensity values
    output_dir : str
        Output directory for the summary
    intensity_type : str
        Type of intensity ('material', 'energy', or 'water')
    """
    # Pivot the data to create a table format
    pivot = data.pivot(index='stage', columns='mineral', values=f'{intensity_type}_intensity')
    
    # Save as CSV
    output_path = os.path.join(output_dir, f'{intensity_type}_intensity_summary.csv')
    pivot.to_csv(output_path)
    print(f"✓ Saved {intensity_type} intensity summary: {output_path}")
    
    # Print summary statistics
    print(f"\n=== {intensity_type.title()} Intensity Summary ===")
    print(f"Average {intensity_type} intensity by mineral:")
    for mineral in pivot.columns:
        avg_intensity = pivot[mineral].mean()
        print(f"  {mineral.title()}: {avg_intensity:.2f}")

def create_water_intensity_plot(excel_path=None, output_dir=None):
    """
    Create water intensity plot from the country water ratios data
    
    Parameters:
    -----------
    excel_path : str, optional
        Path to the Excel file. If None, uses default from config
    output_dir : str, optional
        Output directory for plots. If None, uses default from config
    """
    # Load configuration
    config = load_config()
    
    # Set paths
    if excel_path is None:
        excel_path = os.path.join(
            config['paths']['data'],
            'mineral_extraction_country_intensities (final units w Co edits).xlsx'
        )
    
    if output_dir is None:
        output_dir = os.path.join(config['paths']['figures'], 'intensities', 'water')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the data
    print(f"Reading water data from: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='Country water ratios')
    
    # Filter for the water intensity column
    intensity_col = 'water intensity (m3/kg)'
    
    # Group by mineral and stage to calculate mean across countries
    grouped = df.groupby(['reference_mineral', 'processing_stage'])[intensity_col].mean().reset_index()
    grouped.columns = ['mineral', 'stage', 'water_intensity']
    
    # Exclude Cobalt stage 2
    grouped = grouped[~((grouped['mineral'] == 'cobalt') & (grouped['stage'] == 2.0))]
    
    # Create simplified labels for the bars
    # Format stage numbers: integers for whole numbers, one decimal for others
    grouped['stage_formatted'] = grouped['stage'].apply(lambda x: str(int(x)) if x % 1 == 0 else f'{x:.1f}')
    grouped['label'] = grouped['mineral'].str.title() + ' - ' + grouped['stage_formatted']
    
    # Sort by mineral name and stage for consistent ordering
    grouped = grouped.sort_values(['mineral', 'stage'])
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # Create horizontal bars
    y_positions = np.arange(len(grouped))
    bars = ax.barh(y_positions, grouped['water_intensity'])
    
    # Color bars by mineral
    for i, (idx, row) in enumerate(grouped.iterrows()):
        mineral = row['mineral'].lower()
        color = MINERAL_COLORS.get(mineral, '#999999')
        bars[i].set_color(color)
        bars[i].set_alpha(0.8)
        
        # Add value labels at the end of each bar
        value = row['water_intensity']
        # Use smaller offset for water values since they're much smaller
        ax.text(value + 0.01 * max(grouped['water_intensity']), i, f'{value:.2f}', 
                va='center', fontsize=9, fontweight='bold')
    
    # Customize the plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels(grouped['label'])
    ax.set_ylabel('Mineral and stage number', fontsize=12, fontweight='bold')
    ax.set_xlabel('Water intensity (m³/kg)', fontsize=12, fontweight='bold')
    ax.set_title('Water Intensity by Mineral and Processing Stage\n(Average across countries)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Add grid for better readability
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Adjust x-axis limits to ensure all text is visible
    current_xlim = ax.get_xlim()
    ax.set_xlim(0, current_xlim[1] * 1.1)  # Add 10% padding to the right
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'water_intensity_by_mineral_stage.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved water intensity plot: {output_path}")
    
    # Also save as PDF
    output_path_pdf = os.path.join(output_dir, 'water_intensity_by_mineral_stage.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"✓ Saved water intensity plot (PDF): {output_path_pdf}")
    
    plt.close()
    
    # Create a summary table
    create_intensity_summary_table(grouped, output_dir, 'water')
    
    return grouped

def create_electricity_intensity_plot(excel_path=None, output_dir=None):
    """
    Create electricity intensity plot from the country electricity ratios data
    
    Parameters:
    -----------
    excel_path : str, optional
        Path to the Excel file. If None, uses default from config
    output_dir : str, optional
        Output directory for plots. If None, uses default from config
    """
    # Load configuration
    config = load_config()
    
    # Set paths
    if excel_path is None:
        excel_path = os.path.join(
            config['paths']['data'],
            'mineral_extraction_country_intensities (final units w Co edits).xlsx'
        )
    
    if output_dir is None:
        output_dir = os.path.join(config['paths']['figures'], 'intensities', 'electricity')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the data
    print(f"Reading electricity data from: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='Country electricity ratios')
    
    # Filter for the electricity intensity column
    intensity_col = 'electricity intensity (kWh/kg)'
    
    # Group by mineral and stage to calculate mean across countries
    grouped = df.groupby(['reference_mineral', 'processing_stage'])[intensity_col].mean().reset_index()
    grouped.columns = ['mineral', 'stage', 'electricity_intensity']
    
    # Exclude Cobalt stage 2
    grouped = grouped[~((grouped['mineral'] == 'cobalt') & (grouped['stage'] == 2.0))]
    
    # Create simplified labels for the bars
    # Format stage numbers: integers for whole numbers, one decimal for others
    grouped['stage_formatted'] = grouped['stage'].apply(lambda x: str(int(x)) if x % 1 == 0 else f'{x:.1f}')
    grouped['label'] = grouped['mineral'].str.title() + ' - ' + grouped['stage_formatted']
    
    # Sort by mineral name and stage for consistent ordering
    grouped = grouped.sort_values(['mineral', 'stage'])
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # Create horizontal bars
    y_positions = np.arange(len(grouped))
    bars = ax.barh(y_positions, grouped['electricity_intensity'])
    
    # Color bars by mineral
    for i, (idx, row) in enumerate(grouped.iterrows()):
        mineral = row['mineral'].lower()
        color = MINERAL_COLORS.get(mineral, '#999999')
        bars[i].set_color(color)
        bars[i].set_alpha(0.8)
        
        # Add value labels at the end of each bar
        value = row['electricity_intensity']
        ax.text(value + 0.05 * value, i, f'{value:.1f}', 
                va='center', fontsize=9, fontweight='bold')
    
    # Customize the plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels(grouped['label'])
    ax.set_ylabel('Mineral and stage number', fontsize=12, fontweight='bold')
    ax.set_xlabel('Electricity intensity (kWh/kg)', fontsize=12, fontweight='bold')
    ax.set_title('Electricity Intensity by Mineral and Processing Stage\n(Average across countries)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Add grid for better readability
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Adjust x-axis limits to ensure all text is visible
    current_xlim = ax.get_xlim()
    ax.set_xlim(0, current_xlim[1] * 1.1)  # Add 10% padding to the right
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'electricity_intensity_by_mineral_stage.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved electricity intensity plot: {output_path}")
    
    # Also save as PDF
    output_path_pdf = os.path.join(output_dir, 'electricity_intensity_by_mineral_stage.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"✓ Saved electricity intensity plot (PDF): {output_path_pdf}")
    
    plt.close()
    
    # Create a summary table
    create_intensity_summary_table(grouped, output_dir, 'electricity')
    
    return grouped

def create_fuel_intensity_plot(excel_path=None, output_dir=None, petroleum_energy_content=12.0):
    """
    Create fuel intensity plot from the country fuel ratios data
    Shows stacked bars for different fuel types
    
    Parameters:
    -----------
    excel_path : str, optional
        Path to the Excel file. If None, uses default from config
    output_dir : str, optional
        Output directory for plots. If None, uses default from config
    petroleum_energy_content : float
        Energy content of petroleum in kWh/kg (default: 12.0)
        Used to convert petroleum intensity from kg/kg to kWh/kg
    """
    # Load configuration
    config = load_config()
    
    # Set paths
    if excel_path is None:
        excel_path = os.path.join(
            config['paths']['data'],
            'mineral_extraction_country_intensities (final units w Co edits).xlsx'
        )
    
    if output_dir is None:
        output_dir = os.path.join(config['paths']['figures'], 'intensities', 'fuel')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the data
    print(f"Reading fuel data from: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='Country fuel ratios')
    
    # Define fuel columns and their units
    fuel_columns = {
        'natural gas intensity (kWh/kg)': 'Natural Gas',
        'diesel intensity (kWh/kg)': 'Diesel',
        'heat intensity (kWh/kg)': 'Heat',
        'petroleum intensity (kg/kg)': 'Petroleum',
        'coke intensity (kg/kg)': 'Coke'
    }
    
    # Convert petroleum and coke from kg/kg to kWh/kg
    # Note: Using petroleum_energy_content for petroleum, and 8.0 kWh/kg for coke
    df['petroleum intensity (kWh/kg)'] = df['petroleum intensity (kg/kg)'] * petroleum_energy_content
    df['coke intensity (kWh/kg)'] = df['coke intensity (kg/kg)'] * 8.0  # Typical coke energy content
    
    # Update fuel columns to use converted values
    fuel_columns_converted = {
        'natural gas intensity (kWh/kg)': 'Natural Gas',
        'diesel intensity (kWh/kg)': 'Diesel',
        'heat intensity (kWh/kg)': 'Heat',
        'petroleum intensity (kWh/kg)': 'Petroleum',
        'coke intensity (kWh/kg)': 'Coke'
    }
    
    # Group by mineral and stage to calculate mean across countries
    grouped_data = []
    for col, fuel_name in fuel_columns_converted.items():
        temp_df = df.groupby(['reference_mineral', 'processing_stage'])[col].mean().reset_index()
        temp_df.columns = ['mineral', 'stage', 'intensity']
        temp_df['fuel'] = fuel_name
        grouped_data.append(temp_df)
    
    # Combine all fuel data
    all_fuels = pd.concat(grouped_data, ignore_index=True)
    
    # Pivot to get fuel types as columns
    pivot_df = all_fuels.pivot_table(
        index=['mineral', 'stage'], 
        columns='fuel', 
        values='intensity',
        fill_value=0
    ).reset_index()
    
    # Exclude Cobalt stage 2
    pivot_df = pivot_df[~((pivot_df['mineral'] == 'cobalt') & (pivot_df['stage'] == 2.0))]
    
    # Create labels
    # Format stage numbers: integers for whole numbers, one decimal for others
    pivot_df['stage_formatted'] = pivot_df['stage'].apply(lambda x: str(int(x)) if x % 1 == 0 else f'{x:.1f}')
    pivot_df['label'] = pivot_df['mineral'].str.title() + ' - ' + pivot_df['stage_formatted']
    
    # Sort by mineral name and stage
    pivot_df = pivot_df.sort_values(['mineral', 'stage'])
    
    # Define colors for different fuel types
    fuel_colors = {
        'Natural Gas': '#1f77b4',  # Blue
        'Diesel': '#ff7f0e',        # Orange
        'Heat': '#2ca02c',          # Green
        'Petroleum': '#d62728',     # Red
        'Coke': '#9467bd'           # Purple
    }
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # Prepare data for stacked bars
    y_positions = np.arange(len(pivot_df))
    fuel_types = ['Natural Gas', 'Diesel', 'Heat', 'Petroleum', 'Coke']
    
    # Create stacked horizontal bars
    left_positions = np.zeros(len(pivot_df))
    
    for fuel in fuel_types:
        if fuel in pivot_df.columns:
            values = pivot_df[fuel].values
            bars = ax.barh(y_positions, values, left=left_positions, 
                          label=fuel, color=fuel_colors[fuel], alpha=0.8)
            
            # Add value labels for each segment if value > 0
            for i, (bar, value) in enumerate(zip(bars, values)):
                if value > 0.01:  # Only show label if value is significant
                    # Position text in the middle of the bar segment
                    text_x = left_positions[i] + value / 2
                    ax.text(text_x, i, f'{value:.1f}', 
                           va='center', ha='center', fontsize=8, fontweight='bold',
                           color='white' if value > 0.5 else 'black')
            
            left_positions += values
    
    # Customize the plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels(pivot_df['label'])
    ax.set_ylabel('Mineral and stage number', fontsize=12, fontweight='bold')
    ax.set_xlabel('Fuel Intensity (kWh/kg)', fontsize=12, fontweight='bold')
    ax.set_title('Fuel Intensity by Mineral and Processing Stage\n(Average across countries, all fuel types)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Fuel Type')
    
    # Add grid for better readability
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Adjust x-axis limits to ensure all text is visible
    current_xlim = ax.get_xlim()
    ax.set_xlim(0, current_xlim[1] * 1.1)  # Add 10% padding to the right
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'fuel_intensity_by_mineral_stage.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved fuel intensity plot: {output_path}")
    print(f"  Note: Petroleum converted using {petroleum_energy_content} kWh/kg")
    print(f"  Note: Coke converted using 8.0 kWh/kg")
    
    # Also save as PDF
    output_path_pdf = os.path.join(output_dir, 'fuel_intensity_by_mineral_stage.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"✓ Saved fuel intensity plot (PDF): {output_path_pdf}")
    
    plt.close()
    
    # Create a summary table showing total fuel intensity by mineral
    pivot_df['total_fuel_intensity'] = pivot_df[fuel_types].sum(axis=1)
    summary = pivot_df.groupby('mineral')['total_fuel_intensity'].mean()
    
    # Save summary
    summary_path = os.path.join(output_dir, 'fuel_intensity_summary.csv')
    summary.to_csv(summary_path)
    print(f"✓ Saved fuel intensity summary: {summary_path}")
    
    print(f"\n=== Fuel Intensity Summary ===")
    print(f"Average total fuel intensity by mineral:")
    for mineral, intensity in summary.items():
        print(f"  {mineral.title()}: {intensity:.2f} kWh/kg")
    
    return pivot_df

if __name__ == "__main__":
    # Run all intensity plots
    print("Creating material intensity plot...")
    create_material_intensity_plot()
    
    print("\nCreating water intensity plot...")
    create_water_intensity_plot()
    
    print("\nCreating electricity intensity plot...")
    create_electricity_intensity_plot()
    
    print("\nCreating fuel intensity plot...")
    print("Note: For petroleum intensity conversion from kg/kg to kWh/kg,")
    print("using default value of 12.0 kWh/kg. Please provide correct conversion factor if different.")
    create_fuel_intensity_plot()