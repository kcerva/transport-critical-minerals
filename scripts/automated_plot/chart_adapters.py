import os
import matplotlib.pyplot as plt
import pandas as pd
from plot_production_by_country_all_constraints import plot_production_by_country_all_constraints
from plot_gdp_share_by_country_all_constraints import plot_gdp_share_by_country_all_constraints
from plot_emissions_water_all_countries import plot_emissions_by_country_all_constraints, plot_water_by_country_all_constraints

def adapt_production_charts(df_country, iso3, temp_dir):
    """Adapter for production charts - handles single country data"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'production_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)
        
        goal_by_year = {2030: "Early refining", 2040: "Precursor related product"}
        saved_paths = plot_production_by_country_all_constraints(df_country, country_output_dir, goal_by_year)
        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating production charts for {iso3}: {e}")
        return []

def adapt_gdp_share_charts(df_country, iso3, temp_dir, value_column, title_prefix, ylabel):
    """Adapter for GDP share charts (revenue, value addition)"""
    try:
        # Create country-specific output directory  
        chart_type = value_column.replace('_', '')
        country_output_dir = os.path.join(temp_dir, f'{chart_type}_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)
        
        saved_paths = plot_gdp_share_by_country_all_constraints(
            df_country, country_output_dir, value_column, title_prefix, ylabel
        )
        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating {value_column} charts for {iso3}: {e}")
        return []

def adapt_emissions_charts(df_country, iso3, temp_dir):
    """Adapter for emissions charts"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'emissions_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)
        
        saved_paths = plot_emissions_by_country_all_constraints(df_country, country_output_dir)
        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating emissions charts for {iso3}: {e}")
        return []

def adapt_water_charts(df_country, iso3, temp_dir):
    """Adapter for water usage charts"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'water_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)
        
        saved_paths = plot_water_by_country_all_constraints(df_country, country_output_dir)
        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating water charts for {iso3}: {e}")
        return []

def create_policy_difference_chart(df_country, iso3, temp_dir):
    """Create simple policy comparison charts"""
    try:
        # Create difference analysis for regional vs national
        country_output_dir = os.path.join(temp_dir, f'policy_diff_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)
        
        saved_paths = []
        
        # Production differences (Regional - National)
        production_diff = create_production_difference_table(df_country)
        if not production_diff.empty:
            chart_path = plot_difference_table(production_diff, 'Production Differences (Regional - National)', 
                                             'Production (kt)', country_output_dir, 'production_differences.png')
            if chart_path:
                saved_paths.append(chart_path)
        
        # Revenue differences
        revenue_diff = create_revenue_difference_table(df_country)
        if not revenue_diff.empty:
            chart_path = plot_difference_table(revenue_diff, 'Revenue Differences (Regional - National)',
                                             'Revenue (Million USD)', country_output_dir, 'revenue_differences.png')
            if chart_path:
                saved_paths.append(chart_path)
        
        return saved_paths
    except Exception as e:
        print(f"Error generating policy difference charts for {iso3}: {e}")
        return []

def create_production_difference_table(df_country):
    """Create production difference table for regional vs national"""
    try:
        # Filter for meaningful comparisons
        df_prod = df_country[df_country['processing_stage'] > 0].copy()
        df_prod['production_kt'] = df_prod['production_tonnes'] / 1000
        
        # Group by scenario, constraint, processing_type, year
        grouped = df_prod.groupby(['scenario', 'constraint', 'processing_type', 'year'])['production_kt'].sum().reset_index()
        
        # Create pivot to compare constraints
        pivot = grouped.pivot_table(
            index=['scenario', 'processing_type', 'year'], 
            columns='constraint', 
            values='production_kt', 
            fill_value=0
        )
        
        # Calculate differences (Regional - National)
        differences = []
        for idx, row in pivot.iterrows():
            scenario, proc_type, year = idx
            
            # Compare unconstrained policies
            if 'region_unconstrained' in pivot.columns and 'country_unconstrained' in pivot.columns:
                diff = row.get('region_unconstrained', 0) - row.get('country_unconstrained', 0)
                differences.append({
                    'scenario': scenario,
                    'processing_type': proc_type,
                    'year': year,
                    'constraint_comparison': 'Unconstrained (Regional - National)',
                    'difference': diff
                })
            
            # Compare constrained policies  
            if 'region_constrained' in pivot.columns and 'country_constrained' in pivot.columns:
                diff = row.get('region_constrained', 0) - row.get('country_constrained', 0)
                differences.append({
                    'scenario': scenario,
                    'processing_type': proc_type,
                    'year': year,
                    'constraint_comparison': 'Constrained (Regional - National)',
                    'difference': diff
                })
        
        return pd.DataFrame(differences)
    except Exception as e:
        print(f"Error creating production difference table: {e}")
        return pd.DataFrame()

def create_revenue_difference_table(df_country):
    """Create revenue difference table for regional vs national"""
    try:
        # Group by scenario, constraint, year
        grouped = df_country.groupby(['scenario', 'constraint', 'year'])['revenue_usd'].sum().reset_index()
        grouped['revenue_musd'] = grouped['revenue_usd'] / 1e6
        
        # Create pivot to compare constraints
        pivot = grouped.pivot_table(
            index=['scenario', 'year'], 
            columns='constraint', 
            values='revenue_musd', 
            fill_value=0
        )
        
        # Calculate differences
        differences = []
        for idx, row in pivot.iterrows():
            scenario, year = idx
            
            # Compare unconstrained policies
            if 'region_unconstrained' in pivot.columns and 'country_unconstrained' in pivot.columns:
                diff = row.get('region_unconstrained', 0) - row.get('country_unconstrained', 0)
                differences.append({
                    'scenario': scenario,
                    'year': year,
                    'constraint_comparison': 'Unconstrained (Regional - National)',
                    'difference': diff
                })
            
            # Compare constrained policies
            if 'region_constrained' in pivot.columns and 'country_constrained' in pivot.columns:
                diff = row.get('region_constrained', 0) - row.get('country_constrained', 0)
                differences.append({
                    'scenario': scenario,
                    'year': year,
                    'constraint_comparison': 'Constrained (Regional - National)',
                    'difference': diff
                })
        
        return pd.DataFrame(differences)
    except Exception as e:
        print(f"Error creating revenue difference table: {e}")
        return pd.DataFrame()

def plot_difference_table(diff_df, title, ylabel, output_dir, filename):
    """Plot difference table as bar chart"""
    try:
        if diff_df.empty:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create grouped bar chart
        if 'processing_type' in diff_df.columns:
            # Production differences - group by processing type and year
            pivot_plot = diff_df.pivot_table(
                index=['processing_type', 'constraint_comparison'], 
                columns='year', 
                values='difference', 
                fill_value=0
            )
        else:
            # Revenue differences - group by constraint comparison and year
            pivot_plot = diff_df.pivot_table(
                index='constraint_comparison', 
                columns='year', 
                values='difference', 
                fill_value=0
            )
        
        pivot_plot.plot(kind='bar', ax=ax, rot=45)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xlabel('', fontsize=12)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.grid(axis='y', alpha=0.3)
        ax.legend(title='Year', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        output_path = os.path.join(output_dir, filename)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return output_path
    except Exception as e:
        print(f"Error plotting difference table: {e}")
        return None