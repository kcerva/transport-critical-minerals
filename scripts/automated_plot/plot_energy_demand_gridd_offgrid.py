import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Data - from Camilo's file
data = {
    'Scenario': [
        'Baseline 2022',
        'BAU - Country 2040',
        'Early Refining - Region 2040', 
        'Early Refining - Country 2040',
        'Precursor - Region 2040',
        'Precursor - Country 2040'
    ],
    'Grid_Connection_kWh': [
        14548018100.25,
        14484764485.77,
        47254644481.15,
        43218459077.06,
        41089790238.33,
        33208510970.09
    ],
    'Off_Grid_kWh': [
        873348.56,
        127180.49,
        226394.21,
        209842.11,
        159299.13,
        61730.64
    ]
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Convert units
df['Grid_Connection_GWh'] = df['Grid_Connection_kWh'] / 1e6  # kWh to GWh
df['Off_Grid_MWh'] = df['Off_Grid_kWh'] / 1000              # kWh to MWh

# Create figure and primary axis
fig, ax1 = plt.subplots(figsize=(12, 7))

# Set up bar positions
x = np.arange(len(df['Scenario']))
width = 0.35

# Plot Grid Connection bars (left axis)
bars1 = ax1.bar(x - width/2, df['Grid_Connection_GWh'], width, 
                label='Grid Connection', color='#1f77b4', 
                edgecolor='#1a5490', linewidth=1)

# Configure left axis
ax1.set_xlabel('')
ax1.set_ylabel('Grid Connection (GWh/year)', color='#1f77b4', fontsize=14, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#1f77b4', labelsize=12)
ax1.set_ylim(0, 50000)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

# Create secondary axis
ax2 = ax1.twinx()

# Plot Off-Grid bars (right axis)
bars2 = ax2.bar(x + width/2, df['Off_Grid_MWh'], width,
                label='Off-Grid', color='#ff7f0e',
                edgecolor='#cc5200', linewidth=1)

# Configure right axis
ax2.set_ylabel('Off-Grid (MWh/year)', color='#ff7f0e', fontsize=14, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#ff7f0e', labelsize=12)
ax2.set_ylim(0, 1000)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}'))

# Configure x-axis
ax1.set_xticks(x)
ax1.set_xticklabels(df['Scenario'], rotation=45, ha='right', fontsize=12)
ax1.tick_params(axis='x', labelsize=12)

# Add title
plt.title('Energy Consumption by Scenario', fontsize=18, fontweight='bold', 
          color='#2c3e50', pad=20)

# Add grid
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

# Add legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, 
          loc='upper right', bbox_to_anchor=(1.0, 0.95),
          frameon=True, fancybox=True, shadow=True)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Add subtle styling
fig.patch.set_facecolor('white')
ax1.set_facecolor('white')

# Save high-quality figure
plt.savefig('energy_consumption_scenarios.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')

# Display the plot
plt.show()

# Print summary statistics
print("\nData Summary:")
print("=" * 50)
for i, scenario in enumerate(df['Scenario']):
    print(f"{scenario}:")
    print(f"  Grid Connection: {df['Grid_Connection_GWh'].iloc[i]:,.1f} GWh/year")
    print(f"  Off-Grid: {df['Off_Grid_MWh'].iloc[i]:.1f} MWh/year")
    print()