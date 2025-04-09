from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta
import uuid
import os
from dotenv import load_dotenv
from functools import wraps
import json
import pandas as pd
from csv_import_tools import locate_csv_files, inspect_csv, suggest_column_mapping, preview_import, prepare_import_config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///eviction_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-key-for-development')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
jwt = JWTManager(app)
CORS(app)

# Create template directory if it doesn't exist
os.makedirs('templates', exist_ok=True)

# Import models (must be imported after db initialization)
from models.user import User
from models.property import Property, PropertyUnit, PropertyManager
from models.tenant import Tenant
from models.lease import Lease, LeaseTenant
from models.eviction import EvictionCase, EvictionCaseTenant, EvictionEvent
from models.document import Document, DocumentRelation
from models.payment import Payment, PaymentTransaction
from models.notification import Notification, NotificationDelivery
from models.report import Report, ReportDelivery
from models.activity_log import ActivityLog
from models.setting import Setting

# Import routes
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.properties import property_bp
from routes.tenants import tenant_bp
from routes.leases import lease_bp
from routes.evictions import eviction_bp
from routes.documents import document_bp
from routes.payments import payment_bp
from routes.reports import report_bp
from routes.api import api_bp
from routes.admin import admin_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(property_bp, url_prefix='/properties')
app.register_blueprint(tenant_bp, url_prefix='/tenants')
app.register_blueprint(lease_bp, url_prefix='/leases')
app.register_blueprint(eviction_bp, url_prefix='/evictions')
app.register_blueprint(document_bp, url_prefix='/documents')
app.register_blueprint(payment_bp, url_prefix='/payments')
app.register_blueprint(report_bp, url_prefix='/reports')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/admin')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Utility functions for role-based access control
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Context processors
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.context_processor
def inject_user_notifications():
    if current_user.is_authenticated:
        notification_count = Notification.query.filter_by(
            user_id=current_user.id,
            status='unread'
        ).count()
        return {'notification_count': notification_count}
    return {'notification_count': 0}

# Request hooks
@app.before_request
def update_last_seen():
    if current_user.is_authenticated:
        current_user.last_login_at = datetime.utcnow()
        db.session.commit()

# Home route - redirect to dashboard if logged in
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

# Eviction timeline calculator route
@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST':
        filing_date = request.form.get('filing_date')
        writ_date = request.form.get('writ_date')
        
        # Validate input
        if not filing_date and not writ_date:
            flash('Please provide either a filing date or writ date', 'warning')
            return render_template('calculator.html')
        
        # Average timeline values (in days)
        avg_filing_to_hearing = 10  # 10 days from filing to hearing
        avg_hearing_to_judgment = 3  # 3 days from hearing to judgment
        avg_judgment_to_writ = 7     # 7 days from judgment to writ
        avg_writ_to_eviction = 7     # 7 days from writ to actual eviction
        
        # Calculate timeline
        results = {}
        if filing_date:
            filing_date = datetime.strptime(filing_date, '%Y-%m-%d')
            results['filing_date'] = filing_date
            
            hearing_date = filing_date + timedelta(days=avg_filing_to_hearing)
            results['hearing_date'] = hearing_date
            
            judgment_date = hearing_date + timedelta(days=avg_hearing_to_judgment)
            results['judgment_date'] = judgment_date
            
            writ_date = judgment_date + timedelta(days=avg_judgment_to_writ)
            results['writ_date'] = writ_date
            
            eviction_date = writ_date + timedelta(days=avg_writ_to_eviction)
            results['eviction_date'] = eviction_date
            
            total_days = (eviction_date - filing_date).days
            results['total_days'] = total_days
            
        elif writ_date:
            writ_date = datetime.strptime(writ_date, '%Y-%m-%d')
            results['writ_date'] = writ_date
            
            eviction_date = writ_date + timedelta(days=avg_writ_to_eviction)
            results['eviction_date'] = eviction_date
            
            days_to_eviction = (eviction_date - datetime.now()).days
            results['days_to_eviction'] = max(0, days_to_eviction)
        
        return render_template('calculator_results.html', results=results)
    
    return render_template('calculator.html')

# API health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

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
        with open('eviction_data/evictions.json', 'w') as f:
            json.dump(EVICTIONS_DB, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving evictions: {e}")

# Generate unique ID for evictions
def generate_id():
    return str(datetime.now().timestamp()).replace('.', '')

@app.route('/timeline_calculator')
def timeline_calculator():
    return render_template('timeline_calculator.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    filing_date_str = request.form.get('filing_date')
    writ_date_str = request.form.get('writ_date')
    
    if not filing_date_str and not writ_date_str:
        return render_template('timeline_calculator.html', error="Please provide at least one date")
    
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
    for filename in os.listdir('reports'):
        if filename.endswith('.json'):
            report_path = os.path.join('reports', filename)
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            report_files.append({
                'filename': filename,
                'timestamp': report.get('timestamp', 'Unknown'),
                'records': report.get('records_imported', 0)
            })
    
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
    report_name = f"eviction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report_path = os.path.join('reports', f"{report_name}.json")
    report_md_path = os.path.join('reports', f"{report_name}.md")
    
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
    
    # Create Markdown report
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

if __name__ == '__main__':
    app.run(debug=True) 