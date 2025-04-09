from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import json
import os

from app import db
from models.eviction import EvictionCase, EvictionCaseTenant, EvictionEvent
from models.tenant import Tenant
from models.property import Property
from models.lease import Lease
from forms.eviction import EvictionForm, EvictionEventForm, EvictionReportForm

eviction_bp = Blueprint('eviction', __name__)

@eviction_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status')
    search_term = request.args.get('search')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Base query
    query = EvictionCase.query.join(Property).filter(
        Property.owner_id == current_user.id,
        EvictionCase.deleted_at == None
    )
    
    # Apply filters
    if status_filter:
        query = query.filter(EvictionCase.status == status_filter)
    
    if search_term:
        query = query.filter(
            (EvictionCase.case_number.ilike(f'%{search_term}%')) |
            (Property.address.ilike(f'%{search_term}%'))
        )
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(EvictionCase.filing_date >= date_from)
        except ValueError:
            flash('Invalid from date format', 'danger')
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(EvictionCase.filing_date <= date_to)
        except ValueError:
            flash('Invalid to date format', 'danger')
    
    # Paginate
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(EvictionCase.filing_date.desc()).paginate(page=page, per_page=per_page)
    evictions = pagination.items
    
    # Get tenant info for each eviction
    for eviction in evictions:
        tenant_cases = EvictionCaseTenant.query.filter_by(eviction_case_id=eviction.id).all()
        if tenant_cases:
            primary_tenant_case = next((tc for tc in tenant_cases if tc.is_primary), tenant_cases[0])
            tenant = Tenant.query.get(primary_tenant_case.tenant_id)
            eviction.tenant_name = tenant.full_name if tenant else "Unknown"
        else:
            eviction.tenant_name = "No tenant linked"
    
    return render_template('evictions.html',
                          evictions=evictions,
                          pagination=pagination,
                          status_filter=status_filter,
                          search_term=search_term,
                          date_from=date_from.strftime('%Y-%m-%d') if isinstance(date_from, datetime) else date_from,
                          date_to=date_to.strftime('%Y-%m-%d') if isinstance(date_to, datetime) else date_to)

@eviction_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = EvictionForm()
    
    # Populate property choices
    properties = Property.query.filter_by(owner_id=current_user.id).all()
    form.property_id.choices = [(str(p.id), f"{p.name} - {p.address}") for p in properties]
    
    if form.validate_on_submit():
        eviction = EvictionCase(
            property_id=uuid.UUID(form.property_id.data),
            case_number=form.case_number.data,
            filing_date=form.filing_date.data,
            status=form.status.data,
            reason=form.reason.data,
            back_rent_amount=form.back_rent_amount.data,
            court_costs=form.court_costs.data,
            filing_code=form.filing_code.data,
            notes=form.notes.data
        )
        
        # Set optional fields
        if form.lease_id.data:
            eviction.lease_id = uuid.UUID(form.lease_id.data)
        
        db.session.add(eviction)
        db.session.commit()
        
        # Add event for filing
        if form.filing_date.data:
            filing_event = EvictionEvent(
                eviction_case_id=eviction.id,
                event_type='filing',
                event_date=form.filing_date.data,
                description=f"Eviction case filed with case number {form.case_number.data}",
                created_by=current_user.id
            )
            db.session.add(filing_event)
            db.session.commit()
        
        flash('Eviction case created successfully', 'success')
        return redirect(url_for('eviction.view', eviction_id=eviction.id))
    
    return render_template('eviction_form.html', form=form, title='New Eviction Case')

@eviction_bp.route('/<uuid:eviction_id>')
@login_required
def view(eviction_id):
    eviction = EvictionCase.query.get_or_404(eviction_id)
    
    # Check if user has permission
    property = Property.query.get(eviction.property_id)
    if property.owner_id != current_user.id:
        abort(403)
    
    # Get property
    eviction.property = property
    
    # Get tenant information
    tenant_cases = EvictionCaseTenant.query.filter_by(eviction_case_id=eviction.id).all()
    tenants = []
    for tc in tenant_cases:
        tenant = Tenant.query.get(tc.tenant_id)
        if tenant:
            tenant_info = tenant.to_dict()
            tenant_info['service_status'] = tc.service_status
            tenant_info['service_date'] = tc.service_date
            tenant_info['service_method'] = tc.service_method
            tenant_info['is_primary'] = tc.is_primary
            tenants.append(tenant_info)
    
    # Get events for timeline
    events = EvictionEvent.query.filter_by(eviction_case_id=eviction.id).order_by(EvictionEvent.event_date).all()
    
    # Get lease information if available
    lease = None
    if eviction.lease_id:
        lease = Lease.query.get(eviction.lease_id)
    
    # Calculate days remaining for writ/eviction
    days_remaining = None
    if eviction.status == 'writ' and eviction.writ_date:
        # Average 7 days from writ to eviction
        estimated_eviction = eviction.writ_date + timedelta(days=7)
        days_remaining = (estimated_eviction - datetime.now().date()).days
    
    return render_template('eviction_details.html',
                          eviction=eviction,
                          tenants=tenants,
                          events=events,
                          lease=lease,
                          days_remaining=days_remaining)

@eviction_bp.route('/<uuid:eviction_id>/update', methods=['POST'])
@login_required
def update(eviction_id):
    eviction = EvictionCase.query.get_or_404(eviction_id)
    
    # Check if user has permission
    property = Property.query.get(eviction.property_id)
    if property.owner_id != current_user.id:
        abort(403)
    
    status = request.form.get('status')
    judgment_amount = request.form.get('judgment_amount')
    court_date = request.form.get('court_date')
    judgment_date = request.form.get('judgment_date')
    writ_date = request.form.get('writ_date')
    notes = request.form.get('notes')
    
    # Update status and other fields
    previous_status = eviction.status
    if status:
        eviction.status = status
    
    if judgment_amount:
        eviction.judgment_amount = judgment_amount
    
    if notes:
        eviction.notes = notes
    
    # Update dates if provided
    if court_date:
        try:
            court_date = datetime.strptime(court_date, '%Y-%m-%d').date()
            # Add court event
            event = EvictionEvent(
                eviction_case_id=eviction.id,
                event_type='hearing',
                event_date=court_date,
                description=f"Court hearing scheduled",
                created_by=current_user.id
            )
            db.session.add(event)
        except ValueError:
            flash('Invalid court date format', 'danger')
    
    if judgment_date:
        try:
            eviction.judgment_date = datetime.strptime(judgment_date, '%Y-%m-%d').date()
            # Add judgment event
            event = EvictionEvent(
                eviction_case_id=eviction.id,
                event_type='judgment',
                event_date=eviction.judgment_date,
                description=f"Judgment entered for ${judgment_amount}",
                created_by=current_user.id
            )
            db.session.add(event)
        except ValueError:
            flash('Invalid judgment date format', 'danger')
    
    if writ_date:
        try:
            eviction.writ_date = datetime.strptime(writ_date, '%Y-%m-%d').date()
            # Add writ event
            event = EvictionEvent(
                eviction_case_id=eviction.id,
                event_type='writ',
                event_date=eviction.writ_date,
                description=f"Writ of possession issued",
                created_by=current_user.id
            )
            db.session.add(event)
        except ValueError:
            flash('Invalid writ date format', 'danger')
    
    # Add event for status change
    if status and status != previous_status:
        event = EvictionEvent(
            eviction_case_id=eviction.id,
            event_type='other',
            event_date=datetime.now().date(),
            description=f"Status changed from {previous_status} to {status}",
            created_by=current_user.id
        )
        db.session.add(event)
    
    db.session.commit()
    flash('Eviction updated successfully', 'success')
    
    return redirect(url_for('eviction.view', eviction_id=eviction_id))

@eviction_bp.route('/<uuid:eviction_id>/events/new', methods=['GET', 'POST'])
@login_required
def add_event(eviction_id):
    eviction = EvictionCase.query.get_or_404(eviction_id)
    
    # Check if user has permission
    property = Property.query.get(eviction.property_id)
    if property.owner_id != current_user.id:
        abort(403)
    
    form = EvictionEventForm()
    
    if form.validate_on_submit():
        event = EvictionEvent(
            eviction_case_id=eviction_id,
            event_type=form.event_type.data,
            event_date=form.event_date.data,
            event_time=form.event_time.data,
            location=form.location.data,
            description=form.description.data,
            outcome=form.outcome.data,
            created_by=current_user.id
        )
        
        db.session.add(event)
        
        # Update eviction status based on event type
        if form.event_type.data == 'filing':
            eviction.status = 'active'
        elif form.event_type.data == 'service':
            eviction.status = 'service'
        elif form.event_type.data == 'hearing':
            eviction.status = 'court'
        elif form.event_type.data == 'judgment':
            eviction.status = 'judgment'
            eviction.judgment_date = form.event_date.data
        elif form.event_type.data == 'writ':
            eviction.status = 'writ'
            eviction.writ_date = form.event_date.data
        elif form.event_type.data == 'eviction':
            eviction.status = 'completed'
            eviction.actual_eviction_date = form.event_date.data
        
        db.session.commit()
        flash('Event added successfully', 'success')
        return redirect(url_for('eviction.view', eviction_id=eviction_id))
    
    return render_template('eviction_event_form.html', form=form, eviction=eviction)

@eviction_bp.route('/reports')
@login_required
def reports():
    # List existing reports
    reports_dir = os.path.join(current_app.root_path, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    report_files = []
    for filename in os.listdir(reports_dir):
        if filename.startswith('eviction_report_') and (filename.endswith('.json') or filename.endswith('.md')):
            report_path = os.path.join(reports_dir, filename)
            if filename.endswith('.json'):
                with open(report_path, 'r') as f:
                    report = json.load(f)
                    
                report_files.append({
                    'filename': filename,
                    'timestamp': report.get('timestamp', 'Unknown'),
                    'count': report.get('count', 0),
                    'type': 'Eviction Report'
                })
    
    return render_template('reports.html', reports=report_files)

@eviction_bp.route('/generate-report', methods=['GET', 'POST'])
@login_required
def generate_report():
    form = EvictionReportForm()
    
    if form.validate_on_submit():
        # Get evictions based on filters
        query = EvictionCase.query.join(Property).filter(
            Property.owner_id == current_user.id,
            EvictionCase.deleted_at == None
        )
        
        if form.status.data:
            query = query.filter(EvictionCase.status == form.status.data)
        
        if form.date_from.data:
            query = query.filter(EvictionCase.filing_date >= form.date_from.data)
        
        if form.date_to.data:
            query = query.filter(EvictionCase.filing_date <= form.date_to.data)
        
        evictions = query.all()
        
        # Create report data
        report_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'title': form.title.data,
            'status_filter': form.status.data,
            'date_from': form.date_from.data.strftime('%Y-%m-%d') if form.date_from.data else None,
            'date_to': form.date_to.data.strftime('%Y-%m-%d') if form.date_to.data else None,
            'count': len(evictions),
            'evictions': []
        }
        
        # Add eviction data to report
        for eviction in evictions:
            # Get property
            property = Property.query.get(eviction.property_id)
            
            # Get tenant information
            tenant_cases = EvictionCaseTenant.query.filter_by(eviction_case_id=eviction.id).all()
            tenant_names = []
            for tc in tenant_cases:
                tenant = Tenant.query.get(tc.tenant_id)
                if tenant:
                    tenant_names.append(tenant.full_name)
            
            # Add to report
            eviction_data = eviction.to_dict()
            eviction_data['property_address'] = f"{property.address}, {property.city}, {property.state} {property.zip_code}" if property else "Unknown"
            eviction_data['tenant_names'] = tenant_names
            
            report_data['evictions'].append(eviction_data)
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"eviction_report_{timestamp}"
        
        report_dir = os.path.join(current_app.root_path, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        # Save JSON report
        report_path = os.path.join(report_dir, f"{report_name}.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Save markdown report if requested
        if form.format.data == 'markdown':
            report_md_path = os.path.join(report_dir, f"{report_name}.md")
            with open(report_md_path, 'w') as f:
                f.write(f"# {form.title.data}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## Filters\n")
                f.write(f"- Status: {form.status.data if form.status.data else 'All'}\n")
                f.write(f"- Date Range: {form.date_from.data.strftime('%Y-%m-%d') if form.date_from.data else 'Any'} to {form.date_to.data.strftime('%Y-%m-%d') if form.date_to.data else 'Any'}\n\n")
                
                f.write("## Summary\n")
                f.write(f"- Total Evictions: {len(evictions)}\n")
                
                # Add status breakdown
                status_counts = {}
                for e in evictions:
                    status_counts[e.status] = status_counts.get(e.status, 0) + 1
                
                f.write("- Status Breakdown:\n")
                for status, count in status_counts.items():
                    f.write(f"  - {status.capitalize()}: {count}\n")
                f.write("\n")
                
                # Calculate financial summary
                total_judgment = sum(float(e.judgment_amount) for e in evictions if e.judgment_amount)
                total_back_rent = sum(float(e.back_rent_amount) for e in evictions if e.back_rent_amount)
                
                f.write("## Financial Summary\n")
                f.write(f"- Total Judgment Amount: ${total_judgment:.2f}\n")
                f.write(f"- Total Back Rent: ${total_back_rent:.2f}\n\n")
                
                f.write("## Eviction List\n\n")
                f.write("| Case # | Tenant | Property | Filing Date | Status | Judgment Amount |\n")
                f.write("|---|---|---|---|---|---|\n")
                
                for eviction in evictions:
                    tenant_str = ", ".join(report_data['evictions'][evictions.index(eviction)]['tenant_names'])
                    property_addr = report_data['evictions'][evictions.index(eviction)]['property_address']
                    filing_date = eviction.filing_date.strftime('%Y-%m-%d') if eviction.filing_date else 'N/A'
                    judgment_amount = f"${float(eviction.judgment_amount):.2f}" if eviction.judgment_amount else 'N/A'
                    
                    f.write(f"| {eviction.case_number or 'N/A'} | {tenant_str or 'Unknown'} | {property_addr} | {filing_date} | {eviction.status.capitalize()} | {judgment_amount} |\n")
                
                # Add detailed information for each eviction
                f.write("\n## Detailed Information\n\n")
                for eviction in evictions:
                    tenant_str = ", ".join(report_data['evictions'][evictions.index(eviction)]['tenant_names'])
                    property_addr = report_data['evictions'][evictions.index(eviction)]['property_address']
                    
                    f.write(f"### Case {eviction.case_number or 'N/A'}\n\n")
                    f.write(f"- **Tenant(s)**: {tenant_str or 'Unknown'}\n")
                    f.write(f"- **Property**: {property_addr}\n")
                    f.write(f"- **Filing Date**: {eviction.filing_date.strftime('%Y-%m-%d') if eviction.filing_date else 'N/A'}\n")
                    f.write(f"- **Status**: {eviction.status.capitalize()}\n")
                    f.write(f"- **Reason**: {eviction.reason.replace('_', ' ').capitalize() if eviction.reason else 'N/A'}\n")
                    
                    if eviction.judgment_date:
                        f.write(f"- **Judgment Date**: {eviction.judgment_date.strftime('%Y-%m-%d')}\n")
                    
                    if eviction.judgment_amount:
                        f.write(f"- **Judgment Amount**: ${float(eviction.judgment_amount):.2f}\n")
                    
                    if eviction.back_rent_amount:
                        f.write(f"- **Back Rent**: ${float(eviction.back_rent_amount):.2f}\n")
                    
                    if eviction.court_costs:
                        f.write(f"- **Court Costs**: ${float(eviction.court_costs):.2f}\n")
                    
                    if eviction.writ_date:
                        f.write(f"- **Writ Date**: {eviction.writ_date.strftime('%Y-%m-%d')}\n")
                    
                    if eviction.actual_eviction_date:
                        f.write(f"- **Actual Eviction Date**: {eviction.actual_eviction_date.strftime('%Y-%m-%d')}\n")
                    
                    if eviction.notes:
                        f.write(f"- **Notes**: {eviction.notes}\n")
                    
                    f.write("\n")
        
        flash('Report generated successfully', 'success')
        return redirect(url_for('eviction.reports'))
    
    return render_template('eviction_report_form.html', form=form) 