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
from models.predictions import db, Prediction, FIPMetrics
from utils.logger import logger

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

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

@app.route('/api/fips/predict', methods=['POST'])
def predict_fip_issues():
    """Generate AI predictions for FIP downtime"""
    try:
        request_data = request.get_json() or {}
        selected_fips = request_data.get('fips', [])
        time_horizon = request_data.get('time_horizon', '24h')
        
        # Get current metrics for selected FIPs
        metrics_data = metrics_service.get_fips_metrics(selected_fips)
        
        # Generate AI predictions using Bedrock service
        predictions = bedrock_service.predict_downtime(metrics_data, time_horizon)
        
        # Store predictions in database
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
        
        return jsonify({
            'success': True,
            'data': predictions,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
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
        
        metrics_thread.start()
        predictions_thread.start()
        
        logger.info("AA Gateway AI Operations API started successfully!")
        logger.info(f"Using {'Real' if app.config['USE_REAL_BEDROCK'] else 'Mock'} Bedrock service")

if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
