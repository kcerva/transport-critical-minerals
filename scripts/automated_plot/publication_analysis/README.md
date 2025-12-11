# Publication Analysis Module

Publication-ready visualizations for paper submissions focusing on global scenario comparisons with demand uncertainty analysis.

## Overview

This module provides a clean, organized structure for generating publication-quality figures that:
- Compare BAU vs Early Refining vs Precursor Product scenarios
- Show demand uncertainty using low/mid/high ranges
- Analyze national vs regional policy dimensions
- Include constraint analysis (constrained vs unconstrained)

## Module Structure

```
publication_analysis/
├── __init__.py                      # Package initialization and exports
├── config.py                        # Publication-specific configuration
├── scenario_utils.py                # Scenario filtering and range calculations
├── plot_publication_all.py          # Main orchestrator
├── figure_bau_vs_precursor.py      # BAU vs Precursor comparisons (to be implemented)
├── figure_demand_sensitivity.py    # Demand uncertainty analysis (to be implemented)
├── figure_policy_comparison.py     # National vs Regional analysis (to be implemented)
└── README.md                        # This file
```

## Key Features

### 1. Centralized Configuration (`config.py`)

Defines:
- **Scenario mappings**: Logical goals (bau, precursor) → actual scenario names
- **Color schemes**: Consistent colors across all figures
- **Figure dimensions**: Journal-appropriate sizes (single column, two column, etc.)
- **Metrics**: Standardized metric definitions with units and scaling
- **Style parameters**: Matplotlib style settings for publication quality

### 2. Reusable Utilities (`scenario_utils.py`)

Provides functions for:
- **Scenario filtering**: Filter by goal, demand, policy, constraint
- **Demand ranges**: Calculate low/mid/high ranges for uncertainty visualization
- **Goal comparison**: Compare multiple goals with error bars
- **Policy comparison**: Analyze national vs regional differences
- **Global aggregation**: Sum metrics across all countries

### 3. Main Orchestrator (`plot_publication_all.py`)

Coordinates figure generation:
- Loads data from `all_data.xlsx`
- Verifies scenario availability
- Calls individual figure generators
- Organizes outputs into themed subdirectories
- Reports summary statistics

## Usage

### From Command Line

Run all publication figures:
```bash
cd scripts/automated_plot
python run_all_figures.py --group publication
```

Or run directly:
```bash
cd scripts/automated_plot/publication_analysis
python plot_publication_all.py
```

Or use the convenient alias:
```bash
python run_all_figures.py --group paper
```

### From Python

```python
from publication_analysis.plot_publication_all import generate_all_publication_figures

# Load your data
df = pd.read_excel('all_data.xlsx', index_col=[0,1,2,3,4]).reset_index()

# Generate all publication figures
saved_paths = generate_all_publication_figures(df, output_base_dir)
```

### Using Utility Functions

```python
from publication_analysis import (
    filter_scenarios_by_goal,
    calculate_demand_ranges,
    compare_goals_with_ranges
)

# Filter to only Precursor scenarios
df_precursor = filter_scenarios_by_goal(df, 'precursor')

# Get production ranges by country (low/mid/high demand)
ranges = calculate_demand_ranges(
    df, 'precursor', 'production_tonnes',
    groupby_cols=['iso3']
)

# Compare BAU vs Precursor with demand ranges
comparison = compare_goals_with_ranges(
    df, ['bau', 'precursor'], 'revenue_usd',
    constraint='unconstrained',
    groupby_cols=['iso3', 'reference_mineral']
)
```

## Output Structure

```
figures/publication/
├── bau_vs_precursor/              # Goal comparison figures
│   ├── production_comparison_demand_ranges.png
│   ├── revenue_comparison_demand_ranges.png
│   └── emissions_comparison_demand_ranges.png
│
├── demand_sensitivity/             # Demand uncertainty figures
│   ├── production_by_demand_level.png
│   ├── revenue_sensitivity_heatmap.png
│   └── emissions_demand_ranges.png
│
└── policy_comparison/              # National vs Regional
    ├── production_national_vs_regional_ranges.png
    └── value_addition_policy_comparison.png
```

## Data Availability

The module automatically verifies data availability on startup:

**Goals Available:**
- `baseline`: 2022_baseline (1 scenario)
- `bau`: BAU 2040 scenarios (6 combinations: 3 demands × 2 policies)
- `early_refining`: Early Refining 2040 scenarios (6 combinations)
- `precursor`: Precursor Product 2040 scenarios (6 combinations)

**Total:** 19 scenarios across all combinations of:
- Demand: low, mid, high
- Policy: national (min), regional (max)
- Constraint: constrained, unconstrained

## Creating New Figures

To add a new publication figure:

1. **Create a new module** (e.g., `figure_my_analysis.py`):

```python
"""
My Analysis Figure

Description of what this figure shows and why it's important for the paper.
"""

import matplotlib.pyplot as plt
from .config import FIGURE_SIZES, DPI_PUBLICATION, PUBLICATION_SCENARIOS
from .scenario_utils import filter_scenarios_by_goal, calculate_demand_ranges

def generate_my_analysis_figures(df, output_dir):
    """
    Generate my analysis figures

    Args:
        df: Main data DataFrame
        output_dir: Output directory for figures

    Returns:
        List of saved file paths
    """
    saved_paths = []

    # Your analysis and plotting code here
    # Use utilities from scenario_utils
    # Use configuration from config

    fig_path = os.path.join(output_dir, 'my_figure.png')
    plt.savefig(fig_path, dpi=DPI_PUBLICATION, bbox_inches='tight')
    saved_paths.append(fig_path)

    return saved_paths
```

2. **Register in orchestrator** (`plot_publication_all.py`):

```python
# Import your module
from publication_analysis.figure_my_analysis import generate_my_analysis_figures

# Add to generate_all_publication_figures():
print("\n[4/4] My Analysis")
my_dir = os.path.join(pub_dir, 'my_analysis')
os.makedirs(my_dir, exist_ok=True)
paths = generate_my_analysis_figures(df, my_dir)
saved_paths['my_analysis'] = paths
```

3. **Test**:
```bash
python run_all_figures.py --group publication
```

## Design Principles

1. **Minimal Duplication**: Reuse `scenario_utils.py` for all data filtering/calculations
2. **Consistent Styling**: Use `config.py` for all colors, sizes, fonts
3. **Publication Quality**: Default to 600 DPI, journal-appropriate dimensions
4. **Clear Organization**: Thematic subdirectories, descriptive filenames
5. **Self-Documenting**: Rich docstrings, clear variable names
6. **Testable**: Each figure module is independently testable

## Available Scenarios

### Scenario Naming Convention

Format: `{goal}_2040_{demand}_{policy}_threshold_metal_tons`

Examples:
- `bau_2040_mid_min_threshold_metal_tons` - BAU, mid-demand, national focus
- `precursor_2040_high_max_threshold_metal_tons` - Precursor, high-demand, regional integration

### Mapping to Filters

- **Goal**: `bau`, `early_refining`, `precursor`
- **Demand**: `low`, `mid`, `high`
- **Policy**: `min` (national), `max` (regional)
- **Constraint**: In `constraint` column, not scenario name

## Configuration Reference

### Figure Sizes (inches)
- `single_column`: 3.5 × 2.625 (Nature single column)
- `two_column`: 7.0 × 5.25 (Nature two column)
- `full_page`: 7.0 × 9.0

### Colors
- BAU: `#984ea3` (purple)
- Early Refining: `#ff7f00` (orange)
- Precursor: `#e41a1c` (red)
- Baseline: `#636363` (gray)

### DPI
- Screen preview: 150
- Publication: 600

## Dependencies

- pandas
- numpy
- matplotlib
- Parent modules: `plot_config.py`, `plot_utils.py`

## Version

Current version: 1.0.0

## Authors

Critical Minerals Transport Analysis Team

## Next Steps

The foundation is complete! Now implement individual figure modules:

1. `figure_bau_vs_precursor.py` - Start here for your example figure
2. `figure_demand_sensitivity.py` - Demand uncertainty analysis
3. `figure_policy_comparison.py` - National vs regional comparison

All the reusable utilities are ready to use!
