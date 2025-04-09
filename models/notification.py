import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.Enum(
        'system', 'eviction', 'lease', 'payment', 'document', 'user', 'other',
        name='notification_type'
    ), nullable=False)
    relation_type = db.Column(db.String(50))  # 'eviction', 'lease', 'payment', etc.
    relation_id = db.Column(UUID(as_uuid=True), nullable=True)  # ID of related entity
    status = db.Column(db.Enum('unread', 'read', 'archived', name='notification_status'), default='unread')
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent', name='notification_priority'), default='normal')
    action_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    # Relationships
    deliveries = db.relationship('NotificationDelivery', backref='notification', lazy='dynamic')

    def __repr__(self):
        return f"<Notification {self.id} {self.notification_type} {self.status}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'relation_type': self.relation_type,
            'relation_id': str(self.relation_id) if self.relation_id else None,
            'status': self.status,
            'priority': self.priority,
            'action_url': self.action_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class NotificationDelivery(db.Model):
    __tablename__ = 'notification_deliveries'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = db.Column(UUID(as_uuid=True), db.ForeignKey('notifications.id'), nullable=False)
    channel = db.Column(db.Enum('email', 'sms', 'push', 'in_app', 'other', name='delivery_channel'), nullable=False)
    status = db.Column(db.Enum('pending', 'sent', 'delivered', 'failed', 'cancelled', name='delivery_status'), nullable=False, default='pending')
    recipient = db.Column(db.String(255), nullable=False)  # Email address, phone number, etc.
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    external_id = db.Column(db.String(255))  # ID from external delivery service
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NotificationDelivery {self.id} {self.channel} {self.status}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'notification_id': str(self.notification_id),
            'channel': self.channel,
            'status': self.status,
            'recipient': self.recipient,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 