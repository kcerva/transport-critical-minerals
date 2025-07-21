import os
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
import pandas as pd

def create_country_document(country_name, iso3):
    """Create a new Word document with standard formatting for country reports"""
    doc = Document()
    
    # Set document title
    title = doc.add_heading(f'Critical Minerals Transport Analysis: {country_name} ({iso3})', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add executive summary placeholder
    doc.add_heading('Executive Summary', level=1)
    doc.add_paragraph('This report presents a comprehensive analysis of critical minerals transport scenarios for {}.'.format(country_name))
    doc.add_page_break()
    
    return doc

def add_section_header(doc, title, level=1):
    """Add a section header to the document"""
    header = doc.add_heading(title, level=level)
    return header

def add_table_from_dataframe(doc, df, title=None, max_width_inches=6.5):
    """Convert pandas DataFrame to Word table with formatting"""
    if title:
        doc.add_heading(title, level=3)
    
    # Handle empty DataFrame
    if df.empty:
        doc.add_paragraph("No data available for this section.")
        return
    
    # Create table
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Add header row
    hdr_cells = table.rows[0].cells
    for i, column in enumerate(df.columns):
        hdr_cells[i].text = str(column)
        # Make header bold
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    # Add data rows
    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, value in enumerate(row):
            if pd.isna(value):
                row_cells[i].text = "N/A"
            elif isinstance(value, (int, float)):
                if abs(value) >= 1000:
                    row_cells[i].text = f"{value:,.1f}"
                else:
                    row_cells[i].text = f"{value:.2f}"
            else:
                row_cells[i].text = str(value)
    
    # Set table width
    table.autofit = False
    for row in table.rows:
        for cell in row.cells:
            cell.width = Inches(max_width_inches / len(df.columns))
    
    doc.add_paragraph()  # Add space after table
    return table

def add_image_from_path(doc, image_path, title=None, width_inches=6.0):
    """Add an image to the document with optional title"""
    if title:
        doc.add_heading(title, level=3)
    
    if os.path.exists(image_path):
        doc.add_picture(image_path, width=Inches(width_inches))
        # Center the image
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        doc.add_paragraph(f"Chart not available: {os.path.basename(image_path)}")
    
    doc.add_paragraph()  # Add space after image
    return image_path

def add_subsection_with_table_and_chart(doc, section_title, table_data, chart_path=None, table_title=None, chart_title=None):
    """Add a subsection with both table and chart"""
    doc.add_heading(section_title, level=2)
    
    # Add table if provided
    if table_data is not None and not table_data.empty:
        add_table_from_dataframe(doc, table_data, title=table_title)
    
    # Add chart if provided
    if chart_path and os.path.exists(chart_path):
        add_image_from_path(doc, chart_path, title=chart_title)
    
    return doc

def create_executive_summary_table(df_country):
    """Create a summary table with key metrics for the executive summary"""
    try:
        # Get key metrics across all constraints and scenarios
        summary_data = []
        
        # Metal content production (processing_stage == 0)
        metal_content = df_country[df_country['processing_stage'] == 0]
        if not metal_content.empty:
            total_production = metal_content.groupby(['constraint', 'scenario'])['production_tonnes'].sum() / 1e6  # Convert to Mt
            for (constraint, scenario), production in total_production.items():
                year = scenario.split('_')[0] if scenario.split('_')[0].isdigit() else 'Unknown'
                summary_data.append({
                    'Metric': f'Metal Content Production ({year})',
                    'Constraint': constraint.replace('_', ' ').title(),
                    'Value': f'{production:.2f} Mt',
                    'Scenario': scenario
                })
        
        # Total revenue
        revenue_data = df_country.groupby(['constraint', 'scenario'])['revenue_usd'].sum() / 1e6  # Convert to MUSD
        for (constraint, scenario), revenue in revenue_data.items():
            year = scenario.split('_')[0] if scenario.split('_')[0].isdigit() else 'Unknown'
            summary_data.append({
                'Metric': f'Revenue ({year})',
                'Constraint': constraint.replace('_', ' ').title(),
                'Value': f'${revenue:.1f}M USD',
                'Scenario': scenario
            })
        
        # CO2 emissions
        emissions_data = df_country.groupby(['constraint', 'scenario'])['energy_tonsCO2eq'].sum() / 1e6  # Convert to Mt CO2
        for (constraint, scenario), emissions in emissions_data.items():
            year = scenario.split('_')[0] if scenario.split('_')[0].isdigit() else 'Unknown'
            summary_data.append({
                'Metric': f'CO2 Emissions ({year})',
                'Constraint': constraint.replace('_', ' ').title(),
                'Value': f'{emissions:.2f} Mt CO2eq',
                'Scenario': scenario
            })
        
        return pd.DataFrame(summary_data)
    
    except Exception as e:
        print(f"Error creating executive summary table: {e}")
        return pd.DataFrame({'Error': [str(e)]})

def format_constraint_name(constraint):
    """Format constraint names for display"""
    constraint_mapping = {
        'country_constrained': 'Nationalist Constrained',
        'country_unconstrained': 'Nationalist Unconstrained', 
        'region_constrained': 'Regionalist Constrained',
        'region_unconstrained': 'Regionalist Unconstrained'
    }
    return constraint_mapping.get(constraint, constraint.replace('_', ' ').title())

def format_scenario_name(scenario):
    """Format scenario names for display"""
    # Extract year and demand level
    parts = scenario.split('_')
    year = parts[0] if parts[0].isdigit() else 'Unknown'
    
    if 'low' in scenario:
        demand = 'Low Demand'
    elif 'mid' in scenario:
        demand = 'Mid Demand' 
    elif 'high' in scenario:
        demand = 'High Demand'
    else:
        demand = 'Unknown Demand'
    
    return f'{year} {demand}'

def save_document(doc, output_path):
    """Save the document to the specified path"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path