
import pandas as pd
import os
import json
from plot_production_by_country_all_constraints import plot_production_by_country_all_constraints

# Determine project root (three levels up)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))


# Load config.json
config_path = os.path.join(project_root, "config.json")
with open(config_path, "r") as f:
    config = json.load(f)

# Get paths from config
processed_data_path = config['paths']['data']
output_data_path = config['paths']['results']
pivot_data_path = config['paths']['pivot_tables']
figure_path = config['paths']['figures']

# Set input and output paths
all_data_file = os.path.join(output_data_path, "all_data.xlsx")
output_dir = os.path.join(figure_path, "automated_plots", "all_countries")
os.makedirs(output_dir, exist_ok=True)

# Load data
df = pd.read_excel(all_data_file)

# Define goals for each year
goal_by_year = {
    2022: "Early refining",
    2030: "Early refining",
    2040: "Precursor related product"
}

# Run the plotting function
saved_figures = plot_production_by_country_all_constraints(df, output_dir, goal_by_year)

# Print saved file paths
for path in saved_figures:
    print("Saved:", path)

