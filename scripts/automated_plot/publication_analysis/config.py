"""
Configuration for publication figures

Defines scenario groupings, styling, and output specifications for publication-ready figures.
"""

# Scenario definitions for publication analysis
# Maps logical goals to actual scenario names in all_data.xlsx
PUBLICATION_SCENARIOS = {
    'baseline': {
        'scenarios': ['2022_baseline'],
        'label': '2022 Baseline',
        'short_label': 'Baseline',
        'color': '#636363',  # Gray for baseline
        'include_in_comparisons': False  # Usually shown separately or as reference
    },
    'bau': {
        'scenarios': [
            'bau_2040_low_min_threshold_metal_tons',
            'bau_2040_mid_min_threshold_metal_tons',
            'bau_2040_high_min_threshold_metal_tons',
            'bau_2040_low_max_threshold_metal_tons',
            'bau_2040_mid_max_threshold_metal_tons',
            'bau_2040_high_max_threshold_metal_tons'
        ],
        'label': 'Business as Usual (2040)',
        'short_label': 'BAU',
        'color': '#984ea3',  # Purple
        'target_stage_type': 'Beneficiation'
    },
    'early_refining': {
        'scenarios': [
            'early_refining_2040_low_min_threshold_metal_tons',
            'early_refining_2040_mid_min_threshold_metal_tons',
            'early_refining_2040_high_min_threshold_metal_tons',
            'early_refining_2040_low_max_threshold_metal_tons',
            'early_refining_2040_mid_max_threshold_metal_tons',
            'early_refining_2040_high_max_threshold_metal_tons'
        ],
        'label': 'Early Refining (2040)',
        'short_label': 'Early Refining',
        'color': '#ff7f00',  # Orange
        'target_stage_type': 'Early refining'
    },
    'precursor': {
        'scenarios': [
            'precursor_2040_low_min_threshold_metal_tons',
            'precursor_2040_mid_min_threshold_metal_tons',
            'precursor_2040_high_min_threshold_metal_tons',
            'precursor_2040_low_max_threshold_metal_tons',
            'precursor_2040_mid_max_threshold_metal_tons',
            'precursor_2040_high_max_threshold_metal_tons'
        ],
        'label': 'Precursor Product (2040)',
        'short_label': 'Precursor',
        'color': '#e41a1c',  # Red
        'target_stage_type': 'Precursor related product'
    }
}

# Demand level patterns for scenario name matching
DEMAND_PATTERNS = {
    'low': 'low_',
    'mid': 'mid_',
    'high': 'high_'
}

# Policy patterns for scenario name matching
POLICY_PATTERNS = {
    'national': '_min_',
    'regional': '_max_'
}

# Constraint patterns
CONSTRAINT_PATTERNS = {
    'constrained': 'constrained',
    'unconstrained': 'unconstrained'
}

# Constraint labels for display
CONSTRAINT_LABELS = {
    'country_constrained': 'National Focus (Constrained)',
    'country_unconstrained': 'National Focus (Unconstrained)',
    'region_constrained': 'Regional Integration (Constrained)',
    'region_unconstrained': 'Regional Integration (Unconstrained)'
}

# Shortened constraint labels for compact displays
CONSTRAINT_LABELS_SHORT = {
    'country_constrained': 'National (C)',
    'country_unconstrained': 'National (U)',
    'region_constrained': 'Regional (C)',
    'region_unconstrained': 'Regional (U)'
}

# Publication figure dimensions (inches) for common journal formats
FIGURE_SIZES = {
    'single_column': (3.5, 2.625),       # ~89mm width (Science, Nature single column)
    'one_and_half_column': (5.5, 4.125), # ~140mm width
    'two_column': (7.0, 5.25),           # ~178mm width (Nature two column)
    'full_page': (7.0, 9.0),             # Full page height
    'wide': (10, 6),                     # Wide format for presentations
    'square': (6, 6)                     # Square format
}

# DPI settings
DPI_SCREEN = 150      # For screen display and quick review
DPI_PUBLICATION = 600 # For final publication submission (TIFF/PNG)

# Font sizes for publication figures
FONT_SIZES = {
    'title': 12,
    'axis_label': 10,
    'tick_label': 9,
    'legend': 9,
    'annotation': 8
}

# Color schemes for demand levels (for gradient visualizations)
DEMAND_COLORS = {
    'low': '#d1e5f0',    # Light blue
    'mid': '#67a9cf',    # Medium blue
    'high': '#2166ac'    # Dark blue
}

# Color schemes for policy dimensions
POLICY_COLORS = {
    'national': '#fc8d59',  # Orange
    'regional': '#91bfdb'   # Blue
}

# Metrics commonly used in publication figures
PUBLICATION_METRICS = {
    'production_tonnes': {
        'label': 'Production',
        'unit': 'Mt',
        'scale': 1e-6,
        'decimals': 2
    },
    'revenue_usd': {
        'label': 'Revenue',
        'unit': 'billion USD',
        'scale': 1e-9,
        'decimals': 1
    },
    'total_co2_kt': {
        'label': 'CO₂ Emissions',
        'unit': 'Mt CO₂',
        'scale': 1e-3,
        'decimals': 2
    },
    'water_MCM': {
        'label': 'Water Usage',
        'unit': 'million m³',
        'scale': 1.0,
        'decimals': 1
    },
    'energy_capacity_GW': {
        'label': 'Energy Capacity',
        'unit': 'GW',
        'scale': 1.0,
        'decimals': 2
    },
    'value_added': {
        'label': 'Value Added',
        'unit': 'billion USD',
        'scale': 1e-9,
        'decimals': 2
    }
}

# Matplotlib style parameters for publication figures
PUBLICATION_STYLE = {
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': DPI_SCREEN,
    'savefig.dpi': DPI_PUBLICATION,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.axisbelow': True
}

def get_scenario_color(goal, alpha=1.0):
    """Get color for a scenario goal with optional transparency"""
    if goal not in PUBLICATION_SCENARIOS:
        return '#999999'  # Default gray

    color = PUBLICATION_SCENARIOS[goal]['color']

    if alpha < 1.0:
        # Convert hex to RGBA
        import matplotlib.colors as mcolors
        rgb = mcolors.hex2color(color)
        return (*rgb, alpha)

    return color

def get_metric_info(metric):
    """Get display information for a metric"""
    return PUBLICATION_METRICS.get(metric, {
        'label': metric,
        'unit': '',
        'scale': 1.0,
        'decimals': 2
    })

def format_metric_value(value, metric):
    """Format a metric value for display"""
    info = get_metric_info(metric)
    scaled_value = value * info['scale']
    return f"{scaled_value:.{info['decimals']}f} {info['unit']}"
