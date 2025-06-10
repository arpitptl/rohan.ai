from datetime import datetime
from . import db
import uuid

class WebhookSubscription(db.Model):
    """Model for webhook subscriptions"""
    __tablename__ = 'webhook_subscriptions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    method = db.Column(db.String(10), nullable=False, default='POST')
    headers = db.Column(db.JSON, nullable=True)
    enabled = db.Column(db.Boolean, default=True)
    alert_types = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'method': self.method,
            'headers': self.headers or {},
            'enabled': self.enabled,
            'alertTypes': self.alert_types,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        } 