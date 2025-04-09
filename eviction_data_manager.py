import os
import csv
import pandas as pd
import sqlite3
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
from models import db

# Define models for eviction data
class EvictionRecord(db.Model):
    __tablename__ = 'eviction_records'
    
    id = db.Column(db.Integer, primary_key=True)
    # Case information
    case_number = db.Column(db.String(50), index=True)
    county = db.Column(db.String(50), index=True)
    state = db.Column(db.String(2), index=True)
    filing_date = db.Column(db.Date, index=True)
    judgment_date = db.Column(db.Date, nullable=True, index=True)
    writ_date = db.Column(db.Date, nullable=True, index=True)
    eviction_date = db.Column(db.Date, nullable=True, index=True)
    
    # Tenant information (anonymized)
    tenant_id = db.Column(db.String(50), index=True)  # Hashed ID for anonymization
    zip_code = db.Column(db.String(10), index=True)
    
    # Property information
    property_type = db.Column(db.String(50), nullable=True)
    monthly_rent = db.Column(db.Float, nullable=True)
    
    # Financial information
    amount_claimed = db.Column(db.Float, nullable=True)
    judgment_amount = db.Column(db.Float, nullable=True)
    
    # Process information
    days_filing_to_judgment = db.Column(db.Integer, nullable=True)
    days_judgment_to_writ = db.Column(db.Integer, nullable=True)
    days_writ_to_eviction = db.Column(db.Integer, nullable=True)
    total_process_days = db.Column(db.Integer, nullable=True)
    
    # Analysis flags
    has_legal_representation = db.Column(db.Boolean, default=False)
    has_rental_assistance = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(100), nullable=True)
    
    # Import metadata
    import_date = db.Column(db.Date, default=datetime.date.today)
    data_source = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<EvictionRecord {self.case_number}>"

class CountyTimeline(db.Model):
    __tablename__ = 'county_timelines'
    
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(2), index=True)
    county = db.Column(db.String(50), index=True)
    avg_filing_to_judgment = db.Column(db.Float)
    avg_judgment_to_writ = db.Column(db.Float)
    avg_writ_to_eviction = db.Column(db.Float)
    avg_total_process = db.Column(db.Float)
    sample_size = db.Column(db.Integer)
    last_updated = db.Column(db.Date, default=datetime.date.today)
    
    def __repr__(self):
        return f"<CountyTimeline {self.state}-{self.county}>"

class EvictionReport(db.Model):
    __tablename__ = 'eviction_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, default=datetime.date.today)
    report_type = db.Column(db.String(50))
    state = db.Column(db.String(2), nullable=True)
    county = db.Column(db.String(50), nullable=True)
    date_range_start = db.Column(db.Date, nullable=True)
    date_range_end = db.Column(db.Date, nullable=True)
    total_records = db.Column(db.Integer)
    report_content = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<EvictionReport {self.report_type} {self.report_date}>"

def init_db(app):
    """Initialize the database within the application context"""
    with app.app_context():
        db.create_all()
        print("Eviction data tables created")

def import_csv(filepath, app):
    """Import eviction data from a CSV file into the database"""
    try:
        # Read CSV file with pandas for better handling
        df = pd.read_csv(filepath)
        print(f"Found {len(df)} records in {filepath}")
        
        # Clean column names (lowercase, replace spaces with underscores)
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Convert date columns to datetime if they exist
        date_columns = ['filing_date', 'judgment_date', 'writ_date', 'eviction_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Calculate timeline metrics if dates exist
        if 'filing_date' in df.columns and 'judgment_date' in df.columns:
            df['days_filing_to_judgment'] = (df['judgment_date'] - df['filing_date']).dt.days
        
        if 'judgment_date' in df.columns and 'writ_date' in df.columns:
            df['days_judgment_to_writ'] = (df['writ_date'] - df['judgment_date']).dt.days
            
        if 'writ_date' in df.columns and 'eviction_date' in df.columns:
            df['days_writ_to_eviction'] = (df['eviction_date'] - df['writ_date']).dt.days
            
        if 'filing_date' in df.columns and 'eviction_date' in df.columns:
            df['total_process_days'] = (df['eviction_date'] - df['filing_date']).dt.days
        
        # Create records in database
        records = []
        for _, row in df.iterrows():
            record = EvictionRecord(
                case_number=row.get('case_number', f"CASE-{len(records)+1}"),
                county=row.get('county', 'Unknown'),
                state=row.get('state', 'GA'),  # Default to GA if not specified
                filing_date=row.get('filing_date'),
                judgment_date=row.get('judgment_date'),
                writ_date=row.get('writ_date'),
                eviction_date=row.get('eviction_date'),
                tenant_id=row.get('tenant_id', f"TENANT-{len(records)+1}"),
                zip_code=row.get('zip_code', ''),
                property_type=row.get('property_type'),
                monthly_rent=row.get('monthly_rent'),
                amount_claimed=row.get('amount_claimed'),
                judgment_amount=row.get('judgment_amount'),
                days_filing_to_judgment=row.get('days_filing_to_judgment'),
                days_judgment_to_writ=row.get('days_judgment_to_writ'),
                days_writ_to_eviction=row.get('days_writ_to_eviction'),
                total_process_days=row.get('total_process_days'),
                has_legal_representation=row.get('has_legal_representation', False),
                has_rental_assistance=row.get('has_rental_assistance', False),
                reason=row.get('reason'),
                data_source=os.path.basename(filepath)
            )
            records.append(record)
        
        # Add all records to the database
        with app.app_context():
            db.session.bulk_save_objects(records)
            db.session.commit()
        
        print(f"Successfully imported {len(records)} records into database")
        
        # Generate report and timelines
        generate_county_timelines(app)
        generate_import_report(filepath, len(records), app)
        
        return len(records)
    except Exception as e:
        print(f"Error importing CSV: {str(e)}")
        return 0

def generate_county_timelines(app):
    """Generate timeline averages for each county"""
    with app.app_context():
        # Get all counties with data
        counties = db.session.query(EvictionRecord.state, EvictionRecord.county).distinct().all()
        
        for state, county in counties:
            # Get average timelines for this county
            query = db.session.query(
                db.func.avg(EvictionRecord.days_filing_to_judgment).label('avg_filing_to_judgment'),
                db.func.avg(EvictionRecord.days_judgment_to_writ).label('avg_judgment_to_writ'),
                db.func.avg(EvictionRecord.days_writ_to_eviction).label('avg_writ_to_eviction'),
                db.func.avg(EvictionRecord.total_process_days).label('avg_total_process'),
                db.func.count(EvictionRecord.id).label('sample_size')
            ).filter(
                EvictionRecord.state == state,
                EvictionRecord.county == county
            ).first()
            
            # Check if county timeline already exists
            existing = CountyTimeline.query.filter_by(state=state, county=county).first()
            
            if existing:
                # Update existing record
                existing.avg_filing_to_judgment = query.avg_filing_to_judgment or existing.avg_filing_to_judgment
                existing.avg_judgment_to_writ = query.avg_judgment_to_writ or existing.avg_judgment_to_writ
                existing.avg_writ_to_eviction = query.avg_writ_to_eviction or existing.avg_writ_to_eviction
                existing.avg_total_process = query.avg_total_process or existing.avg_total_process
                existing.sample_size = query.sample_size
                existing.last_updated = datetime.date.today()
            else:
                # Create new county timeline
                timeline = CountyTimeline(
                    state=state,
                    county=county,
                    avg_filing_to_judgment=query.avg_filing_to_judgment,
                    avg_judgment_to_writ=query.avg_judgment_to_writ,
                    avg_writ_to_eviction=query.avg_writ_to_eviction,
                    avg_total_process=query.avg_total_process,
                    sample_size=query.sample_size
                )
                db.session.add(timeline)
            
        db.session.commit()

def generate_import_report(filepath, record_count, app):
    """Generate a report summarizing the imported data"""
    filename = os.path.basename(filepath)
    
    with app.app_context():
        # Get summary statistics from the imported data
        county_stats = db.session.query(
            EvictionRecord.county,
            db.func.count(EvictionRecord.id).label('count')
        ).filter(
            EvictionRecord.data_source == filename
        ).group_by(
            EvictionRecord.county
        ).all()
        
        timeline_stats = db.session.query(
            db.func.avg(EvictionRecord.days_filing_to_judgment).label('avg_filing_to_judgment'),
            db.func.avg(EvictionRecord.days_judgment_to_writ).label('avg_judgment_to_writ'),
            db.func.avg(EvictionRecord.days_writ_to_eviction).label('avg_writ_to_eviction'),
            db.func.avg(EvictionRecord.total_process_days).label('avg_total_process')
        ).filter(
            EvictionRecord.data_source == filename
        ).first()
        
        # Create a report dictionary with the statistics
        report_data = {
            "import_date": datetime.date.today().isoformat(),
            "source_file": filename,
            "record_count": record_count,
            "county_breakdown": dict(county_stats),
            "timeline_statistics": {
                "avg_filing_to_judgment": timeline_stats.avg_filing_to_judgment,
                "avg_judgment_to_writ": timeline_stats.avg_judgment_to_writ,
                "avg_writ_to_eviction": timeline_stats.avg_writ_to_eviction,
                "avg_total_process": timeline_stats.avg_total_process
            }
        }
        
        # Create a report record
        report = EvictionReport(
            report_type="import_summary",
            total_records=record_count,
            report_content=json.dumps(report_data, default=str),
            filename=filename
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Also create a markdown report file
        report_file = f"eviction_import_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(os.path.join("eviction_data", report_file), 'w') as f:
            f.write(f"# Eviction Data Import Report\n")
            f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data source: {filename}\n")
            f.write(f"Total records imported: {record_count}\n\n")
            
            f.write("## County Breakdown\n")
            for county, count in county_stats:
                f.write(f"- {county}: {count} records\n")
            
            f.write("\n## Timeline Statistics\n")
            f.write(f"- Average days from filing to judgment: {timeline_stats.avg_filing_to_judgment:.1f}\n")
            f.write(f"- Average days from judgment to writ: {timeline_stats.avg_judgment_to_writ:.1f}\n")
            f.write(f"- Average days from writ to eviction: {timeline_stats.avg_writ_to_eviction:.1f}\n")
            f.write(f"- Average total process days: {timeline_stats.avg_total_process:.1f}\n")

def get_eviction_predictions(state, county, app):
    """Generate eviction timeline predictions for a specific county"""
    with app.app_context():
        # Get county timeline data
        timeline = CountyTimeline.query.filter_by(state=state, county=county).first()
        
        if not timeline:
            # Fall back to state average
            state_avg = db.session.query(
                db.func.avg(CountyTimeline.avg_filing_to_judgment).label('avg_filing_to_judgment'),
                db.func.avg(CountyTimeline.avg_judgment_to_writ).label('avg_judgment_to_writ'),
                db.func.avg(CountyTimeline.avg_writ_to_eviction).label('avg_writ_to_eviction'),
                db.func.avg(CountyTimeline.avg_total_process).label('avg_total_process')
            ).filter(
                CountyTimeline.state == state
            ).first()
            
            if state_avg.avg_filing_to_judgment:
                return {
                    "state": state,
                    "county": county,
                    "status": "using_state_average",
                    "filing_to_judgment": round(state_avg.avg_filing_to_judgment),
                    "judgment_to_writ": round(state_avg.avg_judgment_to_writ),
                    "writ_to_eviction": round(state_avg.avg_writ_to_eviction),
                    "total_process": round(state_avg.avg_total_process)
                }
            else:
                # Fall back to global average
                global_avg = db.session.query(
                    db.func.avg(CountyTimeline.avg_filing_to_judgment).label('avg_filing_to_judgment'),
                    db.func.avg(CountyTimeline.avg_judgment_to_writ).label('avg_judgment_to_writ'),
                    db.func.avg(CountyTimeline.avg_writ_to_eviction).label('avg_writ_to_eviction'),
                    db.func.avg(CountyTimeline.avg_total_process).label('avg_total_process')
                ).first()
                
                return {
                    "state": state,
                    "county": county,
                    "status": "using_global_average",
                    "filing_to_judgment": round(global_avg.avg_filing_to_judgment or 30),
                    "judgment_to_writ": round(global_avg.avg_judgment_to_writ or 15),
                    "writ_to_eviction": round(global_avg.avg_writ_to_eviction or 30),
                    "total_process": round(global_avg.avg_total_process or 75)
                }
        else:
            return {
                "state": state,
                "county": county,
                "status": "using_county_data",
                "filing_to_judgment": round(timeline.avg_filing_to_judgment or 30),
                "judgment_to_writ": round(timeline.avg_judgment_to_writ or 15),
                "writ_to_eviction": round(timeline.avg_writ_to_eviction or 30),
                "total_process": round(timeline.avg_total_process or 75),
                "sample_size": timeline.sample_size,
                "last_updated": timeline.last_updated.isoformat()
            }

def search_eviction_data(state=None, county=None, zip_code=None, date_from=None, date_to=None, limit=100, app=None):
    """Search for eviction records with filters"""
    with app.app_context():
        query = db.session.query(EvictionRecord)
        
        # Apply filters
        if state:
            query = query.filter(EvictionRecord.state == state)
        if county:
            query = query.filter(EvictionRecord.county == county)
        if zip_code:
            query = query.filter(EvictionRecord.zip_code == zip_code)
        if date_from:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(EvictionRecord.filing_date >= date_from)
        if date_to:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(EvictionRecord.filing_date <= date_to)
        
        # Execute query with limit
        records = query.order_by(EvictionRecord.filing_date.desc()).limit(limit).all()
        
        # Convert to JSON-friendly format
        results = []
        for record in records:
            results.append({
                "case_number": record.case_number,
                "county": record.county,
                "state": record.state,
                "filing_date": record.filing_date.isoformat() if record.filing_date else None,
                "judgment_date": record.judgment_date.isoformat() if record.judgment_date else None,
                "writ_date": record.writ_date.isoformat() if record.writ_date else None,
                "eviction_date": record.eviction_date.isoformat() if record.eviction_date else None,
                "zip_code": record.zip_code,
                "days_filing_to_judgment": record.days_filing_to_judgment,
                "days_judgment_to_writ": record.days_judgment_to_writ,
                "days_writ_to_eviction": record.days_writ_to_eviction,
                "total_process_days": record.total_process_days
            })
        
        return {
            "count": len(results),
            "records": results
        }

def get_county_list(app):
    """Get a list of all counties with eviction data"""
    with app.app_context():
        counties = db.session.query(
            EvictionRecord.state, 
            EvictionRecord.county,
            db.func.count(EvictionRecord.id).label('record_count')
        ).group_by(
            EvictionRecord.state, 
            EvictionRecord.county
        ).order_by(
            EvictionRecord.state,
            EvictionRecord.county
        ).all()
        
        result = []
        for state, county, count in counties:
            result.append({
                "state": state,
                "county": county,
                "record_count": count,
                "value": f"{county.lower()}-{state.lower()}"  # Value for use in UI
            })
        
        return result

def find_csv_files():
    """Find all CSV files in the specified directories"""
    search_paths = [
        os.path.expanduser("~/Downloads"),
        "./eviction_data",
        "./data"
    ]
    
    csv_files = []
    for path in search_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.lower().endswith('.csv'):
                    csv_files.append(os.path.join(path, file))
    
    return csv_files

def update_timelines_in_app(app):
    """Update the TIMELINES dictionary in the app with data from the database"""
    with app.app_context():
        # Get all county timelines
        timelines = CountyTimeline.query.all()
        
        # Create the timeline structure
        timeline_dict = {}
        
        for timeline in timelines:
            # Ensure state exists in dictionary
            if timeline.state not in timeline_dict:
                timeline_dict[timeline.state] = {}
            
            # Add county data
            county_key = f"{timeline.county.lower()}-{timeline.state.lower()}"
            timeline_dict[timeline.state][county_key] = {
                "filing_to_judgment": round(timeline.avg_filing_to_judgment or 30),
                "judgment_to_eviction": round((timeline.avg_judgment_to_writ or 15) + (timeline.avg_writ_to_eviction or 30)),
                "writ_to_eviction": round(timeline.avg_writ_to_eviction or 30)
            }
            
            # Ensure default exists for each state
            if "default" not in timeline_dict[timeline.state]:
                # Compute state averages
                state_avg = db.session.query(
                    db.func.avg(CountyTimeline.avg_filing_to_judgment).label('avg_filing_to_judgment'),
                    db.func.avg(CountyTimeline.avg_judgment_to_writ).label('avg_judgment_to_writ'),
                    db.func.avg(CountyTimeline.avg_writ_to_eviction).label('avg_writ_to_eviction')
                ).filter(
                    CountyTimeline.state == timeline.state
                ).first()
                
                timeline_dict[timeline.state]["default"] = {
                    "filing_to_judgment": round(state_avg.avg_filing_to_judgment or 30),
                    "judgment_to_eviction": round((state_avg.avg_judgment_to_writ or 15) + (state_avg.avg_writ_to_eviction or 30)),
                    "writ_to_eviction": round(state_avg.avg_writ_to_eviction or 30)
                }
        
        # Ensure global default exists
        if "default" not in timeline_dict:
            # Compute global averages
            global_avg = db.session.query(
                db.func.avg(CountyTimeline.avg_filing_to_judgment).label('avg_filing_to_judgment'),
                db.func.avg(CountyTimeline.avg_judgment_to_writ).label('avg_judgment_to_writ'),
                db.func.avg(CountyTimeline.avg_writ_to_eviction).label('avg_writ_to_eviction')
            ).first()
            
            timeline_dict["default"] = {
                "filing_to_judgment": round(global_avg.avg_filing_to_judgment or 30),
                "judgment_to_eviction": round((global_avg.avg_judgment_to_writ or 15) + (global_avg.avg_writ_to_eviction or 30)),
                "writ_to_eviction": round(global_avg.avg_writ_to_eviction or 30)
            }
        
        # Update the app's TIMELINES dictionary
        app.config['TIMELINES'] = timeline_dict
        
        return timeline_dict 