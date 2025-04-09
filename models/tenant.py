import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app import db

class Tenant(db.Model):
    __tablename__ = 'tenants'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    social_security = db.Column(db.String(11))
    drivers_license = db.Column(db.String(50))
    drivers_license_state = db.Column(db.String(2))
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref='tenant_profile', uselist=False)
    lease_tenants = db.relationship('LeaseTenant', backref='tenant', lazy='dynamic')
    eviction_case_tenants = db.relationship('EvictionCaseTenant', backref='tenant', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Tenant {self.id} {self.first_name} {self.last_name}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'social_security': self.social_security,
            'drivers_license': self.drivers_license,
            'drivers_license_state': self.drivers_license_state,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relation': self.emergency_contact_relation,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        } 