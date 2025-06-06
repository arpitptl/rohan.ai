
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuration management for AA Gateway AI Operations
    """
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///aa_gateway.db')
    
    # AWS Bedrock Configuration
    USE_REAL_BEDROCK = os.getenv('USE_REAL_BEDROCK', 'false').lower() == 'true'
    BEDROCK_REGION = os.getenv('BEDROCK_REGION', 'us-east-1')
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # Prometheus Configuration
    PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
    PROMETHEUS_PUSHGATEWAY_URL = os.getenv('PROMETHEUS_PUSHGATEWAY_URL', 'localhost:9091')
    
    # Metrics Configuration
    METRICS_UPDATE_INTERVAL = int(os.getenv('METRICS_UPDATE_INTERVAL', '120'))  # 2 minutes
    PREDICTIONS_UPDATE_INTERVAL = int(os.getenv('PREDICTIONS_UPDATE_INTERVAL', '900'))  # 15 minutes
    
    # FIP Configuration
    ENABLE_BACKGROUND_TASKS = os.getenv('ENABLE_BACKGROUND_TASKS', 'true').lower() == 'true'
    
    @staticmethod
    def get_fip_config():
        """
        Get FIP configuration (can be overridden from environment)
        """
        return {
            'total_fips': int(os.getenv('TOTAL_FIPS', '11')),
            'simulation_mode': os.getenv('SIMULATION_MODE', 'realistic'),
            'enable_degradation_simulation': os.getenv('ENABLE_DEGRADATION_SIMULATION', 'true').lower() == 'true'
        }

