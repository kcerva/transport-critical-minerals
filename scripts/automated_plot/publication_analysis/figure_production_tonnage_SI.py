"""
Production Tonnage SI - Final Stage Production Figure

Creates a two-panel supplementary figure showing final stage production tonnage
across scenarios:

Panel A: Final Stage Production by Mineral
Panel B: Final Stage Production by Processing Type

The figure shows 7 bars representing:
- Baseline: 2022 actual values (1 bar)
- BAU: Constrained/Unconstrained (2 bars - National = Regional for BAU)
- Precursor: Constrained/Unconstrained × National/Regional (4 bars)

Error bars show demand uncertainty (Low-Mid-High range)
Hatching patterns differentiate Constrained (hatched) vs Unconstrained (solid)

Data source: tonnage_flows_with_revenues.xlsx (Export flows only)
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


def load_tonnage_flows_data():
    """Load the tonnage flows data and add processing_type mapping"""
    # Load config
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'
    all_data_path = results_path / 'all_data.xlsx'

    # Load tonnage flows (Export flows only for production)
    df_flows = pd.read_excel(flows_path, sheet_name='All_Flows')

    # Load all_data for processing_type mapping
    df_all = pd.read_excel(all_data_path)

    # Create (mineral, stage) → processing_type mapping
    # Processing type depends on BOTH mineral and stage
    stage_type_mapping = df_all[['reference_mineral', 'processing_stage', 'processing_type']].drop_duplicates()
    stage_type_dict = {
        (row['reference_mineral'], row['processing_stage']): row['processing_type']
        for _, row in stage_type_mapping.iterrows()
    }

    # Filter for Export flows only
    df_flows = df_flows[df_flows['trade_type'] == 'Export'].copy()

    # Apply processing_type mapping
    df_flows['processing_type'] = df_flows.apply(
        lambda row: stage_type_dict.get(
            (row['reference_mineral'], row['final_processing_stage']),
            'Unknown'
        ),
        axis=1
    )

    # Filter out "Metal content" (stage 0.0) - not physical exports
    df_flows = df_flows[df_flows['processing_type'] != 'Metal content'].copy()

    # Check for any unknown mappings
    unknown_count = (df_flows['processing_type'] == 'Unknown').sum()
    if unknown_count > 0:
        print(f"  Warning: {unknown_count} flows with unknown processing type")

    return df_flows


def prepare_production_data(df_flows):
    """
    Prepare final stage production data for panels A and B

    Args:
        df_flows: Tonnage flows DataFrame (Export flows only, with processing_type)

    Returns:
        tuple: (production_by_mineral_data, production_by_type_data)
            production_by_mineral_data: Dict[scenario_label][demand][mineral] = tonnage
            production_by_type_data: Dict[scenario_label][demand][processing_type] = tonnage
    """
    production_by_mineral_data = {}
    production_by_type_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        production_by_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        production_by_type_data[label] = {'low': {}, 'mid': {}, 'high': {}}

        # Handle baseline scenario (no demand variants)
        if goal == 'baseline':
            scenario_name = '2022_baseline'

            # Filter for baseline - use country_unconstrained
            df_scenario = df_flows[
                (df_flows['scenario'] == scenario_name) &
                (df_flows['constraint'] == 'country_unconstrained')
            ].copy()

            if df_scenario.empty:
                print(f"Warning: No data for {label}")
                continue

            # Use same data for low/mid/high (no demand uncertainty for baseline)
            for demand in ['low', 'mid', 'high']:
                # Production by Mineral
                production_by_mineral = df_scenario.groupby('reference_mineral')['final_stage_production_tons'].sum()

                for mineral in MINERAL_ORDER:
                    production_by_mineral_data[label][demand][mineral] = production_by_mineral.get(mineral, 0)

                # Production by Processing Type
                production_by_type = df_scenario.groupby('processing_type')['final_stage_production_tons'].sum()

                for ptype in PROCESSING_ORDER:
                    production_by_type_data[label][demand][ptype] = production_by_type.get(ptype, 0)

        else:
            # Handle BAU and Precursor scenarios with demand variants
            for demand in ['low', 'mid', 'high']:
                # Build scenario name
                scenario_name = f'{goal}_2040_{demand}_{policy}_threshold_metal_tons'

                # Build constraint column name
                constraint_col = f'country_{constraint}' if policy == 'min' else f'region_{constraint}'

                # Filter data
                df_scenario = df_flows[
                    (df_flows['scenario'] == scenario_name) &
                    (df_flows['constraint'] == constraint_col)
                ].copy()

                if df_scenario.empty:
                    print(f"Warning: No data for {label} {demand} demand")
                    continue

                # Production by Mineral
                production_by_mineral = df_scenario.groupby('reference_mineral')['final_stage_production_tons'].sum()

                for mineral in MINERAL_ORDER:
                    production_by_mineral_data[label][demand][mineral] = production_by_mineral.get(mineral, 0)

                # Production by Processing Type
                production_by_type = df_scenario.groupby('processing_type')['final_stage_production_tons'].sum()

                for ptype in PROCESSING_ORDER:
                    production_by_type_data[label][demand][ptype] = production_by_type.get(ptype, 0)

    return production_by_mineral_data, production_by_type_data


def create_production_panels(production_by_mineral_data, production_by_type_data, output_dir):
    """
    Create two-panel figure showing final stage production tonnage

    Args:
        production_by_mineral_data: Dictionary with production by mineral
        production_by_type_data: Dictionary with production by processing type
        output_dir: Output directory for figure
    """
    # Create figure with 2 rows
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))

    scenario_labels = [label for _, _, _, label in SCENARIO_CONFIG]
    x_pos = np.arange(len(scenario_labels))

    # Panel A: Production by Mineral
    ax_a = axes[0]

    # Calculate bar values (mid demand) and error bars (low-high range)
    mineral_bars = {mineral: [] for mineral in MINERAL_ORDER}
    mineral_errors_low = {mineral: [] for mineral in MINERAL_ORDER}
    mineral_errors_high = {mineral: [] for mineral in MINERAL_ORDER}

    for label in scenario_labels:
        for mineral in MINERAL_ORDER:
            mid_val = production_by_mineral_data[label]['mid'].get(mineral, 0) / 1e6  # Convert to Mt
            low_val = production_by_mineral_data[label]['low'].get(mineral, 0) / 1e6
            high_val = production_by_mineral_data[label]['high'].get(mineral, 0) / 1e6

            mineral_bars[mineral].append(mid_val)
            mineral_errors_low[mineral].append(mid_val - low_val)
            mineral_errors_high[mineral].append(high_val - mid_val)

    # Create stacked bars
    bottom = np.zeros(len(scenario_labels))
    bar_width = 0.6

    mineral_patches = []
    for mineral in MINERAL_ORDER:
        values = np.array(mineral_bars[mineral])

        # Determine hatching: Constrained scenarios get hatching
        hatches = ['//' if 'C' in label and label != 'Baseline' else '' for label in scenario_labels]

        bars = ax_a.bar(x_pos, values, bar_width, bottom=bottom,
                       label=mineral.capitalize(),
                       color=reference_mineral_colormap[mineral],
                       edgecolor='black', linewidth=0.5)

        # Apply hatching
        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        mineral_patches.append(mpatches.Patch(color=reference_mineral_colormap[mineral],
                                             label=mineral.capitalize()))

        bottom += values

    # Add error bars on top of stacks
    total_errors_low = np.zeros(len(scenario_labels))
    total_errors_high = np.zeros(len(scenario_labels))
    for mineral in MINERAL_ORDER:
        total_errors_low += np.array(mineral_errors_low[mineral])
        total_errors_high += np.array(mineral_errors_high[mineral])

    ax_a.errorbar(x_pos, bottom, yerr=[total_errors_low, total_errors_high],
                 fmt='none', ecolor='black', capsize=3, capthick=1.5, linewidth=1.5)

    # Formatting Panel A
    ax_a.set_ylabel('Final Stage Production (Mt)', fontsize=12, fontweight='bold')
    ax_a.set_title('A. Final Stage Production by Mineral', fontsize=14, fontweight='bold', pad=15)
    ax_a.set_xticks(x_pos)
    ax_a.set_xticklabels(scenario_labels, fontsize=10)
    ax_a.legend(handles=mineral_patches, loc='upper left', frameon=True, fontsize=10, ncol=2)
    ax_a.grid(axis='y', alpha=0.3, linestyle='--')
    ax_a.set_axisbelow(True)

    # Panel B: Production by Processing Type
    ax_b = axes[1]

    # Calculate bar values (mid demand) and error bars (low-high range)
    type_bars = {ptype: [] for ptype in PROCESSING_ORDER}
    type_errors_low = {ptype: [] for ptype in PROCESSING_ORDER}
    type_errors_high = {ptype: [] for ptype in PROCESSING_ORDER}

    for label in scenario_labels:
        for ptype in PROCESSING_ORDER:
            mid_val = production_by_type_data[label]['mid'].get(ptype, 0) / 1e6  # Convert to Mt
            low_val = production_by_type_data[label]['low'].get(ptype, 0) / 1e6
            high_val = production_by_type_data[label]['high'].get(ptype, 0) / 1e6

            type_bars[ptype].append(mid_val)
            type_errors_low[ptype].append(mid_val - low_val)
            type_errors_high[ptype].append(high_val - mid_val)

    # Create stacked bars
    bottom = np.zeros(len(scenario_labels))

    type_patches = []
    for ptype in PROCESSING_ORDER:
        values = np.array(type_bars[ptype])

        # Determine hatching: Constrained scenarios get hatching
        hatches = ['//' if 'C' in label and label != 'Baseline' else '' for label in scenario_labels]

        color = PROCESSING_TYPE_COLORS[ptype]

        bars = ax_b.bar(x_pos, values, bar_width, bottom=bottom,
                       color=color,
                       edgecolor='black', linewidth=0.5)

        # Apply hatching
        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        type_patches.append(mpatches.Patch(color=color, label=ptype))

        bottom += values

    # Add error bars on top of stacks
    total_errors_low = np.zeros(len(scenario_labels))
    total_errors_high = np.zeros(len(scenario_labels))
    for ptype in PROCESSING_ORDER:
        total_errors_low += np.array(type_errors_low[ptype])
        total_errors_high += np.array(type_errors_high[ptype])

    ax_b.errorbar(x_pos, bottom, yerr=[total_errors_low, total_errors_high],
                 fmt='none', ecolor='black', capsize=3, capthick=1.5, linewidth=1.5)

    # Formatting Panel B
    ax_b.set_ylabel('Final Stage Production (Mt)', fontsize=12, fontweight='bold')
    ax_b.set_title('B. Final Stage Production by Processing Type', fontsize=14, fontweight='bold', pad=15)
    ax_b.set_xticks(x_pos)
    ax_b.set_xticklabels(scenario_labels, fontsize=10)
    ax_b.legend(handles=type_patches, loc='upper left', frameon=True, fontsize=10)
    ax_b.grid(axis='y', alpha=0.3, linestyle='--')
    ax_b.set_axisbelow(True)

    # Add hatching legend
    hatching_patches = [
        mpatches.Patch(facecolor='white', edgecolor='black', label='Unconstrained'),
        mpatches.Patch(facecolor='white', edgecolor='black', hatch='//', label='Constrained')
    ]

    # Add hatching legend to Panel A
    leg2 = ax_a.legend(handles=hatching_patches, loc='upper right',
                       frameon=True, fontsize=10, title='Constraint Type')

    plt.tight_layout()

    # Save figure
    output_path_png = output_dir / 'production_tonnage_SI.png'
    output_path_pdf = output_dir / 'production_tonnage_SI.pdf'
    output_path_preview = output_dir / 'production_tonnage_SI_preview.png'

    fig.savefig(output_path_png, dpi=300, bbox_inches='tight')
    fig.savefig(output_path_pdf, bbox_inches='tight')
    fig.savefig(output_path_preview, dpi=150, bbox_inches='tight')

    plt.close()

    print(f"  ✓ Saved: {output_path_png}")
    print(f"  ✓ Saved: {output_path_pdf}")
    print(f"  ✓ Saved: {output_path_preview}")


def main():
    """Main execution function"""
    print("="*80)
    print("PRODUCTION TONNAGE SI FIGURE GENERATION")
    print("="*80)

    # Setup output directory
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    figures_path = Path(config['paths']['figures'])
    output_dir = figures_path / 'automated_plots' / 'publication' / 'production_tonnage'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print()

    print("[Production Tonnage SI - Final Stage Production]")
    print("-"*80)

    # Load data
    print("Loading tonnage flows data...")
    df_flows = load_tonnage_flows_data()
    print(f"  ✓ Loaded {len(df_flows):,} export flow records")

    # Prepare data
    print("Preparing production data...")
    production_by_mineral_data, production_by_type_data = prepare_production_data(df_flows)
    print("  ✓ Data prepared")

    # Create figure
    print("Creating two-panel figure...")
    create_production_panels(production_by_mineral_data, production_by_type_data, output_dir)

    print()
    print("="*80)
    print("GENERATED 3 FILES")
    print("="*80)


if __name__ == '__main__':
    main()
