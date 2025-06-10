import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
from dataclasses import dataclass
from utils.logger import logger

@dataclass
class MetricQuery:
    name: str
    query: str
    description: str

class PrometheusHistoricalAnalyzer:
    """
    Service to extract and analyze historical Prometheus/VictoriaMetrics data
    for FIP performance insights and pattern detection
    """
    
    def __init__(self, prometheus_url: str = "http://victoriametrics:8428"):
        self.prometheus_url = prometheus_url
        self.logger = logger
        
        # Define key metrics for analysis
        self.metric_queries = {
            'consent_success_rate': MetricQuery(
                name='consent_success_rate',
                query='fip_consent_success_rate',
                description='FIP consent approval success rate'
            ),
            'data_fetch_success_rate': MetricQuery(
                name='data_fetch_success_rate', 
                query='fip_data_fetch_success_rate',
                description='FIP data fetch success rate'
            ),
            'response_time': MetricQuery(
                name='response_time',
                query='fip_avg_response_time_seconds',
                description='FIP average response time'
            ),
            'error_rate': MetricQuery(
                name='error_rate',
                query='fip_error_rate', 
                description='FIP error rate'
            ),
            'status': MetricQuery(
                name='status',
                query='fip_status',
                description='FIP operational status'
            ),
            'total_requests': MetricQuery(
                name='total_requests',
                query='increase(fip_total_requests_total[1h])',
                description='FIP request volume per hour'
            )
        }
    
    def extract_historical_data(self, days_back: int = 7, step: str = "15m") -> Dict[str, pd.DataFrame]:
        """
        Extract historical metrics for all FIPs over specified time period
        
        Args:
            days_back: Number of days to look back
            step: Query resolution (e.g., "15m", "1h", "1d")
            
        Returns:
            Dictionary of DataFrames by metric type
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        self.logger.info(f"Extracting {days_back} days of historical data from {start_time} to {end_time}")
        
        historical_data = {}
        
        for metric_name, metric_query in self.metric_queries.items():
            try:
                self.logger.info(f"Querying {metric_name}...")
                df = self._query_range(
                    query=metric_query.query,
                    start_time=start_time,
                    end_time=end_time,
                    step=step
                )
                historical_data[metric_name] = df
                self.logger.info(f"Retrieved {len(df)} data points for {metric_name}")
                
            except Exception as e:
                self.logger.error(f"Error querying {metric_name}: {e}")
                historical_data[metric_name] = pd.DataFrame()
        
        return historical_data
    
    def _query_range(self, query: str, start_time: datetime, end_time: datetime, step: str) -> pd.DataFrame:
        """
        Execute Prometheus range query and return as DataFrame
        """
        params = {
            'query': query,
            'start': start_time.isoformat() + 'Z',
            'end': end_time.isoformat() + 'Z', 
            'step': step
        }
        # logger.info(f"Prometheus query params: {params}")
        
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                raise Exception(f"Prometheus query failed: {data}")
            
            # Convert to DataFrame
            results = []
            for result in data['data']['result']:
                labels = result['metric']
                fip_name = labels.get('fip_name', 'unknown')
                bank_name = labels.get('bank_name', 'unknown')
                
                for timestamp, value in result['values']:
                    results.append({
                        'timestamp': datetime.fromtimestamp(float(timestamp)),
                        'fip_name': fip_name,
                        'bank_name': bank_name,
                        'value': float(value) if value != 'NaN' else np.nan,
                        'labels': labels
                    })
            
            df = pd.DataFrame(results)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error executing Prometheus query: {e}")
            return pd.DataFrame()
    
    def calculate_features(self, historical_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Calculate ML features from historical data for each FIP
        
        Args:
            historical_data: Dictionary of DataFrames by metric type
            
        Returns:
            Dictionary of features by FIP name
        """
        self.logger.info("Calculating features from historical data...")
        
        # Get all unique FIPs
        all_fips = set()
        for df in historical_data.values():
            if not df.empty:
                all_fips.update(df['fip_name'].unique())
        
        fip_features = {}
        
        for fip_name in all_fips:
            try:
                features = self._calculate_fip_features(fip_name, historical_data)
                fip_features[fip_name] = features
                self.logger.info(f"Calculated {len(features)} features for {fip_name}")
                
            except Exception as e:
                self.logger.error(f"Error calculating features for {fip_name}: {e}")
                fip_features[fip_name] = {}
        
        return fip_features
    
    def _calculate_fip_features(self, fip_name: str, historical_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Calculate comprehensive features for a single FIP
        """
        features = {
            'fip_name': fip_name,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'data_quality': {},
            'statistical_features': {},
            'trend_features': {},
            'pattern_features': {},
            'anomaly_features': {},
            'performance_features': {},
            'stability_features': {}
        }
        
        # Get FIP-specific data
        fip_data = {}
        for metric_name, df in historical_data.items():
            if not df.empty:
                fip_df = df[df['fip_name'] == fip_name].copy()
                if not fip_df.empty:
                    fip_data[metric_name] = fip_df
        
        if not fip_data:
            return features
        
        # Data Quality Features
        features['data_quality'] = self._calculate_data_quality_features(fip_data)
        
        # Statistical Features
        features['statistical_features'] = self._calculate_statistical_features(fip_data)
        
        # Trend Features
        features['trend_features'] = self._calculate_trend_features(fip_data)
        
        # Pattern Features
        features['pattern_features'] = self._calculate_pattern_features(fip_data)
        
        # Anomaly Features
        features['anomaly_features'] = self._calculate_anomaly_features(fip_data)
        
        # Performance Features
        features['performance_features'] = self._calculate_performance_features(fip_data)
        
        # Stability Features
        features['stability_features'] = self._calculate_stability_features(fip_data)
        
        return features
    
    def _calculate_data_quality_features(self, fip_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate data quality metrics"""
        quality_features = {}
        
        for metric_name, df in fip_data.items():
            quality_features[metric_name] = {
                'total_points': len(df),
                'missing_values': df['value'].isna().sum(),
                'missing_percentage': (df['value'].isna().sum() / len(df)) * 100,
                'data_span_hours': (df.index.max() - df.index.min()).total_seconds() / 3600,
                'avg_interval_minutes': df.index.to_series().diff().dt.total_seconds().mean() / 60
            }
        
        return quality_features
    
    def _calculate_statistical_features(self, fip_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate statistical features for each metric"""
        stats_features = {}
        
        for metric_name, df in fip_data.items():
            values = df['value'].dropna()
            if len(values) > 0:
                stats_features[metric_name] = {
                    'mean': float(values.mean()),
                    'median': float(values.median()),
                    'std': float(values.std()),
                    'min': float(values.min()),
                    'max': float(values.max()),
                    'p25': float(values.quantile(0.25)),
                    'p75': float(values.quantile(0.75)),
                    'p95': float(values.quantile(0.95)),
                    'skewness': float(values.skew()),
                    'kurtosis': float(values.kurtosis()),
                    'coefficient_of_variation': float(values.std() / values.mean()) if values.mean() != 0 else 0
                }
        
        return stats_features
    
    def _calculate_trend_features(self, fip_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate trend analysis features"""
        trend_features = {}
        
        for metric_name, df in fip_data.items():
            values = df['value'].dropna()
            if len(values) > 1:
                # Simple linear trend
                x = np.arange(len(values))
                slope, intercept = np.polyfit(x, values, 1)
                
                # Recent vs historical comparison
                split_point = len(values) // 2
                recent_mean = values.iloc[split_point:].mean()
                historical_mean = values.iloc[:split_point].mean()
                relative_change = ((recent_mean - historical_mean) / historical_mean) * 100 if historical_mean != 0 else 0
                
                # Moving averages
                ma_short = values.rolling(window=min(6, len(values)//2)).mean()
                ma_long = values.rolling(window=min(12, len(values)//2)).mean()
                
                trend_features[metric_name] = {
                    'linear_slope': float(slope),
                    'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                    'recent_vs_historical_change_pct': float(relative_change),
                    'trend_strength': abs(float(slope)),
                    'moving_avg_crossover': bool((ma_short.iloc[-1] > ma_long.iloc[-1]) if not (ma_short.isna().iloc[-1] or ma_long.isna().iloc[-1]) else False)
                }
        
        return trend_features
    
    def _calculate_pattern_features(self, fip_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate time-based pattern features"""
        pattern_features = {}
        
        for metric_name, df in fip_data.items():
            if df.empty:
                continue
                
            df_copy = df.copy()
            df_copy['hour'] = df_copy.index.hour
            df_copy['day_of_week'] = df_copy.index.dayofweek
            df_copy['is_weekend'] = df_copy['day_of_week'].isin([5, 6])
            
            values = df_copy['value'].dropna()
            
            if len(values) > 0:
                # Hourly patterns
                hourly_stats = df_copy.groupby('hour')['value'].agg(['mean', 'std', 'count'])
                peak_hour = hourly_stats['mean'].idxmax()
                low_hour = hourly_stats['mean'].idxmin()
                
                # Day of week patterns
                dow_stats = df_copy.groupby('day_of_week')['value'].mean()
                
                # Weekend vs weekday
                weekend_mean = df_copy[df_copy['is_weekend']]['value'].mean()
                weekday_mean = df_copy[~df_copy['is_weekend']]['value'].mean()
                
                pattern_features[metric_name] = {
                    'peak_hour': int(peak_hour),
                    'low_hour': int(low_hour),
                    'hourly_variation_coefficient': float(hourly_stats['mean'].std() / hourly_stats['mean'].mean()) if hourly_stats['mean'].mean() != 0 else 0,
                    'weekend_vs_weekday_ratio': float(weekend_mean / weekday_mean) if weekday_mean != 0 and not np.isnan(weekend_mean) else 1,
                    'has_clear_daily_pattern': bool(hourly_stats['mean'].std() > hourly_stats['mean'].mean() * 0.1),
                    'most_stable_hour': int(hourly_stats['std'].idxmin()) if not hourly_stats['std'].isna().all() else 0
                }
        
        return pattern_features
    
    def _calculate_anomaly_features(self, fip_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate anomaly detection features"""
        anomaly_features = {}
        
        for metric_name, df in fip_data.items():
            values = df['value'].dropna()
            if len(values) > 5:
                # Z-score based anomalies
                z_scores = np.abs((values - values.mean()) / values.std())
                anomaly_threshold = 2.5
                anomalies = z_scores > anomaly_threshold
                
                # IQR based anomalies
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                iqr_anomalies = (values < lower_bound) | (values > upper_bound)
                
                # Recent anomalies (last 20% of data)
                recent_threshold = int(len(values) * 0.8)
                recent_anomalies = anomalies.iloc[recent_threshold:].sum()
                
                anomaly_features[metric_name] = {
                    'total_anomalies': int(anomalies.sum()),
                    'anomaly_rate': float(anomalies.mean()),
                    'recent_anomalies': int(recent_anomalies),
                    'iqr_anomalies': int(iqr_anomalies.sum()),
                    'max_z_score': float(z_scores.max()),
                    'anomaly_severity': 'high' if anomalies.mean() > 0.1 else 'medium' if anomalies.mean() > 0.05 else 'low'
                }
        
        return anomaly_features
    
    def _calculate_performance_features(self, fip_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate performance-specific features"""
        performance_features = {}
        
        # Cross-metric analysis
        if 'consent_success_rate' in fip_data and 'response_time' in fip_data:
            consent_df = fip_data['consent_success_rate']
            response_df = fip_data['response_time']
            
            # Align timestamps for correlation
            merged = pd.merge(consent_df[['value']], response_df[['value']], 
                            left_index=True, right_index=True, suffixes=('_consent', '_response'))
            
            if len(merged) > 2:
                correlation = merged['value_consent'].corr(merged['value_response'])
                performance_features['consent_response_correlation'] = float(correlation) if not np.isnan(correlation) else 0
        
        # Success rate analysis
        if 'consent_success_rate' in fip_data:
            consent_values = fip_data['consent_success_rate']['value'].dropna()
            if len(consent_values) > 0:
                performance_features['consent_stability'] = {
                    'below_80_pct_time': float((consent_values < 80).mean()),
                    'below_50_pct_time': float((consent_values < 50).mean()),
                    'average_success_rate': float(consent_values.mean()),
                    'worst_performance_period': float(consent_values.min()),
                    'performance_volatility': float(consent_values.std())
                }
        
        # Response time analysis
        if 'response_time' in fip_data:
            response_values = fip_data['response_time']['value'].dropna()
            if len(response_values) > 0:
                performance_features['response_time_analysis'] = {
                    'above_5s_time': float((response_values > 5).mean()),
                    'above_10s_time': float((response_values > 10).mean()),
                    'average_response_time': float(response_values.mean()),
                    'worst_response_time': float(response_values.max()),
                    'response_time_volatility': float(response_values.std())
                }
        
        return performance_features
    
    def _calculate_stability_features(self, fip_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate system stability features"""
        stability_features = {}
        # Status changes analysis
        if 'status' in fip_data:
            status_df = fip_data['status']
            status_values = status_df['value'].dropna()
            
            if len(status_values) > 1:
                # Count status changes
                status_changes = (status_values.diff() != 0).sum()
                
                # Time in each state
                healthy_time = (status_values == 1.0).mean()
                degraded_time = (status_values == 0.5).mean()
                critical_time = (status_values == 0.0).mean()
                
                # Stability score
                stability_score = healthy_time * 1.0 + degraded_time * 0.5 + critical_time * 0.0
                
                stability_features['status_analysis'] = {
                    'status_changes': int(status_changes),
                    'healthy_time_pct': float(healthy_time * 100),
                    'degraded_time_pct': float(degraded_time * 100),
                    'critical_time_pct': float(critical_time * 100),
                    'stability_score': float(stability_score),
                    'status_volatility': float(status_values.std())
                }
        
        # Overall system stability
        all_metrics_stability = []
        for metric_name, df in fip_data.items():
            if metric_name in ['consent_success_rate', 'data_fetch_success_rate']:
                values = df['value'].dropna()
                if len(values) > 0:
                    cv = values.std() / values.mean() if values.mean() != 0 else float('inf')
                    all_metrics_stability.append(cv)

        if all_metrics_stability:
            stability_features['overall_stability'] = {
                'average_coefficient_of_variation': float(np.mean(all_metrics_stability)),
                'stability_grade': 'excellent' if np.mean(all_metrics_stability) < 0.1 else 
                                'good' if np.mean(all_metrics_stability) < 0.2 else
                                'fair' if np.mean(all_metrics_stability) < 0.3 else 'poor'
            }
        
        return stability_features
    
    def detect_maintenance_windows(self, historical_data: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict]]:
        """
        Detect recurring maintenance windows from historical data
        """
        maintenance_windows = {}
        
        for fip_name in set().union(*[df['fip_name'].unique() for df in historical_data.values() if not df.empty]):
            windows = []
            
            # Analyze status data for maintenance patterns
            if 'status' in historical_data and not historical_data['status'].empty:
                fip_status = historical_data['status'][historical_data['status']['fip_name'] == fip_name]
                
                if not fip_status.empty:
                    # Find periods where status was critical (0) or degraded (0.5)
                    downtime_periods = fip_status[fip_status['value'] < 0.1]
                    
                    if not downtime_periods.empty:
                        # Group by hour and day of week to find patterns
                        downtime_periods_copy = downtime_periods.copy()
                        downtime_periods_copy['hour'] = downtime_periods_copy.index.hour
                        downtime_periods_copy['day_of_week'] = downtime_periods_copy.index.dayofweek
                        
                        # Find common maintenance hours
                        hourly_downtime = downtime_periods_copy.groupby('hour').size()
                        common_hours = hourly_downtime[hourly_downtime > hourly_downtime.mean()].index.tolist()
                        
                        # Find common maintenance days
                        daily_downtime = downtime_periods_copy.groupby('day_of_week').size()
                        common_days = daily_downtime[daily_downtime > daily_downtime.mean()].index.tolist()
                        
                        if common_hours:
                            windows.append({
                                'type': 'recurring_hourly',
                                'hours': common_hours,
                                'frequency': len(downtime_periods) / len(fip_status),
                                'confidence': min(1.0, len(downtime_periods) / 10),
                                'description': f"Recurring maintenance detected during hours: {common_hours}"
                            })
                        
                        if common_days:
                            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                            day_names_list = [day_names[d] for d in common_days]
                            windows.append({
                                'type': 'recurring_daily',
                                'days': common_days,
                                'day_names': day_names_list,
                                'frequency': len(downtime_periods) / len(fip_status),
                                'confidence': min(1.0, len(downtime_periods) / 5),
                                'description': f"Recurring maintenance detected on: {', '.join(day_names_list)}"
                            })
            
            maintenance_windows[fip_name] = windows
        
        return maintenance_windows
    
    def generate_summary_report(self, historical_data: Dict[str, pd.DataFrame], 
                               fip_features: Dict[str, Dict], 
                               maintenance_windows: Dict[str, List[Dict]]) -> Dict:
        """
        Generate a comprehensive summary report for Bedrock analysis
        """
        
        # Calculate overall system metrics
        total_fips = len(fip_features)
        
        # Aggregate health scores
        health_scores = []
        performance_issues = []
        stability_issues = []
        
        for fip_name, features in fip_features.items():
            # Extract key metrics
            if 'statistical_features' in features and 'consent_success_rate' in features['statistical_features']:
                avg_success = features['statistical_features']['consent_success_rate']['mean']
                health_scores.append(avg_success)
                
                if avg_success < 70:
                    performance_issues.append({
                        'fip_name': fip_name,
                        'issue': 'low_success_rate',
                        'value': avg_success,
                        'severity': 'critical' if avg_success < 50 else 'warning'
                    })
            
            # Check stability
            if 'stability_features' in features and 'overall_stability' in features['stability_features']:
                stability_grade = features['stability_features']['overall_stability']['stability_grade']
                if stability_grade in ['fair', 'poor']:
                    stability_issues.append({
                        'fip_name': fip_name,
                        'issue': 'stability_concern',
                        'grade': stability_grade,
                        'severity': 'critical' if stability_grade == 'poor' else 'warning'
                    })
        
        # System-wide summary
        system_summary = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'total_fips_analyzed': total_fips,
            'data_quality': {
                'fips_with_data': len([f for f in fip_features.values() if f.get('data_quality')]),
                'avg_data_completeness': self._calculate_avg_data_completeness(fip_features)
            },
            'performance_overview': {
                'avg_system_health': np.mean(health_scores) if health_scores else 0,
                'fips_with_performance_issues': len(performance_issues),
                'critical_performance_issues': len([i for i in performance_issues if i['severity'] == 'critical']),
                'fips_with_stability_issues': len(stability_issues)
            },
            'maintenance_patterns': {
                'fips_with_detected_patterns': len([w for w in maintenance_windows.values() if w]),
                'total_maintenance_windows': sum(len(w) for w in maintenance_windows.values())
            },
            'detailed_issues': {
                'performance_issues': performance_issues,
                'stability_issues': stability_issues
            }
        }
        
        # Prepare comprehensive report for Bedrock
        comprehensive_report = {
            'system_summary': system_summary,
            'fip_features': fip_features,
            'maintenance_windows': maintenance_windows,
            'time_range_analyzed': self._get_time_range_info(historical_data),
            'recommendations_needed': {
                'immediate_attention': [i['fip_name'] for i in performance_issues if i['severity'] == 'critical'],
                'monitoring_required': [i['fip_name'] for i in performance_issues if i['severity'] == 'warning'],
                'stability_concerns': [i['fip_name'] for i in stability_issues]
            }
        }
        
        return comprehensive_report
    
    def _calculate_avg_data_completeness(self, fip_features: Dict[str, Dict]) -> float:
        """Calculate average data completeness across all FIPs"""
        completeness_scores = []
        
        for features in fip_features.values():
            if 'data_quality' in features:
                for metric_quality in features['data_quality'].values():
                    if isinstance(metric_quality, dict) and 'missing_percentage' in metric_quality:
                        completeness = 100 - metric_quality['missing_percentage']
                        completeness_scores.append(completeness)
        
        return np.mean(completeness_scores) if completeness_scores else 0
    
    def _get_time_range_info(self, historical_data: Dict[str, pd.DataFrame]) -> Dict:
        """Get information about the time range of analyzed data"""
        all_timestamps = []
        
        for df in historical_data.values():
            if not df.empty:
                all_timestamps.extend(df.index.tolist())
        
        if all_timestamps:
            min_time = min(all_timestamps)
            max_time = max(all_timestamps)
            return {
                'start_time': min_time.isoformat(),
                'end_time': max_time.isoformat(),
                'duration_hours': (max_time - min_time).total_seconds() / 3600,
                'total_data_points': len(all_timestamps)
            }
        
        return {}