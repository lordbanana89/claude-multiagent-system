import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import MultiTerminal from '../terminal/MultiTerminal';
import TerminalPanel from '../panels/TerminalPanel';
import InboxPanel from '../panels/InboxPanel';
import QueuePanel from '../panels/QueuePanel';
import TaskExecutor from '../panels/TaskExecutor';

type OperationTab = 'terminals' | 'multi-terminal' | 'inbox' | 'queue' | 'executor';

const OperationsView: React.FC = () => {
  const { state } = useApp();
  const [activeTab, setActiveTab] = useState<OperationTab>('terminals');
  const [selectedAgent, setSelectedAgent] = useState(state.selectedAgent);

  const tabs = [
    { id: 'terminals' as const, label: 'Terminal', icon: '💻' },
    { id: 'multi-terminal' as const, label: 'Multi-Terminal', icon: '🖥️' },
    { id: 'inbox' as const, label: 'Inbox', icon: '📨' },
    { id: 'queue' as const, label: 'Queue', icon: '📋' },
    { id: 'executor' as const, label: 'Task Executor', icon: '⚡' },
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

      {/* Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Agent List */}
        {activeTab !== 'multi-terminal' && (
          <aside className="w-64 md:w-72 lg:w-80 bg-gray-800 border-r border-gray-700 p-4 flex-shrink-0">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Agents
            </h3>
            <div className="space-y-2">
              {state.agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className={`w-full p-3 rounded-lg text-left transition-all duration-200 border ${
                    selectedAgent?.id === agent.id
                      ? 'bg-blue-600 text-white border-blue-500 shadow-lg scale-102'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium truncate">{agent.name}</span>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          agent.status === 'online'
                            ? 'bg-green-400 animate-pulse'
                            : agent.status === 'busy'
                            ? 'bg-yellow-400 animate-pulse'
                            : 'bg-gray-500'
                        }`}
                      />
                    </div>
                  </div>
                  <div className="text-xs mt-1 opacity-75 flex items-center">
                    <span className="mr-2">🤖</span>
                    <span className="truncate">{agent.type}</span>
                    <span className="mx-1">•</span>
                    <span className={`font-medium ${
                      agent.status === 'online' ? 'text-green-300' :
                      agent.status === 'busy' ? 'text-yellow-300' : 'text-gray-400'
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                </button>
              ))}
            </div>

            {/* Quick Stats */}
            <div className="mt-6 pt-6 border-t border-gray-700">
              <h4 className="text-xs font-semibold text-gray-400 uppercase mb-3">
                System Stats
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-gray-300">
                  <span>Online</span>
                  <span className="text-green-400">
                    {state.agents.filter((a) => a.status === 'online').length}
                  </span>
                </div>
                <div className="flex justify-between text-gray-300">
                  <span>Busy</span>
                  <span className="text-yellow-400">
                    {state.agents.filter((a) => a.status === 'busy').length}
                  </span>
                </div>
                <div className="flex justify-between text-gray-300">
                  <span>Offline</span>
                  <span className="text-gray-400">
                    {state.agents.filter((a) => a.status === 'offline').length}
                  </span>
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 bg-gray-900 overflow-hidden">
          {activeTab === 'terminals' && (
            <TerminalPanel
              selectedAgent={selectedAgent}
              agents={state.agents}
            />
          )}

          {activeTab === 'multi-terminal' && (
            <MultiTerminal agents={state.agents} />
          )}

          {activeTab === 'inbox' && (
            <InboxPanel
              messages={state.messages}
              agents={state.agents}
              selectedAgent={selectedAgent}
            />
          )}

          {activeTab === 'queue' && (
            <QueuePanel
              tasks={state.tasks}
              queueStatus={state.queueStatus}
              agents={state.agents}
            />
          )}

          {activeTab === 'executor' && (
            <div className="h-full p-6">
              <TaskExecutor
                agents={state.agents}
                selectedAgent={selectedAgent}
                onSelectAgent={setSelectedAgent}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default OperationsView;