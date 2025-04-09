import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app import db

class EvictionCase(db.Model):
    __tablename__ = 'eviction_cases'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'), nullable=False)
    lease_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leases.id'), nullable=True)
    case_number = db.Column(db.String(50))
    filing_date = db.Column(db.Date)
    filing_code = db.Column(db.String(50))
    court_name = db.Column(db.String(255))
    court_address = db.Column(db.String(255))
    judge_name = db.Column(db.String(100))
    status = db.Column(db.Enum(
        'pending', 'active', 'service', 'court', 'judgment', 
        'writ', 'eviction', 'completed', 'cancelled', 'settled',
        name='eviction_status'
    ), nullable=False, default='pending')
    reason = db.Column(db.Enum(
        'non_payment', 'lease_violation', 'criminal_activity', 
        'property_damage', 'holdover', 'other',
        name='eviction_reason'
    ))
    back_rent_amount = db.Column(db.Numeric(10, 2))
    court_costs = db.Column(db.Numeric(10, 2))
    attorney_fees = db.Column(db.Numeric(10, 2))
    late_fees = db.Column(db.Numeric(10, 2))
    judgment_amount = db.Column(db.Numeric(10, 2))
    judgment_date = db.Column(db.Date)
    writ_date = db.Column(db.Date)
    actual_eviction_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    case_tenants = db.relationship('EvictionCaseTenant', backref='eviction_case', lazy='dynamic')
    events = db.relationship('EvictionEvent', backref='eviction_case', lazy='dynamic')
    documents = db.relationship('DocumentRelation', backref='eviction_case', lazy='dynamic',
                               primaryjoin="and_(DocumentRelation.relation_type=='eviction', "
                                          "DocumentRelation.relation_id==EvictionCase.id)")
    payments = db.relationship('Payment', backref='eviction_case', lazy='dynamic',
                              primaryjoin="and_(Payment.payment_type=='eviction', "
                                         "Payment.relation_id==EvictionCase.id)")

    def __repr__(self):
        return f"<EvictionCase {self.id} {self.case_number} Status: {self.status}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'lease_id': str(self.lease_id) if self.lease_id else None,
            'case_number': self.case_number,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'filing_code': self.filing_code,
            'court_name': self.court_name,
            'court_address': self.court_address,
            'judge_name': self.judge_name,
            'status': self.status,
            'reason': self.reason,
            'back_rent_amount': float(self.back_rent_amount) if self.back_rent_amount else None,
            'court_costs': float(self.court_costs) if self.court_costs else None,
            'attorney_fees': float(self.attorney_fees) if self.attorney_fees else None,
            'late_fees': float(self.late_fees) if self.late_fees else None,
            'judgment_amount': float(self.judgment_amount) if self.judgment_amount else None,
            'judgment_date': self.judgment_date.isoformat() if self.judgment_date else None,
            'writ_date': self.writ_date.isoformat() if self.writ_date else None,
            'actual_eviction_date': self.actual_eviction_date.isoformat() if self.actual_eviction_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }

    @property
    def total_amount_due(self):
        total = 0
        if self.back_rent_amount:
            total += float(self.back_rent_amount)
        if self.court_costs:
            total += float(self.court_costs)
        if self.attorney_fees:
            total += float(self.attorney_fees)
        if self.late_fees:
            total += float(self.late_fees)
        return total


class EvictionCaseTenant(db.Model):
    __tablename__ = 'eviction_case_tenants'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eviction_case_id = db.Column(UUID(as_uuid=True), db.ForeignKey('eviction_cases.id'), nullable=False)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    service_method = db.Column(db.Enum('personal', 'mail', 'posting', 'substitute', 'other', name='service_method'))
    service_date = db.Column(db.Date)
    service_status = db.Column(db.Enum('pending', 'attempted', 'completed', 'failed', name='service_status'), default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EvictionCaseTenant {self.id} Case {self.eviction_case_id} Tenant {self.tenant_id}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'eviction_case_id': str(self.eviction_case_id),
            'tenant_id': str(self.tenant_id),
            'is_primary': self.is_primary,
            'service_method': self.service_method,
            'service_date': self.service_date.isoformat() if self.service_date else None,
            'service_status': self.service_status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class EvictionEvent(db.Model):
    __tablename__ = 'eviction_events'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eviction_case_id = db.Column(UUID(as_uuid=True), db.ForeignKey('eviction_cases.id'), nullable=False)
    event_type = db.Column(db.Enum(
        'filing', 'service', 'hearing', 'judgment', 'writ', 
        'eviction', 'payment', 'settlement', 'continuance', 'other',
        name='eviction_event_type'
    ), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time)
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    outcome = db.Column(db.Text)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='eviction_events')

    def __repr__(self):
        return f"<EvictionEvent {self.id} {self.event_type} on {self.event_date}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'eviction_case_id': str(self.eviction_case_id),
            'event_type': self.event_type,
            'event_date': self.event_date.isoformat(),
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'location': self.location,
            'description': self.description,
            'outcome': self.outcome,
            'created_by': str(self.created_by) if self.created_by else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 