from datetime import datetime
from utils import PredictionType, FIPStatus
from . import db

class Prediction(db.Model):
    """Store AI predictions for FIPs"""
    id = db.Column(db.Integer, primary_key=True)
    fip_name = db.Column(db.String(50), nullable=False)
    prediction_type = db.Column(db.Enum(PredictionType), nullable=False)
    probability = db.Column(db.Float, nullable=False)
    time_window = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.String(20), nullable=False)  # high, medium, low
    raw_prediction = db.Column(db.Text)  # JSON string of full prediction
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fip_name': self.fip_name,
            'prediction_type': self.prediction_type.value,
            'probability': self.probability,
            'time_window': self.time_window,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat()
        }

class FIPMetrics(db.Model):
    """Store FIP performance metrics"""
    id = db.Column(db.Integer, primary_key=True)
    fip_name = db.Column(db.String(50), nullable=False)
    consent_success_rate = db.Column(db.Float, nullable=False)
    data_fetch_success_rate = db.Column(db.Float, nullable=False)
    avg_response_time = db.Column(db.Float, nullable=False)
    error_rate = db.Column(db.Float, nullable=False)
    current_status = db.Column(db.Enum(FIPStatus), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'fip_name': self.fip_name,
            'consent_success_rate': self.consent_success_rate,
            'data_fetch_success_rate': self.data_fetch_success_rate,
            'avg_response_time': self.avg_response_time,
            'error_rate': self.error_rate,
            'current_status': self.current_status.value,
            'timestamp': self.timestamp.isoformat()
        }