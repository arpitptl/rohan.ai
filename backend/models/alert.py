from datetime import datetime
import json
from . import db

class Alert(db.Model):
    """Store alerts in database"""
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(100), unique=True, nullable=False)
    fip_name = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # critical, warning, info
    alert_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    metrics = db.Column(db.JSON, nullable=False)  # Store metrics as JSON
    context = db.Column(db.JSON, nullable=False)  # Store context as JSON
    recommended_actions = db.Column(db.JSON, nullable=False)  # Store actions as JSON array
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    confidence = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, resolved
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)

    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'fip_name': self.fip_name,
            'severity': self.severity,
            'alert_type': self.alert_type,
            'message': self.message,
            'metrics': self.metrics,
            'context': self.context,
            'recommended_actions': self.recommended_actions,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence,
            'status': self.status,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_note': self.resolution_note
        } 