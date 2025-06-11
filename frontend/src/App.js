import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Users, 
  BarChart3, 
  Brain, 
  RefreshCw,
  Zap,
  TrendingUp,
  TrendingDown,
  Menu,
  X,
  Home,
  Settings,
  History,
  Bell,
  ChevronLeft,
  ChevronRight,
  Calendar,
  } from 'lucide-react';

  import { 
    Plus,
    Edit,
    Trash2,
    TestTube,
    Save,
    Globe,
    Link,
    Copy,
    Check
  } from 'lucide-react';
  
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import Loading from './components/common/Loading';
import StatusBadge from './components/common/StatusBadge';
import { apiService } from './services/api';
import { formatPercentage, prependZero } from './utils/helpers';
import { PER_USER_COST } from './constant';

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fipsData, setFipsData] = useState({});
  const [impactSummary, setImpactSummary] = useState({usersAtRisk: 0, highRiskFips: 0, potentialCostImpact: 0});
  const [systemOverview, setSystemOverview] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [activeTab, setActiveTab] = useState('predictions');
  const [selectedFipsForPrediction, setSelectedFipsForPrediction] = useState([]);
  const [predictionsData, setPredictionsData] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [patternsData, setPatternsData] = useState({});
  const [hourlyMaintenence, setHourlyMaintenence] = useState([])

  // Fetch data on component mount
  useEffect(() => {
    fetchDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [fipsResponse, overviewResponse, predictionsResponse, hourlyPredictionsData] = await Promise.all([
        apiService.getFips(),
        apiService.getSystemOverview(),
        apiService.predictFipIssues({ fips: Object.keys(fipsData), time_horizon: '24h' }),
        apiService.getHourlyPrediction({})
      ]);

      setFipsData(fipsResponse.data.data);
      setSystemOverview(overviewResponse.data.data);
      setPatternsData(predictionsResponse.data?.data || {});
      setHourlyMaintenence(getMainteneceFips(hourlyPredictionsData.data?.data || []))
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData();
  };

  const generatePredictions = async (selectedFips) => {
    try {
      const response = await apiService.predictFipIssues({ fips: selectedFips });
      
      // Create success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-up';
      notification.innerHTML = `✅ AI Predictions generated for ${selectedFips.length} FIPs!`;
      document.body.appendChild(notification);
      
      setTimeout(() => notification.remove(), 3000);
    } catch (err) {
      console.error('Error generating predictions:', err);
      
      // Create error notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = '❌ Failed to generate predictions';
      document.body.appendChild(notification);
      
      setTimeout(() => notification.remove(), 3000);
    }
  };
  useEffect(() => {
    async function fetchData() {
      const response = await apiService.predictFipIssues({});
      const prediction = response.data.data;

      const summary = Object.keys(prediction)
      .reduce((acc, fip) => {
        const prediction_fip = prediction[fip];
        const affectedUsers = prediction_fip.user_impact.estimated_affected_users || 0;
        const isHighRisk = prediction_fip.downtime_prediction.probability > 0.7;
        
        acc.usersAtRisk += affectedUsers;
        acc.highRiskFips += isHighRisk ? 1 : 0;
        acc.potentialCostImpact += affectedUsers * PER_USER_COST;
        return acc;
      }, {usersAtRisk: 0, highRiskFips: 0, potentialCostImpact: 0});
      
      setImpactSummary(summary);
    }
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'analytics') {
      // Generate predictions for all FIPs when analytics tab is opened
      const generatePredictionsForAll = async () => {
        try {
          const allFips = Object.keys(fipsData);
          const response = await apiService.predictFipIssues({ fips: allFips, time_horizon: '24h' });
          if (response.data?.data) {
            setPredictionsData(response.data.data);
          }
        } catch (error) {
          console.error('Error generating predictions:', error);
        }
      };
      generatePredictionsForAll();
    }

    setSelectedFipsForPrediction([]) // Reset for new tab
  }, [activeTab, fipsData]);

  const getMainteneceFips = (hourlyMaintenenceData) => {
    const predictedMaintenance = [];

    hourlyMaintenenceData.forEach((hourData) => {
      const hour = hourData.hour;
      const predictions = hourData.predictions;

      const maintenanceFips = Object.entries(predictions)
        .filter(([_, prediction]) => prediction.isMaintenence)
        .map(([fipName, prediction]) => ({
          fip: fipName,
          timeWindow: prediction.timeWindow
        }));

      if (maintenanceFips.length > 0) {
        predictedMaintenance.push({
          hour,
          prediction: maintenanceFips
        });
      }
    });
  
    return predictedMaintenance;
  };
  const fetchMainteneceFips = () => {
    const hourlyPredictionsData = apiService.getHourlyPrediction({})
    setHourlyMaintenence(getMainteneceFips(hourlyPredictionsData.data?.data || []))
  }

  if (loading && Object.keys(fipsData).length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading text="Loading AA Gateway Dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Error Loading Dashboard</h2>
          <p className="text-slate-400 mb-4">{error}</p>
          <button onClick={handleRefresh} className="btn-primary">
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const healthyFips = Object.values(fipsData).filter(fip => fip.current_status === 'healthy').length;
  const degradedFips = Object.values(fipsData).filter(fip => fip.current_status === 'degraded').length;
  const criticalFips = Object.values(fipsData).filter(fip => fip.current_status === 'critical').length;
  const totalFips = Object.keys(fipsData).length;


  // Prepare chart data
  const chartData = Object.entries(fipsData).map(([fipId, fip]) => ({
    name: fip.bank_name.split(' ')[0],
    consent: parseFloat(fip.consent_success_rate),
    dataFetch: parseFloat(fip.data_fetch_success_rate),
    responseTime: parseFloat(fip.avg_response_time),
    errorRate: parseFloat(fip.error_rate),
    fullName: fip.bank_name
  }));

  const statusData = [
    { name: 'Healthy', value: healthyFips, color: '#10b981' },
    { name: 'Degraded', value: degradedFips, color: '#f59e0b' },
    { name: 'Critical', value: criticalFips, color: '#ef4444' }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-white mb-2">{payload[0]?.payload?.fullName || label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
              {entry.name.includes('Rate') || entry.name.includes('consent') || entry.name.includes('dataFetch') ? '%' : 
               entry.name.includes('Time') ? 's' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const AlertsTab = ({ apiService, activeTab }) => {
    const [alertsData, setAlertsData] = useState({ alerts: [], summary: { total_alerts: 0, critical_alerts: 0, warning_alerts: 0, info_alerts: 0, affected_fips: 0 } });
    const [selectedAlert, setSelectedAlert] = useState(null);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState({
      severity: 'all',
      fip: 'all',
      type: 'all'
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [showDetails, setShowDetails] = useState(false);
  
    // Fetch alerts only when alerts tab is active
    useEffect(() => {
      if (activeTab === 'alerts') {
        fetchAlerts();
        
        // Set up polling only when tab is active
        const interval = setInterval(fetchAlerts, 60000); // Poll every 30 seconds
        
        // Cleanup interval when tab changes or component unmounts
        return () => clearInterval(interval);
      }
    }, [activeTab]);
  
    const fetchAlerts = async () => {
      if (!apiService) return;
      
      setLoading(true);
      try {
        const response = await apiService.alerts.getProactiveAlerts();
        if (response.success) {
          setAlertsData(response.data);
        }
      } catch (error) {
        console.error('Error fetching alerts:', error);
      } finally {
        setLoading(false);
      }
    };
  
    // Get severity icon and color
    const getSeverityIcon = (severity) => {
      switch (severity) {
        case 'critical':
          return <AlertTriangle className="w-5 h-5 text-red-400" />;
        case 'warning':
          return <Activity className="w-5 h-5 text-yellow-400" />;
        case 'info':
          return <CheckCircle className="w-5 h-5 text-blue-400" />;
        default:
          return <Bell className="w-5 h-5 text-slate-400" />;
      }
    };
  
    const getSeverityColor = (severity) => {
      switch (severity) {
        case 'critical':
          return 'border-red-500/30 bg-red-500/10';
        case 'warning':
          return 'border-yellow-500/30 bg-yellow-500/10';
        case 'info':
          return 'border-blue-500/30 bg-blue-500/10';
        default:
          return 'border-slate-500/30 bg-slate-500/10';
      }
    };
  
    const getAlertTypeIcon = (type) => {
      switch (type) {
        case 'consent_success_rate':
          return <Users className="w-4 h-4" />;
        case 'data_fetch_success_rate':
          return <BarChart3 className="w-4 h-4" />;
        case 'response_time':
          return <Clock className="w-4 h-4" />;
        default:
          return <Activity className="w-4 h-4" />;
      }
    };
  
    // Filter alerts based on filters and search
    const filteredAlerts = alertsData.alerts.filter(alert => {
      const matchesSeverity = filters.severity === 'all' || alert.severity === filters.severity;
      const matchesFip = filters.fip === 'all' || alert.fip_name === filters.fip;
      const matchesType = filters.type === 'all' || alert.alert_type === filters.type;
      const matchesSearch = searchTerm === '' || 
        alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.fip_name.toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesSeverity && matchesFip && matchesType && matchesSearch;
    });
  
    // Get unique FIPs and alert types for filters
    const uniqueFips = [...new Set(alertsData.alerts.map(alert => alert.fip_name))];
    const uniqueTypes = [...new Set(alertsData.alerts.map(alert => alert.alert_type))];
  
    const formatTimestamp = (timestamp) => {
      return new Date(timestamp).toLocaleString();
    };
  
    const handleAlertClick = (alert) => {
      setSelectedAlert(alert);
      setShowDetails(true);
    };
  
    const closeDetails = () => {
      setShowDetails(false);
      setSelectedAlert(null);
    };
  
    const refreshAlerts = async () => {
      setLoading(true);
      try {
        await fetchAlerts();
      } catch (error) {
        console.error('Error refreshing alerts:', error);
      } finally {
        setLoading(false);
      }
    };
  
    return (
      <div className="animate-slide-up space-y-8">
        {/* Alert Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="glass-card rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Total Alerts</p>
                <p className="text-3xl font-bold text-white">{alertsData.summary.total_alerts}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <Bell className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
  
          <div className="glass-card rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Critical</p>
                <p className="text-3xl font-bold text-red-400">{alertsData.summary.critical_alerts}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-red-600 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
  
          <div className="glass-card rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Warnings</p>
                <p className="text-3xl font-bold text-yellow-400">{alertsData.summary.warning_alerts}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
  
          <div className="glass-card rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Affected FIPs</p>
                <p className="text-3xl font-bold text-white">{alertsData.summary.affected_fips}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        </div>
  
        {/* Filters and Search */}
        <div className="glass-card rounded-xl p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold text-white">Active Alerts</h2>
              <button
                onClick={refreshAlerts}
                className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
  
            <div className="flex flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search alerts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 text-sm w-64"
                />
              </div>
  
              {/* Severity Filter */}
              <select
                value={filters.severity}
                onChange={(e) => setFilters({...filters, severity: e.target.value})}
                className="px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>
  
              {/* FIP Filter */}
              <select
                value={filters.fip}
                onChange={(e) => setFilters({...filters, fip: e.target.value})}
                className="px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm"
              >
                <option value="all">All FIPs</option>
                {uniqueFips.map(fip => (
                  <option key={fip} value={fip}>{fip}</option>
                ))}
              </select>
  
              {/* Type Filter */}
              <select
                value={filters.type}
                onChange={(e) => setFilters({...filters, type: e.target.value})}
                className="px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm"
              >
                <option value="all">All Types</option>
                {uniqueTypes.map(type => (
                  <option key={type} value={type}>{type.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
          </div>
  
          {/* Alerts List */}
          <div className="space-y-4">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No Alerts Found</h3>
                <p className="text-slate-400">
                  {loading ? "Loading alerts..." : "No alerts match your current filters."}
                </p>
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  onClick={() => handleAlertClick(alert)}
                  className={`${getSeverityColor(alert.severity)} border rounded-xl p-6 hover:border-blue-500/40 transition-all duration-300 cursor-pointer hover:transform hover:-translate-y-1`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="flex items-center gap-2">
                        {getSeverityIcon(alert.severity)}
                        {getAlertTypeIcon(alert.alert_type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-white">{alert.fip_name.toUpperCase()}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium uppercase ${
                            alert.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                            alert.severity === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-blue-500/20 text-blue-400'
                          }`}>
                            {alert.severity}
                          </span>
                          <span className="text-xs text-slate-500">
                            Confidence: {(alert.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        
                        <p className="text-slate-300 mb-3">{alert.message}</p>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          <div className="bg-slate-800/50 rounded-lg p-3">
                            <p className="text-xs text-slate-400 mb-1">Current Rate</p>
                            <p className="text-lg font-semibold text-white">
                              {alert.metrics.current_rate.toFixed(1)}%
                            </p>
                          </div>
                          <div className="bg-slate-800/50 rounded-lg p-3">
                            <p className="text-xs text-slate-400 mb-1">Affected Users</p>
                            <p className="text-lg font-semibold text-white">
                              {alert.context.affected_users.toLocaleString()}
                            </p>
                          </div>
                          <div className="bg-slate-800/50 rounded-lg p-3">
                            <p className="text-xs text-slate-400 mb-1">Deviation</p>
                            <div className="flex items-center gap-1">
                              <TrendingDown className="w-4 h-4 text-red-400" />
                              <span className="text-lg font-semibold text-red-400">
                                {alert.metrics.deviation.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">
                            {formatTimestamp(alert.timestamp)}
                          </span>
                          <span className="text-slate-400">
                            Impact: {alert.context.business_impact}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
  
        {/* Alert Details Modal */}
        {showDetails && selectedAlert && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="glass-card rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    {getSeverityIcon(selectedAlert.severity)}
                    <h2 className="text-2xl font-bold text-white">
                      Alert Details - {selectedAlert.fip_name.toUpperCase()}
                    </h2>
                  </div>
                  <button
                    onClick={closeDetails}
                    className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-slate-400" />
                  </button>
                </div>
  
                {/* Alert Overview */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Alert Information</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Alert ID:</span>
                          <span className="text-white font-mono text-sm">{selectedAlert.alert_id}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Type:</span>
                          <span className="text-white">{selectedAlert.alert_type.replace('_', ' ')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Severity:</span>
                          <span className={`font-medium ${
                            selectedAlert.severity === 'critical' ? 'text-red-400' :
                            selectedAlert.severity === 'warning' ? 'text-yellow-400' :
                            'text-blue-400'
                          }`}>
                            {selectedAlert.severity.toUpperCase()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Confidence:</span>
                          <span className="text-white">{(selectedAlert.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Context</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Affected Users:</span>
                          <span className="text-white font-semibold">{selectedAlert.context.affected_users.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Business Impact:</span>
                          <span className="text-white">{selectedAlert.context.business_impact}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Historical Pattern:</span>
                          <span className="text-white">{selectedAlert.context.historical_pattern}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Time:</span>
                          <span className="text-white">{formatTimestamp(selectedAlert.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
  
                {/* Metrics Details */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-slate-400 text-sm mb-1">Current Rate</p>
                      <p className="text-2xl font-bold text-white">{selectedAlert.metrics.current_rate.toFixed(1)}%</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-slate-400 text-sm mb-1">Historical Average</p>
                      <p className="text-2xl font-bold text-white">{selectedAlert.metrics.historical_avg.toFixed(1)}%</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-slate-400 text-sm mb-1">Deviation</p>
                      <p className="text-2xl font-bold text-red-400">{selectedAlert.metrics.deviation.toFixed(1)}%</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-slate-400 text-sm mb-1">Threshold</p>
                      <p className="text-2xl font-bold text-yellow-400">{selectedAlert.metrics.threshold}%</p>
                    </div>
                  </div>
                </div>
  
                {/* Recommended Actions */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-white mb-4">Recommended Actions</h3>
                  <div className="space-y-3">
                    {selectedAlert.recommended_actions.map((action, index) => (
                      <div key={index} className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg">
                        <div className="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-blue-400 text-sm font-semibold">{index + 1}</span>
                        </div>
                        <p className="text-slate-300">{action}</p>
                      </div>
                    ))}
                  </div>
                </div>
  
             {/* Action Buttons */}
             <div className="flex items-center justify-end gap-3">
                <button
                  onClick={closeDetails}
                  className="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/70 border border-slate-600 text-white rounded-lg transition-colors"
                >
                  Close
                </button>
                <button 
                  onClick={async () => {
                    try {
                      // Send the complete alert data to the webhook endpoint
                      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/alerts/${selectedAlert.alert_id}/notify`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                          alert_id: selectedAlert.alert_id,
                          type: selectedAlert.alert_type,
                          severity: selectedAlert.severity,
                          fip_name: selectedAlert.fip_name,
                          message: selectedAlert.message,
                          metrics: selectedAlert.metrics,
                          context: selectedAlert.context,
                          timestamp: selectedAlert.timestamp,
                          recommended_actions: selectedAlert.recommended_actions,
                          confidence: selectedAlert.confidence
                        })
                      });

                      const result = await response.json();
                      
                      if (result.success) {
                        // Show success notification
                        const notification = document.createElement('div');
                        notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                        notification.innerHTML = '✅ Alert sent to webhook endpoints';
                        document.body.appendChild(notification);
                        setTimeout(() => notification.remove(), 3000);
                      } else {
                        throw new Error(result.error || 'Failed to send alert');
                      }
                    } catch (error) {
                      console.error('Error sending alert to webhooks:', error);
                      // Show error notification
                      const notification = document.createElement('div');
                      notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                      notification.innerHTML = `❌ Failed to send alert: ${error.message}`;
                      document.body.appendChild(notification);
                      setTimeout(() => notification.remove(), 3000);
                    }
                  }}
                  className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  Send to Webhooks
                </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const SettingsTab = ({ apiService }) => {
    const [webhooks, setWebhooks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [editingWebhook, setEditingWebhook] = useState(null);
    const [testingWebhook, setTestingWebhook] = useState(null);
    const [formData, setFormData] = useState({
      name: '',
      url: '',
      method: 'POST',
      headers: {},
      enabled: true,
      alertTypes: ['critical', 'warning', 'info']
    });
    const [showHeaders, setShowHeaders] = useState(false);
    const [headerKey, setHeaderKey] = useState('');
    const [headerValue, setHeaderValue] = useState('');
    const [copiedId, setCopiedId] = useState(null);
  
    useEffect(() => {
      fetchWebhooks();
    }, []);
  
    const fetchWebhooks = async () => {
      if (!apiService) return;
      
      setLoading(true);
      try {
        const response = await apiService.webhooks.getSubscriptions();
        if (response.success) {
          setWebhooks(response.data);
        }
      } catch (error) {
        console.error('Error fetching webhooks:', error);
        showNotification('❌ Failed to fetch webhooks', 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const showNotification = (message, type = 'success') => {
      const notification = document.createElement('div');
      notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 text-white ${
        type === 'success' ? 'bg-gradient-to-r from-green-500 to-green-600' :
        type === 'error' ? 'bg-gradient-to-r from-red-500 to-red-600' :
        'bg-gradient-to-r from-blue-500 to-blue-600'
      }`;
      notification.innerHTML = message;
      document.body.appendChild(notification);
      setTimeout(() => notification.remove(), 3000);
    };
  
    const resetForm = () => {
      setFormData({
        name: '',
        url: '',
        method: 'POST',
        headers: {},
        enabled: true,
        alertTypes: ['critical', 'warning', 'info']
      });
      setEditingWebhook(null);
    };
  
    const openCreateModal = () => {
      resetForm();
      setShowCreateModal(true);
    };
  
    const openEditModal = (webhook) => {
      setFormData({
        name: webhook.name,
        url: webhook.url,
        method: webhook.method,
        headers: webhook.headers || {},
        enabled: webhook.enabled,
        alertTypes: webhook.alertTypes || ['critical', 'warning', 'info']
      });
      setEditingWebhook(webhook);
      setShowCreateModal(true);
    };
  
    const closeModal = () => {
      setShowCreateModal(false);
      setEditingWebhook(null);
      resetForm();
    };
  
    const addHeader = () => {
      if (headerKey && headerValue) {
        setFormData({
          ...formData,
          headers: {
            ...formData.headers,
            [headerKey]: headerValue
          }
        });
        setHeaderKey('');
        setHeaderValue('');
      }
    };
  
    const removeHeader = (key) => {
      const newHeaders = { ...formData.headers };
      delete newHeaders[key];
      setFormData({ ...formData, headers: newHeaders });
    };
  
    const handleAlertTypeChange = (type) => {
      const newAlertTypes = formData.alertTypes.includes(type)
        ? formData.alertTypes.filter(t => t !== type)
        : [...formData.alertTypes, type];
      setFormData({ ...formData, alertTypes: newAlertTypes });
    };
  
    const handleSubmit = async () => {
      if (!formData.name || !formData.url) {
        showNotification('❌ Please fill in all required fields', 'error');
        return;
      }
  
      setLoading(true);
      try {
        let response;
        if (editingWebhook) {
          response = await apiService.webhooks.updateSubscription(editingWebhook.id, formData);
        } else {
          response = await apiService.webhooks.createSubscription(formData);
        }
  
        if (response.success) {
          showNotification(`✅ Webhook ${editingWebhook ? 'updated' : 'created'} successfully`);
          await fetchWebhooks();
          closeModal();
        } else {
          throw new Error(response.error);
        }
      } catch (error) {
        console.error('Error saving webhook:', error);
        showNotification(`❌ Failed to ${editingWebhook ? 'update' : 'create'} webhook`, 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const handleDelete = async (webhookId) => {
      // eslint-disable-next-line no-restricted-globals
      if (!window.confirm('Are you sure you want to delete this webhook?')) return;
  
      setLoading(true);
      try {
        const response = await apiService.webhooks.deleteSubscription(webhookId);
        if (response.success) {
          showNotification('✅ Webhook deleted successfully');
          await fetchWebhooks();
        } else {
          throw new Error(response.error);
        }
      } catch (error) {
        console.error('Error deleting webhook:', error);
        showNotification('❌ Failed to delete webhook', 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const testWebhook = async (webhook) => {
      setTestingWebhook(webhook.id);
      try {
        const response = await apiService.webhooks.testWebhook({
          url: webhook.url,
          method: webhook.method,
          headers: webhook.headers
        });
        
        if (response.success) {
          showNotification('✅ Test notification sent successfully');
        } else {
          throw new Error(response.error);
        }
      } catch (error) {
        console.error('Error testing webhook:', error);
        showNotification('❌ Failed to send test notification', 'error');
      } finally {
        setTestingWebhook(null);
      }
    };
  
    const testAllWebhooks = async () => {
      setLoading(true);
      try {
        const response = await apiService.webhooks.testAllWebhooks();
        if (response.success) {
          showNotification('✅ Test alerts sent to all enabled webhooks');
        } else {
          throw new Error(response.error);
        }
      } catch (error) {
        console.error('Error testing all webhooks:', error);
        showNotification('❌ Failed to test all webhooks', 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const copyToClipboard = (text, id) => {
      navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    };
  
    const getStatusColor = (enabled) => {
      return enabled ? 'text-green-400' : 'text-slate-400';
    };
  
    const getMethodColor = (method) => {
      switch (method) {
        case 'POST': return 'bg-blue-500/20 text-blue-400';
        case 'PUT': return 'bg-yellow-500/20 text-yellow-400';
        case 'PATCH': return 'bg-purple-500/20 text-purple-400';
        default: return 'bg-slate-500/20 text-slate-400';
      }
    };
  
    return (
      <div className="animate-slide-up space-y-8">
        {/* Settings Header */}
        <div className="glass-card rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Settings className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">Settings</h2>
                <p className="text-slate-400">Manage your webhook endpoints and notification preferences</p>
              </div>
            </div>
            <button
              onClick={fetchWebhooks}
              className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
              disabled={loading}
            >
              <RefreshCw className={`w-5 h-5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
  
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <Globe className="w-8 h-8 text-blue-400" />
                <div>
                  <p className="text-slate-400 text-sm">Total Webhooks</p>
                  <p className="text-2xl font-bold text-white">{webhooks.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-8 h-8 text-green-400" />
                <div>
                  <p className="text-slate-400 text-sm">Active Endpoints</p>
                  <p className="text-2xl font-bold text-white">{webhooks.filter(w => w.enabled).length}</p>
                </div>
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <Bell className="w-8 h-8 text-yellow-400" />
                <div>
                  <p className="text-slate-400 text-sm">Alert Types</p>
                  <p className="text-2xl font-bold text-white">3</p>
                </div>
              </div>
            </div>
          </div>
        </div>
  
        {/* Webhook Management */}
        <div className="glass-card rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">Webhook Endpoints</h3>
            <div className="flex gap-3">
              <button
                onClick={testAllWebhooks}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-600/70 border border-slate-600 text-white rounded-lg transition-colors"
                disabled={loading || webhooks.length === 0}
              >
                <TestTube className="w-4 h-4" />
                Test All
              </button>
              <button
                onClick={openCreateModal}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <Plus className="w-4 h-4" />
                Add Webhook
              </button>
            </div>
          </div>
  
          {/* Webhooks List */}
          {webhooks.length === 0 ? (
            <div className="text-center py-12">
              <Globe className="w-16 h-16 text-slate-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No Webhooks Configured</h3>
              <p className="text-slate-400 mb-4">Add your first webhook endpoint to start receiving alerts</p>
              <button
                onClick={openCreateModal}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 text-white rounded-lg transition-all duration-200"
              >
                <Plus className="w-4 h-4 inline mr-2" />
                Add Your First Webhook
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {webhooks.map((webhook) => (
                <div key={webhook.id} className="glass-light rounded-xl p-6 hover:border-blue-500/40 transition-all duration-300">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="text-lg font-semibold text-white">{webhook.name}</h4>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getMethodColor(webhook.method)}`}>
                          {webhook.method}
                        </span>
                        <div className="flex items-center gap-1">
                          <Activity className={`w-4 h-4 ${getStatusColor(webhook.enabled)}`} />
                          <span className={`text-sm font-medium ${getStatusColor(webhook.enabled)}`}>
                            {webhook.enabled ? 'Active' : 'Disabled'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 mb-3">
                        <Link className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-300 font-mono text-sm flex-1">{webhook.url}</span>
                        <button
                          onClick={() => copyToClipboard(webhook.url, webhook.id)}
                          className="p-1 hover:bg-slate-700/50 rounded transition-colors"
                        >
                          {copiedId === webhook.id ? (
                            <Check className="w-4 h-4 text-green-400" />
                          ) : (
                            <Copy className="w-4 h-4 text-slate-400" />
                          )}
                        </button>
                      </div>
  
                      <div className="flex items-center gap-4 mb-3">
                        <div>
                          <span className="text-slate-400 text-sm">Alert Types: </span>
                          <div className="inline-flex gap-1">
                            {webhook.alertTypes?.map((type) => (
                              <span key={type} className={`px-2 py-1 rounded text-xs font-medium ${
                                type === 'critical' ? 'bg-red-500/20 text-red-400' :
                                type === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                                'bg-blue-500/20 text-blue-400'
                              }`}>
                                {type}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
  
                      {Object.keys(webhook.headers || {}).length > 0 && (
                        <div className="mb-3">
                          <span className="text-slate-400 text-sm">Headers: </span>
                          <span className="text-slate-300 text-sm">{Object.keys(webhook.headers).length} custom headers</span>
                        </div>
                      )}
  
                      <div className="text-xs text-slate-500">
                        Created: {new Date(webhook.createdAt).toLocaleString()}
                        {webhook.updatedAt !== webhook.createdAt && (
                          <span className="ml-4">Updated: {new Date(webhook.updatedAt).toLocaleString()}</span>
                        )}
                      </div>
                    </div>
  
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => testWebhook(webhook)}
                        disabled={testingWebhook === webhook.id}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors text-blue-400 hover:text-blue-300"
                        title="Test webhook"
                      >
                        <TestTube className={`w-4 h-4 ${testingWebhook === webhook.id ? 'animate-pulse' : ''}`} />
                      </button>
                      <button
                        onClick={() => openEditModal(webhook)}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors text-yellow-400 hover:text-yellow-300"
                        title="Edit webhook"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(webhook.id)}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors text-red-400 hover:text-red-300"
                        title="Delete webhook"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
  
        {/* Create/Edit Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="glass-card rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">
                    {editingWebhook ? 'Edit Webhook' : 'Add New Webhook'}
                  </h2>
                  <button
                    onClick={closeModal}
                    className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-slate-400" />
                  </button>
                </div>
  
                <div className="space-y-6">
                  {/* Basic Information */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Webhook Name *
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({...formData, name: e.target.value})}
                        placeholder="My Slack Webhook"
                        className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        HTTP Method
                      </label>
                      <select
                        value={formData.method}
                        onChange={(e) => setFormData({...formData, method: e.target.value})}
                        className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="PATCH">PATCH</option>
                      </select>
                    </div>
                  </div>
  
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Webhook URL *
                    </label>
                    <input
                      type="url"
                      value={formData.url}
                      onChange={(e) => setFormData({...formData, url: e.target.value})}
                      placeholder="https://hooks.slack.com/services/..."
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
  
                  {/* Alert Types */}
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Alert Types to Receive
                    </label>
                    <div className="flex gap-3">
                      {['critical', 'warning', 'info'].map((type) => (
                        <label key={type} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.alertTypes.includes(type)}
                            onChange={() => handleAlertTypeChange(type)}
                            className="rounded border-slate-600 bg-slate-700/50 text-blue-500 focus:ring-blue-500"
                          />
                          <span className={`text-sm font-medium ${
                            type === 'critical' ? 'text-red-400' :
                            type === 'warning' ? 'text-yellow-400' :
                            'text-blue-400'
                          }`}>
                            {type.charAt(0).toUpperCase() + type.slice(1)}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
  
                  {/* Headers Section */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label className="block text-sm font-medium text-slate-300">
                        Custom Headers
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowHeaders(!showHeaders)}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        {showHeaders ? 'Hide' : 'Add'} Headers
                      </button>
                    </div>
  
                    {showHeaders && (
                      <div className="space-y-3 p-4 bg-slate-800/50 rounded-lg">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <input
                            type="text"
                            value={headerKey}
                            onChange={(e) => setHeaderKey(e.target.value)}
                            placeholder="Header key (e.g., Authorization)"
                            className="px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={headerValue}
                              onChange={(e) => setHeaderValue(e.target.value)}
                              placeholder="Header value"
                              className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                              type="button"
                              onClick={addHeader}
                              disabled={!headerKey || !headerValue}
                              className="px-3 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                            >
                              <Plus className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
  
                        {Object.keys(formData.headers).length > 0 && (
                          <div className="space-y-2">
                            <p className="text-sm text-slate-400">Current Headers:</p>
                            {Object.entries(formData.headers).map(([key, value]) => (
                              <div key={key} className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                                <span className="text-sm text-slate-300">
                                  <strong>{key}:</strong> {value}
                                </span>
                                <button
                                  type="button"
                                  onClick={() => removeHeader(key)}
                                  className="text-red-400 hover:text-red-300"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
  
                  {/* Enable/Disable */}
                  <div>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.enabled}
                        onChange={(e) => setFormData({...formData, enabled: e.target.checked})}
                        className="rounded border-slate-600 bg-slate-700/50 text-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-slate-300">
                        Enable this webhook
                      </span>
                    </label>
                  </div>
  
                  {/* Form Actions */}
                  <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-700/50">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/70 border border-slate-600 text-white rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSubmit}
                      disabled={loading}
                      className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 disabled:from-slate-600 disabled:to-slate-700 text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2"
                    >
                      {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
                      <Save className="w-4 h-4" />
                      {editingWebhook ? 'Update' : 'Create'} Webhook
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-900" style={{background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)'}}>
      {/* Collapsible Sidebar */}
      <div className={`fixed left-0 top-0 h-full z-50 transition-all duration-300 ${sidebarOpen ? 'w-64' : 'w-20'}`}>
        <div className="h-full glass-header border-r border-slate-700/50 p-4">
          {/* Sidebar Header */}
          <div className="flex items-center justify-between mb-8">
            {sidebarOpen ? (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-700 rounded-xl flex items-center justify-center">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-white">AA Gateway</h1>
                  <p className="text-xs text-slate-400">AI Operations</p>
                </div>
              </div>
            ) : (
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-700 rounded-xl flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
            )}
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
            >
              {sidebarOpen ? <ChevronLeft className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
            </button>
          </div>

          {/* Navigation Links */}
          <div className="space-y-2">
            {[
              { icon: Brain, label: 'AI Predictions', id: 'predictions' },
              { icon: Home, label: 'AI Overview', id: 'overview' },
              { icon: BarChart3, label: 'Analytics', id: 'analytics' },
              { icon: Bell, label: 'Alerts', id: 'alerts', count: criticalFips + degradedFips },
              { icon: History, label: 'History', id: 'history' },
              { icon: Settings, label: 'Settings', id: 'settings' },
              // { icon: FileText, label: 'Reports', id: 'reports' },
              // { icon: Shield, label: 'Security', id: 'security' },
              // { icon: Settings, label: 'Settings', id: 'settings' },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    activeTab === item.id 
                      ? 'bg-blue-500/20 text-blue-400 font-medium' 
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {sidebarOpen && (
                    <span className="flex-1 text-left">{item.label}</span>
                  )}
                  {sidebarOpen && item.count && (
                    <span className="px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs font-medium">
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Help & Support */}
          {/* {sidebarOpen && (
            <div className="absolute bottom-4 left-4 right-4">
              <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-white transition-all duration-200">
                <HelpCircle className="w-5 h-5" />
                <span>Help & Support</span>
              </button>
            </div>
          )} */}
        </div>
      </div>

      {/* Main Content - Adjust margin based on sidebar */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        {/* Header */}
        <header className="glass-header sticky top-0 z-50 border-b border-slate-700/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              {/* Logo Section */}
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-700 rounded-xl flex items-center justify-center shadow-lg">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">AA Gateway</h1>
                  <p className="text-sm text-slate-400">AI Operations Dashboard</p>
                </div>
              </div>

              {/* Status & Actions */}
              <div className="flex items-center gap-6">
                {/* Live Indicator */}
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>Live</span>
                  <span>•</span>
                  <span>{lastUpdated.toLocaleTimeString()}</span>
                </div>

                {/* Action Buttons - FIXED STYLING */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleRefresh}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-600/70 border border-slate-600 hover:border-slate-500 text-white rounded-lg text-sm font-medium transition-all duration-200 backdrop-blur-sm"
                    disabled={loading}
                  >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    <span className="hidden sm:inline">{loading ? 'Refreshing...' : 'Refresh'}</span>
                  </button>
                  <button
                    onClick={async () => {
                      setActiveTab('predictions');
                      const allFips = Object.keys(fipsData);
                      try {
                        await generatePredictions(allFips);
                        const notification = document.createElement('div');
                        notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                        notification.innerHTML = '✅ Generated predictions for all FIPs';
                        document.body.appendChild(notification);
                        setTimeout(() => notification.remove(), 3000);
                      } catch (error) {
                        const notification = document.createElement('div');
                        notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                        notification.innerHTML = '❌ Failed to generate predictions';
                        document.body.appendChild(notification);
                        setTimeout(() => notification.remove(), 3000);
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-700 hover:from-purple-600 hover:to-purple-800 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    <Brain className="w-4 h-4" />
                    <span className="hidden sm:inline">Generate AI Predictions</span>
                    <span className="sm:hidden">AI Predict</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Quick Action Floating Button */}
        <div className="fixed right-6 bottom-6 z-40">
          <div className="relative">
            <button
              onClick={() => setShowQuickActions(!showQuickActions)}
              className="w-14 h-14 bg-gradient-to-r from-blue-500 to-blue-700 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-200"
            >
              {showQuickActions ? (
                <X className="w-6 h-6 text-white" />
              ) : (
                <Menu className="w-6 h-6 text-white" />
              )}
            </button>

            {/* Quick Actions Menu */}
            {showQuickActions && (
              <div className="absolute bottom-16 right-0 w-64 glass-card rounded-xl p-2 animate-fade-in">
                <div className="space-y-1">
                  <button
                    onClick={() => {
                      setActiveTab('predictions');
                      generatePredictions(Object.keys(fipsData));
                    }}
                    className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-700/50 hover:text-white transition-all duration-200"
                  >
                    <Brain className="w-4 h-4" />
                    <span>Generate All Predictions</span>
                  </button>
                  <button
                    onClick={handleRefresh}
                    className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-700/50 hover:text-white transition-all duration-200"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Refresh Data</span>
                  </button>
                  <button
                    onClick={() => {
                      apiService.pushMetrics();
                    }}
                    className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-700/50 hover:text-white transition-all duration-200"
                  >
                    <BarChart3 className="w-4 h-4" />
                    <span>Push Metrics</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'overview' && (
            <div className="animate-slide-up space-y-8">
                {/* System Overview Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 animate-fade-in">
                  {/* System Health */}
                  <div className="metric-card">
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center shadow-lg">
                        <CheckCircle className="w-6 h-6 text-white" />
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 text-sm">System Health</p>
                        <p className="text-3xl font-bold text-white">
                          {systemOverview?.system_health_score || '7.2'}<span className="text-lg text-slate-500">/10</span>
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {systemOverview?.overall_status?.replace('_', ' ') || 'operational_with_issues'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center text-xs text-green-400">
                      <TrendingUp className="w-3 h-3 mr-1" />
                      +0.3 from yesterday
                    </div>
                  </div>

                  {/* Total FIPs */}
                  <div className="metric-card">
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg">
                        <Activity className="w-6 h-6 text-white" />
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 text-sm">Total FIPs</p>
                        <p className="text-3xl font-bold text-white">{totalFips}</p>
                        <div className="flex items-center gap-2 text-xs mt-1">
                          <span className="text-green-400">{healthyFips}✓</span>
                          <span className="text-yellow-400">{degradedFips}⚠</span>
                          <span className="text-red-400">{criticalFips}✗</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center text-xs text-yellow-400">
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      {degradedFips + criticalFips} need attention
                    </div>
                  </div>

                  {/* Success Rate */}
                  <div className="metric-card">
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                        <Users className="w-6 h-6 text-white" />
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 text-sm">Avg Success Rate</p>
                        <p className="text-3xl font-bold text-white">
                          {systemOverview?.performance_metrics?.average_consent_success 
                            ? formatPercentage(systemOverview.performance_metrics.average_consent_success)
                            : '78.4%'
                          }
                        </p>
                        <p className="text-xs text-slate-500 mt-1">Consent approvals</p>
                      </div>
                    </div>
                    <div className="flex items-center text-xs text-red-400">
                      <TrendingDown className="w-3 h-3 mr-1" />
                      -2.1% this hour
                    </div>
                  </div>

                  {/* System Availability */}
                  <div className="metric-card">
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center shadow-lg">
                        <Clock className="w-6 h-6 text-white" />
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 text-sm">System Availability</p>
                        <p className="text-3xl font-bold text-white">
                          {systemOverview?.performance_metrics?.system_availability 
                            ? formatPercentage(systemOverview.performance_metrics.system_availability)
                            : '86.7%'
                          }
                        </p>
                        <p className="text-xs text-slate-500 mt-1">Overall uptime</p>
                      </div>
                    </div>
                    <div className="flex items-center text-xs text-blue-400">
                      <Zap className="w-3 h-3 mr-1" />
                      Real-time monitoring
                    </div>
                  </div>
                </div>
              {/* Two Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* FIP Status Overview - Takes 3 columns */}
                <div className="lg:col-span-3">
                  <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-semibold text-white">FIP Status Overview</h2>
                      <button 
                        onClick={handleRefresh}
                        className="btn-refresh"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Refresh</span>
                      </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Existing FIP Status Cards */}
                      {Object.entries(fipsData)
                        .filter(([fipId]) => selectedFipsForPrediction.length === 0 || selectedFipsForPrediction.includes(fipId))
                        .map(([fipId, fip]) => (
                          <div key={fipId} className="glass-light rounded-xl p-6 hover:border-blue-500/40 transition-all duration-300">
                            <div className="flex items-center justify-between mb-4">
                              <div>
                                <h3 className="text-lg font-semibold text-white">{fip.bank_name}</h3>
                                <p className="text-sm text-slate-400">{fip.fip_name}</p>
                              </div>
                              <StatusBadge status={fip.current_status} />
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 mb-4">
                              <div>
                                <p className="text-sm text-slate-400">Consent Success</p>
                                <p className="text-xl font-bold text-white">
                                  {formatPercentage(fip.consent_success_rate)}
                                </p>
                                <div className="w-full bg-slate-700 rounded-full h-2 mt-1">
                                  <div 
                                    className="bg-blue-600 h-2 rounded-full" 
                                    style={{ width: `${Math.min(fip.consent_success_rate, 100)}%` }}
                                  ></div>
                                </div>
                              </div>
                              <div>
                                <p className="text-sm text-slate-400">Data Fetch Success</p>
                                <p className="text-xl font-bold text-white">
                                  {formatPercentage(fip.data_fetch_success_rate)}
                                </p>
                                <div className="w-full bg-slate-700 rounded-full h-2 mt-1">
                                  <div 
                                    className="bg-green-600 h-2 rounded-full" 
                                    style={{ width: `${Math.min(fip.data_fetch_success_rate, 100)}%` }}
                                  ></div>
                                </div>
                              </div>
                              <div>
                                <p className="text-sm text-slate-400">Response Time</p>
                                <p className="text-xl font-bold text-white">
                                  {fip.avg_response_time}s
                                </p>
                              </div>
                              <div>
                                <p className="text-sm text-slate-400">Error Rate</p>
                                <p className="text-xl font-bold text-white">
                                  {formatPercentage(fip.error_rate)}
                                </p>
                              </div>
                            </div>
                            
                            <div className="pt-4 border-t border-slate-700/50">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-slate-400">
                                  👥 {fip.user_base?.toLocaleString()} users
                                </span>
                                <span className={`font-medium ${
                                  fip.trend === 'stable' ? 'text-green-400' :
                                  fip.trend === 'declining' ? 'text-red-400' : 'text-slate-400'
                                }`}>
                                  {fip.trend === 'stable' ? '📈 Stable' :
                                   fip.trend === 'declining' ? '📉 Declining' :
                                   fip.trend === 'critical' ? '🚨 Critical' : '➡️ Stable'
                                  }
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>

                {/* Alerts & Insights Column - Takes 1 column */}
                <div className="lg:col-span-1 space-y-6">
                  {/* Critical Alerts */}
                  <div className="glass-card rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Critical Alerts</h3>
                    <div className="space-y-4">
                      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-red-400 text-sm font-medium mb-2">
                          <AlertTriangle className="w-4 h-4" />
                          AXIS-FIP Complete Outage
                        </div>
                        <p className="text-sm text-slate-300">System failure detected 45 minutes ago. 1,200+ users affected.</p>
                      </div>
                      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-yellow-400 text-sm font-medium mb-2">
                          <AlertTriangle className="w-4 h-4" />
                          HDFC-FIP Degradation
                        </div>
                        <p className="text-sm text-slate-300">75% probability of outage in next 2 hours.</p>
                      </div>
                    </div>
                  </div>

                  {/* AI Recommendations */}
                  <div className="glass-card rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">AI Recommendations</h3>
                    <div className="space-y-3">
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500/50 flex items-center justify-center flex-shrink-0">
                          <Brain className="w-4 h-4 text-purple-400" />
                        </div>
                        <p className="text-sm text-slate-300">Immediately activate manual data collection for AXIS Bank customers</p>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500/50 flex items-center justify-center flex-shrink-0">
                          <Brain className="w-4 h-4 text-purple-400" />
                        </div>
                        <p className="text-sm text-slate-300">Send proactive notifications to HDFC customers about potential delays</p>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500/50 flex items-center justify-center flex-shrink-0">
                          <Brain className="w-4 h-4 text-purple-400" />
                        </div>
                        <p className="text-sm text-slate-300">Increase PDF processing team capacity by 40% for weekend operations</p>
                      </div>
                    </div>
                  </div>

                  {/* Planned Maintenance */}
                  <div className="glass-card rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Planned Maintenance</h3>
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                      <p className="text-sm text-slate-300">3 FIPs showing maintenance patterns for this weekend. Impact: 60% of user base.</p>
                      <button 
                        onClick={() => {
                          // Switch to AI Predictions tab and scroll to timeline
                          setActiveTab('predictions');
                          setTimeout(() => {
                            const timelineElement = document.querySelector('#prediction-timeline');
                            if (timelineElement) {
                              timelineElement.scrollIntoView({ behavior: 'smooth' });
                            }
                          }, 100);

                          // Show success notification
                          const notification = document.createElement('div');
                          notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
                          notification.innerHTML = '📅 Viewing maintenance schedule in timeline';
                          document.body.appendChild(notification);
                          setTimeout(() => notification.remove(), 3000);
                        }}
                        className="mt-3 w-full px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                      >
                        <Calendar className="w-4 h-4" />
                        View Schedule
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="animate-slide-up space-y-8">

              {/* Historical Downtime Patterns */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                      <History className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-white">Historical Downtime Patterns</h2>
                      <p className="text-sm text-slate-400">AI-analyzed patterns and recurring issues</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <select 
                      className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                      onChange={(e) => {/* Add time range filter handler */}}
                    >
                      <option value="7d">Last 7 days</option>
                      <option value="30d">Last 30 days</option>
                      <option value="90d">Last 90 days</option>
                    </select>
                    <button className="btn-refresh">
                      <RefreshCw className="w-4 h-4" />
                      <span>Refresh</span>
                    </button>
                  </div>
                </div>

                {/* Pattern Analysis */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  {Object.entries(fipsData)
                    .filter(([fipId]) => selectedFipsForPrediction.length === 0 || selectedFipsForPrediction.includes(fipId))
                    .map(([fipId, fip]) => {
                      const prediction = patternsData[fipId] || {};
                      const patterns = prediction?.patterns_detected || [];
                      const anomalies = prediction?.anomalies || [];
                      
                      return (
                        <div key={fipId} className="glass-card rounded-xl p-6">
                          <div className="flex items-center justify-between mb-4">
                            <div>
                              <h4 className="font-semibold text-white text-lg">{fip.bank_name}</h4>
                              <p className="text-sm text-slate-400">Pattern Analysis</p>
                            </div>
                            <StatusBadge status={fip.current_status} />
                          </div>

                          {/* Pattern Categories */}
                          <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="bg-slate-800/50 rounded-lg p-4">
                              <h5 className="text-sm font-medium text-slate-300 mb-2">Maintenance Patterns</h5>
                              <div className="text-2xl font-bold text-white">
                                {Math.floor(Math.random() * 4)}
                              </div>
                              <p className="text-xs text-slate-400">Detected this month</p>
                            </div>
                            {/* <div className="bg-slate-800/50 rounded-lg p-4">
                              <h5 className="text-sm font-medium text-slate-300 mb-2">Performance Issues</h5>
                              <div className="text-2xl font-bold text-white">
                                {patternsData[fipId]?.performance_issues || 0}
                              </div>
                              <p className="text-xs text-slate-400">Detected this month</p>
                            </div> */}
                          </div>

                          {/* Pattern Details */}
                          <div className="space-y-4">
                            <div>
                              <h5 className="text-sm font-medium text-slate-300 mb-3">Recurring Patterns</h5>
                              <div className="space-y-2">
                                {patterns.map((pattern, index) => (
                                  <div 
                                    key={index} 
                                    className="bg-slate-700/30 rounded-lg p-3 hover:bg-slate-700/50 transition-colors cursor-pointer"
                                    onClick={() => {/* Add pattern details handler */}}
                                  >
                                    <div className="flex items-start gap-2">
                                      <div className="mt-1">
                                        {pattern.toLowerCase().includes('maintenance') ? '🔧' :
                                         pattern.toLowerCase().includes('backup') ? '💾' :
                                         pattern.toLowerCase().includes('peak') ? '📈' :
                                         pattern.toLowerCase().includes('degradation') ? '📉' : '⚡'}
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-sm text-slate-300">{pattern}</p>
                                        <div className="flex items-center gap-4 mt-2">
                                          <span className="text-xs text-slate-500">Last occurred: 2 days ago</span>
                                          <span className="text-xs text-slate-500">Frequency: Weekly</span>
                                          <span className="text-xs text-slate-500">Avg Duration: 45 min</span>
                                        </div>
                                      </div>
                                      <ChevronRight className="w-4 h-4 text-slate-500" />
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Anomalies with Severity */}
                            {anomalies.length > 0 && (
                              <div>
                                <h5 className="text-sm font-medium text-red-400 mb-3">Recent Anomalies</h5>
                                <div className="space-y-2">
                                  {anomalies.map((anomaly, index) => (
                                    <div 
                                      key={index} 
                                      className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 hover:bg-red-500/20 transition-colors cursor-pointer"
                                      onClick={() => {/* Add anomaly details handler */}}
                                    >
                                      <div className="flex items-start gap-2">
                                        <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5" />
                                        <div className="flex-1">
                                          <p className="text-sm text-red-300">{anomaly}</p>
                                          <div className="flex items-center gap-2 mt-2">
                                            <span className="px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs">High Severity</span>
                                            <span className="text-xs text-slate-400">Detected 3 hours ago</span>
                                            <span className="text-xs text-slate-400">Impact: 1,200+ users</span>
                                          </div>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-red-400" />
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Impact Metrics */}
                            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-700/30">
                              <div className="bg-slate-700/30 rounded-lg p-3">
                                <p className="text-xs text-slate-400 mb-1">Mean Time Between Failures</p>
                                <p className="text-lg font-semibold text-white">
                                  {fip.current_status === 'critical' ? '8.5' :
                                   fip.current_status === 'degraded' ? '24.3' : '72.1'}
                                  <span className="text-sm text-slate-400 ml-1">hours</span>
                                </p>
                                <div className="w-full bg-slate-800 rounded-full h-1 mt-2">
                                  <div 
                                    className="bg-blue-500 h-1 rounded-full" 
                                    style={{ 
                                      width: `${fip.current_status === 'critical' ? 30 :
                                              fip.current_status === 'degraded' ? 60 : 90}%` 
                                    }}
                                  ></div>
                                </div>
                              </div>
                              <div className="bg-slate-700/30 rounded-lg p-3">
                                <p className="text-xs text-slate-400 mb-1">Mean Time To Recovery</p>
                                <p className="text-lg font-semibold text-white">
                                  {fip.current_status === 'critical' ? '45-60' :
                                   fip.current_status === 'degraded' ? '20-30' : '5-10'}
                                  <span className="text-sm text-slate-400 ml-1">min</span>
                                </p>
                                <div className="w-full bg-slate-800 rounded-full h-1 mt-2">
                                  <div 
                                    className="bg-green-500 h-1 rounded-full" 
                                    style={{ 
                                      width: `${fip.current_status === 'critical' ? 40 :
                                              fip.current_status === 'degraded' ? 70 : 95}%` 
                                    }}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* Historical Trends Chart */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-white">Performance Trends</h2>
                      <p className="text-sm text-slate-400">Long-term performance analysis</p>
                    </div>
                  </div>
                  
                  {/* Chart Controls */}
                  <div className="flex items-center gap-3">
                    <select 
                      className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                      onChange={(e) => {/* Add metric selector handler */}}
                    >
                      <option value="success_rate">Success Rate</option>
                      <option value="response_time">Response Time</option>
                      <option value="error_rate">Error Rate</option>
                      <option value="downtime">Downtime</option>
                    </select>
                  </div>
                </div>
                
                <div className="h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="consent" 
                        stroke="#3b82f6" 
                        name="Consent Success (%)" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                        activeDot={{ r: 8 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="dataFetch" 
                        stroke="#10b981" 
                        name="Data Fetch Success (%)" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                        activeDot={{ r: 8 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="errorRate" 
                        stroke="#ef4444" 
                        name="Error Rate (%)" 
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={{ r: 4 }}
                        activeDot={{ r: 8 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Trend Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <h5 className="text-sm font-medium text-slate-300">Success Rate Trend</h5>
                      <TrendingUp className="w-4 h-4 text-green-400" />
                    </div>
                    <p className="text-2xl font-bold text-white mt-2">+5.2%</p>
                    <p className="text-xs text-slate-400">vs. last period</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <h5 className="text-sm font-medium text-slate-300">Response Time</h5>
                      <TrendingDown className="w-4 h-4 text-red-400" />
                    </div>
                    <p className="text-2xl font-bold text-white mt-2">-12.8%</p>
                    <p className="text-xs text-slate-400">vs. last period</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <h5 className="text-sm font-medium text-slate-300">Error Rate</h5>
                      <TrendingDown className="w-4 h-4 text-green-400" />
                    </div>
                    <p className="text-2xl font-bold text-white mt-2">-3.7%</p>
                    <p className="text-xs text-slate-400">vs. last period</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Analytics Tab - WITH WORKING CHARTS */}
          {activeTab === 'analytics' && (
            <div className="animate-slide-up space-y-8">
            {/* Performance Summary */}
              <div className="glass-card rounded-xl p-6">
                <h3 className="text-xl font-semibold text-white mb-6">Performance Metrics Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-blue-400">
                      {Object.values(fipsData).length > 0 ? 
                        (Object.values(fipsData).reduce((sum, fip) => sum + fip.consent_success_rate, 0) / Object.values(fipsData).length).toFixed(1) + '%'
                        : '67.2%'
                      }
                    </div>
                    <div className="text-blue-300 font-medium">Avg Consent Success</div>
                    <div className="text-blue-400/70 text-sm">Across all FIPs</div>
                  </div>
                  
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-green-400">
                      {Object.values(fipsData).length > 0 ? 
                        (Object.values(fipsData).reduce((sum, fip) => sum + fip.data_fetch_success_rate, 0) / Object.values(fipsData).length).toFixed(1) + '%'
                        : '61.7%'
                      }
                    </div>
                    <div className="text-green-300 font-medium">Avg Data Fetch Success</div>
                    <div className="text-green-400/70 text-sm">Across all FIPs</div>
                  </div>
                  
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-purple-400">
                      {Object.values(fipsData).length > 0 ? 
                        (Object.values(fipsData).reduce((sum, fip) => sum + parseFloat(fip.avg_response_time), 0) / Object.values(fipsData).length).toFixed(1) + 's'
                        : '3.6s'
                      }
                    </div>
                    <div className="text-purple-300 font-medium">Avg Response Time</div>
                    <div className="text-purple-400/70 text-sm">System-wide average</div>
                  </div>
                  
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-red-400">
                      {Object.values(fipsData).length > 0 ? 
                        (Object.values(fipsData).reduce((sum, fip) => sum + fip.error_rate, 0) / Object.values(fipsData).length).toFixed(1) + '%'
                        : '32.8%'
                      }
                    </div>
                    <div className="text-red-300 font-medium">Avg Error Rate</div>
                    <div className="text-red-400/70 text-sm">System-wide average</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Performance Chart */}
                <div className="glass-card rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                      <BarChart3 className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white">Performance Comparison</h3>
                  </div>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="name" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" domain={[0, 100]} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <Bar dataKey="consent" fill="#3b82f6" name="Consent Success (%)" />
                        <Bar dataKey="dataFetch" fill="#10b981" name="Data Fetch Success (%)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Status Distribution */}
                <div className="glass-card rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
                      <Activity className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white">FIP Status Distribution</h3>
                  </div>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={statusData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {statusData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Response Time & Error Rate Line Chart */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Response Time & Error Analysis</h3>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis yAxisId="left" orientation="left" stroke="#94a3b8" />
                      <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="responseTime" 
                        stroke="#8b5cf6" 
                        strokeWidth={3}
                        name="Response Time (s)"
                        dot={{ r: 6 }}
                      />
                      <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="errorRate" 
                        stroke="#ef4444" 
                        strokeWidth={3}
                        name="Error Rate (%)"
                        dot={{ r: 6 }}
                        strokeDasharray="5 5"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* AI Predictions Tab */}
          {activeTab === 'predictions' && (
            <div className="animate-slide-up space-y-8">
              <div className="grid gap-6 glass-card rounded-xl p-6">
              <h3 className="font-semibold text-white">📊 Overall System Impact Summary</h3>
                {/* Overall Impact Summary */}
                <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        {impactSummary.usersAtRisk}
                      </div>
                      <div className="text-sm text-slate-400">Total Users at Risk</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        {impactSummary.highRiskFips}
                      </div>
                      <div className="text-sm text-slate-400">High Risk FIPs</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        ₹{Math.round(
                          impactSummary.potentialCostImpact
                        ).toLocaleString()}
                      </div>
                      <div className="text-sm text-slate-400">Potential Cost Impact</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 24-Hour Prediction Timeline */}
              <div id="prediction-timeline" className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <Clock className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-white">24-Hour Prediction Timeline</h2>
                      <p className="text-sm text-slate-400">AI-predicted events and maintenance windows</p>
                    </div>
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        fetchMainteneceFips();
                        const notification = document.createElement('div');
                        notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                        notification.innerHTML = '✅ Timeline updated with latest predictions';
                        document.body.appendChild(notification);
                        setTimeout(() => notification.remove(), 3000);
                      } catch (error) {
                        console.error('Error updating timeline:', error);
                        const notification = document.createElement('div');
                        notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                        notification.innerHTML = '❌ Failed to update timeline';
                        document.body.appendChild(notification);
                        setTimeout(() => notification.remove(), 3000);
                      }
                    }}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-600/70 border border-slate-600 hover:border-slate-500 text-white rounded-lg text-sm font-medium transition-all duration-200 backdrop-blur-sm shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Update Timeline</span>
                  </button>
                </div>

                {/* Timeline View */}
                <div className="relative">
                  <div className="absolute left-0 top-0 bottom-0 w-px bg-slate-700 ml-3"></div>
                  {
                    hourlyMaintenence.map((hourlyData, idx) => {
                      const color = idx == 0 ? "yellow" : "blue"
                      const now = new Date();
                      const maintenanceTimeHour = (now.getHours() + hourlyData['hour'])%24
                      const maintenanceTime = `~ ${prependZero(maintenanceTimeHour)}:00`;

                      return (
                        <div className="ml-6 mb-6 relative">
                          <div className="absolute -left-9 mt-1.5">
                            <div className={`w-5 h-5 rounded-full border-2 bg-${color}-500/20 border-${color}-500`}></div>
                          </div>
                          <div className="flex items-center text-sm text-slate-400 mb-1">
                            <Clock className="w-4 h-4 mr-2" />
                            {maintenanceTime}
                          </div>
                          <div className="bg-slate-800/50 rounded-lg p-4">
                            <p className="text-white font-medium">Scheduled System Maintenance</p>
                            <div className="mt-2 space-y-1">
                              {
                                hourlyData.prediction.map(fipObject => {
                                  return (
                                    <div className="flex items-center gap-2 text-sm text-slate-300">
                                      <span className={`w-2 h-2 rounded-full bg-${color}-500`}></span>
                                      {fipsData[fipObject.fip].bank_name || ""} <small className='text-slate-400'>{fipObject.timeWindow.split("next ")[1]}</small>
                                    </div>
                                  )
                                })
                              }
                            </div>
                          </div>
                        </div>
                      )
                    })
                  }

                  {/* 9:00 AM - Peak Load */}
                  {/* <div className="ml-6 mb-6 relative">
                    <div className="absolute -left-9 mt-1.5">
                      <div className="w-5 h-5 rounded-full border-2 bg-blue-500/20 border-blue-500"></div>
                    </div>
                    <div className="flex items-center text-sm text-slate-400 mb-1">
                      <Clock className="w-4 h-4 mr-2" />
                      9:00 AM • 3 hours
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-white font-medium">Peak Load Window</p>
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center gap-2 text-sm text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                          Axis Bank - Expected 2x normal traffic
                        </div>
                        <div className="flex items-center gap-2 text-sm text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                          Bank of India - Expected 1.8x normal traffic
                        </div>
                      </div>
                      <p className="text-sm text-slate-400 mt-2">
                        High traffic period - Scale up resources recommended
                      </p>
                    </div>
                  </div> */}

                  {/* Add more timeline events here */}
                </div>
              </div>

              {/* FIP Selection and Predictions */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">AI Analysis for FIP Downtime</h3>
                </div>
                
                {/* FIP Selection */}
                <div className="mb-6 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(fipsData).map(([fipId, fip]) => (
                      <button
                        key={fipId}
                        onClick={() => {
                          const selectedFips = new Set(selectedFipsForPrediction);
                          if (selectedFips.has(fipId)) {
                            selectedFips.delete(fipId);
                          } else {
                            selectedFips.add(fipId);
                          }
                          setSelectedFipsForPrediction(Array.from(selectedFips));
                        }}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                          selectedFipsForPrediction.includes(fipId)
                            ? 'bg-purple-500 text-white shadow-lg'
                            : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/70'
                        }`}
                      >
                        {fip.bank_name}
                      </button>
                    ))}
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-slate-400 text-sm">
                      {selectedFipsForPrediction.length === 0
                        ? 'Select FIPs to analyze'
                        : `${selectedFipsForPrediction.length} FIP${selectedFipsForPrediction.length > 1 ? 's' : ''} selected`}
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setSelectedFipsForPrediction(Object.keys(fipsData))}
                        className="text-sm text-purple-400 hover:text-purple-300"
                      >
                        Select All
                      </button>
                      <button
                        onClick={() => setSelectedFipsForPrediction([])}
                        className="text-sm text-slate-400 hover:text-slate-300"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <button
                    onClick={() => {
                      if (selectedFipsForPrediction.length === 0) {
                        const notification = document.createElement('div');
                        notification.className = 'fixed top-4 right-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                        notification.innerHTML = '⚠️ Please select at least one FIP';
                        document.body.appendChild(notification);
                        setTimeout(() => notification.remove(), 3000);
                        return;
                      }
                      generatePredictions(selectedFipsForPrediction);
                    }}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-700 hover:from-purple-600 hover:to-purple-800 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl mb-4"
                  >
                    <Brain className="w-5 h-5" />
                    Generate Advanced AI Predictions
                  </button>
                  <p className="text-slate-400 text-sm">
                    Use machine learning models to predict potential FIP failures and business impact.
                  </p>
                </div>

                {/* Add FIP Downtime Patterns Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(fipsData)
                    .filter(([fipId]) => selectedFipsForPrediction.length === 0 || selectedFipsForPrediction.includes(fipId))
                    .map(([fipId, fip]) => {
                      const prediction = patternsData[fipId] || {};
                      const patterns = prediction?.patterns_detected || [];
                      const probability = prediction?.downtime_prediction?.probability || 0;
                      const timeWindow = prediction?.downtime_prediction?.time_window || '';
                      const confidence = prediction?.downtime_prediction?.confidence || '';

                      return (
                        <div key={fipId} className="bg-slate-800/50 border border-slate-700/30 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div>
                              <h4 className="font-semibold text-white">{fip.bank_name}</h4>
                              <p className="text-xs text-slate-400">Confidence: {confidence}</p>
                            </div>
                            <div className="text-right">
                              <StatusBadge status={fip.current_status} />
                              <p className="text-xs text-slate-400 mt-1">{timeWindow}</p>
                            </div>
                          </div>

                          {/* Downtime Probability Indicator */}
                          <div className="mb-4">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-slate-400">Downtime Probability</span>
                              <span className={`font-medium ${
                                probability > 0.7 ? 'text-red-400' :
                                probability > 0.4 ? 'text-yellow-400' : 'text-green-400'
                              }`}>{(probability * 100).toFixed(1)}%</span>
                            </div>
                            <div className="w-full h-2 bg-slate-700 rounded-full">
                              <div 
                                className={`h-2 rounded-full ${
                                  probability > 0.7 ? 'bg-red-500' :
                                  probability > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${probability * 100}%` }}
                              ></div>
                            </div>
                          </div>

                          {/* Patterns List */}
                          <div className="space-y-2">
                            {patterns.length > 0 ? (
                              patterns.map((pattern, index) => (
                                <div key={index} className="flex items-start gap-2 text-sm">
                                  <div className="mt-1">
                                    {pattern.toLowerCase().includes('maintenance') ? '🔧' :
                                     pattern.toLowerCase().includes('backup') ? '💾' :
                                     pattern.toLowerCase().includes('peak') ? '📈' :
                                     pattern.toLowerCase().includes('degradation') ? '📉' : '⚡'}
                                  </div>
                                  <p className="text-slate-300">{pattern}</p>
                                </div>
                              ))
                            ) : (
                              <p className="text-sm text-slate-400 italic">Generating patterns...</p>
                            )}
                          </div>

                          {/* Impact Information */}
                          {prediction.user_impact && (
                            <div className="mt-3 pt-3 border-t border-slate-700/30">
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div>
                                  <span className="text-slate-400">Affected Users:</span>
                                  <span className="text-white ml-1">
                                    {prediction.user_impact.estimated_affected_users?.toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-400">Failure Rate:</span>
                                  <span className="text-white ml-1">
                                    {prediction.user_impact.consent_failure_rate}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          )}
          {activeTab === 'alerts' && (
            <AlertsTab apiService={apiService} activeTab={activeTab} />
          )}
        {activeTab === 'settings' && (
          <SettingsTab apiService={apiService} />
        )}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-700/50 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center text-sm text-slate-400">
              <p>AA Gateway AI Operations Dashboard | Powered by React & Flask | Last updated: {lastUpdated.toLocaleString()}</p>
              <p className="mt-2">🚀 Built for the Account Aggregator ecosystem with AI-powered insights</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;