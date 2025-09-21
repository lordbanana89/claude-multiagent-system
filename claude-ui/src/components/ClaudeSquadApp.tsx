import React, { useState, useEffect } from 'react';
import integrationService from '../services/integration';
import {
  Brain,
  Home,
  Users,
  Activity,
  Settings,
  Zap,
  MessageSquare,
  BarChart3,
  GitBranch,
  Sparkles,
  Layers,
  Terminal
} from 'lucide-react';

// Import all our components
import Dashboard from './Dashboard';
import MCPDashboard from './MCPDashboard';
import AgentBuilder from './AgentBuilder';
import KnowledgeGraph from './KnowledgeGraph';
import CompleteDashboard from './CompleteDashboard';
import MultiTerminal from './terminal/MultiTerminal';
import SystemMonitor from './monitoring/SystemMonitor';
import InboxSystem from './inbox/InboxSystem';
import QueueMonitor from './queue/QueueMonitor';
import WorkflowCanvas from './workflow/WorkflowCanvas';

type ViewType =
  | 'overview'
  | 'agents'
  | 'builder'
  | 'knowledge'
  | 'monitoring'
  | 'inbox'
  | 'queue'
  | 'workflow'
  | 'terminal'
  | 'mcp'
  | 'analytics';

interface NavItem {
  id: ViewType;
  label: string;
  icon: React.ReactNode;
  description: string;
  badge?: string;
}

const ClaudeSquadApp: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [integrationStatus, setIntegrationStatus] = useState<string>('checking');

  useEffect(() => {
    // Start health monitoring
    integrationService.startHealthMonitoring((health) => {
      setSystemHealth(health);

      // Update integration status
      if (health.database && health.redis && health.api) {
        setIntegrationStatus('connected');
      } else {
        setIntegrationStatus('partial');
      }
    }, 5000);

    // Initial sync
    integrationService.syncAll();

    return () => {
      integrationService.stopHealthMonitoring();
    };
  }, []);

  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: <Home className="w-5 h-5" />, description: 'System overview' },
    { id: 'agents', label: 'Agent Orchestra', icon: <Users className="w-5 h-5" />, description: 'Manage agents', badge: '9' },
    { id: 'builder', label: 'Agent Builder', icon: <Sparkles className="w-5 h-5" />, description: 'Create custom agents', badge: 'NEW' },
    { id: 'knowledge', label: 'Knowledge Graph', icon: <Brain className="w-5 h-5" />, description: 'AI knowledge base' },
    { id: 'workflow', label: 'Workflow Designer', icon: <GitBranch className="w-5 h-5" />, description: 'Design workflows' },
    { id: 'monitoring', label: 'Monitoring', icon: <Activity className="w-5 h-5" />, description: 'System metrics' },
    { id: 'inbox', label: 'Agent Inbox', icon: <MessageSquare className="w-5 h-5" />, description: 'Messages' },
    { id: 'queue', label: 'Task Queue', icon: <Layers className="w-5 h-5" />, description: 'Queue management' },
    { id: 'terminal', label: 'Terminals', icon: <Terminal className="w-5 h-5" />, description: 'Agent terminals' },
    { id: 'mcp', label: 'MCP Protocol', icon: <Zap className="w-5 h-5" />, description: 'MCP status' },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 className="w-5 h-5" />, description: 'Performance' },
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'overview':
        return <Dashboard />;
      case 'agents':
        return <CompleteDashboard />;
      case 'builder':
        return <AgentBuilder />;
      case 'knowledge':
        return <KnowledgeGraph />;
      case 'workflow':
        return <WorkflowCanvas />;
      case 'monitoring':
        return <SystemMonitor />;
      case 'inbox':
        return <InboxSystem />;
      case 'queue':
        return <QueueMonitor />;
      case 'terminal':
        return <MultiTerminal agents={[]} />;
      case 'mcp':
        return <MCPDashboard />;
      case 'analytics':
        return <SystemMonitor />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="h-screen flex bg-gray-900">
      {/* Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-gray-800 border-r border-gray-700 transition-all duration-300`}>
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-700">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-2">
              <div className="text-2xl">🚀</div>
              <div>
                <div className="text-white font-bold">Claude Squad</div>
                <div className="text-xs text-gray-400">Superior to MeetSquad</div>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="text-gray-400 hover:text-white"
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`w-full flex items-center ${
                sidebarCollapsed ? 'justify-center' : 'justify-between'
              } px-3 py-2.5 mb-1 rounded-lg transition-all ${
                currentView === item.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
              title={sidebarCollapsed ? item.label : undefined}
            >
              <div className="flex items-center space-x-3">
                {item.icon}
                {!sidebarCollapsed && (
                  <div className="text-left">
                    <div className="text-sm font-medium">{item.label}</div>
                    <div className="text-xs opacity-70">{item.description}</div>
                  </div>
                )}
              </div>
              {!sidebarCollapsed && item.badge && (
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  item.badge === 'NEW'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-blue-500/20 text-blue-400'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Bottom Section */}
        {!sidebarCollapsed && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-3">
              <div className="text-white text-sm font-semibold mb-1">🎯 Pro Tip</div>
              <div className="text-white/80 text-xs">
                Use Agent Builder to create custom agents that outperform any competitor!
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-gray-800 border-b border-gray-700 px-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">
              {navItems.find(item => item.id === currentView)?.label}
            </h1>
            <p className="text-xs text-gray-400">
              {navItems.find(item => item.id === currentView)?.description}
            </p>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm flex items-center space-x-2">
              <Sparkles className="w-4 h-4" />
              <span>Quick Deploy</span>
            </button>
            <button className="p-2 text-gray-400 hover:text-white">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto bg-gray-900">
          {renderContent()}
        </main>

        {/* Status Bar */}
        <div className="h-8 bg-gray-800 border-t border-gray-700 px-4 flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <span className={`w-2 h-2 rounded-full animate-pulse ${
                integrationStatus === 'connected' ? 'bg-green-500' :
                integrationStatus === 'partial' ? 'bg-yellow-500' :
                'bg-red-500'
              }`}></span>
              <span>Integration: {integrationStatus}</span>
            </span>
            {systemHealth && (
              <>
                <span>DB: {systemHealth.database ? '✅' : '❌'}</span>
                <span>Redis: {systemHealth.redis ? '✅' : '❌'}</span>
                <span>API: {systemHealth.api ? '✅' : '❌'}</span>
                <span>Agents: {Object.values(systemHealth.agents || {}).filter(Boolean).length}/9</span>
              </>
            )}
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => integrationService.autoFixServices()}
              className="text-blue-400 hover:text-blue-300"
            >
              Auto-Fix Issues
            </button>
            <span>v2.0.0</span>
            <span>Superior to MeetSquad.ai</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClaudeSquadApp;