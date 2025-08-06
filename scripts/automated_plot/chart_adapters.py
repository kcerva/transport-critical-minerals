import os
import matplotlib.pyplot as plt
import pandas as pd
from plot_production_by_country_all_constraints import plot_production_by_country_all_constraints
from plot_gdp_share_by_country_all_constraints import plot_gdp_share_by_country_all_constraints
from plot_emissions_water_all_countries import plot_emissions_by_country_all_constraints, plot_water_by_country_all_constraints
from plot_goal_comparisons import plot_goal_comparisons_2040, plot_production_goal_comparison_by_processing_type

def adapt_production_charts(df_country, iso3, temp_dir):
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
        
        # Also create traditional charts as backup
        goal_by_scenario = {
            'bau_2040': 'Business as Usual',
            'early_refining_2040': 'Early Processing', 
            'precursor_2040': 'Product Manufacturing',
            '2022_baseline': 'Baseline'
        }
        traditional_paths = plot_production_by_country_all_constraints(df_country, country_output_dir, goal_by_scenario)
        if traditional_paths:
            saved_paths.extend(traditional_paths)
        
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
        
        return saved_paths
    except Exception as e:
        print(f"Error generating policy difference charts for {iso3}: {e}")
        return []

def adapt_goal_comparison_charts(df_country, iso3, temp_dir):
    """Adapter for goal comparison charts - comparing 2040 BAU vs Early Refining vs Precursor"""
    try:
        # Create country-specific output directory
        country_output_dir = os.path.join(temp_dir, f'goal_comparison_{iso3}')
        os.makedirs(country_output_dir, exist_ok=True)
        
        saved_paths = []
        
        # Create improved goal comparison charts with better titles and formatting
        improved_paths = create_improved_goal_comparison_charts(df_country, country_output_dir, iso3)
        saved_paths.extend(improved_paths)
        
        # Production goal comparison
        production_paths = plot_goal_comparisons_2040(
            df_country, 
            country_output_dir, 
            metric_column="production_tonnes",
            metric_title="Production",
            metric_units="kt",
            country_iso3=iso3
        )
        saved_paths.extend(production_paths)
        
        # Production by processing type goal comparison
        processing_paths = plot_production_goal_comparison_by_processing_type(
            df_country, 
            country_output_dir, 
            country_iso3=iso3
        )
        saved_paths.extend(processing_paths)
        
        # Revenue goal comparison
        revenue_paths = plot_goal_comparisons_2040(
            df_country,
            country_output_dir,
            metric_column="revenue_usd",
            metric_title="Revenue",
            metric_units="Million USD",
            country_iso3=iso3
        )
        saved_paths.extend(revenue_paths)
        
        # Water use goal comparison
        water_paths = plot_goal_comparisons_2040(
            df_country,
            country_output_dir,
            metric_column="water_usage_m3",
            metric_title="Water Usage",
            metric_units="Million m³",
            country_iso3=iso3
        )
        saved_paths.extend(water_paths)
        
        # CO2 emissions goal comparison (combined transport + energy)
        df_co2 = df_country.copy()
        df_co2["total_co2_tonnes"] = (df_co2["transport_total_tonsCO2eq"] + df_co2["energy_tonsCO2eq"]) / 1000
        co2_paths = plot_goal_comparisons_2040(
            df_co2,
            country_output_dir,
            metric_column="total_co2_tonnes",
            metric_title="Total CO2 Emissions", 
            metric_units="kt CO2",
            country_iso3=iso3
        )
        saved_paths.extend(co2_paths)
        
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
        
        scenario_titles = ['2040 Business as Usual', '2040 Early Processing', '2040 Product Manufacturing']
        
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
            scenario_labels = ['Business as Usual', 'Early Processing', 'Product\nManufacturing']
            
            for i, (scenario, label) in enumerate(zip(scenarios, scenario_labels)):
                scenario_data = df_2040[df_2040['scenario'].str.contains(scenario)]
                
                if scenario_data.empty:
                    axes[i].text(0.5, 0.5, 'No Data', ha='center', va='center', transform=axes[i].transAxes)
                    axes[i].set_title(label)
                    continue
                
                # Compare national vs regional for both constrained and unconstrained
                comparison_data = []
                
                # National approaches (country_constrained, country_unconstrained)
                national_constrained = scenario_data[scenario_data['constraint'] == 'country_constrained'][metric_col].sum() / divisor
                national_open = scenario_data[scenario_data['constraint'] == 'country_unconstrained'][metric_col].sum() / divisor
                
                # Regional approaches (region_constrained, region_unconstrained)
                regional_constrained = scenario_data[scenario_data['constraint'] == 'region_constrained'][metric_col].sum() / divisor
                regional_open = scenario_data[scenario_data['constraint'] == 'region_unconstrained'][metric_col].sum() / divisor
                
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
                scenario_labels = ['Business as Usual', 'Early Processing', 'Product Manufacturing']
                
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
        goal_titles = ['Business as Usual', 'Early Processing', 'Product Manufacturing']
        
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