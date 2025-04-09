import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lease_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leases.id'), nullable=True)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'), nullable=False)
    payment_type = db.Column(db.Enum(
        'rent', 'deposit', 'late_fee', 'eviction', 
        'utility', 'maintenance', 'other',
        name='payment_type'
    ), nullable=False)
    relation_id = db.Column(UUID(as_uuid=True), nullable=True)  # For linking to eviction cases, etc.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum(
        'cash', 'check', 'credit_card', 'bank_transfer', 
        'money_order', 'paypal', 'venmo', 'other',
        name='payment_method'
    ))
    payment_date = db.Column(db.Date, nullable=False)
    payment_status = db.Column(db.Enum(
        'pending', 'completed', 'failed', 'refunded', 'cancelled',
        name='payment_status'
    ), nullable=False, default='pending')
    reference_number = db.Column(db.String(100))
    memo = db.Column(db.Text)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    tenant = db.relationship('Tenant', backref='payments')
    creator = db.relationship('User', backref='created_payments')
    transactions = db.relationship('PaymentTransaction', backref='payment', lazy='dynamic')
    documents = db.relationship('DocumentRelation', backref='payment', lazy='dynamic',
                               primaryjoin="and_(DocumentRelation.relation_type=='payment', "
                                          "DocumentRelation.relation_id==Payment.id)")

    def __repr__(self):
        return f"<Payment {self.id} {self.payment_type} {self.amount}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'lease_id': str(self.lease_id) if self.lease_id else None,
            'tenant_id': str(self.tenant_id),
            'payment_type': self.payment_type,
            'relation_id': str(self.relation_id) if self.relation_id else None,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat(),
            'payment_status': self.payment_status,
            'reference_number': self.reference_number,
            'memo': self.memo,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = db.Column(UUID(as_uuid=True), db.ForeignKey('payments.id'), nullable=False)
    transaction_type = db.Column(db.Enum(
        'payment', 'refund', 'chargeback', 'fee', 'adjustment', 'other',
        name='transaction_type'
    ), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transaction_status = db.Column(db.Enum(
        'pending', 'completed', 'failed', 'cancelled',
        name='transaction_status'
    ), nullable=False, default='pending')
    gateway = db.Column(db.String(100))
    gateway_transaction_id = db.Column(db.String(255))
    gateway_response = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PaymentTransaction {self.id} {self.transaction_type} {self.amount}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'payment_id': str(self.payment_id),
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'transaction_date': self.transaction_date.isoformat(),
            'transaction_status': self.transaction_status,
            'gateway': self.gateway,
            'gateway_transaction_id': self.gateway_transaction_id,
            'gateway_response': self.gateway_response,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 