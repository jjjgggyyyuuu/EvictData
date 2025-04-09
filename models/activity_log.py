import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # 'eviction', 'property', 'tenant', etc.
    entity_id = db.Column(UUID(as_uuid=True), nullable=True)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    changes = db.Column(JSONB)  # Stores before/after changes
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='activities')

    def __repr__(self):
        return f"<ActivityLog {self.id} {self.action} {self.entity_type}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'changes': self.changes,
            'created_at': self.created_at.isoformat()
        } 