
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class DataPipeline:
    """
    Data pipeline for processing FIP metrics and feeding to Bedrock
    Simulates real-time data flow: Metrics -> Processing -> Bedrock -> Predictions
    """
    
    def __init__(self, metrics_service, bedrock_service, prometheus_service):
        self.metrics_service = metrics_service
        self.bedrock_service = bedrock_service
        self.prometheus_service = prometheus_service
        
        self.pipeline_running = False
        self.pipeline_thread = None
        self.processed_data_queue = []
        
        print("🔄 Data pipeline initialized")
    
    def start_pipeline(self):
        """
        Start the data pipeline
        """
        if not self.pipeline_running:
            self.pipeline_running = True
            self.pipeline_thread = threading.Thread(target=self._pipeline_worker, daemon=True)
            self.pipeline_thread.start()
            print("▶️  Data pipeline started")
    
    def stop_pipeline(self):
        """
        Stop the data pipeline
        """
        self.pipeline_running = False
        if self.pipeline_thread:
            self.pipeline_thread.join(timeout=5)
        print("⏹️  Data pipeline stopped")
    
    def _pipeline_worker(self):
        """
        Main pipeline worker that runs continuously
        """
        while self.pipeline_running:
            try:
                # Step 1: Update FIP metrics
                self.metrics_service.update_fip_metrics()
                
                # Step 2: Push metrics to Prometheus
                self.prometheus_service.push_mock_metrics()
                
                # Step 3: Prepare data for Bedrock analysis
                current_metrics = self.metrics_service.get_all_fips_status()
                
                # Step 4: Process with Bedrock (every 15 minutes for predictions)
                if self._should_run_prediction():
                    predictions = self.bedrock_service.predict_downtime(current_metrics, '24h')
                    
                    # Step 5: Store processed results
                    self._store_processed_data({
                        'timestamp': datetime.utcnow().isoformat(),
                        'metrics': current_metrics,
                        'predictions': predictions,
                        'pipeline_status': 'success'
                    })
                    
                    print(f"🔮 Generated predictions for {len(predictions)} FIPs")
                
                # Wait before next cycle (2 minutes for metrics, 15 minutes for predictions)
                time.sleep(120)  # 2 minutes
                
            except Exception as e:
                print(f"❌ Pipeline error: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def _should_run_prediction(self) -> bool:
        """
        Determine if predictions should be run (every 15 minutes)
        """
        current_minute = datetime.utcnow().minute
        return current_minute % 15 == 0  # Run every 15 minutes
    
    def _store_processed_data(self, data: Dict):
        """
        Store processed pipeline data
        """
        self.processed_data_queue.append(data)
        
        # Keep only last 50 entries to prevent memory issues
        if len(self.processed_data_queue) > 50:
            self.processed_data_queue = self.processed_data_queue[-50:]
    
    def get_pipeline_status(self) -> Dict:
        """
        Get current pipeline status and recent results
        """
        return {
            'status': 'running' if self.pipeline_running else 'stopped',
            'last_run': self.processed_data_queue[-1]['timestamp'] if self.processed_data_queue else None,
            'total_runs': len(self.processed_data_queue),
            'recent_results': self.processed_data_queue[-5:] if self.processed_data_queue else []
        }
    
    def process_realtime_data(self, fip_name: str, new_metrics: Dict) -> Dict:
        """
        Process real-time data updates for specific FIP
        """
        try:
            # Update specific FIP metrics
            current_metrics = self.metrics_service.get_all_fips_status()
            current_metrics[fip_name].update(new_metrics)
            
            # Generate immediate prediction for this FIP
            single_fip_metrics = {fip_name: current_metrics[fip_name]}
            prediction = self.bedrock_service.predict_downtime(single_fip_metrics, '4h')
            
            # Push updated metrics to Prometheus
            self.prometheus_service.push_mock_metrics()
            
            return {
                'status': 'success',
                'fip_name': fip_name,
                'updated_metrics': current_metrics[fip_name],
                'prediction': prediction.get(fip_name, {}),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
