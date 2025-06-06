import React from 'react';

const Loading = ({ size = 'medium', text = 'Loading...' }) => {
  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-10 h-10',
    large: 'w-16 h-16'
  };

  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <div className={`animate-spin rounded-full border-4 border-slate-600 border-t-blue-500 ${sizeClasses[size]} mx-auto`}></div>
        <p className="mt-4 text-slate-400 font-medium">{text}</p>
      </div>
    </div>
  );
};

export default Loading;