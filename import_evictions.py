import pandas as pd
from datetime import datetime
from eviction_data_manager import db, EvictionRecord
from flask import Flask
import os

def parse_case_description(desc):
    """Extract plaintiff and defendant from case description"""
    parts = desc.split(" vs. ")
    if len(parts) == 2:
        plaintiff = parts[0].strip()
        defendants = parts[1].split(",")
        primary_defendant = defendants[0].strip()
        return plaintiff, primary_defendant
    return desc, ""

def import_eviction_data(csv_path):
    """Import eviction data from CSV file"""
    print(f"Importing data from {csv_path}")
    
    # Read CSV file
    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} records")
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eviction_calculator.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Process each row
        records_added = 0
        for _, row in df.iterrows():
            try:
                # Parse case description
                plaintiff, defendant = parse_case_description(row['Case Description'])
                
                # Extract county from location
                county = row['Case Location'].split(' - ')[0] if ' - ' in row['Case Location'] else row['Case Location']
                
                # Parse filing date
                filing_date = datetime.strptime(row['Case Filed Date'], '%m/%d/%Y').date()
                
                # Create record
                record = EvictionRecord(
                    case_number=row['Case Number'],
                    county=county,
                    state='GA',  # Hardcoded for now since all cases are from Georgia
                    filing_date=filing_date,
                    tenant_id=defendant,  # Using defendant name as tenant ID
                    property_type='Residential',  # Default assumption for dispossessory cases
                    days_filing_to_judgment=None,  # Will be updated when judgment data is available
                    has_legal_representation=pd.notna(row['Attorneys']),
                    reason=row['Case Type '].strip(),
                    data_source=os.path.basename(csv_path)
                )
                
                db.session.add(record)
                records_added += 1
                
                # Commit in batches of 100
                if records_added % 100 == 0:
                    db.session.commit()
                    print(f"Imported {records_added} records...")
            
            except Exception as e:
                print(f"Error processing record: {str(e)}")
                continue
        
        # Final commit for remaining records
        db.session.commit()
        print(f"\nImport completed. Added {records_added} records to database.")

if __name__ == '__main__':
    csv_path = r'C:\Users\Jorda\Downloads\SearchExport_Cases_638797223707338702.csv'
    import_eviction_data(csv_path) 