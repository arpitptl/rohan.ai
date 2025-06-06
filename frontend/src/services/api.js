import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health check
  getHealth: () => api.get('/api/health'),
  
  // FIP management
  getFips: () => api.get('/api/fips'),
  getFipsHealth: () => api.get('/api/fips/health'),
  
  // Predictions
  predictFipIssues: (data) => api.post('/api/fips/predict', data),
  
  // Business impact
  getBusinessImpact: (data) => api.post('/api/operations/impact', data),
  
  // Alerts
  getProactiveAlerts: () => api.get('/api/alerts/proactive'),
  
  // System overview
  getSystemOverview: () => api.get('/api/system/overview'),
  
  // Metrics
  pushMetrics: () => api.post('/api/metrics/push'),
};

// FIP Action Endpoints
export const activateFallback = async (fipId) => {
  return axios.post(`${API_BASE_URL}/api/fips/${fipId}/fallback`);
};

export const alertTeam = async (fipId, severity) => {
  return axios.post(`${API_BASE_URL}/api/fips/${fipId}/alert`, { severity });
};

export const prepareBackup = async (fipId) => {
  return axios.post(`${API_BASE_URL}/api/fips/${fipId}/backup`);
};

export const notifyUsers = async (fipId, message) => {
  return axios.post(`${API_BASE_URL}/api/fips/${fipId}/notify`, { message });
};

export default api;
