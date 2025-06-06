// Format percentage
export const formatPercentage = (num, decimals = 1) => {
  return `${parseFloat(num).toFixed(decimals)}%`;
};

// Get status color class
export const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'healthy':
      return 'status-healthy';
    case 'degraded':
    case 'warning':
      return 'status-degraded';
    case 'critical':
      return 'status-critical';
    default:
      return 'bg-gray-50 text-gray-700 border border-gray-200';
  }
};

// Get status icon
export const getStatusIcon = (status) => {
  switch (status?.toLowerCase()) {
    case 'healthy':
      return '✅';
    case 'degraded':
    case 'warning':
      return '⚠️';
    case 'critical':
      return '❌';
    default:
      return '❓';
  }
};

// Format currency (Indian Rupees)
export const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};
