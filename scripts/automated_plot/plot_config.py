
# Shared configuration for mineral plotting

reference_minerals = ["cobalt", "copper", "graphite", "lithium", "manganese", "nickel"]
reference_minerals_short = ["Co", "Cu", "Gr", "Li", "Mn", "Ni"]
reference_mineral_colors = ["#fdae61", "#f46d43", "#66c2a5", "#c2a5cf", "#fee08b", "#3288bd"]

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

