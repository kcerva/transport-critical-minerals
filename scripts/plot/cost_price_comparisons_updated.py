import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pathlib import Path

def load_current_data():
    """Load current cost and price data from Final_Price_and_Costs_RP.xlsx"""
    
    # Find the file in transport-outputs/data
    project_root = Path(__file__).parent.parent.parent.parent
    file_path = project_root / "transport-outputs" / "data" / "Final_Price_and_Costs_RP.xlsx"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find {file_path}")
    
    # Load current data sheets
    prices = pd.read_excel(file_path, sheet_name='Price_final')
    capex = pd.read_excel(file_path, sheet_name='CapEx_final')
    opex = pd.read_excel(file_path, sheet_name='OpEx_final')
    
    return {
        'prices': prices,
        'capex': capex,
        'opex': opex
    }

def convert_excel_to_dict_format(excel_data):
    """Convert Excel data format to the dictionary format expected by plotting functions"""
    
    mineral_cost = {}
    mineral_price = {}
    
    # Process each dataframe
    for data_type, df in excel_data.items():
        # Clean up the dataframe
        df_clean = df.copy()
        # Forward fill mineral names
        df_clean['reference_mineral'] = df_clean['reference_mineral'].ffill()
        
        # Group by mineral
        for mineral in df_clean['reference_mineral'].unique():
            if pd.isna(mineral):
                continue
                
            mineral_data = df_clean[df_clean['reference_mineral'] == mineral]
            
            if mineral.lower() not in mineral_cost:
                mineral_cost[mineral.lower()] = {'stages': [], 'capex': {}, 'opex': {}}
            if mineral.lower() not in mineral_price:
                mineral_price[mineral.lower()] = {'stages': [], 'prices': {}}
            
            # Extract stages and values for each year
            for _, row in mineral_data.iterrows():
                if pd.isna(row['processing_stage']):
                    continue
                stage = str(row['processing_stage']).replace('.0', '')
                if stage == 'nan':
                    continue
                stage_key = f'Stage {stage}'

                # Skip graphite stage 5
                if mineral.lower() == 'graphite' and stage_key == 'Stage 5':
                    continue
                
                if stage_key not in mineral_cost[mineral.lower()]['stages']:
                    mineral_cost[mineral.lower()]['stages'].append(stage_key)
                
                if stage_key not in mineral_price[mineral.lower()]['stages']:
                    mineral_price[mineral.lower()]['stages'].append(stage_key)
                
                # Extract values for years 2022, 2030, 2040
                year_cols = [2022, 2030, 2040]

                if data_type == 'capex':
                    values = []
                    for year in year_cols:
                        if year in row:
                            values.append(float(row[year]) if pd.notna(row[year]) else 0)
                        else:
                            values.append(0)
                    mineral_cost[mineral.lower()]['capex'][stage_key] = values

                elif data_type == 'opex':
                    values = []
                    for year in year_cols:
                        if year in row:
                            values.append(float(row[year]) if pd.notna(row[year]) else 0)
                        else:
                            values.append(0)
                    mineral_cost[mineral.lower()]['opex'][stage_key] = values

                elif data_type == 'prices':
                    values = []
                    for year in year_cols:
                        if year in row:
                            values.append(float(row[year]) if pd.notna(row[year]) else 0)
                        else:
                            values.append(0)
                    mineral_price[mineral.lower()]['prices'][stage_key] = values
    
    return mineral_cost, mineral_price

# Load current data and convert to expected format
print("Loading current cost and price data from Excel file...")
excel_data = load_current_data()
mineral_cost, mineral_price = convert_excel_to_dict_format(excel_data)

# Updated data for minerals
years = ['2022', '2030', '2040']

# Stage color map
stage_colors = {
    'Stage 1': ('#1f77b4', '#aec7e8'),
    'Stage 2': ('#ff7f0e', '#ffbb78'),
    'Stage 3': ('#2ca02c', '#98df8a'),
    'Stage 3.1': ('#2ca02c', '#98df8a'),
    'Stage 4': ('#9467bd', '#c5b0d5'),
    'Stage 4.1': ('#9467bd', '#c5b0d5'),
    'Stage 4.2': ('#9467bd', '#c5b0d5'),
    'Stage 4.3': ('#9467bd', '#c5b0d5'),
    'Stage 5': ('#e377c2', '#f7b6d2')
}

stage_line_colors = {k: v[0] for k, v in stage_colors.items()}

# Custom readable stage names by mineral
custom_stage_names = {
    'Copper': {
        'Stage 1': 'Concentrate',
        'Stage 2': 'Anode',
        'Stage 3': 'Cathode',
        'Stage 4.3': 'Oxide',
        'Stage 5': 'Sulphate'
    },
    'Cobalt': {
        'Stage 1': 'Concentrate',
        'Stage 2': 'Matte',
        'Stage 3': 'Refined Co',
        'Stage 4.1': 'Hydroxide',
        'Stage 5': 'Sulphate'
    },
    'Nickel': {
        'Stage 1': 'Concentrate',
        'Stage 2': 'Matte',
        'Stage 3': 'Class 1',
        'Stage 5': 'Sulphate'
    },
    'Lithium': {
        'Stage 1': 'Concentrate',
        'Stage 3': 'Carbonate',
        'Stage 4.2': 'Hydroxide'
    },
    'Manganese': {
        'Stage 1': 'Concentrate',
        'Stage 3.1': 'Fused material',
        'Stage 4.1': 'Sulphate'
    },
    'Graphite': {
        'Stage 1': 'Concentrate',
        'Stage 3': 'Spherical',
        'Stage 4': 'Spherical Purified'
    }
}

def get_stage_label(mineral, stage):
    """Get readable stage label for a mineral with stage number"""
    mineral_caps = mineral.capitalize()
    stage_num = stage.replace("Stage ", "")
    # Format stage number - remove .0 if it's a whole number
    if stage_num.endswith('.0'):
        stage_num = stage_num[:-2]

    if mineral_caps in custom_stage_names and stage in custom_stage_names[mineral_caps]:
        compound_name = custom_stage_names[mineral_caps][stage]
        return f"{stage_num} - {compound_name}"
    return stage_num

# =========================
# COST SUBPLOTS (2x3 grid)
# =========================

fig_cost, axs_cost = plt.subplots(2, 3, figsize=(20, 12))
axs_cost = axs_cost.flatten()

years_to_show = ['2022', '2040']

for idx, (mineral, data) in enumerate(mineral_cost.items()):
    if idx >= 6:  # Only show up to 6 minerals
        break
        
    ax = axs_cost[idx]
    stages = data['stages']
    capex_data = data['capex']
    opex_data = data['opex']

    # Get available stages with data
    available_stages = [s for s in stages if s in capex_data and s in opex_data]

    # Exclude cobalt Stage 2
    if mineral.lower() == 'cobalt':
        available_stages = [s for s in available_stages if s != 'Stage 2']

    if not available_stages:
        ax.set_title(f'{mineral.capitalize()} - No Data')
        continue

    x = np.arange(len(available_stages))
    bar_width = 0.35

    max_total_height = 0

    for i, stage in enumerate(available_stages):
        for j, year in enumerate(years_to_show):
            xpos = x[i] + j * (bar_width + 0.05)
            cap_val = capex_data[stage][years.index(year)]
            ope_val = opex_data[stage][years.index(year)]

            total_height = cap_val + ope_val
            max_total_height = max(max_total_height, total_height)

            # Plot stacked bars
            ax.bar(xpos, cap_val, bar_width, color=stage_colors[stage][0])
            ax.bar(xpos, ope_val, bar_width, bottom=cap_val, color=stage_colors[stage][1])

            # Add year label
            ax.text(xpos, total_height + total_height * 0.03, str(year),
                    ha='center', va='bottom', fontsize=9, fontweight='bold', rotation=90)

    # Set Y-axis limit
    ax.set_ylim(0, max_total_height * 1.38)

    # Custom legend handles
    custom_handles = []
    for stage in available_stages:
        stage_number = stage.replace("Stage ", "")
        cap_patch = plt.Rectangle((0, 0), 1, 1, color=stage_colors[stage][0], label=f'{stage_number} CAPEX')
        ope_patch = plt.Rectangle((0, 0), 1, 1, color=stage_colors[stage][1], label=f'{stage_number} OPEX')
        custom_handles.extend([cap_patch, ope_patch])

    ax.set_title(f'{mineral.capitalize()}')
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    ax.set_ylabel('USD/tonne')

    xtick_locs = x + ((len(years_to_show) - 1) / 2) * (bar_width + 0.05)
    xtick_labels = [get_stage_label(mineral, stage) for stage in available_stages]
    ax.set_xticks(xtick_locs)
    ax.set_xticklabels(xtick_labels, rotation=45, ha='right', fontsize=12)

fig_cost.suptitle('CAPEX and OPEX by Mineral and Stage', fontsize=18)
fig_cost.tight_layout(rect=[0, 0, 1, 0.95], w_pad=3.0)
fig_cost.subplots_adjust(wspace=0.6)

os.makedirs("/home/karlac/critical_minerals_Africa/transport-outputs/figures/cost_price_comparisons", exist_ok=True)

fig_cost.savefig("/home/karlac/critical_minerals_Africa/transport-outputs/figures/cost_price_comparisons/all_minerals_costs.jpeg")

# =========================
# PRICE SUBPLOTS (3x2 grid)
# =========================

fig_price, axs_price = plt.subplots(3, 2, figsize=(11, 12))
axs_price = axs_price.flatten()

for idx, (mineral, data) in enumerate(mineral_price.items()):
    if idx >= 6:
        break

    ax = axs_price[idx]
    stages = data['stages']
    price_data = data['prices']

    # Get available stages with data
    available_stages = [s for s in stages if s in price_data]

    # Exclude cobalt Stage 2
    if mineral.lower() == 'cobalt':
        available_stages = [s for s in available_stages if s != 'Stage 2']

    if not available_stages:
        ax.set_title(f'{mineral.capitalize()} - No Data', fontsize=12, fontweight='bold')
        continue

    for stage in available_stages:
        if stage in stage_line_colors:
            label = get_stage_label(mineral, stage)
            ax.plot(years, price_data[stage], marker='o', label=label, color=stage_line_colors[stage])

    ax.set_title(f'{mineral.capitalize()}', fontsize=12, fontweight='bold')
    ax.set_ylabel('USD/tonne', fontsize=11)
    ax.set_ylim(bottom=0)
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.legend(fontsize=9)
    ax.tick_params(axis='both', labelsize=10)

fig_price.suptitle('Price by Mineral and Stage (2022-2040)', fontsize=16)
fig_price.tight_layout(rect=[0, 0, 0.85, 0.95])
fig_price.subplots_adjust(wspace=0.4, hspace=0.4)
fig_price.savefig("/home/karlac/critical_minerals_Africa/transport-outputs/figures/cost_price_comparisons/all_minerals_prices.jpeg")

print("✅ Cost and price comparison plots generated successfully!")
print("✅ Figures saved to: /transport-outputs/figures/cost_price_comparisons/")
print("  - all_minerals_costs.jpeg")
print("  - all_minerals_prices.jpeg")