import os
import matplotlib.pyplot as plt
import pandas as pd
import shutil
from plot_production_by_country_all_constraints import plot_production_by_country_all_constraints
from plot_gdp_share_by_country_all_constraints import plot_gdp_share_by_country_all_constraints
from plot_emissions_water_all_countries import plot_emissions_by_country_all_constraints, plot_water_by_country_all_constraints
from plot_goal_comparisons import plot_goal_comparisons_2040, plot_production_goal_comparison_by_processing_type

# Try to import difference plotting functions if they exist
try:
    from plot_production_differences import calculate_regional_vs_national_difference, plot_production_difference_bars
    from plot_revenue_differences import calculate_revenue_differences, plot_revenue_difference_bars
except ImportError:
    print("Warning: Difference plotting modules not found. Some charts may not be generated.")

def save_chart_to_permanent_location(temp_path, permanent_dir, iso3):
    """
    Save a chart to permanent location while keeping temp copy for DOCX.

    Args:
        temp_path: Path to temporary chart file
        permanent_dir: Base permanent directory (e.g., /figures/automated_plots/country_figures/)
        iso3: Country ISO3 code

    Returns:
        Path to permanently saved chart
    """
    if not temp_path or not os.path.exists(temp_path):
        return None

    # Create permanent country directory
    permanent_country_dir = os.path.join(permanent_dir, iso3)
    os.makedirs(permanent_country_dir, exist_ok=True)

    # Get filename from temp path
    filename = os.path.basename(temp_path)
    permanent_path = os.path.join(permanent_country_dir, filename)

    # Copy to permanent location
    try:
        shutil.copy2(temp_path, permanent_path)
        return permanent_path
    except Exception as e:
        print(f"Warning: Could not save chart to permanent location: {e}")
        return None

def adapt_production_charts(df_country, iso3, temp_dir, permanent_dir=None):
    """Adapter for production charts - creates improved subplot comparisons"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'production_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)

        saved_paths = []

        # Create subplot-based production comparison charts
        production_paths = create_production_subplot_charts(df_country, country_output_dir, iso3)
        saved_paths.extend(production_paths)

        # Create production charts with error bars
        errorbar_paths = create_production_subplot_charts_with_errorbars(df_country, country_output_dir, iso3)
        saved_paths.extend(errorbar_paths)

        # NOTE: Removed plot_production_by_country_all_constraints call
        # That function generates 12 individual scenario charts (one bar each) incorrectly named "subplots"
        # These are redundant with the actual subplot comparison charts above
        # The consolidated charts below provide better multi-scenario comparisons

        # Save to permanent location if specified
        if permanent_dir:
            for path in saved_paths:
                save_chart_to_permanent_location(path, permanent_dir, iso3)

        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating production charts for {iso3}: {e}")
        return []

def adapt_gdp_share_charts(df_country, iso3, temp_dir, value_column, title_prefix, ylabel, permanent_dir=None):
    """Adapter for GDP share charts (revenue, value addition)"""
    try:
        # Create country-specific output directory
        chart_type = value_column.replace('_', '')
        country_output_dir = os.path.join(temp_dir, f'{chart_type}_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)

        # Handle value_added column - it needs to be computed
        if value_column == 'value_added':
            # Import the calculation function
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))
            from data_tables import calc_value_added

            # Compute value_added column if it doesn't exist
            df_working = df_country.copy()
            if 'value_added' not in df_working.columns:
                df_working = df_working[df_working["processing_stage"] > 0].copy()

                # Check for incomplete pricing/cost data and warn user
                incomplete_data = len(df_working[
                    (df_working['production_tonnes'] > 0) &
                    ((df_working['price_usd_per_tonne'] == 0) | (df_working['production_cost_usd_per_tonne'] == 0))
                ])
                if incomplete_data > 0:
                    print(f"⚠️  Warning: {incomplete_data} rows have production but missing price/cost data. Value addition calculations will be limited to complete data only.")

                df_working["value_added"] = 0.0
                df_working = df_working.groupby(
                    ['scenario', 'constraint', 'iso3', 'reference_mineral']
                ).apply(calc_value_added).reset_index(drop=True)
        else:
            df_working = df_country

        saved_paths = plot_gdp_share_by_country_all_constraints(
            df_working, country_output_dir, value_column, title_prefix, ylabel
        )

        # Save to permanent location if specified
        if permanent_dir:
            for path in saved_paths:
                save_chart_to_permanent_location(path, permanent_dir, iso3)

        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating {value_column} charts for {iso3}: {e}")
        return []

def adapt_emissions_charts(df_country, iso3, temp_dir, permanent_dir=None):
    """Adapter for emissions charts"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'emissions_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)

        saved_paths = plot_emissions_by_country_all_constraints(df_country, country_output_dir)

        # Save to permanent location if specified
        if permanent_dir:
            for path in saved_paths:
                save_chart_to_permanent_location(path, permanent_dir, iso3)

        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating emissions charts for {iso3}: {e}")
        return []

def adapt_water_charts(df_country, iso3, temp_dir, permanent_dir=None):
    """Adapter for water usage charts"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'water_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)

        saved_paths = plot_water_by_country_all_constraints(df_country, country_output_dir)

        # Save to permanent location if specified
        if permanent_dir:
            for path in saved_paths:
                save_chart_to_permanent_location(path, permanent_dir, iso3)

        return saved_paths if saved_paths else []
    except Exception as e:
        print(f"Error generating water charts for {iso3}: {e}")
        return []

def create_policy_difference_chart(df_country, iso3, temp_dir, permanent_dir=None):
    """Create comprehensive policy comparison charts for all 2040 scenarios"""
    try:
        # Create difference analysis for regional vs national
        country_output_dir = os.path.join(temp_dir, f'policy_diff_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)

        saved_paths = []

        # Create improved policy comparison charts
        improved_paths = create_comprehensive_policy_comparison(df_country, country_output_dir, iso3)
        saved_paths.extend(improved_paths)

        # Keep original difference tables as backup
        production_diff = create_production_difference_table(df_country)
        if not production_diff.empty:
            chart_path = plot_difference_table(production_diff, 'Production Differences (Regional - National)',
                                             'Production (kt)', country_output_dir, 'production_differences_original.png')
            if chart_path:
                saved_paths.append(chart_path)

        # Save to permanent location if specified
        if permanent_dir:
            for path in saved_paths:
                save_chart_to_permanent_location(path, permanent_dir, iso3)

        return saved_paths
    except Exception as e:
        print(f"Error generating policy difference charts for {iso3}: {e}")
        return []

def adapt_goal_comparison_charts(df_country, iso3, temp_dir, permanent_dir=None):
    """Adapter for goal comparison charts - comparing 2040 BAU vs Early Refining vs Precursor"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'goal_comparison_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)
        
        saved_paths = []
        
        # Create improved goal comparison charts with better titles and formatting
        improved_paths = create_improved_goal_comparison_charts(df_country, country_output_dir, iso3)
        saved_paths.extend(improved_paths)
        
        # Create consolidated goal comparison chart (all metrics in one figure)
        consolidated_path = create_consolidated_goal_comparison(df_country, country_output_dir, iso3)
        if consolidated_path:
            saved_paths.append(consolidated_path)

        # Save to permanent location if specified
        if permanent_dir:
            for path in saved_paths:
                save_chart_to_permanent_location(path, permanent_dir, iso3)

        return saved_paths
    except Exception as e:
        print(f"Error generating goal comparison charts for {iso3}: {e}")
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

def create_production_subplot_charts(df_country, output_dir, iso3):
    """Create improved production charts using subplots for better comparison"""
    saved_paths = []
    
    try:
        # Import plot utils
        import matplotlib.pyplot as plt
        import seaborn as sns
        from docx_utils import format_scenario_name, format_constraint_name
        
        # Set style
        plt.style.use('default')
        sns.set_palette('Set2')
        
        # Filter for 2040 scenarios only for comparison
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()
        
        if df_2040.empty:
            return saved_paths
        
        # Create production by scenario subplot - use 3 rows for better comparison
        fig, axes = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
        fig.suptitle(f'Production Comparison Across Development Strategies\n{get_country_name(iso3)}', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        scenarios_2040 = ['bau_2040_mid_min_threshold_metal_tons', 
                          'early_refining_2040_mid_min_threshold_metal_tons',
                          'precursor_2040_mid_min_threshold_metal_tons']
        
        scenario_titles = ['2040 Business as Usual', '2040 Early Refining', '2040 Precursor Product']
        
        # Process each scenario
        for i, (scenario, title) in enumerate(zip(scenarios_2040, scenario_titles)):
            scenario_data = df_2040[df_2040['scenario'] == scenario]
            
            if scenario_data.empty:
                axes[i].text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(title)
                continue
            
            # Aggregate by constraint and processing stage
            agg_data = scenario_data.groupby(['constraint', 'processing_stage'])['production_tonnes'].sum().reset_index()
            agg_data['production_kt'] = agg_data['production_tonnes'] / 1000
            
            # Create pivot for plotting
            pivot = agg_data.pivot(index='constraint', columns='processing_stage', values='production_kt').fillna(0)
            
            # Clean constraint names
            pivot.index = [format_constraint_name(c) for c in pivot.index]
            
            # Plot horizontal stacked bars for better comparison
            pivot.plot(kind='barh', ax=axes[i], stacked=True, width=0.8)
            axes[i].set_title(title, fontweight='bold', pad=10)
            axes[i].set_ylabel('Policy Approach', fontweight='bold')
            axes[i].set_xlabel('Production (kt)' if i == 2 else '', fontweight='bold')
            axes[i].grid(axis='x', alpha=0.3)
            
            # Improve legend - show on middle subplot
            if i == 1:  # Show legend on middle subplot
                axes[i].legend(title='Processing Stage', bbox_to_anchor=(1.05, 1), loc='upper left')
            else:
                axes[i].legend().set_visible(False)
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'production_comparison_subplots.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)
        
        # Create constraint comparison subplot (vertical layout)
        fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        fig.suptitle(f'Policy Approach Comparison\n{get_country_name(iso3)}', 
                     fontsize=16, fontweight='bold', y=0.95)
        
        # National vs Regional comparison for each scenario
        for i, policy_type in enumerate(['National Focus', 'Regional Integration']):
            policy_data = df_2040[df_2040['constraint'].str.contains('country' if policy_type == 'National Focus' else 'region')]
            
            if not policy_data.empty:
                # Aggregate by scenario
                agg_data = policy_data.groupby(['scenario'])['production_tonnes'].sum().reset_index()
                agg_data['production_kt'] = agg_data['production_tonnes'] / 1000
                agg_data['scenario_clean'] = agg_data['scenario'].apply(lambda x: format_scenario_name(x))
                
                axes[i].bar(range(len(agg_data)), agg_data['production_kt'], 
                           color=sns.color_palette('Set2')[i], alpha=0.8)
                axes[i].set_title(f'{policy_type} Approaches', fontweight='bold')
                axes[i].set_ylabel('Production (kt)', fontweight='bold')
                axes[i].grid(axis='y', alpha=0.3)
                
                if i == 1:  # Bottom subplot
                    axes[i].set_xticks(range(len(agg_data)))
                    axes[i].set_xticklabels([s.replace('2040 ', '') for s in agg_data['scenario_clean']], 
                                          rotation=45, ha='right')
                    axes[i].set_xlabel('Development Strategy', fontweight='bold')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'policy_comparison_subplots.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)
        
    except Exception as e:
        print(f"Error creating production subplot charts: {e}")
    
    return saved_paths

def create_comprehensive_policy_comparison(df_country, output_dir, iso3):
    """Create comprehensive policy comparison showing regional vs national for all three 2040 scenarios"""
    saved_paths = []
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        from docx_utils import format_scenario_name, format_constraint_name
        import numpy as np
        
        # Set style
        plt.style.use('default')
        sns.set_palette('Set2')
        
        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()
        
        if df_2040.empty:
            return saved_paths
        
        # Define metrics to compare
        metrics = [
            ('production_tonnes', 'Production', 'kt', 1000),
            ('revenue_usd', 'Revenue', 'Million USD', 1e6),
            ('energy_tonsCO2eq', 'CO₂ Emissions', 'kt CO₂eq', 1000)
        ]
        
        for metric_col, metric_title, units, divisor in metrics:
            if metric_col not in df_2040.columns:
                continue
                
            # Create figure with subplots for each scenario (3 rows for better comparison)
            fig, axes = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
            fig.suptitle(f'{metric_title}: Regional vs National Policy Approaches\n{get_country_name(iso3)}', 
                        fontsize=16, fontweight='bold', y=0.98)
            
            scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
            scenario_labels = ['Business as Usual', 'Early Refining', 'Precursor\nProduct']
            
            for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
                # Use correct scenario variants for proper comparison
                scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"  # For country constraints
                scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"   # For region constraints
                
                # National approaches (use country scenario)
                national_constrained = df_2040[
                    (df_2040['scenario'] == scenario_country_mid) & 
                    (df_2040['constraint'] == 'country_constrained')
                ][metric_col].sum() / divisor
                
                national_open = df_2040[
                    (df_2040['scenario'] == scenario_country_mid) & 
                    (df_2040['constraint'] == 'country_unconstrained')
                ][metric_col].sum() / divisor
                
                # Regional approaches (use region scenario)
                regional_constrained = df_2040[
                    (df_2040['scenario'] == scenario_region_mid) & 
                    (df_2040['constraint'] == 'region_constrained')
                ][metric_col].sum() / divisor
                
                regional_open = df_2040[
                    (df_2040['scenario'] == scenario_region_mid) & 
                    (df_2040['constraint'] == 'region_unconstrained')
                ][metric_col].sum() / divisor
                
                # Check if we have any data
                if (national_constrained == 0 and national_open == 0 and 
                    regional_constrained == 0 and regional_open == 0):
                    axes[i].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[i].transAxes)
                    axes[i].set_title(label)
                    continue
                
                # Create grouped bar chart
                x = np.arange(2)  # Two groups: Environmentally Constrained, Environmentally Unconstrained
                width = 0.35
                
                national_values = [national_constrained, national_open]
                regional_values = [regional_constrained, regional_open]
                
                bars1 = axes[i].bar(x - width/2, national_values, width, label='National Focus', alpha=0.8)
                bars2 = axes[i].bar(x + width/2, regional_values, width, label='Regional Integration', alpha=0.8)
                
                # Add value labels on bars
                for bars in [bars1, bars2]:
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            axes[i].text(bar.get_x() + bar.get_width()/2., height,
                                       f'{height:.1f}', ha='center', va='bottom', fontsize=10)
                
                axes[i].set_title(label, fontweight='bold', pad=10)
                axes[i].set_xlabel('Environmental Policy', fontweight='bold')
                if i == 0:
                    axes[i].set_ylabel(f'{metric_title} ({units})', fontweight='bold')
                axes[i].set_xticks(x)
                axes[i].set_xticklabels(['Environmentally\nConstrained', 'Environmentally\nUnconstrained'])
                axes[i].grid(axis='y', alpha=0.3)
                
                if i == 2:  # Show legend on last subplot
                    axes[i].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            output_path = os.path.join(output_dir, f'{metric_col}_policy_comparison_comprehensive.png')
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_paths.append(output_path)
        
    except Exception as e:
        print(f"Error creating comprehensive policy comparison: {e}")
    
    return saved_paths

def get_country_name(iso3):
    """Get full country name from ISO3 code - duplicate from generate_country_docx for independence"""
    country_mapping = {
        "AGO": "Angola", "BDI": "Burundi", "BWA": "Botswana", "KEN": "Kenya",
        "MWI": "Malawi", "UGA": "Uganda", 'ZMB': 'Zambia', 'COD': 'Democratic Republic of Congo', 
        'ZWE': 'Zimbabwe', 'NAM': 'Namibia', 'TZA': 'Tanzania', 'MDG': 'Madagascar',
        'MOZ': 'Mozambique', 'ZAF': 'South Africa'
    }
    return country_mapping.get(iso3, iso3)

def create_improved_goal_comparison_charts(df_country, output_dir, iso3):
    """Create improved goal comparison charts with error bars for low/high scenarios"""
    saved_paths = []
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from docx_utils import format_scenario_name, format_constraint_name
        
        # Set style
        plt.style.use('default')
        sns.set_palette('Set2')
        
        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()
        
        if df_2040.empty:
            return saved_paths
        
        # Define metrics to compare
        metrics = [
            ('production_tonnes', 'Production', 'kt', 1000),
            ('revenue_usd', 'Revenue', 'Million USD', 1e6),
            ('energy_tonsCO2eq', 'CO₂ Emissions', 'kt CO₂eq', 1000),
            ('water_usage_m3', 'Water Usage', 'Million m³', 1e6)
        ]
        
        for metric_col, metric_title, units, divisor in metrics:
            if metric_col not in df_2040.columns:
                continue
                
            # Create subplot for each constraint type
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'{metric_title} Comparison Across Development Strategies\n{get_country_name(iso3)}', 
                        fontsize=16, fontweight='bold', y=0.95)
            
            constraints = ['country_constrained', 'country_unconstrained', 'region_constrained', 'region_unconstrained']
            constraint_titles = ['National Policy\n(Environmentally Constrained)', 'National Policy\n(Environmentally Unconstrained)', 
                               'Regional Integration\n(Environmentally Constrained)', 'Regional Integration\n(Environmentally Unconstrained)']
            
            for i, (constraint, constraint_title) in enumerate(zip(constraints, constraint_titles)):
                row, col = i // 2, i % 2
                
                constraint_data = df_2040[df_2040['constraint'] == constraint]
                
                if constraint_data.empty:
                    axes[row, col].text(0.5, 0.5, 'No Data Available', ha='center', va='center', 
                                      transform=axes[row, col].transAxes, fontsize=12, style='italic')
                    axes[row, col].set_title(constraint_title, fontweight='bold', pad=10)
                    continue
                
                # Extract scenario bases and calculate error bars
                scenario_bases = ['bau_2040', 'early_refining_2040', 'precursor_2040']
                scenario_labels = ['Business as Usual', 'Early Refining', 'Precursor Product']
                
                x_pos = np.arange(len(scenario_bases))
                mid_values = []
                low_errors = []
                high_errors = []
                
                for base in scenario_bases:
                    # Get mid, low, high values - use correct threshold type for each constraint
                    if 'region' in constraint:
                        # Regional constraints use max_threshold
                        mid_data = constraint_data[constraint_data['scenario'] == f'{base}_mid_max_threshold_metal_tons']
                        low_data = constraint_data[constraint_data['scenario'] == f'{base}_low_max_threshold_metal_tons']  
                        high_data = constraint_data[constraint_data['scenario'] == f'{base}_high_max_threshold_metal_tons']
                    else:
                        # Country constraints use min_threshold  
                        mid_data = constraint_data[constraint_data['scenario'] == f'{base}_mid_min_threshold_metal_tons']
                        low_data = constraint_data[constraint_data['scenario'] == f'{base}_low_min_threshold_metal_tons']  
                        high_data = constraint_data[constraint_data['scenario'] == f'{base}_high_min_threshold_metal_tons']
                    
                    mid_val = mid_data[metric_col].sum() / divisor if not mid_data.empty else 0
                    low_val = low_data[metric_col].sum() / divisor if not low_data.empty else mid_val
                    high_val = high_data[metric_col].sum() / divisor if not high_data.empty else mid_val
                    
                    mid_values.append(mid_val)
                    low_errors.append(max(0, mid_val - low_val))  # Ensure non-negative
                    high_errors.append(max(0, high_val - mid_val))
                
                # Create bar plot with error bars
                bars = axes[row, col].bar(x_pos, mid_values, 
                                        yerr=[low_errors, high_errors],
                                        capsize=5,
                                        color=sns.color_palette('Set2', len(scenario_bases)), 
                                        alpha=0.8, edgecolor='black', linewidth=0.5)
                
                # Add value labels on bars
                for j, (bar, mid_val) in enumerate(zip(bars, mid_values)):
                    if mid_val > 0:  # Only label non-zero values
                        axes[row, col].text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                                          f'{mid_val:.1f}', ha='center', va='bottom', fontweight='bold')
                
                axes[row, col].set_title(constraint_title, fontweight='bold', pad=15)
                axes[row, col].set_ylabel(f'{metric_title} ({units})', fontweight='bold')
                axes[row, col].grid(axis='y', alpha=0.3)
                axes[row, col].set_xticks(x_pos)
                axes[row, col].set_xticklabels(scenario_labels, rotation=0, ha='center')
                
                # Set y-axis to start from 0 for better comparison
                axes[row, col].set_ylim(bottom=0)
            
            plt.tight_layout()
            output_path = os.path.join(output_dir, f'{metric_col}_comparison_with_errorbars.png')
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_paths.append(output_path)
        
    except Exception as e:
        print(f"Error creating improved goal comparison charts: {e}")
    
    return saved_paths

def create_production_subplot_charts_with_errorbars(df_country, output_dir, iso3):
    """Create production charts with error bars showing min/max uncertainty for mid scenarios"""
    saved_paths = []
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from docx_utils import format_scenario_name, format_constraint_name
        
        plt.style.use('default')
        sns.set_palette('Set2')
        
        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()
        
        if df_2040.empty:
            return saved_paths
        
        # Define the goal types and their display names
        goals = ['bau', 'early_refining', 'precursor']
        goal_titles = ['Business as Usual', 'Early Refining', 'Precursor Product']
        
        # Create figure with subplots for each goal (3 rows for better comparison)
        fig, axes = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
        fig.suptitle(f'Production Comparison with Uncertainty Range\n{get_country_name(iso3)}', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        for i, (goal, title) in enumerate(zip(goals, goal_titles)):
            # Get mid, min, and max scenarios for this goal
            mid_scenario = f'{goal}_2040_mid_min_threshold_metal_tons'
            min_scenario = f'{goal}_2040_low_min_threshold_metal_tons'
            max_scenario = f'{goal}_2040_high_max_threshold_metal_tons'
            
            # Get data for each scenario
            mid_data = df_2040[df_2040['scenario'] == mid_scenario]
            min_data = df_2040[df_2040['scenario'] == min_scenario]
            max_data = df_2040[df_2040['scenario'] == max_scenario]
            
            if mid_data.empty:
                axes[i].text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(f'2040 {title}')
                continue
            
            # Aggregate by constraint for main values
            mid_agg = mid_data.groupby('constraint')['production_tonnes'].sum().reset_index()
            mid_agg['production_kt'] = mid_agg['production_tonnes'] / 1000
            
            # Get min/max values for error bars
            if not min_data.empty and not max_data.empty:
                min_agg = min_data.groupby('constraint')['production_tonnes'].sum().reset_index()
                min_agg['production_kt'] = min_agg['production_tonnes'] / 1000
                max_agg = max_data.groupby('constraint')['production_tonnes'].sum().reset_index()
                max_agg['production_kt'] = max_agg['production_tonnes'] / 1000
                
                # Merge to align constraints
                merged = mid_agg.merge(min_agg[['constraint', 'production_kt']], on='constraint', suffixes=('', '_min'))
                merged = merged.merge(max_agg[['constraint', 'production_kt']], on='constraint', suffixes=('', '_max'))
                
                # Calculate error bars (distance from mid to min/max)
                merged['error_lower'] = merged['production_kt'] - merged['production_kt_min']
                merged['error_upper'] = merged['production_kt_max'] - merged['production_kt']
            else:
                # No error bars if min/max data not available
                merged = mid_agg.copy()
                merged['error_lower'] = 0
                merged['error_upper'] = 0
            
            # Clean constraint names for display
            merged['constraint_clean'] = merged['constraint'].apply(format_constraint_name)
            
            # Create bar plot with error bars
            x = np.arange(len(merged))
            bars = axes[i].bar(x, merged['production_kt'], width=0.6, 
                             color=sns.color_palette('Set2')[i], alpha=0.8)
            
            # Add error bars
            axes[i].errorbar(x, merged['production_kt'], 
                           yerr=[merged['error_lower'], merged['error_upper']], 
                           fmt='none', color='black', capsize=5, capthick=2, elinewidth=2)
            
            # Customize subplot
            axes[i].set_title(f'2040 {title}', fontweight='bold', pad=10)
            axes[i].set_xlabel('Policy Approach' if i == 1 else '', fontweight='bold')
            if i == 0:
                axes[i].set_ylabel('Production (kt)', fontweight='bold')
            axes[i].grid(axis='y', alpha=0.3)
            axes[i].set_xticks(x)
            axes[i].set_xticklabels(merged['constraint_clean'], rotation=45, ha='right')
            
            # Add value labels on bars
            for j, (bar, row) in enumerate(zip(bars, merged.itertuples())):
                height = bar.get_height()
                axes[i].text(bar.get_x() + bar.get_width()/2., height + row.error_upper,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'production_comparison_with_uncertainty.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)
        
        # Create a second chart showing all scenarios (low/mid/high) for comparison (3 rows for better comparison)
        fig, axes = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
        fig.suptitle(f'Production Scenarios: Low, Mid, High Estimates\n{get_country_name(iso3)}', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        for i, (goal, title) in enumerate(zip(goals, goal_titles)):
            # Get all scenarios for this goal
            goal_data = df_2040[df_2040['scenario'].str.contains(f'{goal}_2040')]
            
            if goal_data.empty:
                axes[i].text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(f'2040 {title}')
                continue
            
            # Aggregate by scenario level (low/mid/high) and constraint
            scenario_agg = []
            for level in ['low', 'mid', 'high']:
                level_data = goal_data[goal_data['scenario'].str.contains(f'_{level}_')]
                if not level_data.empty:
                    for constraint in level_data['constraint'].unique():
                        constraint_data = level_data[level_data['constraint'] == constraint]
                        total_prod = constraint_data['production_tonnes'].sum() / 1000
                        scenario_agg.append({
                            'level': level.capitalize(),
                            'constraint': format_constraint_name(constraint),
                            'production_kt': total_prod
                        })
            
            if scenario_agg:
                scenario_df = pd.DataFrame(scenario_agg)
                pivot = scenario_df.pivot(index='constraint', columns='level', values='production_kt').fillna(0)
                
                # Plot grouped bars
                pivot.plot(kind='bar', ax=axes[i], width=0.8, rot=45)
                axes[i].set_title(f'2040 {title}', fontweight='bold', pad=10)
                axes[i].set_xlabel('Policy Approach' if i == 1 else '', fontweight='bold')
                if i == 0:
                    axes[i].set_ylabel('Production (kt)', fontweight='bold')
                axes[i].grid(axis='y', alpha=0.3)
                axes[i].legend(title='Estimate Level', loc='upper left')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'production_scenarios_comparison.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)
        
    except Exception as e:
        print(f"Error creating production charts with error bars: {e}")
        import traceback
        traceback.print_exc()
    
    return saved_paths

def create_production_difference_charts(df_country, output_dir, iso3, permanent_dir=None):
    """Create production charts comparing all four constraint combinations for a country"""
    saved_paths = []
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from plot_utils import get_processing_type_colors
        
        plt.style.use('default')
        sns.set_palette('Set2')
        
        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()
        
        if df_2040.empty:
            return saved_paths
        
        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['Business as Usual', 'Early Refining', 'Precursor Product']
        
        # Create figure with subplots for each scenario
        fig, axes = plt.subplots(3, 1, figsize=(14, 15))
        fig.suptitle(f'Production by Policy Approach\n{get_country_name(iso3)}', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        constraints = ['country_constrained', 'country_unconstrained', 'region_constrained', 'region_unconstrained']
        constraint_labels = ['National\nConstrained', 'National\nUnconstrained', 'Regional\nConstrained', 'Regional\nUnconstrained']
        
        for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            # Use correct scenario variants for proper comparison
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"  # For country constraints
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"   # For region constraints
            
            # Get production by constraint and processing type (exclude Metal content)
            production_data = []
            
            # Country constrained (use country scenario)
            constraint_data = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_constrained') & 
                (df_2040['processing_type'] != 'Metal content')
            ]
            constraint_prod = constraint_data.groupby('processing_type')['production_tonnes'].sum() / 1000
            production_data.append(constraint_prod)
            
            # Country unconstrained (use country scenario)
            constraint_data = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_unconstrained') & 
                (df_2040['processing_type'] != 'Metal content')
            ]
            constraint_prod = constraint_data.groupby('processing_type')['production_tonnes'].sum() / 1000
            production_data.append(constraint_prod)
            
            # Region constrained (use region scenario)
            constraint_data = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_constrained') & 
                (df_2040['processing_type'] != 'Metal content')
            ]
            constraint_prod = constraint_data.groupby('processing_type')['production_tonnes'].sum() / 1000
            production_data.append(constraint_prod)
            
            # Region unconstrained (use region scenario)
            constraint_data = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_unconstrained') & 
                (df_2040['processing_type'] != 'Metal content')
            ]
            constraint_prod = constraint_data.groupby('processing_type')['production_tonnes'].sum() / 1000
            production_data.append(constraint_prod)
            
            # Get all unique processing types
            all_proc_types = sorted(set().union(*[set(d.index) for d in production_data if not d.empty]))
            
            if not all_proc_types:
                axes[i].text(0.5, 0.5, 'No Production Data', ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(label)
                continue
            
            # Create grouped bar chart
            x = np.arange(len(constraints))
            width = 0.8 / len(all_proc_types)
            
            # Plot bars for each processing type
            for j, proc_type in enumerate(all_proc_types):
                values = [d.get(proc_type, 0) if not d.empty else 0 for d in production_data]
                color = get_processing_type_colors().get(proc_type, '#808080')
                offset = (j - len(all_proc_types)/2 + 0.5) * width
                bars = axes[i].bar(x + offset, values, width, label=proc_type, color=color, alpha=0.8)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    if height > 0.5:  # Only label if significant
                        axes[i].text(bar.get_x() + bar.get_width()/2., height,
                                   f'{height:.0f}', ha='center', va='bottom', fontsize=8)
            
            axes[i].set_title(f'{label}', fontweight='bold', fontsize=12)
            axes[i].set_ylabel('Production (kt)', fontweight='bold')
            axes[i].set_xticks(x)
            axes[i].set_xticklabels(constraint_labels)
            axes[i].grid(axis='y', alpha=0.3)
            
            # Add legend only to first subplot
            if i == 0:
                axes[i].legend(title='Processing Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'production_constraint_comparison.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)
        
        # Create a simplified total production comparison
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f'Total Production by Policy Approach\n{get_country_name(iso3)}', 
                     fontsize=14, fontweight='bold')
        
        for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            # Use correct scenario variants for proper comparison
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"  # For country constraints
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"   # For region constraints
            
            # Calculate total production for each constraint using correct scenarios
            totals = []
            
            # Country constrained (use country scenario)
            country_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_constrained')
            ]['production_tonnes'].sum() / 1000
            totals.append(country_constrained)
            
            # Country unconstrained (use country scenario)
            country_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_unconstrained')
            ]['production_tonnes'].sum() / 1000
            totals.append(country_unconstrained)
            
            # Region constrained (use region scenario)
            region_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_constrained')
            ]['production_tonnes'].sum() / 1000
            totals.append(region_constrained)
            
            # Region unconstrained (use region scenario) 
            region_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_unconstrained')
            ]['production_tonnes'].sum() / 1000
            totals.append(region_unconstrained)
            
            # Check if we have any data
            if all(t == 0 for t in totals):
                axes[i].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(label)
                continue
            
            # Color bars differently for National vs Regional
            colors = ['#1f77b4', '#1f77b4', '#ff7f0e', '#ff7f0e']  # Blue for National, Orange for Regional
            
            # Plot bars individually with different alphas
            bars = []
            alphas = [0.6, 1.0, 0.6, 1.0]  # Lighter for constrained, darker for unconstrained
            for j, (color, alpha, total) in enumerate(zip(colors, alphas, totals)):
                bar = axes[i].bar(j, total, color=color, alpha=alpha)
                bars.extend(bar)
            
            # Add value labels
            for bar, val in zip(bars, totals):
                if val > 0:
                    axes[i].text(bar.get_x() + bar.get_width()/2., val,
                               f'{val:.0f}', ha='center', va='bottom', fontweight='bold')
            
            axes[i].set_title(label, fontweight='bold')
            axes[i].set_ylabel('Total Production (kt)' if i == 0 else '', fontweight='bold')
            axes[i].set_xticks(range(len(constraints)))
            axes[i].set_xticklabels(constraint_labels, rotation=45, ha='right')
            axes[i].grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'production_total_comparison.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)
        
    except Exception as e:
        print(f"Error creating production comparison charts: {e}")
        import traceback
        traceback.print_exc()

    # Save to permanent location if specified
    if permanent_dir:
        for path in saved_paths:
            save_chart_to_permanent_location(path, permanent_dir, iso3)

    return saved_paths

def create_revenue_difference_charts(df_country, output_dir, iso3, permanent_dir=None):
    """Create revenue charts comparing all four constraint combinations for a country"""
    saved_paths = []
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        
        plt.style.use('default')
        sns.set_palette('Set2')
        
        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()
        
        if df_2040.empty:
            return saved_paths
        
        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['Business as Usual', 'Early Refining', 'Precursor Product']
        
        constraints = ['country_constrained', 'country_unconstrained', 'region_constrained', 'region_unconstrained']
        constraint_labels = ['National\nConstrained', 'National\nUnconstrained', 'Regional\nConstrained', 'Regional\nUnconstrained']
        
        # Create figure with subplots for absolute values
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f'Revenue by Policy Approach\n{get_country_name(iso3)}', 
                     fontsize=14, fontweight='bold')
        
        for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            # Use correct scenario variants for proper comparison
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"  # For country constraints
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"   # For region constraints
            
            # Calculate revenue for each constraint using correct scenarios
            revenues = []
            
            # Country constrained (use country scenario)
            country_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_constrained')
            ]['revenue_usd'].sum() / 1e6
            revenues.append(country_constrained)
            
            # Country unconstrained (use country scenario)
            country_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_unconstrained')
            ]['revenue_usd'].sum() / 1e6
            revenues.append(country_unconstrained)
            
            # Region constrained (use region scenario)
            region_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_constrained')
            ]['revenue_usd'].sum() / 1e6
            revenues.append(region_constrained)
            
            # Region unconstrained (use region scenario)
            region_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_unconstrained')
            ]['revenue_usd'].sum() / 1e6
            revenues.append(region_unconstrained)
            
            # Check if we have any data
            if all(r == 0 for r in revenues):
                axes[i].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[i].transAxes)
                axes[i].set_title(label)
                continue
            
            # Color bars differently for National vs Regional  
            colors = ['#1f77b4', '#1f77b4', '#ff7f0e', '#ff7f0e']  # Blue for National, Orange for Regional
            
            # Plot bars individually with different alphas
            bars = []
            alphas = [0.6, 1.0, 0.6, 1.0]  # Lighter for constrained, darker for unconstrained
            for j, (color, alpha, revenue) in enumerate(zip(colors, alphas, revenues)):
                bar = axes[i].bar(j, revenue, color=color, alpha=alpha)
                bars.extend(bar)
            
            # Add value labels
            for bar, val in zip(bars, revenues):
                if val > 0:
                    axes[i].text(bar.get_x() + bar.get_width()/2., val,
                               f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
            
            axes[i].set_title(label, fontweight='bold')
            axes[i].set_ylabel('Revenue (Million USD)' if i == 0 else '', fontweight='bold')
            axes[i].set_xticks(range(len(constraints)))
            axes[i].set_xticklabels(constraint_labels, rotation=45, ha='right')
            axes[i].grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'revenue_constraint_comparison.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)
        
        # Create difference and percentage change chart
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Revenue Differences: Regional vs National\n{get_country_name(iso3)}', 
                     fontsize=14, fontweight='bold')
        
        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            # Use correct scenario variants for proper comparison
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"  # For country constraints
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"   # For region constraints
            
            # Calculate revenues using correct scenario variants
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_constrained')
            ]['revenue_usd'].sum() / 1e6
            
            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) & 
                (df_2040['constraint'] == 'country_unconstrained')
            ]['revenue_usd'].sum() / 1e6
            
            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_constrained')
            ]['revenue_usd'].sum() / 1e6
            
            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) & 
                (df_2040['constraint'] == 'region_unconstrained')
            ]['revenue_usd'].sum() / 1e6
            
            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and 
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue
            
            # Calculate differences (Regional - National)
            diff_constrained = regional_constrained - national_constrained
            diff_unconstrained = regional_unconstrained - national_unconstrained
            
            # Calculate percentage changes
            pct_constrained = ((regional_constrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_unconstrained = ((regional_unconstrained / national_unconstrained) - 1) * 100 if national_unconstrained != 0 else 0
            
            # Plot absolute differences (top row)
            values = [diff_constrained, diff_unconstrained]
            colors = ['#fc8d62', '#66c2a5']  # Different colors for constrained/unconstrained
            bars = axes[0, col].bar(['Constrained', 'Unconstrained'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('Revenue Difference\n(Million USD)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)
            
            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')
            
            # Plot percentage differences (bottom row)
            pct_values = [pct_constrained, pct_unconstrained]
            bars = axes[1, col].bar(['Constrained', 'Unconstrained'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)
            
            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'revenue_differences_regional_vs_national.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

        # Chart 3: Constrained vs Unconstrained differences
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Revenue Differences: Constrained vs Unconstrained\n{get_country_name(iso3)}',
                     fontsize=14, fontweight='bold')

        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"

            # Calculate revenues
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_constrained')
            ]['revenue_usd'].sum() / 1e6

            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_unconstrained')
            ]['revenue_usd'].sum() / 1e6

            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_constrained')
            ]['revenue_usd'].sum() / 1e6

            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_unconstrained')
            ]['revenue_usd'].sum() / 1e6

            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue

            # Calculate differences (Unconstrained - Constrained)
            diff_national = national_unconstrained - national_constrained
            diff_regional = regional_unconstrained - regional_constrained

            # Calculate percentage changes
            pct_national = ((national_unconstrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_regional = ((regional_unconstrained / regional_constrained) - 1) * 100 if regional_constrained != 0 else 0

            # Plot absolute differences (top row)
            values = [diff_national, diff_regional]
            colors = ['#1f77b4', '#ff7f0e']  # Blue for National, Orange for Regional
            bars = axes[0, col].bar(['National', 'Regional'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('Revenue Difference\n(Million USD)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')

            # Plot percentage differences (bottom row)
            pct_values = [pct_national, pct_regional]
            bars = axes[1, col].bar(['National', 'Regional'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)

            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'revenue_differences_constrained_vs_unconstrained.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

    except Exception as e:
        print(f"Error creating revenue comparison charts: {e}")
        import traceback
        traceback.print_exc()

    # Save to permanent location if specified
    if permanent_dir:
        for path in saved_paths:
            save_chart_to_permanent_location(path, permanent_dir, iso3)

    return saved_paths

def create_production_difference_charts(df_country, output_dir, iso3, permanent_dir=None):
    """Create production difference charts comparing Regional vs National and Constrained vs Unconstrained"""
    saved_paths = []

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np

        plt.style.use('default')
        sns.set_palette('Set2')

        # Filter for 2040 scenarios, exclude Metal content
        df_2040 = df_country[
            (df_country['scenario'].str.contains('2040')) &
            (df_country['processing_type'] != 'Metal content')
        ].copy()

        if df_2040.empty:
            return saved_paths

        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['Business as Usual', 'Early Refining', 'Precursor Product']

        # Chart 1: Regional vs National differences
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Production Differences: Regional vs National\n{get_country_name(iso3)}',
                     fontsize=14, fontweight='bold')

        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"

            # Calculate production for each constraint
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_constrained')
            ]['production_tonnes'].sum() / 1000

            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_unconstrained')
            ]['production_tonnes'].sum() / 1000

            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_constrained')
            ]['production_tonnes'].sum() / 1000

            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_unconstrained')
            ]['production_tonnes'].sum() / 1000

            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue

            # Calculate differences (Regional - National)
            diff_constrained = regional_constrained - national_constrained
            diff_unconstrained = regional_unconstrained - national_unconstrained

            # Calculate percentage changes
            pct_constrained = ((regional_constrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_unconstrained = ((regional_unconstrained / national_unconstrained) - 1) * 100 if national_unconstrained != 0 else 0

            # Plot absolute differences (top row)
            values = [diff_constrained, diff_unconstrained]
            colors = ['#fc8d62', '#66c2a5']
            bars = axes[0, col].bar(['Constrained', 'Unconstrained'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('Production Difference\n(kt)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')

            # Plot percentage differences (bottom row)
            pct_values = [pct_constrained, pct_unconstrained]
            bars = axes[1, col].bar(['Constrained', 'Unconstrained'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)

            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'production_differences_regional_vs_national.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

        # Chart 2: Constrained vs Unconstrained differences
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Production Differences: Constrained vs Unconstrained\n{get_country_name(iso3)}',
                     fontsize=14, fontweight='bold')

        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"

            # Calculate production for each combination
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_constrained')
            ]['production_tonnes'].sum() / 1000

            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_unconstrained')
            ]['production_tonnes'].sum() / 1000

            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_constrained')
            ]['production_tonnes'].sum() / 1000

            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_unconstrained')
            ]['production_tonnes'].sum() / 1000

            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue

            # Calculate differences (Unconstrained - Constrained)
            diff_national = national_unconstrained - national_constrained
            diff_regional = regional_unconstrained - regional_constrained

            # Calculate percentage changes
            pct_national = ((national_unconstrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_regional = ((regional_unconstrained / regional_constrained) - 1) * 100 if regional_constrained != 0 else 0

            # Plot absolute differences (top row)
            values = [diff_national, diff_regional]
            colors = ['#1f77b4', '#ff7f0e']  # Blue for National, Orange for Regional
            bars = axes[0, col].bar(['National', 'Regional'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('Production Difference\n(kt)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')

            # Plot percentage differences (bottom row)
            pct_values = [pct_national, pct_regional]
            bars = axes[1, col].bar(['National', 'Regional'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)

            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'production_differences_constrained_vs_unconstrained.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

    except Exception as e:
        print(f"Error creating production difference charts: {e}")
        import traceback
        traceback.print_exc()

    # Save to permanent location if specified
    if permanent_dir:
        for path in saved_paths:
            save_chart_to_permanent_location(path, permanent_dir, iso3)

    return saved_paths

def create_water_difference_charts(df_country, output_dir, iso3, permanent_dir=None):
    """Create water usage difference charts comparing Regional vs National and Constrained vs Unconstrained"""
    saved_paths = []

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np

        plt.style.use('default')
        sns.set_palette('Set2')

        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()

        if df_2040.empty:
            return saved_paths

        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['Business as Usual', 'Early Refining', 'Precursor Product']

        # Chart 1: Regional vs National differences
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Water Usage Differences: Regional vs National\n{get_country_name(iso3)}',
                     fontsize=14, fontweight='bold')

        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"

            # Calculate water usage for each constraint
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_constrained')
            ]['water_usage_m3'].sum() / 1e6

            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_unconstrained')
            ]['water_usage_m3'].sum() / 1e6

            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_constrained')
            ]['water_usage_m3'].sum() / 1e6

            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_unconstrained')
            ]['water_usage_m3'].sum() / 1e6

            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue

            # Calculate differences (Regional - National)
            diff_constrained = regional_constrained - national_constrained
            diff_unconstrained = regional_unconstrained - national_unconstrained

            # Calculate percentage changes
            pct_constrained = ((regional_constrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_unconstrained = ((regional_unconstrained / national_unconstrained) - 1) * 100 if national_unconstrained != 0 else 0

            # Plot absolute differences (top row)
            values = [diff_constrained, diff_unconstrained]
            colors = ['#fc8d62', '#66c2a5']
            bars = axes[0, col].bar(['Constrained', 'Unconstrained'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('Water Usage Difference\n(Million m³)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')

            # Plot percentage differences (bottom row)
            pct_values = [pct_constrained, pct_unconstrained]
            bars = axes[1, col].bar(['Constrained', 'Unconstrained'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)

            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'water_differences_regional_vs_national.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

        # Chart 2: Constrained vs Unconstrained differences
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Water Usage Differences: Constrained vs Unconstrained\n{get_country_name(iso3)}',
                     fontsize=14, fontweight='bold')

        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"

            # Calculate water usage
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_constrained')
            ]['water_usage_m3'].sum() / 1e6

            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_unconstrained')
            ]['water_usage_m3'].sum() / 1e6

            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_constrained')
            ]['water_usage_m3'].sum() / 1e6

            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_unconstrained')
            ]['water_usage_m3'].sum() / 1e6

            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue

            # Calculate differences (Unconstrained - Constrained)
            diff_national = national_unconstrained - national_constrained
            diff_regional = regional_unconstrained - regional_constrained

            # Calculate percentage changes
            pct_national = ((national_unconstrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_regional = ((regional_unconstrained / regional_constrained) - 1) * 100 if regional_constrained != 0 else 0

            # Plot absolute differences (top row)
            values = [diff_national, diff_regional]
            colors = ['#1f77b4', '#ff7f0e']
            bars = axes[0, col].bar(['National', 'Regional'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('Water Usage Difference\n(Million m³)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')

            # Plot percentage differences (bottom row)
            pct_values = [pct_national, pct_regional]
            bars = axes[1, col].bar(['National', 'Regional'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)

            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'water_differences_constrained_vs_unconstrained.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

    except Exception as e:
        print(f"Error creating water difference charts: {e}")
        import traceback
        traceback.print_exc()

    # Save to permanent location if specified
    if permanent_dir:
        for path in saved_paths:
            save_chart_to_permanent_location(path, permanent_dir, iso3)

    return saved_paths

def create_emissions_difference_charts(df_country, output_dir, iso3, permanent_dir=None):
    """Create CO2 emissions difference charts comparing Regional vs National and Constrained vs Unconstrained"""
    saved_paths = []

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np

        plt.style.use('default')
        sns.set_palette('Set2')

        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()

        if df_2040.empty:
            return saved_paths

        # Calculate total CO2 (transport + energy)
        df_2040['total_co2_kt'] = (df_2040['transport_total_tonsCO2eq'] + df_2040['energy_tonsCO2eq']) / 1000

        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['Business as Usual', 'Early Refining', 'Precursor Product']

        # Chart 1: Regional vs National differences
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'CO₂ Emissions Differences: Regional vs National\n{get_country_name(iso3)}',
                     fontsize=14, fontweight='bold')

        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"

            # Calculate emissions for each constraint
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_constrained')
            ]['total_co2_kt'].sum()

            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_unconstrained')
            ]['total_co2_kt'].sum()

            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_constrained')
            ]['total_co2_kt'].sum()

            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_unconstrained')
            ]['total_co2_kt'].sum()

            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue

            # Calculate differences (Regional - National)
            diff_constrained = regional_constrained - national_constrained
            diff_unconstrained = regional_unconstrained - national_unconstrained

            # Calculate percentage changes
            pct_constrained = ((regional_constrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_unconstrained = ((regional_unconstrained / national_unconstrained) - 1) * 100 if national_unconstrained != 0 else 0

            # Plot absolute differences (top row)
            values = [diff_constrained, diff_unconstrained]
            colors = ['#fc8d62', '#66c2a5']
            bars = axes[0, col].bar(['Constrained', 'Unconstrained'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('CO₂ Emissions Difference\n(kt CO₂eq)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')

            # Plot percentage differences (bottom row)
            pct_values = [pct_constrained, pct_unconstrained]
            bars = axes[1, col].bar(['Constrained', 'Unconstrained'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)

            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'emissions_differences_regional_vs_national.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

        # Chart 2: Constrained vs Unconstrained differences
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'CO₂ Emissions Differences: Constrained vs Unconstrained\n{get_country_name(iso3)}',
                     fontsize=14, fontweight='bold')

        for col, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
            scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"
            scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"

            # Calculate emissions
            national_constrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_constrained')
            ]['total_co2_kt'].sum()

            national_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_country_mid) &
                (df_2040['constraint'] == 'country_unconstrained')
            ]['total_co2_kt'].sum()

            regional_constrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_constrained')
            ]['total_co2_kt'].sum()

            regional_unconstrained = df_2040[
                (df_2040['scenario'] == scenario_region_mid) &
                (df_2040['constraint'] == 'region_unconstrained')
            ]['total_co2_kt'].sum()

            # Check if we have any data
            if (national_constrained == 0 and national_unconstrained == 0 and
                regional_constrained == 0 and regional_unconstrained == 0):
                axes[0, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[0, col].transAxes)
                axes[1, col].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[1, col].transAxes)
                axes[0, col].set_title(label)
                continue

            # Calculate differences (Unconstrained - Constrained)
            diff_national = national_unconstrained - national_constrained
            diff_regional = regional_unconstrained - regional_constrained

            # Calculate percentage changes
            pct_national = ((national_unconstrained / national_constrained) - 1) * 100 if national_constrained != 0 else 0
            pct_regional = ((regional_unconstrained / regional_constrained) - 1) * 100 if regional_constrained != 0 else 0

            # Plot absolute differences (top row)
            values = [diff_national, diff_regional]
            colors = ['#1f77b4', '#ff7f0e']
            bars = axes[0, col].bar(['National', 'Regional'], values, color=colors, alpha=0.8)
            axes[0, col].set_title(label, fontweight='bold')
            if col == 0:
                axes[0, col].set_ylabel('CO₂ Emissions Difference\n(kt CO₂eq)', fontweight='bold')
            axes[0, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[0, col].grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, val in zip(bars, values):
                if abs(val) > 0.01:
                    axes[0, col].text(bar.get_x() + bar.get_width()/2., val,
                                    f'{val:.1f}', ha='center',
                                    va='bottom' if val > 0 else 'top', fontweight='bold')

            # Plot percentage differences (bottom row)
            pct_values = [pct_national, pct_regional]
            bars = axes[1, col].bar(['National', 'Regional'], pct_values, color=colors, alpha=0.8)
            if col == 0:
                axes[1, col].set_ylabel('Percentage Change (%)', fontweight='bold')
            axes[1, col].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            axes[1, col].grid(axis='y', alpha=0.3)

            # Add percentage labels
            for bar, pct in zip(bars, pct_values):
                if abs(pct) > 0.01:
                    axes[1, col].text(bar.get_x() + bar.get_width()/2., pct,
                                    f'{pct:.1f}%', ha='center',
                                    va='bottom' if pct > 0 else 'top', fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'emissions_differences_constrained_vs_unconstrained.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(output_path)

    except Exception as e:
        print(f"Error creating emissions difference charts: {e}")
        import traceback
        traceback.print_exc()

    # Save to permanent location if specified
    if permanent_dir:
        for path in saved_paths:
            save_chart_to_permanent_location(path, permanent_dir, iso3)

    return saved_paths

def create_consolidated_goal_comparison(df_country, output_dir, iso3, permanent_dir=None):
    """Create a single consolidated chart showing all goal comparisons"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        
        plt.style.use('default')
        sns.set_palette('Set2')
        
        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()
        
        if df_2040.empty:
            return None
        
        # Define metrics to compare
        metrics = [
            ('production_tonnes', 'Production', 'kt', 1000),
            ('revenue_usd', 'Revenue', 'Million USD', 1e6),
            ('water_usage_m3', 'Water Usage', 'Million m³', 1e6),
            ('energy_tonsCO2eq', 'CO₂ Emissions', 'kt CO₂eq', 1000)
        ]
        
        # Create 2x2 subplot layout
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Strategic Goal Comparison (2040)\n{get_country_name(iso3)}', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['BAU', 'Early\nRefining', 'Precursor']
        
        for idx, (metric_col, metric_title, units, divisor) in enumerate(metrics):
            row, col = idx // 2, idx % 2
            
            if metric_col not in df_2040.columns:
                axes[row, col].text(0.5, 0.5, 'Data Not Available', ha='center', va='center', 
                                   transform=axes[row, col].transAxes, style='italic')
                axes[row, col].set_title(f'{metric_title} ({units})', fontweight='bold')
                continue
            
            # Aggregate data by scenario and constraint
            scenario_data = []
            
            for scenario in scenarios:
                scenario_vals = []
                # Use correct scenario variants for proper comparison
                scenario_country_mid = f"{scenario}_mid_min_threshold_metal_tons"  # For country constraints
                scenario_region_mid = f"{scenario}_mid_max_threshold_metal_tons"   # For region constraints
                
                # Country unconstrained (use country scenario)
                country_val = df_2040[
                    (df_2040['scenario'] == scenario_country_mid) & 
                    (df_2040['constraint'] == 'country_unconstrained')
                ][metric_col].sum() / divisor
                scenario_vals.append(country_val)
                
                # Region unconstrained (use region scenario)
                region_val = df_2040[
                    (df_2040['scenario'] == scenario_region_mid) & 
                    (df_2040['constraint'] == 'region_unconstrained')
                ][metric_col].sum() / divisor
                scenario_vals.append(region_val)
                
                scenario_data.append(scenario_vals)
            
            # Create grouped bar chart
            x = np.arange(len(scenarios))
            width = 0.35
            
            national_vals = [data[0] for data in scenario_data]
            regional_vals = [data[1] for data in scenario_data]
            
            bars1 = axes[row, col].bar(x - width/2, national_vals, width, label='National', alpha=0.8)
            bars2 = axes[row, col].bar(x + width/2, regional_vals, width, label='Regional', alpha=0.8)
            
            # Add value labels
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        axes[row, col].text(bar.get_x() + bar.get_width()/2., height,
                                          f'{height:.1f}', ha='center', va='bottom', fontsize=9)
            
            axes[row, col].set_title(f'{metric_title} ({units})', fontweight='bold', fontsize=12)
            axes[row, col].set_xticks(x)
            axes[row, col].set_xticklabels(scenario_labels)
            axes[row, col].grid(axis='y', alpha=0.3)
            
            # Add legend only to first subplot
            if idx == 0:
                axes[row, col].legend()
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'consolidated_goal_comparison_2040.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Save to permanent location if specified
        if permanent_dir:
            save_chart_to_permanent_location(output_path, permanent_dir, iso3)

        return output_path

    except Exception as e:
        print(f"Error creating consolidated goal comparison: {e}")
        return None

def create_consolidated_revenue_chart(df_country, output_dir, iso3, permanent_dir=None):
    """Create a single consolidated chart showing revenue across scenarios with stacked bars by mineral"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from plot_utils import get_mineral_colors

        plt.style.use('default')

        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()

        if df_2040.empty:
            return None

        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['BAU', 'Early Refining', 'Precursor']

        # Get minerals with revenue
        minerals = df_2040['reference_mineral'].unique()
        minerals_with_revenue = []

        for mineral in minerals:
            mineral_data = df_2040[df_2040['reference_mineral'] == mineral]
            total_revenue = mineral_data['revenue_usd'].sum()
            if total_revenue > 0:
                minerals_with_revenue.append(mineral)

        minerals = sorted(minerals_with_revenue)

        if len(minerals) == 0:
            print(f"No minerals with export revenue found for {iso3}")
            return None

        # Create stacked bar chart with 4 policy combinations
        fig, ax = plt.subplots(figsize=(14, 9))
        fig.suptitle(f'Export Revenue by Development Strategy\n{get_country_name(iso3)}',
                     fontsize=18, fontweight='bold')

        # For BAU: National = Regional, so only show constrained/unconstrained
        # For others: Show all 4 policy combinations
        policy_combos_full = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Nat.\nConstr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Nat.\nUnconstr.'),
            ('mid_max_threshold_metal_tons', 'region_constrained', 'Reg.\nConstr.'),
            ('mid_max_threshold_metal_tons', 'region_unconstrained', 'Reg.\nUnconstr.')
        ]

        policy_combos_bau = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Constr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Unconstr.')
        ]

        # Get mineral colors
        mineral_colors = get_mineral_colors()
        colors = [mineral_colors.get(m, '#808080') for m in minerals]

        # Calculate bar positions manually for each scenario
        bar_width = 0.18
        x_base = np.arange(len(scenarios))

        # For BAU: 2 bars centered, for others: 4 bars
        all_bar_positions = []
        all_bar_labels = []
        all_bar_data = []

        for scenario_idx, scenario in enumerate(scenarios):
            if scenario == 'bau_2040':
                # BAU: only 2 bars (constrained/unconstrained)
                n_bars = 2
                policy_combos = policy_combos_bau
                x_offset = np.array([-0.5, 0.5]) * bar_width
            else:
                # Other scenarios: 4 bars
                n_bars = 4
                policy_combos = policy_combos_full
                x_offset = np.array([-1.5, -0.5, 0.5, 1.5]) * bar_width

            for bar_idx, (scenario_suffix, constraint, label) in enumerate(policy_combos):
                scenario_name = f"{scenario}_{scenario_suffix}"
                x_pos = x_base[scenario_idx] + x_offset[bar_idx]

                # Collect data for this bar
                bar_data = {}
                for mineral in minerals:
                    value = df_2040[
                        (df_2040['scenario'] == scenario_name) &
                        (df_2040['constraint'] == constraint) &
                        (df_2040['reference_mineral'] == mineral)
                    ]['revenue_usd'].sum() / 1e6
                    bar_data[mineral] = value

                all_bar_positions.append(x_pos)
                all_bar_labels.append(label)
                all_bar_data.append(bar_data)

        # Plot all bars with stacked minerals
        for mineral_idx, mineral in enumerate(minerals):
            values = [bar_data.get(mineral, 0) for bar_data in all_bar_data]
            bottoms = np.zeros(len(all_bar_positions))

            # Calculate bottoms for stacking
            for prev_mineral_idx in range(mineral_idx):
                prev_mineral = minerals[prev_mineral_idx]
                prev_values = [bar_data.get(prev_mineral, 0) for bar_data in all_bar_data]
                bottoms += prev_values

            ax.bar(all_bar_positions, values, bar_width, bottom=bottoms,
                   label=mineral.title() if mineral_idx < len(minerals) else "",
                   color=colors[mineral_idx], alpha=0.85,
                   edgecolor='white', linewidth=0.5)

        # Customize chart
        ax.set_ylabel('Export Revenue (Million USD)', fontsize=13, fontweight='bold')
        ax.set_xlabel('Development Strategy', fontsize=13, fontweight='bold')
        ax.set_xticks(x_base)
        ax.set_xticklabels(scenario_labels, fontsize=12, fontweight='bold')

        # Add policy labels below
        minor_ticks = all_bar_positions
        minor_labels = all_bar_labels

        ax.set_xticks(minor_ticks, minor=True)
        ax.set_xticklabels(minor_labels, minor=True, fontsize=7, style='italic')
        ax.tick_params(axis='x', which='minor', length=0, pad=2)
        ax.tick_params(axis='both', which='major', labelsize=11)

        ax.grid(axis='y', alpha=0.3)
        ax.legend(title='Mineral', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11)

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'consolidated_revenue_comparison.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Save to permanent location if specified
        if permanent_dir:
            save_chart_to_permanent_location(output_path, permanent_dir, iso3)

        return output_path

    except Exception as e:
        print(f"Error creating consolidated revenue chart: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_consolidated_production_chart(df_country, output_dir, iso3, permanent_dir=None):
    """Create a single consolidated chart showing production by processing type across scenarios with 4 policy combinations"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from plot_utils import get_processing_type_colors

        # Filter for 2040 scenarios and exclude Metal content
        df_2040 = df_country[
            (df_country['scenario'].str.contains('2040')) &
            (df_country['processing_type'] != 'Metal content')
        ].copy()

        if df_2040.empty:
            return None

        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['BAU', 'Early Refining', 'Precursor']

        # For BAU: National = Regional, so only show constrained/unconstrained
        policy_combos_full = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Nat.\nConstr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Nat.\nUnconstr.'),
            ('mid_max_threshold_metal_tons', 'region_constrained', 'Reg.\nConstr.'),
            ('mid_max_threshold_metal_tons', 'region_unconstrained', 'Reg.\nUnconstr.')
        ]

        policy_combos_bau = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Constr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Unconstr.')
        ]

        # Get unique processing types across all policies
        unique_proc_types = sorted(df_2040['processing_type'].unique())

        if not unique_proc_types:
            return None

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 9))
        fig.suptitle(f'Production by Processing Type and Development Strategy\n{get_country_name(iso3)}',
                     fontsize=18, fontweight='bold')

        # Get processing type colors
        colors = [get_processing_type_colors().get(pt, '#808080') for pt in unique_proc_types]

        # Calculate bar positions for each scenario
        bar_width = 0.18
        x_base = np.arange(len(scenarios))

        all_bar_positions = []
        all_bar_labels = []
        all_bar_data = []

        for scenario_idx, scenario in enumerate(scenarios):
            if scenario == 'bau_2040':
                n_bars = 2
                policy_combos = policy_combos_bau
                x_offset = np.array([-0.5, 0.5]) * bar_width
            else:
                n_bars = 4
                policy_combos = policy_combos_full
                x_offset = np.array([-1.5, -0.5, 0.5, 1.5]) * bar_width

            for bar_idx, (scenario_suffix, constraint, label) in enumerate(policy_combos):
                scenario_name = f"{scenario}_{scenario_suffix}"
                x_pos = x_base[scenario_idx] + x_offset[bar_idx]

                bar_data = {}
                for proc_type in unique_proc_types:
                    value = df_2040[
                        (df_2040['scenario'] == scenario_name) &
                        (df_2040['constraint'] == constraint) &
                        (df_2040['processing_type'] == proc_type)
                    ]['production_tonnes'].sum() / 1000
                    bar_data[proc_type] = value

                all_bar_positions.append(x_pos)
                all_bar_labels.append(label)
                all_bar_data.append(bar_data)

        # Plot all bars with stacked processing types
        for proc_type_idx, proc_type in enumerate(unique_proc_types):
            values = [bar_data.get(proc_type, 0) for bar_data in all_bar_data]
            bottoms = np.zeros(len(all_bar_positions))

            for prev_proc_idx in range(proc_type_idx):
                prev_proc = unique_proc_types[prev_proc_idx]
                prev_values = [bar_data.get(prev_proc, 0) for bar_data in all_bar_data]
                bottoms += prev_values

            ax.bar(all_bar_positions, values, bar_width, bottom=bottoms,
                   label=proc_type if proc_type_idx < len(unique_proc_types) else "",
                   color=colors[proc_type_idx], alpha=0.85,
                   edgecolor='white', linewidth=0.5)

        # Customize chart with larger fonts
        ax.set_ylabel('Production (kt)', fontsize=13, fontweight='bold')
        ax.set_xlabel('Development Strategy', fontsize=13, fontweight='bold')
        ax.set_xticks(x_base)
        ax.set_xticklabels(scenario_labels, fontsize=12, fontweight='bold')

        # Add policy labels below
        minor_ticks = all_bar_positions
        minor_labels = all_bar_labels

        ax.set_xticks(minor_ticks, minor=True)
        ax.set_xticklabels(minor_labels, minor=True, fontsize=7, style='italic')
        ax.tick_params(axis='x', which='minor', length=0, pad=2)
        ax.tick_params(axis='both', which='major', labelsize=11)

        ax.grid(axis='y', alpha=0.3)
        ax.legend(title='Processing Type', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11)

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'consolidated_production_by_type.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Save to permanent location if specified
        if permanent_dir:
            save_chart_to_permanent_location(output_path, permanent_dir, iso3)

        return output_path

    except Exception as e:
        print(f"Error creating consolidated production chart: {e}")
        return None

def create_consolidated_water_chart(df_country, output_dir, iso3, permanent_dir=None):
    """Create a single consolidated chart showing water usage across scenarios with stacked bars by mineral"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from plot_utils import get_mineral_colors

        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()

        if df_2040.empty:
            return None

        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['BAU', 'Early Refining', 'Precursor']

        # Filter out minerals with no water usage
        minerals_with_usage = []
        for mineral in df_2040['reference_mineral'].unique():
            if df_2040[df_2040['reference_mineral'] == mineral]['water_usage_m3'].sum() > 0:
                minerals_with_usage.append(mineral)

        minerals = sorted(minerals_with_usage)

        if len(minerals) == 0:
            print(f"No minerals with water usage found for {iso3}")
            return None

        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(14, 9))
        fig.suptitle(f'Water Usage by Development Strategy\n{get_country_name(iso3)}',
                     fontsize=18, fontweight='bold')

        # For BAU: National = Regional, so only show constrained/unconstrained
        policy_combos_full = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Nat.\nConstr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Nat.\nUnconstr.'),
            ('mid_max_threshold_metal_tons', 'region_constrained', 'Reg.\nConstr.'),
            ('mid_max_threshold_metal_tons', 'region_unconstrained', 'Reg.\nUnconstr.')
        ]

        policy_combos_bau = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Constr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Unconstr.')
        ]

        # Get mineral colors
        mineral_colors = get_mineral_colors()
        colors = [mineral_colors.get(m, '#808080') for m in minerals]

        # Calculate bar positions for each scenario
        bar_width = 0.18
        x_base = np.arange(len(scenarios))

        all_bar_positions = []
        all_bar_labels = []
        all_bar_data = []

        for scenario_idx, scenario in enumerate(scenarios):
            if scenario == 'bau_2040':
                n_bars = 2
                policy_combos = policy_combos_bau
                x_offset = np.array([-0.5, 0.5]) * bar_width
            else:
                n_bars = 4
                policy_combos = policy_combos_full
                x_offset = np.array([-1.5, -0.5, 0.5, 1.5]) * bar_width

            for bar_idx, (scenario_suffix, constraint, label) in enumerate(policy_combos):
                scenario_name = f"{scenario}_{scenario_suffix}"
                x_pos = x_base[scenario_idx] + x_offset[bar_idx]

                bar_data = {}
                for mineral in minerals:
                    value = df_2040[
                        (df_2040['scenario'] == scenario_name) &
                        (df_2040['constraint'] == constraint) &
                        (df_2040['reference_mineral'] == mineral)
                    ]['water_usage_m3'].sum() / 1e6
                    bar_data[mineral] = value

                all_bar_positions.append(x_pos)
                all_bar_labels.append(label)
                all_bar_data.append(bar_data)

        # Plot all bars with stacked minerals
        for mineral_idx, mineral in enumerate(minerals):
            values = [bar_data.get(mineral, 0) for bar_data in all_bar_data]
            bottoms = np.zeros(len(all_bar_positions))

            for prev_mineral_idx in range(mineral_idx):
                prev_mineral = minerals[prev_mineral_idx]
                prev_values = [bar_data.get(prev_mineral, 0) for bar_data in all_bar_data]
                bottoms += prev_values

            ax.bar(all_bar_positions, values, bar_width, bottom=bottoms,
                   label=mineral.title() if mineral_idx < len(minerals) else "",
                   color=colors[mineral_idx], alpha=0.85,
                   edgecolor='white', linewidth=0.5)

        # Customize chart with larger fonts
        ax.set_ylabel('Water Usage (Million m³)', fontsize=13, fontweight='bold')
        ax.set_xlabel('Development Strategy', fontsize=13, fontweight='bold')
        ax.set_xticks(x_base)
        ax.set_xticklabels(scenario_labels, fontsize=12, fontweight='bold')

        # Add policy labels below
        minor_ticks = all_bar_positions
        minor_labels = all_bar_labels

        ax.set_xticks(minor_ticks, minor=True)
        ax.set_xticklabels(minor_labels, minor=True, fontsize=7, style='italic')
        ax.tick_params(axis='x', which='minor', length=0, pad=2)
        ax.tick_params(axis='both', which='major', labelsize=11)

        ax.grid(axis='y', alpha=0.3)
        ax.legend(title='Mineral', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11)

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'consolidated_water_usage.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Save to permanent location if specified
        if permanent_dir:
            save_chart_to_permanent_location(output_path, permanent_dir, iso3)

        return output_path

    except Exception as e:
        print(f"Error creating consolidated water chart: {e}")
        return None

def create_consolidated_emissions_chart(df_country, output_dir, iso3, permanent_dir=None):
    """Create a single consolidated chart showing CO2 emissions across scenarios with stacked bars by mineral"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from plot_utils import get_mineral_colors

        # Filter for 2040 scenarios
        df_2040 = df_country[df_country['scenario'].str.contains('2040')].copy()

        if df_2040.empty:
            return None

        scenarios = ['bau_2040', 'early_refining_2040', 'precursor_2040']
        scenario_labels = ['BAU', 'Early Refining', 'Precursor']

        # Calculate total CO2 (transport + energy)
        df_2040['total_co2_kt'] = (df_2040['transport_total_tonsCO2eq'] + df_2040['energy_tonsCO2eq']) / 1000

        # Filter out minerals with no CO2 emissions
        minerals_with_emissions = []
        for mineral in df_2040['reference_mineral'].unique():
            if df_2040[df_2040['reference_mineral'] == mineral]['total_co2_kt'].sum() > 0:
                minerals_with_emissions.append(mineral)

        minerals = sorted(minerals_with_emissions)

        if len(minerals) == 0:
            print(f"No minerals with CO2 emissions found for {iso3}")
            return None

        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(14, 9))
        fig.suptitle(f'CO₂ Emissions by Development Strategy\n{get_country_name(iso3)}',
                     fontsize=18, fontweight='bold')

        # For BAU: National = Regional, so only show constrained/unconstrained
        policy_combos_full = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Nat.\nConstr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Nat.\nUnconstr.'),
            ('mid_max_threshold_metal_tons', 'region_constrained', 'Reg.\nConstr.'),
            ('mid_max_threshold_metal_tons', 'region_unconstrained', 'Reg.\nUnconstr.')
        ]

        policy_combos_bau = [
            ('mid_min_threshold_metal_tons', 'country_constrained', 'Constr.'),
            ('mid_min_threshold_metal_tons', 'country_unconstrained', 'Unconstr.')
        ]

        # Get mineral colors
        mineral_colors = get_mineral_colors()
        colors = [mineral_colors.get(m, '#808080') for m in minerals]

        # Calculate bar positions for each scenario
        bar_width = 0.18
        x_base = np.arange(len(scenarios))

        all_bar_positions = []
        all_bar_labels = []
        all_bar_data = []

        for scenario_idx, scenario in enumerate(scenarios):
            if scenario == 'bau_2040':
                n_bars = 2
                policy_combos = policy_combos_bau
                x_offset = np.array([-0.5, 0.5]) * bar_width
            else:
                n_bars = 4
                policy_combos = policy_combos_full
                x_offset = np.array([-1.5, -0.5, 0.5, 1.5]) * bar_width

            for bar_idx, (scenario_suffix, constraint, label) in enumerate(policy_combos):
                scenario_name = f"{scenario}_{scenario_suffix}"
                x_pos = x_base[scenario_idx] + x_offset[bar_idx]

                bar_data = {}
                for mineral in minerals:
                    value = df_2040[
                        (df_2040['scenario'] == scenario_name) &
                        (df_2040['constraint'] == constraint) &
                        (df_2040['reference_mineral'] == mineral)
                    ]['total_co2_kt'].sum()
                    bar_data[mineral] = value

                all_bar_positions.append(x_pos)
                all_bar_labels.append(label)
                all_bar_data.append(bar_data)

        # Plot all bars with stacked minerals
        for mineral_idx, mineral in enumerate(minerals):
            values = [bar_data.get(mineral, 0) for bar_data in all_bar_data]
            bottoms = np.zeros(len(all_bar_positions))

            for prev_mineral_idx in range(mineral_idx):
                prev_mineral = minerals[prev_mineral_idx]
                prev_values = [bar_data.get(prev_mineral, 0) for bar_data in all_bar_data]
                bottoms += prev_values

            ax.bar(all_bar_positions, values, bar_width, bottom=bottoms,
                   label=mineral.title() if mineral_idx < len(minerals) else "",
                   color=colors[mineral_idx], alpha=0.85,
                   edgecolor='white', linewidth=0.5)

        # Customize chart with larger fonts
        ax.set_ylabel('CO₂ Emissions (kt CO₂eq)', fontsize=13, fontweight='bold')
        ax.set_xlabel('Development Strategy', fontsize=13, fontweight='bold')
        ax.set_xticks(x_base)
        ax.set_xticklabels(scenario_labels, fontsize=12, fontweight='bold')

        # Add policy labels below
        minor_ticks = all_bar_positions
        minor_labels = all_bar_labels

        ax.set_xticks(minor_ticks, minor=True)
        ax.set_xticklabels(minor_labels, minor=True, fontsize=7, style='italic')
        ax.tick_params(axis='x', which='minor', length=0, pad=2)
        ax.tick_params(axis='both', which='major', labelsize=11)

        ax.grid(axis='y', alpha=0.3)
        ax.legend(title='Mineral', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11)

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'consolidated_co2_emissions.png')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Save to permanent location if specified
        if permanent_dir:
            save_chart_to_permanent_location(output_path, permanent_dir, iso3)

        return output_path

    except Exception as e:
        print(f"Error creating consolidated emissions chart: {e}")
        return None


def adapt_country_single_axis_charts(df_country, iso3, temp_dir, permanent_dir=None):
    """
    Generate single-axis charts for a country and return paths

    Args:
        df_country: Filtered DataFrame for specific country
        iso3: Country ISO3 code
        temp_dir: Temporary directory for chart generation
        permanent_dir: Optional permanent directory for archiving

    Returns:
        dict: {'revenue_clean': path, 'revenue_comparison': path, ...}
    """
    try:
        from plot_country_single_axis import generate_country_single_axis_charts

        # Determine output directory
        if permanent_dir:
            single_axis_dir = os.path.join(permanent_dir, iso3, 'single_axis')
        else:
            single_axis_dir = os.path.join(temp_dir, 'single_axis')

        os.makedirs(single_axis_dir, exist_ok=True)

        # Generate charts
        chart_paths = generate_country_single_axis_charts(df_country, iso3, single_axis_dir)

        return chart_paths

    except Exception as e:
        print(f"Error creating single-axis charts for {iso3}: {e}")
        return {}