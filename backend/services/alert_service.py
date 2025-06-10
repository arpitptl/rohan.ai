from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from utils.logger import logger
import requests
from models.webhook import WebhookSubscription
from models.alert import Alert as AlertModel
from models import db
import json

@dataclass
class AlertMetrics:
    current_rate: float
    historical_avg: float
    deviation: float
    threshold: float

@dataclass
class AlertContext:
    affected_users: int
    business_impact: str
    historical_pattern: str
    peak_hour: int

@dataclass
class Alert:
    alert_id: str
    fip_name: str
    severity: str
    alert_type: str
    message: str
    metrics: AlertMetrics
    context: AlertContext
    recommended_actions: List[str]
    timestamp: str
    confidence: float

class AlertService:
    """Service for generating proactive alerts based on FIP metrics"""
    
    def __init__(self):
        self.logger = logger
        
        # Alert thresholds
        self.thresholds = {
            'consent_success_rate': {
                'critical': 70,
                'warning': 85
            },
            'data_fetch_success_rate': {
                'critical': 65,
                'warning': 80
            },
            'response_time': {
                'critical': 5.0,  # seconds
                'warning': 3.0
            }
        }
        
        # Performance baseline expectations
        self.baselines = {
            'consent_success_rate': 95.0,
            'data_fetch_success_rate': 90.0,
            'response_time': 2.0
        }
    
    def notify_webhooks(self, alert_id: str) -> None:
        """Send alert to all enabled webhook subscriptions"""
        try:
            # Get alert from database
            alert_record = AlertModel.query.filter_by(alert_id=alert_id).first()
            if not alert_record:
                raise ValueError(f"Alert {alert_id} not found")

            # Convert database record to Alert object
            alert = Alert(
                alert_id=alert_record.alert_id,
                fip_name=alert_record.fip_name,
                severity=alert_record.severity,
                alert_type=alert_record.alert_type,
                message=alert_record.message,
                metrics=AlertMetrics(**alert_record.metrics),
                context=AlertContext(**alert_record.context),
                recommended_actions=alert_record.recommended_actions,
                timestamp=alert_record.timestamp.isoformat(),
                confidence=alert_record.confidence
            )
            
            # Get all enabled webhooks that match the alert type
            subscriptions = WebhookSubscription.query.filter_by(enabled=True).all()
            
            for subscription in subscriptions:
                if alert.severity in subscription.alert_types:
                    try:
                        # Prepare notification payload
                        payload = {
                            'alert_id': alert.alert_id,
                            'type': alert.alert_type,
                            'severity': alert.severity,
                            'fip_name': alert.fip_name,
                            'message': alert.message,
                            'metrics': {
                                'current_rate': alert.metrics.current_rate,
                                'historical_avg': alert.metrics.historical_avg,
                                'deviation': alert.metrics.deviation,
                                'threshold': alert.metrics.threshold
                            },
                            'context': {
                                'affected_users': alert.context.affected_users,
                                'business_impact': alert.context.business_impact,
                                'historical_pattern': alert.context.historical_pattern,
                                'peak_hour': alert.context.peak_hour
                            },
                            'timestamp': alert.timestamp,
                            'recommended_actions': alert.recommended_actions
                        }
                        
                        # Send webhook notification
                        response = requests.request(
                            method=subscription.method,
                            url=subscription.url,
                            json=payload,
                            headers=subscription.headers or {},
                            timeout=5
                        )
                        
                        if response.status_code >= 400:
                            self.logger.error(f"Webhook notification failed for {subscription.url}: {response.text}")
                    except Exception as e:
                        self.logger.error(f"Error sending webhook notification to {subscription.url}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in notify_webhooks: {e}")
            raise
    
    def generate_alerts(self, historical_data: Dict, current_metrics: Dict) -> List[Alert]:
        """Generate alerts based on metrics analysis"""
        alerts = []
        
        try:
            # Generate alerts based on current metrics
            for fip_name, metrics in current_metrics.items():
                # Check consent success rate
                if metrics['consent_success_rate'] < self.thresholds['consent_success_rate']['critical']:
                    alert = self._create_alert(
                        fip_name=fip_name,
                        severity='critical',
                        alert_type='consent_success_rate',
                        message=f"Critical: Consent success rate for {fip_name} is {metrics['consent_success_rate']}%, below threshold of {self.thresholds['consent_success_rate']['critical']}%",
                        metrics=AlertMetrics(
                            current_rate=metrics['consent_success_rate'],
                            historical_avg=self.baselines['consent_success_rate'],
                            deviation=metrics['consent_success_rate'] - self.baselines['consent_success_rate'],
                            threshold=self.thresholds['consent_success_rate']['critical']
                        ),
                        context=AlertContext(
                            affected_users=metrics['user_base'],
                            business_impact="High impact on user transactions",
                            historical_pattern=self._analyze_historical_pattern(historical_data, fip_name, 'consent_success_rate'),
                            peak_hour=datetime.utcnow().hour
                        ),
                        recommended_actions=[
                            "Investigate system logs",
                            "Check for recent deployments",
                            "Monitor error rates"
                        ]
                    )
                    alerts.append(alert)
                    self._store_alert(alert)
                elif metrics['consent_success_rate'] < self.thresholds['consent_success_rate']['warning']:
                    alert = self._create_alert(
                        fip_name=fip_name,
                        severity='warning',
                        alert_type='consent_success_rate',
                        message=f"Warning: Consent success rate for {fip_name} is {metrics['consent_success_rate']}%, below threshold of {self.thresholds['consent_success_rate']['warning']}%",
                        metrics=AlertMetrics(
                            current_rate=metrics['consent_success_rate'],
                            historical_avg=self.baselines['consent_success_rate'],
                            deviation=metrics['consent_success_rate'] - self.baselines['consent_success_rate'],
                            threshold=self.thresholds['consent_success_rate']['warning']
                        ),
                        context=AlertContext(
                            affected_users=metrics['user_base'],
                            business_impact="Moderate impact on user transactions",
                            historical_pattern=self._analyze_historical_pattern(historical_data, fip_name, 'consent_success_rate'),
                            peak_hour=datetime.utcnow().hour
                        ),
                        recommended_actions=[
                            "Monitor system performance",
                            "Review error logs",
                            "Prepare for potential escalation"
                        ]
                    )
                    alerts.append(alert)
                    self._store_alert(alert)

                # Check data fetch success rate
                if metrics['data_fetch_success_rate'] < self.thresholds['data_fetch_success_rate']['critical']:
                    alert = self._create_alert(
                        fip_name=fip_name,
                        severity='critical',
                        alert_type='data_fetch_success_rate',
                        message=f"Critical: Data fetch success rate for {fip_name} is {metrics['data_fetch_success_rate']}%, below threshold of {self.thresholds['data_fetch_success_rate']['critical']}%",
                        metrics=AlertMetrics(
                            current_rate=metrics['data_fetch_success_rate'],
                            historical_avg=self.baselines['data_fetch_success_rate'],
                            deviation=metrics['data_fetch_success_rate'] - self.baselines['data_fetch_success_rate'],
                            threshold=self.thresholds['data_fetch_success_rate']['critical']
                        ),
                        context=AlertContext(
                            affected_users=metrics['user_base'],
                            business_impact="High impact on data availability",
                            historical_pattern=self._analyze_historical_pattern(historical_data, fip_name, 'data_fetch_success_rate'),
                            peak_hour=datetime.utcnow().hour
                        ),
                        recommended_actions=[
                            "Check FIP API connectivity",
                            "Verify data fetch endpoints",
                            "Monitor error patterns"
                        ]
                    )
                    alerts.append(alert)
                    self._store_alert(alert)
            
        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
        
        return alerts

    def _create_alert(self, fip_name: str, severity: str, alert_type: str, message: str,
                     metrics: AlertMetrics, context: AlertContext, recommended_actions: List[str]) -> Alert:
        """Create a new alert instance"""
        return Alert(
            alert_id=f"alert_{datetime.utcnow().timestamp()}",
            fip_name=fip_name,
            severity=severity,
            alert_type=alert_type,
            message=message,
            metrics=metrics,
            context=context,
            recommended_actions=recommended_actions,
            timestamp=datetime.utcnow().isoformat(),
            confidence=0.95
        )

    def _store_alert(self, alert: Alert) -> None:
        """Store alert in database"""
        try:
            # Check if alert already exists
            existing_alert = AlertModel.query.filter_by(alert_id=alert.alert_id).first()
            if existing_alert:
                return

            # Create new alert record
            alert_record = AlertModel(
                alert_id=alert.alert_id,
                fip_name=alert.fip_name,
                severity=alert.severity,
                alert_type=alert.alert_type,
                message=alert.message,
                metrics={
                    'current_rate': alert.metrics.current_rate,
                    'historical_avg': alert.metrics.historical_avg,
                    'deviation': alert.metrics.deviation,
                    'threshold': alert.metrics.threshold
                },
                context={
                    'affected_users': alert.context.affected_users,
                    'business_impact': alert.context.business_impact,
                    'historical_pattern': alert.context.historical_pattern,
                    'peak_hour': alert.context.peak_hour
                },
                recommended_actions=alert.recommended_actions,
                timestamp=datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')),
                confidence=alert.confidence
            )
            
            db.session.add(alert_record)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error storing alert in database: {e}")
            db.session.rollback()

    def _analyze_historical_pattern(self, historical_data: Dict, fip_name: str, metric_type: str) -> str:
        """Analyze historical data to detect patterns"""
        try:
            if metric_type not in historical_data:
                return "No historical data available"

            df = historical_data[metric_type]
            if df.empty:
                return "No historical data available"

            fip_data = df[df['fip_name'] == fip_name]
            if fip_data.empty:
                return "No historical data available for this FIP"

            values = fip_data['value'].dropna()
            if len(values) < 2:
                return "Insufficient historical data"

            # Calculate basic trend
            recent_mean = values.iloc[-5:].mean()
            historical_mean = values.iloc[:-5].mean()
            
            if recent_mean < historical_mean * 0.9:
                return "Recent significant decline in performance"
            elif recent_mean > historical_mean * 1.1:
                return "Recent improvement in performance"
            else:
                return "Stable performance pattern"

        except Exception as e:
            self.logger.error(f"Error analyzing historical pattern: {e}")
            return "Error analyzing historical pattern"

    def _get_fip_historical_data(self, historical_data: Dict[str, pd.DataFrame], 
                                fip_name: str) -> Dict[str, pd.DataFrame]:
        """Extract historical data for specific FIP"""
        fip_data = {}
        
        for metric_name, df in historical_data.items():
            if not df.empty:
                fip_df = df[df['fip_name'] == fip_name].copy()
                if not fip_df.empty:
                    fip_data[metric_name] = fip_df
        
        return fip_data
    
    def _check_performance_degradation(self, fip_name: str, current_metrics: Dict,
                                     historical_data: Dict[str, pd.DataFrame]) -> List[Alert]:
        """Check for sudden performance degradation"""
        alerts = []
        
        # Check consent success rate
        if 'consent_success_rate' in historical_data:
            current_rate = current_metrics.get('consent_success_rate', 0)
            historical_avg = historical_data['consent_success_rate']['value'].mean()
            deviation = current_rate - historical_avg
            
            if current_rate < self.thresholds['consent_success_rate']['critical']:
                alerts.append(self._create_alert(
                    fip_name=fip_name,
                    severity='critical',
                    alert_type='performance_degradation',
                    message=f"Severe drop in consent success rate: {current_rate:.1f}% (historical avg: {historical_avg:.1f}%)",
                    metrics=AlertMetrics(
                        current_rate=current_rate,
                        historical_avg=historical_avg,
                        deviation=deviation,
                        threshold=self.thresholds['consent_success_rate']['critical']
                    ),
                    context=self._get_alert_context(fip_name, current_metrics, historical_data),
                    recommended_actions=[
                        "Investigate authentication service health",
                        "Check for API throttling issues",
                        "Monitor error logs for authentication failures"
                    ],
                    confidence=0.95
                ))
            elif current_rate < self.thresholds['consent_success_rate']['warning']:
                alerts.append(self._create_alert(
                    fip_name=fip_name,
                    severity='warning',
                    alert_type='performance_degradation',
                    message=f"Consent success rate below threshold: {current_rate:.1f}% (historical avg: {historical_avg:.1f}%)",
                    metrics=AlertMetrics(
                        current_rate=current_rate,
                        historical_avg=historical_avg,
                        deviation=deviation,
                        threshold=self.thresholds['consent_success_rate']['warning']
                    ),
                    context=self._get_alert_context(fip_name, current_metrics, historical_data),
                    recommended_actions=[
                        "Monitor consent flow closely",
                        "Prepare for potential intervention"
                    ],
                    confidence=0.85
                ))
        
        return alerts
    
    def _check_pattern_anomalies(self, fip_name: str, current_metrics: Dict,
                                historical_data: Dict[str, pd.DataFrame]) -> List[Alert]:
        """Check for anomalies in performance patterns"""
        alerts = []
        current_hour = datetime.utcnow().hour
        
        # Check for unusual combinations
        consent_rate = current_metrics.get('consent_success_rate', 0)
        data_fetch_rate = current_metrics.get('data_fetch_success_rate', 0)
        
        if consent_rate > 90 and data_fetch_rate < 60:
            alerts.append(self._create_alert(
                fip_name=fip_name,
                severity='warning',
                alert_type='pattern_anomaly',
                message=f"Unusual pattern: High consent success ({consent_rate:.1f}%) but low data fetch success ({data_fetch_rate:.1f}%)",
                metrics=AlertMetrics(
                    current_rate=data_fetch_rate,
                    historical_avg=consent_rate,
                    deviation=consent_rate - data_fetch_rate,
                    threshold=80.0
                ),
                context=self._get_alert_context(fip_name, current_metrics, historical_data),
                recommended_actions=[
                    "Investigate data fetch service",
                    "Check data fetch API permissions",
                    "Verify data availability at source"
                ],
                confidence=0.88
            ))
        
        return alerts
    
    def _check_trend_issues(self, fip_name: str, current_metrics: Dict,
                           historical_data: Dict[str, pd.DataFrame]) -> List[Alert]:
        """Check for concerning trends in metrics"""
        alerts = []
        
        # Check for consistent decline in success rates
        if 'consent_success_rate' in historical_data:
            df = historical_data['consent_success_rate']
            recent_trend = self._calculate_trend(df['value'].tail(6))  # Last hour assuming 10-min intervals
            
            if recent_trend < -0.1:  # 10% decline per hour
                alerts.append(self._create_alert(
                    fip_name=fip_name,
                    severity='warning',
                    alert_type='negative_trend',
                    message=f"Consistent decline in consent success rate (trend: {recent_trend:.1%} per hour)",
                    metrics=AlertMetrics(
                        current_rate=current_metrics.get('consent_success_rate', 0),
                        historical_avg=df['value'].mean(),
                        deviation=recent_trend,
                        threshold=-0.1
                    ),
                    context=self._get_alert_context(fip_name, current_metrics, historical_data),
                    recommended_actions=[
                        "Monitor trend closely",
                        "Investigate root cause of decline",
                        "Prepare for intervention if trend continues"
                    ],
                    confidence=0.82
                ))
        
        return alerts
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate trend as rate of change per hour"""
        if len(series) < 2:
            return 0.0
        
        try:
            x = np.arange(len(series))
            y = series.values
            slope, _ = np.polyfit(x, y, 1)
            return slope * len(series)  # Scale to per-hour rate
        except Exception:
            return 0.0
    
    def _get_alert_context(self, fip_name: str, current_metrics: Dict,
                          historical_data: Dict[str, pd.DataFrame]) -> AlertContext:
        """Get context information for alert"""
        current_hour = datetime.utcnow().hour
        peak_hours = [9, 10, 11, 14, 15, 16]  # Business hours
        
        return AlertContext(
            affected_users=current_metrics.get('user_base', 0),
            business_impact='high' if current_hour in peak_hours else 'medium',
            historical_pattern=self._get_historical_pattern(historical_data),
            peak_hour=current_hour in peak_hours
        )
    
    def _get_historical_pattern(self, historical_data: Dict[str, pd.DataFrame]) -> str:
        """Analyze historical pattern"""
        if 'consent_success_rate' in historical_data:
            df = historical_data['consent_success_rate']
            current_hour = datetime.utcnow().hour
            
            # Get average for this hour
            hourly_avg = df.groupby(df.index.hour)['value'].mean()
            if current_hour in hourly_avg.index:
                if df['value'].iloc[-1] < hourly_avg[current_hour] * 0.9:
                    return "Significantly below average for this hour"
                elif df['value'].iloc[-1] > hourly_avg[current_hour] * 1.1:
                    return "Significantly above average for this hour"
        
        return "Within normal range" 