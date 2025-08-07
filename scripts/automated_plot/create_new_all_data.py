import pandas as pd
import os
import json

def create_all_data_from_combined_transport_file(input_file_path, output_file_path):
    """
    Create all_data.xlsx from combined_transport_totals_by_stage.xlsx
    Reuses the exact aggregation logic from new_bar_charts.py but with updated file path
    Note: This version uses combined transport totals without energy data for now
    """
    print(f"Reading data from: {input_file_path}")
    
    # Define the sheets to read (same as original)
    sheets_to_read = ["country_unconstrained", "country_constrained", 
                    "region_unconstrained", "region_constrained"]

    # Read and process each sheet (exact copy from new_bar_charts.py lines 1064-1069)
    df_list = pd.DataFrame()
    for sheet in sheets_to_read:
        print(f"Processing sheet: {sheet}")
        # Use index_col parameter as in the original - the file has multi-level index structure
        df = pd.read_excel(input_file_path, sheet_name=sheet, index_col=[0,1,2,3,4]).reset_index()
        df['constraint'] = sheet
        df_list = pd.concat([df_list, df], ignore_index=True)
    
    print(f"Combined data shape: {df_list.shape}")
    print(f"Columns: {list(df_list.columns)}")
    
    # Unit cost calculations - temporarily without energy (to be restored when energy results are ready)
    unit_costs = [
                    "export_transport_cost_usd_per_tonne",
                    "import_transport_cost_usd_per_tonne",
                    "production_cost_usd_per_tonne",
                    # TODO: Restore when energy results are ready
                    # "energy_opex_per_tonne",
                    # "energy_investment_usd_per_tonne"
                ]
    
    # Calculate total unit cost - temporarily without energy components
    df_list['production_transport_energy_unit_cost_usd_per_tonne'] = [x+y+z for x,y,z in zip(df_list[unit_costs[0]],df_list[unit_costs[1]],
                                                                                              df_list[unit_costs[2]])]
    # TODO: Restore when energy results are ready
    # df_list['production_transport_energy_unit_cost_usd_per_tonne'] = [x+y+z+zz+zy for x,y,z,zz,zy in zip(df_list[unit_costs[0]],df_list[unit_costs[1]],
    #                                                                                                     df_list[unit_costs[2]], df_list[unit_costs[3]],
    #                                                                                                     df_list[unit_costs[4]])]
    df_list['production_transport_energy_unit_cost_usd_per_tonne'] = df_list['production_transport_energy_unit_cost_usd_per_tonne'].fillna(0)

    # Total cost calculations - temporarily without energy (to be restored when energy results are ready)
    costs = [
                "export_transport_cost_usd",
                "import_transport_cost_usd",
                "production_cost_usd",
                # TODO: Restore when energy results are ready
                # "energy_opex",
                # "energy_investment_usd"
            ]

    # Compute total cost - temporarily without energy components
    df_list["all_cost_usd"] = [x+y+z for x,y,z in zip(df_list[costs[0]],df_list[costs[1]], df_list[costs[2]])]
    # TODO: Restore when energy results are ready
    # df_list["all_cost_usd"] = [x+y+z+zz+zy for x,y,z,zz,zy in zip(df_list[costs[0]],df_list[costs[1]],
    #                                                                                                     df_list[costs[2]], df_list[costs[3]],
    #                                                                                                     df_list[costs[4]])]

    # Fix processing_type classifications if needed
    print("Checking processing_type classifications...")
    
    # Define expected corrections
    processing_type_corrections = [
        {'mineral': 'nickel', 'stage': 2.0, 'expected_type': 'Early refining'},
        {'mineral': 'copper', 'stage': 2.0, 'expected_type': 'Early refining'}
    ]
    
    corrections_made = 0
    for correction in processing_type_corrections:
        mineral = correction['mineral']
        stage = correction['stage']
        expected_type = correction['expected_type']
        
        # Find records that need correction
        mask = (df_list['reference_mineral'] == mineral) & (df_list['processing_stage'] == stage)
        current_types = df_list.loc[mask, 'processing_type'].unique()
        
        # Only apply correction if needed
        if len(current_types) > 0 and expected_type not in current_types:
            old_type = current_types[0]
            count = mask.sum()
            df_list.loc[mask, 'processing_type'] = expected_type
            print(f"Corrected {count} {mineral.title()} Stage {stage} records: {old_type} → {expected_type}")
            corrections_made += count
        elif expected_type in current_types:
            print(f"{mineral.title()} Stage {stage} already correctly classified as '{expected_type}'")
    
    if corrections_made == 0:
        print("No processing_type corrections needed - data already correct")
    else:
        print(f"Total corrections made: {corrections_made}")
    
    # Save to new Excel file
    print(f"Saving aggregated data to: {output_file_path}")
    df_list.to_excel(output_file_path, index=False)
    
    print(f"Successfully created all_data.xlsx with {len(df_list)} rows")
    
    return df_list

def create_unit_costs_file(df_list, output_data_path):
    """
    Create unit_costs.xlsx file - temporarily without energy (to be restored when energy results are ready)
    """
    unit_costs = [
                    "export_transport_cost_usd_per_tonne",
                    "import_transport_cost_usd_per_tonne", 
                    "production_cost_usd_per_tonne",
                    # TODO: Restore when energy results are ready
                    # "energy_opex_per_tonne",
                    # "energy_investment_usd_per_tonne"
                ]
    
    uc_list = df_list[["scenario", "reference_mineral", "iso3", 'processing_type',
                         'processing_stage', "constraint"] + unit_costs + ["production_transport_energy_unit_cost_usd_per_tonne"]]
    uc_list = uc_list.drop_duplicates(subset=[ "scenario", "reference_mineral", "iso3", "processing_type",
                                    "processing_stage", "constraint", "production_transport_energy_unit_cost_usd_per_tonne"
                                        ])

    # Define the grouping columns
    group_cols = ["constraint", "scenario", "reference_mineral", "iso3", "processing_type", "processing_stage"]

    # Define aggregation rules: 
    # - Use 'first' if a unit cost is expected to be constant within a group
    # - Use 'sum' for transport costs (since they can vary by country)

    agg_dict = {col: 'sum' for col in ["export_transport_cost_usd_per_tonne","import_transport_cost_usd_per_tonne"]}  # Transport costs
    # TODO: Restore when energy results are ready
    # agg_dict = {col: 'sum' for col in ["export_transport_cost_usd_per_tonne","import_transport_cost_usd_per_tonne",
    #                                    "energy_opex_per_tonne", "energy_investment_usd_per_tonne"]}  # If cost is different per country
    agg_dict["production_cost_usd_per_tonne"] = 'first'  

    # Aggregate data
    aggregated_df = uc_list.groupby(group_cols, as_index=False).agg(agg_dict)

    # Compute the total unit cost
    aggregated_df["production_transport_energy_unit_cost_usd_per_tonne"] = aggregated_df[unit_costs].sum(axis=1)

    uc_output_file = os.path.join(output_data_path, "unit_costs.xlsx")  
    aggregated_df.to_excel(uc_output_file, index=False)
    print(f"Created unit costs file: {uc_output_file}")
    
    return aggregated_df

def main():
    """
    Main function to create new all_data.xlsx from combined_transport_totals_by_stage.xlsx
    """
    # Load configuration
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config.json")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Set paths
    output_data_path = config['paths']['results']
    
    # Input file - the new combined_transport_totals_by_stage.xlsx (without energy for now)
    input_file = os.path.join(output_data_path, "result_summaries", "combined_transport_totals_by_stage.xlsx")
    
    # Output file - the new all_data.xlsx 
    output_file = os.path.join(output_data_path, "all_data.xlsx")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return False
    
    try:
        # Create the aggregated data
        df_aggregated = create_all_data_from_combined_transport_file(input_file, output_file)
        
        # Create unit costs file
        create_unit_costs_file(df_aggregated, output_data_path)
        
        print("\n" + "="*60)
        print("SUCCESS: New data files created!")
        print(f"- all_data.xlsx: {len(df_aggregated)} rows")
        print(f"- unit_costs.xlsx: Created")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"Error during data processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)