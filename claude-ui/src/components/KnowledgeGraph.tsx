import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  type Node,
  type Edge,
  type Connection,
  type NodeProps,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from 'reactflow';
import { Brain, Database, Link, Search, Plus, Save, Upload, Download, Sparkles } from 'lucide-react';
import axios from 'axios';
import { config } from '../config';
import integrationService from '../services/integration';
import 'reactflow/dist/style.css';

interface KnowledgeNode {
  id: string;
  type: string;
  label: string;
  category: 'concept' | 'data' | 'skill' | 'insight' | 'agent';
  metadata?: any;
  embedding?: number[];
}

interface KnowledgeEdge {
  source: string;
  target: string;
  relationship: string;
  strength: number;
}

// Custom Knowledge Node Component
const KnowledgeNodeComponent: React.FC<NodeProps> = ({ data }) => {
  const getNodeStyle = () => {
    switch (data.category) {
      case 'concept':
        return 'bg-blue-500/20 border-blue-500';
      case 'data':
        return 'bg-green-500/20 border-green-500';
      case 'skill':
        return 'bg-purple-500/20 border-purple-500';
      case 'insight':
        return 'bg-yellow-500/20 border-yellow-500';
      case 'agent':
        return 'bg-red-500/20 border-red-500';
      default:
        return 'bg-gray-500/20 border-gray-500';
    }
  };

  const getIcon = () => {
    switch (data.category) {
      case 'concept':
        return '💡';
      case 'data':
        return '📊';
      case 'skill':
        return '⚡';
      case 'insight':
        return '✨';
      case 'agent':
        return '🤖';
      default:
        return '📌';
    }
  };

  return (
    <div className={`px-4 py-3 rounded-lg border-2 ${getNodeStyle()} min-w-[150px]`}>
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center space-x-2">
        <span className="text-lg">{getIcon()}</span>
        <div>
          <div className="text-sm font-semibold text-white">{data.label}</div>
          <div className="text-xs text-gray-400">{data.category}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

const nodeTypes = {
  knowledge: KnowledgeNodeComponent,
};

const KnowledgeGraph: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [graphStats, setGraphStats] = useState({
    totalNodes: 0,
    totalEdges: 0,
    clusters: 0,
    density: 0,
  });

  // Load knowledge graph from backend through integration
  const loadKnowledgeGraph = async () => {
    try {
      // Get knowledge graph through integration service
      const graphData = await integrationService.getKnowledgeGraph();

      let knowledgeNodes = [];
      let knowledgeEdges = [];

      if (graphData.nodes && graphData.edges) {
        knowledgeNodes = graphData.nodes;
        knowledgeEdges = graphData.edges;
      } else {
        // Fallback to direct API call
        const response = await axios.get(`${config.API_URL}/api/knowledge/graph`);
        knowledgeNodes = response.data.nodes || [];
        knowledgeEdges = response.data.edges || [];
      }

      // Convert to ReactFlow format
      const flowNodes = knowledgeNodes.map((node: KnowledgeNode, index: number) => ({
        id: node.id,
        type: 'knowledge',
        position: {
          x: Math.cos((2 * Math.PI * index) / knowledgeNodes.length) * 300 + 400,
          y: Math.sin((2 * Math.PI * index) / knowledgeNodes.length) * 300 + 300,
        },
        data: {
          label: node.label,
          category: node.category,
          metadata: node.metadata,
        },
      }));

      const flowEdges = knowledgeEdges.map((edge: KnowledgeEdge) => ({
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        label: edge.relationship,
        animated: edge.strength > 0.7,
        style: {
          stroke: edge.strength > 0.7 ? '#10b981' : '#6b7280',
          strokeWidth: edge.strength * 3,
        },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);

      // Calculate stats
      setGraphStats({
        totalNodes: flowNodes.length,
        totalEdges: flowEdges.length,
        clusters: Math.floor(flowNodes.length / 5), // Simplified clustering
        density: flowEdges.length / (flowNodes.length * (flowNodes.length - 1) / 2),
      });
    } catch (error) {
      console.error('Failed to load knowledge graph:', error);
    }
  };

  useEffect(() => {
    loadKnowledgeGraph();
  }, []);

  const onConnect = useCallback(
    (params: Connection) => {
      const edge = {
        ...params,
        id: `${params.source}-${params.target}`,
        label: 'relates_to',
        animated: true,
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  const handleSearch = async () => {
    if (!searchQuery) return;

    try {
      const response = await axios.post(`${config.API_URL}/api/knowledge/search`, {
        query: searchQuery,
        limit: 10,
      });

      // Highlight search results
      const resultIds = response.data.results.map((r: any) => r.id);
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          style: {
            ...node.style,
            opacity: resultIds.includes(node.id) ? 1 : 0.3,
          },
        }))
      );
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleAddNode = async (nodeData: any) => {
    try {
      const response = await axios.post(`${config.API_URL}/api/knowledge/nodes`, nodeData);
      if (response.data.success) {
        // If it's an agent node, link it through integration
        if (nodeData.category === 'agent' && nodeData.agent_id) {
          await integrationService.linkKnowledgeToAgent(
            nodeData.agent_id,
            response.data.node_id
          );
        }
        loadKnowledgeGraph(); // Reload graph
        setShowAddModal(false);
      }
    } catch (error) {
      console.error('Failed to add node:', error);
    }
  };

  const handleAutoDiscover = async () => {
    try {
      const response = await axios.post(`${config.API_URL}/api/knowledge/discover`);
      if (response.data.discovered > 0) {
        loadKnowledgeGraph(); // Reload with new discoveries
        alert(`Discovered ${response.data.discovered} new knowledge connections!`);
      }
    } catch (error) {
      console.error('Auto-discovery failed:', error);
    }
  };

  const handleExport = async () => {
    try {
      const response = await axios.get(`${config.API_URL}/api/knowledge/export`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'knowledge-graph.json';
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-white flex items-center">
              <Brain className="mr-2 text-purple-400" />
              Knowledge Graph
            </h1>
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <span>Nodes: {graphStats.totalNodes}</span>
              <span>•</span>
              <span>Edges: {graphStats.totalEdges}</span>
              <span>•</span>
              <span>Clusters: {graphStats.clusters}</span>
              <span>•</span>
              <span>Density: {(graphStats.density * 100).toFixed(1)}%</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            {/* Search */}
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search knowledge..."
                className="px-3 py-1.5 bg-gray-700 text-white rounded-md text-sm w-64"
              />
              <button
                onClick={handleSearch}
                className="p-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>

            <button
              onClick={() => setShowAddModal(true)}
              className="px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm flex items-center"
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Node
            </button>

            <button
              onClick={handleAutoDiscover}
              className="px-3 py-1.5 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm flex items-center"
            >
              <Sparkles className="w-4 h-4 mr-1" />
              Auto Discover
            </button>

            <button
              onClick={handleExport}
              className="px-3 py-1.5 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm flex items-center"
            >
              <Download className="w-4 h-4 mr-1" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Graph Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          onNodeClick={(event, node) => setSelectedNode(node)}
          fitView
        >
          <Background color="#1f2937" gap={20} />
          <Controls className="bg-gray-800 border-gray-700" />
          <MiniMap
            nodeColor={(node) => {
              switch (node.data?.category) {
                case 'concept': return '#3b82f6';
                case 'data': return '#10b981';
                case 'skill': return '#8b5cf6';
                case 'insight': return '#eab308';
                case 'agent': return '#ef4444';
                default: return '#6b7280';
              }
            }}
            className="bg-gray-800 border-gray-700"
          />
        </ReactFlow>
      </div>

      {/* Selected Node Details */}
      {selectedNode && (
        <div className="absolute right-4 top-20 w-80 bg-gray-800 rounded-lg shadow-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Node Details</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400">ID</label>
              <div className="text-sm text-white">{selectedNode.id}</div>
            </div>
            <div>
              <label className="text-xs text-gray-400">Label</label>
              <div className="text-sm text-white">{selectedNode.data?.label}</div>
            </div>
            <div>
              <label className="text-xs text-gray-400">Category</label>
              <div className="text-sm text-white capitalize">{selectedNode.data?.category}</div>
            </div>
            {selectedNode.data?.metadata && (
              <div>
                <label className="text-xs text-gray-400">Metadata</label>
                <pre className="text-xs text-white bg-gray-900 p-2 rounded mt-1">
                  {JSON.stringify(selectedNode.data.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Node Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96">
            <h2 className="text-xl font-semibold text-white mb-4">Add Knowledge Node</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target as HTMLFormElement);
                handleAddNode({
                  label: formData.get('label'),
                  category: formData.get('category'),
                  description: formData.get('description'),
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Label</label>
                <input
                  name="label"
                  type="text"
                  required
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Category</label>
                <select
                  name="category"
                  required
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-md"
                >
                  <option value="concept">Concept</option>
                  <option value="data">Data</option>
                  <option value="skill">Skill</option>
                  <option value="insight">Insight</option>
                  <option value="agent">Agent</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
                <textarea
                  name="description"
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-md"
                />
              </div>
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Add Node
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraph;