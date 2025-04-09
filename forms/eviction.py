from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField, DecimalField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from datetime import datetime, date

class EvictionForm(FlaskForm):
    property_id = SelectField('Property', validators=[DataRequired()])
    lease_id = SelectField('Lease', validators=[Optional()])
    case_number = StringField('Case Number', validators=[Optional(), Length(max=50)])
    filing_date = DateField('Filing Date', validators=[Optional()])
    filing_code = StringField('Filing Code', validators=[Optional(), Length(max=50)])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('service', 'Service'),
        ('court', 'Court'),
        ('judgment', 'Judgment'),
        ('writ', 'Writ'),
        ('eviction', 'Eviction'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('settled', 'Settled')
    ], validators=[DataRequired()])
    reason = SelectField('Reason', choices=[
        ('non_payment', 'Non-payment of Rent'),
        ('lease_violation', 'Lease Violation'),
        ('criminal_activity', 'Criminal Activity'),
        ('property_damage', 'Property Damage'),
        ('holdover', 'Holdover (Staying beyond lease term)'),
        ('other', 'Other')
    ], validators=[Optional()])
    back_rent_amount = DecimalField('Back Rent Amount', validators=[Optional()], places=2)
    court_costs = DecimalField('Court Costs', validators=[Optional()], places=2)
    attorney_fees = DecimalField('Attorney Fees', validators=[Optional()], places=2)
    late_fees = DecimalField('Late Fees', validators=[Optional()], places=2)
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Create Eviction Case')
    
    def validate_filing_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError('Filing date cannot be in the future')


class EvictionEventForm(FlaskForm):
    event_type = SelectField('Event Type', choices=[
        ('filing', 'Filing'),
        ('service', 'Service'),
        ('hearing', 'Court Hearing'),
        ('judgment', 'Judgment'),
        ('writ', 'Writ of Possession'),
        ('eviction', 'Eviction Execution'),
        ('payment', 'Payment'),
        ('settlement', 'Settlement'),
        ('continuance', 'Continuance'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    event_date = DateField('Event Date', validators=[DataRequired()])
    event_time = TimeField('Event Time', validators=[Optional()])
    location = StringField('Location', validators=[Optional(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    outcome = TextAreaField('Outcome', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Add Event')
    
    def validate_event_date(self, field):
        if field.data and field.data > date.today():
            if self.event_type.data not in ['hearing', 'eviction']:
                raise ValidationError('Event date cannot be in the future for this event type')


class EvictionReportForm(FlaskForm):
    title = StringField('Report Title', validators=[DataRequired(), Length(max=100)])
    status = SelectField('Filter by Status', choices=[
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('service', 'Service'),
        ('court', 'Court'),
        ('judgment', 'Judgment'),
        ('writ', 'Writ'),
        ('eviction', 'Eviction'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('settled', 'Settled')
    ], validators=[Optional()])
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    format = SelectField('Report Format', choices=[
        ('json', 'JSON'),
        ('markdown', 'Markdown'),
        ('pdf', 'PDF (Coming Soon)')
    ], default='json', validators=[DataRequired()])
    include_details = BooleanField('Include Case Details', default=True)
    include_financials = BooleanField('Include Financial Information', default=True)
    include_tenant_info = BooleanField('Include Tenant Information', default=True)
    include_timeline = BooleanField('Include Timeline Information', default=True)
    sort_by = SelectField('Sort By', choices=[
        ('filing_date', 'Filing Date'),
        ('status', 'Status'),
        ('judgment_amount', 'Judgment Amount'),
        ('tenant_name', 'Tenant Name')
    ], default='filing_date', validators=[DataRequired()])
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc', validators=[DataRequired()])
    submit = SubmitField('Generate Report')
    
    def validate_date_to(self, field):
        if field.data and self.date_from.data and field.data < self.date_from.data:
            raise ValidationError('To date must be after from date') 