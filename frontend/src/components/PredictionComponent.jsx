import React, { useState } from 'react';
import { Brain, TrendingDown, AlertTriangle, Users, Clock } from 'lucide-react';
import { apiService } from '../services/api';
import { formatCurrency, formatPercentage } from '../utils/helpers';
import Loading from './common/Loading';

const PredictionComponent = ({ fipsData }) => {
  const [loading, setLoading] = useState(false);
  const [predictions, setPredictions] = useState(null);
  const [selectedFips, setSelectedFips] = useState(Object.keys(fipsData));
  const [timeHorizon, setTimeHorizon] = useState('24h');

  const generatePredictions = async () => {
    if (selectedFips.length === 0) {
      alert('Please select at least one FIP');
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.predictFipIssues({
        fips: selectedFips,
        time_horizon: timeHorizon
      });
      setPredictions(response.data.data);
    } catch (error) {
      console.error('Error generating predictions:', error);
      alert('Failed to generate predictions');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel) {
      case 'low': return '🟢';
      case 'medium': return '🟡';
      case 'high': return '🟠';
      case 'critical': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <Brain className="w-6 h-6 text-primary-600 mr-3" />
        <h2 className="text-xl font-semibold text-gray-900">AI Predictions & Risk Analysis</h2>
      </div>

      {/* Controls */}
      <div className="mb-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select FIPs for Analysis
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(fipsData).map(([fipId, fip]) => (
              <label key={fipId} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedFips.includes(fipId)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedFips([...selectedFips, fipId]);
                    } else {
                      setSelectedFips(selectedFips.filter(id => id !== fipId));
                    }
                  }}
                  className="rounded border-gray-300 text-primary-600 mr-2"
                />
                <span className="text-sm text-gray-700">{fip.bank_name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Time Horizon
            </label>
            <select
              value={timeHorizon}
              onChange={(e) => setTimeHorizon(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="1h">Next 1 Hour</option>
              <option value="6h">Next 6 Hours</option>
              <option value="24h">Next 24 Hours</option>
              <option value="7d">Next 7 Days</option>
            </select>
          </div>

          <div className="flex-1 flex justify-end">
            <button
              onClick={generatePredictions}
              disabled={loading || selectedFips.length === 0}
              className="btn-primary flex items-center"
            >
              <Brain className="w-4 h-4 mr-2" />
              {loading ? 'Analyzing...' : 'Generate AI Predictions'}
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && <Loading text="AI is analyzing FIP patterns..." />}

      {/* Predictions Results */}
      {predictions && !loading && (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">AI Analysis Summary</h3>
            <p className="text-sm text-blue-700">
              Generated predictions for {Object.keys(predictions).length} FIPs using machine learning models 
              trained on historical performance data, system metrics, and operational patterns.
            </p>
          </div>

          {/* Prediction Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Object.entries(predictions).map(([fipId, prediction]) => (
              <div key={fipId} className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {fipsData[fipId]?.bank_name || fipId}
                    </h3>
                    <p className="text-sm text-gray-600">{fipId}</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskColor(prediction.risk_level)}`}>
                    {getRiskIcon(prediction.risk_level)} {prediction.risk_level?.toUpperCase()} RISK
                  </div>
                </div>

                {/* Downtime Prediction */}
                <div className="mb-4">
                  <div className="flex items-center mb-2">
                    <TrendingDown className="w-5 h-5 text-red-500 mr-2" />
                    <h4 className="font-medium text-gray-900">Downtime Prediction</h4>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Probability:</span>
                        <span className="font-semibold text-gray-900 ml-2">
                          {formatPercentage(prediction.downtime_prediction?.probability * 100)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Time Window:</span>
                        <span className="font-semibold text-gray-900 ml-2">
                          {prediction.downtime_prediction?.time_window}
                        </span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-gray-600">Confidence:</span>
                        <span className="font-semibold text-gray-900 ml-2">
                          {prediction.downtime_prediction?.confidence}
                        </span>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-sm text-gray-700">
                        <strong>AI Reasoning:</strong> {prediction.downtime_prediction?.reasoning}
                      </p>
                    </div>
                  </div>
                </div>

                {/* User Impact */}
                <div className="mb-4">
                  <div className="flex items-center mb-2">
                    <Users className="w-5 h-5 text-blue-500 mr-2" />
                    <h4 className="font-medium text-gray-900">User Impact Analysis</h4>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-3">
                    <div className="grid grid-cols-1 gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Affected Users:</span>
                        <span className="font-semibold text-gray-900">
                          {prediction.user_impact?.estimated_affected_users?.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Recommended Action:</span>
                        <span className="font-semibold text-gray-900">
                          {prediction.user_impact?.recommended_fallback}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Business Impact */}
                <div className="mb-4">
                  <div className="flex items-center mb-2">
                    <Clock className="w-5 h-5 text-orange-500 mr-2" />
                    <h4 className="font-medium text-gray-900">Business Impact</h4>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-3">
                    <div className="grid grid-cols-1 gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Processing Delay:</span>
                        <span className="font-semibold text-gray-900">
                          {prediction.business_impact?.processing_delay}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Manual Processing Cost:</span>
                        <span className="font-semibold text-gray-900">
                          {prediction.business_impact?.manual_processing_cost}
                        </span>
                      </div>
                      {prediction.health_score && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Health Score:</span>
                          <span className="font-semibold text-gray-900">
                            {prediction.health_score}/10
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Recommendation */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
                    <div>
                      <h5 className="font-medium text-yellow-900 mb-1">Recommended Actions</h5>
                      <p className="text-sm text-yellow-800">
                        {prediction.risk_level === 'critical' ? 
                          'Immediate action required. Activate manual fallback procedures and alert operations team.' :
                          prediction.risk_level === 'high' ?
                          'Prepare fallback procedures and monitor closely. Consider proactive user notifications.' :
                          prediction.risk_level === 'medium' ?
                          'Monitor performance trends and prepare contingency plans.' :
                          'Continue normal monitoring. System appears stable.'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Overall Impact Summary */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Overall System Impact Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {Object.values(predictions).reduce((sum, p) => sum + (p.user_impact?.estimated_affected_users || 0), 0).toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total Users at Risk</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {Object.values(predictions).filter(p => p.risk_level === 'critical' || p.risk_level === 'high').length}
                </div>
                <div className="text-sm text-gray-600">High Risk FIPs</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {formatPercentage(
                    (Object.values(predictions).reduce((sum, p) => sum + (p.downtime_prediction?.probability || 0), 0) / Object.keys(predictions).length) * 100
                  )}
                </div>
                <div className="text-sm text-gray-600">Avg Risk Probability</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!predictions && !loading && (
        <div className="text-center py-8">
          <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Ready for AI Analysis</h3>
          <p className="text-gray-600 mb-4">
            Select FIPs and click "Generate AI Predictions" to get machine learning insights 
            about potential downtime and business impact.
          </p>
        </div>
      )}
    </div>
  );
};

export default PredictionComponent;