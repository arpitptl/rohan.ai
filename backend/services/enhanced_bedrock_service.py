import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np
from utils.logger import logger

@dataclass
class PredictionResult:
    fip_name: str
    downtime_probability: float
    confidence_level: str
    time_window: str
    reasoning: str
    business_impact: Dict
    recommended_actions: List[str]

@dataclass
class Alert:
    severity: str  # critical, warning, info
    fip_name: str
    alert_type: str
    message: str
    recommended_action: str
    confidence: float
    timestamp: str

class EnhancedBedrockService:
    """
    Enhanced AI service using AWS Bedrock for advanced FIP analytics,
    pattern detection, and predictive insights
    """
    
    def __init__(self, use_mock: bool = True, region_name: str = 'us-east-1'):
        self.use_mock = use_mock
        self.region_name = region_name
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.logger = logger
        
        if not use_mock:
            try:
                self.bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=region_name
                )
                self.logger.info("✅ Enhanced Bedrock client initialized")
            except Exception as e:
                self.logger.warning(f"⚠️ Bedrock initialization failed, using mock mode: {e}")
                self.use_mock = True
        else:
            self.logger.info("🎭 Using enhanced mock Bedrock for development")
    
    def analyze_historical_patterns(self, comprehensive_report: Dict) -> Dict[str, Any]:
        """
        Analyze historical data patterns using AI to identify trends,
        anomalies, and maintenance windows
        """
        if not self.use_mock:
            return self._mock_analyze_historical_patterns(comprehensive_report)
        else:
            return self._bedrock_analyze_historical_patterns(comprehensive_report)
    
    def predict_downtime_events(self, comprehensive_report: Dict, 
                               prediction_horizon: str = "24h") -> Dict[str, PredictionResult]:
        """
        Generate AI-powered downtime predictions for each FIP
        """
        if not self.use_mock:
            return self._mock_predict_downtime_events(comprehensive_report, prediction_horizon)
        else:
            return self._bedrock_predict_downtime_events(comprehensive_report, prediction_horizon)
    
    def generate_proactive_alerts(self, comprehensive_report: Dict,
                                 current_metrics: Dict) -> List[Alert]:
        """
        Generate intelligent proactive alerts based on historical patterns
        and current system state
        """
        if self.use_mock:
            return self._mock_generate_proactive_alerts(comprehensive_report, current_metrics)
        else:
            return self._bedrock_generate_proactive_alerts(comprehensive_report, current_metrics)
    
    def generate_business_insights(self, comprehensive_report: Dict,
                                 predictions: Dict[str, PredictionResult]) -> Dict[str, Any]:
        """
        Generate business-focused insights and recommendations
        """
        if self.use_mock:
            return self._mock_generate_business_insights(comprehensive_report, predictions)
        else:
            return self._bedrock_generate_business_insights(comprehensive_report, predictions)
    
    # ===============================
    # BEDROCK IMPLEMENTATION
    # ===============================
    
    def _bedrock_analyze_historical_patterns(self, comprehensive_report: Dict) -> Dict[str, Any]:
        """Use Bedrock to analyze historical patterns"""
        prompt = self._build_pattern_analysis_prompt(comprehensive_report)
        logger.info(f"Bedrock pattern analysis prompt: {prompt}")
        
        try:
            response = self._call_bedrock(prompt, max_tokens=6000)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Bedrock pattern analysis failed: {e}")
            return self._mock_analyze_historical_patterns(comprehensive_report)
    
    def _bedrock_predict_downtime_events(self, comprehensive_report: Dict, 
                                       prediction_horizon: str) -> Dict[str, PredictionResult]:
        """Use Bedrock for downtime predictions"""
        prompt = self._build_prediction_prompt(comprehensive_report, prediction_horizon)
        logger.info(f"Bedrock downtimeprediction prompt: {prompt}")
        
        try:
            response = self._call_bedrock(prompt, max_tokens=8000)
            predictions_data = json.loads(response)
            
            # Convert to PredictionResult objects
            predictions = {}
            for fip_name, pred_data in predictions_data.items():
                predictions[fip_name] = PredictionResult(
                    fip_name=fip_name,
                    downtime_probability=pred_data.get('downtime_probability', 0),
                    confidence_level=pred_data.get('confidence_level', 'medium'),
                    time_window=pred_data.get('time_window', 'unknown'),
                    reasoning=pred_data.get('reasoning', ''),
                    business_impact=pred_data.get('business_impact', {}),
                    recommended_actions=pred_data.get('recommended_actions', [])
                )
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Bedrock prediction failed: {e}")
            return self._mock_predict_downtime_events(comprehensive_report, prediction_horizon)
    
    def _bedrock_generate_proactive_alerts(self, comprehensive_report: Dict,
                                         current_metrics: Dict) -> List[Alert]:
        """Use Bedrock for proactive alert generation"""
        prompt = self._build_alert_generation_prompt(comprehensive_report, current_metrics)
        
        try:
            response = self._call_bedrock(prompt, max_tokens=4000)
            alerts_data = json.loads(response)
            
            # Convert to Alert objects
            alerts = []
            for alert_data in alerts_data.get('alerts', []):
                alerts.append(Alert(
                    severity=alert_data.get('severity', 'info'),
                    fip_name=alert_data.get('fip_name', 'unknown'),
                    alert_type=alert_data.get('alert_type', 'general'),
                    message=alert_data.get('message', ''),
                    recommended_action=alert_data.get('recommended_action', ''),
                    confidence=alert_data.get('confidence', 0.5),
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Bedrock alert generation failed: {e}")
            return self._mock_generate_proactive_alerts(comprehensive_report, current_metrics)
    
    def _bedrock_generate_business_insights(self, comprehensive_report: Dict,
                                          predictions: Dict[str, PredictionResult]) -> Dict[str, Any]:
        """Use Bedrock for business insights"""
        prompt = self._build_business_insights_prompt(comprehensive_report, predictions)
        
        try:
            response = self._call_bedrock(prompt, max_tokens=5000)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Bedrock business insights failed: {e}")
            return self._mock_generate_business_insights(comprehensive_report, predictions)
    
    def _call_bedrock(self, prompt: str, max_tokens: int = 4000) -> str:
        """Make a call to Bedrock Claude model"""
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            self.logger.error(f"Bedrock API call failed: {e}")
            raise
    
    # ===============================
    # PROMPT BUILDERS
    # ===============================
    
    def _build_pattern_analysis_prompt(self, comprehensive_report: Dict) -> str:
        """Build prompt for historical pattern analysis"""
        return f"""
You are an expert AI system analyzing Financial Information Provider (FIP) performance data in India's Account Aggregator ecosystem. Analyze the historical data and identify patterns, trends, and insights.

CONTEXT:
- FIPs are banks/financial institutions providing financial data through Account Aggregator framework
- Key metrics: consent_success_rate, data_fetch_success_rate, response_time, error_rate, status
- Critical thresholds: <70% success rate = concerning, <50% = critical
- Response time: >5s = slow, >10s = critical

HISTORICAL ANALYSIS DATA:
{json.dumps(comprehensive_report, indent=2, default=str)}

ANALYSIS REQUIREMENTS:
1. **Pattern Detection**: Identify recurring patterns in performance data
2. **Trend Analysis**: Detect degradation or improvement trends
3. **Anomaly Identification**: Spot unusual behavior or outliers
4. **Maintenance Window Detection**: Identify scheduled vs unscheduled downtime
5. **Correlation Analysis**: Find relationships between metrics
6. **Risk Assessment**: Evaluate each FIP's stability and reliability

Provide your analysis in this JSON format:
{{
    "system_wide_patterns": {{
        "overall_health_trend": "improving/stable/degrading",
        "common_failure_patterns": ["pattern1", "pattern2"],
        "peak_performance_hours": [hour_ranges],
        "system_wide_correlations": ["correlation_insights"]
    }},
    "fip_specific_analysis": {{
        "fip_name": {{
            "health_trend": "improving/stable/degrading",
            "key_patterns": ["pattern1", "pattern2"],
            "anomalies_detected": ["anomaly1", "anomaly2"],
            "maintenance_patterns": ["maintenance_insights"],
            "risk_level": "low/medium/high/critical",
            "stability_score": 0.0-1.0,
            "performance_insights": ["insight1", "insight2"]
        }}
    }},
    "cross_fip_insights": {{
        "best_performing_fips": ["fip1", "fip2"],
        "worst_performing_fips": ["fip1", "fip2"],
        "similar_behavior_groups": [["fip1", "fip2"], ["fip3", "fip4"]],
        "cascading_failure_risks": ["risk_scenarios"]
    }},
    "temporal_insights": {{
        "time_based_patterns": ["insight1", "insight2"],
        "seasonal_effects": ["effect1", "effect2"],
        "maintenance_window_recommendations": ["recommendation1", "recommendation2"]
    }}
}}

Focus on actionable insights that operations teams can use for proactive management.
"""
    
    def _build_prediction_prompt(self, comprehensive_report: Dict, prediction_horizon: str) -> str:
        """Build prompt for downtime predictions"""
        return f"""
You are an expert AI system predicting FIP downtime events using historical performance data and machine learning insights.

PREDICTION CONTEXT:
- Prediction horizon: {prediction_horizon}
- Current timestamp: {datetime.utcnow().isoformat()}
- Account Aggregator ecosystem in India
- Business impact: Each FIP outage affects thousands of users and causes revenue loss

HISTORICAL DATA FOR PREDICTIONS:
{json.dumps(comprehensive_report, indent=2, default=str)}

PREDICTION REQUIREMENTS:
For each FIP, predict:
1. **Downtime Probability**: 0.0-1.0 probability of outage in prediction window
2. **Confidence Level**: high/medium/low based on data quality and pattern clarity
3. **Time Window**: When the event is most likely (e.g., "next 2-4 hours", "tonight 2-4 AM")
4. **Reasoning**: Detailed explanation based on historical patterns and current trends
5. **Business Impact**: User count affected, estimated revenue impact, operational costs
6. **Recommended Actions**: Specific steps to prevent or mitigate

Provide predictions in this JSON format:
{{
    "fip_name": {{
        "downtime_probability": 0.0-1.0,
        "confidence_level": "high/medium/low",
        "time_window": "descriptive_time_range",
        "reasoning": "detailed_explanation_based_on_data",
        "business_impact": {{
            "affected_users": estimated_number,
            "revenue_impact_inr": estimated_amount,
            "operational_cost_inr": estimated_amount,
            "sla_breach_risk": "high/medium/low",
            "user_satisfaction_impact": "severe/moderate/minor"
        }},
        "recommended_actions": [
            "immediate_action1",
            "immediate_action2",
            "preventive_action1"
        ],
        "fallback_procedures": [
            "manual_process1",
            "communication_template",
            "escalation_path"
        ],
        "monitoring_focus": [
            "metric_to_watch1",
            "threshold_to_monitor"
        ]
    }}
}}

Base predictions on:
- Historical failure patterns
- Current performance trends  
- Maintenance window patterns
- Anomaly detection results
- Cross-FIP correlation analysis
- Time-based patterns (hour, day, week)

Prioritize accuracy and actionability over complexity.
"""
    
    def _build_alert_generation_prompt(self, comprehensive_report: Dict, current_metrics: Dict) -> str:
        """Build prompt for proactive alert generation"""
        return f"""
You are an expert AI system generating proactive alerts for FIP operations teams based on historical patterns and current system state.

CURRENT SYSTEM STATE:
{json.dumps(current_metrics, indent=2, default=str)}

HISTORICAL ANALYSIS:
{json.dumps(comprehensive_report, indent=2, default=str)}

ALERT GENERATION REQUIREMENTS:
Generate intelligent alerts that are:
1. **Actionable**: Include specific steps to take
2. **Prioritized**: Critical alerts first, then warnings, then info
3. **Context-Aware**: Consider historical patterns and current trends
4. **Business-Focused**: Include impact assessment and user implications

Alert Types to Consider:
- **Performance Degradation**: Declining success rates or increasing response times
- **Anomaly Detection**: Unusual patterns compared to historical baseline
- **Maintenance Prediction**: Upcoming maintenance windows based on patterns
- **Capacity Issues**: High load or resource constraints
- **Correlation Alerts**: Issues affecting multiple FIPs simultaneously
- **Threshold Breaches**: Crossing critical performance thresholds

Provide alerts in this JSON format:
{{
    "alerts": [
        {{
            "severity": "critical/warning/info",
            "fip_name": "fip_identifier",
            "alert_type": "performance_degradation/anomaly/maintenance/capacity/correlation/threshold",
            "message": "Clear, actionable alert message",
            "recommended_action": "Specific immediate action to take",
            "confidence": 0.0-1.0,
            "business_impact": {{
                "affected_users": number,
                "estimated_duration": "time_estimate",
                "severity_description": "impact_description"
            }},
            "supporting_evidence": [
                "evidence1_from_data",
                "evidence2_from_patterns"
            ],
            "escalation_path": "who_to_notify_and_when"
        }}
    ],
    "alert_summary": {{
        "total_alerts": number,
        "critical_count": number,
        "warning_count": number,
        "info_count": number,
        "fips_requiring_attention": ["fip1", "fip2"],
        "system_health_status": "critical/degraded/stable/healthy"
    }}
}}

Focus on alerts that prevent issues rather than just reporting them.
"""
    
    def _build_business_insights_prompt(self, comprehensive_report: Dict, 
                                      predictions: Dict[str, PredictionResult]) -> str:
        """Build prompt for business insights generation"""
        
        # Convert PredictionResult objects to dict for JSON serialization
        predictions_dict = {}
        for fip_name, pred in predictions.items():
            predictions_dict[fip_name] = {
                'downtime_probability': pred.downtime_probability,
                'confidence_level': pred.confidence_level,
                'time_window': pred.time_window,
                'reasoning': pred.reasoning,
                'business_impact': pred.business_impact,
                'recommended_actions': pred.recommended_actions
            }
        
        return f"""
You are a senior business analyst specializing in fintech infrastructure and Account Aggregator ecosystem operations. Generate executive-level insights and strategic recommendations.

HISTORICAL PERFORMANCE DATA:
{json.dumps(comprehensive_report, indent=2, default=str)}

AI PREDICTIONS:
{json.dumps(predictions_dict, indent=2, default=str)}

BUSINESS CONTEXT:
- Account Aggregator ecosystem serving millions of users
- Each FIP outage impacts customer loan applications, financial planning, and business operations
- Regulatory compliance requirements (RBI guidelines)
- Competition from other AA platforms
- Cost of manual fallback procedures
- Customer acquisition and retention implications

GENERATE INSIGHTS FOR:
1. **Executive Summary**: High-level business impact and key decisions needed
2. **Cost-Benefit Analysis**: Proactive vs reactive approach costs
3. **Strategic Recommendations**: Long-term improvements and investments
4. **Operational Efficiency**: Process improvements and automation opportunities
5. **Risk Management**: Business continuity and compliance considerations
6. **Customer Impact**: User experience and satisfaction implications

Provide insights in this JSON format:
{{
    "executive_summary": {{
        "overall_system_health": "description",
        "key_business_risks": ["risk1", "risk2"],
        "immediate_decisions_needed": ["decision1", "decision2"],
        "financial_impact_next_24h": {{
            "potential_revenue_loss": amount_in_inr,
            "operational_costs": amount_in_inr,
            "prevention_investment": amount_in_inr
        }}
    }},
    "strategic_recommendations": {{
        "infrastructure_investments": [
            {{
                "recommendation": "investment_description",
                "expected_roi": "roi_description",
                "timeline": "implementation_timeline",
                "priority": "high/medium/low"
            }}
        ],
        "process_improvements": [
            {{
                "improvement": "process_change",
                "implementation_effort": "effort_level",
                "expected_benefit": "benefit_description"
            }}
        ],
        "vendor_management": [
            {{
                "fip_name": "fip_identifier",
                "recommendation": "vendor_action",
                "business_justification": "why_needed"
            }}
        ]
    }},
    "operational_insights": {{
        "resource_optimization": ["optimization1", "optimization2"],
        "automation_opportunities": ["automation1", "automation2"],
        "monitoring_improvements": ["improvement1", "improvement2"],
        "team_recommendations": ["team_action1", "team_action2"]
    }},
    "customer_impact_analysis": {{
        "user_experience_risks": ["risk1", "risk2"],
        "satisfaction_impact": "high/medium/low",
        "communication_strategy": ["strategy1", "strategy2"],
        "retention_risks": ["risk1", "risk2"]
    }},
    "compliance_considerations": {{
        "regulatory_risks": ["risk1", "risk2"],
        "reporting_requirements": ["requirement1", "requirement2"],
        "audit_preparation": ["action1", "action2"]
    }},
    "competitive_analysis": {{
        "market_position": "position_assessment",
        "competitive_advantages": ["advantage1", "advantage2"],
        "improvement_areas": ["area1", "area2"]
    }}
}}

Focus on actionable business insights that drive strategic decisions and operational improvements.
"""

    # ===============================
    # MOCK IMPLEMENTATIONS
    # ===============================
    
    def _mock_analyze_historical_patterns(self, comprehensive_report: Dict) -> Dict[str, Any]:
        """Enhanced mock pattern analysis based on actual data"""
        
        fip_features = comprehensive_report.get('fip_features', {})
        system_summary = comprehensive_report.get('system_summary', {})
        
        # Analyze actual data for realistic insights
        patterns = {
            "system_wide_patterns": {
                "overall_health_trend": self._determine_system_trend(system_summary),
                "common_failure_patterns": [
                    "Peak hour performance degradation (9-11 AM, 2-4 PM)",
                    "Weekend maintenance windows affecting availability",
                    "Response time spikes correlating with high error rates",
                    "Cascading failures during system-wide load events"
                ],
                "peak_performance_hours": ["6-8 AM", "12-2 PM", "8-10 PM"],
                "system_wide_correlations": [
                    "Strong negative correlation between success rate and response time",
                    "Error rate increases significantly when response time > 5 seconds",
                    "Status degradation typically precedes success rate drops by 15-30 minutes"
                ]
            },
            "fip_specific_analysis": {},
            "cross_fip_insights": {
                "best_performing_fips": ["sbi-fip", "icici-fip", "kotak-fip"],
                "worst_performing_fips": ["axis-fip", "central-fip", "ubi-fip"],
                "similar_behavior_groups": [
                    ["sbi-fip", "icici-fip"],  # High performers
                    ["hdfc-fip", "boi-fip"],  # Medium performers with degradation
                    ["axis-fip", "central-fip"]  # Critical status group
                ],
                "cascading_failure_risks": [
                    "HDFC-FIP degradation often precedes BOI-FIP issues",
                    "System-wide load balancing issues when multiple FIPs fail",
                    "Manual processing bottlenecks during peak failure periods"
                ]
            },
            "temporal_insights": {
                "time_based_patterns": [
                    "Monday morning performance dips due to weekend maintenance recovery",
                    "Friday evening degradation as maintenance windows approach",
                    "Month-end spikes in error rates due to increased transaction volume"
                ],
                "seasonal_effects": [
                    "Festival periods show 40% increase in transaction failures",
                    "Quarter-end reporting creates system-wide performance pressure",
                    "Summer months show higher cooling-related infrastructure issues"
                ],
                "maintenance_window_recommendations": [
                    "Consolidate maintenance windows: 2-4 AM Sunday for maximum impact minimization",
                    "Implement rolling updates to avoid simultaneous FIP outages",
                    "Coordinate with high-volume FIPs for advance user notifications"
                ]
            }
        }
        
        # Generate FIP-specific analysis based on actual features
        for fip_name, features in fip_features.items():
            patterns["fip_specific_analysis"][fip_name] = self._analyze_fip_patterns(fip_name, features)
        
        return patterns
    
    def _mock_predict_downtime_events(self, comprehensive_report: Dict, 
                                    prediction_horizon: str) -> Dict[str, PredictionResult]:
        """Enhanced mock predictions based on actual FIP data"""
        
        fip_features = comprehensive_report.get('fip_features', {})
        predictions = {}
        
        for fip_name, features in fip_features.items():
            prediction = self._generate_realistic_prediction(fip_name, features, prediction_horizon)
            predictions[fip_name] = prediction
        
        return predictions
    
    def _mock_generate_proactive_alerts(self, comprehensive_report: Dict,
                                      current_metrics: Dict) -> List[Alert]:
        """Enhanced mock alert generation based on data patterns"""
        
        alerts = []
        fip_features = comprehensive_report.get('fip_features', {})
        
        for fip_name, features in fip_features.items():
            fip_alerts = self._generate_fip_alerts(fip_name, features, current_metrics.get(fip_name, {}))
            alerts.extend(fip_alerts)
        
        # Sort alerts by severity and confidence
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        alerts.sort(key=lambda x: (severity_order.get(x.severity, 3), -x.confidence))
        
        return alerts[:10]  # Return top 10 most important alerts
    
    def _mock_generate_business_insights(self, comprehensive_report: Dict,
                                       predictions: Dict[str, PredictionResult]) -> Dict[str, Any]:
        """Enhanced mock business insights"""
        
        # Calculate metrics from actual data
        total_affected_users = sum(pred.business_impact.get('affected_users', 0) 
                                 for pred in predictions.values())
        total_revenue_risk = sum(pred.business_impact.get('revenue_impact_inr', 0) 
                               for pred in predictions.values())
        
        high_risk_fips = [fip for fip, pred in predictions.items() 
                         if pred.downtime_probability > 0.7]
        
        return {
            "executive_summary": {
                "overall_system_health": f"System at moderate risk with {len(high_risk_fips)} FIPs requiring immediate attention",
                "key_business_risks": [
                    f"Potential {total_affected_users:,} users affected in next 24 hours",
                    f"Estimated ₹{total_revenue_risk:,.0f} revenue at risk",
                    "Manual processing costs could increase by 300% during outages",
                    "Customer satisfaction scores likely to drop 15-25% during peak failures"
                ],
                "immediate_decisions_needed": [
                    "Activate enhanced monitoring for high-risk FIPs",
                    "Pre-position manual processing teams for weekend coverage",
                    "Prepare customer communication templates for proactive notifications"
                ],
                "financial_impact_next_24h": {
                    "potential_revenue_loss": total_revenue_risk,
                    "operational_costs": total_revenue_risk * 0.4,
                    "prevention_investment": total_revenue_risk * 0.1
                }
            },
            "strategic_recommendations": {
                "infrastructure_investments": [
                    {
                        "recommendation": "Implement redundant FIP connections with automatic failover",
                        "expected_roi": "300% ROI within 6 months through reduced outage costs",
                        "timeline": "3-4 months implementation",
                        "priority": "high"
                    },
                    {
                        "recommendation": "Deploy AI-powered predictive monitoring system",
                        "expected_roi": "250% ROI through proactive issue prevention",
                        "timeline": "2-3 months implementation",
                        "priority": "high"
                    },
                    {
                        "recommendation": "Establish dedicated FIP performance SLAs with penalties",
                        "expected_roi": "Improved reliability, reduced operational overhead",
                        "timeline": "1-2 months negotiation",
                        "priority": "medium"
                    }
                ],
                "process_improvements": [
                    {
                        "improvement": "Automated fallback to manual processing workflows",
                        "implementation_effort": "medium",
                        "expected_benefit": "50% reduction in user impact during outages"
                    },
                    {
                        "improvement": "Real-time customer notification system for FIP issues",
                        "implementation_effort": "low",
                        "expected_benefit": "Improved customer satisfaction and reduced support load"
                    },
                    {
                        "improvement": "Predictive capacity planning based on historical patterns",
                        "implementation_effort": "medium",
                        "expected_benefit": "Better resource allocation and cost optimization"
                    }
                ],
                "vendor_management": [
                    {
                        "fip_name": "axis-fip",
                        "recommendation": "Escalate to senior management for immediate stability improvement",
                        "business_justification": "Critical status affecting 1,200+ daily users"
                    },
                    {
                        "fip_name": "hdfc-fip",
                        "recommendation": "Request dedicated technical support during maintenance windows",
                        "business_justification": "High-volume FIP with predictable degradation patterns"
                    }
                ]
            },
            "operational_insights": {
                "resource_optimization": [
                    "Implement dynamic load balancing during peak hours",
                    "Optimize manual processing team schedules based on predicted outages",
                    "Consolidate monitoring tools to reduce alert fatigue"
                ],
                "automation_opportunities": [
                    "Automated customer notifications for predicted maintenance windows",
                    "Auto-scaling of manual processing resources during outages",
                    "Intelligent alert routing based on severity and business impact"
                ],
                "monitoring_improvements": [
                    "Implement cross-FIP correlation monitoring",
                    "Add business impact scoring to technical alerts",
                    "Deploy real-time customer impact dashboards"
                ],
                "team_recommendations": [
                    "Train operations team on predictive alert interpretation",
                    "Establish dedicated FIP relationship management roles",
                    "Create escalation procedures for vendor accountability"
                ]
            },
            "customer_impact_analysis": {
                "user_experience_risks": [
                    "Loan application delays during FIP outages",
                    "Financial planning service disruptions",
                    "Increased customer support inquiries during peak failures"
                ],
                "satisfaction_impact": "high",
                "communication_strategy": [
                    "Proactive SMS/email notifications for predicted maintenance",
                    "In-app status page with real-time FIP availability",
                    "Dedicated customer support team for FIP-related issues"
                ],
                "retention_risks": [
                    "Power users may switch to competitors after repeated failures",
                    "Enterprise customers require 99.5% uptime guarantees",
                    "New user acquisition affected by negative reviews"
                ]
            },
            "compliance_considerations": {
                "regulatory_risks": [
                    "RBI guidelines on data availability and customer protection",
                    "Account Aggregator framework compliance requirements",
                    "Data localization and security during manual processing"
                ],
                "reporting_requirements": [
                    "Monthly availability reports to regulatory authorities",
                    "Incident reporting within 24 hours of major outages",
                    "Customer impact assessments for compliance audits"
                ],
                "audit_preparation": [
                    "Document all FIP SLAs and performance metrics",
                    "Maintain detailed incident response logs",
                    "Prepare business continuity plan documentation"
                ]
            },
            "competitive_analysis": {
                "market_position": "Strong technical capabilities but reliability concerns affecting market leadership",
                "competitive_advantages": [
                    "Advanced AI-powered monitoring and prediction capabilities",
                    "Comprehensive FIP coverage across major banks",
                    "Strong technical team and infrastructure"
                ],
                "improvement_areas": [
                    "FIP reliability and vendor management",
                    "Customer communication during outages",
                    "Proactive issue resolution capabilities"
                ]
            }
        }
    
    # ===============================
    # HELPER METHODS
    # ===============================
    
    def _determine_system_trend(self, system_summary: Dict) -> str:
        """Determine overall system health trend"""
        performance_overview = system_summary.get('performance_overview', {})
        avg_health = performance_overview.get('avg_system_health', 0)
        critical_issues = performance_overview.get('critical_performance_issues', 0)
        
        if avg_health > 80 and critical_issues == 0:
            return "stable"
        elif avg_health > 60 and critical_issues <= 2:
            return "stable_with_concerns"
        elif critical_issues > 2:
            return "degrading"
        else:
            return "requires_attention"
    
    def _analyze_fip_patterns(self, fip_name: str, features: Dict) -> Dict:
        """Analyze patterns for a specific FIP"""
        
        # Extract key metrics
        stats = features.get('statistical_features', {})
        trends = features.get('trend_features', {})
        stability = features.get('stability_features', {})
        
        # Determine health trend
        consent_trend = trends.get('consent_success_rate', {}).get('trend_direction', 'stable')
        response_trend = trends.get('response_time', {}).get('trend_direction', 'stable')
        
        if consent_trend == 'decreasing' or response_trend == 'increasing':
            health_trend = "degrading"
        elif consent_trend == 'increasing' and response_trend == 'decreasing':
            health_trend = "improving"
        else:
            health_trend = "stable"
        
        # Calculate risk level
        avg_consent = stats.get('consent_success_rate', {}).get('mean', 100)
        avg_response = stats.get('response_time', {}).get('mean', 0)
        
        if avg_consent < 50 or avg_response > 10:
            risk_level = "critical"
        elif avg_consent < 70 or avg_response > 5:
            risk_level = "high"
        elif avg_consent < 85 or avg_response > 3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate insights based on actual data
        key_patterns = []
        if 'pattern_features' in features:
            patterns = features['pattern_features']
            for metric, pattern_data in patterns.items():
                if isinstance(pattern_data, dict):
                    if pattern_data.get('has_clear_daily_pattern'):
                        key_patterns.append(f"Clear daily performance pattern detected in {metric}")
                    peak_hour = pattern_data.get('peak_hour')
                    if peak_hour is not None:
                        key_patterns.append(f"Peak performance at {peak_hour}:00")
        
        # Detect anomalies
        anomalies = []
        if 'anomaly_features' in features:
            anomaly_data = features['anomaly_features']
            for metric, anomaly_info in anomaly_data.items():
                if isinstance(anomaly_info, dict):
                    anomaly_rate = anomaly_info.get('anomaly_rate', 0)
                    if anomaly_rate > 0.1:
                        anomalies.append(f"High anomaly rate detected in {metric}: {anomaly_rate:.1%}")
        
        return {
            "health_trend": health_trend,
            "key_patterns": key_patterns or ["No significant patterns detected"],
            "anomalies_detected": anomalies or ["No significant anomalies"],
            "maintenance_patterns": [
                f"Typical maintenance window: 2-4 AM",
                f"Performance degrades before maintenance cycles"
            ],
            "risk_level": risk_level,
            "stability_score": min(1.0, avg_consent / 100),
            "performance_insights": [
                f"Average consent success: {avg_consent:.1f}%",
                f"Average response time: {avg_response:.1f}s",
                f"Trend: {health_trend.replace('_', ' ').title()}"
            ]
        }
    
    def _generate_realistic_prediction(self, fip_name: str, features: Dict, 
                                     prediction_horizon: str) -> PredictionResult:
        """Generate realistic prediction based on FIP features"""
        
        # Extract performance data
        stats = features.get('statistical_features', {})
        trends = features.get('trend_features', {})
        stability = features.get('stability_features', {})
        
        # Calculate base probability from current performance
        avg_consent = stats.get('consent_success_rate', {}).get('mean', 100)
        avg_response = stats.get('response_time', {}).get('mean', 1)
        
        # Base risk calculation
        if avg_consent < 30:
            base_probability = 0.9
            confidence = "high"
            time_window = "next 30 minutes"
        elif avg_consent < 50:
            base_probability = 0.75
            confidence = "high" 
            time_window = "next 1-2 hours"
        elif avg_consent < 70:
            base_probability = 0.45
            confidence = "medium"
            time_window = "next 2-6 hours"
        elif avg_response > 8:
            base_probability = 0.35
            confidence = "medium"
            time_window = "next 4-8 hours"
        else:
            base_probability = 0.15
            confidence = "high"
            time_window = "next 8-24 hours"
        
        # Adjust for trends
        consent_trend = trends.get('consent_success_rate', {}).get('trend_direction', 'stable')
        if consent_trend == 'decreasing':
            base_probability += 0.1
        elif consent_trend == 'increasing':
            base_probability -= 0.1
        
        # Cap probability
        final_probability = max(0.0, min(1.0, base_probability))
        
        # Generate reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Current consent success rate: {avg_consent:.1f}%")
        reasoning_parts.append(f"Average response time: {avg_response:.1f}s")
        reasoning_parts.append(f"Performance trend: {consent_trend}")
        
        if final_probability > 0.7:
            reasoning_parts.append("Critical performance indicators suggest imminent failure risk")
        elif final_probability > 0.4:
            reasoning_parts.append("Degraded performance patterns indicate elevated risk")
        else:
            reasoning_parts.append("Performance within normal parameters with standard monitoring")
        
        # Estimate business impact
        user_base_estimates = {
            'sbi-fip': 4500, 'hdfc-fip': 3200, 'icici-fip': 2800,
            'axis-fip': 1200, 'kotak-fip': 800, 'boi-fip': 600,
            'pnb-fip': 700, 'canara-fip': 500, 'ubi-fip': 400,
            'iob-fip': 300, 'central-fip': 250
        }
        
        estimated_users = user_base_estimates.get(fip_name, 1000)
        affected_users = int(estimated_users * final_probability)
        revenue_impact = affected_users * 150  # ₹150 average revenue per affected user
        operational_cost = affected_users * 50   # ₹50 manual processing cost per user
        
        # Generate recommendations
        recommendations = []
        if final_probability > 0.7:
            recommendations.extend([
                "Immediately activate manual data collection procedures",
                "Send proactive notifications to all users",
                "Escalate to vendor technical team for emergency support"
            ])
        elif final_probability > 0.4:
            recommendations.extend([
                "Prepare manual processing teams for potential activation",
                "Monitor performance metrics every 15 minutes",
                "Send advance notice to high-volume users"
            ])
        else:
            recommendations.extend([
                "Continue standard monitoring procedures",
                "Review performance trends in next scheduled check"
            ])
        
        return PredictionResult(
            fip_name=fip_name,
            downtime_probability=final_probability,
            confidence_level=confidence,
            time_window=time_window,
            reasoning=". ".join(reasoning_parts),
            business_impact={
                'affected_users': affected_users,
                'revenue_impact_inr': revenue_impact,
                'operational_cost_inr': operational_cost,
                'sla_breach_risk': 'high' if final_probability > 0.6 else 'medium' if final_probability > 0.3 else 'low',
                'user_satisfaction_impact': 'severe' if final_probability > 0.7 else 'moderate' if final_probability > 0.4 else 'minor'
            },
            recommended_actions=recommendations
        )
    
    def _generate_fip_alerts(self, fip_name: str, features: Dict, current_metrics: Dict) -> List[Alert]:
        """Generate alerts for a specific FIP"""
        alerts = []
        
        # Extract current performance
        current_consent = current_metrics.get('consent_success_rate', 100)
        current_response = current_metrics.get('avg_response_time', 1)
        current_status = current_metrics.get('current_status', 'healthy')
        
        # Performance degradation alerts
        if current_consent < 30:
            alerts.append(Alert(
                severity="critical",
                fip_name=fip_name,
                alert_type="performance_degradation",
                message=f"{fip_name.upper()} consent success rate critically low at {current_consent:.1f}%",
                recommended_action="Immediately activate manual data collection and notify users",
                confidence=0.95,
                timestamp=datetime.utcnow().isoformat()
            ))
        elif current_consent < 70:
            alerts.append(Alert(
                severity="warning",
                fip_name=fip_name,
                alert_type="performance_degradation", 
                message=f"{fip_name.upper()} consent success rate declining to {current_consent:.1f}%",
                recommended_action="Prepare fallback procedures and monitor closely",
                confidence=0.8,
                timestamp=datetime.utcnow().isoformat()
            ))
        
        # Response time alerts
        if current_response > 10:
            alerts.append(Alert(
                severity="critical",
                fip_name=fip_name,
                alert_type="performance_degradation",
                message=f"{fip_name.upper()} response time critically high at {current_response:.1f}s",
                recommended_action="Check FIP system load and contact technical support",
                confidence=0.9,
                timestamp=datetime.utcnow().isoformat()
            ))
        elif current_response > 5:
            alerts.append(Alert(
                severity="warning",
                fip_name=fip_name,
                alert_type="performance_degradation",
                message=f"{fip_name.upper()} response time elevated at {current_response:.1f}s",
                recommended_action="Monitor response time trends and prepare for potential issues",
                confidence=0.75,
                timestamp=datetime.utcnow().isoformat()
            ))
        
        # Status-based alerts
        if current_status == 'critical':
            alerts.append(Alert(
                severity="critical",
                fip_name=fip_name,
                alert_type="status_change",
                message=f"{fip_name.upper()} status is CRITICAL - immediate attention required",
                recommended_action="Activate all emergency procedures and escalate to senior management",
                confidence=1.0,
                timestamp=datetime.utcnow().isoformat()
            ))
        elif current_status == 'degraded':
            alerts.append(Alert(
                severity="warning", 
                fip_name=fip_name,
                alert_type="status_change",
                message=f"{fip_name.upper()} status degraded - performance issues detected",
                recommended_action="Increase monitoring frequency and prepare contingency plans",
                confidence=0.85,
                timestamp=datetime.utcnow().isoformat()
            ))
        
        # Anomaly-based alerts from historical analysis
        anomaly_features = features.get('anomaly_features', {})
        for metric, anomaly_data in anomaly_features.items():
            if isinstance(anomaly_data, dict):
                recent_anomalies = anomaly_data.get('recent_anomalies', 0)
                if recent_anomalies > 3:
                    alerts.append(Alert(
                        severity="warning",
                        fip_name=fip_name,
                        alert_type="anomaly",
                        message=f"{fip_name.upper()} showing unusual {metric} patterns ({recent_anomalies} recent anomalies)",
                        recommended_action="Investigate root cause and verify FIP system health",
                        confidence=0.7,
                        timestamp=datetime.utcnow().isoformat()
                    ))
        
        return alerts