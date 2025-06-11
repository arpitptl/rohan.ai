import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from utils.logger import logger
from config import Config
# def format_currency(amount: float, currency: str = '₹') -> str:
#     """
#     Format currency amounts for display
#     """
#     if amount >= 100000:  # 1 lakh or more
#         return f"{currency}{amount/100000:.1f}L"
#     elif amount >= 1000:  # 1 thousand or more
#         return f"{currency}{amount/1000:.1f}K"
#     else:
#         return f"{currency}{amount:.0f}"

def calculate_time_ago(timestamp: str) -> str:
    """
    Calculate human-readable time ago string
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except:
        return "Unknown"

def validate_fip_name(fip_name: str) -> bool:
    """
    Validate FIP name format
    """
    if not fip_name:
        return False
    
    # Should end with -fip and contain valid bank code
    if not fip_name.endswith('-fip'):
        return False
    
    valid_banks = [
        'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'boi', 
        'pnb', 'canara', 'ubi', 'iob', 'central'
    ]
    
    bank_code = fip_name.replace('-fip', '')
    return bank_code in valid_banks

def generate_alert_id(fip_name: str, alert_type: str) -> str:
    """
    Generate unique alert ID
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{fip_name}_{alert_type}_{timestamp}"

def parse_time_window(time_window: str) -> timedelta:
    """
    Parse time window string to timedelta
    """
    try:
        if 'minute' in time_window:
            minutes = int(''.join(filter(str.isdigit, time_window)))
            return timedelta(minutes=minutes)
        elif 'hour' in time_window:
            hours = int(''.join(filter(str.isdigit, time_window)))
            return timedelta(hours=hours)
        elif 'day' in time_window:
            days = int(''.join(filter(str.isdigit, time_window)))
            return timedelta(days=days)
        else:
            return timedelta(hours=1)  # Default to 1 hour
    except:
        return timedelta(hours=1)

def get_risk_color(probability: float) -> str:
    """
    Get color code for risk probability
    """
    if probability >= 0.7:
        return '#ef4444'  # Red
    elif probability >= 0.4:
        return '#f59e0b'  # Yellow
    else:
        return '#10b981'  # Green

def calculate_business_impact_score(affected_users: int, processing_cost: float, downtime_hours: float) -> float:
    """
    Calculate overall business impact score (1-10)
    """
    # Normalize factors
    user_factor = min(affected_users / 5000, 1.0)  # Max 5000 users
    cost_factor = min(processing_cost / 500000, 1.0)  # Max 5L cost
    time_factor = min(downtime_hours / 24, 1.0)  # Max 24 hours
    
    # Weighted average (users have highest weight)
    impact_score = (user_factor * 0.5 + cost_factor * 0.3 + time_factor * 0.2) * 10
    
    return round(impact_score, 1)

def export_metrics_to_csv(metrics_data: Dict, filename: Optional[str] = None) -> str:
    """
    Export metrics data to CSV format
    """
    import csv
    import io
    
    if not filename:
        filename = f"fip_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        'FIP Name', 'Bank Name', 'Consent Success Rate', 'Data Fetch Success Rate',
        'Avg Response Time', 'Error Rate', 'Current Status', 'User Base', 'Last Updated'
    ]
    writer.writerow(headers)
    
    # Write data
    for fip_name, metrics in metrics_data.items():
        row = [
            fip_name,
            metrics.get('bank_name', ''),
            metrics.get('consent_success_rate', 0),
            metrics.get('data_fetch_success_rate', 0),
            metrics.get('avg_response_time', 0),
            metrics.get('error_rate', 0),
            metrics.get('current_status', ''),
            metrics.get('user_base', 0),
            metrics.get('last_updated', '')
        ]
        writer.writerow(row)
    
    return output.getvalue()

print("✅ All services and utilities loaded successfully!")

def get_fip_status_from_success_rate(data_fetch_success_rate: float, consent_success_rate: float) -> str:
    """
    Get FIP status from success rates
    """
    if data_fetch_success_rate >= 80 and consent_success_rate >= 80:
        return 'excellent'
    elif data_fetch_success_rate >= 50 or consent_success_rate >= 50:
        return 'fair'
    else:
        return 'poor'
    
def get_fip_response(base_fips, fip_features):
    # Initialize real metrics
    fips_data = {}
    
    if not Config.USE_REAL_BEDROCK:
        return {
        "sbi-fip": {
            "fip_name": "sbi-fip",
            "bank_name": "State Bank of India",
            "consent_success_rate": 24.3,
            "data_fetch_success_rate": 31.7,
            "avg_response_time": 13.4,
            "error_rate": 48.2,
            "current_status": "critical",
            "user_base": 4500,
            "last_updated": "2025-06-11T11:02:31.279136",
            "trend": "decreasing",
            "maintenance_window": True,
            "health_metrics": {
                "health_score": 3.2,
                "reliability": 35.7,
                "volatility": 0.85,
                "performance_grade": "poor",
            },
        },
        "hdfc-fip": {
            "fip_name": "hdfc-fip",
            "bank_name": "HDFC Bank",
            "consent_success_rate": 90.2,
            "data_fetch_success_rate": 90.5,
            "avg_response_time": 4.51,
            "error_rate": 4.6,
            "current_status": "healthy",
            "user_base": 3200,
            "last_updated": "2025-06-11T11:02:31.279145",
            "trend": "increasing",
            "maintenance_window": False,
            "health_metrics": {
                "health_score": 9.2,
                "reliability": 92.4,
                "volatility": 0.15,
                "performance_grade": "excellent",
            },
        },
        "icici-fip": {
            "fip_name": "icici-fip",
            "bank_name": "ICICI Bank",
            "consent_success_rate": 82.2,
            "data_fetch_success_rate": 85.6,
            "avg_response_time": 4.33,
            "error_rate": 9.87,
            "current_status": "healthy",
            "user_base": 2800,
            "last_updated": "2025-06-11T11:02:31.279150",
            "trend": "stable",
            "maintenance_window": False,
            "health_metrics": {
                "health_score": 8.5,
                "reliability": 85.8,
                "volatility": 0.25,
                "performance_grade": "excellent",
            },
        },
        "axis-fip": {
            "fip_name": "axis-fip",
            "bank_name": "Axis Bank",
            "consent_success_rate": 8.3,
            "data_fetch_success_rate": 11.2,
            "avg_response_time": 15.0,
            "error_rate": 56.3,
            "current_status": "critical",
            "user_base": 1200,
            "last_updated": "2025-06-11T11:02:31.279155",
            "trend": "decreasing",
            "maintenance_window": True,
            "health_metrics": {
                "health_score": 2.1,
                "reliability": 25.8,
                "volatility": 0.92,
                "performance_grade": "poor",
            },
        },
        "kotak-fip": {
            "fip_name": "kotak-fip",
            "bank_name": "Kotak Mahindra Bank",
            "consent_success_rate": 59.9,
            "data_fetch_success_rate": 64.4,
            "avg_response_time": 8.04,
            "error_rate": 16.9,
            "current_status": "degraded",
            "user_base": 800,
            "last_updated": "2025-06-11T11:02:31.279163",
            "trend": "decreasing",
            "maintenance_window": False,
            "health_metrics": {
                "health_score": 5.8,
                "reliability": 58.9,
                "volatility": 0.55,
                "performance_grade": "fair",
            },
        },
        "boi-fip": {
            "fip_name": "boi-fip",
            "bank_name": "Bank of India",
            "consent_success_rate": 86.8,
            "data_fetch_success_rate": 84.5,
            "avg_response_time": 5.37,
            "error_rate": 4.0,
            "current_status": "healthy",
            "user_base": 600,
            "last_updated": "2025-06-11T11:02:31.279167",
            "trend": "stable",
            "maintenance_window": False,
            "health_metrics": {
                "health_score": 8.8,
                "reliability": 88.5,
                "volatility": 0.22,
                "performance_grade": "excellent",
            },
        },
        "pnb-fip": {
            "fip_name": "pnb-fip",
            "bank_name": "Punjab National Bank",
            "consent_success_rate": 17.3,
            "data_fetch_success_rate": 23.4,
            "avg_response_time": 12.04,
            "error_rate": 46.8,
            "current_status": "critical",
            "user_base": 700,
            "last_updated": "2025-06-11T11:02:31.279171",
            "trend": "decreasing",
            "maintenance_window": True,
            "health_metrics": {
                "health_score": 2.8,
                "reliability": 32.4,
                "volatility": 0.88,
                "performance_grade": "poor",
            },
        },
        "canara-fip": {
            "fip_name": "canara-fip",
            "bank_name": "Canara Bank",
            "consent_success_rate": 96.3,
            "data_fetch_success_rate": 91.6,
            "avg_response_time": 2.43,
            "error_rate": 2.4,
            "current_status": "healthy",
            "user_base": 500,
            "last_updated": "2025-06-11T11:02:31.279175",
            "trend": "increasing",
            "maintenance_window": False,
            "health_metrics": {
                "health_score": 9.5,
                "reliability": 94.8,
                "volatility": 0.12,
                "performance_grade": "excellent",
            },
        },
        "ubi-fip": {
            "fip_name": "ubi-fip",
            "bank_name": "Union Bank of India",
            "consent_success_rate": 89.6,
            "data_fetch_success_rate": 93.9,
            "avg_response_time": 4.42,
            "error_rate": 5.9,
            "current_status": "healthy",
            "user_base": 400,
            "last_updated": "2025-06-11T11:02:31.279179",
            "trend": "stable",
            "maintenance_window": False,
            "health_metrics": {
                "health_score": 9.1,
                "reliability": 91.2,
                "volatility": 0.18,
                "performance_grade": "excellent",
            },
        },
        "iob-fip": {
            "fip_name": "iob-fip",
            "bank_name": "Indian Overseas Bank",
            "consent_success_rate": 89.9,
            "data_fetch_success_rate": 94.4,
            "avg_response_time": 4.87,
            "error_rate": 3.8,
            "current_status": "healthy",
            "user_base": 300,
            "last_updated": "2025-06-11T11:02:31.279183",
            "trend": "increasing",
            "maintenance_window": False,
            "health_metrics": {
                "health_score": 9.3,
                "reliability": 93.1,
                "volatility": 0.14,
                "performance_grade": "excellent",
            },
        },
        "central-fip": {
            "fip_name": "central-fip",
            "bank_name": "Central Bank of India",
            "consent_success_rate": 63.5,
            "data_fetch_success_rate": 64.6,
            "avg_response_time": 9.65,
            "error_rate": 18.2,
            "current_status": "degraded",
            "user_base": 250,
            "last_updated": "2025-06-11T11:02:31.279187",
            "trend": "decreasing",
            "maintenance_window":False,
            "health_metrics": {
                "health_score": 5.4,
                "reliability": 55.2,
                "volatility": 0.58,
                "performance_grade": "fair",
            },
        },
    }
        
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

    return fips_data