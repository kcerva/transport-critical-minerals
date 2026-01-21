"""
Economic Indicators SI - Net Export Revenue Figure

Creates a two-panel supplementary figure showing net export revenues
(export revenue minus import cost) across scenarios:

Panel A: Net Export Revenue by Mineral
Panel B: Net Export Revenue by Processing Type

The figure shows 7 bars representing:
- Baseline: 2022 actual values (1 bar)
- BAU: Constrained/Unconstrained (2 bars - National = Regional for BAU)
- Precursor: Constrained/Unconstrained × National/Regional (4 bars)

Error bars show demand uncertainty (Low-Mid-High range)
Hatching patterns differentiate Constrained (hatched) vs Unconstrained (solid)

IMPORTANT: Uses MARKET PRICE basis for imports (import_cost_at_price_usd)
This reflects actual cash flows and trade balance.

Data source: tonnage_flows_with_revenues.xlsx
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

# Processing type order (for stacking)
PROCESSING_ORDER = ['Beneficiation', 'Early refining', 'Precursor related product']


def load_tonnage_flows_with_revenues():
    """Load the tonnage flows with revenue/cost data"""
    # Load config
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    results_path = Path(config['paths']['results'])
    flows_path = results_path / 'tonnage_flows_with_revenues.xlsx'
    all_data_path = results_path / 'all_data.xlsx'

    # Load tonnage flows (for export/import revenues)
    df_flows = pd.read_excel(flows_path, sheet_name='All_Flows')

    # Load all_data (for processing_type mapping)
    df_all = pd.read_excel(all_data_path)

    # Create processing_type mapping from all_data
    # Get unique combinations of processing_stage and processing_type
    stage_to_type = df_all[['processing_stage', 'processing_type']].drop_duplicates()
    stage_to_type_dict = dict(zip(stage_to_type['processing_stage'], stage_to_type['processing_type']))

    # Map final_processing_stage to processing_type in flows data
    df_flows['processing_type'] = df_flows['final_processing_stage'].map(stage_to_type_dict)

    return df_flows


def prepare_net_revenue_data(df_flows):
    """
    Prepare net export revenue data for panels A and B

    Args:
        df_flows: Tonnage flows DataFrame with revenue/cost data

    Returns:
        tuple: (revenue_by_mineral_data, revenue_by_processing_data)
            revenue_by_mineral_data: Dict[scenario_label][demand][mineral] = net_revenue
            revenue_by_processing_data: Dict[scenario_label][demand][processing_type] = net_revenue
    """
    revenue_by_mineral_data = {}
    revenue_by_processing_data = {}

    for goal, policy, constraint, label in SCENARIO_CONFIG:
        revenue_by_mineral_data[label] = {'low': {}, 'mid': {}, 'high': {}}
        revenue_by_processing_data[label] = {'low': {}, 'mid': {}, 'high': {}}

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
                # Net Revenue by Mineral: Sum (exports - imports) by mineral - USING MARKET PRICE BASIS
                exports = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('reference_mineral')['export_revenue_usd'].sum()
                imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('reference_mineral')['import_cost_at_price_usd'].sum()

                for mineral in MINERAL_ORDER:
                    export_rev = exports.get(mineral, 0)
                    import_cost = imports.get(mineral, 0)
                    revenue_by_mineral_data[label][demand][mineral] = export_rev - import_cost

                # Net Revenue by Processing Type - USING MARKET PRICE BASIS
                exports_by_type = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('processing_type')['export_revenue_usd'].sum()
                imports_by_type = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('processing_type')['import_cost_at_price_usd'].sum()

                for ptype in PROCESSING_ORDER:
                    export_rev = exports_by_type.get(ptype, 0)
                    import_cost = imports_by_type.get(ptype, 0)
                    revenue_by_processing_data[label][demand][ptype] = export_rev - import_cost

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

                # Net Revenue by Mineral - USING MARKET PRICE BASIS
                exports = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('reference_mineral')['export_revenue_usd'].sum()
                imports = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('reference_mineral')['import_cost_at_price_usd'].sum()

                for mineral in MINERAL_ORDER:
                    export_rev = exports.get(mineral, 0)
                    import_cost = imports.get(mineral, 0)
                    revenue_by_mineral_data[label][demand][mineral] = export_rev - import_cost

                # Net Revenue by Processing Type - USING MARKET PRICE BASIS
                exports_by_type = df_scenario[df_scenario['trade_type'] == 'Export'].groupby('processing_type')['export_revenue_usd'].sum()
                imports_by_type = df_scenario[df_scenario['trade_type'].str.contains('Import', na=False)].groupby('processing_type')['import_cost_at_price_usd'].sum()

                for ptype in PROCESSING_ORDER:
                    export_rev = exports_by_type.get(ptype, 0)
                    import_cost = imports_by_type.get(ptype, 0)
                    revenue_by_processing_data[label][demand][ptype] = export_rev - import_cost

    return revenue_by_mineral_data, revenue_by_processing_data


def create_net_revenue_panels(revenue_by_mineral_data, revenue_by_processing_data, output_dir):
    """
    Create two-panel figure showing net export revenue

    Args:
        revenue_by_mineral_data: Dictionary with net revenue by mineral
        revenue_by_processing_data: Dictionary with net revenue by processing type
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

    # Panel A: Net Export Revenue by Mineral
    ax_a = axes[0]

    # Determine hatching for constrained scenarios
    hatches = ['//' if 'C' in label and label != 'Baseline' else '' for label in scenario_labels]

    # Calculate bar values (mid demand) and error bars (low-high range)
    mineral_bars = {mineral: [] for mineral in MINERAL_ORDER}
    mineral_errors_low = {mineral: [] for mineral in MINERAL_ORDER}
    mineral_errors_high = {mineral: [] for mineral in MINERAL_ORDER}

    for label in scenario_labels:
        for mineral in MINERAL_ORDER:
            mid_val = revenue_by_mineral_data[label]['mid'].get(mineral, 0) / 1e9  # Convert to billions
            low_val = revenue_by_mineral_data[label]['low'].get(mineral, 0) / 1e9
            high_val = revenue_by_mineral_data[label]['high'].get(mineral, 0) / 1e9

            mineral_bars[mineral].append(mid_val)
            mineral_errors_low[mineral].append(mid_val - low_val)
            mineral_errors_high[mineral].append(high_val - mid_val)

    # Plot stacked horizontal bars
    lefts = np.zeros(len(scenario_labels))
    for mineral in MINERAL_ORDER:
        values = np.array(mineral_bars[mineral])
        errors_low = np.array(mineral_errors_low[mineral])
        errors_high = np.array(mineral_errors_high[mineral])

        bars = ax_a.barh(y_positions, values, bar_height,
                        left=lefts,
                        label=mineral.capitalize(),
                        color=reference_mineral_colormap.get(mineral, '#999999'),
                        edgecolor='black', linewidth=0.5)

        # Apply hatching
        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        # Add error bars only on right end of each stack
        if mineral == MINERAL_ORDER[-1]:  # Last mineral (right end of stack)
            ax_a.errorbar(lefts + values, y_positions,
                         xerr=[errors_low, errors_high],
                         fmt='none', ecolor='black', capsize=3, capthick=1.5,
                         linewidth=1.5, zorder=10)

        lefts += values

    # Format Panel A
    ax_a.set_xlabel('Net Export Revenue (Billion USD)', fontsize=13, fontweight='bold')
    ax_a.set_title('A. Net Export Revenue by Mineral', fontsize=13, fontweight='bold', pad=15)
    ax_a.set_yticks(y_positions)
    ax_a.set_yticklabels(scenario_labels, fontsize=10)
    ax_a.invert_yaxis()  # Top to bottom
    ax_a.grid(axis='x', linestyle='--', alpha=0.3)
    ax_a.set_axisbelow(True)

    # Create legend with mineral colors - place outside plot on right
    mineral_patches = [mpatches.Patch(color=reference_mineral_colormap[m],
                                     label=m.capitalize())
                      for m in MINERAL_ORDER]
    leg1 = ax_a.legend(handles=mineral_patches,
                       bbox_to_anchor=(1.02, 1), loc='upper left',
                       frameon=True, fontsize=9, ncol=1, title='Minerals')

    # Add hatching legend - place below mineral legend
    hatching_patches = [
        mpatches.Patch(facecolor='white', edgecolor='black', label='Unconstrained'),
        mpatches.Patch(facecolor='white', edgecolor='black', hatch='//', label='Constrained')
    ]
    leg2 = ax_a.legend(handles=hatching_patches,
                       bbox_to_anchor=(1.02, 0.55), loc='upper left',
                       frameon=True, fontsize=9, title='Constraint')
    ax_a.add_artist(leg1)

    # Panel B: Net Export Revenue by Processing Type
    ax_b = axes[1]

    # Calculate bar values (mid demand) and error bars (low-high range)
    processing_bars = {ptype: [] for ptype in PROCESSING_ORDER}
    processing_errors_low = {ptype: [] for ptype in PROCESSING_ORDER}
    processing_errors_high = {ptype: [] for ptype in PROCESSING_ORDER}

    for label in scenario_labels:
        for ptype in PROCESSING_ORDER:
            mid_val = revenue_by_processing_data[label]['mid'].get(ptype, 0) / 1e9  # Convert to billions
            low_val = revenue_by_processing_data[label]['low'].get(ptype, 0) / 1e9
            high_val = revenue_by_processing_data[label]['high'].get(ptype, 0) / 1e9

            processing_bars[ptype].append(mid_val)
            processing_errors_low[ptype].append(mid_val - low_val)
            processing_errors_high[ptype].append(high_val - mid_val)

    # Plot stacked horizontal bars
    lefts_b = np.zeros(len(scenario_labels))
    for ptype in PROCESSING_ORDER:
        values = np.array(processing_bars[ptype])
        errors_low = np.array(processing_errors_low[ptype])
        errors_high = np.array(processing_errors_high[ptype])

        bars = ax_b.barh(y_positions, values, bar_height,
                        left=lefts_b,
                        label=ptype,
                        color=PROCESSING_TYPE_COLORS.get(ptype, '#999999'),
                        edgecolor='black', linewidth=0.5)

        # Apply hatching
        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)

        # Add error bars only on right end of each stack
        if ptype == PROCESSING_ORDER[-1]:  # Last processing type (right end of stack)
            ax_b.errorbar(lefts_b + values, y_positions,
                         xerr=[errors_low, errors_high],
                         fmt='none', ecolor='black', capsize=3, capthick=1.5,
                         linewidth=1.5, zorder=10)

        lefts_b += values

    # Format Panel B
    ax_b.set_xlabel('Net Export Revenue (Billion USD)', fontsize=13, fontweight='bold')
    ax_b.set_title('B. Net Export Revenue by Processing Type', fontsize=13, fontweight='bold', pad=15)
    ax_b.set_yticks(y_positions)
    ax_b.set_yticklabels(scenario_labels, fontsize=10)
    ax_b.invert_yaxis()  # Top to bottom
    ax_b.grid(axis='x', linestyle='--', alpha=0.3)
    ax_b.set_axisbelow(True)

    # Create legend with processing type colors - place outside plot on right
    ptype_patches = [mpatches.Patch(color=PROCESSING_TYPE_COLORS[p],
                                    label=p)
                    for p in PROCESSING_ORDER]
    leg3 = ax_b.legend(handles=ptype_patches,
                       bbox_to_anchor=(1.02, 1), loc='upper left',
                       frameon=True, fontsize=9, ncol=1, title='Processing Types')

    # Adjust layout to leave space for legends on the right
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    # Save figure
    output_path = os.path.join(output_dir, 'economic_indicators_net_revenue_SI.png')
    output_path_pdf = os.path.join(output_dir, 'economic_indicators_net_revenue_SI.pdf')
    output_path_preview = os.path.join(output_dir, 'economic_indicators_net_revenue_SI_preview.png')

    # Get all legend artists for bbox_extra_artists
    all_legends = [leg1, leg2, leg3]

    plt.savefig(output_path, dpi=300, bbox_inches='tight', bbox_extra_artists=all_legends)
    plt.savefig(output_path_pdf, bbox_inches='tight', bbox_extra_artists=all_legends)
    plt.savefig(output_path_preview, dpi=150, bbox_inches='tight', bbox_extra_artists=all_legends)
    plt.close()

    print(f"  ✓ Saved: {output_path}")
    print(f"  ✓ Saved: {output_path_pdf}")
    print(f"  ✓ Saved: {output_path_preview}")

    return [output_path, output_path_pdf, output_path_preview]


def generate_economic_indicators_SI_figures(df, output_dir):
    """
    Main function to generate net export revenue SI figure

    Note: This function takes df parameter for consistency with other publication
    figure generators, but actually uses tonnage_flows_with_revenues.xlsx data.

    Args:
        df: Main data DataFrame (not used, kept for API consistency)
        output_dir: Output directory for figures

    Returns:
        list: Paths to generated figures
    """
    print("\n[Economic Indicators SI - Net Export Revenue]")
    print("-" * 80)

    # Load tonnage flows data (with revenues/costs)
    print("Loading tonnage flows with revenue/cost data...")
    df_flows = load_tonnage_flows_with_revenues()
    print(f"  ✓ Loaded {len(df_flows)} flow records")

    # Prepare data
    print("Preparing net export revenue data...")
    revenue_by_mineral_data, revenue_by_processing_data = prepare_net_revenue_data(df_flows)
    print("  ✓ Data prepared")

    # Create figure
    print("Creating two-panel figure...")
    paths = create_net_revenue_panels(revenue_by_mineral_data, revenue_by_processing_data, output_dir)

    return paths


if __name__ == '__main__':
    """Standalone execution for testing"""
    # Load config
    config_path = Path(__file__).parent.parent.parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    output_dir = Path(config['paths']['figures']) / 'automated_plots' / 'publication' / 'economic_indicators'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("NET EXPORT REVENUE SI FIGURE GENERATION")
    print("="*80)
    print(f"Output directory: {output_dir}")
    print()

    # Generate figures (df parameter not used but kept for consistency)
    paths = generate_economic_indicators_SI_figures(None, output_dir)

    print()
    print("="*80)
    print(f"GENERATED {len(paths)} FILES")
    print("="*80)
