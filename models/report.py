import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app import db

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    report_type = db.Column(db.Enum(
        'eviction', 'financial', 'tenant', 'property', 'lease', 
        'payment', 'document', 'summary', 'custom', 'other',
        name='report_type'
    ), nullable=False)
    format = db.Column(db.Enum('json', 'pdf', 'csv', 'excel', 'markdown', 'html', name='report_format'), nullable=False)
    file_path = db.Column(db.String(500))
    parameters = db.Column(JSONB)  # Stores filters, date ranges, etc.
    record_count = db.Column(db.Integer)
    is_scheduled = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.String(50))  # daily, weekly, monthly, etc.
    last_run_at = db.Column(db.DateTime)
    next_run_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref='reports')
    deliveries = db.relationship('ReportDelivery', backref='report', lazy='dynamic')

    def __repr__(self):
        return f"<Report {self.id} {self.title} {self.report_type}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'format': self.format,
            'file_path': self.file_path,
            'parameters': self.parameters,
            'record_count': self.record_count,
            'is_scheduled': self.is_scheduled,
            'schedule_frequency': self.schedule_frequency,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class ReportDelivery(db.Model):
    __tablename__ = 'report_deliveries'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = db.Column(UUID(as_uuid=True), db.ForeignKey('reports.id'), nullable=False)
    channel = db.Column(db.Enum('email', 'download', 'api', 'other', name='report_delivery_channel'), nullable=False)
    status = db.Column(db.Enum('pending', 'sent', 'delivered', 'failed', 'cancelled', name='delivery_status'), nullable=False, default='pending')
    recipient = db.Column(db.String(255))  # Email address, user ID, etc.
    delivery_time = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ReportDelivery {self.id} {self.channel} {self.status}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'report_id': str(self.report_id),
            'channel': self.channel,
            'status': self.status,
            'recipient': self.recipient,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 