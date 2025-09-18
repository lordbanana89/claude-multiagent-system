import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { config } from '../../config';
import { getErrorMessage } from '../../utils/error-handler';

interface TerminalStatus {
  agent_id: string;
  running: boolean;
  port?: number;
  url?: string;
}

interface TerminalControlsProps {
  agentId: string;
  agentName: string;
  onStatusChange?: (status: TerminalStatus) => void;
}

const TerminalControls: React.FC<TerminalControlsProps> = ({
  agentId,
  agentName,
  onStatusChange
}) => {
  const [status, setStatus] = useState<TerminalStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check terminal status
  const checkStatus = async () => {
    try {
      const response = await axios.get(
        `${config.API_URL}/api/agents/${agentId}/terminal/status`
      );
      setStatus(response.data);
      onStatusChange?.(response.data);
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, [agentId]);

  const startTerminal = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${config.API_URL}/api/agents/${agentId}/terminal/start`
      );
      if (response.data.success) {
        await checkStatus();
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const stopTerminal = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${config.API_URL}/api/agents/${agentId}/terminal/stop`
      );
      if (response.data.success) {
        await checkStatus();
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const openInNewTab = () => {
    if (status?.url) {
      window.open(status.url, '_blank');
    }
  };

  return (
    <div className="p-4 bg-gray-800 border-b border-gray-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div>
            <h3 className="text-sm font-semibold text-white">
              {agentName} Terminal
            </h3>
            <p className="text-xs text-gray-400">
              {status?.running ? (
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></span>
                  Running on port {status.port}
                </span>
              ) : (
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-gray-500 rounded-full mr-1"></span>
                  Stopped
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {status?.running ? (
            <>
              <button
                onClick={openInNewTab}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
              >
                🔗 Open in Tab
              </button>
              <button
                onClick={stopTerminal}
                disabled={loading}
                className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded text-sm"
              >
                {loading ? '⏳' : '⏹️'} Stop
              </button>
            </>
          ) : (
            <button
              onClick={startTerminal}
              disabled={loading}
              className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded text-sm"
            >
              {loading ? '⏳' : '▶️'} Start
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-2 p-2 bg-red-900/50 border border-red-700 rounded text-xs text-red-300">
          {error}
        </div>
      )}
    </div>
  );
};

export default TerminalControls;