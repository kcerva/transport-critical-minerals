"""
Test Sankey diagram for revenue flows across processing stages and minerals
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

# Add paths
import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

from plot_config import reference_minerals, reference_mineral_colormap

def create_revenue_sankey(df_analysis, goal_type, title_suffix=""):
    """
    Create a Sankey diagram showing revenue flows from minerals through processing stages
    
    Structure:
    - Left: Minerals (source)
    - Middle/Right: Processing stages (targets)
    - Flows: Revenue amounts
    """
    
    # Filter data
    df_goal = df_analysis[
        (df_analysis['goal_type'] == goal_type) & 
        (df_analysis['processing_stage'] > 0)  # Exclude stage 0
    ].copy()
    
    if df_goal.empty:
        return None
    
    # Create nodes
    minerals = sorted(df_goal['reference_mineral'].unique())
    stages = sorted(df_goal['processing_stage'].unique())
    
    # Node labels and positions
    node_labels = []
    node_colors = []
    node_x = []
    node_y = []
    
    # Add mineral nodes (left side)
    for i, mineral in enumerate(minerals):
        node_labels.append(mineral.title())
        node_colors.append(reference_mineral_colormap.get(mineral, '#999999'))
        node_x.append(0.1)  # Left position
        node_y.append(i / (len(minerals) - 1) if len(minerals) > 1 else 0.5)
    
    # Add stage nodes (right side, grouped)
    stage_groups = {
        'beneficiation': [],
        'early_refining': [],
        'precursor': []
    }
    
    for stage in stages:
        if stage <= 1.5:
            stage_groups['beneficiation'].append(stage)
        elif stage <= 3.5:
            stage_groups['early_refining'].append(stage)
        else:
            stage_groups['precursor'].append(stage)
    
    # Position stages
    y_offset = 0
    x_positions = {'beneficiation': 0.4, 'early_refining': 0.7, 'precursor': 0.95}
    stage_to_node_idx = {}
    
    for group_name, group_stages in stage_groups.items():
        if group_stages:
            for i, stage in enumerate(sorted(group_stages)):
                idx = len(node_labels)
                stage_to_node_idx[stage] = idx
                node_labels.append(f"Stage {stage}")
                node_colors.append('#cccccc')  # Gray for stages
                node_x.append(x_positions[group_name])
                node_y.append(y_offset + (i + 0.5) / (len(stages) + 2))
            y_offset += len(group_stages) / (len(stages) + 2)
    
    # Create links (flows)
    source = []
    target = []
    value = []
    link_colors = []
    link_labels = []
    
    # Calculate revenue flows from minerals to stages
    for mineral_idx, mineral in enumerate(minerals):
        mineral_data = df_goal[df_goal['reference_mineral'] == mineral]
        
        # Group by stage and sum revenue
        stage_revenue = mineral_data.groupby('processing_stage')['revenue_usd'].sum()
        
        for stage, revenue in stage_revenue.items():
            if stage in stage_to_node_idx and revenue > 0:
                source.append(mineral_idx)
                target.append(stage_to_node_idx[stage])
                value.append(revenue / 1e6)  # Convert to millions
                link_colors.append(reference_mineral_colormap.get(mineral, '#999999') + '80')  # Add transparency
                link_labels.append(f"{mineral.title()} → Stage {stage}: ${revenue/1e6:.1f}M")
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
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
            color=link_colors,
            label=link_labels,
            hovertemplate='%{label}<br>Revenue: $%{value:.1f}M<extra></extra>'
        )
    )])
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"Revenue Flows by Mineral and Processing Stage<br><sub>{goal_type.replace('_', ' ').title()} Scenario{title_suffix}</sub>",
            x=0.5,
            xanchor='center'
        ),
        font_size=10,
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_comparative_sankey(df_analysis, constraint):
    """Create a comparative view showing how revenue flows change between scenarios"""
    
    # Create subplots for each goal
    from plotly.subplots import make_subplots
    
    goals = ['bau', 'early_refining', 'precursor']
    
    # Calculate total revenues for sizing
    total_revenues = {}
    for goal in goals:
        df_goal = df_analysis[
            (df_analysis['goal_type'] == goal) & 
            (df_analysis['processing_stage'] > 0)
        ]
        total_revenues[goal] = df_goal['revenue_usd'].sum() / 1e9  # Billions
    
    # Create individual Sankey for each goal
    figs = []
    for goal in goals:
        fig = create_revenue_sankey(df_analysis, goal, f" - Total: ${total_revenues[goal]:.1f}B")
        if fig:
            figs.append(fig)
    
    return figs

def test_sankey_creation():
    """Test the Sankey diagram creation"""
    
    # Load configuration
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.json"
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Load data
    output_data_path = config['paths']['results']
    df = pd.read_excel(os.path.join(output_data_path, 'all_data.xlsx'))
    
    # Filter to a specific constraint for testing
    constraint = 'country_unconstrained'
    df_test = df[df['constraint'] == constraint].copy()
    
    # Add goal type
    df_test['goal_type'] = df_test['scenario'].apply(lambda x: 
        'bau' if 'bau_2040' in x else
        'early_refining' if 'early_refining_2040' in x else
        'precursor' if 'precursor_2040' in x else
        'baseline'
    )
    
    # Filter to mid scenarios
    df_test = df_test[df_test['scenario'].str.contains('mid_min|mid_max', na=False)]
    
    print(f"Testing with {len(df_test)} records")
    print(f"Goals present: {df_test['goal_type'].unique()}")
    print(f"Stages present: {sorted(df_test[df_test['processing_stage'] > 0]['processing_stage'].unique())}")
    
    # Test single Sankey
    for goal in ['bau', 'early_refining', 'precursor']:
        fig = create_revenue_sankey(df_test, goal)
        if fig:
            output_file = os.path.join(output_data_path, f'test_sankey_{goal}_{constraint}.html')
            fig.write_html(output_file)
            print(f"Saved test Sankey for {goal}: {output_file}")
    
    # Test comparative view
    figs = create_comparative_sankey(df_test, constraint)
    print(f"\nGenerated {len(figs)} comparative Sankey diagrams")
    
    # Also create a combined view showing stage concentration
    print("\n=== Stage Revenue Concentration Analysis ===")
    for goal in ['bau', 'early_refining', 'precursor']:
        df_goal = df_test[
            (df_test['goal_type'] == goal) & 
            (df_test['processing_stage'] > 0)
        ]
        
        if not df_goal.empty:
            # Categorize stages
            beneficiation_rev = df_goal[df_goal['processing_stage'] <= 1.5]['revenue_usd'].sum() / 1e9
            early_refining_rev = df_goal[(df_goal['processing_stage'] > 1.5) & (df_goal['processing_stage'] <= 3.5)]['revenue_usd'].sum() / 1e9
            precursor_rev = df_goal[df_goal['processing_stage'] > 3.5]['revenue_usd'].sum() / 1e9
            total_rev = beneficiation_rev + early_refining_rev + precursor_rev
            
            print(f"\n{goal.upper()}:")
            print(f"  Beneficiation (≤1.5): ${beneficiation_rev:.1f}B ({beneficiation_rev/total_rev*100:.1f}%)")
            print(f"  Early Refining (1.5-3.5): ${early_refining_rev:.1f}B ({early_refining_rev/total_rev*100:.1f}%)")
            print(f"  Precursor (>3.5): ${precursor_rev:.1f}B ({precursor_rev/total_rev*100:.1f}%)")

if __name__ == "__main__":
    test_sankey_creation()