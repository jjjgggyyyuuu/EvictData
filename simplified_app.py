from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from datetime import datetime, timedelta
import uuid
import os
import json
import pandas as pd
from csv_import_tools import locate_csv_files, inspect_csv, suggest_column_mapping, preview_import, prepare_import_config

# Create necessary directories
os.makedirs('templates', exist_ok=True)
os.makedirs('reports', exist_ok=True)
os.makedirs('eviction_data', exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-development'

# Make enumerate available in templates
app.jinja_env.globals.update(enumerate=enumerate)

# Make split available as a filter in templates
app.jinja_env.filters['split'] = lambda value, delimiter: value.split(delimiter)

# Make common Python functions available in templates
app.jinja_env.globals.update(min=min)
app.jinja_env.globals.update(max=max)
app.jinja_env.globals.update(len=len)
app.jinja_env.globals.update(sum=sum)
app.jinja_env.globals.update(round=round)

# Define average timelines for eviction process (in days)
AVERAGE_TIMELINES = {
    'filing_to_service': 5,
    'service_to_court': 14,
    'court_to_judgment': 2,
    'judgment_to_writ': 7,
    'writ_to_eviction': 7
}

# Database of evictions (for demo purposes)
EVICTIONS_DB = []

# Load existing evictions if available
def load_evictions():
    global EVICTIONS_DB
    try:
        if os.path.exists('eviction_data/evictions.json'):
            with open('eviction_data/evictions.json', 'r') as f:
                EVICTIONS_DB = json.load(f)
    except Exception as e:
        print(f"Error loading evictions: {e}")
        EVICTIONS_DB = []

# Save evictions to file
def save_evictions():
    try:
        os.makedirs('eviction_data', exist_ok=True)
        with open('eviction_data/evictions.json', 'w') as f:
            json.dump(EVICTIONS_DB, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving evictions: {e}")

# Generate unique ID for evictions
def generate_id():
    return str(datetime.now().timestamp()).replace('.', '')

# Home route
@app.route('/')
def index():
    # Load some demo data for the dashboard
    load_evictions()
    active_evictions = len([e for e in EVICTIONS_DB if e.get('status') == 'active'])
    monthly_evictions = len([e for e in EVICTIONS_DB if e.get('filing_date', '').startswith(datetime.now().strftime('%Y-%m'))])
    pending_judgments = len([e for e in EVICTIONS_DB if e.get('status') == 'judgment'])
    
    recent_evictions = EVICTIONS_DB[:5] if EVICTIONS_DB else []
    
    return render_template('index.html', 
                          active_evictions=active_evictions,
                          monthly_evictions=monthly_evictions,
                          pending_judgments=pending_judgments,
                          recent_evictions=recent_evictions)

@app.route('/timeline_calculator')
def timeline_calculator():
    return render_template('timeline_calculator.html', AVERAGE_TIMELINES=AVERAGE_TIMELINES)

@app.route('/calculate', methods=['POST'])
def calculate():
    filing_date_str = request.form.get('filing_date')
    writ_date_str = request.form.get('writ_date')
    
    if not filing_date_str and not writ_date_str:
        return render_template('timeline_calculator.html', error="Please provide at least one date", AVERAGE_TIMELINES=AVERAGE_TIMELINES)
    
    result = {}
    
    # Convert string dates to datetime objects
    filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d') if filing_date_str else None
    writ_date = datetime.strptime(writ_date_str, '%Y-%m-%d') if writ_date_str else None
    
    # Calculate based on filing date
    if filing_date and not writ_date:
        service_date = filing_date + timedelta(days=AVERAGE_TIMELINES['filing_to_service'])
        court_date = service_date + timedelta(days=AVERAGE_TIMELINES['service_to_court'])
        judgment_date = court_date + timedelta(days=AVERAGE_TIMELINES['court_to_judgment'])
        writ_date = judgment_date + timedelta(days=AVERAGE_TIMELINES['judgment_to_writ'])
        eviction_date = writ_date + timedelta(days=AVERAGE_TIMELINES['writ_to_eviction'])
        
        days_to_eviction = (eviction_date - datetime.now()).days
        result = {
            'filing_date': filing_date.strftime('%Y-%m-%d'),
            'service_date': service_date.strftime('%Y-%m-%d'),
            'court_date': court_date.strftime('%Y-%m-%d'),
            'judgment_date': judgment_date.strftime('%Y-%m-%d'),
            'writ_date': writ_date.strftime('%Y-%m-%d'),
            'eviction_date': eviction_date.strftime('%Y-%m-%d'),
            'days_to_eviction': days_to_eviction
        }
    
    # Calculate based on writ date
    elif writ_date and not filing_date:
        eviction_date = writ_date + timedelta(days=AVERAGE_TIMELINES['writ_to_eviction'])
        judgment_date = writ_date - timedelta(days=AVERAGE_TIMELINES['judgment_to_writ'])
        court_date = judgment_date - timedelta(days=AVERAGE_TIMELINES['court_to_judgment'])
        service_date = court_date - timedelta(days=AVERAGE_TIMELINES['service_to_court'])
        filing_date = service_date - timedelta(days=AVERAGE_TIMELINES['filing_to_service'])
        
        days_to_eviction = (eviction_date - datetime.now()).days
        result = {
            'filing_date': filing_date.strftime('%Y-%m-%d'),
            'service_date': service_date.strftime('%Y-%m-%d'),
            'court_date': court_date.strftime('%Y-%m-%d'),
            'judgment_date': judgment_date.strftime('%Y-%m-%d'),
            'writ_date': writ_date.strftime('%Y-%m-%d'),
            'eviction_date': eviction_date.strftime('%Y-%m-%d'),
            'days_to_eviction': days_to_eviction
        }
    
    # Calculate based on both dates
    elif filing_date and writ_date:
        days_to_writ = (writ_date - filing_date).days
        eviction_date = writ_date + timedelta(days=AVERAGE_TIMELINES['writ_to_eviction'])
        judgment_date = writ_date - timedelta(days=AVERAGE_TIMELINES['judgment_to_writ'])
        
        days_to_eviction = (eviction_date - datetime.now()).days
        result = {
            'filing_date': filing_date.strftime('%Y-%m-%d'),
            'writ_date': writ_date.strftime('%Y-%m-%d'),
            'judgment_date': judgment_date.strftime('%Y-%m-%d'),
            'eviction_date': eviction_date.strftime('%Y-%m-%d'),
            'days_to_writ': days_to_writ,
            'days_to_eviction': days_to_eviction
        }
    
    return render_template('timeline_result.html', result=result)

# CSV Import Routes
@app.route('/import')
def import_page():
    csv_files = locate_csv_files()
    return render_template('import.html', csv_files=csv_files)

@app.route('/inspect_csv', methods=['POST'])
def inspect_csv_route():
    filepath = request.form.get('filepath')
    if not filepath:
        flash('No file selected', 'error')
        return redirect(url_for('import_page'))
    
    csv_info = inspect_csv(filepath)
    column_mapping = suggest_column_mapping(csv_info)
    session['filepath'] = filepath
    session['column_mapping'] = column_mapping
    
    return render_template('mapping.html', 
                          csv_info=csv_info, 
                          column_mapping=column_mapping,
                          filepath=filepath)

@app.route('/preview_import', methods=['POST'])
def preview_import_route():
    filepath = session.get('filepath')
    column_mapping = {}
    
    # Get user-defined column mappings from form
    for field in request.form:
        if field.startswith('mapping_'):
            db_field = field.replace('mapping_', '')
            csv_column = request.form.get(field)
            if csv_column and csv_column != 'none':
                column_mapping[db_field] = csv_column
    
    if not filepath or not column_mapping:
        flash('Missing file or column mapping', 'error')
        return redirect(url_for('import_page'))
    
    preview_data = preview_import(filepath, column_mapping)
    session['column_mapping'] = column_mapping
    
    return render_template('preview.html', 
                          preview=preview_data, 
                          column_mapping=column_mapping,
                          filepath=filepath)

@app.route('/process_import', methods=['POST'])
def process_import():
    filepath = session.get('filepath')
    column_mapping = session.get('column_mapping')
    
    if not filepath or not column_mapping:
        flash('Missing file or column mapping', 'error')
        return redirect(url_for('import_page'))
    
    try:
        # Read CSV with pandas
        df = pd.read_csv(filepath)
        
        # Process each row and add to database
        imported_count = 0
        load_evictions()  # Load existing evictions
        
        for _, row in df.iterrows():
            eviction = {
                'id': generate_id(),
                'import_date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'pending'
            }
            
            # Map CSV columns to database fields
            for db_field, csv_column in column_mapping.items():
                if csv_column in df.columns:
                    value = row[csv_column]
                    # Handle NaN values
                    if pd.isna(value):
                        value = None
                    # Handle date conversions
                    elif db_field in ['filing_date', 'service_date', 'court_date', 'judgment_date', 'writ_date', 'eviction_date']:
                        try:
                            # Try to parse the date - handle various formats
                            date_obj = pd.to_datetime(value)
                            value = date_obj.strftime('%Y-%m-%d')
                        except:
                            value = None
                    eviction[db_field] = value
            
            # Add to database
            EVICTIONS_DB.append(eviction)
            imported_count += 1
        
        # Save updated database
        save_evictions()
        
        # Generate import report
        os.makedirs('reports', exist_ok=True)
        report_name = f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join('reports', report_name)
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filepath': filepath,
            'records_imported': imported_count,
            'column_mapping': column_mapping
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        flash(f'Successfully imported {imported_count} eviction records', 'success')
        return redirect(url_for('evictions'))
        
    except Exception as e:
        flash(f'Error during import: {str(e)}', 'error')
        return redirect(url_for('import_page'))

# Eviction Management Routes
@app.route('/evictions')
def evictions():
    load_evictions()
    status_filter = request.args.get('status')
    
    filtered_evictions = EVICTIONS_DB
    if status_filter:
        filtered_evictions = [e for e in EVICTIONS_DB if e.get('status') == status_filter]
    
    return render_template('evictions.html', evictions=filtered_evictions)

@app.route('/eviction/<eviction_id>')
def view_eviction(eviction_id):
    load_evictions()
    eviction = next((e for e in EVICTIONS_DB if e.get('id') == eviction_id), None)
    
    if not eviction:
        flash('Eviction not found', 'error')
        return redirect(url_for('evictions'))
    
    return render_template('eviction_details.html', eviction=eviction)

@app.route('/eviction/<eviction_id>/update', methods=['POST'])
def update_eviction(eviction_id):
    load_evictions()
    
    # Find eviction by ID
    for i, eviction in enumerate(EVICTIONS_DB):
        if eviction.get('id') == eviction_id:
            # Update fields from form
            for field in request.form:
                EVICTIONS_DB[i][field] = request.form.get(field)
            
            # Handle status updates
            if request.form.get('status') != eviction.get('status'):
                EVICTIONS_DB[i]['status_updated'] = datetime.now().strftime('%Y-%m-%d')
            
            save_evictions()
            flash('Eviction updated successfully', 'success')
            break
    
    return redirect(url_for('view_eviction', eviction_id=eviction_id))

@app.route('/reports')
def reports():
    # List all reports in the reports directory
    report_files = []
    if os.path.exists('reports'):
        for filename in os.listdir('reports'):
            if filename.endswith('.json'):
                report_path = os.path.join('reports', filename)
                try:
                    with open(report_path, 'r') as f:
                        report = json.load(f)
                    
                    report_files.append({
                        'filename': filename,
                        'timestamp': report.get('timestamp', 'Unknown'),
                        'records': report.get('records_imported', 0) or report.get('count', 0)
                    })
                except:
                    pass
    
    return render_template('reports.html', reports=report_files)

@app.route('/report/<filename>')
def view_report(filename):
    report_path = os.path.join('reports', filename)
    
    if not os.path.exists(report_path):
        flash('Report not found', 'error')
        return redirect(url_for('reports'))
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    return render_template('report_details.html', report=report, filename=filename)

@app.route('/generate_eviction_report', methods=['POST'])
def generate_eviction_report():
    load_evictions()
    status_filter = request.form.get('status')
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    report_format = request.form.get('format', 'json')
    
    # Filter evictions
    filtered_evictions = EVICTIONS_DB
    
    if status_filter:
        filtered_evictions = [e for e in filtered_evictions if e.get('status') == status_filter]
    
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        filtered_evictions = [e for e in filtered_evictions if datetime.strptime(e.get('filing_date', '1900-01-01'), '%Y-%m-%d') >= date_from]
    
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        filtered_evictions = [e for e in filtered_evictions if datetime.strptime(e.get('filing_date', '2100-12-31'), '%Y-%m-%d') <= date_to]
    
    # Generate report
    os.makedirs('reports', exist_ok=True)
    report_name = f"eviction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report_path = os.path.join('reports', f"{report_name}.json")
    
    # Create JSON report
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status_filter': status_filter,
        'date_from': date_from.strftime('%Y-%m-%d') if date_from else None,
        'date_to': date_to.strftime('%Y-%m-%d') if date_to else None,
        'count': len(filtered_evictions),
        'evictions': filtered_evictions
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Create Markdown report if requested
    if report_format == 'markdown':
        report_md_path = os.path.join('reports', f"{report_name}.md")
        with open(report_md_path, 'w') as f:
            f.write(f"# Eviction Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Filters\n")
            f.write(f"- Status: {status_filter if status_filter else 'All'}\n")
            f.write(f"- Date Range: {date_from.strftime('%Y-%m-%d') if date_from else 'Any'} to {date_to.strftime('%Y-%m-%d') if date_to else 'Any'}\n\n")
            
            f.write(f"## Summary\n")
            f.write(f"- Total Evictions: {len(filtered_evictions)}\n\n")
            
            f.write("## Eviction List\n\n")
            f.write("| ID | Tenant | Property | Filing Date | Status | Judgment Amount |\n")
            f.write("|---|---|---|---|---|---|\n")
            
            for eviction in filtered_evictions:
                tenant = eviction.get('tenant_name', 'Unknown')
                property_addr = eviction.get('property_address', 'Unknown')
                filing_date = eviction.get('filing_date', 'Unknown')
                status = eviction.get('status', 'Unknown')
                judgment_amount = eviction.get('judgment_amount', 'N/A')
                
                f.write(f"| {eviction.get('id', 'Unknown')} | {tenant} | {property_addr} | {filing_date} | {status} | {judgment_amount} |\n")
    
    flash('Report generated successfully', 'success')
    return redirect(url_for('view_report', filename=f"{report_name}.json"))

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/evictions')
def api_evictions():
    load_evictions()
    return jsonify(EVICTIONS_DB)

@app.route('/api/eviction/<eviction_id>')
def api_eviction(eviction_id):
    load_evictions()
    eviction = next((e for e in EVICTIONS_DB if e.get('id') == eviction_id), None)
    
    if not eviction:
        return jsonify({'error': 'Eviction not found'}), 404
    
    return jsonify(eviction)

# Add a new create_sample_data_without_flash function after save_evictions
def create_sample_data_without_flash():
    """Create sample data without using flash messages"""
    global EVICTIONS_DB
    
    # Create some sample evictions
    EVICTIONS_DB = [
        {
            'id': '1682485763',
            'case_number': 'EV-2025-001',
            'tenant_name': 'John Smith',
            'property_address': '123 Main St, Apt 4B, Cityville, ST 12345',
            'filing_date': '2025-03-15',
            'status': 'pending',
            'judgment_amount': 3200.00,
            'court_date': '2025-04-01',
            'writ_date': None,
            'days_to_eviction': 35
        },
        {
            'id': '1682485764',
            'case_number': 'EV-2025-002',
            'tenant_name': 'Jane Doe',
            'property_address': '456 Oak Ave, Unit 7, Townburg, ST 54321',
            'filing_date': '2025-02-10',
            'status': 'judgment',
            'judgment_amount': 4500.00,
            'court_date': '2025-02-28',
            'judgment_date': '2025-03-01',
            'writ_date': None,
            'days_to_eviction': 22
        },
        {
            'id': '1682485765',
            'case_number': 'EV-2025-003',
            'tenant_name': 'Michael Johnson',
            'property_address': '789 Pine Rd, Villageton, ST 67890',
            'filing_date': '2025-01-05',
            'status': 'writ',
            'judgment_amount': 2800.00,
            'court_date': '2025-01-20',
            'judgment_date': '2025-01-22',
            'writ_date': '2025-01-29',
            'days_to_eviction': 7
        },
        {
            'id': '1682485766',
            'case_number': 'EV-2025-004',
            'tenant_name': 'Emily Brown',
            'property_address': '321 Elm St, Hamlet, ST 13579',
            'filing_date': '2024-12-12',
            'status': 'completed',
            'judgment_amount': 3700.00,
            'court_date': '2024-12-28',
            'judgment_date': '2024-12-30',
            'writ_date': '2025-01-06',
            'eviction_date': '2025-01-13',
            'days_to_eviction': 0
        },
        {
            'id': '1682485767',
            'case_number': 'EV-2025-005',
            'tenant_name': 'Robert Wilson',
            'property_address': '555 Maple Ave, Boroughville, ST 24680',
            'filing_date': '2025-03-20',
            'status': 'active',
            'judgment_amount': None,
            'court_date': '2025-04-05',
            'days_to_eviction': 40
        }
    ]
    
    save_evictions()
    return True

# Modify the create_sample_data function to check if we're in a request context
def create_sample_data():
    """Create sample data and use flash messages if in a request context"""
    create_sample_data_without_flash()
    
    # Only attempt to flash if in an app context
    try:
        from flask import flash
        flash('Sample data created successfully', 'success')
    except RuntimeError:
        # Outside of request context
        print('Sample data created successfully')
    
    return redirect(url_for('evictions'))

# Modify the if __name__ == '__main__' block to use the create_sample_data_without_flash function
if __name__ == '__main__':
    # Create required directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('eviction_data', exist_ok=True)
    
    # Create sample data if no evictions exist
    load_evictions()
    if not EVICTIONS_DB:
        create_sample_data_without_flash()
        print("Created sample eviction data")
    else:
        print(f"Loaded {len(EVICTIONS_DB)} existing eviction records")
    
    app.run(debug=True) 