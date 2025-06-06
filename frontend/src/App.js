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
  FileText,
  Shield,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Calendar
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import Loading from './components/common/Loading';
import StatusBadge from './components/common/StatusBadge';
import { apiService } from './services/api';
import { formatPercentage } from './utils/helpers';

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fipsData, setFipsData] = useState({});
  const [systemOverview, setSystemOverview] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedFipsForPrediction, setSelectedFipsForPrediction] = useState([]);
  const [predictionsData, setPredictionsData] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [patternsData, setPatternsData] = useState({});

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

      const [fipsResponse, overviewResponse, predictionsResponse] = await Promise.all([
        apiService.getFips(),
        apiService.getSystemOverview(),
        apiService.predictFipIssues({ fips: Object.keys(fipsData), time_horizon: '24h' })
      ]);

      setFipsData(fipsResponse.data.data);
      setSystemOverview(overviewResponse.data.data);
      setPatternsData(predictionsResponse.data?.data || {});
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
      console.log('Predictions:', response.data);
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
  }, [activeTab, fipsData]);

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

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Activity },
    { id: 'history', name: 'History', icon: History },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
    { id: 'predictions', name: 'AI Predictions', icon: Brain },
  ];

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
              { icon: Home, label: 'Overview', id: 'overview' },
              { icon: BarChart3, label: 'Analytics', id: 'analytics' },
              { icon: Brain, label: 'AI Predictions', id: 'predictions' },
              { icon: Bell, label: 'Alerts', id: 'alerts', count: criticalFips + degradedFips },
              { icon: History, label: 'History', id: 'history' },
              { icon: FileText, label: 'Reports', id: 'reports' },
              { icon: Shield, label: 'Security', id: 'security' },
              { icon: Settings, label: 'Settings', id: 'settings' },
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
          {sidebarOpen && (
            <div className="absolute bottom-4 left-4 right-4">
              <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-white transition-all duration-200">
                <HelpCircle className="w-5 h-5" />
                <span>Help & Support</span>
              </button>
            </div>
          )}
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

          {activeTab === 'overview' && (
            <div className="animate-slide-up space-y-8">
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
                      {Object.entries(fipsData).map(([fipId, fip]) => (
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
                  {Object.entries(fipsData).map(([fipId, fip]) => {
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
                              {patterns.filter(p => p.toLowerCase().includes('maintenance')).length}
                            </div>
                            <p className="text-xs text-slate-400">Detected this month</p>
                          </div>
                          <div className="bg-slate-800/50 rounded-lg p-4">
                            <h5 className="text-sm font-medium text-slate-300 mb-2">Performance Issues</h5>
                            <div className="text-2xl font-bold text-white">
                              {patterns.filter(p => p.toLowerCase().includes('degradation')).length}
                            </div>
                            <p className="text-xs text-slate-400">Detected this month</p>
                          </div>
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

              {/* Add FIP Downtime Patterns Section */}
              <div className="glass-card rounded-xl p-6 mb-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-lg flex items-center justify-center">
                    <Clock className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">FIP Downtime Patterns</h3>
                    <p className="text-sm text-slate-400 mt-1">AI-predicted maintenance windows and patterns</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(fipsData).map(([fipId, fip]) => {
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
            </div>
          )}

          {/* AI Predictions Tab */}
          {activeTab === 'predictions' && (
            <div className="animate-slide-up space-y-8">
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
                        const allFips = Object.keys(fipsData);
                        const response = await apiService.predictFipIssues({ fips: allFips, time_horizon: '24h' });
                        setPredictionsData(response.data?.data || {});
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
                  
                  {/* 2:00 AM - Combined Maintenance */}
                  <div className="ml-6 mb-6 relative">
                    <div className="absolute -left-9 mt-1.5">
                      <div className="w-5 h-5 rounded-full border-2 bg-yellow-500/20 border-yellow-500"></div>
                    </div>
                    <div className="flex items-center text-sm text-slate-400 mb-1">
                      <Clock className="w-4 h-4 mr-2" />
                      2:00 AM • 2 hours
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-white font-medium">Scheduled System Maintenance</p>
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center gap-2 text-sm text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                          Axis Bank
                        </div>
                        <div className="flex items-center gap-2 text-sm text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                          Bank of India
                        </div>
                        <div className="flex items-center gap-2 text-sm text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                          Canara Bank
                        </div>
                      </div>
                      <p className="text-sm text-slate-400 mt-2">
                        Coordinated maintenance window for multiple FIPs
                      </p>
                    </div>
                  </div>

                  {/* 9:00 AM - Peak Load */}
                  <div className="ml-6 mb-6 relative">
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
                  </div>

                  {/* Add more timeline events here */}
                </div>
              </div>

              {/* FIP Selection and Predictions */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">AI Predictions & Risk Analysis</h3>
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

                {/* Prediction Results */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {Object.entries(fipsData)
                    .filter(([fipId]) => selectedFipsForPrediction.length === 0 || selectedFipsForPrediction.includes(fipId))
                    .map(([fipId, fip]) => {
                      const riskLevel = fip.current_status === 'critical' ? 'critical' : 
                                       fip.current_status === 'degraded' ? 'medium' : 'low';
                      const probability = fip.current_status === 'critical' ? 95 : 
                                         fip.current_status === 'degraded' ? 75 : 15;
                      
                      return (
                        <div key={fipId} className="bg-slate-800/50 border border-slate-700/30 rounded-lg p-6">
                          <div className="flex items-center justify-between mb-4">
                            <div>
                              <h4 className="font-semibold text-white">{fip.bank_name}</h4>
                              <p className="text-sm text-slate-400">{fip.fip_name}</p>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                              riskLevel === 'critical' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                              riskLevel === 'medium' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                              'bg-green-500/20 text-green-400 border border-green-500/30'
                            }`}>
                              {riskLevel === 'critical' ? '🔴 CRITICAL' :
                               riskLevel === 'medium' ? '🟡 MEDIUM' : '🟢 LOW'} RISK
                            </div>
                          </div>

                          {/* Prediction Details */}
                          <div className="space-y-4">
                            <div className="bg-slate-900/50 rounded-lg p-4">
                              <h5 className="font-medium text-white mb-2">🔮 Downtime Prediction</h5>
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-slate-400">Probability:</span>
                                  <span className="font-semibold text-white ml-2">{probability}%</span>
                                </div>
                                <div>
                                  <span className="text-slate-400">Time Window:</span>
                                  <span className="font-semibold text-white ml-2">
                                    {riskLevel === 'critical' ? 'Next 30 min' :
                                     riskLevel === 'medium' ? 'Next 2 hours' : 'Next 8 hours'}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                              <h5 className="font-medium text-white mb-2">👥 User Impact</h5>
                              <div className="text-sm">
                                <div className="flex justify-between">
                                  <span className="text-slate-400">Affected Users:</span>
                                  <span className="font-semibold text-white">
                                    {Math.round(fip.user_base * probability / 100).toLocaleString()}
                                  </span>
                                </div>
                                <div className="flex justify-between mt-2">
                                  <span className="text-slate-400">Estimated Cost:</span>
                                  <span className="font-semibold text-white">
                                    ₹{Math.round(probability * 1000).toLocaleString()}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                              <div className="flex items-start gap-2">
                                <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5" />
                                <div>
                                  <h6 className="font-medium text-yellow-300 text-sm">Recommended Actions</h6>
                                  <p className="text-yellow-200/80 text-sm">
                                    {riskLevel === 'critical' ? 
                                      'Immediate action required. Activate manual fallback procedures.' :
                                      riskLevel === 'medium' ?
                                      'Prepare fallback procedures and monitor closely.' :
                                      'Continue normal monitoring. System appears stable.'
                                    }
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>

                {/* Overall Impact Summary */}
                <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 mt-8">
                  <h3 className="font-semibold text-white mb-4">📊 Overall System Impact Summary</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        {Object.values(fipsData).reduce((sum, fip) => sum + fip.user_base, 0).toLocaleString()}
                      </div>
                      <div className="text-sm text-slate-400">Total Users at Risk</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        {Object.values(fipsData).filter(fip => fip.current_status === 'critical' || fip.current_status === 'degraded').length}
                      </div>
                      <div className="text-sm text-slate-400">High Risk FIPs</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        ₹{Math.round(
                          Object.values(fipsData).reduce((sum, fip) => {
                            const risk = fip.current_status === 'critical' ? 95 : 
                                        fip.current_status === 'degraded' ? 75 : 15;
                            return sum + (risk * 1000);
                          }, 0)
                        ).toLocaleString()}
                      </div>
                      <div className="text-sm text-slate-400">Potential Cost Impact</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
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