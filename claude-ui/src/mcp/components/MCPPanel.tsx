// MCP Panel - Complete MCP v2 Control Interface
import React, { useState } from 'react';
import MCPStatusCard from './MCPStatusCard';
import ActivityStream from './ActivityStream';
import ToolExecutor from './ToolExecutor';

type MCPTab = 'status' | 'activities' | 'tools';

const MCPPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<MCPTab>('status');

  const tabs = [
    { id: 'status' as const, label: 'Status', icon: '📊' },
    { id: 'activities' as const, label: 'Activities', icon: '📝' },
    { id: 'tools' as const, label: 'Tools', icon: '🔧' },
  ];

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Tab Navigation */}
      <div className="bg-gray-800 border-b border-gray-700 px-4">
        <nav className="flex space-x-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-blue-400'
                  : 'text-gray-400 border-transparent hover:text-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden p-4">
        {activeTab === 'status' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
            <div>
              <MCPStatusCard />
            </div>
            <div className="h-full">
              <ActivityStream maxItems={20} />
            </div>
          </div>
        )}

        {activeTab === 'activities' && (
          <div className="h-full">
            <ActivityStream maxItems={100} />
          </div>
        )}

        {activeTab === 'tools' && (
          <div className="h-full">
            <ToolExecutor />
          </div>
        )}
      </div>
    </div>
  );
};

export default MCPPanel;