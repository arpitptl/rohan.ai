import boto3
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional
from utils.logger import logger
from datetime import datetime, timedelta

class FIPDowntimePredictor:
    """
    Advanced downtime prediction system for FIP services using VictoriaMetrics and AWS Bedrock
    """
    
    def __init__(self, vm_url: str, aws_region: str = 'us-east-1'):
        """
        Initialize the FIP downtime predictor
        
        Args:
            vm_url: VictoriaMetrics URL (e.g., 'http://localhost:8428')
            aws_region: AWS region for Bedrock
        """
        self.vm_url = vm_url
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
        # self.lookout_client = boto3.client('lookoutmetrics', region_name=aws_region)

        # FIP metrics configuration based on your Prometheus service
        self.fip_metrics_config = {
            'consent_success_rate': {
                'query': 'fip_consent_success_rate',
                'threshold_critical': 70,  # Below 70% is critical
                'threshold_warning': 85,   # Below 85% is warning
                'weight': 0.25
            },
            'data_fetch_success_rate': {
                'query': 'fip_data_fetch_success_rate',
                'threshold_critical': 75,
                'threshold_warning': 90,
                'weight': 0.25
            },
            'response_time': {
                'query': 'fip_avg_response_time_seconds',
                'threshold_critical': 5.0,  # Above 5 seconds is critical
                'threshold_warning': 3.0,   # Above 3 seconds is warning
                'weight': 0.20,
                'invert': True  # Higher values are worse
            },
            'error_rate': {
                'query': 'fip_error_rate',
                'threshold_critical': 10,   # Above 10% is critical
                'threshold_warning': 5,     # Above 5% is warning
                'weight': 0.15,
                'invert': True
            },
            'status': {
                'query': 'fip_status',
                'threshold_critical': 0.5,  # Below 0.5 is critical
                'threshold_warning': 0.8,   # Below 0.8 is warning
                'weight': 0.15
            }
        }
    
    def extract_fip_metrics(self, fip_name: str, bank_name: str, hours_back: int = 168) -> pd.DataFrame:
        """
        Extract FIP metrics from VictoriaMetrics for the last N hours
        
        Args:
            fip_name: FIP service name
            bank_name: Bank name
            hours_back: Hours of historical data to fetch (default: 7 days)
        
        Returns:
            DataFrame with timestamped metrics
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        all_metrics = []
        
        for metric_name, config in self.fip_metrics_config.items():
            try:
                # Build PromQL query with labels
                query = f'{config["query"]}{{fip_name="{fip_name}", bank_name="{bank_name}"}}'
                
                params = {
                    'query': query,
                    'start': int(start_time.timestamp()),
                    'end': int(end_time.timestamp()),
                    'step': '300'  # 5-minute intervals
                }
                
                response = requests.get(f"{self.vm_url}/api/v1/query_range", params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'data' in data and 'result' in data['data'] and data['data']['result']:
                    series = data['data']['result'][0]  # Take first series
                    
                    for timestamp_str, value_str in series.get('values', []):
                        timestamp = pd.to_datetime(float(timestamp_str), unit='s')
                        value = float(value_str) if value_str != 'NaN' else np.nan
                        
                        all_metrics.append({
                            'timestamp': timestamp,
                            'metric': metric_name,
                            'value': value,
                            'fip_name': fip_name,
                            'bank_name': bank_name
                        })
                
            except Exception as e:
                logger.warning(f"Failed to fetch {metric_name} for {fip_name}: {e}")
        
        if not all_metrics:
            logger.error(f"No metrics found for FIP {fip_name}")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_metrics)
        df = df.pivot(index=['timestamp', 'fip_name', 'bank_name'], 
                     columns='metric', values='value').reset_index()
        
        # Fill missing values with forward fill then backward fill
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(method='ffill').fillna(method='bfill')
        
        return df
    
    def calculate_health_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate composite health score for FIP service
        
        Args:
            df: DataFrame with FIP metrics
        
        Returns:
            DataFrame with health scores and risk levels
        """
        df = df.copy()
        
        # Initialize health score
        df['health_score'] = 0.0
        df['risk_factors'] = ''
        
        for metric_name, config in self.fip_metrics_config.items():
            if metric_name in df.columns:
                metric_values = df[metric_name]
                weight = config['weight']
                
                if config.get('invert', False):
                    # For metrics where higher is worse (error_rate, response_time)
                    critical_threshold = config['threshold_critical']
                    warning_threshold = config['threshold_warning']
                    
                    # Score: 1.0 (excellent) to 0.0 (critical)
                    metric_score = np.where(
                        metric_values <= warning_threshold, 1.0,
                        np.where(
                            metric_values <= critical_threshold,
                            1.0 - (metric_values - warning_threshold) / (critical_threshold - warning_threshold),
                            0.0
                        )
                    )
                else:
                    # For metrics where higher is better (success rates, status)
                    critical_threshold = config['threshold_critical']
                    warning_threshold = config['threshold_warning']
                    
                    metric_score = np.where(
                        metric_values >= warning_threshold, 1.0,
                        np.where(
                            metric_values >= critical_threshold,
                            (metric_values - critical_threshold) / (warning_threshold - critical_threshold),
                            0.0
                        )
                    )
                
                df['health_score'] += metric_score * weight
                
                # Track risk factors
                risk_mask = metric_score < 0.5
                df.loc[risk_mask, 'risk_factors'] += f"{metric_name},"
        
        # Normalize health score to 0-100
        df['health_score'] = np.clip(df['health_score'] * 100, 0, 100)
        
        # Determine risk level
        df['risk_level'] = pd.cut(
            df['health_score'],
            bins=[0, 30, 60, 85, 100],
            labels=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            include_lowest=True
        )
        
        # Add time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        df['is_business_hours'] = df['hour'].between(9, 17)
        
        return df
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Detect downtime patterns and maintenance windows
        
        Args:
            df: DataFrame with health scores and metrics
        
        Returns:
            Dictionary with detected patterns
        """
        patterns = {
            'downtime_events': [],
            'maintenance_windows': [],
            'recurring_patterns': {},
            'risk_trends': {}
        }
        
        # Define downtime as health score < 30 for more than 15 minutes
        downtime_mask = df['health_score'] < 30
        df['is_downtime'] = downtime_mask
        
        # Group consecutive downtime periods
        df['downtime_group'] = (downtime_mask != downtime_mask.shift()).cumsum()
        downtime_groups = df[downtime_mask].groupby('downtime_group')
        
        for group_id, group_data in downtime_groups:
            if len(group_data) >= 3:  # At least 15 minutes (3 * 5min intervals)
                start_time = group_data['timestamp'].min()
                end_time = group_data['timestamp'].max()
                duration_minutes = (end_time - start_time).total_seconds() / 60
                
                # Determine if it's planned maintenance
                is_maintenance = (
                    group_data['is_business_hours'].sum() == 0 or  # Outside business hours
                    group_data['is_weekend'].sum() > 0  # During weekend
                )
                
                event = {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_minutes': duration_minutes,
                    'min_health_score': group_data['health_score'].min(),
                    'affected_metrics': group_data['risk_factors'].iloc[0].rstrip(',').split(','),
                    'is_maintenance': is_maintenance
                }
                
                if is_maintenance:
                    patterns['maintenance_windows'].append(event)
                else:
                    patterns['downtime_events'].append(event)
        
        # Analyze recurring patterns
        # Daily patterns
        hourly_downtime = df.groupby('hour')['is_downtime'].mean()
        high_risk_hours = hourly_downtime[hourly_downtime > 0.1].index.tolist()
        
        # Weekly patterns
        daily_downtime = df.groupby('day_of_week')['is_downtime'].mean()
        high_risk_days = daily_downtime[daily_downtime > 0.1].index.tolist()
        
        patterns['recurring_patterns'] = {
            'high_risk_hours': high_risk_hours,
            'high_risk_days': high_risk_days,
            'weekend_risk': df[df['is_weekend']]['is_downtime'].mean(),
            'business_hours_risk': df[df['is_business_hours']]['is_downtime'].mean()
        }
        
        # Risk trends
        df_recent = df.tail(288)  # Last 24 hours
        patterns['risk_trends'] = {
            'current_health_score': df['health_score'].iloc[-1],
            'health_trend_24h': df_recent['health_score'].diff().mean(),
            'critical_incidents_24h': len(df_recent[df_recent['health_score'] < 30]),
            'avg_health_score_7d': df['health_score'].mean()
        }
        
        return patterns
    
    def predict_next_24h_risks(self, df: pd.DataFrame, patterns: Dict) -> Dict:
        """
        Predict downtime risks for the next 24 hours
        
        Args:
            df: Historical data with health scores
            patterns: Detected patterns from historical analysis
        
        Returns:
            Dictionary with 24-hour predictions
        """
        now = datetime.now()
        predictions = {
            'high_risk_periods': [],
            'maintenance_recommendations': [],
            'overall_risk_score': 0,
            'confidence_level': 'MEDIUM'
        }
        
        # Generate hourly predictions for next 24 hours
        for hour_offset in range(24):
            prediction_time = now + timedelta(hours=hour_offset)
            hour = prediction_time.hour
            day_of_week = prediction_time.weekday()
            is_weekend = day_of_week in [5, 6]
            is_business_hours = 9 <= hour <= 17
            
            # Base risk from historical patterns
            base_risk = 0.1  # 10% base risk
            
            # Add risk factors
            if hour in patterns['recurring_patterns']['high_risk_hours']:
                base_risk += 0.3
            
            if day_of_week in patterns['recurring_patterns']['high_risk_days']:
                base_risk += 0.2
            
            if is_weekend:
                base_risk += patterns['recurring_patterns']['weekend_risk'] * 0.5
            
            # Current trend impact
            health_trend = patterns['risk_trends']['health_trend_24h']
            if health_trend < -1:  # Declining health
                base_risk += 0.2
            elif health_trend > 1:  # Improving health
                base_risk -= 0.1
            
            # Current health score impact
            current_health = patterns['risk_trends']['current_health_score']
            if current_health < 50:
                base_risk += 0.3
            elif current_health < 70:
                base_risk += 0.1
            
            risk_score = min(base_risk, 1.0)
            
            if risk_score > 0.4:  # High risk threshold
                predictions['high_risk_periods'].append({
                    'time': prediction_time.isoformat(),
                    'hour': hour,
                    'risk_score': risk_score,
                    'risk_level': 'HIGH' if risk_score > 0.6 else 'MEDIUM',
                    'factors': [
                        f"Historical hour pattern" if hour in patterns['recurring_patterns']['high_risk_hours'] else None,
                        f"Weekend pattern" if is_weekend and patterns['recurring_patterns']['weekend_risk'] > 0.1 else None,
                        f"Declining health trend" if health_trend < -1 else None,
                        f"Current low health score ({current_health:.1f})" if current_health < 70 else None
                    ]
                })
        
        # Calculate overall risk score
        if predictions['high_risk_periods']:
            predictions['overall_risk_score'] = np.mean([p['risk_score'] for p in predictions['high_risk_periods']])
        
        # Maintenance recommendations
        if patterns['maintenance_windows']:
            last_maintenance = max([pd.to_datetime(mw['start_time']) for mw in patterns['maintenance_windows']])
            days_since_maintenance = (now - last_maintenance).days
            
            if days_since_maintenance > 30:  # More than 30 days since last maintenance
                predictions['maintenance_recommendations'].append({
                    'urgency': 'HIGH',
                    'reason': f"No maintenance detected in {days_since_maintenance} days",
                    'suggested_window': 'Weekend non-business hours',
                    'estimated_duration': '30-60 minutes'
                })
        
        return predictions
    
    def generate_bedrock_analysis(self, fip_name: str, patterns: Dict, predictions: Dict) -> str:
        """
        Generate comprehensive analysis using AWS Bedrock
        
        Args:
            fip_name: FIP service name
            patterns: Historical patterns
            predictions: 24-hour predictions
        
        Returns:
            AI-generated analysis and recommendations
        """
        prompt = f"""
        Analyze the following FIP service health data for predictive maintenance and downtime prevention:
        
        SERVICE: {fip_name}
        ANALYSIS PERIOD: Last 7 days
        
        HISTORICAL PATTERNS:
        - Total Downtime Events: {len(patterns['downtime_events'])}
        - Planned Maintenance Windows: {len(patterns['maintenance_windows'])}
        - High Risk Hours: {patterns['recurring_patterns']['high_risk_hours']}
        - High Risk Days: {patterns['recurring_patterns']['high_risk_days']}
        - Weekend Risk Factor: {patterns['recurring_patterns']['weekend_risk']:.2%}
        - Business Hours Risk: {patterns['recurring_patterns']['business_hours_risk']:.2%}
        
        CURRENT STATUS:
        - Current Health Score: {patterns['risk_trends']['current_health_score']:.1f}/100
        - 24h Health Trend: {patterns['risk_trends']['health_trend_24h']:+.2f}
        - Critical Incidents (24h): {patterns['risk_trends']['critical_incidents_24h']}
        - 7-day Average Health: {patterns['risk_trends']['avg_health_score_7d']:.1f}/100
        
        NEXT 24 HOURS PREDICTION:
        - High Risk Periods: {len(predictions['high_risk_periods'])}
        - Overall Risk Score: {predictions['overall_risk_score']:.2%}
        - Maintenance Recommendations: {len(predictions['maintenance_recommendations'])}
        
        HIGH RISK PERIODS:
        {json.dumps(predictions['high_risk_periods'], indent=2)}
        
        Please provide:
        1. Root cause analysis of downtime patterns
        2. Specific time windows for preventive maintenance
        3. Early warning indicators to monitor
        4. Actionable recommendations to reduce downtime risk
        5. Business impact assessment
        6. Emergency response procedures for predicted high-risk periods
        
        Format the response with clear sections and actionable insights.
        """
        logger.info("Generating bedrock analysis")
        logger.info(prompt)
        return "ai_analysis"
        
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=body,
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Bedrock analysis failed: {e}")
            return f"Analysis unavailable due to error: {e}"
    
    def run_comprehensive_analysis(self, fip_name: str, bank_name: str) -> Dict:
        """
        Run complete downtime prediction analysis for a FIP service
        
        Args:
            fip_name: FIP service name
            bank_name: Bank name
        
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting comprehensive analysis for {fip_name} ({bank_name})")
        
        try:
            # Step 1: Extract metrics
            df = self.extract_fip_metrics(fip_name, bank_name, hours_back=168)  # 7 days
            if df.empty:
                raise ValueError("No metrics data available")
            
            # Step 2: Calculate health scores
            df_with_health = self.calculate_health_score(df)
            
            # # Step 3: Detect patterns
            patterns = self.detect_patterns(df_with_health)
            logger.info(f"Patterns: {patterns}")
            
            # # Step 4: Predict next 24h risks
            predictions = self.predict_next_24h_risks(df_with_health, patterns)
            logger.info(f"Predictions: {predictions}")
            # # Step 5: Generate AI analysis
            ai_analysis = self.generate_bedrock_analysis(fip_name, patterns, predictions)
            

            patterns = {
                "risk_trends": {
                    "current_health_score": 0,
                }
            }

            predictions = {
                "high_risk_periods": [],
                "maintenance_recommendations": [],
                "overall_risk_score": 0.7,
                "confidence_level": "MEDIUM"
            }
            
            # Step 6: Compile results
            results = {
                'fip_name': fip_name,
                'bank_name': bank_name,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_points_analyzed': len(df_with_health),
                'patterns': patterns,
                'predictions_24h': predictions,
                'ai_analysis': "ai_analysis",
                'summary': {
                    'current_health_score': patterns['risk_trends']['current_health_score'],
                    'risk_level': 'HIGH' if predictions['overall_risk_score'] > 0.6 else 'MEDIUM' if predictions['overall_risk_score'] > 0.3 else 'LOW',
                    'next_high_risk_period': predictions['high_risk_periods'][0] if predictions['high_risk_periods'] else None,
                    'maintenance_needed': len(predictions['maintenance_recommendations']) > 0
                }
            }
            
            logger.info(f"✅ Analysis completed for {fip_name}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {fip_name}: {e}")
            raise
    
    def monitor_all_fips(self, fip_list: List[Tuple[str, str]]) -> Dict:
        """
        Monitor multiple FIP services
        
        Args:
            fip_list: List of (fip_name, bank_name) tuples
        
        Returns:
            Combined monitoring results
        """
        all_results = {}
        critical_alerts = []
        
        for fip_name, bank_name in fip_list:
            try:
                result = self.run_comprehensive_analysis(fip_name, bank_name)
                all_results[fip_name] = result
                
                # Check for critical alerts
                if result['summary']['risk_level'] == 'HIGH':
                    critical_alerts.append({
                        'fip_name': fip_name,
                        'bank_name': bank_name,
                        'health_score': result['summary']['current_health_score'],
                        'next_risk_period': result['summary']['next_high_risk_period']
                    })
                    
            except Exception as e:
                logger.error(f"Failed to analyze {fip_name}: {e}")
                all_results[fip_name] = {'error': str(e)}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_fips_analyzed': len(fip_list),
            'critical_alerts': critical_alerts,
            'results': all_results
        }

# Example usage
def predictor_main():
    # Initialize predictor
    predictor = FIPDowntimePredictor(vm_url='http://victoriametrics:8428')
    
    # Analyze single FIP
    try:
        result = predictor.run_comprehensive_analysis('sbi-fip', 'State Bank of India')
        logger.info(result)
        
        logger.info(f"🏥 Health Score: {result['summary']['current_health_score']:.1f}/100")
        logger.info(f"⚠️  Risk Level: {result['summary']['risk_level']}")
        logger.info(f"📅 High Risk Periods (24h): {len(result['predictions_24h']['high_risk_periods'])}")
        logger.info(f"🔧 Maintenance Needed: {result['summary']['maintenance_needed']}")
        
        # logger.info AI analysis
        logger.info("\n🤖 AI Analysis:")
        logger.info(result['ai_analysis'])
        
    except Exception as e:
        logger.info(f"❌ Analysis failed: {e}")
    
    # Monitor multiple FIPs
    fip_services = [
        ('sbi-fip', 'State Bank of India')
    ]
    
    monitoring_results = predictor.monitor_all_fips(fip_services)
    logger.info(f"\n📊 Monitoring Summary: {len(monitoring_results['critical_alerts'])} critical alerts")