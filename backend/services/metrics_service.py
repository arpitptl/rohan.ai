import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class MetricsService:
    """
    Service for managing FIP metrics and generating realistic data
    """
    
    def __init__(self):
        self.fips = {
            'sbi-fip': {
                'bank_name': 'State Bank of India',
                'base_success_rate': 95.0,
                'base_response_time': 1.2,
                'user_base': 4500,
                'maintenance_hours': [2, 3, 4],  # 2 AM - 4 AM
                'status': 'healthy'
            },
            'hdfc-fip': {
                'bank_name': 'HDFC Bank',
                'base_success_rate': 92.0,
                'base_response_time': 1.5,
                'user_base': 3200,
                'maintenance_hours': [1, 2, 3],
                'status': 'degraded'
            },
            'icici-fip': {
                'bank_name': 'ICICI Bank',
                'base_success_rate': 90.0,
                'base_response_time': 1.8,
                'user_base': 2800,
                'maintenance_hours': [23, 0, 1],
                'status': 'healthy'
            },
            'axis-fip': {
                'bank_name': 'Axis Bank',
                'base_success_rate': 88.0,
                'base_response_time': 2.1,
                'user_base': 1200,
                'maintenance_hours': [3, 4, 5],
                'status': 'critical'
            },
            'kotak-fip': {
                'bank_name': 'Kotak Mahindra Bank',
                'base_success_rate': 87.0,
                'base_response_time': 2.3,
                'user_base': 800,
                'maintenance_hours': [2, 3],
                'status': 'healthy'
            },
            'boi-fip': {
                'bank_name': 'Bank of India',
                'base_success_rate': 85.0,
                'base_response_time': 2.8,
                'user_base': 600,
                'maintenance_hours': [1, 2, 3, 4],
                'status': 'degraded'
            },
            'pnb-fip': {
                'bank_name': 'Punjab National Bank',
                'base_success_rate': 82.0,
                'base_response_time': 3.2,
                'user_base': 700,
                'maintenance_hours': [0, 1, 2],
                'status': 'healthy'
            },
            'canara-fip': {
                'bank_name': 'Canara Bank',
                'base_success_rate': 80.0,
                'base_response_time': 3.5,
                'user_base': 500,
                'maintenance_hours': [2, 3, 4, 5],
                'status': 'healthy'
            },
            'ubi-fip': {
                'bank_name': 'Union Bank of India',
                'base_success_rate': 78.0,
                'base_response_time': 4.0,
                'user_base': 400,
                'maintenance_hours': [1, 2],
                'status': 'degraded'
            },
            'iob-fip': {
                'bank_name': 'Indian Overseas Bank',
                'base_success_rate': 75.0,
                'base_response_time': 4.5,
                'user_base': 300,
                'maintenance_hours': [3, 4],
                'status': 'healthy'
            },
            'central-fip': {
                'bank_name': 'Central Bank of India',
                'base_success_rate': 72.0,
                'base_response_time': 5.0,
                'user_base': 250,
                'maintenance_hours': [2, 3, 4],
                'status': 'warning'
            }
        }
        
        # Track metrics over time for trend analysis
        self.metrics_history = {}
        self.last_update = datetime.utcnow()
        
        # Initialize current metrics
        self.current_metrics = self._generate_initial_metrics()
    
    def get_all_fips_status(self) -> Dict:
        """
        Get current status of all FIPs
        """
        return self.current_metrics
    
    def get_fips_metrics(self, fip_names: List[str]) -> Dict:
        """
        Get metrics for specific FIPs
        """
        if not fip_names:
            return self.current_metrics
        
        return {
            fip: self.current_metrics[fip] 
            for fip in fip_names 
            if fip in self.current_metrics
        }
    
    def get_comprehensive_health(self) -> Dict:
        """
        Get comprehensive health analysis
        """
        total_fips = len(self.current_metrics)
        healthy_count = sum(1 for fip in self.current_metrics.values() if fip['current_status'] == 'healthy')
        degraded_count = sum(1 for fip in self.current_metrics.values() if fip['current_status'] == 'degraded')
        critical_count = sum(1 for fip in self.current_metrics.values() if fip['current_status'] == 'critical')
        
        avg_consent_success = sum(fip['consent_success_rate'] for fip in self.current_metrics.values()) / total_fips
        avg_data_success = sum(fip['data_fetch_success_rate'] for fip in self.current_metrics.values()) / total_fips
        
        return {
            'summary': {
                'total_fips': total_fips,
                'healthy': healthy_count,
                'degraded': degraded_count,
                'critical': critical_count,
                'overall_health_percentage': (healthy_count / total_fips) * 100
            },
            'performance': {
                'average_consent_success_rate': round(avg_consent_success, 2),
                'average_data_fetch_success_rate': round(avg_data_success, 2),
                'system_availability': round((avg_consent_success + avg_data_success) / 2, 2)
            },
            'fips': self.current_metrics,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def update_fip_metrics(self):
        """
        Update FIP metrics with realistic variations
        """
        current_hour = datetime.utcnow().hour
        
        for fip_name, fip_config in self.fips.items():
            # Get current metrics
            current = self.current_metrics.get(fip_name, {})
            
            # Apply time-based variations
            time_factor = self._get_time_factor(current_hour, fip_config['maintenance_hours'])
            
            # Apply status-based degradation
            status_factor = self._get_status_factor(fip_config['status'])
            
            # Calculate new metrics with realistic variations
            base_consent = fip_config['base_success_rate']
            base_response = fip_config['base_response_time']
            
            # Add random variations
            consent_variation = random.uniform(-5, 3)
            response_variation = random.uniform(-0.3, 0.8)
            
            new_consent_rate = max(0, min(100, 
                base_consent * time_factor * status_factor + consent_variation
            ))
            
            new_data_rate = max(0, min(100, 
                new_consent_rate * random.uniform(0.85, 0.98)  # Data fetch usually slightly lower
            ))
            
            new_response_time = max(0.1, 
                base_response * (2 - time_factor) * (2 - status_factor) + response_variation
            )
            
            # Determine current status based on metrics
            new_status = self._determine_status(new_consent_rate, new_data_rate, new_response_time)
            
            # Update metrics
            self.current_metrics[fip_name] = {
                'fip_name': fip_name,
                'bank_name': fip_config['bank_name'],
                'consent_success_rate': round(new_consent_rate, 1),
                'data_fetch_success_rate': round(new_data_rate, 1),
                'avg_response_time': round(new_response_time, 2),
                'error_rate': round(100 - new_consent_rate, 1),
                'current_status': new_status,
                'user_base': fip_config['user_base'],
                'last_updated': datetime.utcnow().isoformat(),
                'trend': self._calculate_trend(fip_name, new_consent_rate),
                'maintenance_window': self._check_maintenance_window(current_hour, fip_config['maintenance_hours'])
            }
        
        # Store in history for trend analysis
        self._store_metrics_history()
        self.last_update = datetime.utcnow()
    
    def _generate_initial_metrics(self) -> Dict:
        """
        Generate initial realistic metrics for all FIPs
        """
        metrics = {}
        
        for fip_name, fip_config in self.fips.items():
            base_consent = fip_config['base_success_rate']
            base_response = fip_config['base_response_time']
            status = fip_config['status']
            
            # Apply status-based modifications
            status_factor = self._get_status_factor(status)
            
            consent_rate = base_consent * status_factor + random.uniform(-3, 2)
            consent_rate = max(0, min(100, consent_rate))
            
            data_rate = consent_rate * random.uniform(0.90, 0.98)
            data_rate = max(0, min(100, data_rate))
            
            response_time = base_response * (2 - status_factor) + random.uniform(-0.2, 0.5)
            response_time = max(0.1, response_time)
            
            metrics[fip_name] = {
                'fip_name': fip_name,
                'bank_name': fip_config['bank_name'],
                'consent_success_rate': round(consent_rate, 1),
                'data_fetch_success_rate': round(data_rate, 1),
                'avg_response_time': round(response_time, 2),
                'error_rate': round(100 - consent_rate, 1),
                'current_status': self._determine_status(consent_rate, data_rate, response_time),
                'user_base': fip_config['user_base'],
                'last_updated': datetime.utcnow().isoformat(),
                'trend': 'stable',
                'maintenance_window': False
            }
        
        return metrics
    
    def _get_time_factor(self, current_hour: int, maintenance_hours: List[int]) -> float:
        """
        Get performance factor based on time of day
        """
        if current_hour in maintenance_hours:
            return random.uniform(0.3, 0.6)  # Severe degradation during maintenance
        elif current_hour in [9, 10, 11, 14, 15, 16]:  # Business hours
            return random.uniform(0.85, 0.95)  # Slight degradation during peak
        else:
            return random.uniform(0.95, 1.0)  # Normal performance
    
    def _get_status_factor(self, status: str) -> float:
        """
        Get performance factor based on current status
        """
        status_factors = {
            'healthy': random.uniform(0.95, 1.0),
            'degraded': random.uniform(0.65, 0.85),
            'critical': random.uniform(0.1, 0.35),
            'warning': random.uniform(0.75, 0.95)
        }
        return status_factors.get(status, 0.9)
    
    def _determine_status(self, consent_rate: float, data_rate: float, response_time: float) -> str:
        """
        Determine FIP status based on metrics
        """
        avg_success = (consent_rate + data_rate) / 2
        
        if avg_success < 30 or response_time > 10:
            return 'critical'
        elif avg_success < 70 or response_time > 5:
            return 'degraded'
        elif avg_success < 85 or response_time > 3:
            return 'warning'
        else:
            return 'healthy'
    
    def _calculate_trend(self, fip_name: str, current_consent_rate: float) -> str:
        """
        Calculate trend based on historical data
        """
        if fip_name in self.metrics_history and len(self.metrics_history[fip_name]) > 2:
            recent_rates = [m['consent_success_rate'] for m in self.metrics_history[fip_name][-3:]]
            if len(recent_rates) >= 2:
                if current_consent_rate > recent_rates[-1] + 2:
                    return 'improving'
                elif current_consent_rate < recent_rates[-1] - 2:
                    return 'declining'
        return 'stable'
    
    def _check_maintenance_window(self, current_hour: int, maintenance_hours: List[int]) -> bool:
        """
        Check if currently in maintenance window
        """
        return current_hour in maintenance_hours
    
    def _store_metrics_history(self):
        """
        Store current metrics in history for trend analysis
        """
        timestamp = datetime.utcnow()
        
        for fip_name, metrics in self.current_metrics.items():
            if fip_name not in self.metrics_history:
                self.metrics_history[fip_name] = []
            
            # Store historical data point
            historical_point = {
                'timestamp': timestamp.isoformat(),
                'consent_success_rate': metrics['consent_success_rate'],
                'data_fetch_success_rate': metrics['data_fetch_success_rate'],
                'avg_response_time': metrics['avg_response_time'],
                'current_status': metrics['current_status']
            }
            
            self.metrics_history[fip_name].append(historical_point)
            
            # Keep only last 100 data points to prevent memory issues
            if len(self.metrics_history[fip_name]) > 100:
                self.metrics_history[fip_name] = self.metrics_history[fip_name][-100:]
