import React from 'react';

const StatusBadge = ({ status, showIcon = true, className = '' }) => {
  const getStatusStyles = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return 'status-healthy';
      case 'degraded':
      case 'warning':
        return 'status-degraded';
      case 'critical':
        return 'status-critical';
      default:
        return 'bg-slate-600 text-slate-300 border border-slate-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return '✅';
      case 'degraded':
      case 'warning':
        return '⚠️';
      case 'critical':
        return '🚨';
      default:
        return '❓';
    }
  };

  return (
    <span className={`status-badge ${getStatusStyles(status)} ${className}`}>
      {showIcon && <span className="mr-1">{getStatusIcon(status)}</span>}
      {status?.charAt(0).toUpperCase() + status?.slice(1)}
    </span>
  );
};

export default StatusBadge;