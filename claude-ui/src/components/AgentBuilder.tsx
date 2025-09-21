import React, { useState } from 'react';
import { Brain, Code, Database, Globe, TestTube, Camera, Package, Rocket, Save, Play, Zap } from 'lucide-react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import axios from 'axios';
import { config } from '../config';
import integrationService from '../services/integration';

interface AgentSkill {
  id: string;
  name: string;
  type: string;
  icon: React.ReactNode;
  description: string;
  parameters?: any;
}

interface CustomAgent {
  id: string;
  name: string;
  description: string;
  icon: string;
  skills: AgentSkill[];
  knowledge: string[];
  triggers: string[];
  outputs: string[];
}

const availableSkills: AgentSkill[] = [
  { id: 'code-gen', name: 'Code Generation', type: 'development', icon: <Code />, description: 'Generate code in any language' },
  { id: 'api-design', name: 'API Design', type: 'backend', icon: <Globe />, description: 'Design RESTful APIs' },
  { id: 'db-schema', name: 'Database Schema', type: 'database', icon: <Database />, description: 'Design database schemas' },
  { id: 'testing', name: 'Automated Testing', type: 'qa', icon: <TestTube />, description: 'Create and run tests' },
  { id: 'ui-gen', name: 'UI Generation', type: 'frontend', icon: <Package />, description: 'Generate UI components' },
  { id: 'social', name: 'Social Media', type: 'marketing', icon: <Camera />, description: 'Social media automation' },
  { id: 'deploy', name: 'Deployment', type: 'devops', icon: <Rocket />, description: 'Deploy to cloud' },
  { id: 'analyze', name: 'Data Analysis', type: 'analytics', icon: <Brain />, description: 'Analyze data and metrics' },
];

const SkillCard: React.FC<{ skill: AgentSkill; onAdd?: (skill: AgentSkill) => void }> = ({ skill, onAdd }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'skill',
    item: skill,
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }));

  return (
    <div
      ref={drag as any}
      className={`p-3 bg-gray-700 rounded-lg cursor-move transition-all ${
        isDragging ? 'opacity-50' : 'hover:bg-gray-600'
      }`}
      onClick={() => onAdd?.(skill)}
    >
      <div className="flex items-center space-x-2">
        <div className="text-blue-400">{skill.icon}</div>
        <div>
          <div className="text-sm font-medium text-white">{skill.name}</div>
          <div className="text-xs text-gray-400">{skill.description}</div>
        </div>
      </div>
    </div>
  );
};

const AgentCanvas: React.FC<{ agent: CustomAgent; onUpdate: (agent: CustomAgent) => void }> = ({ agent, onUpdate }) => {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: 'skill',
    drop: (item: AgentSkill) => {
      if (!agent.skills.find(s => s.id === item.id)) {
        onUpdate({
          ...agent,
          skills: [...agent.skills, item]
        });
      }
    },
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
    }),
  }));

  const removeSkill = (skillId: string) => {
    onUpdate({
      ...agent,
      skills: agent.skills.filter(s => s.id !== skillId)
    });
  };

  return (
    <div
      ref={drop as any}
      className={`flex-1 bg-gray-800 rounded-lg p-6 transition-all ${
        isOver ? 'ring-2 ring-blue-500' : ''
      }`}
    >
      <h3 className="text-lg font-semibold text-white mb-4">Agent Configuration</h3>

      {/* Agent Name & Description */}
      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Agent Name</label>
          <input
            type="text"
            value={agent.name}
            onChange={(e) => onUpdate({ ...agent, name: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="My Custom Agent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
          <textarea
            value={agent.description}
            onChange={(e) => onUpdate({ ...agent, description: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded-md focus:ring-2 focus:ring-blue-500"
            rows={3}
            placeholder="What does this agent do?"
          />
        </div>
      </div>

      {/* Skills */}
      <div>
        <h4 className="text-sm font-medium text-gray-400 mb-2">Skills (Drop here or click to add)</h4>
        <div className="min-h-[100px] bg-gray-900 rounded-lg p-4 space-y-2">
          {agent.skills.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              Drag skills here to add them to your agent
            </div>
          ) : (
            agent.skills.map(skill => (
              <div key={skill.id} className="flex items-center justify-between bg-gray-800 p-2 rounded">
                <div className="flex items-center space-x-2">
                  <div className="text-blue-400">{skill.icon}</div>
                  <span className="text-sm text-white">{skill.name}</span>
                </div>
                <button
                  onClick={() => removeSkill(skill.id)}
                  className="text-red-400 hover:text-red-300"
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Knowledge Base */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-400 mb-2">Knowledge Base</h4>
        <textarea
          value={agent.knowledge.join('\n')}
          onChange={(e) => onUpdate({ ...agent, knowledge: e.target.value.split('\n').filter(k => k) })}
          className="w-full px-3 py-2 bg-gray-700 text-white rounded-md focus:ring-2 focus:ring-blue-500"
          rows={3}
          placeholder="Enter knowledge items, one per line..."
        />
      </div>

      {/* Triggers */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-400 mb-2">Triggers</h4>
        <div className="space-y-2">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={agent.triggers.includes('manual')}
              onChange={(e) => {
                if (e.target.checked) {
                  onUpdate({ ...agent, triggers: [...agent.triggers, 'manual'] });
                } else {
                  onUpdate({ ...agent, triggers: agent.triggers.filter(t => t !== 'manual') });
                }
              }}
              className="rounded text-blue-500"
            />
            <span className="text-sm text-white">Manual Trigger</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={agent.triggers.includes('webhook')}
              onChange={(e) => {
                if (e.target.checked) {
                  onUpdate({ ...agent, triggers: [...agent.triggers, 'webhook'] });
                } else {
                  onUpdate({ ...agent, triggers: agent.triggers.filter(t => t !== 'webhook') });
                }
              }}
              className="rounded text-blue-500"
            />
            <span className="text-sm text-white">Webhook</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={agent.triggers.includes('schedule')}
              onChange={(e) => {
                if (e.target.checked) {
                  onUpdate({ ...agent, triggers: [...agent.triggers, 'schedule'] });
                } else {
                  onUpdate({ ...agent, triggers: agent.triggers.filter(t => t !== 'schedule') });
                }
              }}
              className="rounded text-blue-500"
            />
            <span className="text-sm text-white">Scheduled (Cron)</span>
          </label>
        </div>
      </div>
    </div>
  );
};

const AgentBuilder: React.FC = () => {
  const [customAgent, setCustomAgent] = useState<CustomAgent>({
    id: `agent-${Date.now()}`,
    name: '',
    description: '',
    icon: '🤖',
    skills: [],
    knowledge: [],
    triggers: ['manual'],
    outputs: ['json', 'webhook']
  });

  const [savedAgents, setSavedAgents] = useState<CustomAgent[]>([]);
  const [isDeploying, setIsDeploying] = useState(false);

  const handleSaveAgent = async () => {
    if (!customAgent.name || customAgent.skills.length === 0) {
      alert('Please provide a name and at least one skill for your agent');
      return;
    }

    try {
      // Save through integration service
      const response = await axios.post(`${config.API_URL}/api/agents/custom`, customAgent);
      if (response.data.success) {
        setSavedAgents([...savedAgents, customAgent]);

        // Register with integration orchestrator
        await integrationService.routeMessage({
          sender: 'agent-builder',
          recipient: 'supervisor',
          content: `New custom agent created: ${customAgent.name} with ${customAgent.skills.length} skills`,
          priority: 'normal'
        });

        // Reset form
        setCustomAgent({
          id: `agent-${Date.now()}`,
          name: '',
          description: '',
          icon: '🤖',
          skills: [],
          knowledge: [],
          triggers: ['manual'],
          outputs: ['json', 'webhook']
        });
        alert('Agent saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save agent:', error);
      alert('Failed to save agent. Please try again.');
    }
  };

  const handleDeployAgent = async () => {
    if (!customAgent.name || customAgent.skills.length === 0) {
      alert('Please configure your agent before deploying');
      return;
    }

    setIsDeploying(true);
    try {
      // Deploy through integration service for real execution
      const result = await integrationService.executeCustomAgent(customAgent, 'deploy');

      if (result && result.task_id) {
        // Notify supervisor about deployment
        await integrationService.routeMessage({
          sender: 'agent-builder',
          recipient: 'deployment',
          content: `Deploy custom agent: ${customAgent.name}`,
          priority: 'high'
        });

        alert(`Agent deployed successfully! Task ID: ${result.task_id}`);

        // Add to saved agents
        setSavedAgents([...savedAgents, customAgent]);
      }
    } catch (error) {
      console.error('Failed to deploy agent:', error);
      alert('Failed to deploy agent. Please try again.');
    } finally {
      setIsDeploying(false);
    }
  };

  const handleTestAgent = async () => {
    if (customAgent.skills.length === 0) {
      alert('Please add at least one skill to test');
      return;
    }

    try {
      // Test through integration service for real execution
      const testInput = prompt('Enter test input for your agent:') || 'Test input data';

      const result = await integrationService.executeCustomAgent(customAgent, testInput);

      if (result && result.task_id) {
        // Notify testing agent
        await integrationService.routeMessage({
          sender: 'agent-builder',
          recipient: 'testing',
          content: `Test custom agent: ${customAgent.name} with input: ${testInput}`,
          priority: 'normal'
        });

        console.log('Test execution started:', result);
        alert(`Test started! Task ID: ${result.task_id}\nCheck the Testing agent terminal for results.`);
      }
    } catch (error) {
      console.error('Test failed:', error);
      alert('Test failed. Please check your configuration.');
    }
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="min-h-screen bg-gray-900 p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">🎨 Agent Builder</h1>
          <p className="text-gray-400">Create custom AI agents with drag & drop simplicity</p>
        </div>

        {/* Main Layout */}
        <div className="flex gap-6">
          {/* Skills Library */}
          <div className="w-80 bg-gray-800 rounded-lg p-4">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Zap className="mr-2 text-yellow-400" />
              Available Skills
            </h2>
            <div className="space-y-2">
              {availableSkills.map(skill => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                  onAdd={(skill) => {
                    if (!customAgent.skills.find(s => s.id === skill.id)) {
                      setCustomAgent({
                        ...customAgent,
                        skills: [...customAgent.skills, skill]
                      });
                    }
                  }}
                />
              ))}
            </div>
          </div>

          {/* Agent Canvas */}
          <AgentCanvas agent={customAgent} onUpdate={setCustomAgent} />

          {/* Actions Panel */}
          <div className="w-64 space-y-4">
            <button
              onClick={handleTestAgent}
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
            >
              <Play className="w-4 h-4" />
              <span>Test Agent</span>
            </button>

            <button
              onClick={handleSaveAgent}
              className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>Save Agent</span>
            </button>

            <button
              onClick={handleDeployAgent}
              disabled={isDeploying}
              className="w-full px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Rocket className="w-4 h-4" />
              <span>{isDeploying ? 'Deploying...' : 'Deploy Agent'}</span>
            </button>

            {/* Saved Agents */}
            {savedAgents.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-white mb-2">Saved Agents</h3>
                <div className="space-y-2">
                  {savedAgents.map(agent => (
                    <div key={agent.id} className="text-sm text-gray-400">
                      {agent.icon} {agent.name}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tips */}
            <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-400 mb-2">💡 Pro Tips</h3>
              <ul className="text-xs text-blue-300 space-y-1">
                <li>• Drag skills to the canvas</li>
                <li>• Combine multiple skills</li>
                <li>• Add knowledge for context</li>
                <li>• Test before deploying</li>
                <li>• Share agents with team</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Template Gallery */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">🚀 Quick Start Templates</h2>
          <div className="grid grid-cols-4 gap-4">
            {[
              { name: 'API Developer', icon: '⚙️', skills: ['code-gen', 'api-design', 'testing'] },
              { name: 'Full Stack', icon: '🎯', skills: ['code-gen', 'db-schema', 'ui-gen', 'deploy'] },
              { name: 'Data Analyst', icon: '📊', skills: ['analyze', 'db-schema'] },
              { name: 'DevOps Master', icon: '🚀', skills: ['deploy', 'testing'] },
            ].map(template => (
              <button
                key={template.name}
                onClick={() => {
                  setCustomAgent({
                    ...customAgent,
                    name: template.name,
                    skills: availableSkills.filter(s => template.skills.includes(s.id))
                  });
                }}
                className="p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors text-left"
              >
                <div className="text-2xl mb-2">{template.icon}</div>
                <div className="text-sm font-medium text-white">{template.name}</div>
                <div className="text-xs text-gray-400">{template.skills.length} skills</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </DndProvider>
  );
};

export default AgentBuilder;