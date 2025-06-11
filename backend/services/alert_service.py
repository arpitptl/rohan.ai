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

        # Time windows for analysis (in minutes)
        self.time_windows = {
            'short_term': 180,  # 3 hours
            'medium_term': 720,  # 12 hours
            'long_term': 1440   # 24 hours
        }

        # Trend thresholds (percentage change)
        self.trend_thresholds = {
            'rapid_decline': -10.0,  # 10% decline in 3 hours
            'gradual_decline': -5.0,  # 5% decline in 3 hours
            'improvement': 5.0        # 5% improvement
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
        """Generate alerts based on metrics analysis with focus on last 3 hours"""
        alerts = []
        
        try:
            # Process each FIP
            for fip_name, metrics in current_metrics.items():
                # Get time-sliced data for different windows
                short_term_data = self._get_time_sliced_data(historical_data, fip_name, self.time_windows['short_term'])
                
                # Generate different types of alerts
                alerts.extend(self._check_threshold_violations(fip_name, metrics, short_term_data))
                alerts.extend(self._check_trend_anomalies(fip_name, metrics, short_term_data))
                alerts.extend(self._check_pattern_anomalies(fip_name, metrics, short_term_data))
                alerts.extend(self._check_stability_issues(fip_name, metrics, short_term_data))
                
                # Deduplicate alerts
                alerts = self._deduplicate_alerts(alerts)
                
                # Sort by severity and confidence
                alerts.sort(key=lambda x: (x.severity == 'critical', x.confidence), reverse=True)
                
        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
        
        return alerts

    def _get_time_sliced_data(self, historical_data: Dict, fip_name: str, minutes: int) -> Dict[str, pd.DataFrame]:
        """Get data for specified time window"""
        sliced_data = {}
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        for metric_name, df in historical_data.items():
            if not df.empty:
                # Filter for FIP and time window
                mask = (df['fip_name'] == fip_name) & (df.index >= cutoff_time)
                sliced_data[metric_name] = df[mask].copy()
        
        return sliced_data

    def _check_threshold_violations(self, fip_name: str, current_metrics: Dict, 
                                  short_term_data: Dict[str, pd.DataFrame]) -> List[Alert]:
        """Check for immediate threshold violations with short-term context"""
        alerts = []
        
        # Check consent success rate
        current_consent_rate = current_metrics.get('consent_success_rate', 0)
        if current_consent_rate < self.thresholds['consent_success_rate']['critical']:
            # Calculate short-term trend
            if 'consent_success_rate' in short_term_data:
                df = short_term_data['consent_success_rate']
                trend = self._calculate_trend(df['value']) if not df.empty else 0
                
                severity = 'critical' if trend < self.trend_thresholds['rapid_decline'] else 'warning'
                confidence = 0.95 if trend < self.trend_thresholds['rapid_decline'] else 0.85
                
                alert = self._create_alert(
                    fip_name=fip_name,
                    severity=severity,
                    alert_type='consent_rate_violation',
                    message=self._generate_threshold_message(fip_name, current_consent_rate, trend),
                    metrics=AlertMetrics(
                        current_rate=current_consent_rate,
                        historical_avg=df['value'].mean() if not df.empty else self.baselines['consent_success_rate'],
                        deviation=trend,
                        threshold=self.thresholds['consent_success_rate']['critical']
                    ),
                    context=self._get_enhanced_context(fip_name, current_metrics, short_term_data),
                    recommended_actions=self._get_recommended_actions('consent_rate', severity, trend)
                )
                alerts.append(alert)
        
        # Similar checks for data fetch rate
        current_fetch_rate = current_metrics.get('data_fetch_success_rate', 0)
        if current_fetch_rate < self.thresholds['data_fetch_success_rate']['critical']:
            if 'data_fetch_success_rate' in short_term_data:
                df = short_term_data['data_fetch_success_rate']
                trend = self._calculate_trend(df['value']) if not df.empty else 0
                
                alert = self._create_alert(
                    fip_name=fip_name,
                    severity='critical' if trend < self.trend_thresholds['rapid_decline'] else 'warning',
                    alert_type='data_fetch_violation',
                    message=self._generate_threshold_message(fip_name, current_fetch_rate, trend, metric_type='data fetch'),
                    metrics=AlertMetrics(
                        current_rate=current_fetch_rate,
                        historical_avg=df['value'].mean() if not df.empty else self.baselines['data_fetch_success_rate'],
                        deviation=trend,
                        threshold=self.thresholds['data_fetch_success_rate']['critical']
                    ),
                    context=self._get_enhanced_context(fip_name, current_metrics, short_term_data),
                    recommended_actions=self._get_recommended_actions('data_fetch', 'critical' if trend < self.trend_thresholds['rapid_decline'] else 'warning', trend)
                )
                alerts.append(alert)
        
        return alerts

    def _check_trend_anomalies(self, fip_name: str, current_metrics: Dict, 
                              short_term_data: Dict[str, pd.DataFrame]) -> List[Alert]:
        """Analyze trends in the last 3 hours"""
        alerts = []
        
        for metric_name in ['consent_success_rate', 'data_fetch_success_rate']:
            if metric_name in short_term_data:
                df = short_term_data[metric_name]
                if not df.empty:
                    # Calculate trend using rolling windows
                    window_sizes = [30, 60, 180]  # 30min, 1hr, 3hr windows
                    trends = []
                    
                    for window in window_sizes:
                        trend = self._calculate_rolling_trend(df['value'], window)
                        trends.append(trend)
                    
                    # Check for accelerating decline
                    if all(t < 0 for t in trends) and trends[0] < trends[1] < trends[2]:
                        alert = self._create_alert(
                            fip_name=fip_name,
                            severity='warning',
                            alert_type='accelerating_decline',
                            message=f"Accelerating decline detected in {metric_name.replace('_', ' ')}: -"
                                   f"{abs(trends[0]):.1f}% (30min), -{abs(trends[1]):.1f}% (1hr), -{abs(trends[2]):.1f}% (3hr)",
                            metrics=AlertMetrics(
                                current_rate=current_metrics.get(metric_name, 0),
                                historical_avg=df['value'].mean(),
                                deviation=trends[0],
                                threshold=self.trend_thresholds['rapid_decline']
                            ),
                            context=self._get_enhanced_context(fip_name, current_metrics, short_term_data),
                            recommended_actions=self._get_recommended_actions(metric_name, 'warning', trends[0])
                        )
                        alerts.append(alert)
        
        return alerts

    def _check_pattern_anomalies(self, fip_name: str, current_metrics: Dict,
                                short_term_data: Dict[str, pd.DataFrame]) -> List[Alert]:
        """Check for unusual patterns in metrics"""
        alerts = []
        
        # Check for diverging metrics
        consent_rate = current_metrics.get('consent_success_rate', 0)
        data_fetch_rate = current_metrics.get('data_fetch_success_rate', 0)
        
        if abs(consent_rate - data_fetch_rate) > 20:  # Significant divergence
            worse_metric = 'consent' if consent_rate < data_fetch_rate else 'data fetch'
            better_metric = 'data fetch' if consent_rate < data_fetch_rate else 'consent'
            
            alert = self._create_alert(
                fip_name=fip_name,
                severity='warning',
                alert_type='metric_divergence',
                message=f"Unusual pattern: {worse_metric} rate ({min(consent_rate, data_fetch_rate):.1f}%) "
                       f"significantly lower than {better_metric} rate ({max(consent_rate, data_fetch_rate):.1f}%)",
                metrics=AlertMetrics(
                    current_rate=min(consent_rate, data_fetch_rate),
                    historical_avg=max(consent_rate, data_fetch_rate),
                    deviation=abs(consent_rate - data_fetch_rate),
                    threshold=20.0
                ),
                context=self._get_enhanced_context(fip_name, current_metrics, short_term_data),
                recommended_actions=[
                    f"Investigate {worse_metric} service health",
                    f"Check {worse_metric} API endpoints",
                    "Review error logs for specific failure patterns",
                    "Monitor service dependencies"
                ]
            )
            alerts.append(alert)
        
        return alerts

    def _check_stability_issues(self, fip_name: str, current_metrics: Dict,
                               short_term_data: Dict[str, pd.DataFrame]) -> List[Alert]:
        """Check for stability issues in the last 3 hours"""
        alerts = []
        
        for metric_name in ['consent_success_rate', 'data_fetch_success_rate']:
            if metric_name in short_term_data:
                df = short_term_data[metric_name]
                if not df.empty:
                    # Calculate volatility
                    volatility = df['value'].std()
                    mean_value = df['value'].mean()
                    cv = (volatility / mean_value) * 100 if mean_value > 0 else 0
                    
                    if cv > 15:  # High coefficient of variation
                        alert = self._create_alert(
                            fip_name=fip_name,
                            severity='warning',
                            alert_type='stability_issue',
                            message=f"High variability in {metric_name.replace('_', ' ')}: "
                                   f"±{volatility:.1f}% around mean of {mean_value:.1f}%",
                            metrics=AlertMetrics(
                                current_rate=current_metrics.get(metric_name, 0),
                                historical_avg=mean_value,
                                deviation=volatility,
                                threshold=15.0
                            ),
                            context=self._get_enhanced_context(fip_name, current_metrics, short_term_data),
                            recommended_actions=[
                                "Monitor service stability",
                                "Check for intermittent issues",
                                "Review system resources",
                                "Investigate potential network issues"
                            ]
                        )
                        alerts.append(alert)
        
        return alerts

    def _calculate_rolling_trend(self, series: pd.Series, window_minutes: int) -> float:
        """Calculate trend using rolling windows"""
        if len(series) < 2:
            return 0.0
        
        try:
            rolling_mean = series.rolling(window=window_minutes//5).mean()  # Assuming 5-minute intervals
            if len(rolling_mean) >= 2:
                return ((rolling_mean.iloc[-1] - rolling_mean.iloc[0]) / rolling_mean.iloc[0]) * 100
            return 0.0
        except Exception:
            return 0.0

    def _generate_threshold_message(self, fip_name: str, current_rate: float, trend: float, 
                                  metric_type: str = 'consent') -> str:
        """Generate detailed alert message"""
        trend_desc = "declining rapidly" if trend < self.trend_thresholds['rapid_decline'] else \
                    "declining gradually" if trend < 0 else "stable"
        
        return (f"Critical: {metric_type} success rate for {fip_name} is {current_rate:.1f}%, "
                f"below threshold and {trend_desc} (trend: {trend:.1f}% over 3 hours)")

    def _get_enhanced_context(self, fip_name: str, current_metrics: Dict,
                            short_term_data: Dict[str, pd.DataFrame]) -> AlertContext:
        """Get enhanced context with short-term analysis"""
        current_hour = datetime.utcnow().hour
        is_business_hours = 9 <= current_hour <= 18
        
        # Calculate user impact
        base_users = current_metrics.get('user_base', 0)
        affected_users = int(base_users * (1 - current_metrics.get('consent_success_rate', 0) / 100))
        
        # Determine business impact
        if is_business_hours and affected_users > base_users * 0.3:
            business_impact = "Severe impact on business operations during peak hours"
        elif is_business_hours:
            business_impact = "Moderate impact on business operations"
        else:
            business_impact = "Limited business impact during off-hours"
        
        return AlertContext(
            affected_users=affected_users,
            business_impact=business_impact,
            historical_pattern=self._analyze_short_term_pattern(short_term_data),
            peak_hour=is_business_hours
        )

    def _analyze_short_term_pattern(self, short_term_data: Dict[str, pd.DataFrame]) -> str:
        """Analyze pattern in short-term data"""
        patterns = []
        
        for metric_name, df in short_term_data.items():
            if not df.empty:
                recent_std = df['value'].std()
                recent_trend = self._calculate_trend(df['value'])
                
                if recent_std > 10:
                    patterns.append("highly variable")
                elif recent_trend < -5:
                    patterns.append("declining")
                elif recent_trend > 5:
                    patterns.append("improving")
                else:
                    patterns.append("stable")
        
        if not patterns:
            return "Insufficient short-term data"
        
        # Return most severe pattern
        if "highly variable" in patterns:
            return "Highly variable performance in last 3 hours"
        elif "declining" in patterns:
            return "Declining performance trend in last 3 hours"
        elif "improving" in patterns:
            return "Improving performance trend in last 3 hours"
        else:
            return "Stable performance in last 3 hours"

    def _get_recommended_actions(self, metric_type: str, severity: str, trend: float) -> List[str]:
        """Get context-aware recommended actions"""
        actions = []
        
        if severity == 'critical':
            actions.extend([
                "Immediately investigate system logs",
                "Check for recent deployments or changes",
                "Monitor error rates and patterns",
                "Prepare incident response if trend continues"
            ])
        else:
            actions.extend([
                "Monitor system performance",
                "Review error logs for patterns",
                "Prepare for potential escalation"
            ])
        
        if trend < self.trend_thresholds['rapid_decline']:
            actions.extend([
                "Analyze recent system changes",
                "Check service dependencies",
                "Review capacity metrics"
            ])
        
        if metric_type == 'consent_rate':
            actions.extend([
                "Verify authentication service health",
                "Check consent flow configuration"
            ])
        elif metric_type == 'data_fetch':
            actions.extend([
                "Check data source connectivity",
                "Verify API permissions and quotas"
            ])
        
        return actions[:5]  # Return top 5 most relevant actions

    def _deduplicate_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """Remove duplicate or similar alerts"""
        unique_alerts = []
        seen_combinations = set()
        
        for alert in alerts:
            # Create a unique key for similar alerts
            key = f"{alert.fip_name}:{alert.alert_type}:{alert.severity}"
            
            if key not in seen_combinations:
                unique_alerts.append(alert)
                seen_combinations.add(key)
        
        return unique_alerts

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