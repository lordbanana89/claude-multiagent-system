// Hook for MCP WebSocket Real-time Updates
import { useState, useEffect, useCallback } from 'react';
import { getMCPClient } from '../services/mcpClient';
import type { MCPActivity, MCPAgentState, MCPWebSocketMessage } from '../services/mcpTypes';

interface WebSocketState {
  connected: boolean;
  lastMessage: MCPWebSocketMessage | null;
  activities: MCPActivity[];
  agentStates: Record<string, MCPAgentState>;
}

export const useMCPWebSocket = (maxActivities: number = 100) => {
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    lastMessage: null,
    activities: [],
    agentStates: {},
  });

  const client = getMCPClient();

  // Handle new activity
  const handleActivity = useCallback((activity: MCPActivity) => {
    setState(prev => ({
      ...prev,
      activities: [activity, ...prev.activities].slice(0, maxActivities),
    }));
  }, [maxActivities]);

  // Handle agent state change
  const handleStateChange = useCallback((agentState: MCPAgentState) => {
    setState(prev => ({
      ...prev,
      agentStates: {
        ...prev.agentStates,
        [agentState.agent_id]: agentState,
      },
    }));
  }, []);

  // Handle any message
  const handleMessage = useCallback((message: MCPWebSocketMessage) => {
    setState(prev => ({ ...prev, lastMessage: message }));
  }, []);

  // Handle connection status
  const handleConnection = useCallback((data: any) => {
    // Handle both direct boolean and object with connected property
    const connected = typeof data === 'boolean' ? data : data?.connected ?? false;
    setState(prev => ({ ...prev, connected }));
  }, []);

  // Subscribe to events
  useEffect(() => {
    const unsubscribers = [
      client.on('activity', handleActivity),
      client.on('state_change', handleStateChange),
      client.on('message', handleMessage),
      client.on('connection', handleConnection),
    ];

    // Load initial agent states
    client.getAgentStates().then(states => {
      const stateMap = states.reduce((acc, state) => {
        acc[state.agent_id] = state;
        return acc;
      }, {} as Record<string, MCPAgentState>);

      setState(prev => ({ ...prev, agentStates: stateMap }));
    }).catch(console.error);

    // Load recent activities
    client.getActivities(maxActivities).then(activities => {
      setState(prev => ({ ...prev, activities }));
    }).catch(console.error);

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [client, handleActivity, handleStateChange, handleMessage, handleConnection, maxActivities]);

  // Send a custom message
  const sendMessage = useCallback((type: string, data: any) => {
    if (client.isConnected()) {
      // This would need to be implemented in mcpClient
      console.log('Sending WebSocket message:', { type, data });
    }
  }, [client]);

  // Clear activities
  const clearActivities = useCallback(() => {
    setState(prev => ({ ...prev, activities: [] }));
  }, []);

  return {
    connected: state.connected,
    activities: state.activities,
    agentStates: state.agentStates,
    lastMessage: state.lastMessage,
    sendMessage,
    clearActivities,
    totalAgents: Object.keys(state.agentStates).length,
    onlineAgents: Object.values(state.agentStates).filter(a => a.status === 'online').length,
  };
};

export default useMCPWebSocket;