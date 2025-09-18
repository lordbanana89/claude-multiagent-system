import { useEffect, useRef } from 'react';
import { useInboxStore } from '../store/inboxStore';
import { config } from '../config';

export const useInboxAPI = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const {
    addMessage,
    markAsRead,
    markAsUnread,
    archiveMessage,
    clearAllMessages,
  } = useInboxStore();

  // Fetch messages from API
  const fetchMessages = async () => {
    try {
      const response = await fetch(`${config.INBOX_API_URL}/api/inbox/messages`);
      if (response.ok) {
        const data = await response.json();

        // Clear existing and add new messages
        clearAllMessages();
        data.messages.forEach((message: any) => {
          addMessage(message);
        });

        console.log(`Loaded ${data.messages.length} messages from Inbox API`);
      }
    } catch (error) {
      console.error('Failed to fetch inbox messages:', error);
    }
  };

  // Connect to WebSocket for real-time updates
  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsRef.current = new WebSocket(config.INBOX_WEBSOCKET_URL);

      wsRef.current.onopen = () => {
        console.log('Connected to Inbox WebSocket');
        reconnectAttempts.current = 0;

        // Subscribe to updates
        wsRef.current?.send(JSON.stringify({ action: 'subscribe' }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'new_message') {
            addMessage(data.message);
          } else if (data.type === 'message_updated') {
            // Handle message updates
            const { message_id, status } = data;
            if (status === 'read') {
              markAsRead(message_id);
            } else if (status === 'unread') {
              markAsUnread(message_id);
            } else if (status === 'archived') {
              archiveMessage(message_id);
            }
          } else if (data.type === 'update') {
            // Handle general updates
            console.log('Inbox update:', data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Inbox WebSocket error:', error);
      };

      wsRef.current.onclose = () => {
        console.log('Inbox WebSocket disconnected');

        // Attempt reconnection with exponential backoff
        if (reconnectAttempts.current < config.MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(
            config.RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts.current),
            30000
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connectWebSocket();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Failed to connect to Inbox WebSocket:', error);
    }
  };

  // Send action to API
  const sendAction = async (messageId: string, action: string) => {
    try {
      const response = await fetch(
        `${config.INBOX_API_URL}/api/inbox/messages/${messageId}/${action}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to ${action} message`);
      }

      return true;
    } catch (error) {
      console.error(`Error performing ${action}:`, error);
      return false;
    }
  };

  // Convert inbox message to MCP task
  const convertToMCPTask = async (messageId: string, action: string, response?: string) => {
    try {
      const result = await fetch(
        `${config.INBOX_API_URL}/api/mcp/inbox-to-task`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message_id: messageId,
            action,
            response: response || '',
          }),
        }
      );

      if (!result.ok) {
        throw new Error('Failed to convert to MCP task');
      }

      const data = await result.json();
      console.log('Converted to MCP task:', data.task_id);
      return data.task_id;
    } catch (error) {
      console.error('Error converting to MCP task:', error);
      return null;
    }
  };

  // Initialize connection
  useEffect(() => {
    // Fetch initial messages
    fetchMessages();

    // Connect to WebSocket
    connectWebSocket();

    // Set up periodic refresh
    const refreshInterval = setInterval(fetchMessages, 30000); // Refresh every 30 seconds

    // Cleanup
    return () => {
      clearInterval(refreshInterval);

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    sendAction,
    convertToMCPTask,
    refreshMessages: fetchMessages,
  };
};