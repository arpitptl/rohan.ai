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
  alerts: {
    // Get all proactive alerts
    getProactiveAlerts: async () => {
      try {
        const response = await api.get('/api/alerts/proactive');
        return {
          success: true,
          data: response.data.data,
          timestamp: response.data.timestamp
        };
      } catch (error) {
        console.error('Error fetching alerts:', error);
        return {
          success: false,
          error: error.message,
          data: {
            alerts: [],
            summary: {
              critical_alerts: 0,
              warning_alerts: 0,
              info_alerts: 0,
              total_alerts: 0,
              affected_fips: 0
            }
          }
        };
      }
    },

    // Get alert details by ID
    getAlertDetails: async (alertId) => {
      try {
        const response = await api.get(`/api/alerts/${alertId}`);
        return {
          success: true,
          data: response.data.data
        };
      } catch (error) {
        console.error('Error fetching alert details:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    // Send alert to all webhooks
    notifyWebhooks: async (alertId) => {
      try {
        const response = await api.post(`/api/alerts/${alertId}/notify`);
        return {
          success: true,
          message: response.data.message
        };
      } catch (error) {
        console.error('Error sending alert to webhooks:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    // Mark alert as resolved
    resolveAlert: async (alertId, resolution) => {
      try {
        const response = await api.post(`/api/alerts/${alertId}/resolve`, { resolution });
        return {
          success: true,
          data: response.data.data
        };
      } catch (error) {
        console.error('Error resolving alert:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    // Get alert history for a FIP
    getFipAlertHistory: async (fipName, timeRange = '24h') => {
      try {
        const response = await api.get(`/api/alerts/history/${fipName}`, {
          params: { timeRange }
        });
        return {
          success: true,
          data: response.data.data
        };
      } catch (error) {
        console.error('Error fetching alert history:', error);
        return {
          success: false,
          error: error.message,
          data: []
        };
      }
    },

    // Get alert trends and statistics
    getAlertTrends: async (timeRange = '24h') => {
      try {
        const response = await api.get('/api/alerts/trends', {
          params: { timeRange }
        });
        return {
          success: true,
          data: response.data.data
        };
      } catch (error) {
        console.error('Error fetching alert trends:', error);
        return {
          success: false,
          error: error.message,
          data: {
            common_issues: [],
            peak_hours: [],
            resolution_times: {}
          }
        };
      }
    }
  },
  
  // System overview
  getSystemOverview: () => api.get('/api/system/overview'),
  
  // Metrics
  pushMetrics: () => api.post('/api/metrics/push'),

  webhooks: {
    // Get all webhook subscriptions
    getSubscriptions: async () => {
      try {
        const response = await api.get('/api/webhooks');
        return {
          success: true,
          data: response.data.data
        };
      } catch (error) {
        console.error('Error fetching webhook subscriptions:', error);
        return {
          success: false,
          error: error.message,
          data: []
        };
      }
    },

    // Create new webhook subscription
    createSubscription: async (subscription) => {
      try {
        const response = await api.post('/api/webhooks', subscription);
        return {
          success: true,
          data: response.data.data,
          message: response.data.message
        };
      } catch (error) {
        console.error('Error creating webhook subscription:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    // Update webhook subscription
    updateSubscription: async (id, subscription) => {
      try {
        const response = await api.put(`/api/webhooks/${id}`, subscription);
        return {
          success: true,
          data: response.data.data,
          message: response.data.message
        };
      } catch (error) {
        console.error('Error updating webhook subscription:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    // Delete webhook subscription
    deleteSubscription: async (id) => {
      try {
        const response = await api.delete(`/api/webhooks/${id}`);
        return {
          success: true,
          message: response.data.message
        };
      } catch (error) {
        console.error('Error deleting webhook subscription:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    // Test webhook
    testWebhook: async (webhookData) => {
      try {
        const response = await api.post('/api/webhooks/test', webhookData);
        return {
          success: true,
          data: response.data,
          message: response.data.message
        };
      } catch (error) {
        console.error('Error testing webhook:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    // Test all webhooks
    testAllWebhooks: async () => {
      try {
        const response = await api.post('/api/webhooks/test-all');
        return {
          success: true,
          message: response.data.message
        };
      } catch (error) {
        console.error('Error testing all webhooks:', error);
        return {
          success: false,
          error: error.message
        };
      }
    }
  }
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
