#!/usr/bin/env python3
"""
Main orchestrator for publication figure generation

This script coordinates the generation of all publication-ready figures,
organizing them into thematic subdirectories under figures/publication/.

Usage:
------
From command line:
    cd scripts/automated_plot/publication_analysis
    python plot_publication_all.py

From run_all_figures.py:
    python run_all_figures.py --group publication

From Python:
    from publication_analysis.plot_publication_all import generate_all_publication_figures
    generate_all_publication_figures(df, output_base_dir)
"""

import os
import sys
import pandas as pd
import json

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publication_analysis.config import PUBLICATION_SCENARIOS
from publication_analysis.scenario_utils import filter_scenarios_by_goal


def generate_all_publication_figures(df, output_base_dir):
    """
    Generate all publication-ready figures

    Args:
        df: Main data DataFrame (from all_data.xlsx)
        output_base_dir: Base figures directory (e.g., '../transport-outputs/figures')

    Returns:
        dict: Mapping of figure type to list of saved file paths
    """
    pub_dir = os.path.join(output_base_dir, 'publication')
    os.makedirs(pub_dir, exist_ok=True)

    print("\n" + "="*80)
    print("GENERATING PUBLICATION FIGURES")
    print("="*80)
    print(f"Output directory: {pub_dir}")
    print(f"Data shape: {df.shape}")
    print(f"Scenarios available: {df['scenario'].nunique()}")
    print("="*80)

    saved_paths = {}

    # ========================================================================
    # 1. Production Indicators
    # ========================================================================
    print("\n[1/4] Production Indicators")
    print("-" * 80)
    production_indicators_dir = os.path.join(pub_dir, 'production_indicators')
    os.makedirs(production_indicators_dir, exist_ok=True)

    try:
        from publication_analysis.figure_production_indicators import generate_production_indicators_figures
        paths = generate_production_indicators_figures(df, production_indicators_dir)
        saved_paths['production_indicators'] = paths
        print(f"✓ Generated {len(paths)} figure(s)")
    except ImportError:
        print("⚠ figure_production_indicators.py not yet implemented - skipping")
        saved_paths['production_indicators'] = []
    except Exception as e:
        print(f"✗ Error: {e}")
        saved_paths['production_indicators'] = []

    # ========================================================================
    # 2. Economic Indicators
    # ========================================================================
    print("\n[2/4] Economic Indicators")
    print("-" * 80)
    economic_dir = os.path.join(pub_dir, 'economic_indicators')
    os.makedirs(economic_dir, exist_ok=True)

    try:
        from publication_analysis.figure_economic_indicators import generate_economic_indicators_figures
        paths = generate_economic_indicators_figures(df, economic_dir)
        saved_paths['economic_indicators'] = paths
        print(f"✓ Generated {len(paths)} figure(s)")
    except ImportError:
        print("⚠ figure_economic_indicators.py not yet implemented - skipping")
        saved_paths['economic_indicators'] = []
    except Exception as e:
        print(f"✗ Error: {e}")
        saved_paths['economic_indicators'] = []

    # ========================================================================
    # 3. Infrastructure Indicators
    # ========================================================================
    print("\n[3/7] Infrastructure Indicators")
    print("-" * 80)
    infrastructure_dir = os.path.join(pub_dir, 'infrastructure_indicators')
    os.makedirs(infrastructure_dir, exist_ok=True)

    try:
        from publication_analysis.figure_infrastructure_indicators import generate_infrastructure_indicators_figures
        paths = generate_infrastructure_indicators_figures(df, infrastructure_dir)
        saved_paths['infrastructure_indicators'] = paths
        print(f"✓ Generated {len(paths)} figure(s)")
    except ImportError:
        print("⚠ figure_infrastructure_indicators.py not yet implemented - skipping")
        saved_paths['infrastructure_indicators'] = []
    except Exception as e:
        print(f"✗ Error: {e}")
        saved_paths['infrastructure_indicators'] = []

    # ========================================================================
    # 3b. Infrastructure Indicators V2 (with electricity capacity change)
    # ========================================================================
    print("\n[3b/7] Infrastructure Indicators V2")
    print("-" * 80)
    infrastructure_v2_dir = os.path.join(pub_dir, 'infrastructure_indicators_v2')
    os.makedirs(infrastructure_v2_dir, exist_ok=True)

    try:
        from publication_analysis.figure_infrastructure_indicators_v2 import generate_infrastructure_indicators_v2_figures
        paths = generate_infrastructure_indicators_v2_figures(df, infrastructure_v2_dir)
        saved_paths['infrastructure_indicators_v2'] = paths
        print(f"✓ Generated {len(paths)} figure(s)")
    except ImportError:
        print("⚠ figure_infrastructure_indicators_v2.py not yet implemented - skipping")
        saved_paths['infrastructure_indicators_v2'] = []
    except Exception as e:
        print(f"✗ Error: {e}")
        saved_paths['infrastructure_indicators_v2'] = []

    # ========================================================================
    # 4. Environmental Indicators
    # ========================================================================
    print("\n[4/7] Environmental Indicators")
    print("-" * 80)
    environmental_dir = os.path.join(pub_dir, 'environmental_indicators')
    os.makedirs(environmental_dir, exist_ok=True)

    try:
        from publication_analysis.figure_environmental_indicators import generate_environmental_indicators_figures
        paths = generate_environmental_indicators_figures(df, environmental_dir)
        saved_paths['environmental_indicators'] = paths
        print(f"✓ Generated {len(paths)} figure(s)")
    except ImportError:
        print("⚠ figure_environmental_indicators.py not yet implemented - skipping")
        saved_paths['environmental_indicators'] = []
    except Exception as e:
        print(f"✗ Error: {e}")
        saved_paths['environmental_indicators'] = []

    # ========================================================================
    # 5. Demand Sensitivity Analysis
    # ========================================================================
    print("\n[5/7] Demand Sensitivity Analysis")
    print("-" * 80)
    demand_dir = os.path.join(pub_dir, 'demand_sensitivity')
    os.makedirs(demand_dir, exist_ok=True)

    try:
        from publication_analysis.figure_demand_sensitivity import generate_demand_sensitivity_figures
        paths = generate_demand_sensitivity_figures(df, demand_dir)
        saved_paths['demand_sensitivity'] = paths
        print(f"✓ Generated {len(paths)} figure(s)")
    except ImportError:
        print("⚠ figure_demand_sensitivity.py not yet implemented - skipping")
        saved_paths['demand_sensitivity'] = []
    except Exception as e:
        print(f"✗ Error: {e}")
        saved_paths['demand_sensitivity'] = []

    # ========================================================================
    # 6. Policy Dimension Comparison
    # ========================================================================
    print("\n[6/7] Policy Dimension Comparison")
    print("-" * 80)
    policy_dir = os.path.join(pub_dir, 'policy_comparison')
    os.makedirs(policy_dir, exist_ok=True)

    try:
        from publication_analysis.figure_policy_comparison import generate_policy_comparison_figures
        paths = generate_policy_comparison_figures(df, policy_dir)
        saved_paths['policy_comparison'] = paths
        print(f"✓ Generated {len(paths)} figure(s)")
    except ImportError:
        print("⚠ figure_policy_comparison.py not yet implemented - skipping")
        saved_paths['policy_comparison'] = []
    except Exception as e:
        print(f"✗ Error: {e}")
        saved_paths['policy_comparison'] = []

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "="*80)
    print("PUBLICATION FIGURES SUMMARY")
    print("="*80)
    total_figures = sum(len(paths) for paths in saved_paths.values())
    print(f"Total figures generated: {total_figures}")
    for category, paths in saved_paths.items():
        print(f"  - {category}: {len(paths)} figure(s)")
    print(f"\nAll figures saved to: {pub_dir}")
    print("="*80)

    return saved_paths


def verify_data_availability(df):
    """
    Verify that required scenarios are present in the data

    Args:
        df: Input dataframe

    Prints summary of available data
    """
    print("\nData Availability Check:")
    print("-" * 80)

    scenarios_in_data = set(df['scenario'].unique())

    for goal, config in PUBLICATION_SCENARIOS.items():
        expected_scenarios = set(config['scenarios'])
        available = expected_scenarios & scenarios_in_data
        missing = expected_scenarios - scenarios_in_data

        print(f"\n{goal.upper()}:")
        print(f"  Expected: {len(expected_scenarios)} scenarios")
        print(f"  Available: {len(available)} scenarios")

        if missing:
            print(f"  ⚠ Missing: {len(missing)} scenarios")
            for s in sorted(missing):
                print(f"    - {s}")

    print("\nConstraints available:")
    for constraint in df['constraint'].unique():
        count = len(df[df['constraint'] == constraint])
        print(f"  - {constraint}: {count} rows")

    print("-" * 80)


if __name__ == "__main__":
    """
    Run publication figure generation from command line
    """
    # Determine project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..', '..', '..')

    # Load config
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: config.json not found at {config_path}")
        print("Please ensure you're running from the correct directory.")
        sys.exit(1)

    # Load data
    data_file = os.path.join(config['paths']['results'], 'all_data.xlsx')
    print(f"Loading data from: {data_file}")

    try:
        df = pd.read_excel(data_file, index_col=[0,1,2,3,4])
        df = df.reset_index()
        print(f"✓ Data loaded successfully: {df.shape}")
    except FileNotFoundError:
        print(f"Error: all_data.xlsx not found at {data_file}")
        sys.exit(1)

    # Verify data availability
    verify_data_availability(df)

    # Generate figures (match run_all_figures.py path structure with automated_plots)
    output_dir = os.path.join(config['paths']['figures'], 'automated_plots')
    saved_paths = generate_all_publication_figures(df, output_dir)

    # Print file paths for easy access
    print("\nGenerated files:")
    for category, paths in saved_paths.items():
        if paths:
            print(f"\n{category}:")
            for path in paths:
                print(f"  - {path}")
