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
from utils.helpers import get_fip_status_from_success_rate
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
from utils.enums import PredictionType


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
        
        # Initialize real metrics
        fips_data = {}
        
        # Process each FIP
        for fip_name, base_info in base_fips.items():
            try:
                features = fip_features.get(fip_name, {})
                # logger.info(f"Features: {features}")
                
                # Get latest metrics from statistical features
                stats = features.get('statistical_features', {})
                consent_stats = stats.get('consent_success_rate', {})
                data_fetch_stats = stats.get('data_fetch_success_rate', {})
                response_stats = stats.get('response_time', {})
                
                # Get trend information
                trend_features = features.get('trend_features', {})
                consent_trend = trend_features.get('consent_success_rate', {})
                
                # Get stability information
                stability = features.get('stability_features', {})
                # logger.info(f"Stability: {stability}")
                status_analysis = stability.get('status_analysis', {})
                
                stability['overall_stability']['stability_grade'] = get_fip_status_from_success_rate(data_fetch_stats.get('mean', base_info['data_fetch_success_rate']), consent_stats.get('mean', base_info['consent_success_rate']))
                # Determine current status based on health score
                health_score = stability.get('overall_stability', {}).get('stability_grade', 'fair')
                current_status = 'healthy' if health_score == 'excellent' else \
                               'degraded' if health_score == 'fair' else \
                               'critical' if health_score == 'poor' else 'warning'
                
                
                # Create FIP data structure with real metrics
                fips_data[fip_name] = {
                    'fip_name': fip_name,
                    'bank_name': base_info['bank_name'],
                    'consent_success_rate': round(consent_stats.get('mean', base_info['consent_success_rate']), 1),
                    'data_fetch_success_rate': round(data_fetch_stats.get('mean', base_info['data_fetch_success_rate']), 1),
                    'avg_response_time': round(response_stats.get('mean', base_info['avg_response_time']), 2),
                    'error_rate': round(100 - consent_stats.get('mean', 100 - base_info['error_rate']), 1),
                    'current_status': current_status,
                    'user_base': base_info['user_base'],
                    'last_updated': datetime.utcnow().isoformat(),
                    'trend': consent_trend.get('trend_direction', 'stable'),
                    'maintenance_window': base_info.get('maintenance_window', False),
                    'health_metrics': {
                        'health_score': round(status_analysis.get('stability_score', 0.5) * 10, 1),
                        'reliability': round(status_analysis.get('healthy_time_pct', 50), 1),
                        'volatility': round(status_analysis.get('status_volatility', 0.5), 2),
                        'performance_grade': stability.get('overall_stability', {}).get('stability_grade', 'fair')
                    }
                }
                
            except Exception as e:
                logger.warning(f"Error processing historical data for {fip_name}: {e}")
                # Fallback to base metrics if processing fails
                fips_data[fip_name] = base_info

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
        
        # Generate proactive alerts
        alerts = bedrock_service.generate_proactive_alerts(current_metrics)
        
        return jsonify({
            'success': True,
            'data': alerts,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
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
        logger.info(f"Using {'Real' if app.config['USE_REAL_BEDROCK'] else 'Mock'} Bedrock service")

if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
