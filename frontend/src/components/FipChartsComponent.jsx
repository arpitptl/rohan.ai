import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { TrendingUp, PieChart as PieChartIcon } from 'lucide-react';

const FipChartsComponent = ({ fipsData }) => {
  // Prepare data for charts
  const successRateData = Object.entries(fipsData).map(([fipId, fip]) => ({
    name: fip.bank_name.split(' ')[0], // Short name for better display
    consent: parseFloat(fip.consent_success_rate),
    dataFetch: parseFloat(fip.data_fetch_success_rate),
    fullName: fip.bank_name
  }));

  const statusDistribution = Object.values(fipsData).reduce((acc, fip) => {
    const status = fip.current_status;
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  const pieData = Object.entries(statusDistribution).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    percentage: ((count / Object.keys(fipsData).length) * 100).toFixed(1)
  }));

  const responseTimeData = Object.entries(fipsData).map(([fipId, fip]) => ({
    name: fip.bank_name.split(' ')[0],
    responseTime: parseFloat(fip.avg_response_time),
    errorRate: parseFloat(fip.error_rate),
    fullName: fip.bank_name
  }));

  // Chart colors
  const colors = {
    healthy: '#22c55e',
    degraded: '#f59e0b', 
    critical: '#ef4444',
    consent: '#3b82f6',
    dataFetch: '#10b981',
    responseTime: '#8b5cf6',
    errorRate: '#ef4444'
  };

  const RADIAN = Math.PI / 180;
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        className="text-sm font-medium"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{payload[0]?.payload?.fullName || label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
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
    <div className="space-y-8">
      {/* Success Rates Comparison */}
      <div className="card">
        <div className="flex items-center mb-6">
          <TrendingUp className="w-6 h-6 text-primary-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">FIP Performance Comparison</h2>
        </div>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={successRateData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="consent" fill={colors.consent} name="Consent Success Rate (%)" />
              <Bar dataKey="dataFetch" fill={colors.dataFetch} name="Data Fetch Success Rate (%)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="mt-4 text-sm text-gray-600">
          <p>📊 Compare consent approval and data fetch success rates across all FIPs</p>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card">
          <div className="flex items-center mb-6">
            <PieChartIcon className="w-6 h-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">FIP Status Distribution</h2>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={colors[entry.name.toLowerCase()] || '#8884d8'} 
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name) => [`${value} FIPs`, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 space-y-2">
            {pieData.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: colors[item.name.toLowerCase()] }}
                  ></div>
                  <span className="text-gray-700">{item.name}</span>
                </div>
                <span className="font-medium text-gray-900">
                  {item.value} ({item.percentage}%)
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Response Time & Error Rate */}
        <div className="card">
          <div className="flex items-center mb-6">
            <TrendingUp className="w-6 h-6 text-orange-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Response Time & Error Analysis</h2>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={responseTimeData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" orientation="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="responseTime" 
                  stroke={colors.responseTime} 
                  strokeWidth={3}
                  name="Response Time (s)"
                  dot={{ r: 6 }}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="errorRate" 
                  stroke={colors.errorRate} 
                  strokeWidth={3}
                  name="Error Rate (%)"
                  dot={{ r: 6 }}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 text-sm text-gray-600">
            <p>📈 Monitor response times (solid line) and error rates (dashed line) for performance insights</p>
          </div>
        </div>
      </div>

      {/* Performance Metrics Summary */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Performance Metrics Summary</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600">
              {(successRateData.reduce((sum, item) => sum + item.consent, 0) / successRateData.length).toFixed(1)}%
            </div>
            <div className="text-sm text-blue-700 font-medium">Avg Consent Success</div>
            <div className="text-xs text-blue-600 mt-1">Across all FIPs</div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">
              {(successRateData.reduce((sum, item) => sum + item.dataFetch, 0) / successRateData.length).toFixed(1)}%
            </div>
            <div className="text-sm text-green-700 font-medium">Avg Data Fetch Success</div>
            <div className="text-xs text-green-600 mt-1">Across all FIPs</div>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-600">
              {(responseTimeData.reduce((sum, item) => sum + item.responseTime, 0) / responseTimeData.length).toFixed(1)}s
            </div>
            <div className="text-sm text-purple-700 font-medium">Avg Response Time</div>
            <div className="text-xs text-purple-600 mt-1">System-wide average</div>
          </div>
          
          <div className="bg-red-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-600">
              {(responseTimeData.reduce((sum, item) => sum + item.errorRate, 0) / responseTimeData.length).toFixed(1)}%
            </div>
            <div className="text-sm text-red-700 font-medium">Avg Error Rate</div>
            <div className="text-xs text-red-600 mt-1">System-wide average</div>
          </div>
        </div>
      </div>

      {/* Detailed FIP Comparison Table */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Detailed FIP Comparison</h2>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  FIP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Consent Success
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data Fetch Success
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Response Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Error Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User Base
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(fipsData).map(([fipId, fip]) => (
                <tr key={fipId} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{fip.bank_name}</div>
                    <div className="text-sm text-gray-500">{fip.fip_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      fip.current_status === 'healthy' ? 'bg-green-100 text-green-800' :
                      fip.current_status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {fip.current_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{fip.consent_success_rate}%</div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${fip.consent_success_rate}%` }}
                      ></div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{fip.data_fetch_success_rate}%</div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full" 
                        style={{ width: `${fip.data_fetch_success_rate}%` }}
                      ></div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {fip.avg_response_time}s
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {fip.error_rate}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {fip.user_base?.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FipChartsComponent;