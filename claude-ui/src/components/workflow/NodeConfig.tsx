import React, { useState, useEffect } from 'react';
import type { Node } from 'reactflow';

interface NodeConfigProps {
  node: Node;
  onUpdate: (node: Node) => void;
  onClose: () => void;
}

const NodeConfig: React.FC<NodeConfigProps> = ({ node, onUpdate, onClose }) => {
  const [config, setConfig] = useState(node.data.config || {});

  useEffect(() => {
    setConfig(node.data.config || {});
  }, [node]);

  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
  };

  const handleSave = () => {
    const updatedNode = {
      ...node,
      data: {
        ...node.data,
        config: config
      }
    };
    onUpdate(updatedNode);
    onClose();
  };

  const renderConfigField = (key: string, value: any) => {
    // Render different input types based on value type
    if (typeof value === 'boolean') {
      return (
        <div key={key} className="mb-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config[key]}
              onChange={(e) => handleConfigChange(key, e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </label>
        </div>
      );
    }

    if (typeof value === 'number') {
      return (
        <div key={key} className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </label>
          <input
            type="number"
            value={config[key]}
            onChange={(e) => handleConfigChange(key, parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
      );
    }

    // Default to text input
    return (
      <div key={key} className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </label>
        <input
          type="text"
          value={config[key] || ''}
          onChange={(e) => handleConfigChange(key, e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        />
      </div>
    );
  };

  // Special configuration for different node types
  const renderNodeTypeConfig = () => {
    switch (node.data.nodeType) {
      case 'agent':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Agent
              </label>
              <select
                value={config.agentId || ''}
                onChange={(e) => handleConfigChange('agentId', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="">Select Agent...</option>
                <option value="master">Master Agent</option>
                <option value="supervisor">Supervisor Agent</option>
                <option value="backend-api">Backend API Agent</option>
                <option value="database">Database Agent</option>
                <option value="frontend-ui">Frontend UI Agent</option>
                <option value="testing">Testing Agent</option>
                <option value="instagram">Instagram Agent</option>
                <option value="queue-manager">Queue Manager</option>
                <option value="deployment">Deployment Agent</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Command
              </label>
              <textarea
                value={config.command || ''}
                onChange={(e) => handleConfigChange('command', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                placeholder="Enter command to execute..."
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Timeout (ms)
              </label>
              <input
                type="number"
                value={config.timeout || 30000}
                onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          </>
        );

      case 'condition':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Condition Expression
              </label>
              <input
                type="text"
                value={config.condition || ''}
                onChange={(e) => handleConfigChange('condition', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                placeholder="e.g., status === 'success'"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Operator
              </label>
              <select
                value={config.operator || 'equals'}
                onChange={(e) => handleConfigChange('operator', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="equals">Equals (===)</option>
                <option value="not_equals">Not Equals (!==)</option>
                <option value="greater">Greater Than (&gt;)</option>
                <option value="less">Less Than (&lt;)</option>
                <option value="contains">Contains</option>
                <option value="regex">Regex Match</option>
              </select>
            </div>
          </>
        );

      case 'loop':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Items Source
              </label>
              <input
                type="text"
                value={config.items || ''}
                onChange={(e) => handleConfigChange('items', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                placeholder="Variable or array path"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Max Iterations
              </label>
              <input
                type="number"
                value={config.maxIterations || 100}
                onChange={(e) => handleConfigChange('maxIterations', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          </>
        );

      case 'trigger':
        return (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Trigger Type
              </label>
              <select
                value={config.triggerType || 'manual'}
                onChange={(e) => handleConfigChange('triggerType', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="manual">Manual</option>
                <option value="schedule">Schedule</option>
                <option value="webhook">Webhook</option>
                <option value="event">Event</option>
              </select>
            </div>
            {config.triggerType === 'schedule' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cron Expression
                </label>
                <input
                  type="text"
                  value={config.schedule || ''}
                  onChange={(e) => handleConfigChange('schedule', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  placeholder="e.g., 0 */5 * * *"
                />
              </div>
            )}
          </>
        );

      default:
        // Generic config fields
        return Object.keys(config).map(key => renderConfigField(key, config[key]));
    }
  };

  return (
    <div className="w-80 h-full bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Node Configuration
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="mt-2">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {node.data.icon} {node.data.label}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            ID: {node.id}
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Node Name
          </label>
          <input
            type="text"
            value={config.name || node.data.label}
            onChange={(e) => handleConfigChange('name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            value={config.description || ''}
            onChange={(e) => handleConfigChange('description', e.target.value)}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            placeholder="Optional description..."
          />
        </div>

        {/* Node type specific configuration */}
        {renderNodeTypeConfig()}

        {/* Advanced Settings */}
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Advanced Settings
          </summary>
          <div className="mt-2 space-y-2">
            <div className="mb-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.async || false}
                  onChange={(e) => handleConfigChange('async', e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Run asynchronously
                </span>
              </label>
            </div>
            <div className="mb-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.continueOnError || false}
                  onChange={(e) => handleConfigChange('continueOnError', e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Continue on error
                </span>
              </label>
            </div>
          </div>
        </details>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex space-x-2">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
          >
            Save Changes
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 font-medium dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default NodeConfig;