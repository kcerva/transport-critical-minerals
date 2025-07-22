import os
import sys
import pandas as pd
import json
import tempfile
from datetime import datetime

# Add parent directories to path to import existing functions
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))
sys.path.append(os.path.dirname(__file__))

# Import existing table generation functions
from data_tables import (
    create_metal_content_table,
    create_production_table, 
    create_production_by_type_table,
    create_revenue_tables,
    create_value_added_tables,
    create_water_use_by_mineral,
    create_transport_emissions_by_mineral,
    create_energy_emissions_by_mineral
)

# Import chart adapters
from chart_adapters import (
    adapt_production_charts,
    adapt_gdp_share_charts, 
    adapt_emissions_charts,
    adapt_water_charts,
    create_policy_difference_chart,
    adapt_goal_comparison_charts
)

# Import DOCX utilities
from docx_utils import (
    create_country_document,
    add_section_header,
    add_table_from_dataframe,
    add_image_from_path,
    add_subsection_with_table_and_chart,
    create_executive_summary_table,
    format_constraint_name,
    format_scenario_name,
    save_document
)

def get_country_name(iso3):
    """Get full country name from ISO3 code"""
    country_mapping = {
        "AGO": "Angola",
        "BDI": "Burundi",
        "BWA": "Botswana",
        "KEN": "Kenya",
        "MWI": "Malawi", 
        "UGA": "Uganda", 
        'ZMB': 'Zambia',
        'COD': 'Democratic Republic of Congo', 
        'ZWE': 'Zimbabwe',
        'NAM': 'Namibia',
        'TZA': 'Tanzania',
        'MDG': 'Madagascar',
        'MOZ': 'Mozambique',
        'ZAF': 'South Africa'
    }
    return country_mapping.get(iso3, iso3)

def generate_country_charts(df_country, iso3, temp_dir):
    """Generate charts for a specific country and return paths"""
    chart_paths = {}
    
    try:
        # Production charts
        production_paths = adapt_production_charts(df_country, iso3, temp_dir)
        if production_paths:
            chart_paths['production'] = production_paths
        
        # GDP share charts for revenue
        revenue_paths = adapt_gdp_share_charts(
            df_country, iso3, temp_dir, 'revenue_usd', 'Revenue Share', 'Revenue (Million USD)'
        )
        if revenue_paths:
            chart_paths['revenue'] = revenue_paths
        
        # GDP share charts for value addition  
        value_paths = adapt_gdp_share_charts(
            df_country, iso3, temp_dir, 'value_added', 'Value Addition Share', 'Value Added (Million USD)'
        )
        if value_paths:
            chart_paths['value_addition'] = value_paths
        
        # Emissions charts
        emissions_paths = adapt_emissions_charts(df_country, iso3, temp_dir)
        if emissions_paths:
            chart_paths['emissions'] = emissions_paths
        
        # Water usage charts  
        water_paths = adapt_water_charts(df_country, iso3, temp_dir)
        if water_paths:
            chart_paths['water'] = water_paths
        
        # Policy difference plots (regional vs national)
        diff_paths = create_policy_difference_chart(df_country, iso3, temp_dir)
        if diff_paths:
            chart_paths['differences'] = diff_paths
        
        # Goal comparison charts (BAU vs Early Refining vs Precursor for 2040)
        goal_comparison_paths = adapt_goal_comparison_charts(df_country, iso3, temp_dir)
        if goal_comparison_paths:
            chart_paths['goal_comparisons'] = goal_comparison_paths
            
    except Exception as e:
        print(f"Error generating charts for {iso3}: {e}")
    
    return chart_paths

def add_metal_content_section(doc, df_country):
    """Add metal content production section"""
    add_section_header(doc, 'Metal Content Production', level=1)
    
    try:
        metal_table = create_metal_content_table(df_country, to_kt=True)
        if not metal_table.empty:
            # Add interpretation
            doc.add_paragraph(
                "The following table shows the metal content (or mineral in the case of graphite) production (processing stage 0) across different "
                "policy constraints and scenarios. Values are shown in kilotonnes (kt) for the country."
            )
            add_table_from_dataframe(doc, metal_table, 
                                   title="Metal Content Production by Constraint (kilotonnes)")
            
            
        else:
            doc.add_paragraph("No metal content production data available.")
            
    except Exception as e:
        doc.add_paragraph(f"Error generating metal content table: {e}")

def add_production_analysis_section(doc, df_country, chart_paths):
    """Add production analysis section with tables and charts"""
    add_section_header(doc, 'Production Analysis by Processing Type', level=1)
    
    try:
        # Production by processing type table
        prod_type_table = create_production_by_type_table(df_country, to_kt=True)
        if not prod_type_table.empty:
            add_table_from_dataframe(doc, prod_type_table,
                                   title="Production by Processing Type and Year (kilotonnes)")
        
        # Production by stage table  
        prod_stage_table = create_production_table(df_country, to_kt=True)
        if not prod_stage_table.empty:
            add_table_from_dataframe(doc, prod_stage_table,
                                   title="Production by Processing Stage and Year (kilotonnes)")
        
        # Add production charts if available
        if 'production' in chart_paths and chart_paths['production']:
            for chart_path in chart_paths['production']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, 
                                      title=f"Production: {os.path.basename(chart_path)}")
        
        doc.add_paragraph(
            "The production analysis shows output across different processing stages and types. "
            "Processing stage 0 represents units of metal content at the extraction stage (or mineral in the case of graphite), while higher stages represent "
            "value-added processing activities."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating production analysis: {e}")

def add_economic_analysis_section(doc, df_country, chart_paths):
    """Add economic analysis section"""
    add_section_header(doc, 'Economic Analysis', level=1)
    
    try:
        # Revenue analysis
        add_section_header(doc, 'Revenue Analysis', level=2)
        rev_summary, rev_by_type = create_revenue_tables(df_country, to_kt=True)
        
        if not rev_summary.empty:
            add_table_from_dataframe(doc, rev_summary, title="Revenue Summary (Million USD)")
        
        if not rev_by_type.empty:
            add_table_from_dataframe(doc, rev_by_type, title="Revenue by Processing Type (Million USD)")
        
        # Add revenue charts
        if 'revenue' in chart_paths and chart_paths['revenue']:
            for chart_path in chart_paths['revenue']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title=f"Revenue")
        
        # Value addition analysis
        add_section_header(doc, 'Value Addition Analysis', level=2)
        va_summary, va_by_type = create_value_added_tables(df_country, to_kt=True)
        
        if not va_summary.empty:
            add_table_from_dataframe(doc, va_summary, title="Value Addition Summary (Million USD)")
        
        if not va_by_type.empty:
            add_table_from_dataframe(doc, va_by_type, title="Value Addition by Processing Type (Million USD)")
        
        # Add value addition charts
        if 'value_addition' in chart_paths and chart_paths['value_addition']:
            for chart_path in chart_paths['value_addition']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title=f"Value Addition")
        
        doc.add_paragraph(
            "The economic analysis examines revenue generation and value addition across different "
            "processing activities and policy scenarios. Value addition represents the economic "
            "benefit gained from higher-stage processing activities."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating economic analysis: {e}")

def add_environmental_impact_section(doc, df_country, chart_paths):
    """Add environmental impact section"""
    add_section_header(doc, 'Environmental Impact Analysis', level=1)
    
    try:
        # Water usage analysis
        add_section_header(doc, 'Water Usage', level=2)
        water_table = create_water_use_by_mineral(df_country, to_kt=True)
        if not water_table.empty:
            add_table_from_dataframe(doc, water_table, title="Water Usage by Mineral (Million m³)")
        
        # Add water charts
        if 'water' in chart_paths and chart_paths['water']:
            for chart_path in chart_paths['water']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Water Usage")
        
        # CO2 emissions analysis  
        add_section_header(doc, 'CO2e Emissions', level=2)
        
        # Transport emissions
        transport_emissions = create_transport_emissions_by_mineral(df_country, to_kt=True)
        if not transport_emissions.empty:
            add_table_from_dataframe(doc, transport_emissions, 
                                   title="Transport Emissions by Mineral (kt CO2eq)")
        
        # Energy emissions
        energy_emissions = create_energy_emissions_by_mineral(df_country, to_kt=True)
        if not energy_emissions.empty:
            add_table_from_dataframe(doc, energy_emissions,
                                   title="Energy Emissions by Mineral (kt CO2eq)")
        
        # Add emissions charts
        if 'emissions' in chart_paths and chart_paths['emissions']:
            for chart_path in chart_paths['emissions']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="CO2 Emissions")
        
        doc.add_paragraph(
            "The environmental impact analysis covers water usage and CO2 emissions from both "
            "transport and energy consumption across different policy scenarios."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating environmental impact analysis: {e}")

def add_policy_comparison_section(doc, df_country, chart_paths):
    """Add policy comparison section"""
    add_section_header(doc, 'Scenario Comparison', level=1)
    
    try:
        doc.add_paragraph(
            "This section compares outcomes between different policy constraints: "
            "Nationalist vs Regionalist approaches, and Constrained vs Unconstrained scenarios."
        )
        
        # Add difference plots if available
        if 'differences' in chart_paths and chart_paths['differences']:
            for chart_path in chart_paths['differences']:
                if os.path.exists(chart_path):
                    chart_name = os.path.basename(chart_path).replace('_', ' ').replace('.png', '')
                    add_image_from_path(doc, chart_path, title=f"Scenario Comparisons: {chart_name}")
        
        doc.add_paragraph(
            "The scenario comparisons show the quantitative differences in production, economic, and "
            "environmental outcomes under different policy scenarios. Positive values indicate "
            "benefits of regionalist or unconstrained approaches."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating policy comparison: {e}")

def add_goal_comparison_section(doc, df_country, chart_paths):
    """Add 2040 goal comparison section"""
    add_section_header(doc, '2040 Goal Comparison Analysis', level=1)
    
    try:
        doc.add_paragraph(
            "This section compares the three 2040 development goals: Business as Usual (BAU), "
            "Early Refining, and Precursor related product scenarios. These comparisons show "
            "how different strategic objectives lead to varying outcomes in production, revenue, "
            "water consumption, and CO2 emissions."
        )
        
        # Add goal comparison plots if available
        if 'goal_comparisons' in chart_paths and chart_paths['goal_comparisons']:
            for chart_path in chart_paths['goal_comparisons']:
                if os.path.exists(chart_path):
                    chart_name = os.path.basename(chart_path).replace('_', ' ').replace('.png', '')
                    add_image_from_path(doc, chart_path, title=f"Goal Comparison: {chart_name}")
        
        doc.add_paragraph(
            "The goal comparison analysis reveals the trade-offs and benefits of pursuing different "
            "strategic development pathways for critical mineral processing."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating goal comparison analysis: {e}")

def generate_country_docx(df_country, iso3, output_dir):
    """Generate a comprehensive DOCX report for a specific country"""
    country_name = get_country_name(iso3)
    print(f"Generating DOCX report for {country_name} ({iso3})")
    
    # Create document
    doc = create_country_document(country_name, iso3)
    
    # Add executive summary table
    try:
        exec_summary = create_executive_summary_table(df_country)
        if not exec_summary.empty:
            add_table_from_dataframe(doc, exec_summary, title="Key Metrics Summary")
        else:
            doc.add_paragraph("Unable to generate executive summary metrics.")
    except Exception as e:
        doc.add_paragraph(f"Error generating executive summary: {e}")
    
    # Generate charts in temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        chart_paths = generate_country_charts(df_country, iso3, temp_dir)
        
        # Add sections
        add_metal_content_section(doc, df_country)
        doc.add_page_break()
        
        add_production_analysis_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        add_economic_analysis_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        add_environmental_impact_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        add_policy_comparison_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        add_goal_comparison_section(doc, df_country, chart_paths)
    
    
    # Save document
    docx_filename = f"{iso3}_country_report.docx"
    docx_path = os.path.join(output_dir, docx_filename)
    save_document(doc, docx_path)
    
    print(f"DOCX report saved: {docx_path}")
    return docx_path

def generate_all_country_docx_reports(df, output_dir):
    """Generate DOCX reports for all countries in the dataset"""
    print("Starting DOCX report generation for all countries...")
    
    generated_reports = []
    countries = df['iso3'].dropna().unique()
    
    for iso3 in countries:
        try:
            df_country = df[df['iso3'] == iso3].copy()
            if not df_country.empty:
                docx_path = generate_country_docx(df_country, iso3, output_dir)
                generated_reports.append(docx_path)
            else:
                print(f"No data found for country: {iso3}")
        except Exception as e:
            print(f"Error generating report for {iso3}: {e}")
    
    print(f"Generated {len(generated_reports)} DOCX reports")
    return generated_reports

if __name__ == "__main__":
    # Load configuration
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config.json")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Set paths
    output_data_path = config['paths']['results']
    docx_output_dir = os.path.join(output_data_path, 'country_reports')
    os.makedirs(docx_output_dir, exist_ok=True)
    
    # Load data
    all_data_file = os.path.join(output_data_path, "all_data.xlsx")
    if not os.path.exists(all_data_file):
        print(f"Error: {all_data_file} not found. Please run the data processing pipeline first.")
        sys.exit(1)
    
    df = pd.read_excel(all_data_file)
    
    # Generate reports
    generated_reports = generate_all_country_docx_reports(df, docx_output_dir)
    
    print(f"All country DOCX reports completed. Output directory: {docx_output_dir}")