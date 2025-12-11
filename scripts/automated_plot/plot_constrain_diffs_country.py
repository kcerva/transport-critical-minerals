import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import json

# --- input data (kilotonnes, constrained – unconstrained) ---
data = {
    "scenario": [
        "BAU_2040_mid_min_threshold_metal_tons",
        "early_refining_2040_mid_min_threshold_metal_tons",
        "precursor_product_2040_mid_min_threshold_metal_tons"
    ],
    "constraint": ["country", "country", "country"],
    "processing_type": [
        ["Beneficiation","Early refining"],
        ["Beneficiation","Early refining"],
        ["Beneficiation","Early refining","Precursor related product"]
    ],
    "Cu":[[-47.1,-12.3],[-47.1,-15.7],[-47.1,-7.9,-13.3]],
    "Co":[[0,0],[0,0],[0,0]],
}

region_data = {
    "scenario":[
        "BAU_2040_mid_max_threshold_metal_tons",
        "early_refining_2040_mid_max_threshold_metal_tons",
        "precursor_product_2040_mid_max_threshold_metal_tons"
    ],
    "constraint":["region","region","region"],
    "processing_type":[
        ["Beneficiation","Early refining"],
        ["Beneficiation","Early refining"],
        ["Beneficiation","Early refining","Precursor related product"]
    ],
    "Cu":[[-47.1,-12.3],[-47.1,87.4],[-47.1,34.3,88.1]],
    "Co":[[0,0],[0,96.9],[0,67.7,46.4]],
}

# color palette (same as earlier)
colors = {
    "Beneficiation": "#E6B800",
    "Early refining": "#E67300",
    "Precursor related product": "#800000"
}

def plot_diff_scenarios(df_dict, title, output_path, xlim_dict=None):
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
    for ax, sc, cu_vals, co_vals, procs in zip(
        axes, df_dict["scenario"], df_dict["Cu"], df_dict["Co"], df_dict["processing_type"]
    ):
        # build per-mineral stacks
        minerals = []
        if any(v!=0 for v in cu_vals): minerals.append("Cu")
        if any(v!=0 for v in co_vals): minerals.append("Co")

        if len(minerals) == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(sc.replace("_mid_min_threshold_metal_tons","").replace("_mid_max_threshold_metal_tons","").replace("_"," ").title())
            continue

        y_pos = np.arange(len(minerals))

        # Calculate left positions for stacking - need to handle negative values correctly
        # For negative values, we stack from right to left (more negative)
        # For positive values, we stack from left to right (more positive)

        # Separate negative and positive values for each processing type
        negative_left = {m: 0 for m in minerals}
        positive_left = {m: 0 for m in minerals}

        for p_idx, p in enumerate(procs):
            vals = []
            for m in minerals:
                val = cu_vals[p_idx] if m == "Cu" else co_vals[p_idx]
                vals.append(val)

            # Plot bars with appropriate left positions
            lefts = []
            for m_idx, m in enumerate(minerals):
                val = vals[m_idx]
                if val < 0:
                    # Negative value: stack from right (0) going left (negative)
                    lefts.append(negative_left[m])
                    negative_left[m] += val  # Add negative value moves further left
                else:
                    # Positive value: stack from left (0) going right (positive)
                    lefts.append(positive_left[m])
                    positive_left[m] += val  # Add positive value moves further right

            # Plot bars
            ax.barh(y_pos, vals, color=colors[p], label=p, left=lefts)

        ax.set_title(sc.replace("_mid_min_threshold_metal_tons","").replace("_mid_max_threshold_metal_tons","").replace("_"," ").title())
        ax.set_xlabel("Production difference (kilotonne)")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(minerals)
        ax.axvline(0, color='black', lw=0.8)
        ax.grid(axis='x', linestyle=':', alpha=0.5)

        # Apply shared x-axis limits if provided
        if xlim_dict is not None:
            # Extract scenario base name (BAU, early_refining, precursor_product)
            scenario_base = sc.split("_2040")[0]
            if scenario_base in xlim_dict:
                ax.set_xlim(xlim_dict[scenario_base])

    fig.suptitle(title, fontsize=13, fontweight='bold')
    handles = [plt.Rectangle((0,0),1,1,color=colors[k]) for k in colors]
    fig.legend(handles, colors.keys(), loc='lower center', ncol=3, frameon=False)
    plt.tight_layout(rect=[0,0.05,1,0.93])
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Saved: {output_path}")
    return output_path

def main():
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Set up output directory for Zambia constraint difference plots
    output_dir = os.path.join(config['paths']['figures'], 'by_country', 'ZMB')
    os.makedirs(output_dir, exist_ok=True)

    # Calculate shared x-axis limits for each scenario pair (country + region)
    xlim_dict = {}

    for idx, (country_sc, region_sc) in enumerate(zip(data["scenario"], region_data["scenario"])):
        scenario_base = country_sc.split("_2040")[0]

        # Get values for both country and region for this scenario
        country_cu = data["Cu"][idx]
        country_co = data["Co"][idx]
        region_cu = region_data["Cu"][idx]
        region_co = region_data["Co"][idx]

        # Calculate cumulative min/max for country
        country_cu_cumsum = [sum(country_cu[:i+1]) for i in range(len(country_cu))]
        country_co_cumsum = [sum(country_co[:i+1]) for i in range(len(country_co))]
        country_min = min(country_cu_cumsum + country_co_cumsum + [0])
        country_max = max(country_cu_cumsum + country_co_cumsum + [0])

        # Calculate cumulative min/max for region
        region_cu_cumsum = [sum(region_cu[:i+1]) for i in range(len(region_cu))]
        region_co_cumsum = [sum(region_co[:i+1]) for i in range(len(region_co))]
        region_min = min(region_cu_cumsum + region_co_cumsum + [0])
        region_max = max(region_cu_cumsum + region_co_cumsum + [0])

        # Take overall min/max across both
        overall_min = min(country_min, region_min)
        overall_max = max(country_max, region_max)

        # Add 5% padding
        x_range = overall_max - overall_min
        overall_min -= x_range * 0.05
        overall_max += x_range * 0.05

        xlim_dict[scenario_base] = (overall_min, overall_max)

    # --- render both figures with shared x-limits ---
    country_path = os.path.join(output_dir, "zambia_country_constraint_differences.png")
    region_path = os.path.join(output_dir, "zambia_region_constraint_differences.png")

    plot_diff_scenarios(data, "Zambia: Country – Constrained minus Unconstrained (kilotonnes)", country_path, xlim_dict)
    plot_diff_scenarios(region_data, "Zambia: Region – Constrained minus Unconstrained (kilotonnes)", region_path, xlim_dict)

    print(f"\n✅ Zambia constraint difference plots saved to: {output_dir}")

if __name__ == "__main__":
    main()
