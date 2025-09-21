import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface Message {
  id: string;
  from: string;
  to: string;
  subject: string;
  content: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'unread' | 'read' | 'archived';
  timestamp: string;
  type: 'task' | 'notification' | 'error' | 'success';
  metadata?: Record<string, any>;
  attachments?: Array<{
    name: string;
    url: string;
    type: string;
    size: number;
  }>;
}

interface InboxState {
  messages: Message[];
  unreadCount: number;
  selectedMessage: Message | null;
  filter: 'all' | 'unread' | 'high-priority' | 'archived';
  searchQuery: string;

  // Actions
  addMessage: (message: Message) => void;
  markAsRead: (messageId: string) => void;
  markAsUnread: (messageId: string) => void;
  archiveMessage: (messageId: string) => void;
  deleteMessage: (messageId: string) => void;
  setSelectedMessage: (message: Message | null) => void;
  setFilter: (filter: InboxState['filter']) => void;
  setSearchQuery: (query: string) => void;
  clearAllMessages: () => void;
  getFilteredMessages: () => Message[];
}

const useInboxStore = create<InboxState>()(
  devtools(
    persist(
      (set, get) => ({
        messages: [],
        unreadCount: 0,
        selectedMessage: null,
        filter: 'all',
        searchQuery: '',

        addMessage: (message) =>
          set((state) => {
            const newMessages = [...state.messages, message];
            const unreadCount = newMessages.filter(m => m.status === 'unread').length;
            return { messages: newMessages, unreadCount };
          }),

        markAsRead: (messageId) =>
          set((state) => {
            const messages = state.messages.map(m =>
              m.id === messageId ? { ...m, status: 'read' as const } : m
            );
            const unreadCount = messages.filter(m => m.status === 'unread').length;
            return { messages, unreadCount };
          }),

        markAsUnread: (messageId) =>
          set((state) => {
            const messages = state.messages.map(m =>
              m.id === messageId ? { ...m, status: 'unread' as const } : m
            );
            const unreadCount = messages.filter(m => m.status === 'unread').length;
            return { messages, unreadCount };
          }),

        archiveMessage: (messageId) =>
          set((state) => {
            const messages = state.messages.map(m =>
              m.id === messageId ? { ...m, status: 'archived' as const } : m
            );
            const unreadCount = messages.filter(m => m.status === 'unread').length;
            return {
              messages,
              unreadCount,
              selectedMessage:
                state.selectedMessage?.id === messageId ? null : state.selectedMessage,
            };
          }),

        deleteMessage: (messageId) =>
          set((state) => {
            const messages = state.messages.filter(m => m.id !== messageId);
            const unreadCount = messages.filter(m => m.status === 'unread').length;
            return {
              messages,
              unreadCount,
              selectedMessage:
                state.selectedMessage?.id === messageId ? null : state.selectedMessage,
            };
          }),

        setSelectedMessage: (message) =>
          set({ selectedMessage: message }),

        setFilter: (filter) =>
          set({ filter }),

        setSearchQuery: (query) =>
          set({ searchQuery: query }),

        clearAllMessages: () =>
          set({ messages: [], unreadCount: 0, selectedMessage: null }),

        getFilteredMessages: () => {
          const state = get();
          let filtered = [...state.messages];

          // Apply filter
          switch (state.filter) {
            case 'unread':
              filtered = filtered.filter(m => m.status === 'unread');
              break;
            case 'high-priority':
              filtered = filtered.filter(m => m.priority === 'high' || m.priority === 'urgent');
              break;
            case 'archived':
              filtered = filtered.filter(m => m.status === 'archived');
              break;
          }

          // Apply search
          if (state.searchQuery) {
            const query = state.searchQuery.toLowerCase();
            filtered = filtered.filter(
              m =>
                m.subject.toLowerCase().includes(query) ||
                m.content.toLowerCase().includes(query) ||
                m.from.toLowerCase().includes(query) ||
                m.to.toLowerCase().includes(query)
            );
          }

          // Sort by timestamp (newest first)
          filtered.sort((a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          );

          return filtered;
        },
      }),
      {
        name: 'inbox-store',
        partialize: (state) => ({
          messages: state.messages,
          filter: state.filter,
        }),
      }
    )
  )
);

export { useInboxStore };
export default useInboxStore;