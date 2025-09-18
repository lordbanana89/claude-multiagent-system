// MCP Activity Stream Component - Real-time activity display
import React, { useState, useRef, useEffect } from 'react';
import { useMCPWebSocket } from '../hooks/useMCPWebSocket';
import type { MCPActivity } from '../services/mcpTypes';

interface ActivityStreamProps {
  maxItems?: number;
  autoScroll?: boolean;
}

const ActivityStream: React.FC<ActivityStreamProps> = ({
  maxItems = 50,
  autoScroll = true
}) => {
  const { activities, connected, clearActivities } = useMCPWebSocket(maxItems);
  const [filter, setFilter] = useState<string>('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to new activities
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [activities, autoScroll]);

  // Filter activities
  const filteredActivities = (activities || []).filter(activity => {
    if (!filter) return true;
    const searchStr = filter.toLowerCase();
    return (
      activity.agent?.toLowerCase().includes(searchStr) ||
      activity.action?.toLowerCase().includes(searchStr) ||
      activity.category?.toLowerCase().includes(searchStr) ||
      activity.type?.toLowerCase().includes(searchStr)
    );
  });

  // Group activities by time
  const groupActivitiesByTime = (activities: MCPActivity[]) => {
    const groups: { [key: string]: MCPActivity[] } = {};

    activities.forEach(activity => {
      const date = new Date(activity.timestamp);
      const timeKey = date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });

      if (!groups[timeKey]) {
        groups[timeKey] = [];
      }
      groups[timeKey].push(activity);
    });

    return groups;
  };

  const groupedActivities = groupActivitiesByTime(filteredActivities);

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'coordination': 'text-blue-400',
      'execution': 'text-green-400',
      'monitoring': 'text-yellow-400',
      'error': 'text-red-400',
      'system': 'text-purple-400',
      'communication': 'text-cyan-400',
      'default': 'text-gray-400',
    };
    return colors[category?.toLowerCase() || 'default'] || colors.default;
  };

  const getAgentIcon = (agent: string) => {
    const icons: { [key: string]: string } = {
      'master': '🎖️',
      'supervisor': '👨‍💼',
      'backend-api': '⚙️',
      'database': '🗄️',
      'frontend-ui': '🎨',
      'testing': '🧪',
      'instagram': '📷',
      'queue-manager': '📋',
      'deployment': '🚀',
      'default': '🤖',
    };
    return icons[agent.toLowerCase()] || icons.default;
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg flex flex-col h-full">
      {/* Header */}
      <div className="bg-gray-800 px-4 py-3 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-white font-semibold flex items-center">
            <span className={`w-2 h-2 rounded-full mr-2 ${
              connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}></span>
            Activity Stream
            {filteredActivities.length > 0 && (
              <span className="ml-2 text-xs text-gray-400">
                ({filteredActivities.length})
              </span>
            )}
          </h3>
          <button
            onClick={clearActivities}
            className="text-gray-400 hover:text-white text-xs px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 transition-colors"
          >
            Clear
          </button>
        </div>

        {/* Filter */}
        <input
          type="text"
          placeholder="Filter activities..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full px-3 py-1 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Activity List */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3"
      >
        {filteredActivities.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-sm">No activities yet</p>
            <p className="text-xs mt-1">Activities will appear here as agents work</p>
          </div>
        ) : (
          Object.entries(groupedActivities).map(([timeKey, timeActivities]) => (
            <div key={timeKey} className="space-y-2">
              <div className="text-xs text-gray-500 font-semibold">{timeKey}</div>
              {timeActivities.map((activity) => (
                <div
                  key={activity.id}
                  className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50 hover:border-gray-600 transition-colors"
                >
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">{getAgentIcon(activity.agent)}</span>
                      <span className="text-sm font-semibold text-gray-200">
                        {activity.agent}
                      </span>
                      <span className={`ml-2 text-xs ${getCategoryColor(activity.category || activity.type)}`}>
                        [{activity.category || activity.type || 'info'}]
                      </span>
                    </div>
                  </div>

                  <div className="text-sm text-gray-300 ml-8">
                    {activity.action}
                  </div>

                  {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                    <div className="mt-2 ml-8 text-xs text-gray-500 font-mono">
                      {Object.entries(activity.metadata).map(([key, value]) => (
                        <div key={key} className="flex">
                          <span className="text-gray-600">{key}:</span>
                          <span className="ml-1 text-gray-400">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))
        )}
      </div>

      {/* Footer Status */}
      <div className="bg-gray-800 px-4 py-2 border-t border-gray-700 text-xs text-gray-400">
        <div className="flex justify-between items-center">
          <span>
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          <span>
            {autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ActivityStream;