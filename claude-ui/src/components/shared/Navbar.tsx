import React from 'react';

interface NavbarProps {
  currentView: 'dashboard' | 'workflow' | 'monitor' | 'inbox' | 'terminal' | 'control' | 'queue' | 'docs';
  onViewChange: (view: 'dashboard' | 'workflow' | 'monitor' | 'inbox' | 'terminal' | 'control' | 'queue' | 'docs') => void;
}

const Navbar: React.FC<NavbarProps> = ({ currentView, onViewChange }) => {
  return (
    <nav className="bg-white dark:bg-gray-800 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              🤖 Claude Multi-Agent System
            </h1>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={() => onViewChange('control')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'control'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              🎮 Control
            </button>
            <button
              onClick={() => onViewChange('dashboard')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'dashboard'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              📊 Dashboard
            </button>
            <button
              onClick={() => onViewChange('workflow')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'workflow'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              🔄 Workflow
            </button>
            <button
              onClick={() => onViewChange('monitor')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'monitor'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              📈 Monitor
            </button>
            <button
              onClick={() => onViewChange('queue')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'queue'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              📡 Queue
            </button>
            <button
              onClick={() => onViewChange('inbox')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'inbox'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              📬 Inbox
            </button>
            <button
              onClick={() => onViewChange('docs')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'docs'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              📝 Docs
            </button>
            <button
              onClick={() => onViewChange('terminal')}
              className={`px-3 py-2 rounded-md transition-colors text-sm ${
                currentView === 'terminal'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              }`}
            >
              🖥️ Terminal
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <span className="flex items-center">
              <span className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
              <span className="text-sm text-gray-600 dark:text-gray-300">System Online</span>
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;