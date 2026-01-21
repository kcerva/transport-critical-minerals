"""
Production Domestic vs Export SI - Supplementary Figure

Creates a two-panel figure with HORIZONTAL STACKED BARS comparing domestic
vs export production with mineral/type breakdown visible in both portions:

Panel A: Production by Mineral
  - Horizontal bars, one per scenario
  - Left portion: Domestic use (stacked by mineral, lighter colors)
  - Right portion: Export production (stacked by mineral, darker colors)
  - Bar length = Total production (domestic + export)
  - Same mineral stacking order in both portions for easy comparison

Panel B: Production by Processing Type
  - Horizontal bars, one per scenario
  - Left portion: Domestic use (stacked by processing type, lighter)
  - Right portion: Export production (stacked by processing type, darker)
  - Shows which processing types are exported vs used domestically

The figure shows 7 scenarios (7 horizontal bars per panel):
- Baseline: 2022 actual values
- BAU: Constrained/Unconstrained (National = Regional for BAU)
- Precursor: Constrained/Unconstrained × National/Regional (4 scenarios)

Data sources:
- Total Production: all_data.xlsx (production_tonnes, stage > 0)
- Export Production: tonnage_flows_with_revenues.xlsx (trade_type == 'Export')
- Domestic Use: Calculated as Total - Export

Visual elements:
- Error bars on right end show total production uncertainty (Low-Mid-High)
- Hatching patterns differentiate Constrained (hatched) vs Unconstrained (solid)
- Alpha transparency: Domestic (0.5) vs Export (1.0)
- Vertical dashed line separates domestic/export portions at the transition point
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
from pathlib import Path

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plot_config import reference_mineral_colormap
from plot_utils import PROCESSING_TYPE_COLORS

# Scenario configuration for 7 bars (Baseline + BAU + Precursor)
SCENARIO_CONFIG = [
    ('baseline', None, None, 'Baseline'),
    ('bau', 'min', 'constrained', 'BAU_C'),
    ('bau', 'min', 'unconstrained', 'BAU_U'),
    ('precursor', 'min', 'constrained', 'Prec_C_N'),
    ('precursor', 'min', 'unconstrained', 'Prec_U_N'),
    ('precursor', 'max', 'constrained', 'Prec_C_R'),
    ('precursor', 'max', 'unconstrained', 'Prec_U_R'),
]

# Mineral order by production volume (for stacking)
MINERAL_ORDER = ['copper', 'manganese', 'graphite', 'cobalt', 'nickel', 'lithium']

# Processing type order (for stacking in Panel B)
PROCESSING_ORDER = ['Beneficiation', 'Early refining', 'Precursor related product']


def load_data():
    """Load both total production and export flow data"""
    # Load config
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    all_data_path = results_path / 'all_data.xlsx'
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'

    # Load total production data
    df_all = pd.read_excel(all_data_path, index_col=[0,1,2,3,4]).reset_index()
    
    # Load export flows
    df_flows = pd.read_excel(flows_path, sheet_name='All_Flows')
    df_flows = df_flows[df_flows['trade_type'] == 'Export'].copy()

    # Add processing_type mapping to both datasets
    stage_type_mapping = df_all[['reference_mineral', 'processing_stage', 'processing_type']].drop_duplicates()
    stage_type_dict = {
        (row['reference_mineral'], row['processing_stage']): row['processing_type']
        for _, row in stage_type_mapping.iterrows()
    }

    # Apply to flows
    df_flows['processing_type'] = df_flows.apply(
        lambda row: stage_type_dict.get(
            (row['reference_mineral'], row['final_processing_stage']),
            'Unknown'
        ),
        axis=1
    )

    # Filter out stage 0 and Metal content
    df_all_processing = df_all[df_all['processing_stage'] > 0].copy()
    df_flows = df_flows[df_flows['processing_type'] != 'Metal content'].copy()

    return df_all_processing, df_flows


def prepare_comparison_data(df_all, df_flows):
    """
    Prepare production comparison data for panels A and B

    Args:
        df_all: Total production DataFrame (stage > 0)
        df_flows: Export flows DataFrame

    Returns:
        tuple: (mineral_data, processing_data)
            Each contains: Dict[scenario_label][demand][category] = {'total': X, 'export': Y, 'domestic': Z}
    """
    mineral_data = {}
    processing_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        processing_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants)
        if goal == 'baseline':
            scenario_name = '2022_baseline'
            constraint_col = 'country_unconstrained'

            # Total production
            df_total = df_all[
                (df_all['scenario'] == scenario_name) &
                (df_all['constraint'] == constraint_col)
            ].copy()

            # Export production
            df_export = df_flows[
                (df_flows['scenario'] == scenario_name) &
                (df_flows['constraint'] == constraint_col)
            ].copy()

            # Use same data for low/mid/high (no demand uncertainty for baseline)
            for demand in ['low', 'mid', 'high']:
                # By Mineral
                for mineral in MINERAL_ORDER:
                    total = df_total[df_total['reference_mineral'] == mineral]['production_tonnes'].sum()
                    export = df_export[df_export['reference_mineral'] == mineral]['final_stage_production_tons'].sum()
                    domestic = total - export
                    
                    mineral_data[label][demand][mineral] = {
                        'total': total,
                        'export': export,
                        'domestic': domestic
                    }

                # By Processing Type
                for ptype in PROCESSING_ORDER:
                    total = df_total[df_total['processing_type'] == ptype]['production_tonnes'].sum()
                    export = df_export[df_export['processing_type'] == ptype]['final_stage_production_tons'].sum()
                    domestic = total - export
                    
                    processing_data[label][demand][ptype] = {
                        'total': total,
                        'export': export,
                        'domestic': domestic
                    }

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                # Build scenario name
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'

                # Build constraint column name
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                # Total production
                df_total = df_all[
                    (df_all['scenario'] == scenario_name) &
                    (df_all['constraint'] == constraint_col)
                ].copy()

                # Export production
                df_export = df_flows[
                    (df_flows['scenario'] == scenario_name) &
                    (df_flows['constraint'] == constraint_col)
                ].copy()

                if df_total.empty or df_export.empty:
                    print(f"Warning: Missing data for {label} {demand} demand")
                    continue

                # By Mineral
                for mineral in MINERAL_ORDER:
                    total = df_total[df_total['reference_mineral'] == mineral]['production_tonnes'].sum()
                    export = df_export[df_export['reference_mineral'] == mineral]['final_stage_production_tons'].sum()
                    domestic = total - export
                    
                    mineral_data[label][demand][mineral] = {
                        'total': total,
                        'export': export,
                        'domestic': domestic
                    }

                # By Processing Type
                for ptype in PROCESSING_ORDER:
                    total = df_total[df_total['processing_type'] == ptype]['production_tonnes'].sum()
                    export = df_export[df_export['processing_type'] == ptype]['final_stage_production_tons'].sum()
                    domestic = total - export
                    
                    processing_data[label][demand][ptype] = {
                        'total': total,
                        'export': export,
                        'domestic': domestic
                    }

    return mineral_data, processing_data


def create_comparison_panels(mineral_data, processing_data, output_dir):
    """
    Create two-panel figure with horizontal stacked bars showing domestic vs export

    Args:
        mineral_data: Dictionary with production by mineral
        processing_data: Dictionary with production by processing type
        output_dir: Output directory for figure
    """
    # Create figure with 2 rows, extra space on right for legends
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))

    scenario_labels = [label for _, _, _, label in SCENARIO_CONFIG]
    n_scenarios = len(scenario_labels)

    # Y positions for horizontal bars (with gaps for visual grouping)
    y_positions = np.arange(n_scenarios, dtype=float)

    # Add gaps: between baseline and BAU, between BAU and Precursor
    baseline_gap = 0.5
    bau_precursor_gap = 0.5
    y_positions[1:] += baseline_gap  # Gap after baseline
    y_positions[3:] += bau_precursor_gap  # Gap after BAU

    bar_height = 0.7

    # Panel A: Production by Mineral
    ax_a = axes[0]

    # Determine hatching for constrained scenarios
    hatches = ['//' if 'C' in label and label != 'Baseline' else '' for label in scenario_labels]

    # For each scenario, track where domestic ends (for export to start)
    domestic_ends = []

    # First, plot DOMESTIC portions (left side of each bar)
    for mineral in MINERAL_ORDER:
        left_positions = []
        widths = []

        for i, label in enumerate(scenario_labels):
            domestic_val = mineral_data[label]['mid'][mineral]['domestic'] / 1e6

            # Calculate left position (sum of previous domestic minerals)
            if mineral == MINERAL_ORDER[0]:
                left = 0
            else:
                left = sum(mineral_data[label]['mid'][m]['domestic'] / 1e6
                          for m in MINERAL_ORDER[:MINERAL_ORDER.index(mineral)])

            left_positions.append(left)
            widths.append(domestic_val)

        # Plot domestic segments
        bars = ax_a.barh(y_positions, widths, bar_height,
                        left=left_positions,
                        color=reference_mineral_colormap[mineral],
                        edgecolor='black', linewidth=0.5,
                        alpha=0.5,  # Lighter for domestic
                        label=f'{mineral.capitalize()}' if mineral == MINERAL_ORDER[0] else '')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        # Track domestic end positions after first mineral loop
        if mineral == MINERAL_ORDER[-1]:
            for i, label in enumerate(scenario_labels):
                domestic_end = sum(mineral_data[label]['mid'][m]['domestic'] / 1e6
                                  for m in MINERAL_ORDER)
                domestic_ends.append(domestic_end)

    # Second, plot EXPORT portions (right side of each bar, starting where domestic ends)
    for mineral in MINERAL_ORDER:
        left_positions = []
        widths = []

        for i, label in enumerate(scenario_labels):
            export_val = mineral_data[label]['mid'][mineral]['export'] / 1e6

            # Calculate left position (domestic_end + sum of previous export minerals)
            if mineral == MINERAL_ORDER[0]:
                left = domestic_ends[i]
            else:
                left = domestic_ends[i] + sum(mineral_data[label]['mid'][m]['export'] / 1e6
                                             for m in MINERAL_ORDER[:MINERAL_ORDER.index(mineral)])

            left_positions.append(left)
            widths.append(export_val)

        # Plot export segments
        bars = ax_a.barh(y_positions, widths, bar_height,
                        left=left_positions,
                        color=reference_mineral_colormap[mineral],
                        edgecolor='black', linewidth=0.5,
                        alpha=1.0,  # Full opacity for export
                        label='')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

    # Add vertical lines at domestic/export boundary for each scenario
    for i, domestic_end in enumerate(domestic_ends):
        ax_a.plot([domestic_end, domestic_end],
                 [y_positions[i] - bar_height/2, y_positions[i] + bar_height/2],
                 color='black', linestyle=':', linewidth=1.5, alpha=0.7)

    # Add error bars at the right end of each bar
    for i, label in enumerate(scenario_labels):
        total_mid = sum(mineral_data[label]['mid'][m]['total'] for m in MINERAL_ORDER) / 1e6
        total_low = sum(mineral_data[label]['low'][m]['total'] for m in MINERAL_ORDER) / 1e6
        total_high = sum(mineral_data[label]['high'][m]['total'] for m in MINERAL_ORDER) / 1e6

        yerr_low = total_mid - total_low
        yerr_high = total_high - total_mid

        ax_a.errorbar(total_mid, y_positions[i],
                     xerr=[[yerr_low], [yerr_high]],
                     fmt='none', ecolor='black', capsize=3, capthick=1.5, linewidth=1.5)

    # Formatting Panel A
    ax_a.set_xlabel('Production (Mt)', fontsize=12, fontweight='bold')
    ax_a.set_title('A. Production by Mineral: Domestic (light) vs Export (dark)',
                   fontsize=13, fontweight='bold', pad=15)
    ax_a.set_yticks(y_positions)
    ax_a.set_yticklabels(scenario_labels, fontsize=10)
    ax_a.invert_yaxis()  # Top to bottom

    # Create legend with mineral colors - place outside plot on right
    mineral_patches = [mpatches.Patch(color=reference_mineral_colormap[m],
                                     label=m.capitalize())
                      for m in MINERAL_ORDER]
    leg1 = ax_a.legend(handles=mineral_patches,
                       bbox_to_anchor=(1.02, 1), loc='upper left',
                       frameon=True, fontsize=9, ncol=1, title='Minerals')

    # Add domestic/export legend - place below mineral legend
    dom_exp_patches = [
        mpatches.Patch(color='gray', alpha=0.5, label='Domestic (left)'),
        mpatches.Patch(color='gray', alpha=1.0, label='Export (right)')
    ]
    leg2 = ax_a.legend(handles=dom_exp_patches,
                      bbox_to_anchor=(1.02, 0.65), loc='upper left',
                      frameon=True, fontsize=9, ncol=1, title='Production Type')
    ax_a.add_artist(leg1)

    ax_a.grid(axis='x', alpha=0.3, linestyle='--')
    ax_a.set_axisbelow(True)

    # Panel B: Production by Processing Type
    ax_b = axes[1]

    # For each scenario, track where domestic ends (for export to start)
    domestic_ends_b = []

    # First, plot DOMESTIC portions (left side of each bar)
    for ptype in PROCESSING_ORDER:
        left_positions = []
        widths = []

        for i, label in enumerate(scenario_labels):
            domestic_val = processing_data[label]['mid'][ptype]['domestic'] / 1e6

            # Calculate left position (sum of previous domestic processing types)
            if ptype == PROCESSING_ORDER[0]:
                left = 0
            else:
                left = sum(processing_data[label]['mid'][p]['domestic'] / 1e6
                          for p in PROCESSING_ORDER[:PROCESSING_ORDER.index(ptype)])

            left_positions.append(left)
            widths.append(domestic_val)

        # Plot domestic segments
        bars = ax_b.barh(y_positions, widths, bar_height,
                        left=left_positions,
                        color=PROCESSING_TYPE_COLORS[ptype],
                        edgecolor='black', linewidth=0.5,
                        alpha=0.5,  # Lighter for domestic
                        label=f'{ptype}' if ptype == PROCESSING_ORDER[0] else '')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        # Track domestic end positions after last processing type
        if ptype == PROCESSING_ORDER[-1]:
            for i, label in enumerate(scenario_labels):
                domestic_end = sum(processing_data[label]['mid'][p]['domestic'] / 1e6
                                  for p in PROCESSING_ORDER)
                domestic_ends_b.append(domestic_end)

    # Second, plot EXPORT portions (right side of each bar, starting where domestic ends)
    for ptype in PROCESSING_ORDER:
        left_positions = []
        widths = []

        for i, label in enumerate(scenario_labels):
            export_val = processing_data[label]['mid'][ptype]['export'] / 1e6

            # Calculate left position (domestic_end + sum of previous export processing types)
            if ptype == PROCESSING_ORDER[0]:
                left = domestic_ends_b[i]
            else:
                left = domestic_ends_b[i] + sum(processing_data[label]['mid'][p]['export'] / 1e6
                                               for p in PROCESSING_ORDER[:PROCESSING_ORDER.index(ptype)])

            left_positions.append(left)
            widths.append(export_val)

        # Plot export segments
        bars = ax_b.barh(y_positions, widths, bar_height,
                        left=left_positions,
                        color=PROCESSING_TYPE_COLORS[ptype],
                        edgecolor='black', linewidth=0.5,
                        alpha=1.0,  # Full opacity for export
                        label='')

        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

    # Add vertical lines at domestic/export boundary
    for i, domestic_end in enumerate(domestic_ends_b):
        ax_b.plot([domestic_end, domestic_end],
                 [y_positions[i] - bar_height/2, y_positions[i] + bar_height/2],
                 color='black', linestyle=':', linewidth=1.5, alpha=0.7)

    # Add error bars at the right end of each bar
    for i, label in enumerate(scenario_labels):
        total_mid = sum(processing_data[label]['mid'][p]['total'] for p in PROCESSING_ORDER) / 1e6
        total_low = sum(processing_data[label]['low'][p]['total'] for p in PROCESSING_ORDER) / 1e6
        total_high = sum(processing_data[label]['high'][p]['total'] for p in PROCESSING_ORDER) / 1e6

        yerr_low = total_mid - total_low
        yerr_high = total_high - total_mid

        ax_b.errorbar(total_mid, y_positions[i],
                     xerr=[[yerr_low], [yerr_high]],
                     fmt='none', ecolor='black', capsize=3, capthick=1.5, linewidth=1.5)

    # Formatting Panel B
    ax_b.set_xlabel('Production (Mt)', fontsize=12, fontweight='bold')
    ax_b.set_title('B. Production by Processing Type: Domestic (light) vs Export (dark)',
                   fontsize=13, fontweight='bold', pad=15)
    ax_b.set_yticks(y_positions)
    ax_b.set_yticklabels(scenario_labels, fontsize=10)
    ax_b.invert_yaxis()  # Top to bottom

    # Create legend with processing type colors - place outside plot on right
    ptype_patches = [mpatches.Patch(color=PROCESSING_TYPE_COLORS[p],
                                    label=p)
                    for p in PROCESSING_ORDER]
    leg1_b = ax_b.legend(handles=ptype_patches,
                        bbox_to_anchor=(1.02, 1), loc='upper left',
                        frameon=True, fontsize=9, ncol=1, title='Processing Types')

    # Add domestic/export legend - place below processing legend
    leg2_b = ax_b.legend(handles=dom_exp_patches,
                        bbox_to_anchor=(1.02, 0.70), loc='upper left',
                        frameon=True, fontsize=9, ncol=1, title='Production Type')
    ax_b.add_artist(leg1_b)

    ax_b.grid(axis='x', alpha=0.3, linestyle='--')
    ax_b.set_axisbelow(True)

    # Add hatching legend to Panel A - place below production type legend
    hatching_patches = [
        mpatches.Patch(facecolor='white', edgecolor='black', label='Unconstrained'),
        mpatches.Patch(facecolor='white', edgecolor='black', hatch='//', label='Constrained')
    ]
    leg3 = ax_a.legend(handles=hatching_patches,
                       bbox_to_anchor=(1.02, 0.42), loc='upper left',
                       frameon=True, fontsize=9, title='Constraint')
    ax_a.add_artist(leg1)
    ax_a.add_artist(leg2)

    # Adjust layout to leave space for legends on the right
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    # Save figure
    output_path_png = output_dir / 'production_domestic_vs_export_SI.png'
    output_path_pdf = output_dir / 'production_domestic_vs_export_SI.pdf'
    output_path_preview = output_dir / 'production_domestic_vs_export_SI_preview.png'

    # Get all legend artists for bbox_extra_artists
    all_legends = [leg1, leg2, leg3, leg1_b, leg2_b]

    fig.savefig(output_path_png, dpi=300, bbox_inches='tight', bbox_extra_artists=all_legends)
    fig.savefig(output_path_pdf, bbox_inches='tight', bbox_extra_artists=all_legends)
    fig.savefig(output_path_preview, dpi=150, bbox_inches='tight', bbox_extra_artists=all_legends)

    plt.close()

    print(f"  ✓ Saved: {output_path_png}")
    print(f"  ✓ Saved: {output_path_pdf}")
    print(f"  ✓ Saved: {output_path_preview}")


def main():
    """Main execution function"""
    print("="*80)
    print("PRODUCTION DOMESTIC VS EXPORT SI FIGURE GENERATION")
    print("="*80)

    # Setup output directory
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    figures_path = Path(config['paths']['figures'])
    output_dir = figures_path / 'automated_plots' / 'publication' / 'production_comparison'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print()

    print("[Production Domestic vs Export Comparison]")
    print("-"*80)

    # Load data
    print("Loading data...")
    df_all, df_flows = load_data()
    print(f"  ✓ Total production: {len(df_all):,} records (stage > 0)")
    print(f"  ✓ Export flows: {len(df_flows):,} records")

    # Prepare data
    print("Preparing comparison data...")
    mineral_data, processing_data = prepare_comparison_data(df_all, df_flows)
    print("  ✓ Data prepared")

    # Create figure
    print("Creating two-panel comparison figure...")
    create_comparison_panels(mineral_data, processing_data, output_dir)

    print()
    print("="*80)
    print("GENERATED 3 FILES")
    print("="*80)


if __name__ == '__main__':
    main()
