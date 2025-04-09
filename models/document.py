import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app import db

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    file_type = db.Column(db.String(100))
    mime_type = db.Column(db.String(100))
    document_type = db.Column(db.Enum(
        'lease', 'notice', 'court', 'writ', 
        'judgment', 'payment', 'correspondence', 'other',
        name='document_type'
    ))
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    # Relationships
    document_relations = db.relationship('DocumentRelation', backref='document', lazy='dynamic')

    def __repr__(self):
        return f"<Document {self.id} {self.filename}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'owner_id': str(self.owner_id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'document_type': self.document_type,
            'description': self.description,
            'is_public': self.is_public,
            'upload_date': self.upload_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class DocumentRelation(db.Model):
    __tablename__ = 'document_relations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('documents.id'), nullable=False)
    relation_type = db.Column(db.Enum(
        'property', 'tenant', 'lease', 'eviction', 'payment', 'user', 'other',
        name='document_relation_type'
    ), nullable=False)
    relation_id = db.Column(UUID(as_uuid=True), nullable=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # User relationship
    user = db.relationship('User', backref='document_relations')

    def __repr__(self):
        return f"<DocumentRelation {self.id} Document {self.document_id} {self.relation_type} {self.relation_id}>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'relation_type': self.relation_type,
            'relation_id': str(self.relation_id),
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 