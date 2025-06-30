
# Shared configuration for mineral plotting

reference_minerals = ["cobalt", "copper", "graphite", "lithium", "manganese", "nickel"]
reference_minerals_short = ["Co", "Cu", "Gr", "Li", "Mn", "Ni"]
reference_mineral_colors = ["#fdae61", "#f46d43", "#66c2a5", "#c2a5cf", "#fee08b", "#3288bd"]

reference_mineral_colormap = dict(zip(reference_minerals, reference_mineral_colors))
reference_mineral_namemap = dict(zip(reference_minerals, reference_minerals_short))
reference_mineral_colormapshort = dict(zip(reference_minerals_short, reference_mineral_colors))


allowed_mineral_processing = {
    "nickel": {
        "processing_stage": [1, 2, 5],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2030, 2040]
    },
    "copper": {
        "processing_stage": [1, 3, 5],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2030, 2040]
    },
    "cobalt": {
        "processing_stage": [1, 4.1, 5],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2030, 2040]
    },
    "graphite": {
        "processing_stage": [1, 3, 4],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2030, 2040]
    },
    "manganese": {
        "processing_stage": [1, 3.1, 4.1],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2030, 2040]
    },
    "lithium": {
        "processing_stage": [1, 3, 4.2],
        "processing_type": ["Beneficiation", "Early refining", "Precursor related product"],
        "processing_year": [2022, 2030, 2040]
    }
}

