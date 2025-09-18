import React from 'react';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  sessionId: string;
  lastActivity: string;
}

interface AgentCardProps {
  agent: Agent;
  isSelected: boolean;
  onClick: () => void;
}

const AgentCard: React.FC<AgentCardProps> = ({ agent, isSelected, onClick }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'busy':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'coordinator':
        return '👥';
      case 'strategic':
        return '🎯';
      case 'development':
        return '💻';
      case 'database':
        return '🗄️';
      case 'ui':
        return '🎨';
      case 'qa':
        return '🧪';
      case 'social':
        return '📱';
      case 'infrastructure':
        return '🏗️';
      case 'devops':
        return '🚀';
      default:
        return '🤖';
    }
  };

  const getAgentColor = (id: string) => {
    const colors: { [key: string]: string } = {
      'supervisor': 'border-agent-supervisor',
      'master': 'border-agent-master',
      'backend-api': 'border-agent-backend',
      'database': 'border-agent-database',
      'frontend-ui': 'border-agent-frontend',
      'testing': 'border-agent-testing',
      'instagram': 'border-agent-instagram',
      'queue-manager': 'border-agent-queue',
      'deployment': 'border-agent-deployment',
    };
    return colors[agent.id] || 'border-gray-300';
  };

  return (
    <div
      onClick={onClick}
      className={`
        bg-white dark:bg-gray-800 rounded-lg p-4 cursor-pointer
        border-2 transition-all hover:shadow-lg
        ${isSelected ? 'ring-2 ring-primary-500 border-primary-500' : getAgentColor(agent.id)}
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getAgentIcon(agent.type)}</span>
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">
              {agent.name}
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {agent.id}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`}></span>
          <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
            {agent.status}
          </span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Session: {agent.sessionId}</span>
          <span>{new Date(agent.lastActivity).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default AgentCard;