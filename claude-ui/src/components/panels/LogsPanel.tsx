import React, { useState, useEffect, useRef } from 'react';
import type { Log } from '../../context/AppContext';

interface LogsPanelProps {
  logs: Log[];
  selectedAgent: any;
  agents: any[];
}

const LogsPanel: React.FC<LogsPanelProps> = ({ logs, selectedAgent, agents }) => {
  const [filter, setFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const [selectedLogAgent, setSelectedLogAgent] = useState(selectedAgent?.id || 'all');
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Update selected agent when prop changes
  useEffect(() => {
    if (selectedAgent?.id) {
      setSelectedLogAgent(selectedAgent.id);
    }
  }, [selectedAgent]);

  const exportLogs = () => {
    const logText = filteredLogs
      .map(log => `[${log.timestamp}] [${log.level.toUpperCase()}] [${log.agent}] ${log.message}`)
      .join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      case 'debug': return 'text-gray-500';
      default: return 'text-gray-300';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'debug': return '🔍';
      default: return 'ℹ️';
    }
  };

  // Filter logs
  const filteredLogs = logs.filter(log => {
    if (filter !== 'all' && log.level.toLowerCase() !== filter) return false;
    if (selectedLogAgent !== 'all' && log.agent !== selectedLogAgent) return false;
    return true;
  });

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white">System Logs</h2>
          <div className="flex items-center gap-3">
            <label className="flex items-center text-sm text-gray-400">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="mr-2"
              />
              Auto-scroll
            </label>
            <button
              onClick={exportLogs}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white"
            >
              📥 Export
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Level</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-1 bg-gray-700 text-white rounded text-sm border border-gray-600"
            >
              <option value="all">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="debug">Debug</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Agent</label>
            <select
              value={selectedLogAgent}
              onChange={(e) => setSelectedLogAgent(e.target.value)}
              className="px-3 py-1 bg-gray-700 text-white rounded text-sm border border-gray-600"
            >
              <option value="all">All Agents</option>
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Logs Content */}
      <div className="flex-1 overflow-auto p-4 font-mono text-sm">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="text-2xl mb-2">📄</div>
            <p>No logs found</p>
            <p className="text-xs mt-1">Try adjusting your filters</p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={`${log.id}-${index}`}
                className="flex items-start gap-3 p-2 rounded hover:bg-gray-800/50 group"
              >
                <span className="text-xs text-gray-500 shrink-0 w-20">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>

                <span className="shrink-0 w-6 text-center">
                  {getLevelIcon(log.level)}
                </span>

                <span className={`shrink-0 w-3 font-bold ${getLevelColor(log.level)}`}>
                  {log.level.toUpperCase().charAt(0)}
                </span>

                <span className="text-blue-400 shrink-0 min-w-0 w-24 truncate">
                  {log.agent}
                </span>

                <span className="text-gray-300 flex-1 break-words">
                  {log.message}
                </span>

                {log.details && (
                  <button
                    className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-gray-300"
                    title="Show details"
                  >
                    🔍
                  </button>
                )}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="bg-gray-800 border-t border-gray-700 p-2 text-xs text-gray-400">
        <div className="flex justify-between items-center">
          <span>
            Showing {filteredLogs.length} of {logs.length} logs
          </span>
          <span>
            {filteredLogs.length > 0 && `Latest: ${new Date(filteredLogs[filteredLogs.length - 1]?.timestamp).toLocaleTimeString()}`}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LogsPanel;