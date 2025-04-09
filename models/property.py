import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app import db

class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), default='USA')
    property_type = db.Column(db.Enum('apartment', 'house', 'condo', 'townhouse', 'commercial', 'other', name='property_type'), nullable=False)
    status = db.Column(db.Enum('active', 'inactive', 'maintenance', name='property_status'), nullable=False, default='active')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    units = db.relationship('PropertyUnit', backref='property', lazy='dynamic')
    managers = db.relationship('PropertyManager', backref='property', lazy='dynamic')
    leases = db.relationship('Lease', backref='property', lazy='dynamic')
    eviction_cases = db.relationship('EvictionCase', backref='property', lazy='dynamic')

    def __repr__(self):
        return f"<Property {self.id} {self.name}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'owner_id': str(self.owner_id),
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'property_type': self.property_type,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class PropertyUnit(db.Model):
    __tablename__ = 'property_units'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.String(10))
    size_sqft = db.Column(db.Integer)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Float)
    rent_amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.Enum('vacant', 'occupied', 'maintenance', name='unit_status'), nullable=False, default='vacant')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    leases = db.relationship('Lease', backref='unit', lazy='dynamic')

    def __repr__(self):
        return f"<PropertyUnit {self.id} {self.property_id} {self.unit_number}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'unit_number': self.unit_number,
            'floor': self.floor,
            'size_sqft': self.size_sqft,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'rent_amount': float(self.rent_amount) if self.rent_amount else None,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class PropertyManager(db.Model):
    __tablename__ = 'property_managers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'), nullable=False)
    manager_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('primary', 'secondary', 'maintenance', 'leasing', name='manager_role'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manager = db.relationship('User', backref='managed_properties')

    def __repr__(self):
        return f"<PropertyManager {self.id} Property {self.property_id} Manager {self.manager_id}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'manager_id': str(self.manager_id),
            'role': self.role,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 