import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

def format_currency(amount: float, currency: str = '₹') -> str:
    """
    Format currency amounts for display
    """
    if amount >= 100000:  # 1 lakh or more
        return f"{currency}{amount/100000:.1f}L"
    elif amount >= 1000:  # 1 thousand or more
        return f"{currency}{amount/1000:.1f}K"
    else:
        return f"{currency}{amount:.0f}"

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