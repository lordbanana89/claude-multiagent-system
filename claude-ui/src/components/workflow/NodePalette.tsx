import React from 'react';
import { useDrag } from 'react-dnd';

// Node types definition
export const NODE_TYPES = {
  AGENT: 'agent',
  TASK: 'task',
  CONDITION: 'condition',
  LOOP: 'loop',
  TRIGGER: 'trigger',
  INPUT: 'input',
  OUTPUT: 'output',
  TRANSFORM: 'transform'
} as const;

interface NodeTemplate {
  type: string;
  label: string;
  icon: string;
  description: string;
  category: string;
  defaultConfig?: any;
}

// Node templates
const nodeTemplates: NodeTemplate[] = [
  {
    type: NODE_TYPES.AGENT,
    label: 'Agent Node',
    icon: '🤖',
    description: 'Execute task via agent',
    category: 'Execution',
    defaultConfig: {
      agentId: '',
      command: '',
      timeout: 30000
    }
  },
  {
    type: NODE_TYPES.TASK,
    label: 'Task Node',
    icon: '📋',
    description: 'Define a task to execute',
    category: 'Execution',
    defaultConfig: {
      name: '',
      description: '',
      priority: 'normal'
    }
  },
  {
    type: NODE_TYPES.CONDITION,
    label: 'Condition',
    icon: '❓',
    description: 'Conditional branching',
    category: 'Control Flow',
    defaultConfig: {
      condition: '',
      operator: 'equals'
    }
  },
  {
    type: NODE_TYPES.LOOP,
    label: 'Loop',
    icon: '🔄',
    description: 'Iterate over items',
    category: 'Control Flow',
    defaultConfig: {
      items: [],
      maxIterations: 100
    }
  },
  {
    type: NODE_TYPES.TRIGGER,
    label: 'Trigger',
    icon: '⚡',
    description: 'Workflow trigger',
    category: 'Events',
    defaultConfig: {
      triggerType: 'manual',
      schedule: ''
    }
  },
  {
    type: NODE_TYPES.INPUT,
    label: 'Input',
    icon: '📥',
    description: 'Data input node',
    category: 'Data',
    defaultConfig: {
      inputType: 'text',
      defaultValue: ''
    }
  },
  {
    type: NODE_TYPES.OUTPUT,
    label: 'Output',
    icon: '📤',
    description: 'Data output node',
    category: 'Data',
    defaultConfig: {
      outputType: 'console',
      format: 'json'
    }
  },
  {
    type: NODE_TYPES.TRANSFORM,
    label: 'Transform',
    icon: '🔧',
    description: 'Transform data',
    category: 'Data',
    defaultConfig: {
      transformation: '',
      outputFormat: 'json'
    }
  }
];

// Draggable node component
const DraggableNode: React.FC<{ template: NodeTemplate }> = ({ template }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'node',
    item: () => ({
      nodeType: template.type,
      template: template
    }),
    collect: (monitor) => ({
      isDragging: monitor.isDragging()
    })
  });

  const onDragStart = (event: React.DragEvent) => {
    event.dataTransfer.setData('application/reactflow', template.type);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      ref={drag as any}
      draggable
      onDragStart={onDragStart}
      className={`p-3 bg-gray-700 rounded-lg cursor-move transition-all hover:bg-gray-600 ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-center space-x-2">
        <span className="text-2xl">{template.icon}</span>
        <div className="flex-1">
          <div className="text-sm font-medium text-white">{template.label}</div>
          <div className="text-xs text-gray-400">{template.description}</div>
        </div>
      </div>
    </div>
  );
};

interface NodePaletteProps {
  onNodeSelect?: (template: NodeTemplate) => void;
}

const NodePalette: React.FC<NodePaletteProps> = ({ onNodeSelect }) => {
  const categories = [...new Set(nodeTemplates.map(n => n.category))];

  return (
    <div className="h-full bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">Node Palette</h3>
        <p className="text-xs text-gray-400 mt-1">Drag nodes to canvas</p>
      </div>

      {/* Search */}
      <div className="p-3 border-b border-gray-700">
        <input
          type="text"
          placeholder="Search nodes..."
          className="w-full px-3 py-2 bg-gray-700 text-white rounded text-sm border border-gray-600 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Node Categories */}
      <div className="flex-1 overflow-y-auto p-3">
        {categories.map(category => (
          <div key={category} className="mb-4">
            <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">
              {category}
            </h4>
            <div className="space-y-2">
              {nodeTemplates
                .filter(n => n.category === category)
                .map((template, index) => (
                  <DraggableNode
                    key={`${template.type}-${index}`}
                    template={template}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>

      {/* Footer with tips */}
      <div className="p-3 border-t border-gray-700 bg-gray-900">
        <div className="text-xs text-gray-400">
          <div className="flex items-center space-x-1">
            <span>💡</span>
            <span>Tip: Drag nodes to add them to workflow</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NodePalette;
export type { NodeTemplate };