"""
Integrated Value Chain Visualization Module

Creates visualizations for integrated value chain analysis results including:
1. Percentage change by mineral (Regional vs National)
2. Stacked bar charts (Revenue vs Costs)
3. Heatmaps (Country × Mineral)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import json
import os
from plot_config import reference_mineral_colormap

# Load configuration
with open('../../config.json', 'r') as f:
    config = json.load(f)


def load_integrated_analysis_data():
    """Load all integrated analysis CSV files"""
    data_dir = os.path.join(config['paths']['results'], 'integrated_value_chain_analysis')

    all_data = []
    for filename in os.listdir(data_dir):
        if filename.startswith('integrated_analysis_') and filename.endswith('.csv'):
            filepath = os.path.join(data_dir, filename)
            df = pd.read_csv(filepath)
            all_data.append(df)

    return pd.concat(all_data, ignore_index=True)


def calculate_percentage_changes_by_mineral(df):
    """
    Calculate percentage changes in integrated value added by mineral
    comparing Regional vs National policies

    Returns:
    --------
    DataFrame with columns: scenario, constraint_type, reference_mineral,
                           national_value, regional_value, pct_change
    """
    results = []

    # Map constraint names to comparison types
    constraint_map = {
        'country_unconstrained': 'national',
        'country_constrained': 'national',
        'region_unconstrained': 'regional',
        'region_constrained': 'regional'
    }

    # Get unique scenario bases and constraint levels
    # Each combination should compare national vs regional for same constraint level

    # Define the comparisons we want to make
    comparisons = [
        {
            'scenario_base': 'Early Refining 2040',
            'constraint_level': 'Unconstrained',
            'national_scenario': 'early_refining_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_unconstrained',
            'regional_scenario': 'early_refining_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_unconstrained'
        },
        {
            'scenario_base': 'Early Refining 2040',
            'constraint_level': 'Constrained',
            'national_scenario': 'early_refining_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_constrained',
            'regional_scenario': 'early_refining_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_constrained'
        },
        {
            'scenario_base': 'Precursor Product 2040',
            'constraint_level': 'Unconstrained',
            'national_scenario': 'precursor_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_unconstrained',
            'regional_scenario': 'precursor_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_unconstrained'
        },
        {
            'scenario_base': 'Precursor Product 2040',
            'constraint_level': 'Constrained',
            'national_scenario': 'precursor_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_constrained',
            'regional_scenario': 'precursor_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_constrained'
        }
    ]

    for comp in comparisons:
        # Get national data
        national_data = df[
            (df['scenario'] == comp['national_scenario']) &
            (df['constraint'] == comp['national_constraint'])
        ]

        # Get regional data
        regional_data = df[
            (df['scenario'] == comp['regional_scenario']) &
            (df['constraint'] == comp['regional_constraint'])
        ]

        if national_data.empty or regional_data.empty:
            continue

        # Aggregate by mineral
        national_by_mineral = national_data.groupby('reference_mineral')['integrated_value_added'].sum()
        regional_by_mineral = regional_data.groupby('reference_mineral')['integrated_value_added'].sum()

        # Calculate percentage changes
        for mineral in national_by_mineral.index:
            if mineral in regional_by_mineral.index:
                nat_val = national_by_mineral[mineral]
                reg_val = regional_by_mineral[mineral]

                if nat_val != 0:
                    pct_change = ((reg_val - nat_val) / abs(nat_val)) * 100
                else:
                    pct_change = 0 if reg_val == 0 else np.inf

                results.append({
                    'scenario_base': comp['scenario_base'],
                    'constraint_level': comp['constraint_level'],
                    'reference_mineral': mineral,
                    'national_value': nat_val,
                    'regional_value': reg_val,
                    'pct_change': pct_change
                })

    return pd.DataFrame(results)


def plot_percentage_change_by_mineral(pct_change_df, output_dir):
    """
    Create percentage change visualizations by mineral
    Similar format to existing value_added_pct_change plots
    """

    # Create figure for each constraint level
    for constraint_level in ['Unconstrained', 'Constrained']:
        constraint_data = pct_change_df[pct_change_df['constraint_level'] == constraint_level]

        if constraint_data.empty:
            continue

        # Get scenarios
        scenarios = sorted(constraint_data['scenario_base'].unique())

        # Create subplots (one per scenario)
        fig, axes = plt.subplots(len(scenarios), 1, figsize=(12, 6 * len(scenarios)))
        if len(scenarios) == 1:
            axes = [axes]

        # Calculate global x-axis range
        all_pct_changes = constraint_data['pct_change'].values
        x_min = min(all_pct_changes.min(), 0) * 1.1
        x_max = max(all_pct_changes.max(), 0) * 1.1

        for idx, scenario in enumerate(scenarios):
            ax = axes[idx]
            scenario_data = constraint_data[constraint_data['scenario_base'] == scenario].copy()

            # Sort by percentage change
            scenario_data = scenario_data.sort_values('pct_change', ascending=True)

            # Create bars
            minerals = scenario_data['reference_mineral'].values
            pct_changes = scenario_data['pct_change'].values

            # Color bars by mineral
            colors = [reference_mineral_colormap.get(m, '#808080') for m in minerals]

            bars = ax.barh(minerals, pct_changes, color=colors, edgecolor='black', linewidth=0.5)

            # Add zero line
            ax.axvline(x=0, color='black', linestyle='-', linewidth=1)

            # Set labels and title
            ax.set_xlabel('Integrated Value Added Change (%)', fontsize=13, fontweight='bold')
            ax.set_ylabel('Mineral', fontsize=13, fontweight='bold')
            ax.set_title(scenario, fontsize=14, fontweight='bold', pad=15)

            # Set consistent x-axis range
            ax.set_xlim(x_min, x_max)

            # Grid
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)

            # Tick labels
            ax.tick_params(axis='both', labelsize=11)

        # Overall title
        fig.suptitle(
            f'Integrated Value Added Change by Mineral: Regional vs National Integration - {constraint_level}',
            fontsize=16, fontweight='bold'
        )

        plt.tight_layout(rect=[0, 0.04, 1, 0.96])

        # Add subtitle at the bottom
        fig.text(
            0.5, 0.01,
            'Global integrated value added (Revenue - All Costs) aggregated across all countries - shows which minerals\' value chains benefit most from regional integration',
            ha='center', fontsize=10, style='italic', wrap=True
        )

        # Save
        filename = f'integrated_value_added_pct_change_by_mineral_regional_vs_national_{constraint_level.lower()}.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Saved: {filename}")


def calculate_percentage_changes_by_country(df):
    """
    Calculate percentage changes in integrated value added by country
    comparing Regional vs National policies

    Returns top countries by absolute change for visualization
    """
    results = []

    # Define the comparisons we want to make
    comparisons = [
        {
            'scenario_base': 'Early Refining 2040',
            'constraint_level': 'Unconstrained',
            'national_scenario': 'early_refining_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_unconstrained',
            'regional_scenario': 'early_refining_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_unconstrained'
        },
        {
            'scenario_base': 'Early Refining 2040',
            'constraint_level': 'Constrained',
            'national_scenario': 'early_refining_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_constrained',
            'regional_scenario': 'early_refining_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_constrained'
        },
        {
            'scenario_base': 'Precursor Product 2040',
            'constraint_level': 'Unconstrained',
            'national_scenario': 'precursor_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_unconstrained',
            'regional_scenario': 'precursor_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_unconstrained'
        },
        {
            'scenario_base': 'Precursor Product 2040',
            'constraint_level': 'Constrained',
            'national_scenario': 'precursor_2040_mid_min_threshold_metal_tons',
            'national_constraint': 'country_constrained',
            'regional_scenario': 'precursor_2040_mid_max_threshold_metal_tons',
            'regional_constraint': 'region_constrained'
        }
    ]

    for comp in comparisons:
        # Get national data
        national_data = df[
            (df['scenario'] == comp['national_scenario']) &
            (df['constraint'] == comp['national_constraint'])
        ]

        # Get regional data
        regional_data = df[
            (df['scenario'] == comp['regional_scenario']) &
            (df['constraint'] == comp['regional_constraint'])
        ]

        if national_data.empty or regional_data.empty:
            continue

        # Aggregate by country (across all minerals)
        national_by_country = national_data.groupby('iso3')['integrated_value_added'].sum()
        regional_by_country = regional_data.groupby('iso3')['integrated_value_added'].sum()

        # Calculate percentage changes
        for country in national_by_country.index:
            if country in regional_by_country.index:
                nat_val = national_by_country[country]
                reg_val = regional_by_country[country]

                if nat_val != 0:
                    pct_change = ((reg_val - nat_val) / abs(nat_val)) * 100
                else:
                    pct_change = 0 if reg_val == 0 else np.inf

                # Calculate absolute change for filtering
                abs_change = reg_val - nat_val

                results.append({
                    'scenario_base': comp['scenario_base'],
                    'constraint_level': comp['constraint_level'],
                    'iso3': country,
                    'national_value': nat_val,
                    'regional_value': reg_val,
                    'pct_change': pct_change,
                    'abs_change': abs_change
                })

    return pd.DataFrame(results)


def plot_percentage_change_by_country(pct_change_df, output_dir, top_n=15):
    """
    Create percentage change visualizations by country
    Shows top N countries by absolute change value
    """

    # Create figure for each constraint level
    for constraint_level in ['Unconstrained', 'Constrained']:
        constraint_data = pct_change_df[pct_change_df['constraint_level'] == constraint_level]

        if constraint_data.empty:
            continue

        # Get scenarios
        scenarios = sorted(constraint_data['scenario_base'].unique())

        # Create subplots (one per scenario)
        fig, axes = plt.subplots(len(scenarios), 1, figsize=(14, 6 * len(scenarios)))
        if len(scenarios) == 1:
            axes = [axes]

        for idx, scenario in enumerate(scenarios):
            ax = axes[idx]
            scenario_data = constraint_data[constraint_data['scenario_base'] == scenario].copy()

            # Select top N countries by absolute change
            scenario_data = scenario_data.nlargest(top_n, 'abs_change')

            # Sort by percentage change for visualization
            scenario_data = scenario_data.sort_values('pct_change', ascending=True)

            # Create bars
            countries = scenario_data['iso3'].values
            pct_changes = scenario_data['pct_change'].values

            # Color bars: green for positive, red for negative
            colors = ['#2E7D32' if x >= 0 else '#C62828' for x in pct_changes]

            bars = ax.barh(countries, pct_changes, color=colors, edgecolor='black', linewidth=0.5)

            # Add zero line
            ax.axvline(x=0, color='black', linestyle='-', linewidth=1)

            # Set labels and title
            ax.set_xlabel('Integrated Value Added Change (%)', fontsize=13, fontweight='bold')
            ax.set_ylabel('Country', fontsize=13, fontweight='bold')
            ax.set_title(f'{scenario}',
                        fontsize=14, fontweight='bold', pad=15)

            # Grid
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)

            # Tick labels
            ax.tick_params(axis='both', labelsize=11)

        # Overall title
        fig.suptitle(
            f'Integrated Value Added Change by Country: Regional vs National Integration - {constraint_level}',
            fontsize=16, fontweight='bold'
        )

        plt.tight_layout(rect=[0, 0.04, 1, 0.96])

        # Add subtitle at the bottom
        fig.text(
            0.5, 0.01,
            'Countries sorted by absolute change in integrated value added - shows which countries benefit or lose most from regional integration',
            ha='center', fontsize=10, style='italic', wrap=True
        )

        # Save
        filename = f'integrated_value_added_pct_change_by_country_regional_vs_national_{constraint_level.lower()}.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Saved: {filename}")


def plot_revenue_vs_costs_stacked(df, output_dir):
    """
    Create stacked bar charts showing export revenue vs total costs
    for top countries by integrated value added
    """

    # Process each unique scenario-constraint combination
    for scenario in df['scenario'].unique():
        for constraint in df[df['scenario'] == scenario]['constraint'].unique():
            scenario_data = df[(df['scenario'] == scenario) & (df['constraint'] == constraint)].copy()

            # Parse scenario name
            if 'early_refining' in scenario:
                scenario_label = 'Early Refining 2040'
            elif 'precursor' in scenario:
                scenario_label = 'Precursor Product 2040'
            else:
                continue

            # Parse constraint
            if 'unconstrained' in constraint:
                constraint_label = 'Unconstrained'
            else:
                constraint_label = 'Constrained'

            # Parse policy from scenario name (mid_min = national, mid_max = regional)
            if 'mid_min' in scenario:
                policy_label = 'National'
            elif 'mid_max' in scenario:
                policy_label = 'Regional'
            else:
                continue

            # Get top 15 country-mineral combinations by absolute integrated value added
            scenario_data['abs_value_added'] = scenario_data['integrated_value_added'].abs()
            top_entries = scenario_data.nlargest(15, 'abs_value_added')

            if top_entries.empty:
                continue

            # Create figure
            fig, ax = plt.subplots(figsize=(14, 10))

            # Prepare data
            labels = [f"{row['iso3']}-{row['reference_mineral']}" for _, row in top_entries.iterrows()]
            revenues = top_entries['total_export_revenue'].values / 1e9  # Convert to billions
            costs = -top_entries['total_costs'].values / 1e9  # Negative for stacking
            value_added = top_entries['integrated_value_added'].values / 1e9

            # Create positions
            x = np.arange(len(labels))
            width = 0.6

            # Plot bars
            revenue_bars = ax.bar(x, revenues, width, label='Export Revenue',
                                 color='#2E7D32', edgecolor='black', linewidth=0.5)
            cost_bars = ax.bar(x, costs, width, label='Total Costs (negative)',
                              color='#C62828', edgecolor='black', linewidth=0.5)

            # Add value added as scatter points
            ax.scatter(x, value_added, color='#1565C0', s=100, marker='D',
                      label='Integrated Value Added', zorder=5, edgecolor='black', linewidth=0.5)

            # Add zero line
            ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

            # Labels and title
            ax.set_xlabel('Country - Mineral', fontsize=13, fontweight='bold')
            ax.set_ylabel('Value (Billion USD)', fontsize=13, fontweight='bold')
            ax.set_title(f'{scenario_label} - {policy_label} {constraint_label}\nExport Revenue vs Total Costs (Top 15 by Value Added)',
                        fontsize=14, fontweight='bold', pad=15)

            # X-axis
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)

            # Grid and legend
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
            ax.legend(fontsize=11, loc='best')

            plt.tight_layout()

            # Save with clear filename
            policy_short = policy_label.lower()
            constraint_short = constraint_label.lower()
            if 'early_refining' in scenario:
                scenario_short = 'early_refining_2040'
            else:
                scenario_short = 'precursor_2040'

            filename = f'revenue_vs_costs_stacked_{scenario_short}_{policy_short}_{constraint_short}.png'
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"Saved: {filename}")


def plot_country_mineral_heatmap(df, output_dir):
    """
    Create heatmaps showing Country × Mineral integrated value added
    """

    # Process each unique scenario-constraint combination
    for scenario in df['scenario'].unique():
        for constraint in df[df['scenario'] == scenario]['constraint'].unique():
            scenario_data = df[(df['scenario'] == scenario) & (df['constraint'] == constraint)].copy()

            # Parse scenario name
            if 'early_refining' in scenario:
                scenario_label = 'Early Refining 2040'
            elif 'precursor' in scenario:
                scenario_label = 'Precursor Product 2040'
            else:
                continue

            # Parse constraint
            if 'unconstrained' in constraint:
                constraint_label = 'Unconstrained'
            else:
                constraint_label = 'Constrained'

            # Parse policy from scenario name (mid_min = national, mid_max = regional)
            if 'mid_min' in scenario:
                policy_label = 'National'
            elif 'mid_max' in scenario:
                policy_label = 'Regional'
            else:
                continue

            # Create pivot table
            pivot = scenario_data.pivot_table(
                index='iso3',
                columns='reference_mineral',
                values='integrated_value_added',
                aggfunc='sum',
                fill_value=0
            )

            # Convert to billions
            pivot = pivot / 1e9

            # Filter to countries/minerals with significant activity
            # Keep countries with at least one value > 0.1B or < -0.1B
            significant_countries = pivot[(pivot.abs() > 0.1).any(axis=1)].index
            pivot = pivot.loc[significant_countries]

            # Keep minerals that appear
            significant_minerals = pivot.columns[(pivot != 0).any(axis=0)]
            pivot = pivot[significant_minerals]

            if pivot.empty:
                continue

            # Create figure
            fig, ax = plt.subplots(figsize=(12, max(8, len(pivot) * 0.4)))

            # Determine color scale (diverging around zero)
            vmax = max(abs(pivot.min().min()), abs(pivot.max().max()))
            vmin = -vmax

            # Create heatmap
            sns.heatmap(
                pivot,
                cmap='RdYlGn',
                center=0,
                vmin=vmin,
                vmax=vmax,
                annot=True,
                fmt='.1f',
                cbar_kws={'label': 'Integrated Value Added (Billion USD)'},
                linewidths=0.5,
                linecolor='gray',
                ax=ax
            )

            # Labels and title
            ax.set_xlabel('Mineral', fontsize=13, fontweight='bold')
            ax.set_ylabel('Country', fontsize=13, fontweight='bold')
            ax.set_title(
                f'{scenario_label} - {policy_label} {constraint_label}\nIntegrated Value Added by Country and Mineral',
                fontsize=14, fontweight='bold', pad=15
            )

            # Rotate labels
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

            plt.tight_layout()

            # Save with clear filename
            policy_short = policy_label.lower()
            constraint_short = constraint_label.lower()
            if 'early_refining' in scenario:
                scenario_short = 'early_refining_2040'
            else:
                scenario_short = 'precursor_2040'

            filename = f'heatmap_country_mineral_{scenario_short}_{policy_short}_{constraint_short}.png'
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"Saved: {filename}")


def main():
    """Main execution function"""

    print("="*80)
    print("INTEGRATED VALUE CHAIN VISUALIZATIONS")
    print("="*80)

    # Create output directory
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots', 'integrated_value_chain')
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print("\nLoading integrated analysis data...")
    df = load_integrated_analysis_data()
    print(f"Loaded {len(df)} country-mineral-scenario combinations")

    # 1. Percentage change by mineral
    print("\n" + "-"*80)
    print("Creating percentage change by mineral visualizations...")
    print("-"*80)
    pct_change_mineral_df = calculate_percentage_changes_by_mineral(df)
    plot_percentage_change_by_mineral(pct_change_mineral_df, output_dir)

    # 1b. Percentage change by country
    print("\n" + "-"*80)
    print("Creating percentage change by country visualizations...")
    print("-"*80)
    pct_change_country_df = calculate_percentage_changes_by_country(df)
    plot_percentage_change_by_country(pct_change_country_df, output_dir)

    # 2. Revenue vs Costs stacked bars
    print("\n" + "-"*80)
    print("Creating revenue vs costs stacked bar charts...")
    print("-"*80)
    plot_revenue_vs_costs_stacked(df, output_dir)

    # 3. Country × Mineral heatmaps
    print("\n" + "-"*80)
    print("Creating country × mineral heatmaps...")
    print("-"*80)
    plot_country_mineral_heatmap(df, output_dir)

    print("\n" + "="*80)
    print(f"All visualizations saved to: {output_dir}")
    print("="*80)


if __name__ == "__main__":
    main()
