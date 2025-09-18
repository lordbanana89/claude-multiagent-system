import React, { useState, useEffect, useRef } from 'react';
import { config, getTerminalUrl } from '../../config';

interface TerminalPanelProps {
  selectedAgent: any;
  agents: any[];
}

const TerminalPanel: React.FC<TerminalPanelProps> = ({ selectedAgent, agents }) => {
  const [terminalAgent, setTerminalAgent] = useState(selectedAgent);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (selectedAgent) {
      setTerminalAgent(selectedAgent);
    }
  }, [selectedAgent]);

  const getTerminalPort = (agentId: string): string => {
    return getTerminalUrl(agentId as any);
  };

  const handleAgentSelect = (agent: any) => {
    setTerminalAgent(agent);
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Terminal Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">
            Terminal - {terminalAgent?.name || 'No Agent Selected'}
          </h2>
          <div className="flex gap-2">
            {agents.map(agent => (
              <button
                key={agent.id}
                onClick={() => handleAgentSelect(agent)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  terminalAgent?.id === agent.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {agent.name.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Terminal Content */}
      <div className="flex-1 relative">
        {terminalAgent ? (
          <iframe
            ref={iframeRef}
            src={getTerminalPort(terminalAgent.id)}
            className="w-full h-full bg-black"
            title={`Terminal for ${terminalAgent.name}`}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-gray-400 mb-4">No agent selected</p>
              <p className="text-gray-500 text-sm">Select an agent to view its terminal</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TerminalPanel;