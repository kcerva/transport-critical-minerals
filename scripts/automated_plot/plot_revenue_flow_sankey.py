"""
Create Sankey diagrams showing revenue flows across processing stages and minerals
"""

import os
import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from plot_config import reference_minerals, reference_mineral_colormap, get_goal_from_scenario
from global_constraint_dashboards import get_mid_scenarios_symmetric

def categorize_stage(stage):
    """Categorize processing stage into broader categories"""
    if stage <= 1.5:
        return 'Beneficiation'
    elif stage <= 3.5:
        return 'Early Refining'
    else:
        return 'Precursor'

def create_revenue_flow_sankey(df_analysis, goal_type, constraint, show_stage_groups=True):
    """
    Create a Sankey diagram showing revenue flows from minerals through processing stages
    
    Args:
        df_analysis: DataFrame with analysis data
        goal_type: 'bau', 'early_refining', or 'precursor'
        constraint: e.g., 'country_unconstrained'
        show_stage_groups: If True, shows stage groupings; if False, shows individual stages
    """
    
    # Filter data
    df_goal = df_analysis[
        (df_analysis['goal_type'] == goal_type) & 
        (df_analysis['processing_stage'] > 0)  # Exclude stage 0
    ].copy()
    
    if df_goal.empty:
        return None
    
    # Prepare nodes and links
    minerals = sorted(df_goal['reference_mineral'].unique())
    
    if show_stage_groups:
        # Aggregate by stage categories
        df_goal['stage_category'] = df_goal['processing_stage'].apply(categorize_stage)
        stage_revenue = df_goal.groupby(['reference_mineral', 'stage_category'])['revenue_usd'].sum().reset_index()
        stages = ['Beneficiation', 'Early Refining', 'Precursor']
    else:
        # Use individual stages
        stage_revenue = df_goal.groupby(['reference_mineral', 'processing_stage'])['revenue_usd'].sum().reset_index()
        stage_revenue.rename(columns={'processing_stage': 'stage_category'}, inplace=True)
        stages = sorted(df_goal['processing_stage'].unique())
    
    # Create node labels
    node_labels = []
    node_colors = []
    node_positions = {}
    
    # Add mineral nodes (source)
    for i, mineral in enumerate(minerals):
        node_labels.append(mineral.title())
        node_colors.append(reference_mineral_colormap.get(mineral, '#999999'))
        node_positions[f"mineral_{mineral}"] = len(node_labels) - 1
    
    # Add stage nodes (target)
    stage_colors = {
        'Beneficiation': '#8dd3c7',
        'Early Refining': '#ffffb3', 
        'Precursor': '#bebada'
    }
    
    for stage in stages:
        node_labels.append(str(stage) if isinstance(stage, float) else stage)
        if show_stage_groups:
            node_colors.append(stage_colors.get(stage, '#cccccc'))
        else:
            node_colors.append(stage_colors.get(categorize_stage(stage), '#cccccc'))
        node_positions[f"stage_{stage}"] = len(node_labels) - 1
    
    # Create links
    source = []
    target = []
    value = []
    link_colors = []
    link_labels = []
    
    for _, row in stage_revenue.iterrows():
        mineral = row['reference_mineral']
        stage = row['stage_category']
        revenue = row['revenue_usd']
        
        if revenue > 0:  # Only show positive flows
            source.append(node_positions[f"mineral_{mineral}"])
            target.append(node_positions[f"stage_{stage}"])
            value.append(revenue / 1e6)  # Convert to millions
            
            # Use mineral color with rgba format for transparency
            hex_color = reference_mineral_colormap.get(mineral, '#999999')
            # Convert hex to rgba with transparency
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            link_colors.append(f'rgba({r},{g},{b},0.4)')
            link_labels.append(f"{mineral.title()} → {stage}: ${revenue/1e6:.1f}M")
    
    # Calculate total revenue
    total_revenue = sum(value)
    
    # Create Sankey figure
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors,
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
            label=link_labels,
            hovertemplate='%{label}<br>Revenue: $%{value:.1f}M<br>%{value:.1f}% of total<extra></extra>'
        )
    )])
    
    # Update layout
    goal_title = goal_type.replace('_', ' ').title()
    constraint_title = constraint.replace('_', ' ').title()
    
    fig.update_layout(
        title=dict(
            text=f"Revenue Flows: {goal_title} - {constraint_title}<br><sub>Total Revenue: ${total_revenue:.1f}M</sub>",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=500,
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    return fig

def create_comparative_sankey_figure(df_analysis, constraint):
    """Create a figure with three Sankey diagrams comparing scenarios"""
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.33, 0.33, 0.34],
        vertical_spacing=0.05,
        subplot_titles=(
            'BAU (Business as Usual)',
            'Early Refining', 
            'Precursor Related Product'
        )
    )
    
    goals = ['bau', 'early_refining', 'precursor']
    
    # This approach won't work directly with Sankey in subplots
    # Instead, we'll create separate figures
    figs = []
    for goal in goals:
        sankey_fig = create_revenue_flow_sankey(df_analysis, goal, constraint, show_stage_groups=True)
        if sankey_fig:
            figs.append(sankey_fig)
    
    return figs

def create_mineral_focus_sankey(df_analysis, mineral, constraint):
    """Create a Sankey focused on a single mineral across all scenarios"""
    
    # Filter to specific mineral
    df_mineral = df_analysis[
        (df_analysis['reference_mineral'] == mineral) &
        (df_analysis['processing_stage'] > 0)
    ].copy()
    
    if df_mineral.empty:
        return None
    
    # Create nodes: Goals → Stages
    goals = ['bau', 'early_refining', 'precursor']
    stages = sorted(df_mineral['processing_stage'].unique())
    
    node_labels = []
    node_colors = []
    node_positions = {}
    
    # Goal nodes (source)
    goal_colors = {'bau': '#1f77b4', 'early_refining': '#ff7f0e', 'precursor': '#2ca02c'}
    for goal in goals:
        node_labels.append(goal.replace('_', ' ').title())
        node_colors.append(goal_colors[goal])
        node_positions[f"goal_{goal}"] = len(node_labels) - 1
    
    # Stage nodes (target)
    for stage in stages:
        node_labels.append(f"Stage {stage}")
        node_colors.append('#cccccc')
        node_positions[f"stage_{stage}"] = len(node_labels) - 1
    
    # Create links
    source = []
    target = []
    value = []
    link_labels = []
    
    for goal in goals:
        goal_data = df_mineral[df_mineral['goal_type'] == goal]
        stage_revenue = goal_data.groupby('processing_stage')['revenue_usd'].sum()
        
        for stage, revenue in stage_revenue.items():
            if revenue > 0:
                source.append(node_positions[f"goal_{goal}"])
                target.append(node_positions[f"stage_{stage}"])
                value.append(revenue / 1e6)
                link_labels.append(f"{goal.title()} → Stage {stage}: ${revenue/1e6:.1f}M")
    
    # Create figure
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            label=link_labels
        )
    )])
    
    fig.update_layout(
        title=f"{mineral.title()} Revenue Flows by Scenario - {constraint.replace('_', ' ').title()}",
        height=400
    )
    
    return fig

def main():
    """Generate revenue flow Sankey diagrams"""
    
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
    
    # Output directory - use figures folder for single plots
    figures_path = config['paths']['figures']
    output_dir = os.path.join(figures_path, 'revenue_flow_sankey')
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== GENERATING REVENUE FLOW SANKEY DIAGRAMS ===\n")
    
    # Generate for each constraint
    constraints = ['country_unconstrained', 'country_constrained', 
                  'region_unconstrained', 'region_constrained']
    
    for constraint in constraints:
        print(f"\nProcessing {constraint}...")
        
        df_constraint = df_mid[df_mid['constraint'] == constraint]
        
        # 1. Individual scenario Sankeys with stage groups
        for goal in ['bau', 'early_refining', 'precursor']:
            fig = create_revenue_flow_sankey(df_constraint, goal, constraint, show_stage_groups=True)
            if fig:
                filename_html = f"sankey_{constraint}_{goal}_grouped.html"
                filename_png = f"sankey_{constraint}_{goal}_grouped.png"
                fig.write_html(os.path.join(output_dir, filename_html))
                fig.write_image(os.path.join(output_dir, filename_png), width=1200, height=600)
                print(f"  ✓ Created {filename_html} and {filename_png}")
        
        # 2. Individual scenario Sankeys with detailed stages
        for goal in ['bau', 'early_refining', 'precursor']:
            fig = create_revenue_flow_sankey(df_constraint, goal, constraint, show_stage_groups=False)
            if fig:
                filename_html = f"sankey_{constraint}_{goal}_detailed.html"
                filename_png = f"sankey_{constraint}_{goal}_detailed.png"
                fig.write_html(os.path.join(output_dir, filename_html))
                fig.write_image(os.path.join(output_dir, filename_png), width=1200, height=600)
                print(f"  ✓ Created {filename_html} and {filename_png}")
        
        # 3. Mineral-focused Sankeys for key minerals
        for mineral in ['copper', 'cobalt', 'lithium']:
            fig = create_mineral_focus_sankey(df_constraint, mineral, constraint)
            if fig:
                filename_html = f"sankey_{constraint}_{mineral}_focus.html"
                filename_png = f"sankey_{constraint}_{mineral}_focus.png"
                fig.write_html(os.path.join(output_dir, filename_html))
                fig.write_image(os.path.join(output_dir, filename_png), width=1200, height=500)
                print(f"  ✓ Created {filename_html} and {filename_png}")
    
    # Generate summary statistics
    print("\n=== REVENUE CONCENTRATION ANALYSIS ===")
    
    for constraint in constraints:
        print(f"\n{constraint.replace('_', ' ').upper()}:")
        df_constraint = df_mid[df_mid['constraint'] == constraint]
        
        for goal in ['bau', 'early_refining', 'precursor']:
            df_goal = df_constraint[
                (df_constraint['goal_type'] == goal) & 
                (df_constraint['processing_stage'] > 0)
            ]
            
            if not df_goal.empty:
                # Calculate stage category revenues
                df_goal['stage_category'] = df_goal['processing_stage'].apply(categorize_stage)
                category_revenue = df_goal.groupby('stage_category')['revenue_usd'].sum() / 1e9
                total = category_revenue.sum()
                
                print(f"\n  {goal.upper()}:")
                for category in ['Beneficiation', 'Early Refining', 'Precursor']:
                    rev = category_revenue.get(category, 0)
                    pct = (rev / total * 100) if total > 0 else 0
                    print(f"    {category}: ${rev:.1f}B ({pct:.1f}%)")
    
    print(f"\n✓ All Sankey diagrams saved to: {output_dir}")
    print("\nOpen the HTML files in a browser to view interactive diagrams.")

if __name__ == "__main__":
    main()