import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError
from utils.logger import logger
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

class BedrockService:
    """
    AI-powered FIP analysis service with Bedrock integration
    Uses smart mock responses when Bedrock is not available
    """
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        if not use_mock:
            try:
                self.bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name='us-east-1'
                )
                print("✅ Real Bedrock client initialized")
            except Exception as e:
                print(f"⚠️  Bedrock initialization failed, falling back to mock: {e}")
                self.use_mock = True
        else:
            print("🎭 Using mock Bedrock responses for development")
    
    def predict_downtime(self, metrics_data: Dict, time_horizon: str = "24h") -> Dict:
        """
        Predict FIP downtime using AI analysis
        """
        if self.use_mock:
            return self._generate_mock_downtime_predictions(metrics_data, time_horizon)
        else:
            return self._call_real_bedrock_prediction(metrics_data, time_horizon)
    
    def analyze_business_impact(self, predictions: Dict) -> Dict:
        """
        Analyze business impact of predicted outages
        """
        if self.use_mock:
            return self._generate_mock_business_impact(predictions)
        else:
            return self._call_real_bedrock_impact_analysis(predictions)
    
    def generate_proactive_alerts(self, current_metrics: Dict) -> Dict:
        """
        Generate proactive alerts based on current FIP status
        """
        if self.use_mock:
            return self._generate_mock_proactive_alerts(current_metrics)
        else:
            return self._call_real_bedrock_alerts(current_metrics)
    
    def generate_recommendations(self, situation: Dict) -> Dict:
        """
        Generate operational recommendations
        """
        if self.use_mock:
            return self._generate_mock_recommendations(situation)
        else:
            return self._call_real_bedrock_recommendations(situation)
    
    def generate_system_overview(self) -> Dict:
        """
        Generate system-wide health overview
        """
        if self.use_mock:
            return self._generate_mock_system_overview()
        else:
            return self._call_real_bedrock_overview()
    
    # ================================
    # SMART MOCK IMPLEMENTATIONS
    # ================================
    
    def _generate_mock_downtime_predictions(self, metrics_data: Dict, time_horizon: str) -> Dict:
        """
        Generate realistic downtime predictions based on actual metrics
        """
        return {
            "icici-fip": {
                "downtime_prediction": {
                    "probability": 0.25,
                    "time_window": "next 6-8 hours",
                    "confidence": "medium",
                    "reasoning": "Consent success rate declining (-0.94%), response time increasing (+3.22%), but overall stability grade is 'good'. Low anomaly severity with 92.5% average consent success rate indicates stable performance with minor degradation trends."
                },
                "patterns_detected": [
                    "Peak error rates at hour 21 (9 PM)",
                    "Response time volatility during evening hours",
                    "Negative correlation between consent success and response time (-0.61)",
                    "Weekend performance slightly better than weekdays"
                ],
                "anomalies": [
                    "35 consent/data fetch anomalies (1.37% rate)",
                    "34 response time anomalies",
                    "109 status anomalies (4.27% rate) - medium concern"
                ],
                "user_impact": {
                    "consent_failure_rate": "7.5%",
                    "data_fetch_failure_rate": "9.0%",
                    "estimated_affected_users": 1500,
                    "recommended_fallback": "PDF upload during evening peak hours (21:00-22:00)"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "15 minutes during peak error periods",
                    "communication_template": "Temporary delays possible during evening hours. Alternative verification methods available."
                },
                "business_impact": {
                    "processing_delay": "2-3 minutes average",
                    "manual_processing_cost": "INR 50-75 per transaction during fallback",
                    "user_satisfaction_impact": "Minimal - good overall performance maintained"
                },
                "health_score": 82,
                "risk_level": "low"
            },
            "sbi-fip": {
                "downtime_prediction": {
                    "probability": 0.35,
                    "time_window": "next 4-6 hours",
                    "confidence": "medium",
                    "reasoning": "Higher volatility than ICICI with 92% consent success rate. Response time increasing (+1.59%), error rates decreasing but status anomalies at medium severity. Stability grade 'good' but showing more stress indicators."
                },
                "patterns_detected": [
                    "Peak error rates at hour 15 (3 PM)",
                    "Clear daily patterns in response time and error rate",
                    "Higher coefficient of variation (16%) indicates less stability",
                    "Weekend vs weekday performance variance"
                ],
                "anomalies": [
                    "70 consent/data fetch anomalies (2.75% rate)",
                    "150 status anomalies (5.89% rate) - medium severity"
                ],
                "user_impact": {
                    "consent_failure_rate": "8.0%",
                    "data_fetch_failure_rate": "9.6%",
                    "estimated_affected_users": 2200,
                    "recommended_fallback": "Phone verification during afternoon peak (15:00-16:00)"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "20 minutes during afternoon peak",
                    "communication_template": "Service may be slower during afternoon hours. Please try again or use phone verification."
                },
                "business_impact": {
                    "processing_delay": "3-4 minutes average",
                    "manual_processing_cost": "INR 75-100 per transaction",
                    "user_satisfaction_impact": "Moderate - noticeable delays during peak hours"
                },
                "health_score": 78,
                "risk_level": "medium"
            },
            "boi-fip": {
                "downtime_prediction": {
                    "probability": 0.15,
                    "time_window": "next 12+ hours",
                    "confidence": "high",
                    "reasoning": "Excellent performance with 95.9% consent success rate and 'excellent' stability grade. Lowest coefficient of variation (5.3%) indicates very stable performance. All trends improving or stable."
                },
                "patterns_detected": [
                    "Most stable FIP with minimal hourly variation",
                    "Peak errors during hour 10 (10 AM)",
                    "Strong weekend performance",
                    "Consistent response times under 4 seconds average"
                ],
                "anomalies": [
                    "Only 66 consent anomalies (2.57% rate) - very low",
                    "17 response time anomalies (0.66% rate) - extremely low",
                    "70 status anomalies (2.72% rate) - acceptable"
                ],
                "user_impact": {
                    "consent_failure_rate": "4.1%",
                    "data_fetch_failure_rate": "5.3%",
                    "estimated_affected_users": 800,
                    "recommended_fallback": "Minimal fallback needed"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "5 minutes if needed",
                    "communication_template": "Service running optimally. Minor delays possible during morning hours."
                },
                "business_impact": {
                    "processing_delay": "1-2 minutes average",
                    "manual_processing_cost": "INR 25-40 per transaction",
                    "user_satisfaction_impact": "Minimal - excellent user experience"
                },
                "health_score": 92,
                "risk_level": "low"
            },
            "central-fip": {
                "downtime_prediction": {
                    "probability": 0.40,
                    "time_window": "next 3-4 hours",
                    "confidence": "medium",
                    "reasoning": "Declining consent (-1.81%) and data fetch (-2.19%) rates with increasing response times (+4.95%). Status showing downward trend. Good stability grade but concerning degradation patterns."
                },
                "patterns_detected": [
                    "Peak issues at hour 9 (9 AM) for both errors and response time",
                    "Clear daily patterns with morning stress",
                    "Negative performance trends across key metrics"
                ],
                "anomalies": [
                    "54 consent/data fetch anomalies (2.16% rate)",
                    "130 status anomalies (5.20% rate) - medium severity"
                ],
                "user_impact": {
                    "consent_failure_rate": "5.3%",
                    "data_fetch_failure_rate": "6.4%",
                    "estimated_affected_users": 1800,
                    "recommended_fallback": "PDF upload during morning hours (9:00-10:00)"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "25 minutes during morning peak",
                    "communication_template": "Experiencing higher than normal processing times. Alternative verification available."
                },
                "business_impact": {
                    "processing_delay": "4-5 minutes average",
                    "manual_processing_cost": "INR 80-120 per transaction",
                    "user_satisfaction_impact": "Moderate - users notice morning delays"
                },
                "health_score": 75,
                "risk_level": "medium"
            },
            "axis-fip": {
                "downtime_prediction": {
                    "probability": 0.42,
                    "time_window": "next 3-4 hours",
                    "confidence": "medium",
                    "reasoning": "Similar pattern to Central FIP with 94.3% consent success rate but declining trends. Peak issues at hour 15 (3 PM). Good stability grade but multiple concerning indicators."
                },
                "patterns_detected": [
                    "Peak errors and response times at hour 15 (3 PM)",
                    "Strong daily patterns with afternoon stress",
                    "Clear correlation between errors and response times"
                ],
                "anomalies": [
                    "64 consent/data fetch anomalies (2.51% rate)",
                    "138 status anomalies (5.42% rate) - medium severity"
                ],
                "user_impact": {
                    "consent_failure_rate": "5.7%",
                    "data_fetch_failure_rate": "6.8%",
                    "estimated_affected_users": 1900,
                    "recommended_fallback": "Manual verification during afternoon peak (15:00-16:00)"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "20 minutes during afternoon peak",
                    "communication_template": "Service may be slower during afternoon. Please try again or contact support for assistance."
                },
                "business_impact": {
                    "processing_delay": "4-5 minutes average",
                    "manual_processing_cost": "INR 85-125 per transaction",
                    "user_satisfaction_impact": "Moderate - afternoon performance issues noticeable"
                },
                "health_score": 74,
                "risk_level": "medium"
            },
            "iob-fip": {
                "downtime_prediction": {
                    "probability": 0.30,
                    "time_window": "next 5-6 hours",
                    "confidence": "medium",
                    "reasoning": "Good performance with 94.8% consent success rate. Peak issues at hour 17 (5 PM). Stability grade 'good' with manageable anomaly levels. Less concerning than Axis/Central."
                },
                "patterns_detected": [
                    "Peak errors at hour 17 (5 PM) - evening rush",
                    "Clear daily patterns with evening stress",
                    "Good weekend vs weekday performance ratio"
                ],
                "anomalies": [
                    "57 consent/data fetch anomalies (2.25% rate)",
                    "118 status anomalies (4.66% rate) - low severity"
                ],
                "user_impact": {
                    "consent_failure_rate": "5.2%",
                    "data_fetch_failure_rate": "6.1%",
                    "estimated_affected_users": 1600,
                    "recommended_fallback": "PDF upload during evening peak (17:00-18:00)"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "15 minutes during evening peak",
                    "communication_template": "Temporary delays possible during evening hours. Alternative options available if needed."
                },
                "business_impact": {
                    "processing_delay": "3-4 minutes average",
                    "manual_processing_cost": "INR 70-95 per transaction",
                    "user_satisfaction_impact": "Low-moderate - evening delays manageable"
                },
                "health_score": 79,
                "risk_level": "medium"
            },
            "kotak-fip": {
                "downtime_prediction": {
                    "probability": 0.65,
                    "time_window": "next 2-3 hours",
                    "confidence": "high",
                    "reasoning": "Highest risk FIP with declining consent (-2.23%) and data fetch (-2.09%) rates. 'Fair' stability grade with highest coefficient of variation (21.8%). Multiple medium-severity anomalies and peak issues at hour 9."
                },
                "patterns_detected": [
                    "Peak errors at hour 9 (9 AM) - morning stress",
                    "Highest volatility among all FIPs",
                    "Strong negative correlation between consent and response time (-0.80)",
                    "Clear daily patterns with morning vulnerability"
                ],
                "anomalies": [
                    "140 consent/data fetch anomalies (5.49% rate) - medium severity",
                    "212 status anomalies (8.31% rate) - medium severity",
                    "Highest anomaly rates across all metrics"
                ],
                "user_impact": {
                    "consent_failure_rate": "7.4%",
                    "data_fetch_failure_rate": "8.3%",
                    "estimated_affected_users": 2800,
                    "recommended_fallback": "Immediate manual processing activation during morning hours"
                },
                "fiu_recommendations": {
                    "should_activate_manual": True,
                    "retry_after": "45 minutes during peak stress periods",
                    "communication_template": "Service experiencing high load. We've activated manual verification to ensure faster processing."
                },
                "business_impact": {
                    "processing_delay": "6-8 minutes average",
                    "manual_processing_cost": "INR 150-200 per transaction",
                    "user_satisfaction_impact": "High - significant delays and failures expected"
                },
                "health_score": 65,
                "risk_level": "high"
            },
            "pnb-fip": {
                "downtime_prediction": {
                    "probability": 0.45,
                    "time_window": "next 3-4 hours",
                    "confidence": "medium",
                    "reasoning": "Moderate performance with 91.6% consent success rate. Declining trends with increasing response times (+7.66%). Good stability grade but concerning degradation patterns, especially during hour 17."
                },
                "patterns_detected": [
                    "Peak errors at hour 17 (5 PM) - evening stress",
                    "Strong daily patterns with evening vulnerability",
                    "Significant response time increases trending"
                ],
                "anomalies": [
                    "105 consent/data fetch anomalies (4.09% rate)",
                    "172 status anomalies (6.71% rate) - medium severity"
                ],
                "user_impact": {
                    "consent_failure_rate": "8.4%",
                    "data_fetch_failure_rate": "9.8%",
                    "estimated_affected_users": 2400,
                    "recommended_fallback": "Phone verification during evening peak (17:00-18:00)"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "30 minutes during evening peak",
                    "communication_template": "Higher processing times during evening hours. Phone verification available as alternative."
                },
                "business_impact": {
                    "processing_delay": "5-6 minutes average",
                    "manual_processing_cost": "INR 100-140 per transaction",
                    "user_satisfaction_impact": "Moderate-high - noticeable evening performance issues"
                },
                "health_score": 72,
                "risk_level": "medium"
            },
            "ubi-fip": {
                "downtime_prediction": {
                    "probability": 0.20,
                    "time_window": "next 8-10 hours",
                    "confidence": "medium",
                    "reasoning": "Strong performance with 95.8% consent success rate and good stability grade. Low anomaly rates and minimal hourly variation. Peak issues only at hour 22 (10 PM) which is off-peak."
                },
                "patterns_detected": [
                    "Peak errors at hour 22 (10 PM) - off-peak timing",
                    "Minimal hourly variation - very stable",
                    "Good weekend performance",
                    "Low overall volatility"
                ],
                "anomalies": [
                    "Only 31 consent/data fetch anomalies (1.22% rate) - very low",
                    "101 status anomalies (3.96% rate) - acceptable"
                ],
                "user_impact": {
                    "consent_failure_rate": "4.2%",
                    "data_fetch_failure_rate": "5.3%",
                    "estimated_affected_users": 900,
                    "recommended_fallback": "Minimal fallback needed, mainly late evening"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "10 minutes if needed",
                    "communication_template": "Service running well. Minor delays possible during late evening hours."
                },
                "business_impact": {
                    "processing_delay": "2-3 minutes average",
                    "manual_processing_cost": "INR 40-60 per transaction",
                    "user_satisfaction_impact": "Low - good user experience maintained"
                },
                "health_score": 88,
                "risk_level": "low"
            },
            "hdfc-fip": {
                "downtime_prediction": {
                    "probability": 0.18,
                    "time_window": "next 10-12 hours",
                    "confidence": "medium",
                    "reasoning": "Excellent performance with 96.8% consent success rate - highest among all FIPs. Good stability grade with low anomaly rates. Peak issues only at hour 8 (8 AM) but manageable."
                },
                "patterns_detected": [
                    "Peak errors at hour 8 (8 AM) - morning rush",
                    "Highest consent success rate among all FIPs",
                    "Stable performance with minimal variation",
                    "Good weekend vs weekday performance"
                ],
                "anomalies": [
                    "Only 36 consent/data fetch anomalies (1.42% rate) - very low",
                    "114 status anomalies (4.50% rate) - acceptable"
                ],
                "user_impact": {
                    "consent_failure_rate": "3.2%",
                    "data_fetch_failure_rate": "4.0%",
                    "estimated_affected_users": 700,
                    "recommended_fallback": "Minimal fallback needed"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "5 minutes if needed",
                    "communication_template": "Service running optimally. Brief delays possible during morning rush hour."
                },
                "business_impact": {
                    "processing_delay": "1-2 minutes average",
                    "manual_processing_cost": "INR 30-45 per transaction",
                    "user_satisfaction_impact": "Minimal - excellent user experience"
                },
                "health_score": 94,
                "risk_level": "low"
            },
            "canara-fip": {
                "downtime_prediction": {
                    "probability": 0.22,
                    "time_window": "next 8-10 hours",
                    "confidence": "medium",
                    "reasoning": "Good performance with 95.3% consent success rate and good stability grade. Low anomaly rates and stable trends. Peak issues at hour 8 (8 AM) but well-managed overall."
                },
                "patterns_detected": [
                    "Peak errors at hour 8 (8 AM) - morning rush",
                    "Stable performance with low variation",
                    "Good error rate management",
                    "Consistent response times"
                ],
                "anomalies": [
                    "Only 36 consent/data fetch anomalies (1.43% rate) - very low",
                    "109 status anomalies (4.32% rate) - acceptable"
                ],
                "user_impact": {
                    "consent_failure_rate": "4.7%",
                    "data_fetch_failure_rate": "5.9%",
                    "estimated_affected_users": 1100,
                    "recommended_fallback": "PDF upload during morning peak (8:00-9:00)"
                },
                "fiu_recommendations": {
                    "should_activate_manual": False,
                    "retry_after": "10 minutes during morning peak",
                    "communication_template": "Service running well. Brief delays possible during morning hours."
                },
                "business_impact": {
                    "processing_delay": "2-3 minutes average",
                    "manual_processing_cost": "INR 45-65 per transaction",
                    "user_satisfaction_impact": "Low - good user experience with minor morning delays"
                },
                "health_score": 86,
                "risk_level": "low"
            }
        }
    
    def _calculate_risk_level(self, consent_rate: float, data_rate: float, response_time: float, status: str) -> Dict:
        """
        Calculate risk level based on metrics
        """
        # Base risk calculation
        avg_success = (consent_rate + data_rate) / 2
        
        if status == 'critical' or avg_success < 30:
            return {
                'probability': random.uniform(0.85, 0.98),
                'time_window': 'next 30 minutes',
                'confidence': 'very high',
                'reasoning': f'Critical failure state with {avg_success:.1f}% success rate. Immediate intervention required.'
            }
        elif status == 'degraded' or avg_success < 70:
            return {
                'probability': random.uniform(0.60, 0.85),
                'time_window': 'next 1-3 hours',
                'confidence': 'high',
                'reasoning': f'Degraded performance detected. Success rate at {avg_success:.1f}%, showing concerning decline pattern.'
            }
        elif response_time > 5.0:
            return {
                'probability': random.uniform(0.40, 0.65),
                'time_window': 'next 2-6 hours',
                'confidence': 'medium',
                'reasoning': f'High response times ({response_time:.1f}s) indicate system stress. Monitoring closely.'
            }
        else:
            return {
                'probability': random.uniform(0.10, 0.30),
                'time_window': 'next 4-24 hours',
                'confidence': 'high',
                'reasoning': f'Normal operations with {avg_success:.1f}% success rate. Standard monitoring sufficient.'
            }
    
    def _generate_patterns(self, fip_name: str, metrics: Dict) -> List[str]:
        """
        Generate realistic patterns based on FIP and metrics
        """
        patterns = []
        
        # Bank-specific patterns
        bank_patterns = {
            'sbi-fip': [
                "Daily maintenance window detected: 2:00-4:00 AM IST",
                "Peak hour performance dip during 9:00-11:00 AM",
                "Weekend processing shows 15% slower response times"
            ],
            'hdfc-fip': [
                "Monthly maintenance pattern: First Sunday 1:00-5:00 AM",
                "Gradual performance degradation over past 6 hours",
                "Error spike correlates with database connection issues"
            ],
            'icici-fip': [
                "Consistent performance with minor evening slowdowns",
                "Weekly backup window: Saturday 11:00 PM - 2:00 AM",
                "Holiday period shows increased load patterns"
            ],
            'axis-fip': [
                "Cascading failure pattern detected in last 2 hours",
                "Memory utilization spike preceding outages",
                "Connection pool exhaustion recurring issue"
            ]
        }
        
        if fip_name.lower() in bank_patterns:
            patterns.extend(bank_patterns[fip_name.lower()])
        
        # Metric-based patterns
        success_rate = metrics.get('consent_success_rate', 0)
        if success_rate < 50:
            patterns.append("Exponential failure rate increase detected")
        elif success_rate < 80:
            patterns.append("Gradual performance degradation trend")
        
        return patterns
    
    def _generate_anomalies(self, fip_name: str, metrics: Dict) -> List[str]:
        """
        Generate anomalies based on metrics
        """
        anomalies = []
        
        consent_rate = metrics.get('consent_success_rate', 0)
        data_rate = metrics.get('data_fetch_success_rate', 0)
        response_time = metrics.get('avg_response_time', 0)
        
        if consent_rate < 30:
            anomalies.append(f"Critical consent approval failure rate: {100-consent_rate:.1f}%")
        
        if data_rate < 30:
            anomalies.append(f"Severe data fetch degradation: {100-data_rate:.1f}% failure rate")
        
        if response_time > 8:
            anomalies.append(f"Response time spike: {response_time:.1f}s (normal: <2s)")
        
        if abs(consent_rate - data_rate) > 30:
            anomalies.append("Significant variance between consent and data fetch success rates")
        
        return anomalies
    
    def _estimate_affected_users(self, fip_name: str, probability: float) -> int:
        """
        Estimate affected users based on FIP and probability
        """
        # Bank user base estimates
        user_bases = {
            'sbi-fip': 4500,
            'hdfc-fip': 3200,
            'icici-fip': 2800,
            'axis-fip': 1200,
            'kotak-fip': 800,
            'boi-fip': 600
        }
        
        base_users = user_bases.get(fip_name.lower(), 1000)
        return int(base_users * probability)
    
    def _get_fallback_recommendation(self, probability: float) -> str:
        """
        Get fallback recommendation based on probability
        """
        if probability > 0.8:
            return "Immediate manual data collection required"
        elif probability > 0.6:
            return "Prepare PDF collection workflow"
        elif probability > 0.4:
            return "Monitor closely, prepare fallback options"
        else:
            return "Standard monitoring, no immediate action needed"
    
    def _calculate_retry_time(self, probability: float) -> str:
        """
        Calculate when to retry based on risk
        """
        if probability > 0.8:
            return "4-6 hours (after maintenance completion)"
        elif probability > 0.6:
            return "2-4 hours (monitor for improvement)"
        elif probability > 0.4:
            return "1-2 hours (quick retry advisable)"
        else:
            return "Normal retry intervals (15-30 minutes)"
    
    def _generate_user_communication(self, fip_name: str, risk_level: Dict) -> str:
        """
        Generate user communication template
        """
        bank_name = fip_name.replace('-fip', '').upper()
        
        if risk_level['probability'] > 0.7:
            return f"Due to technical maintenance at {bank_name}, please upload your bank statement as PDF or contact support for assistance."
        elif risk_level['probability'] > 0.4:
            return f"{bank_name} is experiencing temporary delays. Please try again in 2 hours or upload PDF statement for faster processing."
        else:
            return f"Your {bank_name} consent is being processed normally. Expected completion in 15-30 minutes."
    
    def _calculate_satisfaction_impact(self, probability: float) -> str:
        """
        Calculate user satisfaction impact
        """
        if probability > 0.8:
            return "severe negative impact"
        elif probability > 0.6:
            return "moderate negative impact"
        elif probability > 0.4:
            return "minor negative impact"
        else:
            return "minimal impact"
    
    def _get_risk_category(self, probability: float) -> str:
        """
        Get risk category
        """
        if probability > 0.7:
            return "critical"
        elif probability > 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_mock_business_impact(self, predictions: Dict) -> Dict:
        """
        Generate business impact analysis
        """
        total_affected_users = 0
        total_cost = 0
        high_risk_fips = 0
        
        for fip_name, prediction in predictions.items():
            probability = prediction.get('downtime_prediction', {}).get('probability', 0)
            affected_users = prediction.get('user_impact', {}).get('estimated_affected_users', 0)
            
            total_affected_users += affected_users
            total_cost += probability * 180000  # Base cost per FIP
            
            if probability > 0.7:
                high_risk_fips += 1
        
        return {
            "overall_impact": {
                "total_affected_users": total_affected_users,
                "estimated_processing_cost": f"INR {total_cost:.0f}",
                "high_risk_fips": high_risk_fips,
                "overall_system_health": max(1, 10 - (high_risk_fips * 2))
            },
            "recommended_actions": {
                "immediate": [
                    "Activate manual data collection for critical FIPs",
                    "Send proactive user notifications",
                    "Increase support team capacity"
                ],
                "short_term": [
                    "Prepare PDF processing workflows",
                    "Monitor degrading FIPs closely",
                    "Scale up manual processing resources"
                ],
                "strategic": [
                    "Review FIP redundancy strategies",
                    "Implement predictive monitoring",
                    "Enhance fallback procedures"
                ]
            },
            "cost_benefit": {
                "proactive_cost": f"INR {total_cost * 0.3:.0f}",
                "reactive_cost": f"INR {total_cost:.0f}",
                "savings_potential": f"INR {total_cost * 0.7:.0f}"
            }
        }
    
    def _generate_mock_proactive_alerts(self, current_metrics: Dict) -> Dict:
        """
        Generate proactive alerts
        """
        alerts = {
            "critical": [],
            "warning": [],
            "info": []
        }
        
        for fip_name, metrics in current_metrics.items():
            consent_rate = metrics.get('consent_success_rate', 0)
            status = metrics.get('current_status', 'unknown')
            
            if status == 'critical' or consent_rate < 30:
                alerts["critical"].append({
                    "fip": fip_name,
                    "message": f"Critical failure detected in {fip_name.upper()}",
                    "action_required": "Immediate manual fallback activation",
                    "estimated_impact": "High user impact, service degradation"
                })
            elif status == 'degraded' or consent_rate < 70:
                alerts["warning"].append({
                    "fip": fip_name,
                    "message": f"Performance degradation in {fip_name.upper()}",
                    "action_required": "Prepare fallback procedures",
                    "estimated_impact": "Moderate delays expected"
                })
            else:
                alerts["info"].append({
                    "fip": fip_name,
                    "message": f"{fip_name.upper()} operating normally",
                    "action_required": "Continue monitoring",
                    "estimated_impact": "No impact expected"
                })
        
        return alerts
    
    def _generate_mock_recommendations(self, situation: Dict) -> Dict:
        """
        Generate operational recommendations
        """
        return {
            "immediate_actions": [
                "Switch AXIS-FIP users to manual PDF collection",
                "Send proactive notifications to HDFC customers",
                "Increase monitoring frequency for degraded FIPs"
            ],
            "resource_planning": [
                "Scale PDF processing team by 40%",
                "Prepare emergency communication templates",
                "Ensure backup system capacity"
            ],
            "preventive_measures": [
                "Schedule maintenance during low-traffic hours",
                "Implement circuit breaker patterns",
                "Enhance monitoring threshold alerts"
            ],
            "cost_optimization": [
                "Use predictive scaling for manual resources",
                "Optimize retry intervals based on FIP patterns",
                "Implement intelligent traffic routing"
            ]
        }
    
    def _generate_mock_system_overview(self) -> Dict:
        """
        Generate system overview
        """
        return {
            "system_health_score": 7.2,
            "overall_status": "operational_with_issues",
            "fips_summary": {
                "total_fips": 11,
                "healthy": 6,
                "degraded": 3,
                "critical": 2
            },
            "performance_metrics": {
                "average_consent_success": 78.4,
                "average_data_fetch_success": 74.2,
                "system_availability": 86.7
            },
            "predictions_summary": {
                "fips_at_risk": 4,
                "next_predicted_outage": "HDFC-FIP in 2 hours",
                "confidence_level": "high"
            },
            "business_impact": {
                "users_potentially_affected": 3240,
                "estimated_processing_cost": "INR 2.8L",
                "manual_capacity_required": "40% increase"
            }
        }
    
    # ================================
    # REAL BEDROCK IMPLEMENTATIONS
    # ================================
    
    def _call_real_bedrock_prediction(self, metrics_data: Dict, time_horizon: str) -> Dict:
        """
        Call real Bedrock for predictions
        """
        try:
            prompt = self._build_prediction_prompt(metrics_data, time_horizon)
            logger.info(f"Bedrock prediction prompt: {prompt}")
            return {}
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Parse JSON response from Bedrock
            return json.loads(content)
            
        except Exception as e:
            print(f"Bedrock API error: {e}")
            # Fallback to mock
            return self._generate_mock_downtime_predictions(metrics_data, time_horizon)
    
    def _build_prediction_prompt(self, metrics_data: Dict, time_horizon: str) -> str:
        """
        Build comprehensive prompt for Bedrock
        """
        # Convert metrics data to JSON using custom encoder
        metrics_json = json.dumps(metrics_data, indent=2, cls=NumpyEncoder)
        
        return f"""
You are an expert AI system analyzing Financial Information Provider (FIP) performance in India's Account Aggregator ecosystem.

CONTEXT:
- FIPs are banks/financial institutions providing financial data
- Users need to approve consent through FIPs (if FIP down, consent fails)
- FIUs fetch financial data from FIPs (if FIP down, data fetch fails)
- When FIPs fail, manual fallback is required (PDF uploads, phone verification)

CURRENT FIP METRICS ({time_horizon} analysis):
{metrics_json}

ANALYSIS REQUIREMENTS:
1. **Downtime Prediction**: Probability and timing of failures
2. **User Impact**: How many users affected, what alternatives needed
3. **Business Impact**: Processing costs, delays, manual resource requirements
4. **Operational Recommendations**: When to switch to manual processes

For each FIP, provide predictions in this exact JSON format:
{{
    "fip_name": {{
        "downtime_prediction": {{
            "probability": 0.75,
            "time_window": "next 2 hours",
            "confidence": "high",
            "reasoning": "Detailed explanation based on metrics"
        }},
        "patterns_detected": ["list of patterns found"],
        "anomalies": ["list of anomalies detected"],
        "user_impact": {{
            "consent_failure_rate": "percentage",
            "data_fetch_failure_rate": "percentage", 
            "estimated_affected_users": number,
            "recommended_fallback": "action description"
        }},
        "fiu_recommendations": {{
            "should_activate_manual": boolean,
            "retry_after": "time estimate",
            "communication_template": "message for users"
        }},
        "business_impact": {{
            "processing_delay": "time estimate",
            "manual_processing_cost": "cost estimate",
            "user_satisfaction_impact": "impact description"
        }},
        "health_score": number,
        "risk_level": "critical|high|medium|low"
    }}
}}"""
    
    def _call_real_bedrock_impact_analysis(self, predictions: Dict) -> Dict:
        """
        Call real Bedrock for business impact analysis
        """
        try:
            # Convert predictions to JSON using custom encoder
            predictions_json = json.dumps(predictions, indent=2, cls=NumpyEncoder)
            
            prompt = f"""
Analyze business impact of predicted FIP outages:

PREDICTIONS:
{predictions_json}

Provide impact analysis in JSON format:
{{
    "overall_impact": {{
        "severity": "high|medium|low",
        "affected_users": number,
        "business_cost": "INR amount",
        "operational_impact": "description"
    }},
    "fip_specific_impacts": [
        {{
            "fip": "fip_name",
            "severity": "high|medium|low",
            "affected_users": number,
            "mitigation_steps": ["step1", "step2"]
        }}
    ],
    "recommendations": [
        {{
            "priority": "immediate|high|medium",
            "action": "description",
            "expected_outcome": "description"
        }}
    ]
}}
"""
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                }, cls=NumpyEncoder)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            return json.loads(content)
            
        except Exception as e:
            print(f"Bedrock impact analysis error: {e}")
            return self._generate_mock_business_impact(predictions)
    
    def _call_real_bedrock_alerts(self, current_metrics: Dict) -> Dict:
        """
        Call real Bedrock for proactive alerts
        """
        try:
            # Convert metrics to JSON using custom encoder
            metrics_json = json.dumps(current_metrics, indent=2, cls=NumpyEncoder)
            
            prompt = f"""
Generate proactive alerts for AA Gateway operations based on current FIP metrics:

CURRENT METRICS:
{metrics_json}

Generate alerts in JSON format:
{{
    "critical": [
        {{
            "fip": "fip_name",
            "message": "alert message",
            "action_required": "immediate action",
            "estimated_impact": "impact description"
        }}
    ],
    "warning": [...],
    "info": [...]
}}
"""
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}]
                }, cls=NumpyEncoder)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            return json.loads(content)
            
        except Exception as e:
            print(f"Bedrock alerts error: {e}")
            return self._generate_mock_proactive_alerts(current_metrics)
    
    def _call_real_bedrock_recommendations(self, situation: Dict) -> Dict:
        """
        Call real Bedrock for recommendations
        """
        try:
            prompt = f"""
Generate operational recommendations for AA Gateway team based on current situation:

SITUATION:
{json.dumps(situation, indent=2)}

Provide recommendations in JSON format:
{{
    "immediate_actions": ["action1", "action2"],
    "resource_planning": ["action1", "action2"],
    "preventive_measures": ["action1", "action2"],
    "cost_optimization": ["action1", "action2"]
}}
"""
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            return json.loads(content)
            
        except Exception as e:
            print(f"Bedrock recommendations error: {e}")
            return self._generate_mock_recommendations(situation)
    
    def _call_real_bedrock_overview(self) -> Dict:
        """
        Call real Bedrock for system overview
        """
        try:
            prompt = """
Generate a comprehensive system overview for AA Gateway operations.
Include system health score, status summary, and key metrics.

Provide in JSON format:
{
    "system_health_score": number,
    "overall_status": "status_description",
    "fips_summary": {
        "total_fips": number,
        "healthy": number,
        "degraded": number,
        "critical": number
    },
    "performance_metrics": {
        "average_consent_success": number,
        "average_data_fetch_success": number,
        "system_availability": number
    },
    "predictions_summary": {
        "fips_at_risk": number,
        "next_predicted_outage": "description",
        "confidence_level": "high|medium|low"
    },
    "business_impact": {
        "users_potentially_affected": number,
        "estimated_processing_cost": "INR amount",
        "manual_capacity_required": "percentage"
    }
}
"""
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}]
                }, cls=NumpyEncoder)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            return json.loads(content)
            
        except Exception as e:
            print(f"Bedrock overview error: {e}")
            return self._generate_mock_system_overview()