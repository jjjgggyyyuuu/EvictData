#!/usr/bin/env python3
import pandas as pd
import re
import datetime
from dateutil.parser import parse
import statistics
import numpy as np

def extract_date(text):
    """Extract date patterns from text."""
    # Common date formats: MM/DD/YYYY, M/D/YYYY, MM-DD-YYYY, etc.
    date_patterns = [
        r'\b(\d{1,2}[/\\-]\d{1,2}[/\\-]\d{2,4})\b',  # MM/DD/YYYY or M/D/YY
        r'\b(\d{1,2}[-/]\d{4})\b',  # MM/YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, str(text))
        if matches:
            for match in matches:
                try:
                    return parse(match, fuzzy=True).date()
                except:
                    continue
    return None

def main():
    print("Eviction Timeline Analysis")
    print("=========================")
    
    # Load the CSV file
    csv_path = r"C:\Users\Jorda\Downloads\SearchExport_Documents_638796844774398793.csv"
    print(f"Loading data from {csv_path}...")
    
    # Try reading the first few lines of the CSV file to see its structure
    try:
        with open(csv_path, 'r') as f:
            header = f.readline().strip()
            first_line = f.readline().strip()
            print(f"CSV header: {header}")
            print(f"First line: {first_line}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    # Load the CSV file with different approaches
    try:
        # Attempt 1: Regular pandas read_csv
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} records with standard read_csv.")
        
        # Print columns to verify
        print("\nColumns in DataFrame:", df.columns.tolist())
        
        # Print sample data rows
        print("\nSample data (first row):")
        first_row = df.iloc[0]
        for col, value in first_row.items():
            print(f"  {col}: {value}")
        
    except Exception as e:
        print(f"Error loading CSV with standard method: {e}")
        return
    
    # Let's identify the columns that contain actual dates
    print("\nChecking columns for date content...")
    
    date_columns = []
    for col in df.columns:
        # Get sample of values from the column
        sample_values = df[col].dropna().head(10).astype(str)
        
        # Check if column values match date patterns
        date_pattern = r'^\d{1,2}/\d{1,2}/\d{4}$'  # MM/DD/YYYY
        matches = [bool(re.match(date_pattern, val)) for val in sample_values]
        match_ratio = sum(matches) / len(matches) if matches else 0
        
        if match_ratio > 0.5:  # If more than 50% of samples look like dates
            date_columns.append(col)
            print(f"  Column '{col}' appears to contain dates (match ratio: {match_ratio:.1f})")
    
    # Try to identify key columns
    case_number_col = None
    filing_code_col = None
    
    # Look for column with "WRIT OF POSSESSION" pattern
    for col in df.columns:
        sample_values = df[col].dropna().astype(str).head(10)
        if any("WRIT OF POSSESSION" in val for val in sample_values):
            filing_code_col = col
            print(f"  Found filing code column: {col}")
            break
    
    # Look for column with case number pattern (e.g., "20ED123456")
    for col in df.columns:
        sample_values = df[col].dropna().astype(str).head(10)
        if any(re.match(r'\d{2}ED\d{6}', val) for val in sample_values):
            case_number_col = col
            print(f"  Found case number column: {col}")
            break
    
    # If we found a date column and filing code column, we can proceed with the analysis
    if date_columns:
        file_date_col = date_columns[0]
        print(f"\nUsing '{file_date_col}' as the file date column")
        
        # Convert file dates to datetime
        df['FileDate'] = pd.to_datetime(df[file_date_col], errors='coerce')
        valid_dates = df['FileDate'].notna()
        print(f"Successfully converted {valid_dates.sum()} file dates to datetime format")
        
        # Find records with "EJECTED" in the filing code
        if filing_code_col:
            ejection_records = df[df[filing_code_col].str.contains("EJECTED", na=False)]
            print(f"Found {len(ejection_records)} records with EJECTED in filing code")
        else:
            # If we couldn't find a filing code column, try all columns
            ejection_mask = np.zeros(len(df), dtype=bool)
            for col in df.columns:
                if df[col].dtype == object:  # Only check string columns
                    ejection_mask |= df[col].astype(str).str.contains("EJECTED", na=False)
            ejection_records = df[ejection_mask]
            print(f"Found {len(ejection_records)} records containing 'EJECTED' in any column")
        
        # Look for content text column (contains form text like "Vacated Settled Ejected")
        content_col = None
        for col in df.columns:
            if df[col].dtype == object:  # Only check string columns
                sample = df[col].dropna().astype(str).head(10)
                if any(("Vacated" in val and "Settled" in val and "Ejected" in val) for val in sample):
                    content_col = col
                    print(f"Found content text column: {col}")
                    break
        
        if not content_col:
            print("Could not identify content text column, using all text columns for date extraction")
        
        # Analyze time from filing to ejection by examining dates
        print("\nAnalyzing time from filing to ejection...")
        
        # Extract ejection dates from content text or other suitable columns
        ejection_dates = []
        delays = []
        
        for idx, row in ejection_records.iterrows():
            filing_date = row['FileDate']
            
            if pd.isna(filing_date):
                continue
                
            # Find all text columns to search for ejection date
            text_columns = [col for col in df.columns if df[col].dtype == object] if not content_col else [content_col]
            
            # Search for dates in content fields
            ejection_date = None
            
            for col in text_columns:
                text = str(row[col])
                date_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                
                for date_str in date_matches:
                    try:
                        date = datetime.datetime.strptime(date_str, '%m/%d/%Y').date()
                        
                        # Skip if this is the filing date or earlier
                        if date <= filing_date.date():
                            continue
                            
                        # Skip dates more than a year after filing (likely incorrect)
                        days_diff = (date - filing_date.date()).days
                        if days_diff > 365:
                            continue
                            
                        # Found a potential ejection date
                        ejection_date = date
                        break
                    except Exception:
                        continue
                
                if ejection_date:
                    break
            
            # If we found a valid ejection date, add it to our results
            if ejection_date:
                delay = (ejection_date - filing_date.date()).days
                delays.append(delay)
                
                ejection_dates.append({
                    'Filing Date': filing_date.date(),
                    'Ejection Date': ejection_date,
                    'Delay (days)': delay,
                    'Case Number': row.get(case_number_col, 'Unknown') if case_number_col else 'Unknown'
                })
        
        print(f"Found {len(delays)} records with identifiable ejection dates")
        
        if delays:
            # Calculate statistics
            average_delay = sum(delays) / len(delays)
            median_delay = statistics.median(delays)
            min_delay = min(delays)
            max_delay = max(delays)
            
            print("\nEviction Timeline Analysis Results:")
            print("------------------------------------")
            print(f"Average time from filing to ejection: {average_delay:.1f} days")
            print(f"Median time from filing to ejection: {median_delay:.1f} days")
            print(f"Range: {min_delay} to {max_delay} days")
            
            # Distribution of delays
            print("\nDistribution of delays:")
            delay_brackets = [
                (0, 30, "0-30 days (very fast)"),
                (31, 60, "31-60 days (fast)"),
                (61, 90, "61-90 days (moderate)"),
                (91, 180, "91-180 days (slow)"),
                (181, 365, "181-365 days (very slow)")
            ]
            
            for start, end, label in delay_brackets:
                count = sum(1 for d in delays if start <= d <= end)
                percentage = (count / len(delays)) * 100
                print(f"{label}: {count} cases ({percentage:.1f}%)")
            
            # Example cases
            print("\nExample cases:")
            for case in sorted(ejection_dates, key=lambda x: x['Delay (days)'])[:3]:
                print(f"Fast case: {case['Case Number']}: {case['Filing Date']} to {case['Ejection Date']} = {case['Delay (days)']} days")
                
            for case in sorted(ejection_dates, key=lambda x: x['Delay (days)'], reverse=True)[:3]:
                print(f"Slow case: {case['Case Number']}: {case['Filing Date']} to {case['Ejection Date']} = {case['Delay (days)']} days")
        else:
            print("\nCould not find enough data to calculate ejection timeline")
    else:
        print("\nCould not identify any date columns in the data")
    
    print("\nAnalysis complete")

if __name__ == "__main__":
    main() 