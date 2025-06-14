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
import random
# Import services
from utils.helpers import get_fip_status_from_success_rate, get_fip_response
from services.bedrock_service import BedrockService
from services.metrics_service import MetricsService
from services.prometheus_service import PrometheusService
from models import db
from models.predictions import Prediction
from utils.logger import logger
from services.backfill_historical_data import backfill_historical_metrics, GenerateHistoricalData
from services.predictor import predictor_main
# Load environment variables
load_dotenv()

from services.fip_ai_analytics_service import FIPAIAnalyticsService
from services.enhanced_bedrock_service import PredictionResult, Alert
from services.alert_service import AlertService, AlertMetrics, AlertContext
from dataclasses import asdict
import asyncio
from functools import wraps
from utils.enums import PredictionType
from models.webhook import WebhookSubscription
import requests


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
app.config['USE_REAL_BEDROCK'] = os.getenv('USE_REAL_BEDROCK', 'false').lower() == 'True'

# Initialize SQLAlchemy with app
db.init_app(app)

# Initialize services
bedrock_service = BedrockService(use_mock=not app.config['USE_REAL_BEDROCK'])
metrics_service = MetricsService()
prometheus_service = PrometheusService()
alert_service = AlertService()

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
        # Get base FIP list from metrics service for structure
        base_fips = metrics_service.get_all_fips_status()
        
        # Get historical data for the last hour
        historical_data = ai_analytics_service.historical_analyzer.extract_historical_data(
            days_back=1,  # Last 24 hours
            step="1m"     # 1-minute resolution
        )
        # logger.info(f"Historical data: {historical_data}")
        
        # Calculate features from historical data
        fip_features = ai_analytics_service.historical_analyzer.calculate_features(historical_data)

        fips_data = get_fip_response(base_fips, fip_features)

        return jsonify({
            'success': True,
            'data': fips_data,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics_source': 'historical_analyzer'
        })
    except Exception as e:
        logger.error(f"Error in get_fips: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fips/predict', methods=['POST'])
def predict_fip_issues():
    """Get predictions for selected FIPs"""
    try:
        request_data = request.get_json() or {}
        selected_fips = request_data.get('fips', [])
        time_horizon = request_data.get('time_horizon', '24h')

        # Get predictions from database
        predictions = {}
        
        # If no FIPs selected, get predictions for all FIPs
        if not selected_fips:
            # Get all predictions ordered by created_at
            all_predictions = Prediction.query.filter_by(
                prediction_type=PredictionType.DOWNTIME
            ).order_by(Prediction.created_at.desc()).all()
            
            # Get latest prediction for each FIP
            for prediction in all_predictions:
                if prediction.fip_name not in predictions:
                    predictions[prediction.fip_name] = json.loads(prediction.raw_prediction)
        else:
            # Get predictions for selected FIPs
            for fip_name in selected_fips:
                prediction = Prediction.query.filter_by(
                    fip_name=fip_name,
                    prediction_type=PredictionType.DOWNTIME
                ).order_by(Prediction.created_at.desc()).first()
                
                if prediction:
                    predictions[fip_name] = json.loads(prediction.raw_prediction)
        
        return jsonify({
            'success': True,
            'data': predictions,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        print(f"Error in predict_fip_issues: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/api/fips/predictions/hourly', methods=['POST'])
def get_fip_predictions_hourly():
    """Get hourly predictions for all FIPs"""
    try:
        # Get hours parameter, default to 24 if not provided
        request_data = request.get_json() or {}
        hours = request_data.get('hours', 24)
        
        # Get all predictions
        predictions = Prediction.query.filter_by(
            prediction_type=PredictionType.DOWNTIME
        ).order_by(Prediction.created_at.desc()).all()
        
        # Initialize hourly predictions structure
        hourly_predictions = {}
        
        # Process each prediction
        for prediction in predictions:
            try:                
                pred_data = json.loads(prediction.raw_prediction)
                downtime_pred = pred_data.get('downtime_prediction', {})
                time_window = downtime_pred.get('time_window', '')
                is_maintenece = random.choices([True, False], weights=[80, 20])[0]
                
                                
                # Extract hours from time window (e.g., "next 6-8 hours" -> [6,7,8])
                if 'next' in time_window.lower() and 'hours' in time_window.lower():
                    # Extract numbers from the time window, handling hyphenated ranges
                    try:
                        # First split by spaces and find the part with numbers
                        parts = time_window.lower().split()
                        number_part = next((part for part in parts if any(c.isdigit() for c in part)), '')
                        
                        if '-' in number_part:
                            # Handle hyphenated range (e.g., "6-8")
                            start, end = map(int, number_part.split('-'))
                            numbers = [start, end]
                        else:
                            # Handle single number
                            numbers = [int(n) for n in number_part if n.isdigit()]
                                                
                        if len(numbers) >= 2:
                            start_hour, end_hour = numbers[0], numbers[1]
                            # Generate list of hours
                            hours_list = list(range(start_hour, end_hour + 1))
                            
                            # Add prediction to each hour
                            for hour in hours_list:
                                if hour <= hours:  # Only include hours within requested range
                                    if hour not in hourly_predictions:
                                        hourly_predictions[hour] = {}
                                    
                                    hourly_predictions[hour][prediction.fip_name] = {
                                        'probability': downtime_pred.get('probability', 0),
                                        'confidence': downtime_pred.get('confidence', 'medium'),
                                        'reasoning': downtime_pred.get('reasoning', ''),
                                        'isMaintenence': is_maintenece if downtime_pred.get('probability', 0) > 0.7 else False, # If confidence is low then always `False`
                                        'timeWindow': time_window,
                                    }
                                    logger.info(f"Added prediction for hour {hour}, FIP {prediction.fip_name}")
                        else:
                            logger.warning(f"Could not extract valid hour range from time window: {time_window}")
                    except Exception as e:
                        logger.error(f"Error parsing time window '{time_window}': {str(e)}")
                else:
                    logger.warning(f"Invalid time window format: {time_window}")
            except Exception as e:
                logger.error(f"Error processing prediction {prediction.id} for {prediction.fip_name}: {str(e)}")
                continue
        
        # Convert to list format and sort by hour
        response_data = [
            {
                'hour': hour,
                'predictions': predictions
            }
            for hour, predictions in sorted(hourly_predictions.items())
        ]
        
        logger.info(f"Generated response with {len(response_data)} hours of predictions")
        
        return jsonify({
            'success': True,
            'data': response_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_fip_predictions_hourly: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/operations/impact', methods=['POST'])
def get_business_impact():
    """Calculate business impact of predicted outages"""
    try:
        request_data = request.get_json() or {}
        predictions = request_data.get('predictions', {})
        
        impact_analysis = bedrock_service.analyze_business_impact(predictions)
        
        return jsonify({
            'success': True,
            'data': impact_analysis,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/proactive', methods=['GET'])
def get_proactive_alerts():
    """Get proactive alerts and recommendations"""
    try:
        # Get current metrics
        current_metrics = metrics_service.get_all_fips_status()
        
        # Get historical data for analysis
        historical_data = ai_analytics_service.historical_analyzer.extract_historical_data(
            days_back=1,  # Last 24 hours
            step="1m"     # 1-minute resolution
        )
        
        # Generate alerts using AlertService
        alerts = alert_service.generate_alerts(historical_data, current_metrics)
        
        # Convert alerts to dictionary format for JSON response
        alert_dicts = [
            {
                'alert_id': alert.alert_id,
                'fip_name': alert.fip_name,
                'severity': alert.severity,
                'alert_type': alert.alert_type,
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
                'recommended_actions': alert.recommended_actions,
                'timestamp': alert.timestamp,
                'confidence': alert.confidence
            }
            for alert in alerts
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alert_dicts,
                'summary': {
                    'total_alerts': len(alert_dicts),
                    'critical_alerts': len([a for a in alert_dicts if a['severity'] == 'critical']),
                    'warning_alerts': len([a for a in alert_dicts if a['severity'] == 'warning']),
                    'info_alerts': len([a for a in alert_dicts if a['severity'] == 'info']),
                    'affected_fips': len(set(a['fip_name'] for a in alert_dicts))
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_proactive_alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get AI-powered operational recommendations"""
    try:
        request_data = request.get_json() or {}
        current_situation = request_data.get('situation', {})
        
        recommendations = bedrock_service.generate_recommendations(current_situation)
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

        backfill_historical_metrics()
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

@app.route('/api/webhooks', methods=['GET'])
def get_webhook_subscriptions():
    """Get all webhook subscriptions"""
    try:
        subscriptions = WebhookSubscription.query.all()
        return jsonify({
            'success': True,
            'data': [subscription.to_dict() for subscription in subscriptions],
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webhooks', methods=['POST'])
def create_webhook_subscription():
    """Create a new webhook subscription"""
    try:
        data = request.get_json()
        subscription = WebhookSubscription(
            name=data['name'],
            url=data['url'],
            method=data.get('method', 'POST'),
            headers=data.get('headers', {}),
            enabled=data.get('enabled', True),
            alert_types=data.get('alertTypes', ['critical', 'warning', 'info'])
        )
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': 'Webhook subscription created successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webhooks/<subscription_id>', methods=['PUT'])
def update_webhook_subscription(subscription_id):
    """Update a webhook subscription"""
    try:
        data = request.get_json()
        subscription = WebhookSubscription.query.get(subscription_id)
        if not subscription:
            return jsonify({'success': False, 'error': 'Subscription not found'}), 404
            
        subscription.name = data.get('name', subscription.name)
        subscription.url = data.get('url', subscription.url)
        subscription.method = data.get('method', subscription.method)
        subscription.headers = data.get('headers', subscription.headers)
        subscription.enabled = data.get('enabled', subscription.enabled)
        subscription.alert_types = data.get('alertTypes', subscription.alert_types)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': 'Webhook subscription updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webhooks/<subscription_id>', methods=['DELETE'])
def delete_webhook_subscription(subscription_id):
    """Delete a webhook subscription"""
    try:
        subscription = WebhookSubscription.query.get(subscription_id)
        if not subscription:
            return jsonify({'success': False, 'error': 'Subscription not found'}), 404
            
        db.session.delete(subscription)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Webhook subscription deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webhooks/test', methods=['POST'])
def test_webhook():
    """Test a webhook subscription"""
    try:
        data = request.get_json()
        url = data.get('url')
        method = data.get('method', 'POST')
        headers = data.get('headers', {})
        
        # Send test notification
        test_data = {
            'type': 'test',
            'message': 'This is a test notification',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        response = requests.request(
            method=method,
            url=url,
            json=test_data,
            headers=headers,
            timeout=5
        )
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'response': response.text,
            'message': 'Test notification sent successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webhooks/test-all', methods=['POST'])
def test_all_webhooks():
    """Test all enabled webhook subscriptions with a test alert"""
    try:
        # Create a test alert
        test_alert = Alert(
            alert_id=f"test_alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            fip_name="test-fip",
            severity="info",
            alert_type="test_notification",
            message="This is a test alert notification",
            metrics=AlertMetrics(
                current_rate=95.0,
                historical_avg=90.0,
                deviation=5.0,
                threshold=70.0
            ),
            context=AlertContext(
                affected_users=0,
                business_impact="No impact - test notification",
                historical_pattern="Test pattern",
                peak_hour=datetime.utcnow().hour
            ),
            recommended_actions=["No action needed - test notification"],
            timestamp=datetime.utcnow().isoformat(),
            confidence=1.0
        )
        
        # Send test alert to all enabled webhooks
        alert_service.notify_webhooks(test_alert)
        
        return jsonify({
            'success': True,
            'message': 'Test alert sent to all enabled webhooks'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/notify', methods=['POST'])
def notify_alert_to_webhooks(alert_id):
    """Send a specific alert to all enabled webhooks"""
    try:
        # Check if content type is JSON
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 415

        # Get alert data from request body
        alert_data = request.get_json(force=True)  # force=True will handle requests without proper content-type
        if not alert_data:
            return jsonify({
                'success': False,
                'error': 'Alert data is required'
            }), 400

        # Get all enabled webhooks
        subscriptions = WebhookSubscription.query.filter_by(enabled=True).all()
        
        # Send alert to each enabled webhook
        for subscription in subscriptions:
            if alert_data.get('severity') in subscription.alert_types:
                try:
                    # Send webhook notification
                    response = requests.request(
                        method=subscription.method,
                        url=subscription.url,
                        json=alert_data,
                        headers=subscription.headers or {},
                        timeout=5
                    )
                    
                    if response.status_code >= 400:
                        logger.error(f"Webhook notification failed for {subscription.url}: {response.text}")
                except Exception as e:
                    logger.error(f"Error sending webhook notification to {subscription.url}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Alert {alert_id} sent to all enabled webhooks'
        })
    except Exception as e:
        logger.error(f"Error in notify_alert_to_webhooks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
                # clear the predictions table
                db.session.query(Prediction).delete()
                db.session.commit()

                # Get historical data
                historical_data = ai_analytics_service.get_historical_data(days_back=30, step="15m")
                fip_features = ai_analytics_service.get_fip_features(historical_data)
                # Generate predictions for all FIPs
                predictions = bedrock_service.predict_downtime(fip_features, '24h')
                
                # Store predictions in database
                for fip_name, prediction in predictions.items():
                    prediction_record = Prediction(
                        fip_name=fip_name,
                        prediction_type=PredictionType.DOWNTIME,
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

if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
