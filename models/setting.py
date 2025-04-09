import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app import db

class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)  # Null for system-wide settings
    category = db.Column(db.String(50), nullable=False)  # 'system', 'user', 'notification', etc.
    key = db.Column(db.String(255), nullable=False)
    value = db.Column(JSONB)
    description = db.Column(db.Text)
    is_system = db.Column(db.Boolean, default=False)
    is_required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='settings')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'key', name='uix_setting_user_category_key'),
    )

    def __repr__(self):
        return f"<Setting {self.id} {self.category}.{self.key}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'category': self.category,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'is_system': self.is_system,
            'is_required': self.is_required,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 