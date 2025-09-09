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
    create_energy_emissions_by_mineral,
    create_transport_volume_by_mineral,
    create_energy_capacity_by_mineral,
    create_transport_volume_table_with_columns,
    create_energy_capacity_table_with_columns,
    create_transport_volume_table_all_scenarios,
    create_energy_capacity_table_all_scenarios
)

# Import chart adapters
from chart_adapters import (
    adapt_production_charts,
    adapt_gdp_share_charts, 
    adapt_emissions_charts,
    adapt_water_charts,
    create_policy_difference_chart,
    adapt_goal_comparison_charts,
    create_production_difference_charts,
    create_revenue_difference_charts,
    create_consolidated_revenue_chart,
    create_consolidated_production_chart,
    create_consolidated_water_chart,
    create_consolidated_emissions_chart
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
    save_document,
    add_key_findings_section,
    standardise_column_name,
    format_number_for_display,
    add_table_of_contents
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
        
        # Consolidated charts
        consolidated_revenue_dir = os.path.join(temp_dir, f'consolidated_revenue_{iso3}')
        os.makedirs(consolidated_revenue_dir, exist_ok=True)
        consolidated_revenue_path = create_consolidated_revenue_chart(df_country, consolidated_revenue_dir, iso3)
        if consolidated_revenue_path:
            chart_paths['revenue'] = [consolidated_revenue_path]
        
        # Consolidated production chart
        consolidated_production_dir = os.path.join(temp_dir, f'consolidated_production_{iso3}')
        os.makedirs(consolidated_production_dir, exist_ok=True)
        consolidated_production_path = create_consolidated_production_chart(df_country, consolidated_production_dir, iso3)
        if consolidated_production_path:
            chart_paths['production_consolidated'] = [consolidated_production_path]
        
        # Consolidated water chart
        consolidated_water_dir = os.path.join(temp_dir, f'consolidated_water_{iso3}')
        os.makedirs(consolidated_water_dir, exist_ok=True)
        consolidated_water_path = create_consolidated_water_chart(df_country, consolidated_water_dir, iso3)
        if consolidated_water_path:
            chart_paths['water_consolidated'] = [consolidated_water_path]
        
        # Consolidated emissions chart
        consolidated_emissions_dir = os.path.join(temp_dir, f'consolidated_emissions_{iso3}')
        os.makedirs(consolidated_emissions_dir, exist_ok=True)
        consolidated_emissions_path = create_consolidated_emissions_chart(df_country, consolidated_emissions_dir, iso3)
        if consolidated_emissions_path:
            chart_paths['emissions_consolidated'] = [consolidated_emissions_path]
        
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
        
        # Production difference charts (constraint comparison)
        production_diff_dir = os.path.join(temp_dir, f'production_diff_{iso3}')
        os.makedirs(production_diff_dir, exist_ok=True)
        production_diff_paths = create_production_difference_charts(df_country, production_diff_dir, iso3)
        if production_diff_paths:
            chart_paths['production_differences'] = production_diff_paths
        
        # Revenue difference charts (constraint comparison)
        revenue_diff_dir = os.path.join(temp_dir, f'revenue_diff_{iso3}')
        os.makedirs(revenue_diff_dir, exist_ok=True)
        revenue_diff_paths = create_revenue_difference_charts(df_country, revenue_diff_dir, iso3)
        if revenue_diff_paths:
            chart_paths['revenue_differences'] = revenue_diff_paths
            
    except Exception as e:
        print(f"Error generating charts for {iso3}: {e}")
    
    return chart_paths

def add_metal_content_section(doc, df_country):
    """Add metal content production section"""
    add_section_header(doc, 'Metal Content Production', level=1)
    
    try:
        metal_table = create_metal_content_table(df_country, to_kt=True, scenarios_filter='mid_only', consolidated_format=True)
        if not metal_table.empty:
            # Add interpretation
            doc.add_paragraph(
                "This section shows mineral extraction quantities considering only the metal (or mineral in the case of graphite). "
                "Values are shown in kilotonnes (kt). Note: Regional and National values are the same for metal content, "
                "so values shown apply to all policy approaches for each scenario. "
                "Baseline (2022) data is included where available, but may be absent if the country was not extracting minerals in 2022."
            )
            add_table_from_dataframe(doc, metal_table, 
                                   title="Metal Content Production by Scenario (kilotonnes)")
            
            
        else:
            doc.add_paragraph("No metal content production data available.")
            
    except Exception as e:
        doc.add_paragraph(f"Error generating metal content table: {e}")

def add_production_analysis_section(doc, df_country, chart_paths):
    """Add production analysis section with tables and charts"""
    add_section_header(doc, 'Production Analysis by Processing Type', level=1)
    
    try:
        # Production by processing type table (filtered to remove zero rows)
        prod_type_table = create_production_by_type_table(df_country, to_kt=True, scenarios_filter='mid_only', remove_zero_rows=True)
        if not prod_type_table.empty:
            add_table_from_dataframe(doc, prod_type_table,
                                   title="Production by Processing Type and Year (kilotonnes)")
            doc.add_paragraph(
                "Note: Only rows with non-zero production values are shown for clarity."
            )
        
        # Production by stage table (filtered to remove zero rows)
        prod_stage_table = create_production_table(df_country, to_kt=True, scenarios_filter='mid_only', remove_zero_rows=True)
        if not prod_stage_table.empty:
            add_table_from_dataframe(doc, prod_stage_table,
                                   title="Production by Processing Stage and Year (kilotonnes)")
            doc.add_paragraph(
                "Note: Only rows with non-zero production values are shown for clarity."
            )
        
        # Add consolidated production chart if available
        if 'production_consolidated' in chart_paths and chart_paths['production_consolidated']:
            for chart_path in chart_paths['production_consolidated']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, 
                                      title="Production by Processing Type and Scenario")
        
        doc.add_paragraph(
            "This analysis reveals how different policy approaches affect production across the value chain. "
            "Stage 0 refers to the metal content (or mineral in the case of graphite) extracted, whilst higher processing stages create increasing value through beneficiation, "
            "early refining, and product manufacturing. The data shows potential opportunities for moving up the value chain."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating production analysis: {e}")

def add_economic_analysis_section(doc, df_country, chart_paths):
    """Add economic analysis section"""
    add_section_header(doc, 'Economic Analysis', level=1)
    
    try:
        # Export Revenue analysis
        add_section_header(doc, 'Export Revenue Analysis', level=2)
        rev_summary, rev_by_type = create_revenue_tables(df_country, to_kt=True, scenarios_filter='mid_only')
        
        if not rev_summary.empty:
            add_table_from_dataframe(doc, rev_summary, title="Export Revenue Summary (Million USD)")
        
        if not rev_by_type.empty:
            add_table_from_dataframe(doc, rev_by_type, title="Export Revenue by Processing Type (Million USD)")
        
        # Add consolidated export revenue chart
        if 'revenue' in chart_paths and chart_paths['revenue']:
            for chart_path in chart_paths['revenue']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Export Revenue by Scenario and Mineral")
        
        # Value addition analysis - TEMPORARILY DISABLED pending better data
        # add_section_header(doc, 'Value Addition Analysis', level=2)
        # va_summary, va_by_type = create_value_added_tables(df_country, to_kt=True)
        # 
        # if not va_summary.empty:
        #     add_table_from_dataframe(doc, va_summary, title="Value Addition Summary (Million USD)")
        # 
        # if not va_by_type.empty:
        #     add_table_from_dataframe(doc, va_by_type, title="Value Addition by Processing Type (Million USD)")
        # 
        # # Add value addition charts
        # if 'value_addition' in chart_paths and chart_paths['value_addition']:
        #     for chart_path in chart_paths['value_addition']:
        #         if os.path.exists(chart_path):
        #             add_image_from_path(doc, chart_path, title=f"Value Addition")
        
        doc.add_paragraph(
            "This economic analysis demonstrates the financial impact of different mineral development strategies. "
            "Export revenue shows total economic value generated across different processing stages and policy approaches."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating economic analysis: {e}")

def add_environmental_impact_section(doc, df_country, chart_paths):
    """Add environmental impact section"""
    add_section_header(doc, 'Environmental Impact Analysis', level=1)
    
    try:
        # Water usage analysis
        add_section_header(doc, 'Water Usage', level=2)
        water_table = create_water_use_by_mineral(df_country, to_kt=True, scenarios_filter='mid_only')
        if not water_table.empty:
            add_table_from_dataframe(doc, water_table, title="Water Usage by Mineral (Million m³)")
        
        # Add consolidated water chart
        if 'water_consolidated' in chart_paths and chart_paths['water_consolidated']:
            for chart_path in chart_paths['water_consolidated']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Water Usage by Scenario and Mineral")
        
        # CO2 emissions analysis  
        add_section_header(doc, 'CO2e Emissions', level=2)
        
        # Transport emissions
        transport_emissions = create_transport_emissions_by_mineral(df_country, to_kt=True, scenarios_filter='mid_only')
        if not transport_emissions.empty:
            add_table_from_dataframe(doc, transport_emissions, 
                                   title="Transport Emissions by Mineral (kt CO2eq)")
        
        # Energy emissions
        energy_emissions = create_energy_emissions_by_mineral(df_country, to_kt=True, scenarios_filter='mid_only')
        if not energy_emissions.empty:
            add_table_from_dataframe(doc, energy_emissions,
                                   title="Energy Emissions by Mineral (kt CO2eq)")
        
        # Add consolidated emissions chart
        if 'emissions_consolidated' in chart_paths and chart_paths['emissions_consolidated']:
            for chart_path in chart_paths['emissions_consolidated']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="CO2 Emissions by Scenario and Mineral")
        
        doc.add_paragraph(
            "The environmental impact analysis covers water usage and CO2 emissions from both "
            "transport and energy consumption across different scenarios."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating environmental impact analysis: {e}")

def add_infrastructure_analysis_section(doc, df_country, chart_paths):
    """Add infrastructure requirements section"""
    add_section_header(doc, 'Infrastructure Requirements', level=1)
    
    try:
        # Transport volumes
        add_section_header(doc, 'Transport Volumes', level=2)
        
        # Create transport volume table with constraints as columns
        transport_table = create_transport_volume_table_with_columns(df_country, scenarios_filter='mid_only')
        if not transport_table.empty:
            add_table_from_dataframe(doc, transport_table,
                                   title="Transport Volume Requirements by Scenario and Policy Approach (Million ton-km)")
            doc.add_paragraph(
                "This table shows transport volume requirements across different scenarios and policy approaches. "
                "Values represent million tonne-kilometres needed for mineral transport."
            )
        
        # Add transport charts if available
        if 'transport' in chart_paths and chart_paths['transport']:
            for chart_path in chart_paths['transport']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Transport Infrastructure")
        
        # Electricity capacity
        add_section_header(doc, 'Electricity Capacity Requirements', level=2)
        
        # Create electricity capacity table with constraints as columns
        electricity_table = create_energy_capacity_table_with_columns(df_country, scenarios_filter='mid_only')
        if not electricity_table.empty:
            add_table_from_dataframe(doc, electricity_table,
                                   title="Electricity Capacity Requirements by Scenario and Policy Approach (GW)")
            doc.add_paragraph(
                "This table shows electricity capacity requirements across different scenarios and policy approaches. "
                "Values represent gigawatts (GW) of electricity capacity needed for mineral processing."
            )
        
        # Add electricity charts if available
        if 'electricity' in chart_paths and chart_paths['electricity']:
            for chart_path in chart_paths['electricity']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Electricity Infrastructure")
        
        doc.add_paragraph(
            "Infrastructure requirements analysis shows the transport and electricity capacity needed "
            "to support different mineral processing scenarios. Higher processing stages typically "
            "require more electricity capacity, while transport volumes depend on trade patterns."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating infrastructure analysis: {e}")

def add_comparative_analysis_section(doc, df_country, chart_paths):
    """Add comprehensive comparative analysis section"""
    add_section_header(doc, 'Comparative Analysis', level=1)
    
    try:
        # Regional vs National comparisons
        add_section_header(doc, 'Regional vs National Policy Impacts', level=2)
        doc.add_paragraph(
            "This analysis quantifies the differences between National Focus and Regional Integration approaches, "
            "showing how regional cooperation affects production volumes, export revenues, and environmental impacts."
        )
        
        # Add production difference plots
        if 'production_differences' in chart_paths and chart_paths['production_differences']:
            for chart_path in chart_paths['production_differences']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Production: Regional vs National Differences")
        
        # Add revenue difference plots
        if 'revenue_differences' in chart_paths and chart_paths['revenue_differences']:
            for chart_path in chart_paths['revenue_differences']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Export Revenue: Regional vs National Differences")
        
        # Constrained vs Unconstrained comparisons
        add_section_header(doc, 'Environmental Constraint Impacts', level=2)
        doc.add_paragraph(
            "This section shows the trade-offs between environmentally constrained and unconstrained scenarios, "
            "highlighting the economic costs and benefits of environmental regulations."
        )
        
        # Add constraint comparison charts
        if 'constraint_differences' in chart_paths and chart_paths['constraint_differences']:
            for chart_path in chart_paths['constraint_differences']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Constrained vs Unconstrained Impacts")
        
        # Strategic Goal Comparisons (formerly goal_comparison_section)
        add_section_header(doc, 'Strategic Goal Comparisons (2040)', level=2)
        doc.add_paragraph(
            "Comparison of three development strategies: Business as Usual (BAU), "
            "Early Refining, and Precursor Product scenarios, showing their relative impacts."
        )
        
        # Add goal comparison plots
        if 'goal_comparisons' in chart_paths and chart_paths['goal_comparisons']:
            for chart_path in chart_paths['goal_comparisons']:
                if os.path.exists(chart_path):
                    add_image_from_path(doc, chart_path, title="Strategic Goal Comparison")
        
        doc.add_paragraph(
            "The comparative analysis reveals key trade-offs between different policy approaches "
            "and strategic goals, providing insights for decision-making on mineral development strategies."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating comparative analysis: {e}")

def add_enhanced_executive_summary(doc, df_country, iso3):
    """Add enhanced executive summary with written insights only"""
    add_section_header(doc, 'Executive Summary', level=1)
    
    try:
        # Load country-specific summary table for insights
        pivot_file = f"/home/karlac/critical_minerals_Africa/transport-outputs/results/pivot_tables/all_data_pivots_{iso3}.xlsx"
        
        if os.path.exists(pivot_file):
            try:
                summary_df = pd.read_excel(pivot_file, sheet_name='summary_table')
                
                # Extract key insights from summary data
                doc.add_paragraph(
                    f"This report analyses critical mineral development pathways for {get_country_name(iso3)}, "
                    f"comparing National Focus and Regional Integration strategies across different environmental constraints."
                )
                
                # Analyse National vs Regional differences
                if not summary_df.empty:
                    # Find largest percentage changes
                    significant_changes = summary_df[summary_df['percentage_change'].abs() > 10].sort_values(
                        'percentage_change', ascending=False
                    )
                    
                    if not significant_changes.empty:
                        doc.add_heading('Key Findings: National vs Regional Integration', level=2)
                        
                        # Production insights
                        prod_changes = significant_changes[significant_changes['indicator'].str.contains('Production')]
                        if not prod_changes.empty:
                            max_prod = prod_changes.iloc[0]
                            doc.add_paragraph(
                                f"• Production: Regional integration shows {max_prod['percentage_change']:.1f}% "
                                f"change in {max_prod['indicator']} under {max_prod['scenario']} scenario."
                            )
                        
                        # Revenue insights
                        rev_changes = significant_changes[significant_changes['indicator'].str.contains('revenue')]
                        if not rev_changes.empty:
                            max_rev = rev_changes.iloc[0]
                            doc.add_paragraph(
                                f"• Revenue: {max_rev['percentage_change']:.1f}% difference observed in "
                                f"{max_rev['scenario']} scenario, indicating {'increased' if max_rev['percentage_change'] > 0 else 'decreased'} "
                                f"economic benefits from regional cooperation."
                            )
                        
                        # Environmental insights
                        env_changes = significant_changes[significant_changes['indicator'].str.contains('co2|water', case=False)]
                        if not env_changes.empty:
                            doc.add_paragraph(
                                f"• Environmental: Regional integration affects resource usage and emissions, "
                                f"with implications for sustainable development strategies."
                            )
                
            except Exception as e:
                print(f"Could not load summary table for insights: {e}")
        
        doc.add_paragraph(
            "The following sections provide detailed analysis of production capabilities, infrastructure requirements, "
            "economic impacts, and environmental considerations under different policy scenarios."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating executive summary: {e}")

def generate_country_docx(df_country, iso3, output_dir):
    """Generate a comprehensive DOCX report for a specific country"""
    country_name = get_country_name(iso3)
    print(f"Generating DOCX report for {country_name} ({iso3})")
    
    # Create document
    doc = create_country_document(country_name, iso3)
    
    # Add table of contents
    add_table_of_contents(doc)
    
    # Add enhanced executive summary (written insights only)
    try:
        add_enhanced_executive_summary(doc, df_country, iso3)
    except Exception as e:
        print(f"Error adding executive summary: {e}")
    
    # Generate charts in temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        chart_paths = generate_country_charts(df_country, iso3, temp_dir)
        
        # Add sections in new order
        # 1. Metal Content Production (moved before processing analysis)
        add_metal_content_section(doc, df_country)
        doc.add_page_break()
        
        # 2. Production Analysis by Processing Type  
        add_production_analysis_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        # 3. Infrastructure Analysis
        add_infrastructure_analysis_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        # 4. Economic Analysis
        add_economic_analysis_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        # 5. Comparative Analysis (combines policy and goal comparisons)
        add_comparative_analysis_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        # 6. Environmental Analysis
        add_environmental_impact_section(doc, df_country, chart_paths)
        doc.add_page_break()
        
        # 7. Technical Annex (comprehensive tables with all scenarios)
        add_technical_annex_section(doc, df_country, iso3)
        doc.add_page_break()
        
        # 7. Summary Tables (if needed) - DEPRECATED, keeping for backwards compatibility
        # add_summary_tables_section(doc, iso3)
    
    
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

def add_technical_annex_section(doc, df_country, iso3):
    """Add comprehensive technical annex with all scenarios"""
    add_section_header(doc, f"Technical Annex: Complete Scenario Analysis", level=1)
    
    doc.add_paragraph(
        "This section provides comprehensive data across all demand scenarios (low/mid/high) "
        "for detailed analysis by researchers and policy makers who require complete scenario coverage."
    )
    
    try:
        # Metal content production with all scenarios
        add_section_header(doc, 'Metal Content Production (All Scenarios)', level=2)
        metal_table_full = create_metal_content_table(df_country, to_kt=True, scenarios_filter='all')
        if not metal_table_full.empty:
            add_table_from_dataframe(doc, metal_table_full, 
                                   title="Metal Content Production by All Scenarios (kilotonnes)")
        
        # Production analysis with all scenarios
        add_section_header(doc, 'Production Analysis (All Scenarios)', level=2)
        prod_type_table_full = create_production_by_type_table(df_country, to_kt=True, scenarios_filter='all', remove_zero_rows=True)
        if not prod_type_table_full.empty:
            add_table_from_dataframe(doc, prod_type_table_full,
                                   title="Production by Processing Type - All Scenarios (kilotonnes)")
            doc.add_paragraph(
                "Note: Only rows with non-zero production values are shown. This table includes all demand scenarios (low/medium/high)."
            )
        
        prod_stage_table_full = create_production_table(df_country, to_kt=True, scenarios_filter='all', remove_zero_rows=True)
        if not prod_stage_table_full.empty:
            add_table_from_dataframe(doc, prod_stage_table_full,
                                   title="Production by Processing Stage - All Scenarios (kilotonnes)")
            doc.add_paragraph(
                "Note: Only rows with non-zero production values are shown. This table includes all demand scenarios (low/medium/high)."
            )
        
        # Export revenue with all scenarios
        add_section_header(doc, 'Export Revenue Analysis (All Scenarios)', level=2)
        rev_summary_full, rev_by_type_full = create_revenue_tables(df_country, to_kt=True, scenarios_filter='all')
        if not rev_summary_full.empty:
            add_table_from_dataframe(doc, rev_summary_full, title="Export Revenue Summary - All Scenarios (Million USD)")
        if not rev_by_type_full.empty:
            add_table_from_dataframe(doc, rev_by_type_full, title="Export Revenue by Processing Type - All Scenarios (Million USD)")
        
        # Environmental impact with all scenarios
        add_section_header(doc, 'Environmental Impact Analysis (All Scenarios)', level=2)
        
        # Water usage
        water_table_full = create_water_use_by_mineral(df_country, to_kt=True, scenarios_filter='all')
        if not water_table_full.empty:
            add_table_from_dataframe(doc, water_table_full, title="Water Usage by Mineral - All Scenarios (Million m³)")
        
        # Transport emissions
        transport_emissions_full = create_transport_emissions_by_mineral(df_country, to_kt=True, scenarios_filter='all')
        if not transport_emissions_full.empty:
            add_table_from_dataframe(doc, transport_emissions_full, 
                                   title="Transport Emissions by Mineral - All Scenarios (kt CO2eq)")
        
        # Energy emissions
        energy_emissions_full = create_energy_emissions_by_mineral(df_country, to_kt=True, scenarios_filter='all')
        if not energy_emissions_full.empty:
            add_table_from_dataframe(doc, energy_emissions_full,
                                   title="Energy Emissions by Mineral - All Scenarios (kt CO2eq)")
        
        # Infrastructure requirements with all scenarios  
        add_section_header(doc, 'Infrastructure Requirements (All Scenarios)', level=2)
        
        doc.add_paragraph(
            "The following tables show infrastructure requirements across all demand scenarios (low, medium, high) "
            "and policy approaches. Each scenario is shown with its demand level for comprehensive analysis."
        )
        
        # Transport volume with all scenarios - grouped row format
        transport_volume_full = create_transport_volume_table_all_scenarios(df_country)
        if not transport_volume_full.empty:
            add_table_from_dataframe(doc, transport_volume_full,
                                   title="Transport Volume Requirements - All Demand Scenarios (Million ton-km)")
            doc.add_paragraph(
                "Note: Values show transport volume requirements for each combination of scenario, demand level, and policy approach."
            )
        
        # Energy capacity with all scenarios - grouped row format
        energy_capacity_full = create_energy_capacity_table_all_scenarios(df_country)
        if not energy_capacity_full.empty:
            add_table_from_dataframe(doc, energy_capacity_full,
                                   title="Electricity Capacity Requirements - All Demand Scenarios (GW)")
            doc.add_paragraph(
                "Note: Values show electricity capacity requirements for each combination of scenario, demand level, and policy approach."
            )
        
        doc.add_paragraph(
            "Note: This technical annex includes high, medium, and low demand scenarios across all constraint types. "
            "The main report sections focus on medium-demand scenarios for clarity and readability."
        )
        
    except Exception as e:
        doc.add_paragraph(f"Error generating technical annex: {e}")
        print(f"Error in technical annex for {iso3}: {e}")

def add_summary_tables_section(doc, iso3):
    """Add summary tables from pivot files to the document"""
    try:
        # Check if pivot table file exists for this country  
        pivot_file = f"/home/karlac/critical_minerals_Africa/transport-outputs/results/pivot_tables/all_data_pivots_{iso3}.xlsx"
        if not os.path.exists(pivot_file):
            print(f"Pivot file not found for {iso3}: {pivot_file}")
            return
        
        add_section_header(doc, f"Summary Tables - {get_country_name(iso3)}")
        doc.add_paragraph("This section provides key summary tables extracted from detailed pivot analyses.")
        
        # Load pivot tables
        try:
            # Priority: Simplified summary table (the format we want)
            try:
                summary_df = pd.read_excel(pivot_file, sheet_name='summary_table')
                if not summary_df.empty:
                    doc.add_heading("Country-Specific Summary Metrics", level=2)
                    doc.add_paragraph("This table shows key metrics comparing National and Regional policy approaches for this country.")
                    # Format the summary table for better display
                    summary_display = summary_df[['scenario', 'constraint_comparison', 'indicator', 'national', 'regional', 'percentage_change']]
                    add_table_from_dataframe(doc, summary_display.head(20), "National vs Regional comparison with percentage changes")
                    doc.add_paragraph()
            except:
                print(f"Summary table sheet not found for {iso3}")
            
            # Production summary (fallback)
            try:
                production_df = pd.read_excel(pivot_file, sheet_name='production_kt')
                if not production_df.empty:
                    doc.add_heading("Production Summary (kt)", level=2)
                    add_table_from_dataframe(doc, production_df.head(15), "Production by scenario, constraint, and processing stage")
                    doc.add_paragraph()
            except:
                pass
                
            # Production by type summary (fallback)
            try:
                prod_type_df = pd.read_excel(pivot_file, sheet_name='production_by_type_kt')
                if not prod_type_df.empty:
                    doc.add_heading("Production by Processing Type (kt)", level=2)
                    add_table_from_dataframe(doc, prod_type_df.head(15), "Production grouped by processing type")
                    doc.add_paragraph()
            except:
                pass
                
        except Exception as e:
            print(f"Error reading pivot table sheets for {iso3}: {e}")
            doc.add_paragraph(f"Unable to load summary tables. Error: {str(e)}")
            
    except Exception as e:
        print(f"Error adding summary tables section for {iso3}: {e}")
        doc.add_paragraph("Summary tables section could not be generated due to technical issues.")

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