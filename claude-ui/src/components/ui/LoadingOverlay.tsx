import React from 'react';

const LoadingOverlay: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-gray-800 rounded-lg p-6 flex flex-col items-center space-y-4">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-gray-600 rounded-full"></div>
          <div className="w-16 h-16 border-4 border-blue-500 rounded-full animate-spin absolute top-0 left-0 border-t-transparent"></div>
        </div>
        <p className="text-white text-sm font-medium">Loading...</p>
      </div>
    </div>
  );
};

export default LoadingOverlay;