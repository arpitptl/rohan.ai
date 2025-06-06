
# ================================
# Quick Start Instructions
# ================================

## 🚀 Quick Start Guide

### Option 1: Direct Python Run (Recommended for Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env file if needed

# 3. Run the application
python run.py

# 4. Access the dashboard
# http://localhost:5000
```

### Option 2: Docker Compose (Recommended for Demo)

```bash
# 1. Start all services
python run.py docker

# 2. Access services
# Dashboard: http://localhost:5000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)

# 3. Stop services
docker-compose down
```

### Option 3: Manual Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start Prometheus (optional)
# Download from https://prometheus.io/download/
./prometheus --config.file=prometheus.yml

# 3. Start Pushgateway (optional)
# Download from https://prometheus.io/download/
./pushgateway

# 4. Run Flask app
export FLASK_DEBUG=true
export USE_REAL_BEDROCK=false
python app.py
```

## 📊 Testing the Setup

### 1. Verify Flask API
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/fips
```

### 2. Test Bedrock Mock Service
```bash
curl -X POST http://localhost:5000/api/fips/predict \
  -H "Content-Type: application/json" \
  -d '{"fips": ["sbi-fip", "hdfc-fip"]}'
```

### 3. Push Mock Metrics to Prometheus
```bash
curl -X POST http://localhost:5000/api/metrics/push
```

### 4. Check Prometheus Metrics
```bash
# If Prometheus is running
curl 'http://localhost:9090/api/v1/query?query=fip_consent_success_rate'
```

## 🎯 Demo Scenarios

### Scenario 1: Healthy Operations
```bash
# All FIPs show good performance
curl http://localhost:5000/api/fips/health
```

### Scenario 2: FIP Degradation
```bash
# Simulate HDFC degradation
curl -X POST http://localhost:5000/api/fips/predict \
  -H "Content-Type: application/json" \
  -d '{"fips": ["hdfc-fip"], "time_horizon": "2h"}'
```

### Scenario 3: Business Impact Analysis
```bash
# Get business impact of current issues
curl -X POST http://localhost:5000/api/operations/impact \
  -H "Content-Type: application/json" \
  -d '{"predictions": {}}'
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Bedrock Configuration
USE_REAL_BEDROCK=false          # Set to true when you have Bedrock access
BEDROCK_REGION=us-east-1        # AWS region
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Metrics Configuration
METRICS_UPDATE_INTERVAL=120     # Update every 2 minutes
PREDICTIONS_UPDATE_INTERVAL=900 # Predict every 15 minutes

# Simulation Configuration
SIMULATION_MODE=realistic       # realistic | demo | stress-test
ENABLE_DEGRADATION_SIMULATION=true
```

### Switching to Real Bedrock
```bash
# 1. Set environment variables
export USE_REAL_BEDROCK=true
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# 2. Restart the application
python app.py
```

## 📈 Monitoring & Observability

### Prometheus Queries
```promql
# FIP success rates
fip_consent_success_rate

# FIPs with low success rates
fip_consent_success_rate < 70

# Average response times
avg(fip_avg_response_time_seconds) by (fip_name)

# Critical FIPs
fip_status == 0
```

### Grafana Dashboard
- Import the provided dashboard JSON
- Connect to Prometheus datasource
- Monitor real-time FIP metrics

## 🚨 Troubleshooting

### Common Issues

1. **Port 5000 already in use**
```bash
# Find and kill process
lsof -ti:5000 | xargs kill -9

# Or use different port
export FLASK_RUN_PORT=5001
python app.py
```

2. **Database connection issues**
```bash
# Reset database
rm aa_gateway.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

3. **Prometheus connection failed**
```bash
# Check if Prometheus is running
curl http://localhost:9090/-/healthy

# Start Prometheus if not running
./prometheus --config.file=prometheus.yml
```

4. **Bedrock mock not working**
```bash
# Check environment variable
echo $USE_REAL_BEDROCK

# Should show 'false' for mock mode
export USE_REAL_BEDROCK=false
```

### Debug Mode
```bash
# Enable detailed logging
export FLASK_DEBUG=true
export FLASK_ENV=development
python app.py
```

## 🎥 Demo Preparation

### Before the Demo
1. Start all services: `python run.py docker`
2. Wait 2 minutes for metrics to populate
3. Open dashboard: http://localhost:5000
4. Verify all FIPs are showing data
5. Test prediction API
6. Prepare demo scenarios

### Demo Flow
1. **Overview**: Show dashboard with all FIPs
2. **Healthy State**: Point to green FIPs (SBI, ICICI)
3. **Problem Detection**: Highlight AXIS-FIP critical state
4. **AI Prediction**: Show HDFC degradation prediction
5. **Business Impact**: Display cost and user impact
6. **Recommendations**: Show AI-generated actions
7. **Real-time**: Refresh to show live updates

### Backup Plans
- **Plan A**: Full Docker setup with Prometheus
- **Plan B**: Flask only with mock data
- **Plan C**: Static screenshots with manual demo

## 📦 Project Structure
```
aa-gateway-ai-operations/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration
├── docker-compose.yml    # Docker services
├── Dockerfile            # Flask app container
├── prometheus.yml        # Prometheus configuration
├── fip_alert_rules.yml   # Prometheus alerts
├── run.py                # Production runner
├── services/
│   ├── bedrock_service.py    # AI service with mock
│   ├── metrics_service.py    # FIP metrics management
│   ├── prometheus_service.py # Prometheus integration
│   └── data_pipeline.py      # Data processing pipeline
├── models/
│   └── predictions.py        # Database models
├── utils/
│   └── helpers.py           # Utility functions
├── config.py             # Configuration management
├── data/                 # SQLite database storage
└── README.md            # Documentation
```

## 🏆 Success Metrics

### Technical Metrics
- ✅ Flask API responding (< 200ms)
- ✅ Mock Bedrock generating realistic predictions
- ✅ Prometheus metrics being pushed
- ✅ Database storing predictions
- ✅ Background tasks running

### Demo Metrics
- ✅ Dashboard loads instantly
- ✅ FIP selection works smoothly
- ✅ AI predictions appear realistic
- ✅ Business impact calculations
- ✅ Real-time updates working

### Business Metrics
- ✅ Clear ROI demonstration
- ✅ Operational value evident
- ✅ AWS Bedrock integration showcased
- ✅ Scalable architecture presented
- ✅ Production-ready implementation
