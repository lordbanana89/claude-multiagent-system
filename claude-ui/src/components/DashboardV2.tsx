import React, { useState, useEffect } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { AppProvider, useApp } from '../context/AppContext';

// Views
import WorkflowView from './workflow/WorkflowView';
import OperationsView from './views/OperationsView';
import MonitoringView from './views/MonitoringView';

// Components
import NotificationToast from './ui/NotificationToast';
import LoadingOverlay from './ui/LoadingOverlay';

const DashboardCore: React.FC = () => {
  const { state, dispatch, notify } = useApp();
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize
  useEffect(() => {
    if (!isInitialized) {
      notify('info', 'Dashboard loading...');
      setIsInitialized(true);
    }
  }, [isInitialized, notify]);

  // Render active view
  const renderView = () => {
    switch (state.activeView) {
      case 'workflow':
        return (
          <WorkflowView
            agents={state.agents}
            mode={state.workflowMode}
            onModeChange={(mode) =>
              dispatch({ type: 'SET_WORKFLOW_MODE', payload: mode })
            }
          />
        );

      case 'operations':
        return <OperationsView />;

      case 'monitoring':
        return <MonitoringView />;

      default:
        return null;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Compact Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-white flex items-center">
              <span className="mr-2 text-blue-500">🎯</span>
              Multi-Agent System
            </h1>

            {/* System Status */}
            <div className="flex items-center space-x-3 text-sm">
              <div className={`flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                state.systemHealth?.status === 'healthy'
                  ? 'bg-green-900/50 text-green-300 border border-green-700'
                  : state.systemHealth?.status === 'degraded'
                  ? 'bg-yellow-900/50 text-yellow-300 border border-yellow-700'
                  : 'bg-red-900/50 text-red-300 border border-red-700'
              }`}>
                <span className={`w-2 h-2 rounded-full mr-2 ${
                  state.systemHealth?.status === 'healthy'
                    ? 'bg-green-400 animate-pulse'
                    : state.systemHealth?.status === 'degraded'
                    ? 'bg-yellow-400 animate-pulse'
                    : 'bg-red-400 animate-pulse'
                }`}></span>
                {state.systemHealth?.status?.toUpperCase() || 'CHECKING...'}
              </div>

              <div className="bg-gray-700/50 px-3 py-1 rounded-full text-xs font-medium border border-gray-600">
                <span className="text-gray-400 mr-1">Agents:</span>
                <span className="text-green-400 font-bold">
                  {state.agents.filter(a => a.status === 'online').length}
                </span>
                <span className="text-gray-400 mx-1">/</span>
                <span className="text-gray-300">{state.agents.length}</span>
              </div>

              {state.wsConnected && (
                <div className="bg-green-900/50 text-green-300 px-3 py-1 rounded-full text-xs font-medium border border-green-700">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2 inline-block animate-pulse"></span>
                  WebSocket
                </div>
              )}
            </div>
          </div>

          {/* View Switcher */}
          <nav className="flex items-center bg-gray-700/30 rounded-lg p-1 border border-gray-600">
            <button
              onClick={() => dispatch({ type: 'SET_ACTIVE_VIEW', payload: 'workflow' })}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                state.activeView === 'workflow'
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'text-gray-300 hover:bg-gray-600/50 hover:text-white'
              }`}
            >
              <span className="mr-2">🔄</span>
              Workflow
            </button>

            <button
              onClick={() => dispatch({ type: 'SET_ACTIVE_VIEW', payload: 'operations' })}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                state.activeView === 'operations'
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'text-gray-300 hover:bg-gray-600/50 hover:text-white'
              }`}
            >
              <span className="mr-2">⚙️</span>
              Operations
            </button>

            <button
              onClick={() => dispatch({ type: 'SET_ACTIVE_VIEW', payload: 'monitoring' })}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                state.activeView === 'monitoring'
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'text-gray-300 hover:bg-gray-600/50 hover:text-white'
              }`}
            >
              <span className="mr-2">📊</span>
              Monitoring
            </button>
          </nav>
        </div>
      </header>

      {/* Error Banner */}
      {state.error && (
        <div className="bg-red-900/50 border-b border-red-500 px-4 py-2 flex items-center justify-between">
          <span className="text-red-200 text-sm">{state.error}</span>
          <button
            onClick={() => dispatch({ type: 'SET_ERROR', payload: null })}
            className="text-red-400 hover:text-red-200"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {renderView()}
      </main>

      {/* Status Bar */}
      <footer className="bg-gray-800 border-t border-gray-700 px-4 py-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-gray-400">Queue:</span>
              <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded font-medium">
                {state.queueStatus?.pending || 0} pending
              </span>
              <span className="px-2 py-1 bg-yellow-900/50 text-yellow-300 rounded font-medium">
                {state.queueStatus?.processing || 0} processing
              </span>
              <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded font-medium">
                {state.queueStatus?.completed || 0} completed
              </span>
              {(state.queueStatus?.failed || 0) > 0 && (
                <span className="px-2 py-1 bg-red-900/50 text-red-300 rounded font-medium">
                  {state.queueStatus?.failed} failed
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-4 text-gray-400">
            <div className="flex items-center space-x-2">
              <span>Data:</span>
              <span className="text-blue-300">{state.logs.length} logs</span>
              <span className="text-green-300">{state.messages.length} messages</span>
              <span className="text-yellow-300">{state.tasks.length} tasks</span>
            </div>
            <span className="text-gray-500">|</span>
            <span className="font-mono">{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </footer>

      {/* Loading Overlay */}
      {state.loading && <LoadingOverlay />}

      {/* Notifications */}
      <NotificationToast notifications={state.notifications} />
    </div>
  );
};

// Main Dashboard with Providers
const DashboardV2: React.FC = () => {
  return (
    <AppProvider>
      <ReactFlowProvider>
        <DashboardCore />
      </ReactFlowProvider>
    </AppProvider>
  );
};

export default DashboardV2;