import os
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import pandas as pd

def create_country_document(country_name, iso3):
    """Create a new Word document with standard formatting for country reports"""
    doc = Document()
    
    # Set document title
    title = doc.add_heading(f'Critical Minerals Value Addition Analysis: {country_name}', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add subtitle
    subtitle = doc.add_paragraph(f'Strategic Development Scenarios for Critical Mineral Processing')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add glossary section
    add_glossary_section(doc)
    
    # Executive summary will be added by generate_country_docx function
    doc.add_page_break()
    
    return doc

def add_section_header(doc, title, level=1):
    """Add a section header to the document"""
    header = doc.add_heading(title, level=level)
    return header

def add_table_from_dataframe(doc, df, title=None, max_width_inches=6.5, interpretation=None):
    """Convert pandas DataFrame to Word table with improved formatting and interpretation"""
    if title:
        doc.add_heading(title, level=3)
    
    # Add interpretation before table if provided
    if interpretation:
        doc.add_paragraph(interpretation)
    
    # Handle empty DataFrame
    if df.empty:
        doc.add_paragraph("No data available for this section.")
        return
    
    # Clean column names to be more readable
    df_clean = df.copy()
    df_clean.columns = [standardise_column_name(col) for col in df_clean.columns]
    
    # Create table
    table = doc.add_table(rows=1, cols=len(df_clean.columns))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Add header row
    hdr_cells = table.rows[0].cells
    for i, column in enumerate(df_clean.columns):
        hdr_cells[i].text = str(column)
        # Make header bold
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    # Add data rows
    for _, row in df_clean.iterrows():
        row_cells = table.add_row().cells
        for i, value in enumerate(row):
            if pd.isna(value):
                row_cells[i].text = "N/A"
            elif isinstance(value, (int, float)):
                # Check if this column contains year data
                column_name = df_clean.columns[i].lower()
                original_column_name = df.columns[i].lower()
                # Don't format numbers that appear to be years
                if ('year' in column_name or 'year' in original_column_name or 
                    (isinstance(value, (int, float)) and 1900 <= value <= 2100)):
                    if isinstance(value, int):
                        row_cells[i].text = str(value)
                    else:  # float
                        row_cells[i].text = str(int(value)) if value.is_integer() else f"{value:.0f}"
                else:
                    row_cells[i].text = format_number_for_display(value)
            else:
                row_cells[i].text = str(value)
    
    # Set table width
    table.autofit = False
    for row in table.rows:
        for cell in row.cells:
            cell.width = Inches(max_width_inches / len(df_clean.columns))
    
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

def add_glossary_section(doc):
    """Add a glossary section explaining key terms"""
    doc.add_heading('Key Terms and Concepts', level=1)
    
    glossary_items = [
        ('Business as Usual (BAU)', 'Continuation of current mineral extraction practices with minimal processing investment.'),
        ('Early Refining', 'Reaching intermediate or full mineral refining capabilities usable in multiple industries.'),
        ('Precursor Product', 'Manufacturing of products which are inputs to battery precursor manufacturing.'),
        ('National Focus', 'Policy approach prioritising domestic industry development.'),
        ('Regional Integration', 'Policy approach emphasising cooperation and trade within the 14 African countries in the study.'),
        ('Environmentally Constrained vs Unconstrained', 'Whether policies include environmental constraints related to areas with biodiversity or future water stress or operate with no restrictions.'),
        ('Metal Content', 'The amount of pure metal that is extracted from raw mineral ores. For graphite, it is not metal, but mineral content'),
        ('Processing Stage', 'Level of value addition: the higher the stage, the higher the processing.'),
    ]
    
    for term, definition in glossary_items:
        p = doc.add_paragraph()
        p.add_run(f'{term}: ').bold = True
        p.add_run(definition)
    
    doc.add_page_break()
    return doc

def create_executive_summary_table(df_country):
    """Create a summary table with key metrics for the executive summary"""
    try:
        # Get key metrics across all constraints and scenarios
        summary_data = []
        
        # Metal content production (processing_stage == 0)
        metal_content = df_country[df_country['processing_stage'] == 0]
        if not metal_content.empty:
            total_production = metal_content.groupby(['constraint', 'scenario'])['production_tonnes'].sum() / 1e3  # Convert to kt
            for (constraint, scenario), production in total_production.items():
                scenario_name = format_scenario_name(scenario)
                constraint_name = format_constraint_name(constraint)
                summary_data.append({
                    'Metric': 'Raw Mineral Production',
                    'Scenario': scenario_name,
                    'Policy Approach': constraint_name,
                    'Value (kt)': f'{production:.1f}'
                })
        
        # Total revenue
        revenue_data = df_country.groupby(['constraint', 'scenario'])['revenue_usd'].sum() / 1e6  # Convert to million USD
        for (constraint, scenario), revenue in revenue_data.items():
            scenario_name = format_scenario_name(scenario)
            constraint_name = format_constraint_name(constraint)
            summary_data.append({
                'Metric': 'Total Revenue',
                'Scenario': scenario_name,
                'Policy Approach': constraint_name,
                'Value (Million USD)': f'{revenue:.1f}'
            })
        
        # CO2 emissions
        emissions_data = df_country.groupby(['constraint', 'scenario'])['energy_tonsCO2eq'].sum() / 1e3  # Convert to kt CO2
        for (constraint, scenario), emissions in emissions_data.items():
            scenario_name = format_scenario_name(scenario)
            constraint_name = format_constraint_name(constraint)
            summary_data.append({
                'Metric': 'CO₂ Emissions',
                'Scenario': scenario_name,
                'Policy Approach': constraint_name,
                'Value (kt CO₂eq)': f'{emissions:.1f}'
            })
        
        return pd.DataFrame(summary_data)
    
    except Exception as e:
        print(f"Error creating executive summary table: {e}")
        return pd.DataFrame({'Error': [str(e)]})

def format_constraint_name(constraint):
    """Format constraint names for display in user-friendly terms"""
    constraint_mapping = {
        'country_constrained': 'National Focus (Environmentally Constrained)',
        'country_unconstrained': 'National Focus (Environmentally Unconstrained)', 
        'region_constrained': 'Regional Integration (Environmentally Constrained)',
        'region_unconstrained': 'Regional Integration (Environmentally Unconstrained)'
    }
    return constraint_mapping.get(constraint, constraint.replace('_', ' ').title())

def format_scenario_name(scenario):
    """Format scenario names for display in user-friendly terms"""
    # Handle 2040 scenarios with clear development strategies
    if '2040' in scenario:
        if 'bau' in scenario.lower():
            return '2040 Business as Usual'
        elif 'early_refining' in scenario.lower():
            return '2040 Early Refining'
        elif 'precursor' in scenario.lower():
            return '2040 Precursor Product'
    
    # Handle other scenarios
    parts = scenario.split('_')
    year = parts[0] if parts[0].isdigit() else '2040'
    
    if 'low' in scenario:
        demand = 'Low Demand'
    elif 'mid' in scenario:
        demand = 'Medium Demand' 
    elif 'high' in scenario:
        demand = 'High Demand'
    else:
        demand = 'Medium Demand'
    
    return f'{year} {demand}'

def standardise_column_name(col_name):
    """Standardise column names for better readability"""
    # Common column name mappings
    column_mapping = {
        'production_tonnes': 'Production (tonnes)',
        'revenue_usd': 'Revenue (million USD)',
        'value_added': 'Value Added (million USD)',
        'energy_tonsCO2eq': 'CO₂ Emissions (kt CO₂eq)',
        'water_use_MCM': 'Water Use (million m³)',
        'transport_volume_million_ton_km': 'Transport Volume (million tonne-km)',
        'constraint': 'Policy Approach',
        'scenario': 'Mineral Development Scenario',
        'processing_stage': 'Processing Stage',
        'reference_mineral': 'Mineral',
        'iso3': 'Country Code'
    }
    
    # Apply mapping or clean up the name
    clean_name = column_mapping.get(col_name, col_name)
    
    # If no direct mapping, clean up the name
    if clean_name == col_name:
        clean_name = col_name.replace('_', ' ').title()
        # Remove technical suffixes
        clean_name = clean_name.replace('Threshold To Metal Tons', '')
        clean_name = clean_name.replace('Usd', 'USD')
        clean_name = clean_name.replace('Co2', 'CO₂')
        clean_name = clean_name.replace('Mcm', '(million m³)')
    
    return clean_name

def format_number_for_display(value):
    """Format numbers for better display in tables"""
    if abs(value) >= 1e6:
        return f"{value/1e6:.1f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.1f}k"
    elif abs(value) >= 100:
        return f"{value:,.0f}"
    elif abs(value) >= 1:
        return f"{value:.1f}"
    else:
        return f"{value:.2f}"

def add_key_findings_section(doc, df_country):
    """Add a key findings section with main insights"""
    doc.add_heading('Key Findings', level=2)
    
    findings = []
    
    try:
        # Find highest revenue scenario
        revenue_by_scenario = df_country.groupby(['constraint', 'scenario'])['revenue_usd'].sum()
        if not revenue_by_scenario.empty:
            best_revenue = revenue_by_scenario.max() / 1e6
            best_scenario = revenue_by_scenario.idxmax()
            constraint_name = format_constraint_name(best_scenario[0])
            scenario_name = format_scenario_name(best_scenario[1])
            findings.append(f"Highest revenue potential: £{best_revenue:.0f} million under {scenario_name} with {constraint_name} policies")
        
        # Compare regional vs national approaches
        regional_revenue = df_country[df_country['constraint'].str.contains('region')]['revenue_usd'].sum() / 1e6
        national_revenue = df_country[df_country['constraint'].str.contains('country')]['revenue_usd'].sum() / 1e6
        
        if regional_revenue > national_revenue:
            diff = ((regional_revenue - national_revenue) / national_revenue) * 100
            findings.append(f"Regional integration approaches show {diff:.0f}% higher revenue potential than national focus strategies")
        else:
            diff = ((national_revenue - regional_revenue) / regional_revenue) * 100
            findings.append(f"National focus approaches show {diff:.0f}% higher revenue potential than regional integration strategies")
        
        # Environmental trade-offs
        emissions_data = df_country.groupby(['constraint', 'scenario'])['energy_tonsCO2eq'].sum()
        if not emissions_data.empty:
            min_emissions = emissions_data.min() / 1e3
            max_emissions = emissions_data.max() / 1e3
            findings.append(f"CO₂ emissions vary significantly across scenarios, from {min_emissions:.0f}kt to {max_emissions:.0f}kt CO₂eq")
    
    except Exception as e:
        findings.append("Unable to generate automated insights from the data")
    
    # Add findings as bullet points
    for finding in findings:
        p = doc.add_paragraph(finding, style='List Bullet')
    
    return doc

def add_table_of_contents(doc):
    """Add a table of contents to the document"""
    try:
        # Add TOC heading
        toc_heading = doc.add_heading('Table of Contents', level=1) 
        toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add TOC field
        paragraph = doc.add_paragraph()
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        
        # Create TOC field XML
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = r'TOC \o "1-3" \h \z \u'
        
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        
        # Add to paragraph
        run._r.append(fldChar1)
        run._r.append(instrText)  
        run._r.append(fldChar2)
        
        # Add note about updating TOC
        note_para = doc.add_paragraph()
        note_para.add_run("Note: ").bold = True
        note_para.add_run("Right-click on the table of contents in Word and select 'Update Field' to refresh the page numbers and headings.")
        note_para.style = 'Caption'
        
        # Add page break after TOC
        doc.add_page_break()
        
        return True
    except Exception as e:
        print(f"Error adding table of contents: {e}")
        return False

def save_document(doc, output_path):
    """Save the document to the specified path"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path