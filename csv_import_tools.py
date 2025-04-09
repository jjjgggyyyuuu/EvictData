import os
import sys
import datetime
import pandas as pd
from pathlib import Path

def locate_csv_files():
    """Find all CSV files in Downloads directory and other common locations"""
    # List of directories to search for CSV files
    search_paths = [
        # User's Downloads folder
        str(Path.home() / "Downloads"),
        # Current directory and subdirectories
        os.path.join(os.getcwd(), "eviction_data"),
        os.path.join(os.getcwd(), "data"),
        os.getcwd()
    ]
    
    csv_files = []
    
    print("Searching for CSV files in common locations...")
    for path in search_paths:
        if os.path.exists(path):
            print(f"Checking directory: {path}")
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.csv'):
                        full_path = os.path.join(root, file)
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        
                        # Get file creation/modification time
                        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                        mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Try to peek at the first few rows
                        try:
                            df_peek = pd.read_csv(full_path, nrows=2)
                            columns = list(df_peek.columns)
                            num_columns = len(columns)
                            first_cols = ', '.join(columns[:3]) + ('...' if num_columns > 3 else '')
                        except Exception as e:
                            first_cols = f"Error peeking: {str(e)}"
                            num_columns = 0
                        
                        csv_files.append({
                            "path": full_path,
                            "filename": file,
                            "directory": root,
                            "size_mb": round(size_mb, 2),
                            "modified": mod_time_str,
                            "num_columns": num_columns,
                            "first_columns": first_cols
                        })
    
    return csv_files

def inspect_csv(filepath):
    """Inspect a CSV file and return information about its structure and contents"""
    try:
        # Read CSV file with pandas
        df = pd.read_csv(filepath)
        
        # Basic file info
        file_info = {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2),
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": list(df.columns)
        }
        
        # Check for eviction-related columns
        eviction_keywords = ['evict', 'tenant', 'landlord', 'filing', 'judgment', 'writ', 'rent', 'case']
        eviction_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in eviction_keywords)]
        
        # Date column detection
        date_columns = []
        for col in df.columns:
            try:
                # Try to convert to datetime
                pd.to_datetime(df[col], errors='raise')
                date_columns.append(col)
            except:
                pass
        
        # Sample data - first 5 rows
        sample_data = df.head(5).to_dict('records')
        
        # Check for missing values
        missing_values = df.isnull().sum().to_dict()
        
        # Check for potential address or location data
        location_keywords = ['address', 'street', 'city', 'state', 'zip', 'county', 'location']
        location_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in location_keywords)]
        
        # Check for monetary columns (rent, amounts)
        monetary_keywords = ['amount', 'rent', 'fee', 'cost', 'dollar', 'payment']
        monetary_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in monetary_keywords)]
        
        return {
            "file_info": file_info,
            "eviction_related": {
                "is_eviction_data": len(eviction_columns) > 0,
                "eviction_columns": eviction_columns
            },
            "date_columns": date_columns,
            "location_data": {
                "has_location_data": len(location_columns) > 0,
                "location_columns": location_columns
            },
            "monetary_data": {
                "has_monetary_data": len(monetary_columns) > 0,
                "monetary_columns": monetary_columns
            },
            "sample_data": sample_data,
            "missing_values": missing_values
        }
    except Exception as e:
        return {
            "error": str(e),
            "filepath": filepath,
            "filename": os.path.basename(filepath)
        }

def suggest_column_mapping(csv_info):
    """Suggest column mappings for the CSV file to import into our database schema"""
    mappings = {}
    
    # Case information mappings
    case_mapping_candidates = {
        'case_number': ['case', 'case_num', 'case_number', 'case_id', 'casenumber', 'caseid'],
        'county': ['county', 'county_name'],
        'state': ['state', 'state_name', 'state_code'],
        'filing_date': ['file_date', 'filing_date', 'filed_date', 'date_filed'],
        'judgment_date': ['judgment_date', 'judgement_date', 'date_of_judgment', 'judgment_dt'],
        'writ_date': ['writ_date', 'writ_of_possession_date', 'writ_issued_date'],
        'eviction_date': ['eviction_date', 'evicted_date', 'date_of_eviction', 'actual_eviction']
    }
    
    # Tenant information mappings
    tenant_mapping_candidates = {
        'tenant_id': ['tenant_id', 'tenant', 'defendant_id', 'defendant'],
        'zip_code': ['zip', 'zip_code', 'zipcode', 'postal_code', 'postal']
    }
    
    # Property information mappings
    property_mapping_candidates = {
        'property_type': ['property_type', 'prop_type', 'housing_type', 'type_of_property'],
        'monthly_rent': ['monthly_rent', 'rent', 'rent_amount', 'monthly_payment']
    }
    
    # Financial information mappings
    financial_mapping_candidates = {
        'amount_claimed': ['amount_claimed', 'claim_amount', 'amount', 'claimed_amount', 'total_claimed'],
        'judgment_amount': ['judgment_amount', 'judgement_amount', 'awarded_amount', 'judgment_sum']
    }
    
    # Flag mappings
    flag_mapping_candidates = {
        'has_legal_representation': ['has_attorney', 'attorney', 'legal_rep', 'represented', 'has_lawyer'],
        'has_rental_assistance': ['rental_assistance', 'assistance', 'aid', 'received_assistance'],
        'reason': ['reason', 'cause', 'eviction_reason', 'eviction_cause']
    }
    
    # Get columns from CSV info
    columns = csv_info['file_info']['columns']
    
    # Function to find best match for a field
    def find_best_match(field, candidates, columns):
        for col in columns:
            col_lower = col.lower()
            # Check for exact matches first
            if col_lower == field:
                return col
            
            # Then check for candidates
            for candidate in candidates:
                if candidate == col_lower or candidate in col_lower:
                    return col
        
        return None
    
    # Match case information
    for field, candidates in case_mapping_candidates.items():
        match = find_best_match(field, candidates, columns)
        if match:
            mappings[field] = match
    
    # Match tenant information
    for field, candidates in tenant_mapping_candidates.items():
        match = find_best_match(field, candidates, columns)
        if match:
            mappings[field] = match
    
    # Match property information
    for field, candidates in property_mapping_candidates.items():
        match = find_best_match(field, candidates, columns)
        if match:
            mappings[field] = match
    
    # Match financial information
    for field, candidates in financial_mapping_candidates.items():
        match = find_best_match(field, candidates, columns)
        if match:
            mappings[field] = match
    
    # Match flags
    for field, candidates in flag_mapping_candidates.items():
        match = find_best_match(field, candidates, columns)
        if match:
            mappings[field] = match
    
    # For date columns, prefer columns already identified as date columns
    date_columns = csv_info.get('date_columns', [])
    for field in ['filing_date', 'judgment_date', 'writ_date', 'eviction_date']:
        if field in mappings:
            # If the mapped column is not in date_columns, try to find a better match
            if mappings[field] not in date_columns:
                for date_col in date_columns:
                    date_col_lower = date_col.lower()
                    if any(candidate in date_col_lower for candidate in case_mapping_candidates[field]):
                        mappings[field] = date_col
                        break
    
    return mappings

def preview_import(filepath, column_mapping):
    """Preview the data import with the given column mapping"""
    try:
        df = pd.read_csv(filepath)
        
        # Create a preview dataframe with mapped columns
        preview_data = {}
        for target_field, source_column in column_mapping.items():
            if source_column in df.columns:
                preview_data[target_field] = df[source_column].head(5).tolist()
        
        # Calculate import statistics
        row_count = len(df)
        mapped_field_count = len(column_mapping)
        
        # Check for date columns and attempt to format them
        date_format_samples = {}
        for field in ['filing_date', 'judgment_date', 'writ_date', 'eviction_date']:
            if field in column_mapping and column_mapping[field] in df.columns:
                source_col = column_mapping[field]
                try:
                    # Try to convert to datetime
                    dates = pd.to_datetime(df[source_col])
                    # Format a sample
                    sample = dates.head(1).dt.strftime('%Y-%m-%d').iloc[0] if not dates.empty else None
                    date_format_samples[field] = sample
                except:
                    date_format_samples[field] = "Error: Could not parse as date"
        
        return {
            "preview_data": preview_data,
            "row_count": row_count,
            "mapped_field_count": mapped_field_count,
            "unmapped_fields": set(df.columns) - set(column_mapping.values()),
            "date_format_samples": date_format_samples
        }
    except Exception as e:
        return {
            "error": str(e),
            "filepath": filepath
        }

def prepare_import_config(filepath, column_mapping=None):
    """Prepare a configuration for importing a CSV file"""
    # If no column mapping provided, generate one
    if not column_mapping:
        csv_info = inspect_csv(filepath)
        column_mapping = suggest_column_mapping(csv_info)
    
    # Preview the import
    preview = preview_import(filepath, column_mapping)
    
    # Create an import configuration
    import_config = {
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "column_mapping": column_mapping,
        "date_formats": {
            "filing_date": "%Y-%m-%d",
            "judgment_date": "%Y-%m-%d",
            "writ_date": "%Y-%m-%d", 
            "eviction_date": "%Y-%m-%d"
        },
        "preview": preview,
        "created_at": datetime.datetime.now().isoformat(),
        "status": "pending"
    }
    
    return import_config

if __name__ == "__main__":
    # If run as a script, find and print CSV files
    csv_files = locate_csv_files()
    print(f"\nFound {len(csv_files)} CSV files:")
    for i, file_info in enumerate(csv_files):
        print(f"{i+1}. {file_info['filename']} ({file_info['size_mb']} MB) - {file_info['num_columns']} columns - {file_info['modified']}")
        print(f"   Path: {file_info['path']}")
        print(f"   Columns preview: {file_info['first_columns']}")
        print()
    
    # Allow user to select a file for inspection
    if csv_files:
        selection = input("Enter a number to inspect a CSV file (or 'q' to quit): ")
        if selection.lower() != 'q' and selection.isdigit() and 1 <= int(selection) <= len(csv_files):
            file_index = int(selection) - 1
            selected_file = csv_files[file_index]['path']
            
            print(f"\nInspecting {selected_file}...")
            csv_info = inspect_csv(selected_file)
            
            if 'error' in csv_info:
                print(f"Error inspecting file: {csv_info['error']}")
            else:
                print(f"\nFile Information:")
                print(f"Filename: {csv_info['file_info']['filename']}")
                print(f"Size: {csv_info['file_info']['size_mb']} MB")
                print(f"Rows: {csv_info['file_info']['num_rows']}")
                print(f"Columns: {csv_info['file_info']['num_columns']}")
                
                print("\nColumn List:")
                for col in csv_info['file_info']['columns']:
                    print(f"- {col}")
                
                if csv_info['eviction_related']['is_eviction_data']:
                    print("\nThis appears to be eviction-related data.")
                    print("Eviction-related columns: ", ', '.join(csv_info['eviction_related']['eviction_columns']))
                
                print("\nSuggested column mapping:")
                mapping = suggest_column_mapping(csv_info)
                for target, source in mapping.items():
                    print(f"{target} <- {source}")
                
                # Show import preview
                print("\nImport preview with suggested mapping:")
                preview = preview_import(selected_file, mapping)
                if 'error' in preview:
                    print(f"Error generating preview: {preview['error']}")
                else:
                    print(f"Will import {preview['row_count']} rows with {preview['mapped_field_count']} mapped fields.")
                    print("\nData sample:")
                    for field, values in preview['preview_data'].items():
                        print(f"{field}: {values}")
                
                # Ask if user wants to save the import configuration
                save_config = input("\nWould you like to save this import configuration? (y/n): ")
                if save_config.lower() == 'y':
                    config = prepare_import_config(selected_file, mapping)
                    
                    # Create directory if it doesn't exist
                    if not os.path.exists('eviction_data'):
                        os.makedirs('eviction_data')
                    
                    # Save configuration to a file
                    config_file = os.path.join('eviction_data', f"import_config_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                    with open(config_file, 'w') as f:
                        f.write(f"# Eviction Data Import Configuration\n")
                        f.write(f"File: {config['filename']}\n")
                        f.write(f"Path: {config['filepath']}\n\n")
                        
                        f.write("## Column Mapping\n")
                        for target, source in config['column_mapping'].items():
                            f.write(f"{target}: {source}\n")
                        
                        f.write("\n## Import Preview\n")
                        f.write(f"Rows to import: {config['preview']['row_count']}\n")
                        f.write(f"Mapped fields: {config['preview']['mapped_field_count']}\n\n")
                        
                        f.write("## Data Sample\n")
                        for field, values in config['preview']['preview_data'].items():
                            f.write(f"{field}: {values}\n")
                    
                    print(f"\nImport configuration saved to {config_file}")
                    print("You can now import this data using the eviction_data_manager.py script.") 