import React, { useState } from 'react';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: string;
}

interface CommandHistory {
  agentId: string;
  command: string;
  timestamp: string;
  status: 'sent' | 'completed' | 'error';
}

interface CommandPanelProps {
  selectedAgent: Agent | null;
  onSendCommand: (command: string) => void;
  isLoading: boolean;
  commandHistory: CommandHistory[];
}

const CommandPanel: React.FC<CommandPanelProps> = ({
  selectedAgent,
  onSendCommand,
  isLoading,
  commandHistory
}) => {
  const [command, setCommand] = useState('');

  const predefinedCommands = [
    { label: 'Status Check', command: 'status' },
    { label: 'Run Tests', command: 'run tests' },
    { label: 'Build Project', command: 'build' },
    { label: 'Deploy', command: 'deploy' },
    { label: 'Check Logs', command: 'logs --tail 50' },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim() && selectedAgent) {
      onSendCommand(command);
      setCommand('');
    }
  };

  const handlePredefinedCommand = (cmd: string) => {
    setCommand(cmd);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 sticky top-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Command Panel
      </h3>

      {selectedAgent ? (
        <>
          <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-sm text-gray-600 dark:text-gray-400">Selected Agent:</div>
            <div className="font-semibold text-gray-900 dark:text-white">
              {selectedAgent.name}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              ID: {selectedAgent.id} | Status: {selectedAgent.status}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mb-4">
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Command
              </label>
              <textarea
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={3}
                placeholder="Enter command..."
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !command.trim()}
              className={`w-full py-2 px-4 rounded-md font-medium transition-colors
                ${isLoading || !command.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-700'
                }`}
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending...
                </span>
              ) : (
                'Send Command'
              )}
            </button>
          </form>

          <div className="mb-4">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Quick Commands
            </div>
            <div className="grid grid-cols-2 gap-2">
              {predefinedCommands.map((cmd) => (
                <button
                  key={cmd.label}
                  onClick={() => handlePredefinedCommand(cmd.command)}
                  className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300
                           rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  {cmd.label}
                </button>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          Select an agent to send commands
        </div>
      )}

      {/* Command History */}
      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          Recent Commands
        </h4>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {commandHistory.length > 0 ? (
            commandHistory.map((item, index) => (
              <div
                key={index}
                className={`text-xs p-2 rounded ${
                  item.status === 'error'
                    ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                    : 'bg-gray-50 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <span className="font-medium">{item.agentId}:</span> {item.command}
                  </div>
                  <span className={`ml-2 ${
                    item.status === 'sent' ? 'text-blue-500' :
                    item.status === 'completed' ? 'text-green-500' :
                    'text-red-500'
                  }`}>
                    {item.status === 'sent' ? '📤' :
                     item.status === 'completed' ? '✅' : '❌'}
                  </span>
                </div>
                <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          ) : (
            <div className="text-xs text-gray-500 dark:text-gray-400 text-center py-4">
              No commands sent yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CommandPanel;