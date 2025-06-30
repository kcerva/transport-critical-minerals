
import pandas as pd
import os
import json

from plot_emissions_water_all_countries import plot_metric_by_mineral_all_countries

# Load project paths from config
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(project_root, "config.json")

with open(config_path, "r") as f:
    config = json.load(f)

output_data_path = config['paths']['results']
figure_path = config['paths']['figures']
data_file = os.path.join(output_data_path, "all_data.xlsx")

# Output folder
output_dir = os.path.join(figure_path, "automated_plots", "all_countries")
os.makedirs(output_dir, exist_ok=True)

# Load data
df = pd.read_excel(data_file)

# Plot emissions
plot_metric_by_mineral_all_countries(
    df=df,
    output_dir=output_dir,
    value_column="emissions_kt",
    ylabel="CO₂e emissions (kt)",
    title_prefix="Emissions",
    unit_divisor=1
)

# Plot water use
plot_metric_by_mineral_all_countries(
    df=df,
    output_dir=output_dir,
    value_column="water_m3",
    ylabel="Water use (million m³)",
    title_prefix="Water Use",
    unit_divisor=1e6
)
