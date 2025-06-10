from typing import Dict, List
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import threading
import time
# Import services
from services.bedrock_service import BedrockService
from services.metrics_service import MetricsService
from services.prometheus_service import PrometheusService
from models.predictions import db, Prediction
from utils.logger import logger
from services.backfill_historical_data import backfill_historical_metrics, GenerateHistoricalData
from services.predictor import predictor_main
# Load environment variables
load_dotenv()

from services.fip_ai_analytics_service import FIPAIAnalyticsService
from services.enhanced_bedrock_service import PredictionResult, Alert
from dataclasses import asdict
import asyncio
from functools import wraps


app = Flask(__name__)
# Update CORS configuration to allow requests from both ports
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "*"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///aa_gateway.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['USE_REAL_BEDROCK'] = os.getenv('USE_REAL_BEDROCK', 'false').lower() == 'true'

# Initialize SQLAlchemy with app
db.init_app(app)

# Initialize services
bedrock_service = BedrockService(use_mock=not app.config['USE_REAL_BEDROCK'])
metrics_service = MetricsService()
prometheus_service = PrometheusService()

# Initialize the AI Analytics service
ai_analytics_service = FIPAIAnalyticsService(
    prometheus_url=os.getenv('VICTORIAMETRICS_URL', 'http://victoriametrics:8428'),
    use_real_bedrock=app.config['USE_REAL_BEDROCK'],
    bedrock_region=os.getenv('AWS_REGION', 'us-east-1')
)

def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


# ================================
# API Routes
# ================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'bedrock': 'mock' if not app.config['USE_REAL_BEDROCK'] else 'real',
            'prometheus': 'active',
            'database': 'connected'
        }
    })

@app.route('/api/fips', methods=['GET'])
def get_fips():
    """Get all available FIPs with current status"""
    try:
        fips_data = metrics_service.get_all_fips_status()
        return jsonify({
            'success': True,
            'data': fips_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/fips/health', methods=['GET'])
def get_fips_health():
    """Get comprehensive FIP health analysis"""
    try:
        health_data = metrics_service.get_comprehensive_health()
        return jsonify({
            'success': True,
            'data': health_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/fips/predict', methods=['POST'])
# def predict_fip_issues():
#     """Generate AI predictions for FIP downtime"""
#     try:
#         request_data = request.get_json() or {}
#         selected_fips = request_data.get('fips', [])
#         time_horizon = request_data.get('time_horizon', '24h')
        
#         # Get current metrics for selected FIPs
#         metrics_data = metrics_service.get_fips_metrics(selected_fips)
        
#         # Generate AI predictions using Bedrock service
#         predictions = bedrock_service.predict_downtime(metrics_data, time_horizon)
        
#         # Store predictions in database
#         for fip_name, prediction in predictions.items():
#             prediction_record = Prediction(
#                 fip_name=fip_name,
#                 prediction_type='downtime',
#                 probability=prediction.get('downtime_prediction', {}).get('probability', 0),
#                 time_window=prediction.get('downtime_prediction', {}).get('time_window', ''),
#                 confidence=prediction.get('downtime_prediction', {}).get('confidence', 'medium'),
#                 raw_prediction=json.dumps(prediction)
#             )
#             db.session.add(prediction_record)
        
#         db.session.commit()
        
#         return jsonify({
#             'success': True,
#             'data': predictions,
#             'timestamp': datetime.utcnow().isoformat()
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/operations/impact', methods=['POST'])
# def get_business_impact():
#     """Calculate business impact of predicted outages"""
#     try:
#         request_data = request.get_json() or {}
#         predictions = request_data.get('predictions', {})
        
#         impact_analysis = bedrock_service.analyze_business_impact(predictions)
        
#         return jsonify({
#             'success': True,
#             'data': impact_analysis,
#             'timestamp': datetime.utcnow().isoformat()
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/alerts/proactive', methods=['GET'])
# def get_proactive_alerts():
#     """Get proactive alerts and recommendations"""
#     try:
#         # Get current metrics
#         current_metrics = metrics_service.get_all_fips_status()
        
#         # Generate proactive alerts
#         alerts = bedrock_service.generate_proactive_alerts(current_metrics)
        
#         return jsonify({
#             'success': True,
#             'data': alerts,
#             'timestamp': datetime.utcnow().isoformat()
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/recommendations', methods=['POST'])
# def get_recommendations():
    # """Get AI-powered operational recommendations"""
    # try:
    #     request_data = request.get_json() or {}
    #     current_situation = request_data.get('situation', {})
        
    #     recommendations = bedrock_service.generate_recommendations(current_situation)
        
    #     return jsonify({
    #         'success': True,
    #         'data': recommendations,
    #         'timestamp': datetime.utcnow().isoformat()
    #     })
    # except Exception as e:
    #     return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/metrics/push', methods=['POST'])
def push_metrics_to_prometheus():
    """Push mock metrics to Prometheus"""
    try:
        # Generate and push mock metrics
        metrics_generated = prometheus_service.push_mock_metrics()
        
        return jsonify({
            'success': True,
            'message': 'Mock metrics pushed to Prometheus',
            'metrics_count': metrics_generated,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/overview', methods=['GET'])
def get_system_overview():
    """Get system-wide overview and health score"""
    try:
        overview = bedrock_service.generate_system_overview()
        return jsonify({
            'success': True,
            'data': overview,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metrics/historical', methods=['POST'])
def push_historical_metrics():
    """Generate and push historical metrics to VictoriaMetrics"""
    try:
        logger.info("Pushing historical metrics to VictoriaMetrics")

        # backfill_historical_metrics()
        # g = GenerateHistoricalData()
        # g.generate_historical_data()
        predictor_main()
   
        return jsonify({
            'success': True,
            'message': 'Historical metrics generated and pushed to VictoriaMetrics',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ================================
# AI ANALYTICS API ROUTES
# ================================

@app.route('/api/analytics/comprehensive', methods=['POST'])
@async_route
async def get_comprehensive_analytics():
    """
    Generate comprehensive AI-powered analytics using historical data
    
    POST Body:
    {
        "days_back": 7,
        "prediction_horizon": "24h",
        "include_current_metrics": true
    }
    """
    try:
        request_data = request.get_json() or {}
        days_back = request_data.get('days_back', 7)
        prediction_horizon = request_data.get('prediction_horizon', '24h')
        include_current = request_data.get('include_current_metrics', True)
        
        logger.info(f"🔍 Generating comprehensive analytics for {days_back} days")
        
        # Generate comprehensive analysis
        result = await ai_analytics_service.generate_comprehensive_analysis(
            days_back=days_back,
            prediction_horizon=prediction_horizon,
            include_current_metrics=include_current
        )
        
        # Convert dataclasses to dictionaries for JSON serialization
        response_data = {
            'timestamp': result.timestamp,
            'time_range_analyzed': result.time_range_analyzed,
            'historical_patterns': result.historical_patterns,
            'predictions': {
                fip: {
                    'fip_name': pred.fip_name,
                    'downtime_probability': pred.downtime_probability,
                    'confidence_level': pred.confidence_level,
                    'time_window': pred.time_window,
                    'reasoning': pred.reasoning,
                    'business_impact': pred.business_impact,
                    'recommended_actions': pred.recommended_actions
                } for fip, pred in result.predictions.items()
            },
            'proactive_alerts': [asdict(alert) for alert in result.proactive_alerts],
            'business_insights': result.business_insights,
            'maintenance_windows': result.maintenance_windows,
            'summary': result.summary
        }
        
        return jsonify({
            'success': True,
            'data': response_data,
            'metadata': {
                'analysis_type': 'comprehensive',
                'days_analyzed': days_back,
                'prediction_horizon': prediction_horizon,
                'fips_analyzed': len(result.predictions),
                'alerts_generated': len(result.proactive_alerts)
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in comprehensive analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'comprehensive_analytics_error'
        }), 500

@app.route('/api/analytics/quick-insights', methods=['POST'])
@async_route
async def get_quick_insights():
    """
    Generate quick insights for immediate operational decisions
    
    POST Body:
    {
        "days_back": 3,
        "fip_filter": ["sbi-fip", "hdfc-fip"]  // optional
    }
    """
    try:
        request_data = request.get_json() or {}
        days_back = request_data.get('days_back', 3)
        fip_filter = request_data.get('fip_filter', None)
        
        logger.info(f"⚡ Generating quick insights for {days_back} days")
        
        result = await ai_analytics_service.generate_quick_insights(
            days_back=days_back,
            fip_filter=fip_filter
        )
        
        return jsonify({
            'success': True,
            'data': result,
            'metadata': {
                'analysis_type': 'quick_insights',
                'days_analyzed': days_back,
                'fips_filtered': fip_filter or 'all'
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in quick insights: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'quick_insights_error'
        }), 500

@app.route('/api/analytics/historical-patterns', methods=['POST'])
@async_route
async def analyze_historical_patterns():
    """
    Analyze historical patterns using AI without full predictions
    
    POST Body:
    {
        "days_back": 30,
        "pattern_types": ["maintenance", "performance", "anomalies"]
    }
    """
    try:
        request_data = request.get_json() or {}
        days_back = request_data.get('days_back', 30)
        pattern_types = request_data.get('pattern_types', ['maintenance', 'performance', 'anomalies'])
        
        logger.info(f"📊 Analyzing historical patterns for {days_back} days")
        
        # Extract historical data
        historical_data = ai_analytics_service.historical_analyzer.extract_historical_data(
            days_back=days_back,
            step="1h"
        )
        
        # Calculate features
        fip_features = ai_analytics_service.historical_analyzer.calculate_features(historical_data)
        
        # Detect maintenance windows
        maintenance_windows = ai_analytics_service.historical_analyzer.detect_maintenance_windows(historical_data)
        
        # Generate comprehensive report
        comprehensive_report = ai_analytics_service.historical_analyzer.generate_summary_report(
            historical_data, fip_features, maintenance_windows
        )
        
        # Analyze patterns with AI
        patterns = ai_analytics_service.bedrock_service.analyze_historical_patterns(comprehensive_report)
        
        # Filter results based on requested pattern types
        filtered_patterns = {}
        if 'maintenance' in pattern_types:
            filtered_patterns['maintenance_windows'] = maintenance_windows
            filtered_patterns['maintenance_insights'] = patterns.get('temporal_insights', {})
        
        if 'performance' in pattern_types:
            filtered_patterns['performance_patterns'] = patterns.get('system_wide_patterns', {})
            filtered_patterns['fip_performance'] = patterns.get('fip_specific_analysis', {})
        
        if 'anomalies' in pattern_types:
            filtered_patterns['anomaly_analysis'] = {
                fip: analysis.get('anomalies_detected', [])
                for fip, analysis in patterns.get('fip_specific_analysis', {}).items()
            }
        
        return jsonify({
            'success': True,
            'data': {
                'patterns': filtered_patterns,
                'analysis_summary': {
                    'time_range': comprehensive_report.get('time_range_analyzed', {}),
                    'fips_analyzed': len(fip_features),
                    'pattern_types': pattern_types,
                    'data_quality': comprehensive_report.get('system_summary', {}).get('data_quality', {})
                }
            },
            'metadata': {
                'analysis_type': 'historical_patterns',
                'days_analyzed': days_back,
                'pattern_types_requested': pattern_types
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in historical pattern analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'historical_patterns_error'
        }), 500

@app.route('/api/analytics/downtime-predictions', methods=['POST'])
@async_route
async def generate_downtime_predictions():
    """
    Generate AI-powered downtime predictions for specific FIPs
    
    POST Body:
    {
        "fips": ["sbi-fip", "hdfc-fip"],
        "prediction_horizon": "24h",
        "confidence_threshold": 0.7
    }
    """
    try:
        request_data = request.get_json() or {}
        target_fips = request_data.get('fips', [])
        prediction_horizon = request_data.get('prediction_horizon', '24h')
        confidence_threshold = request_data.get('confidence_threshold', 0.0)
        
        logger.info(f"🔮 Generating predictions for {len(target_fips)} FIPs")
        
        # Generate comprehensive analysis first
        full_analysis = await ai_analytics_service.generate_comprehensive_analysis(
            days_back=7,
            prediction_horizon=prediction_horizon,
            include_current_metrics=True
        )
        
        # Filter predictions based on requested FIPs and confidence
        filtered_predictions = {}
        for fip_name, prediction in full_analysis.predictions.items():
            if (not target_fips or fip_name in target_fips):
                confidence_score = {
                    'high': 0.9,
                    'medium': 0.7,
                    'low': 0.4
                }.get(prediction.confidence_level, 0.5)
                
                if confidence_score >= confidence_threshold:
                    filtered_predictions[fip_name] = {
                        'fip_name': prediction.fip_name,
                        'downtime_probability': prediction.downtime_probability,
                        'confidence_level': prediction.confidence_level,
                        'confidence_score': confidence_score,
                        'time_window': prediction.time_window,
                        'reasoning': prediction.reasoning,
                        'business_impact': prediction.business_impact,
                        'recommended_actions': prediction.recommended_actions,
                        'risk_category': 'critical' if prediction.downtime_probability > 0.8 else
                                       'high' if prediction.downtime_probability > 0.6 else
                                       'medium' if prediction.downtime_probability > 0.3 else 'low'
                    }
        
        # Calculate summary statistics
        if filtered_predictions:
            avg_probability = sum(p['downtime_probability'] for p in filtered_predictions.values()) / len(filtered_predictions)
            max_risk_fip = max(filtered_predictions.items(), key=lambda x: x[1]['downtime_probability'])
            total_affected_users = sum(p['business_impact'].get('affected_users', 0) for p in filtered_predictions.values())
        else:
            avg_probability = 0
            max_risk_fip = ('none', {'downtime_probability': 0})
            total_affected_users = 0
        
        return jsonify({
            'success': True,
            'data': {
                'predictions': filtered_predictions,
                'summary': {
                    'total_predictions': len(filtered_predictions),
                    'average_probability': round(avg_probability, 3),
                    'highest_risk_fip': max_risk_fip[0],
                    'highest_risk_probability': max_risk_fip[1]['downtime_probability'],
                    'total_users_at_risk': total_affected_users,
                    'prediction_horizon': prediction_horizon
                }
            },
            'metadata': {
                'analysis_type': 'downtime_predictions',
                'fips_requested': target_fips or 'all',
                'confidence_threshold': confidence_threshold,
                'prediction_horizon': prediction_horizon
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in downtime predictions: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'downtime_predictions_error'
        }), 500

@app.route('/api/analytics/proactive-alerts', methods=['POST'])
@async_route
async def generate_proactive_alerts():
    """
    Generate proactive alerts based on historical patterns and current state
    
    POST Body:
    {
        "severity_filter": ["critical", "warning"],
        "fips": ["sbi-fip", "hdfc-fip"],
        "include_recommendations": true
    }
    """
    try:
        request_data = request.get_json() or {}
        severity_filter = request_data.get('severity_filter', ['critical', 'warning', 'info'])
        target_fips = request_data.get('fips', [])
        include_recommendations = request_data.get('include_recommendations', True)
        
        logger.info(f"🚨 Generating proactive alerts with severity filter: {severity_filter}")
        
        # Get current metrics
        current_metrics = {}
        try:
            current_metrics = metrics_service.get_all_fips_status()
        except Exception as e:
            logger.warning(f"Could not fetch current metrics: {e}")
        
        # Generate quick analysis for alerts
        quick_insights = await ai_analytics_service.generate_quick_insights(
            days_back=3,
            fip_filter=target_fips if target_fips else None
        )
        
        # Extract alerts from insights
        alerts = quick_insights.get('critical_alerts', [])
        
        # Filter alerts by severity and FIP
        filtered_alerts = []
        for alert_data in alerts:
            if alert_data.get('severity') in severity_filter:
                if not target_fips or alert_data.get('fip_name') in target_fips:
                    # Enhance alert with additional context
                    enhanced_alert = {
                        **alert_data,
                        'generated_at': datetime.utcnow().isoformat(),
                        'alert_id': f"alert_{alert_data.get('fip_name', 'system')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        'business_impact': {
                            'estimated_users_affected': current_metrics.get(alert_data.get('fip_name', ''), {}).get('user_base', 0),
                            'urgency_level': 'immediate' if alert_data.get('severity') == 'critical' else 'high' if alert_data.get('severity') == 'warning' else 'medium'
                        }
                    }
                    
                    if include_recommendations:
                        enhanced_alert['detailed_recommendations'] = [
                            alert_data.get('recommended_action', 'Monitor situation'),
                            'Document incident for pattern analysis',
                            'Notify relevant stakeholders' if alert_data.get('severity') == 'critical' else 'Continue monitoring'
                        ]
                    
                    filtered_alerts.append(enhanced_alert)
        
        # Sort alerts by severity and confidence
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        filtered_alerts.sort(key=lambda x: (
            severity_order.get(x.get('severity', 'info'), 3),
            -x.get('confidence', 0)
        ))
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': filtered_alerts,
                'summary': {
                    'total_alerts': len(filtered_alerts),
                    'critical_count': len([a for a in filtered_alerts if a.get('severity') == 'critical']),
                    'warning_count': len([a for a in filtered_alerts if a.get('severity') == 'warning']),
                    'info_count': len([a for a in filtered_alerts if a.get('severity') == 'info']),
                    'fips_with_alerts': list(set(a.get('fip_name') for a in filtered_alerts if a.get('fip_name'))),
                    'highest_priority_alert': filtered_alerts[0] if filtered_alerts else None
                }
            },
            'metadata': {
                'analysis_type': 'proactive_alerts',
                'severity_filter': severity_filter,
                'fips_requested': target_fips or 'all',
                'include_recommendations': include_recommendations
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error generating proactive alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'proactive_alerts_error'
        }), 500

@app.route('/api/analytics/business-insights', methods=['POST'])
@async_route
async def get_business_insights():
    """
    Generate business-focused insights and strategic recommendations
    
    POST Body:
    {
        "insight_categories": ["executive", "operational", "strategic"],
        "time_horizon": "quarterly"
    }
    """
    try:
        request_data = request.get_json() or {}
        insight_categories = request_data.get('insight_categories', ['executive', 'operational', 'strategic'])
        time_horizon = request_data.get('time_horizon', 'monthly')
        
        # Map time horizons to days
        time_map = {
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365
        }
        days_back = time_map.get(time_horizon, 30)
        
        logger.info(f"💼 Generating business insights for {time_horizon} period")
        
        # Generate comprehensive analysis
        full_analysis = await ai_analytics_service.generate_comprehensive_analysis(
            days_back=days_back,
            prediction_horizon="7d",  # Weekly outlook for business planning
            include_current_metrics=True
        )
        
        # Extract business insights
        business_insights = full_analysis.business_insights
        
        # Filter insights by requested categories
        filtered_insights = {}
        
        if 'executive' in insight_categories:
            filtered_insights['executive'] = {
                'summary': business_insights.get('executive_summary', {}),
                'key_decisions': business_insights.get('executive_summary', {}).get('immediate_decisions_needed', []),
                'financial_impact': business_insights.get('executive_summary', {}).get('financial_impact_next_24h', {}),
                'risk_assessment': full_analysis.summary.get('business_impact', {})
            }
        
        if 'operational' in insight_categories:
            filtered_insights['operational'] = {
                'resource_optimization': business_insights.get('operational_insights', {}).get('resource_optimization', []),
                'automation_opportunities': business_insights.get('operational_insights', {}).get('automation_opportunities', []),
                'monitoring_improvements': business_insights.get('operational_insights', {}).get('monitoring_improvements', []),
                'immediate_actions': _extract_operational_actions(full_analysis)
            }
        
        if 'strategic' in insight_categories:
            filtered_insights['strategic'] = {
                'infrastructure_investments': business_insights.get('strategic_recommendations', {}).get('infrastructure_investments', []),
                'process_improvements': business_insights.get('strategic_recommendations', {}).get('process_improvements', []),
                'vendor_management': business_insights.get('strategic_recommendations', {}).get('vendor_management', []),
                'competitive_analysis': business_insights.get('competitive_analysis', {})
            }
        
        # Add performance metrics
        performance_summary = {
            'system_health_score': full_analysis.summary.get('key_statistics', {}).get('average_system_health', 0),
            'reliability_trend': full_analysis.summary.get('trend_direction', 'stable'),
            'user_impact_projection': sum(
                pred.business_impact.get('affected_users', 0) 
                for pred in full_analysis.predictions.values()
            ),
            'cost_impact_projection': sum(
                pred.business_impact.get('revenue_impact_inr', 0) 
                for pred in full_analysis.predictions.values()
            )
        }
        
        return jsonify({
            'success': True,
            'data': {
                'insights': filtered_insights,
                'performance_summary': performance_summary,
                'recommendations_summary': {
                    'high_priority_actions': len([
                        alert for alert in full_analysis.proactive_alerts 
                        if alert.severity == 'critical'
                    ]),
                    'strategic_investments_needed': len(
                        business_insights.get('strategic_recommendations', {}).get('infrastructure_investments', [])
                    ),
                    'operational_improvements_identified': len(
                        business_insights.get('operational_insights', {}).get('automation_opportunities', [])
                    )
                }
            },
            'metadata': {
                'analysis_type': 'business_insights',
                'time_horizon': time_horizon,
                'days_analyzed': days_back,
                'insight_categories': insight_categories
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error generating business insights: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'business_insights_error'
        }), 500

@app.route('/api/analytics/scheduled-report', methods=['POST'])
@async_route
async def generate_scheduled_report():
    """
    Generate scheduled reports for different stakeholders
    
    POST Body:
    {
        "report_type": "weekly",
        "recipients": ["executives", "operations"],
        "include_appendix": true
    }
    """
    try:
        request_data = request.get_json() or {}
        report_type = request_data.get('report_type', 'daily')
        recipients = request_data.get('recipients', ['operations'])
        include_appendix = request_data.get('include_appendix', False)
        
        logger.info(f"📊 Generating {report_type} report for {recipients}")
        
        # Generate the report
        report = await ai_analytics_service.generate_scheduled_report(
            report_type=report_type,
            recipients=recipients
        )
        
        # Remove appendix if not requested to reduce response size
        if not include_appendix and 'appendix' in report:
            del report['appendix']
        
        # Add export options
        report['export_options'] = {
            'pdf_available': True,
            'excel_available': True,
            'email_distribution': True,
            'dashboard_integration': True
        }
        
        return jsonify({
            'success': True,
            'data': report,
            'metadata': {
                'analysis_type': 'scheduled_report',
                'report_type': report_type,
                'recipients': recipients,
                'appendix_included': include_appendix,
                'report_size': 'full' if include_appendix else 'summary'
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error generating scheduled report: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'scheduled_report_error'
        }), 500

@app.route('/api/analytics/prediction-accuracy', methods=['GET'])
@async_route
async def monitor_prediction_accuracy():
    """
    Monitor prediction accuracy and model performance
    """
    try:
        prediction_window_hours = request.args.get('window_hours', 24, type=int)
        
        logger.info(f"📈 Monitoring prediction accuracy for {prediction_window_hours} hours")
        
        accuracy_report = await ai_analytics_service.monitor_predictions_accuracy(
            prediction_window_hours=prediction_window_hours
        )
        
        return jsonify({
            'success': True,
            'data': accuracy_report,
            'metadata': {
                'analysis_type': 'prediction_accuracy',
                'window_hours': prediction_window_hours
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error monitoring prediction accuracy: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'prediction_accuracy_error'
        }), 500

@app.route('/api/analytics/maintenance-schedule', methods=['POST'])
@async_route
async def get_maintenance_schedule():
    """
    Get predicted maintenance schedules based on historical patterns
    
    POST Body:
    {
        "days_back": 60,
        "forecast_days": 30
    }
    """
    try:
        request_data = request.get_json() or {}
        days_back = request_data.get('days_back', 60)
        forecast_days = request_data.get('forecast_days', 30)
        
        logger.info(f"🔧 Analyzing maintenance patterns for {days_back} days")
        
        # Extract historical data
        historical_data = ai_analytics_service.historical_analyzer.extract_historical_data(
            days_back=days_back,
            step="1h"
        )
        
        # Detect maintenance windows
        maintenance_windows = ai_analytics_service.historical_analyzer.detect_maintenance_windows(historical_data)
        
        # Generate future maintenance predictions
        maintenance_predictions = {}
        for fip_name, windows in maintenance_windows.items():
            if windows:
                # Extract patterns and predict future windows
                next_windows = []
                for window in windows:
                    if window['type'] == 'recurring_hourly':
                        next_windows.append({
                            'predicted_date': 'This weekend',
                            'hours': window['hours'],
                            'confidence': window['confidence'],
                            'type': 'recurring',
                            'impact_estimate': 'medium'
                        })
                    elif window['type'] == 'recurring_daily':
                        next_windows.append({
                            'predicted_date': f"Next {', '.join(window.get('day_names', []))}",
                            'days': window.get('day_names', []),
                            'confidence': window['confidence'],
                            'type': 'scheduled',
                            'impact_estimate': 'high'
                        })
                
                maintenance_predictions[fip_name] = {
                    'historical_patterns': windows,
                    'upcoming_predictions': next_windows,
                    'maintenance_frequency': len(windows),
                    'reliability_score': 1.0 - (len(windows) * 0.1)  # Simple scoring
                }
        
        return jsonify({
            'success': True,
            'data': {
                'maintenance_schedule': maintenance_predictions,
                'system_summary': {
                    'total_fips_analyzed': len(maintenance_windows),
                    'fips_with_patterns': len([w for w in maintenance_windows.values() if w]),
                    'total_patterns_detected': sum(len(w) for w in maintenance_windows.values()),
                    'forecast_period_days': forecast_days
                }
            },
            'metadata': {
                'analysis_type': 'maintenance_schedule',
                'days_analyzed': days_back,
                'forecast_days': forecast_days
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting maintenance schedule: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'maintenance_schedule_error'
        }), 500

# ================================
# HELPER FUNCTIONS
# ================================

def _extract_operational_actions(analysis) -> List[Dict]:
    """Extract operational actions from analysis"""
    actions = []
    
    # From critical alerts
    for alert in analysis.proactive_alerts:
        if alert.severity == 'critical':
            actions.append({
                'action': alert.recommended_action,
                'fip_name': alert.fip_name,
                'urgency': 'immediate',
                'category': 'incident_response'
            })
    
    # From high-risk predictions
    for fip_name, pred in analysis.predictions.items():
        if pred.downtime_probability > 0.7:
            actions.append({
                'action': pred.recommended_actions[0] if pred.recommended_actions else 'Monitor closely',
                'fip_name': fip_name,
                'urgency': 'high',
                'category': 'preventive_action'
            })
    
    return actions[:10]  # Return top 10 actions

# ================================
# BACKGROUND TASK FOR CONTINUOUS MONITORING
# ================================

def background_ai_analytics_updater():
    """Background task to continuously update AI analytics"""
    with app.app_context():
        while True:
            try:
                # Run quick insights every 30 minutes
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    insights = loop.run_until_complete(
                        ai_analytics_service.generate_quick_insights(days_back=1)
                    )
                    
                    # Log key insights
                    if insights.get('immediate_concerns'):
                        logger.warning(f"🚨 {len(insights['immediate_concerns'])} immediate concerns detected")
                    
                    if insights.get('risk_summary', {}).get('overall_risk') in ['high', 'critical']:
                        logger.error(f"⚠️ System risk level: {insights['risk_summary']['overall_risk']}")
                
                finally:
                    loop.close()
                
                time.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in background AI analytics updater: {e}")
                time.sleep(600)  # Retry after 10 minutes


# ================================
# Background Tasks
# ================================

def background_metrics_generator():
    """Background task to continuously generate realistic metrics"""
    with app.app_context():
        while True:
            try:
                # Update FIP metrics every 2 minutes
                metrics_service.update_fip_metrics()
                time.sleep(120)  # 2 minutes
            except Exception as e:
                logger.error(f"Error in background metrics generator: {e}")
                time.sleep(60)  # Retry after 1 minute

def background_predictions_updater():
    """Background task to update predictions every 15 minutes"""
    with app.app_context():
        while True:
            try:
                # Generate fresh predictions for all FIPs
                all_fips = metrics_service.get_all_fips_status()
                fip_names = list(all_fips.keys())
                
                metrics_data = metrics_service.get_fips_metrics(fip_names)
                predictions = bedrock_service.predict_downtime(metrics_data, '24h')
                
                # Store in database
                for fip_name, prediction in predictions.items():
                    prediction_record = Prediction(
                        fip_name=fip_name,
                        prediction_type='downtime',
                        probability=prediction.get('downtime_prediction', {}).get('probability', 0),
                        time_window=prediction.get('downtime_prediction', {}).get('time_window', ''),
                        confidence=prediction.get('downtime_prediction', {}).get('confidence', 'medium'),
                        raw_prediction=json.dumps(prediction)
                    )
                    db.session.add(prediction_record)
                
                db.session.commit()
                logger.info(f"Updated predictions for {len(predictions)} FIPs")
                
                time.sleep(900)  # 15 minutes
            except Exception as e:
                logger.error(f"Error in background predictions updater: {e}")
                time.sleep(300)  # Retry after 5 minutes

# ================================
# Initialize Database and Start Background Tasks
# ================================

def init_app():
    """Initialize the application"""
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Start background tasks
        metrics_thread = threading.Thread(target=background_metrics_generator, daemon=True)
        predictions_thread = threading.Thread(target=background_predictions_updater, daemon=True)
        
        # # Start AI analytics background task
        # ai_thread = threading.Thread(target=background_ai_analytics_updater, daemon=True)
        # ai_thread.start()

        metrics_thread.start()
        predictions_thread.start()
        
        logger.info("AA Gateway AI Operations API started successfully!")
        logger.info(f"Using {'Real' if app.config['USE_REAL_BEDROCK'] else 'Mock'} Bedrock service")

if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
