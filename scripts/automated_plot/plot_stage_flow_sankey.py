"""
Create enhanced Sankey diagrams showing stage-to-stage flow of minerals through processing
"""

import os
import sys
import pandas as pd
import plotly.graph_objects as go
import json
from pathlib import Path
import numpy as np

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from plot_config import reference_minerals, reference_mineral_colormap, get_goal_from_scenario, mineral_processing_stages
from global_constraint_dashboards import get_mid_scenarios_symmetric

def get_stage_info(mineral, stage):
    """Get processing type information for a mineral/stage combination"""
    if mineral in mineral_processing_stages:
        stages_info = mineral_processing_stages[mineral]["stages"]
        if stage in stages_info:
            return stages_info[stage]["type"]
    return "Unknown"

def analyze_mineral_stages(df):
    """Analyze which stages exist for each mineral"""
    df_products = df[df['processing_stage'] > 0].copy()
    
    print("\n=== MINERAL STAGE ANALYSIS ===")
    for mineral in sorted(df_products['reference_mineral'].unique()):
        mineral_data = df_products[df_products['reference_mineral'] == mineral]
        stages = sorted(mineral_data['processing_stage'].unique())
        
        print(f"\n{mineral.upper()}:")
        print(f"  Stages: {stages}")
        
        # Check processing types
        for stage in stages:
            stage_type = get_stage_info(mineral, stage)
            production = mineral_data[mineral_data['processing_stage'] == stage]['production_tonnes'].sum() / 1e6
            revenue = mineral_data[mineral_data['processing_stage'] == stage]['revenue_usd'].sum() / 1e9
            print(f"    Stage {stage} ({stage_type}): {production:.2f} Mt, ${revenue:.2f}B")

def create_stage_flow_sankey(df_analysis, goal_type, constraint, metric='tonnage'):
    """
    Create a Sankey diagram showing stage-to-stage flow of minerals
    
    Args:
        df_analysis: DataFrame with analysis data
        goal_type: 'bau', 'early_refining', or 'precursor'
        constraint: e.g., 'country_unconstrained'
        metric: 'tonnage' or 'revenue' for flow width
    """
    
    # Filter data
    df_goal = df_analysis[
        (df_analysis['goal_type'] == goal_type) & 
        (df_analysis['processing_stage'] > 0)  # Exclude stage 0
    ].copy()
    
    if df_goal.empty:
        return None
    
    # Get all unique stages and minerals
    all_stages = sorted(df_goal['processing_stage'].unique())
    all_minerals = sorted(df_goal['reference_mineral'].unique())
    
    # Create node structure
    nodes = []
    node_labels = []
    node_colors = []
    node_x = []  # X position for layout
    node_y = []  # Y position for layout
    node_lookup = {}  # Maps (mineral, stage) to node index
    
    # Stage positions (normalized 0-1)
    stage_x_positions = {}
    for i, stage in enumerate(all_stages):
        stage_x_positions[stage] = i / (len(all_stages) - 1) if len(all_stages) > 1 else 0.5
    
    # Create nodes for each mineral/stage combination that exists
    y_offset = 0
    y_spacing = 1.0 / (len(all_minerals) + 1)
    
    for mineral_idx, mineral in enumerate(all_minerals):
        mineral_stages = sorted(df_goal[df_goal['reference_mineral'] == mineral]['processing_stage'].unique())
        
        for stage in mineral_stages:
            node_idx = len(nodes)
            nodes.append((mineral, stage))
            
            # Get stage info
            stage_type = get_stage_info(mineral, stage)
            node_labels.append(f"{mineral.title()}<br>Stage {stage}<br>({stage_type})")
            
            # Color by mineral
            node_colors.append(reference_mineral_colormap.get(mineral, '#999999'))
            
            # Position
            node_x.append(stage_x_positions[stage])
            node_y.append((mineral_idx + 1) * y_spacing)
            
            # Store lookup
            node_lookup[(mineral, stage)] = node_idx
    
    # Add "Exit/Sales" nodes for each stage
    exit_node_lookup = {}
    for stage in all_stages:
        node_idx = len(nodes)
        nodes.append(('exit', stage))
        node_labels.append(f"Sales<br>Stage {stage}")
        node_colors.append('#cccccc')  # Gray for exit nodes
        node_x.append(stage_x_positions[stage])
        node_y.append(1.0)  # Bottom position
        exit_node_lookup[stage] = node_idx
    
    # Create links
    source = []
    target = []
    value = []
    link_colors = []
    link_labels = []
    
    # For each mineral, track flow through stages
    for mineral in all_minerals:
        mineral_data = df_goal[df_goal['reference_mineral'] == mineral]
        mineral_stages = sorted(mineral_data['processing_stage'].unique())
        
        # Calculate production at each stage
        stage_production = {}
        stage_revenue = {}
        for stage in mineral_stages:
            stage_data = mineral_data[mineral_data['processing_stage'] == stage]
            if metric == 'tonnage':
                stage_production[stage] = stage_data['production_tonnes'].sum() / 1e3  # Convert to kt
            else:  # revenue
                stage_revenue[stage] = stage_data['revenue_usd'].sum() / 1e6  # Convert to M$
        
        # Calculate actual exports using real data
        stage_exports = {}
        stage_imports = {}
        for stage in mineral_stages:
            stage_data = mineral_data[mineral_data['processing_stage'] == stage]
            stage_exports[stage] = stage_data['export_tonnes'].sum() / 1e3  # Convert to kt
            stage_imports[stage] = stage_data['import_tonnes'].sum() / 1e3  # Convert to kt
        
        # Create flows: show production at each stage and actual exports
        for i, stage in enumerate(mineral_stages):
            # Flow to sales (actual exports)
            if stage in exit_node_lookup and stage in stage_exports:
                if metric == 'tonnage':
                    exit_value = stage_exports.get(stage, 0)
                    unit = 'kt'
                else:
                    # Calculate export revenue proportionally
                    stage_prod = stage_production.get(stage, 0)
                    export_ratio = stage_exports.get(stage, 0) / (stage_prod + 1e-6)
                    exit_value = stage_revenue.get(stage, 0) * export_ratio
                    unit = 'M$'
                
                if exit_value > 0:
                    source.append(node_lookup[(mineral, stage)])
                    target.append(exit_node_lookup[stage])
                    value.append(exit_value)
                    link_colors.append(reference_mineral_colormap.get(mineral, '#999999') + '60')
                    link_labels.append(f"{mineral.title()} Stage {stage} Sales: {exit_value:.1f} {unit}")
        
        # Create conceptual flows between consecutive stages 
        # (material that could potentially flow, not actual tracked flows)
        for i in range(len(mineral_stages) - 1):
            current_stage = mineral_stages[i]
            next_stage = mineral_stages[i + 1]
            
            if (mineral, current_stage) in node_lookup and (mineral, next_stage) in node_lookup:
                if metric == 'tonnage':
                    # Ensure all stages are connected with meaningful flows
                    stage_prod = stage_production.get(current_stage, 0)
                    retained = stage_prod - stage_exports.get(current_stage, 0)
                    next_stage_prod = stage_production.get(next_stage, 0)
                    
                    # Use the minimum of retained material or next stage production
                    # but ensure minimum flow for visibility (at least 5kt or 10% of current production)
                    flow_value = max(min(retained, next_stage_prod), min(stage_prod * 0.1, 5))
                else:
                    stage_prod = stage_production.get(current_stage, 0)
                    next_stage_prod = stage_production.get(next_stage, 0)
                    export_ratio = stage_exports.get(current_stage, 0) / (stage_prod + 1e-6)
                    
                    # Calculate flow proportionally but ensure minimum visibility
                    base_flow = stage_revenue.get(current_stage, 0) * (1 - export_ratio)
                    next_stage_revenue = stage_revenue.get(next_stage, 0)
                    flow_value = max(min(base_flow, next_stage_revenue), stage_revenue.get(current_stage, 0) * 0.1)
                
                # Flow to next stage
                source.append(node_lookup[(mineral, current_stage)])
                target.append(node_lookup[(mineral, next_stage)])
                value.append(flow_value)
                link_colors.append(reference_mineral_colormap.get(mineral, '#999999') + '80')  # Add transparency
                unit = 'kt' if metric == 'tonnage' else 'M$'
                link_labels.append(f"{mineral.title()} {current_stage}→{next_stage}: {flow_value:.1f} {unit}")
                
                # Flow to exit/sales
                if current_stage in exit_node_lookup:
                    source.append(node_lookup[(mineral, current_stage)])
                    target.append(exit_node_lookup[current_stage])
                    value.append(exit_value)
                    link_colors.append(reference_mineral_colormap.get(mineral, '#999999') + '40')  # More transparent
                    link_labels.append(f"{mineral.title()} Stage {current_stage} Sales: {exit_value:.1f} {unit}")
        
        # Note: Final stage exports are already handled in the loop above
    
    # Convert colors to rgba format
    link_colors_rgba = []
    for color in link_colors:
        if len(color) == 9:  # Has alpha
            hex_color = color[:7]
            alpha = int(color[7:], 16) / 255
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            link_colors_rgba.append(f'rgba({r},{g},{b},{alpha:.2f})')
        else:
            link_colors_rgba.append(color)
    
    # Create Sankey figure
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=10,
            thickness=15,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors,
            x=node_x,
            y=node_y
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors_rgba,
            label=link_labels,
            hovertemplate='%{label}<extra></extra>'
        )
    )])
    
    # Update layout
    goal_title = goal_type.replace('_', ' ').title()
    constraint_title = constraint.replace('_', ' ').title()
    metric_title = "Production Flow (kt)" if metric == 'tonnage' else "Revenue Flow ($M)"
    
    fig.update_layout(
        title=dict(
            text=f"{metric_title}: {goal_title} - {constraint_title}<br><sub>Shows progression through processing stages and sales at each stage</sub>",
            font=dict(size=14)
        ),
        font=dict(size=10),
        height=700,
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    return fig

def main():
    """Generate enhanced stage flow Sankey diagrams"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Filter to mid scenarios
    df_mid = get_mid_scenarios_symmetric(df)
    df_mid['goal_type'] = df_mid['scenario'].apply(get_goal_from_scenario)
    
    # First, analyze mineral stages
    analyze_mineral_stages(df_mid)
    
    # Output directory
    figures_path = config['paths']['figures']
    output_dir = os.path.join(figures_path, 'stage_flow_sankey')
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n=== GENERATING STAGE FLOW SANKEY DIAGRAMS ===\n")
    
    # Generate for each constraint and scenario
    constraints = ['country_unconstrained', 'country_constrained', 
                  'region_unconstrained', 'region_constrained']
    
    for constraint in constraints:
        print(f"\nProcessing {constraint}...")
        
        df_constraint = df_mid[df_mid['constraint'] == constraint]
        
        # Generate for each goal and metric
        for goal in ['bau', 'early_refining', 'precursor']:
            for metric in ['tonnage', 'revenue']:
                fig = create_stage_flow_sankey(df_constraint, goal, constraint, metric=metric)
                if fig:
                    filename_base = f"stage_flow_{constraint}_{goal}_{metric}"
                    fig.write_html(os.path.join(output_dir, f"{filename_base}.html"))
                    fig.write_image(os.path.join(output_dir, f"{filename_base}.png"), width=1400, height=700)
                    print(f"  ✓ Created {filename_base}.html and .png")
    
    print(f"\n✓ All stage flow Sankey diagrams saved to: {output_dir}")

if __name__ == "__main__":
    main()