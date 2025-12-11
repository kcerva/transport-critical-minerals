"""
Competitiveness Matrix - Comprehensive SI Figure

Creates a 3×2 grid showing competitiveness matrices for:
- BAU: Constrained and Unconstrained (National policies)
- Precursor: All 4 variants (C_Nat, U_Nat, C_Reg, U_Reg)

Layout:
Row 1: BAU National_C | BAU National_U
Row 2: Prec National_C | Prec National_U
Row 3: Prec Regional_C | Prec Regional_U

Each subplot shows country × mineral heatmap with cost competitiveness rankings.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publication_analysis.config import (
    FIGURE_SIZES, DPI_PUBLICATION, DPI_SCREEN,
    PUBLICATION_STYLE
)

# Import competitiveness functions
from plot_competitiveness_summary import (
    extract_cumulative_costs,
    calculate_quintile_ranks,
    create_heatmap_matrix,
    format_cost_annotation,
    MINERAL_ORDER
)

# Extend scenario config to include BAU
SCENARIO_CONFIG = {
    'bau_2040': {
        'title': 'BAU',
        'included_types': ['Beneficiation'],
        'target_type': 'Beneficiation'
    },
    'early_refining_2040': {
        'title': 'Early Refining',
        'included_types': ['Beneficiation', 'Early refining'],
        'target_type': 'Early refining'
    },
    'precursor_2040': {
        'title': 'Precursor Product',
        'included_types': ['Beneficiation', 'Early refining', 'Precursor related product'],
        'target_type': 'Precursor related product'
    }
}


def plot_single_competitiveness_subplot(ax, cost_matrix, quintile_matrix, rank_matrix,
                                         title, panel_label, show_ylabel=True, show_cbar=True):
    """
    Plot a single competitiveness heatmap subplot.

    Args:
        ax: Matplotlib axis
        cost_matrix, quintile_matrix, rank_matrix: DataFrames with country × mineral data
        title: Subplot title
        panel_label: Panel label (A, B, C, etc.)
        show_ylabel: Whether to show y-axis label
        show_cbar: Whether to show colorbar
    """
    # Create annotations
    annot = np.empty(cost_matrix.shape, dtype=object)
    for i in range(cost_matrix.shape[0]):
        for j in range(cost_matrix.shape[1]):
            cost = cost_matrix.iloc[i, j]
            rank = rank_matrix.iloc[i, j]
            annot[i, j] = format_cost_annotation(cost, rank)

    # Plot heatmap
    cmap = 'Greens_r'  # Darker = more competitive (lower cost)
    cbar_kws = {'label': 'Competitiveness\nQuintile'} if show_cbar else None

    sns.heatmap(
        quintile_matrix,
        annot=annot,
        fmt='',
        cmap=cmap,
        vmin=1,
        vmax=5,
        cbar_kws=cbar_kws,
        ax=ax,
        linewidths=0.5,
        linecolor='gray',
        square=False,
        annot_kws={'fontsize': 9, 'va': 'center'},
        cbar=show_cbar,
        mask=quintile_matrix.isna()
    )

    # Title with panel label
    full_title = f"{panel_label}) {title}"
    ax.set_title(full_title, fontsize=12, fontweight='bold', pad=10)

    # Axis labels
    ax.set_xlabel('Mineral', fontsize=11)
    if show_ylabel:
        ax.set_ylabel('Country (ISO3)', fontsize=11)
    else:
        ax.set_ylabel('')

    # Tick labels
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
    ax.set_xticklabels([m.capitalize() for m in MINERAL_ORDER],
                       rotation=0, ha='center', fontsize=10)


def generate_competitiveness_matrices_SI(df, output_dir):
    """
    Generate comprehensive competitiveness matrix SI figure.

    Creates 3×2 grid showing:
    - Row 1: BAU (C_Nat, U_Nat)
    - Row 2: Precursor National (C_Nat, U_Nat)
    - Row 3: Precursor Regional (C_Reg, U_Reg)

    Args:
        df: Main data DataFrame
        output_dir: Directory to save figures

    Returns:
        list: Paths to saved figures
    """
    print("  Generating SI competitiveness matrices...")

    os.makedirs(output_dir, exist_ok=True)

    # Apply publication style
    plt.style.use('default')
    for key, value in PUBLICATION_STYLE.items():
        plt.rcParams[key] = value

    # Define scenarios to plot (in order)
    scenarios_to_plot = [
        # Row 1: BAU
        ('bau_2040', 'country_constrained', 'BAU (C)', 'A'),
        ('bau_2040', 'country_unconstrained', 'BAU (U)', 'B'),
        # Row 2: Precursor National
        ('precursor_2040', 'country_constrained', 'Precursor National (C)', 'C'),
        ('precursor_2040', 'country_unconstrained', 'Precursor National (U)', 'D'),
        # Row 3: Precursor Regional
        ('precursor_2040', 'region_constrained', 'Precursor Regional (C)', 'E'),
        ('precursor_2040', 'region_unconstrained', 'Precursor Regional (U)', 'F'),
    ]

    # First, collect all countries across all scenarios to ensure consistency
    all_countries = set()
    for scenario_key, constraint, _, _ in scenarios_to_plot:
        scenario_config = SCENARIO_CONFIG[scenario_key]
        cost_df = extract_cumulative_costs(df, scenario_key, constraint, scenario_config)
        if not cost_df.empty:
            all_countries.update(cost_df['iso3'].unique())

    # Sort countries alphabetically for consistent ordering
    all_countries = sorted(all_countries)
    print(f"    Found {len(all_countries)} unique countries across all scenarios")

    # Extract data for all scenarios using consistent country list
    matrices_data = []

    for scenario_key, constraint, title, panel_label in scenarios_to_plot:
        # Get scenario config
        scenario_config = SCENARIO_CONFIG[scenario_key]

        # Extract cumulative costs
        cost_df = extract_cumulative_costs(df, scenario_key, constraint, scenario_config)

        if cost_df.empty:
            print(f"    Warning: No data for {title}")
            # Create empty matrices with all countries
            cost_matrix = pd.DataFrame(index=all_countries, columns=MINERAL_ORDER)
            quintile_matrix = pd.DataFrame(index=all_countries, columns=MINERAL_ORDER)
            rank_matrix = pd.DataFrame(index=all_countries, columns=MINERAL_ORDER)
        else:
            # Calculate rankings
            cost_df = calculate_quintile_ranks(cost_df)

            # Create matrices using ALL countries (not just those with data)
            cost_matrix, quintile_matrix, rank_matrix = create_heatmap_matrix(cost_df, all_countries)

        matrices_data.append({
            'cost_matrix': cost_matrix,
            'quintile_matrix': quintile_matrix,
            'rank_matrix': rank_matrix,
            'title': title,
            'panel_label': panel_label
        })

    # Create figure with 3×2 grid (reduced vertical spacing for taller subplots)
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(3, 2, hspace=0.20, wspace=0.15,
                          left=0.06, right=0.97, top=0.94, bottom=0.08)

    # Plot all subplots
    for idx, data in enumerate(matrices_data):
        row = idx // 2
        col = idx % 2

        ax = fig.add_subplot(gs[row, col])

        # Show ylabel only for left column
        show_ylabel = (col == 0)
        # Show colorbar only for right column
        show_cbar = (col == 1)

        plot_single_competitiveness_subplot(
            ax,
            data['cost_matrix'],
            data['quintile_matrix'],
            data['rank_matrix'],
            data['title'],
            data['panel_label'],
            show_ylabel=show_ylabel,
            show_cbar=show_cbar
        )

    # Overall title
    fig.suptitle('Competitiveness Matrix: BAU and Precursor Scenarios (2040)\n' +
                 'Cost Competitiveness by Country and Mineral',
                 fontsize=14, fontweight='bold', y=0.98)

    # Add interpretation note at bottom (positioned below x-axis labels)
    note_text = (
        "Colors show within-mineral quintile rankings (Q1-Q5). Darker green = more competitive (lower cost).\n"
        "Cell annotations: Cost in thousands (USD/tonne) / Rank (#1 = lowest cost).\n"
        "Costs are cumulative unit costs (production + transport + energy) for all processing stages up to scenario target."
    )
    fig.text(0.5, 0.01, note_text, ha='center', fontsize=9, style='italic',
             wrap=True, color='gray')

    # Save figures
    saved_paths = []

    # High-res PNG
    png_path = os.path.join(output_dir, 'competitiveness_matrix_comprehensive_SI.png')
    plt.savefig(png_path, dpi=DPI_PUBLICATION, bbox_inches='tight', facecolor='white')
    saved_paths.append(png_path)
    print(f"    ✓ Saved: {os.path.basename(png_path)}")

    # PDF
    pdf_path = os.path.join(output_dir, 'competitiveness_matrix_comprehensive_SI.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    saved_paths.append(pdf_path)
    print(f"    ✓ Saved: {os.path.basename(pdf_path)}")

    # Preview PNG (lower resolution)
    preview_path = os.path.join(output_dir, 'competitiveness_matrix_comprehensive_SI_preview.png')
    plt.savefig(preview_path, dpi=DPI_SCREEN, bbox_inches='tight', facecolor='white')
    saved_paths.append(preview_path)
    print(f"    ✓ Saved: {os.path.basename(preview_path)}")

    plt.close(fig)

    return saved_paths


if __name__ == '__main__':
    """Test the competitiveness SI figure generation"""
    import json

    print("Testing competitiveness SI figure generation...")

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load data
    data_path = os.path.join(config['paths']['results'], 'all_data.xlsx')
    df = pd.read_excel(data_path)

    # Generate figure
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'publication', 'economic_indicators')
    paths = generate_competitiveness_matrices_SI(df, output_dir)

    print(f"\nGenerated {len(paths)} files:")
    for path in paths:
        print(f"  - {path}")
