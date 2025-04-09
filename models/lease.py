import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app import db

class Lease(db.Model):
    __tablename__ = 'leases'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'), nullable=False)
    unit_id = db.Column(UUID(as_uuid=True), db.ForeignKey('property_units.id'), nullable=True)
    lease_number = db.Column(db.String(50))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    rent_amount = db.Column(db.Numeric(10, 2), nullable=False)
    security_deposit = db.Column(db.Numeric(10, 2))
    pet_deposit = db.Column(db.Numeric(10, 2))
    late_fee_amount = db.Column(db.Numeric(10, 2))
    late_fee_grace_period = db.Column(db.Integer, default=5)  # Days
    status = db.Column(db.Enum('active', 'expired', 'terminated', 'pending', name='lease_status'), nullable=False, default='pending')
    payment_day = db.Column(db.Integer, default=1)  # Day of month
    payment_frequency = db.Column(db.Enum('monthly', 'weekly', 'bi-weekly', 'quarterly', 'annually', name='payment_frequency'), default='monthly')
    renewal_reminder_sent = db.Column(db.Boolean, default=False)
    move_out_notice_date = db.Column(db.Date)
    move_out_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    lease_tenants = db.relationship('LeaseTenant', backref='lease', lazy='dynamic')
    payments = db.relationship('Payment', backref='lease', lazy='dynamic')
    eviction_cases = db.relationship('EvictionCase', backref='lease', lazy='dynamic')
    documents = db.relationship('DocumentRelation', backref='lease', lazy='dynamic', 
                               primaryjoin="and_(DocumentRelation.relation_type=='lease', "
                                          "DocumentRelation.relation_id==Lease.id)")

    def __repr__(self):
        return f"<Lease {self.id} Property {self.property_id} {self.start_date} to {self.end_date}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'unit_id': str(self.unit_id) if self.unit_id else None,
            'lease_number': self.lease_number,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'rent_amount': float(self.rent_amount),
            'security_deposit': float(self.security_deposit) if self.security_deposit else None,
            'pet_deposit': float(self.pet_deposit) if self.pet_deposit else None,
            'late_fee_amount': float(self.late_fee_amount) if self.late_fee_amount else None,
            'late_fee_grace_period': self.late_fee_grace_period,
            'status': self.status,
            'payment_day': self.payment_day,
            'payment_frequency': self.payment_frequency,
            'renewal_reminder_sent': self.renewal_reminder_sent,
            'move_out_notice_date': self.move_out_notice_date.isoformat() if self.move_out_notice_date else None,
            'move_out_completed': self.move_out_completed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class LeaseTenant(db.Model):
    __tablename__ = 'lease_tenants'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lease_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leases.id'), nullable=False)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LeaseTenant {self.id} Lease {self.lease_id} Tenant {self.tenant_id}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'lease_id': str(self.lease_id),
            'tenant_id': str(self.tenant_id),
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 