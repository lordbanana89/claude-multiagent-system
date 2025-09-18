import React from 'react';
import type { Notification } from '../../context/AppContext';

interface NotificationToastProps {
  notifications: Notification[];
}

const NotificationToast: React.FC<NotificationToastProps> = ({ notifications }) => {
  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      default: return 'ℹ️';
    }
  };

  const getColorClasses = (type: Notification['type']) => {
    switch (type) {
      case 'success': return 'bg-green-600 border-green-500';
      case 'error': return 'bg-red-600 border-red-500';
      case 'warning': return 'bg-yellow-600 border-yellow-500';
      default: return 'bg-blue-600 border-blue-500';
    }
  };

  return (
    <div className="fixed bottom-20 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`
            ${getColorClasses(notification.type)}
            border rounded-lg p-3 shadow-lg
            animate-slide-in-right
            flex items-start space-x-2
          `}
        >
          <span className="text-white">{getIcon(notification.type)}</span>
          <span className="text-white text-sm flex-1">{notification.message}</span>
        </div>
      ))}
    </div>
  );
};

export default NotificationToast;