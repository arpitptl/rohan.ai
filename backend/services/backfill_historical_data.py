#!/usr/bin/env python3

import json
import random
from typing import Any, Dict
import requests
import time
import sys
import os
from datetime import datetime, timedelta
from utils.logger import logger

def json_to_vm_import(json_file_path, vm_url="http://localhost:8428"):
    """
    Import JSON metrics directly into VictoriaMetrics using /api/v1/import
    This is the fastest way to backfill historical data
    """
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"❌ Error reading JSON file: {e}")
        return False
    
    logger.info(f"📊 Processing {len(data)} entries from {json_file_path}")
    
    # Prepare data for VictoriaMetrics import format
    import_lines = []
    
    for entry in data:
        fip_name = entry['fip_name']
        bank_name = entry['bank_name']
        metrics = entry['metrics']
        
        # Get timestamp (VictoriaMetrics expects milliseconds)
        timestamp = entry.get('timestamp')
        if timestamp:
            if timestamp < 10**12:  # Convert seconds to milliseconds
                timestamp_ms = int(timestamp * 1000)
            else:
                timestamp_ms = int(timestamp)
        else:
            timestamp_ms = int(time.time() * 1000)
        
        # Convert to VictoriaMetrics import format
        # Format: {"metric":{"__name__":"metric_name","label1":"value1"},"value":123,"timestamp":1234567890000}
        
        metrics_data = [
            {
                "metric": {
                    "__name__": "fip_consent_success_rate",
                    "fip_name": fip_name,
                    "bank_name": bank_name,
                    "job":"manual"
                },
                "values": [metrics["consent_success_rate"]],
                "timestamps": [timestamp_ms]
            },
            {
                "metric": {
                    "__name__": "fip_data_fetch_success_rate", 
                    "fip_name": fip_name,
                    "bank_name": bank_name,
                    "job":"manual"
                },
                "values": [metrics["data_fetch_success_rate"]],
                "timestamps": [timestamp_ms]
            },
            {
                "metric": {
                    "__name__": "fip_avg_response_time_seconds",
                    "fip_name": fip_name,
                    "bank_name": bank_name,
                    "job":"manual"
                },
                "values": [metrics["avg_response_time"]],
                "timestamps": [timestamp_ms]
            },
            {
                "metric": {
                    "__name__": "fip_error_rate",
                    "fip_name": fip_name,
                    "bank_name": bank_name,
                    "job":"manual"
                },
                "values": [metrics["error_rate"]],
                "timestamps": [timestamp_ms]
            },
            {
                "metric": {
                    "__name__": "fip_total_requests",
                    "fip_name": fip_name,
                    "bank_name": bank_name,
                    "request_type": "total",
                    "job":"manual"
                },
                "values": [metrics["total_requests"]],
                "timestamps": [timestamp_ms]
            },
            {
                "metric": {
                    "__name__": "fip_status",
                    "fip_name": fip_name,
                    "bank_name": bank_name,
                    "job":"manual"
                },
                "values": [metrics["status"]],
                "timestamps": [timestamp_ms]
            }
        ]

        import_lines.extend(metrics_data)
    
    logger.info(f"📈 Prepared {len(import_lines)} total metrics for import")
    
    # Convert to JSONL format (one JSON object per line)
    jsonl_data = '\n'.join(json.dumps(line) for line in import_lines)
    
    # Import into VictoriaMetrics
    try:
        logger.info(f"🚀 Importing to VictoriaMetrics at {vm_url}")
        
        headers = {
            'Content-Type': 'application/x-jsonlines'
        }
        
        response = requests.post(
            f"{vm_url}/api/v1/import",
            data=jsonl_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 204:
            logger.info("✅ Import successful!")
            
            # Show sample timestamp info
            if import_lines:
                sample_ts = import_lines[0]['timestamps'][0]
                sample_datetime = datetime.fromtimestamp(sample_ts/1000).strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"📅 Sample timestamp: {sample_datetime}")
            
            return True
        else:
            logger.error(f"❌ Import failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during import: {e}")
        return False

def prometheus_format_import(json_file_path, vm_url="http://localhost:8428"):
    """
    Alternative: Import using Prometheus format via /api/v1/import/prometheus
    """
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"❌ Error reading JSON file: {e}")
        return False
    
    logger.info(f"📊 Converting {len(data)} entries to Prometheus format")
    
    # Generate Prometheus format
    lines = []
    
    for entry in data:
        fip_name = entry['fip_name']
        bank_name = entry['bank_name']
        metrics = entry['metrics']
        
        # Get timestamp in milliseconds
        timestamp = entry.get('timestamp')
        if timestamp:
            if timestamp < 10**12:
                timestamp_ms = int(timestamp * 1000)
            else:
                timestamp_ms = int(timestamp)
        else:
            timestamp_ms = int(time.time() * 1000)
        
        lines.extend([
            f'fip_consent_success_rate{{fip_name="{fip_name}",bank_name="{bank_name}"}} {metrics["consent_success_rate"]} {timestamp_ms}',
            f'fip_data_fetch_success_rate{{fip_name="{fip_name}",bank_name="{bank_name}"}} {metrics["data_fetch_success_rate"]} {timestamp_ms}',
            f'fip_avg_response_time_seconds{{fip_name="{fip_name}",bank_name="{bank_name}"}} {metrics["avg_response_time"]} {timestamp_ms}',
            f'fip_error_rate{{fip_name="{fip_name}",bank_name="{bank_name}"}} {metrics["error_rate"]} {timestamp_ms}',
            f'fip_total_requests{{fip_name="{fip_name}",bank_name="{bank_name}",request_type="total"}} {metrics["total_requests"]} {timestamp_ms}',
            f'fip_status{{fip_name="{fip_name}",bank_name="{bank_name}"}} {metrics["status"]} {timestamp_ms}'
        ])
    
    prometheus_data = '\n'.join(lines)
    
    # Import using Prometheus format
    try:
        logger.info("🚀 Importing Prometheus format to VictoriaMetrics")
        
        headers = {
            'Content-Type': 'text/plain'
        }
        
        response = requests.post(
            f"{vm_url}/api/v1/import/prometheus",
            data=prometheus_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 204:
            logger.info("✅ Prometheus format import successful!")
            logger.info(f"📊 Imported {len(lines)} metrics")
            return True
        else:
            logger.error(f"❌ Import failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during import: {e}")
        return False

def backfill_historical_metrics():
    
    json_file = "fip_metrics_historical.json"
    vm_url = "http://victoriametrics:8428"
    method = "prometheus"
    
    if not os.path.exists(json_file):
        logger.error(f"❌ JSON file not found: {json_file}")
        sys.exit(1)
    
    logger.info("🎯 VictoriaMetrics Import Tool")
    logger.info(f"📁 File: {json_file}")
    logger.info(f"🌐 VM URL: {vm_url}")
    logger.info(f"⚙️  Method: {method}")
    logger.info("-" * 50)
    
    if method == "prometheus":
        success = prometheus_format_import(json_file, vm_url)
    else:
        success = json_to_vm_import(json_file, vm_url)
    
    if success:
        logger.info("\n✅ Import completed successfully!")
        logger.info("🔍 Test queries:")
        logger.info(f"   curl '{vm_url}/api/v1/query?query=fip_consent_success_rate'")
        logger.info(f"   curl '{vm_url}/api/v1/query_range?query=fip_consent_success_rate&start=2025-05-07T10:00:00Z&end=2025-05-07T12:00:00Z&step=1m'")
    else:
        logger.error("❌ Import failed!")
        sys.exit(1)

class GenerateHistoricalData:
    def __init__(self):
        """
        Initialize the backfiller
        
        """
        
        # Sample FIP and Bank names for realistic data
        self.fips = {
            'sbi-fip': 'State Bank of India',
            'hdfc-fip': 'HDFC Bank',
            'icici-fip': 'ICICI Bank',
            'axis-fip': 'Axis Bank',
            'kotak-fip': 'Kotak Mahindra Bank',
            'boi-fip': 'Bank of India',
            'pnb-fip': 'Punjab National Bank',
            'canara-fip': 'Canara Bank',
            'ubi-fip': 'Union Bank of India',
            'iob-fip': 'Indian Overseas Bank',
            'central-fip': 'Central Bank of India'
        }
        self.request_types = ["consent", "data_fetch", "account_discovery"]
    
    def generate_realistic_metrics(self, timestamp: int, fip_name: str, bank_name: str) -> Dict[str, Any]:
        """
        Generate realistic metric values based on time patterns
        """
        # Get hour of day for realistic patterns
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        
        # Peak hours: 9-11 AM and 2-4 PM on weekdays
        is_peak_hour = (9 <= hour <= 11 or 14 <= hour <= 16) and day_of_week < 5
        
        # Weekend pattern - lower activity
        is_weekend = day_of_week >= 5
        
        # Base success rates (higher during non-peak, lower on weekends)
        base_consent_success = 0.95 if not is_peak_hour else 0.87
        base_data_fetch_success = 0.92 if not is_peak_hour else 0.84
        
        if is_weekend:
            base_consent_success += 0.03
            base_data_fetch_success += 0.03
        
        # Add some randomness and bank-specific variations
        bank_modifier = hash(bank_name) % 10 / 100  # -0.05 to +0.05 range

        # Define downtime windows for each FIP
        forced_downtime = False
        
        if fip_name == 'axis-fip' and 19 <= hour < 23:  # 7pm-11pm
            forced_downtime = True
        elif fip_name == 'hdfc-fip' and (23 <= hour < 24 or 0 <= hour < 1):  # 11pm-1am
            forced_downtime = True
        elif fip_name == 'icici-fip' and 2 <= hour < 3:  # 2-3am
            forced_downtime = True
        elif fip_name == 'sbi-fip' and (13 <= hour < 14 or 20 <= hour < 21):  # 1-2pm AND 8-9pm
            forced_downtime = True
        elif fip_name == 'kotak-fip' and 12 <= hour < 16:  # 12-4pm
            forced_downtime = True
        elif fip_name == 'pnb-fip' and (20 <= hour < 21 or 22 <= hour < 24):  # 8-9pm AND 10-12pm
            forced_downtime = True
        elif fip_name == 'canara-fip' and 13 <= hour < 14:  # 1-2pm
            forced_downtime = True
        elif fip_name == 'ubi-fip' and 3 <= hour < 4:  # 3-4am
            forced_downtime = True
        elif fip_name == 'iob-fip' and 22 <= hour < 24:  # 10-12pm
            forced_downtime = True
        elif fip_name == 'central-fip' and 14 <= hour < 16:  # 2-4pm
            forced_downtime = True

        if forced_downtime:
            # Severe downtime - near complete failure
            consent_success = random.uniform(0.05, 0.15)  # 5-15% success rate
            data_success = random.uniform(0.05, 0.15)     # 5-15% success rate
            avg_resp = random.uniform(8.0, 15.0)          # Very slow response times
            error_rate = 1 - consent_success
            status_val = 0.0  # critical status
        else:
            consent_success = max(0.7, min(1.0, base_consent_success + random.uniform(-0.1, 0.05) + bank_modifier))
            data_success = max(0.7, min(1.0, base_data_fetch_success + random.uniform(-0.08, 0.05) + bank_modifier))
            avg_resp = max(0.1, 2.5 + random.uniform(-1.0, 3.0) + (2.0 if is_peak_hour else 0))
            error_rate = 1 - consent_success
            status_val = random.choices([1.0, 0.5, 0.0], weights=[85, 12, 3])[0]

        metrics = {
            'consent_success_rate': round(consent_success, 3),
            'data_fetch_success_rate': round(data_success, 3),
            'avg_response_time': round(avg_resp, 2),
            'error_rate': round(error_rate, 3),
            'total_requests': random.randint(50 if is_weekend else 100, 200 if is_weekend else 500),
            'status': status_val
        }
        
        return metrics

    def export_to_file(self, days_back: int = 30, interval_minutes: int = 15, output_file: str = "metrics_data.json"):
        """
        Export historical data to JSON file for import into Prometheus/Grafana
        """
        logger.info(f"Exporting data to {output_file}")
        
        # Calculate time range starting from 30 days ago
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        current_time = start_time
        
        all_data = []
        
        while current_time <= end_time:
            timestamp = int(current_time.timestamp())
            
            for fip_name, bank_name in self.fips.items():
                if random.random() > 0.7:  # 70% chance of having data
                    continue
                
                metrics = self.generate_realistic_metrics(timestamp, fip_name, bank_name)
                
                data_point = {
                    "timestamp": timestamp,
                    "datetime": current_time.isoformat(),
                    "fip_name": fip_name,
                    "bank_name": bank_name,
                    "metrics": metrics
                }
                all_data.append(data_point)
            
            # Move forward by interval
            current_time += timedelta(minutes=interval_minutes)
            
            # Log progress every hour
            if current_time.minute == 0:
                logger.info(f"Generating data for {current_time.isoformat()}")
        
        # Sort data by timestamp to ensure chronological order
        all_data.sort(key=lambda x: x['timestamp'])
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        logger.info(f"Exported {len(all_data)} data points from {start_time.isoformat()} to {end_time.isoformat()}")
        return output_file

    def generate_historical_data(self, output_file: str = "fip_metrics_historical.json"):
        """Generate historical data if file doesn't exist"""
        logger.info("Generating new historical data...")
        
        self.export_to_file(days_back=30, interval_minutes=15, output_file=output_file)
        
        logger.info(f"Historical data generated and saved to {output_file}")
