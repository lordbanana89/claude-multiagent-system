import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { config } from '../../config';

const API_URL = config.API_URL;

interface Document {
  id: string;
  name: string;
  type: 'instruction' | 'readme' | 'guide' | 'api';
  path: string;
  content: string;
  lastModified: string;
}

interface Agent {
  id: string;
  name: string;
  instructionFile?: string;
}

const DocumentationEditor: React.FC = () => {
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documents = [] } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/documents`);
      return response.data;
    },
  });

  // Fetch agents for instructions
  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/agents`);
      return response.data;
    },
  });

  // Save document mutation
  const saveDocumentMutation = useMutation({
    mutationFn: async (doc: { id: string; content: string }) => {
      const response = await axios.put(`${API_URL}/api/documents/${doc.id}`, {
        content: doc.content,
      });
      return response.data;
    },
    onSuccess: () => {
      setEditMode(false);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Create document mutation
  const createDocumentMutation = useMutation({
    mutationFn: async (doc: { name: string; type: string; content: string }) => {
      const response = await axios.post(`${API_URL}/api/documents`, doc);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setSelectedDoc(data);
    },
  });

  const filteredDocuments = documents.filter(doc =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getDocIcon = (type: string) => {
    switch (type) {
      case 'instruction':
        return '📋';
      case 'readme':
        return '📖';
      case 'guide':
        return '📚';
      case 'api':
        return '🔌';
      default:
        return '📄';
    }
  };

  const getDocTypeColor = (type: string) => {
    switch (type) {
      case 'instruction':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'readme':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'guide':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400';
      case 'api':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const handleEdit = () => {
    if (selectedDoc) {
      setEditContent(selectedDoc.content);
      setEditMode(true);
    }
  };

  const handleSave = () => {
    if (selectedDoc) {
      saveDocumentMutation.mutate({
        id: selectedDoc.id,
        content: editContent,
      });
    }
  };

  const handleCancel = () => {
    setEditMode(false);
    setEditContent('');
  };

  return (
    <div className="h-full flex">
      {/* Left Sidebar - Document List */}
      <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            📝 Documentation
          </h2>

          {/* Search Bar */}
          <div className="mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          {/* Document Categories */}
          <div className="space-y-4">
            {/* Agent Instructions */}
            <div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2 uppercase">
                Agent Instructions
              </h3>
              <div className="space-y-1">
                {filteredDocuments
                  .filter(doc => doc.type === 'instruction')
                  .map(doc => (
                    <button
                      key={doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      className={`w-full text-left p-2 rounded-lg transition-colors ${
                        selectedDoc?.id === doc.id
                          ? 'bg-primary-100 dark:bg-primary-900/30 border-l-4 border-primary-500'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center">
                        <span className="text-lg mr-2">{getDocIcon(doc.type)}</span>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {doc.name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            Modified: {new Date(doc.lastModified).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
              </div>
            </div>

            {/* README Files */}
            <div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2 uppercase">
                README Files
              </h3>
              <div className="space-y-1">
                {filteredDocuments
                  .filter(doc => doc.type === 'readme')
                  .map(doc => (
                    <button
                      key={doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      className={`w-full text-left p-2 rounded-lg transition-colors ${
                        selectedDoc?.id === doc.id
                          ? 'bg-primary-100 dark:bg-primary-900/30 border-l-4 border-primary-500'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center">
                        <span className="text-lg mr-2">{getDocIcon(doc.type)}</span>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {doc.name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {doc.path}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
              </div>
            </div>

            {/* Guides */}
            <div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2 uppercase">
                Guides
              </h3>
              <div className="space-y-1">
                {filteredDocuments
                  .filter(doc => doc.type === 'guide')
                  .map(doc => (
                    <button
                      key={doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      className={`w-full text-left p-2 rounded-lg transition-colors ${
                        selectedDoc?.id === doc.id
                          ? 'bg-primary-100 dark:bg-primary-900/30 border-l-4 border-primary-500'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center">
                        <span className="text-lg mr-2">{getDocIcon(doc.type)}</span>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {doc.name}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
              </div>
            </div>
          </div>

          {/* Create New Document */}
          <div className="mt-6 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <button
              onClick={() => {
                const name = prompt('Document name:');
                const type = prompt('Document type (instruction/readme/guide/api):');
                if (name && type) {
                  createDocumentMutation.mutate({
                    name,
                    type,
                    content: `# ${name}\n\n<!-- Start writing here -->\n`,
                  });
                }
              }}
              className="w-full px-3 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
            >
              ➕ New Document
            </button>
          </div>
        </div>
      </div>

      {/* Main Content - Document Editor */}
      <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900">
        {selectedDoc ? (
          <>
            {/* Document Header */}
            <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">{getDocIcon(selectedDoc.type)}</span>
                  <div>
                    <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                      {selectedDoc.name}
                    </h1>
                    <div className="flex items-center mt-1">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full mr-2 ${getDocTypeColor(
                          selectedDoc.type
                        )}`}
                      >
                        {selectedDoc.type}
                      </span>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {selectedDoc.path}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {editMode ? (
                    <>
                      <button
                        onClick={handleSave}
                        disabled={saveDocumentMutation.isPending}
                        className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
                      >
                        {saveDocumentMutation.isPending ? 'Saving...' : '💾 Save'}
                      </button>
                      <button
                        onClick={handleCancel}
                        className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={handleEdit}
                      className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                    >
                      ✏️ Edit
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Document Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              {editMode ? (
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full h-full px-4 py-3 font-mono text-sm border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white resize-none"
                  placeholder="Enter document content..."
                />
              ) : (
                <div className="prose dark:prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm bg-white dark:bg-gray-800 p-4 rounded-lg">
                    {selectedDoc.content}
                  </pre>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">📚</div>
              <div className="text-xl text-gray-500 dark:text-gray-400">
                Select a document to view or edit
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentationEditor;