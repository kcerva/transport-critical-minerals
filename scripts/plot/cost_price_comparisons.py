import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pathlib import Path

def load_current_data():
    """Load current cost and price data from Final_Price_and_Costs_RP.xlsx"""
    
    # Find the file in transport-outputs/data
    file_path = Path("/home/karlac/critical_minerals_Africa/transport-outputs/data/Final_Price_and_Costs_RP.xlsx")
    
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

# Updated data for minerals - now loaded dynamically from Excel file above
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
    # 'Stage 4.1 & 4.2': ('#9467bd', '#c5b0d5'),
    'Stage 5': ('#e377c2', '#f7b6d2')
}

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
        'Stage 3.1': 'Oxide',
        'Stage 4.1': 'Sulphate'
    },
    'Graphite': {
        'Stage 1': 'Concentrate',
        'Stage 3': 'Spherical',
        'Stage 4': 'Spherical Purified'
    }
}


stage_line_colors = {k: v[0] for k, v in stage_colors.items()}

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



bar_width = 0.35
group_spacing = 1.5

fig_cost, axs_cost = plt.subplots(3, 2, figsize=(15, 16))  # 3 rows, 2 columns - optimized for tighter spacing
axs_cost = axs_cost.flatten()

# Only use the first and last years
years_to_show = [years[0], years[-1]]

for idx, (mineral, data) in enumerate(mineral_cost.items()):
    ax = axs_cost[idx]
    stages = data['stages']
    capex_data = data['capex']
    opex_data = data['opex']

    # Get available stages with data
    available_stages = [s for s in stages if s in capex_data and s in opex_data]
    
    if not available_stages:
        ax.set_title(f'{mineral.capitalize()} - No Data')
        continue

    # Much more spacing between stage groups to avoid text overlap
    x = np.arange(len(available_stages)) * 2.0
    max_total_height = 0

    for i, stage in enumerate(available_stages):
        for j, year in enumerate(years_to_show):
            xpos = x[i] + j * (bar_width + 0.1)
            cap_val = capex_data[stage][years.index(year)]
            ope_val = opex_data[stage][years.index(year)]

            total_height = cap_val + ope_val
            max_total_height = max(max_total_height, total_height)

            # Use consistent colors - darker for CAPEX, lighter for OPEX
            capex_color = '#2E5A87'  # Dark blue for all CAPEX
            opex_color = '#87CEEB'   # Light blue for all OPEX
            
            # Plot stacked bars
            ax.bar(xpos, cap_val, bar_width, color=capex_color, alpha=0.8)
            ax.bar(xpos, ope_val, bar_width, bottom=cap_val, color=opex_color, alpha=0.8)


    # Simplified subplot title - mineral name only
    ax.set_title(f'{mineral.capitalize()}', fontsize=12, fontweight='bold')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.set_ylabel('USD/tonne', fontsize=11)

    # X-axis labels - stage names horizontal (no rotation to avoid collision with year labels)
    xtick_locs = x + ((len(years_to_show) - 1) / 2) * (bar_width + 0.1)
    xtick_labels = [get_stage_label(mineral, stage) for stage in available_stages]
    ax.set_xticks(xtick_locs)
    ax.set_xticklabels(xtick_labels, rotation=0, ha='center', fontsize=9)

    # Add year labels using axes coordinates (clean approach - no negative axis space)
    for i, stage in enumerate(available_stages):
        # Convert stage position to 0-1 scale relative to axes
        x_pos = (i + 0.5) / len(available_stages) if len(available_stages) > 1 else 0.5
        
        # Position text below axes using transform (closer to horizontal stage labels)
        ax.text(x_pos, -0.12, '2022 | 2040', 
                transform=ax.transAxes, ha='center', va='top', 
                fontsize=8, color='#666666', weight='bold')

    ax.tick_params(axis='both', labelsize=10)
    
    # Normal y-axis scaling (no negative space needed)
    if max_total_height > 0:
        ax.set_ylim(0, max_total_height * 1.05)

# Add clean global legend - years now shown on x-axis
capex_patch = plt.Rectangle((0, 0), 1, 1, color='#2E5A87', alpha=0.8, label='CAPEX')
opex_patch = plt.Rectangle((0, 0), 1, 1, color='#87CEEB', alpha=0.8, label='OPEX')
fig_cost.legend(handles=[capex_patch, opex_patch], 
               loc='upper right', bbox_to_anchor=(0.98, 0.95), fontsize=12)

# Figure-level settings
fig_cost.suptitle('CAPEX and OPEX by Mineral and Stage (2022 vs 2040)', fontsize=16, y=0.98)
fig_cost.tight_layout(rect=[0, 0.10, 0.95, 0.93])  # Reduced space since year labels are closer
fig_cost.subplots_adjust(wspace=0.3, hspace=0.35)  # Tighter spacing between subplots

os.makedirs("/home/karlac/critical_minerals_Africa/transport-outputs/figures/cost_price_comparisons", exist_ok=True)

fig_cost.savefig("/home/karlac/critical_minerals_Africa/transport-outputs/figures/cost_price_comparisons/all_minerals_costs.jpeg")

# =========================
# PRICE SUBPLOTS (2x3 grid)
# =========================
# fig_price, axs_price = plt.subplots(2, 3, figsize=(18, 10))
fig_price, axs_price = plt.subplots(3,2, figsize=(11, 12))
axs_price = axs_price.flatten()

for idx, (mineral, data) in enumerate(mineral_price.items()):
    ax = axs_price[idx]
    stages = data['stages']
    price_data = data['prices']

    # Get available stages with data
    available_stages = [s for s in stages if s in price_data]
    
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