#!/usr/bin/env python3
"""
Test script for DOCX generation functionality
"""
import os
import sys
import pandas as pd
import json

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plot'))

def test_docx_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    try:
        from generate_country_docx import generate_country_docx, get_country_name
        from docx_utils import create_country_document
        from chart_adapters import adapt_production_charts
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_data_loading():
    """Test data loading and basic operations"""
    print("\nTesting data loading...")
    try:
        # Load configuration
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, "config.json")
        
        if not os.path.exists(config_path):
            print(f"✗ Config file not found: {config_path}")
            return False
            
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Check data file
        all_data_file = os.path.join(config['paths']['results'], "all_data.xlsx")
        if not os.path.exists(all_data_file):
            print(f"✗ Data file not found: {all_data_file}")
            print("  Please run the data processing pipeline first")
            return False
        
        df = pd.read_excel(all_data_file)
        print(f"✓ Data loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        
        # Check for required columns
        required_cols = ['iso3', 'constraint', 'scenario', 'processing_stage', 'production_tonnes']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"✗ Missing required columns: {missing_cols}")
            return False
        
        print(f"✓ All required columns present")
        
        # Check countries
        countries = df['iso3'].dropna().unique()
        print(f"✓ Found {len(countries)} countries: {', '.join(sorted(countries))}")
        
        return True, df, config
    except Exception as e:
        print(f"✗ Data loading error: {e}")
        return False, None, None

def test_single_country_generation(df, config, test_country='ZMB'):
    """Test generating DOCX for a single country"""
    print(f"\nTesting DOCX generation for {test_country}...")
    
    try:
        from generate_country_docx import generate_country_docx, get_country_name
        
        # Filter data for test country
        df_country = df[df['iso3'] == test_country].copy()
        
        if df_country.empty:
            print(f"✗ No data found for country: {test_country}")
            return False
        
        print(f"✓ Country data: {len(df_country)} rows")
        
        # Set output directory
        docx_output_dir = os.path.join(config['paths']['results'], 'country_reports', 'test')
        os.makedirs(docx_output_dir, exist_ok=True)
        
        # Generate DOCX
        docx_path = generate_country_docx(df_country, test_country, docx_output_dir)
        
        if os.path.exists(docx_path):
            file_size = os.path.getsize(docx_path)
            print(f"✓ DOCX generated successfully: {docx_path}")
            print(f"  File size: {file_size:,} bytes")
            return True
        else:
            print(f"✗ DOCX file not created: {docx_path}")
            return False
            
    except Exception as e:
        print(f"✗ DOCX generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("DOCX Generation Test Suite")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_docx_imports():
        return False
    
    # Test 2: Data loading  
    data_result = test_data_loading()
    if isinstance(data_result, tuple):
        success, df, config = data_result
        if not success:
            return False
    else:
        return False
    
    # Test 3: Single country generation
    if not test_single_country_generation(df, config):
        return False
    
    print(f"\n{'='*50}")
    print("✓ All tests passed successfully!")
    print("\nNext steps:")
    print("1. Run: python generate_country_docx.py")
    print("2. Or run: python run_all_figures.py --plots country_docx_reports")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)