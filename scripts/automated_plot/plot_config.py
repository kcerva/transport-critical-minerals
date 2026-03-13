
# Shared configuration for mineral plotting

reference_minerals = ["cobalt", "copper", "graphite", "lithium", "manganese", "nickel"]
reference_minerals_short = ["Co", "Cu", "Gr", "Li", "Mn", "Ni"]

# OPTIMAL COLOR REASSIGNMENT (Jan 2025)
# Solves copper-cobalt and cobalt-nickel overlap issues in map visualizations
# Same colors, better assignments for overlapping elements
reference_mineral_colors = ["#3288bd", "#fee08b", "#66c2a5", "#c2a5cf", "#fdae61", "#f46d43"]
# Color mapping explanation:
# Cobalt: #3288bd (blue - was nickel) - maximum separation from copper
# Copper: #fee08b (yellow - was manganese) - maximum separation from cobalt  
# Graphite: #66c2a5 (teal - unchanged)
# Lithium: #c2a5cf (purple - unchanged)
# Manganese: #fdae61 (orange - was cobalt) 
# Nickel: #f46d43 (orange-red - was copper)

reference_mineral_colormap = dict(zip(reference_minerals, reference_mineral_colors))
reference_mineral_namemap = dict(zip(reference_minerals, reference_minerals_short))
reference_mineral_colormapshort = dict(zip(reference_minerals_short, reference_mineral_colors))


# New comprehensive mineral processing configuration (with corrected processing_type classifications)
# Supports both goal-focused and stage-comparison analyses

# Complete processing chain definitions based on corrected data structure
mineral_processing_stages = {
    "nickel": {
        "stages": {
            1.0: {"type": "Beneficiation", "is_target": True, "available_scenarios": ["baseline", "bau", "early_refining", "precursor"]},
            2.0: {"type": "Early refining", "is_target": False, "available_scenarios": ["baseline", "early_refining", "precursor"]},  # Corrected: Early refining, intermediate
            3.0: {"type": "Early refining", "is_target": True, "available_scenarios": ["baseline", "early_refining", "precursor"]},   # Target for Early refining goal
            5.0: {"type": "Precursor related product", "is_target": True, "available_scenarios": ["baseline", "precursor"]}
        },
        "target_stages": {
            "Beneficiation": 1.0,                    # BAU goal: Stage 1
            "Early refining": 3.0,                   # Early refining goal: Stage 3 (not Stage 2)
            "Precursor related product": 5.0         # Precursor goal: Stage 5
        }
    },
    "copper": {
        "stages": {
            1.0: {"type": "Beneficiation", "is_target": True, "available_scenarios": ["baseline", "bau", "early_refining", "precursor"]},
            2.0: {"type": "Early refining", "is_target": False, "available_scenarios": ["baseline", "early_refining", "precursor"]},  # Corrected: Early refining, intermediate
            3.0: {"type": "Early refining", "is_target": True, "available_scenarios": ["baseline", "early_refining", "precursor"]},   # Target for Early refining goal
            4.3: {"type": "Precursor related product", "is_target": False, "available_scenarios": ["baseline", "precursor"]},         # Intermediate
            5.0: {"type": "Precursor related product", "is_target": True, "available_scenarios": ["baseline", "precursor"]}          # Target for Precursor goal
        },
        "target_stages": {
            "Beneficiation": 1.0,                    # BAU goal: Stage 1
            "Early refining": 3.0,                   # Early refining goal: Stage 3 (not Stage 2)
            "Precursor related product": 5.0         # Precursor goal: Stage 5 (not Stage 4.3)
        }
    },
    "cobalt": {
        "stages": {
            1.0: {"type": "Beneficiation", "is_target": True, "available_scenarios": ["baseline", "bau", "early_refining", "precursor"]},
            4.1: {"type": "Early refining", "is_target": True, "available_scenarios": ["baseline", "early_refining", "precursor"]},
            5.0: {"type": "Precursor related product", "is_target": True, "available_scenarios": ["baseline", "precursor"]}
        },
        "target_stages": {
            "Beneficiation": 1.0,
            "Early refining": 4.1,
            "Precursor related product": 5.0
        }
    },
    "graphite": {
        "stages": {
            1.0: {"type": "Beneficiation", "is_target": True, "available_scenarios": ["baseline", "bau", "early_refining", "precursor"]},
            3.0: {"type": "Early refining", "is_target": True, "available_scenarios": ["baseline", "early_refining", "precursor"]},
            4.0: {"type": "Precursor related product", "is_target": True, "available_scenarios": ["baseline", "precursor"]}
        },
        "target_stages": {
            "Beneficiation": 1.0,
            "Early refining": 3.0,
            "Precursor related product": 4.0
        }
    },
    "manganese": {
        "stages": {
            1.0: {"type": "Beneficiation", "is_target": True, "available_scenarios": ["baseline", "bau", "early_refining", "precursor"]},
            3.1: {"type": "Early refining", "is_target": True, "available_scenarios": ["baseline", "early_refining", "precursor"]},
            4.1: {"type": "Precursor related product", "is_target": True, "available_scenarios": ["baseline", "precursor"]}
        },
        "target_stages": {
            "Beneficiation": 1.0,
            "Early refining": 3.1,
            "Precursor related product": 4.1
        }
    },
    "lithium": {
        "stages": {
            1.0: {"type": "Beneficiation", "is_target": True, "available_scenarios": ["baseline", "bau", "early_refining", "precursor"]},
            3.0: {"type": "Early refining", "is_target": True, "available_scenarios": ["baseline", "early_refining", "precursor"]},
            4.2: {"type": "Precursor related product", "is_target": True, "available_scenarios": ["baseline", "precursor"]}
        },
        "target_stages": {
            "Beneficiation": 1.0,
            "Early refining": 3.0,
            "Precursor related product": 4.2
        }
    }
}

# Goal-focused filtering: Primary processing focus per scenario type
goal_based_processing = {
    "baseline": {
        # 2022 baseline - show all available processing stages
        "focus_type": "comprehensive",
        "description": "All available processing stages"
    },
    "bau": {
        # Business as Usual - focus on basic beneficiation
        "focus_type": "Beneficiation",
        "description": "Basic mineral processing only"
    },
    "early_refining": {
        # Early refining scenarios - focus on refining capabilities
        "focus_type": "Early refining",
        "description": "Value-added refining processes"
    },
    "precursor": {
        # Precursor/product manufacturing - focus on advanced processing
        "focus_type": "Precursor related product",
        "description": "Advanced product manufacturing"
    }
}

# Stage-comparison filtering: For cross-scenario stage analysis
stage_comparison_sets = {
    "beneficiation_comparison": {
        # Compare Stage 1 (Beneficiation) across all scenarios
        "stages": [1.0],
        "scenarios": ["baseline", "bau", "early_refining", "precursor"],
        "description": "Basic processing comparison across all scenarios"
    },
    "early_refining_comparison": {
        # Compare Early refining stages across relevant scenarios
        "processing_type": "Early refining",
        "scenarios": ["baseline", "early_refining", "precursor"],
        "description": "Early refining development across scenarios"
    },
    "precursor_comparison": {
        # Compare Precursor stages across relevant scenarios
        "processing_type": "Precursor related product", 
        "scenarios": ["baseline", "precursor"],
        "description": "Advanced processing comparison"
    },
    "full_chain_comparison": {
        # Show complete processing chain evolution
        "stages": "all",
        "scenarios": ["baseline", "bau", "early_refining", "precursor"],
        "description": "Complete processing evolution across scenarios"
    }
}

# Analysis type configurations
analysis_types = {
    "goal_comparison": {
        # For comparing 2040 scenario goals - use ONLY target stages
        "filter_method": "target_stages_only",
        "description": "Compare primary goals across scenarios using target stages"
    },
    "stage_evolution": {
        # For showing processing chain development - use ALL stages
        "filter_method": "all_stages",
        "description": "Show complete processing evolution including intermediates"
    },
    "cross_scenario_stage": {
        # For comparing specific stages across scenarios - flexible
        "filter_method": "specified_stages",
        "description": "Compare specific processing stages across scenarios"
    }
}

# Legacy compatibility - simplified version for backward compatibility
allowed_mineral_processing = {
    "nickel": {
        "processing_stage": [1.0, 3.0, 5.0],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2040, 2040]
    },
    "copper": {
        "processing_stage": [1.0, 3.0, 5.0],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2040, 2040]
    },
    "cobalt": {
        "processing_stage": [1.0, 4.1, 5.0],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2040, 2040]
    },
    "graphite": {
        "processing_stage": [1.0, 3.0, 4.0],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2040, 2040]
    },
    "manganese": {
        "processing_stage": [1.0, 3.1, 4.1],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2040, 2040]
    },
    "lithium": {
        "processing_stage": [1.0, 3.0, 4.2],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2040, 2040]
    }
}

# Mineral-specific processing routes for value addition calculation
MINERAL_PROCESSING_ROUTES = {
    # High Priority - Complex Routes
    'copper': {
        'valid_routes': [
            [1.0, 2.0, 3.0, 4.3, 5.0],  # Main route: Beneficiation → Early → Early → Precursor → Precursor
            [1.0, 3.0, 5.0],            # Alternative: Beneficiation → Early → Precursor
            [1.0, 3.0, 4.3, 5.0]        # Additional route: Beneficiation → Early → Precursor → Precursor
        ],
        'invalid_routes': [
            [1.0, 5.0]                   # Direct route - should be flagged as invalid
        ],
        'flag_message': 'Direct Beneficiation→Precursor route detected - should not exist'
    },
    
    'cobalt': {
        'valid_routes': [
            [1.0, 3.0],                  # Beneficiation → Early (terminal - no further processing)
            [1.0, 4.1, 5.0],            # Beneficiation → Early → Precursor  
            [4.1, 5.0]                  # Early → Precursor (disconnected - starts from imported/processed cobalt)
        ],
        'invalid_routes': [],
        'flag_message': None
    },
    
    'nickel': {
        'valid_routes': [
            [1.0, 2.0, 3.0, 5.0],       # Ideal route: Beneficiation → Early → Early → Precursor
            [1.0, 3.0, 5.0]             # Alternative: Beneficiation → Early → Precursor (acceptable)
        ],
        'invalid_routes': [],
        'flag_message': None
    },
    
    # Medium Priority - Some Variation  
    'lithium': {
        'valid_routes': [
            [1.0, 3.0, 4.2],            # Ideal route: Beneficiation → Early → Precursor
            [1.0, 4.2]                  # Alternative: Beneficiation → Precursor (acceptable if occurs)
        ],
        'invalid_routes': [],
        'flag_message': None
    },
    
    'graphite': {
        'valid_routes': [
            [1.0, 3.0, 4.0]             # Standard route: Beneficiation → Early → Precursor
        ],
        'invalid_routes': [],
        'flag_message': None
    },
    
    # Low Priority - Consistent (keeping existing behavior for now)
    'manganese': {
        'valid_routes': [
            [1.0, 3.1, 4.1]             # Standard route: Beneficiation → Early → Precursor
        ],
        'invalid_routes': [],
        'flag_message': None
    }
}

# Helper functions for using the new configuration
def get_target_stage_for_goal(mineral, goal_type):
    """
    Get target processing stage for a specific mineral and goal type.
    
    Args:
        mineral (str): Mineral name (e.g., 'nickel', 'copper')
        goal_type (str): Goal type ('Beneficiation', 'Early refining', 'Precursor related product')
    
    Returns:
        float: Target processing stage for the goal
    """
    if mineral in mineral_processing_stages:
        return mineral_processing_stages[mineral]["target_stages"].get(goal_type)
    return None

def get_stages_for_processing_type(mineral, processing_type, target_only=False):
    """
    Get all stages for a mineral and processing type.
    
    Args:
        mineral (str): Mineral name
        processing_type (str): Processing type
        target_only (bool): If True, return only target stages
    
    Returns:
        list: List of processing stages
    """
    if mineral not in mineral_processing_stages:
        return []
    
    stages = []
    for stage, info in mineral_processing_stages[mineral]["stages"].items():
        if info["type"] == processing_type:
            if not target_only or info["is_target"]:
                stages.append(stage)
    
    return sorted(stages)

def get_goal_from_scenario(scenario):
    """Extract goal type from scenario name (improved version)"""
    if 'bau_2040' in scenario:
        return "bau"
    elif 'early_refining_2040' in scenario:
        return "early_refining"
    elif 'precursor_2040' in scenario:
        return "precursor"
    elif '2022_baseline' in scenario:
        return "baseline"
    else:
        return "unknown"

def get_mineral_processing_routes(mineral):
    """Get valid processing routes for a mineral"""
    if mineral in MINERAL_PROCESSING_ROUTES:
        return MINERAL_PROCESSING_ROUTES[mineral]['valid_routes']
    return []

def get_invalid_mineral_routes(mineral):
    """Get invalid processing routes for a mineral (for flagging)"""
    if mineral in MINERAL_PROCESSING_ROUTES:
        return MINERAL_PROCESSING_ROUTES[mineral]['invalid_routes']
    return []

def get_route_flag_message(mineral):
    """Get flag message for invalid routes"""
    if mineral in MINERAL_PROCESSING_ROUTES:
        return MINERAL_PROCESSING_ROUTES[mineral]['flag_message']
    return None

def find_matching_route(country_stages, valid_routes):
    """
    Find which valid route best matches the country's processing stages
    
    Args:
        country_stages (list): List of processing stages present in country
        valid_routes (list): List of valid route sequences
    
    Returns:
        list: Best matching route, or None if no match
    """
    country_stages_set = set(country_stages)
    
    best_match = None
    best_match_score = 0
    
    for route in valid_routes:
        # Check how many stages in the route are present in country data
        route_stages_in_country = [stage for stage in route if stage in country_stages_set]
        
        # Route is valid if we have all stages in sequence that exist in country
        if len(route_stages_in_country) >= 2:  # Need at least 2 stages for value addition
            # Score = number of matching stages / total route length (prefer complete routes)
            score = len(route_stages_in_country) / len(route)
            if score > best_match_score:
                best_match = route
                best_match_score = score
    
    return best_match

def validate_route_sequence(country_stages, invalid_routes):
    """
    Check if country follows ONLY invalid processing routes (strict interpretation)
    
    Args:
        country_stages (list): List of processing stages present in country
        invalid_routes (list): List of invalid route sequences to check
    
    Returns:
        tuple: (is_invalid, invalid_route_found)
    """
    country_stages_set = set(country_stages)
    
    for invalid_route in invalid_routes:
        # Check if country has EXACTLY the invalid route stages and no others
        # This means they're following the direct invalid pathway
        if set(invalid_route) == country_stages_set:
            return True, invalid_route
    
    return False, None


# =============================================================================
# FIXED COUNTRY COLOR MAPPING
# =============================================================================
# Fixed colors for African countries to ensure consistency across all figures
# Based on matplotlib tab20 palette with alphabetical country ordering
# This ensures colors remain consistent regardless of which countries appear in each figure
COUNTRY_COLORS = {
    "AGO": "#1f77b4",  # Angola
    "BDI": "#aec7e8",  # Burundi
    "BWA": "#ff7f0e",  # Botswana
    "COD": "#ffbb78",  # DR Congo
    "KEN": "#2ca02c",  # Kenya
    "MDG": "#98df8a",  # Madagascar
    "MOZ": "#d62728",  # Mozambique
    "MWI": "#ff9896",  # Malawi
    "NAM": "#9467bd",  # Namibia
    "TZA": "#c5b0d5",  # Tanzania
    "UGA": "#8c564b",  # Uganda
    "ZAF": "#c49c94",  # South Africa
    "ZMB": "#e377c2",  # Zambia
    "ZWE": "#f7b6d2",  # Zimbabwe
    "Other": "#999999",  # Other/aggregated
}

# Short name mapping for countries
COUNTRY_NAMES = {
    "AGO": "Angola",
    "BDI": "Burundi",
    "BWA": "Botswana",
    "COD": "DR Congo",
    "KEN": "Kenya",
    "MDG": "Madagascar",
    "MOZ": "Mozambique",
    "MWI": "Malawi",
    "NAM": "Namibia",
    "TZA": "Tanzania",
    "UGA": "Uganda",
    "ZAF": "South Africa",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
}

