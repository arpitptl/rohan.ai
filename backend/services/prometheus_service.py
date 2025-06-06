import random
import time
from datetime import datetime
from prometheus_client import Gauge, Counter, Histogram, CollectorRegistry, push_to_gateway
import requests
from typing import Dict, List
import os
from utils.logger import logger

class PrometheusService:
    """
    Service for integrating with Prometheus metrics
    Pushes mock FIP metrics to Prometheus for realistic demo
    """
    
    def __init__(self):
        # Prometheus pushgateway configuration
        self.pushgateway_url = os.getenv('PROMETHEUS_PUSHGATEWAY_URL', 'pushgateway:9091')  # Use Docker service name
        self.job_name = 'aa_gateway_fips'
        
        # Create custom registry for FIP metrics
        self.registry = CollectorRegistry()
        
        # Define Prometheus metrics
        self.fip_consent_success_rate = Gauge(
            'fip_consent_success_rate',
            'FIP consent approval success rate percentage',
            ['fip_name', 'bank_name'],
            registry=self.registry
        )
        
        self.fip_data_fetch_success_rate = Gauge(
            'fip_data_fetch_success_rate',
            'FIP data fetch success rate percentage',
            ['fip_name', 'bank_name'],
            registry=self.registry
        )
        
        self.fip_response_time = Gauge(
            'fip_avg_response_time_seconds',
            'FIP average response time in seconds',
            ['fip_name', 'bank_name'],
            registry=self.registry
        )
        
        self.fip_error_rate = Gauge(
            'fip_error_rate',
            'FIP error rate percentage',
            ['fip_name', 'bank_name'],
            registry=self.registry
        )
        
        self.fip_total_requests = Counter(
            'fip_total_requests',
            'Total requests processed by FIP',
            ['fip_name', 'bank_name', 'request_type'],
            registry=self.registry
        )
        
        self.fip_status = Gauge(
            'fip_status',
            'FIP operational status (1=healthy, 0.5=degraded, 0=critical)',
            ['fip_name', 'bank_name'],
            registry=self.registry
        )
        
        logger.info("✅ Prometheus metrics initialized")
    
    def push_mock_metrics(self) -> int:
        """
        Push mock FIP metrics to Prometheus
        Returns number of metrics generated
        """
        try:
            from services.metrics_service import MetricsService
            metrics_service = MetricsService()
            
            # Get current FIP metrics
            fip_metrics = metrics_service.get_all_fips_status()
            
            metrics_count = 0
            
            for fip_name, metrics in fip_metrics.items():
                bank_name = metrics.get('bank_name', fip_name)
                
                # Update Prometheus metrics
                self.fip_consent_success_rate.labels(
                    fip_name=fip_name, 
                    bank_name=bank_name
                ).set(metrics['consent_success_rate'])
                
                self.fip_data_fetch_success_rate.labels(
                    fip_name=fip_name, 
                    bank_name=bank_name
                ).set(metrics['data_fetch_success_rate'])
                
                self.fip_response_time.labels(
                    fip_name=fip_name, 
                    bank_name=bank_name
                ).set(metrics['avg_response_time'])
                
                self.fip_error_rate.labels(
                    fip_name=fip_name, 
                    bank_name=bank_name
                ).set(metrics['error_rate'])
                
                # Convert status to numeric
                status_value = self._status_to_numeric(metrics['current_status'])
                self.fip_status.labels(
                    fip_name=fip_name, 
                    bank_name=bank_name
                ).set(status_value)
                
                # Simulate request counters
                consent_requests = random.randint(50, 200)
                data_requests = random.randint(30, 150)
                
                self.fip_total_requests.labels(
                    fip_name=fip_name, 
                    bank_name=bank_name, 
                    request_type='consent'
                )._value._value += consent_requests
                
                self.fip_total_requests.labels(
                    fip_name=fip_name, 
                    bank_name=bank_name, 
                    request_type='data_fetch'
                )._value._value += data_requests
                
                metrics_count += 5  # 5 metrics per FIP
            
            # Push to Prometheus pushgateway
            self._push_to_gateway()
            
            logger.info(f"📊 Pushed {metrics_count} metrics to Prometheus")
            return metrics_count
            
        except Exception as e:
            logger.error(f"❌ Error pushing metrics to Prometheus: {e}")
            return 0
    
    def _status_to_numeric(self, status: str) -> float:
        """
        Convert status string to numeric value for Prometheus
        """
        status_map = {
            'healthy': 1.0,
            'warning': 0.8,
            'degraded': 0.5,
            'critical': 0.0
        }
        return status_map.get(status, 0.5)
    
    def _push_to_gateway(self):
        """
        Push metrics to Prometheus pushgateway
        """
        try:
            # Try to push to pushgateway
            push_to_gateway(
                self.pushgateway_url, 
                job=self.job_name, 
                registry=self.registry,
            )
            logger.info(f"✅ Successfully pushed metrics to Prometheus pushgateway at {self.pushgateway_url}")
            
        except Exception as e:
            logger.error(f"⚠️  Could not push to Prometheus pushgateway: {self.pushgateway_url} - {e}")
            logger.error("💡 Make sure Prometheus pushgateway is running and accessible")
            # In development, we can continue without Prometheus
    
    def fetch_prometheus_metrics(self, query: str, time_range: str = '1h') -> Dict:
        """
        Fetch metrics from Prometheus (for when connecting to real Prometheus)
        """
        try:
            prometheus_url = "http://localhost:9090"  # Default Prometheus URL
            
            # Example queries for FIP metrics
            queries = {
                'fip_health': 'fip_consent_success_rate',
                'response_times': 'fip_avg_response_time_seconds',
                'error_rates': 'fip_error_rate',
                'status': 'fip_status'
            }
            
            if query in queries:
                prom_query = queries[query]
                
                response = requests.get(
                    f"{prometheus_url}/api/v1/query",
                    params={'query': prom_query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_prometheus_response(data)
                else:
                    print(f"❌ Prometheus query failed: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error fetching from Prometheus: {e}")
        
        # Return empty result if Prometheus is not available
        return {'status': 'error', 'data': []}
    
    def _parse_prometheus_response(self, response_data: Dict) -> Dict:
        """
        Parse Prometheus response into usable format
        """
        try:
            if response_data.get('status') == 'success':
                results = response_data.get('data', {}).get('result', [])
                
                parsed_data = []
                for result in results:
                    metric_labels = result.get('metric', {})
                    value = result.get('value', [None, None])[1]
                    
                    parsed_data.append({
                        'fip_name': metric_labels.get('fip_name'),
                        'bank_name': metric_labels.get('bank_name'),
                        'value': float(value) if value else 0.0,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                return {
                    'status': 'success',
                    'data': parsed_data,
                    'count': len(parsed_data)
                }
            else:
                return {'status': 'error', 'message': 'Prometheus query failed'}
                
        except Exception as e:
            print(f"❌ Error parsing Prometheus response: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_prometheus_config(self) -> str:
        """
        Generate Prometheus configuration for FIP monitoring
        """
        config = """
# Prometheus configuration for AA Gateway FIP monitoring
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "fip_alert_rules.yml"

scrape_configs:
  # AA Gateway FIP metrics
  - job_name: 'aa-gateway-fips'
    static_configs:
      - targets: ['localhost:5000']  # Your Flask app
    metrics_path: '/metrics'
    scrape_interval: 30s

  # Pushgateway for batch metrics
  - job_name: 'pushgateway'
    static_configs:
      - targets: ['localhost:9091']
    honor_labels: true

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Alert rules for FIP monitoring
"""
        
        alert_rules = """
# fip_alert_rules.yml
groups:
  - name: fip_alerts
    rules:
      - alert: FIPConsentsSuccessRateLow
        expr: fip_consent_success_rate < 70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "FIP {{ $labels.fip_name }} consent success rate is low"
          description: "{{ $labels.fip_name }} has consent success rate of {{ $value }}% for more than 5 minutes"

      - alert: FIPConsentsSuccessRateCritical
        expr: fip_consent_success_rate < 30
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "FIP {{ $labels.fip_name }} consent success rate is critically low"
          description: "{{ $labels.fip_name }} has consent success rate of {{ $value }}% for more than 2 minutes"

      - alert: FIPResponseTimeHigh
        expr: fip_avg_response_time_seconds > 5
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "FIP {{ $labels.fip_name }} response time is high"
          description: "{{ $labels.fip_name }} response time is {{ $value }}s for more than 3 minutes"

      - alert: FIPDown
        expr: fip_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FIP {{ $labels.fip_name }} is down"
          description: "{{ $labels.fip_name }} has been down for more than 1 minute"
"""
        
        return config + "\n" + alert_rules
