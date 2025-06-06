import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError

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
        predictions = {}
        
        for fip_name, metrics in metrics_data.items():
            consent_rate = metrics.get('consent_success_rate', 0)
            data_rate = metrics.get('data_fetch_success_rate', 0)
            response_time = metrics.get('avg_response_time', 0)
            current_status = metrics.get('current_status', 'unknown')
            
            # Calculate risk based on actual metrics
            risk_level = self._calculate_risk_level(consent_rate, data_rate, response_time, current_status)
            
            predictions[fip_name] = {
                "downtime_prediction": {
                    "probability": risk_level['probability'],
                    "time_window": risk_level['time_window'],
                    "confidence": risk_level['confidence'],
                    "reasoning": risk_level['reasoning']
                },
                "patterns_detected": self._generate_patterns(fip_name, metrics),
                "anomalies": self._generate_anomalies(fip_name, metrics),
                "user_impact": {
                    "consent_failure_rate": f"{max(0, 100 - consent_rate):.1f}%",
                    "data_fetch_failure_rate": f"{max(0, 100 - data_rate):.1f}%",
                    "estimated_affected_users": self._estimate_affected_users(fip_name, risk_level['probability']),
                    "recommended_fallback": self._get_fallback_recommendation(risk_level['probability'])
                },
                "fiu_recommendations": {
                    "should_activate_manual": risk_level['probability'] > 0.6,
                    "retry_after": self._calculate_retry_time(risk_level['probability']),
                    "communication_template": self._generate_user_communication(fip_name, risk_level)
                },
                "business_impact": {
                    "processing_delay": f"{risk_level['probability'] * 8:.1f} hours",
                    "manual_processing_cost": f"₹{risk_level['probability'] * 200000:.0f}",
                    "user_satisfaction_impact": self._calculate_satisfaction_impact(risk_level['probability'])
                },
                "health_score": max(1.0, 10.0 - (risk_level['probability'] * 9)),
                "risk_level": self._get_risk_category(risk_level['probability']),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        return predictions
    
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
                "estimated_processing_cost": f"₹{total_cost:.0f}",
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
                "proactive_cost": f"₹{total_cost * 0.3:.0f}",
                "reactive_cost": f"₹{total_cost:.0f}",
                "savings_potential": f"₹{total_cost * 0.7:.0f}"
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
                "estimated_processing_cost": "₹2.8L",
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
        return f"""
You are an expert AI system analyzing Financial Information Provider (FIP) performance in India's Account Aggregator ecosystem.

CONTEXT:
- FIPs are banks/financial institutions providing financial data
- Users need to approve consent through FIPs (if FIP down, consent fails)
- FIUs fetch financial data from FIPs (if FIP down, data fetch fails)
- When FIPs fail, manual fallback is required (PDF uploads, phone verification)

CURRENT FIP METRICS ({time_horizon} analysis):
{json.dumps(metrics_data, indent=2)}

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
            "processing_delay": "hours",
            "manual_processing_cost": "₹amount",
            "user_satisfaction_impact": "description"
        }},
        "health_score": float_1_to_10,
        "risk_level": "low/medium/critical"
    }}
}}

Focus on actionable insights for AA Gateway operations team.
"""
    
    def _call_real_bedrock_impact_analysis(self, predictions: Dict) -> Dict:
        """
        Call real Bedrock for business impact analysis
        """
        try:
            prompt = f"""
Analyze the business impact of these FIP predictions for an Account Aggregator operations team:

PREDICTIONS:
{json.dumps(predictions, indent=2)}

Provide comprehensive business impact analysis in JSON format:
{{
    "overall_impact": {{
        "total_affected_users": number,
        "estimated_processing_cost": "₹amount",
        "high_risk_fips": number,
        "overall_system_health": score_1_to_10
    }},
    "recommended_actions": {{
        "immediate": ["action1", "action2"],
        "short_term": ["action1", "action2"],
        "strategic": ["action1", "action2"]
    }},
    "cost_benefit": {{
        "proactive_cost": "₹amount",
        "reactive_cost": "₹amount",
        "savings_potential": "₹amount"
    }}
}}
"""
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                })
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
            prompt = f"""
Generate proactive alerts for AA Gateway operations based on current FIP metrics:

CURRENT METRICS:
{json.dumps(current_metrics, indent=2)}

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
                })
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
    "system_health_score": float_1_to_10,
    "overall_status": "status_description",
    "fips_summary": {
        "total_fips": number,
        "healthy": number,
        "degraded": number,
        "critical": number
    },
    "performance_metrics": {
        "average_consent_success": percentage,
        "average_data_fetch_success": percentage,
        "system_availability": percentage
    },
    "predictions_summary": {
        "fips_at_risk": number,
        "next_predicted_outage": "description",
        "confidence_level": "high/medium/low"
    },
    "business_impact": {
        "users_potentially_affected": number,
        "estimated_processing_cost": "₹amount",
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
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            return json.loads(content)
            
        except Exception as e:
            print(f"Bedrock overview error: {e}")
            return self._generate_mock_system_overview()