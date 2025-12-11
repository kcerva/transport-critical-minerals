"""
Publication Analysis Module

Publication-ready visualizations for paper submissions, focusing on:
- BAU vs Early Refining vs Precursor Product comparisons
- Demand sensitivity analysis (low/mid/high)
- Policy dimension analysis (national vs regional)
- Constraint analysis (constrained vs unconstrained)

All figures are designed for publication quality with:
- Consistent styling and color schemes
- Error bars/ranges for demand uncertainty
- Clear labels and legends
- Appropriate figure dimensions for journals

Usage:
------
From run_all_figures.py:
    python run_all_figures.py --group publication

Directly:
    cd scripts/automated_plot/publication_analysis
    python plot_publication_all.py

Module Structure:
-----------------
- config.py: Publication-specific configuration (scenarios, colors, dimensions)
- scenario_utils.py: Scenario filtering and demand range calculations
- figure_*.py: Individual figure generation modules
- plot_publication_all.py: Main orchestrator
"""

__version__ = "1.0.0"
__author__ = "Critical Minerals Transport Analysis Team"

# Make key functions available at package level
from .config import (
    PUBLICATION_SCENARIOS,
    DEMAND_PATTERNS,
    POLICY_PATTERNS,
    FIGURE_SIZES,
    DPI_SCREEN,
    DPI_PUBLICATION
)

from .scenario_utils import (
    filter_scenarios_by_goal,
    calculate_demand_ranges,
    extract_scenario_attributes,
    compare_goals_with_ranges
)

__all__ = [
    'PUBLICATION_SCENARIOS',
    'DEMAND_PATTERNS',
    'POLICY_PATTERNS',
    'FIGURE_SIZES',
    'DPI_SCREEN',
    'DPI_PUBLICATION',
    'filter_scenarios_by_goal',
    'calculate_demand_ranges',
    'extract_scenario_attributes',
    'compare_goals_with_ranges'
]
