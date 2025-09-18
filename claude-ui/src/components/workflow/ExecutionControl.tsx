import React, { useState, useEffect } from 'react';
import type { Node } from 'reactflow';
import axios from 'axios';
import { config } from '../../config';

interface ExecutionControlProps {
  onExecute: () => void;
  isExecuting: boolean;
  nodes: Node[];
}

interface ExecutionLog {
  id: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  nodeId?: string;
}

const ExecutionControl: React.FC<ExecutionControlProps> = ({
  onExecute,
  isExecuting,
  nodes
}) => {
  const [executionLogs, setExecutionLogs] = useState<ExecutionLog[]>([]);
  const [executionProgress, setExecutionProgress] = useState(0);
  const [showLogs, setShowLogs] = useState(false);
  const [executionMode, setExecutionMode] = useState<'sequential' | 'parallel'>('sequential');
  const [executionSpeed, setExecutionSpeed] = useState<'slow' | 'normal' | 'fast'>('normal');

  const speedMap = {
    slow: 2000,
    normal: 1000,
    fast: 500
  };

  const addLog = (type: ExecutionLog['type'], message: string, nodeId?: string) => {
    const log: ExecutionLog = {
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      type,
      message,
      nodeId
    };
    setExecutionLogs(prev => [...prev, log]);
  };

  const handleExecute = async () => {
    setExecutionLogs([]);
    setExecutionProgress(0);
    addLog('info', 'Starting workflow execution...');

    try {
      // Send workflow to backend for execution
      const response = await axios.post(`${config.API_URL}/api/workflows/execute`, {
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          data: n.data
        })),
        mode: executionMode,
        speed: speedMap[executionSpeed]
      });

      addLog('success', `Workflow execution started: ${response.data.executionId}`);
      onExecute();

      // Simulate progress
      const totalNodes = nodes.length;
      for (let i = 0; i < totalNodes; i++) {
        const progress = ((i + 1) / totalNodes) * 100;
        setExecutionProgress(progress);

        const node = nodes[i];
        addLog('info', `Executing node: ${node.data.label}`, node.id);

        await new Promise(resolve => setTimeout(resolve, speedMap[executionSpeed]));

        addLog('success', `Node completed: ${node.data.label}`, node.id);
      }

      addLog('success', 'Workflow execution completed successfully!');
    } catch (error: any) {
      addLog('error', `Execution failed: ${error.message}`);
    } finally {
      setExecutionProgress(100);
    }
  };

  const handleStop = () => {
    addLog('warning', 'Execution stopped by user');
    // TODO: Implement actual stop logic
  };

  const handlePause = () => {
    addLog('info', 'Execution paused');
    // TODO: Implement pause logic
  };

  const clearLogs = () => {
    setExecutionLogs([]);
  };

  const getLogIcon = (type: ExecutionLog['type']) => {
    switch (type) {
      case 'info': return 'ℹ️';
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
    }
  };

  const getLogColor = (type: ExecutionLog['type']) => {
    switch (type) {
      case 'info': return 'text-blue-600 dark:text-blue-400';
      case 'success': return 'text-green-600 dark:text-green-400';
      case 'warning': return 'text-yellow-600 dark:text-yellow-400';
      case 'error': return 'text-red-600 dark:text-red-400';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
      {/* Control Bar */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          {/* Execution Controls */}
          <div className="flex items-center space-x-3">
            {!isExecuting ? (
              <button
                onClick={handleExecute}
                disabled={nodes.length === 0}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  nodes.length === 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                ▶️ Execute
              </button>
            ) : (
              <>
                <button
                  onClick={handlePause}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 font-medium"
                >
                  ⏸️ Pause
                </button>
                <button
                  onClick={handleStop}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
                >
                  ⏹️ Stop
                </button>
              </>
            )}

            {/* Execution Mode */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Mode:
              </label>
              <select
                value={executionMode}
                onChange={(e) => setExecutionMode(e.target.value as any)}
                disabled={isExecuting}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="sequential">Sequential</option>
                <option value="parallel">Parallel</option>
              </select>
            </div>

            {/* Execution Speed */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Speed:
              </label>
              <select
                value={executionSpeed}
                onChange={(e) => setExecutionSpeed(e.target.value as any)}
                disabled={isExecuting}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="slow">Slow</option>
                <option value="normal">Normal</option>
                <option value="fast">Fast</option>
              </select>
            </div>
          </div>

          {/* Progress and Stats */}
          <div className="flex items-center space-x-4">
            {/* Progress Bar */}
            {isExecuting && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Progress:</span>
                <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-500"
                    style={{ width: `${executionProgress}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {Math.round(executionProgress)}%
                </span>
              </div>
            )}

            {/* Workflow Stats */}
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">{nodes.length}</span> nodes
            </div>

            {/* Toggle Logs */}
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              {showLogs ? '📜 Hide Logs' : '📜 Show Logs'}
              {executionLogs.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-600 text-white rounded-full">
                  {executionLogs.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Execution Logs */}
      {showLogs && (
        <div className="max-h-64 overflow-y-auto bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Execution Logs
              </h4>
              <button
                onClick={clearLogs}
                className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                Clear
              </button>
            </div>

            {executionLogs.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                No logs yet. Execute the workflow to see logs.
              </p>
            ) : (
              <div className="space-y-1">
                {executionLogs.map(log => (
                  <div
                    key={log.id}
                    className="flex items-start space-x-2 text-sm font-mono"
                  >
                    <span className="text-gray-500 dark:text-gray-400 text-xs">
                      {log.timestamp}
                    </span>
                    <span>{getLogIcon(log.type)}</span>
                    <span className={`flex-1 ${getLogColor(log.type)}`}>
                      {log.message}
                      {log.nodeId && (
                        <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                          (Node: {log.nodeId})
                        </span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-3">
          <button
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            onClick={() => console.log('Validate workflow')}
          >
            🔍 Validate
          </button>
          <button
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            onClick={() => console.log('Debug mode')}
          >
            🐛 Debug
          </button>
          <button
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            onClick={() => console.log('Schedule execution')}
          >
            ⏰ Schedule
          </button>
        </div>
        <div className="text-gray-500 dark:text-gray-400">
          Last execution: {executionLogs.length > 0 ? executionLogs[executionLogs.length - 1].timestamp : 'Never'}
        </div>
      </div>
    </div>
  );
};

export default ExecutionControl;