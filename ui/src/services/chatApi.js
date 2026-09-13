import axios from 'axios';
import { USER_ID, ORGANIZATION_ID } from '../constants/config';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 50000,
});

// Interceptor to attach user/org context to requests
apiClient.interceptors.request.use((config) => {
  config.params = {
    user_id: USER_ID,
    organization_id: ORGANIZATION_ID,
    ...config.params,
  };
  return config;
});

/**
 * Sends a customer support message to the backend.
 *
 * @param {Object} params
 * @param {string} params.message - Message content from customer
 * @param {string} params.conversationId - Session conversation ID
 * @returns {Promise<{ response: string, conversation_id: string }>} API response payload
 */
export const sendChatMessage = async ({ message, conversationId }) => {
  const payload = {
    message,
    conversation_id: conversationId,
  };
  
  const { data } = await apiClient.post('/chat', payload);
  return data;
};

/**
 * Fetches all available conversations.
 * Calls GET /conversations from backend.
 *
 * @returns {Promise<Array<{ id: string, title: string, last_message: string, lastMessage: string, timestamp: string }>>}
 */
export const fetchConversations = async () => {
  const { data } = await apiClient.get('/conversations');
  return data.map((conv) => ({
    ...conv,
    lastMessage: conv.last_message || conv.lastMessage || 'No messages yet',
  }));
};

/**
 * Creates a new conversation thread.
 * Calls POST /conversations.
 *
 * @returns {Promise<{ id: string, title: string, last_message: string, lastMessage: string, timestamp: string }>}
 */
export const createConversation = async () => {
  const { data } = await apiClient.post('/conversations');
  return {
    ...data,
    lastMessage: data.last_message || data.lastMessage || 'Chat started',
  };
};

/**
 * Fetches all messages for a given conversation.
 * Calls GET /conversations/:id/messages.
 *
 * @param {string} conversationId
 * @returns {Promise<Array<{ id: string, sender: string, text: string, timestamp: string }>>}
 */
export const fetchConversationMessages = async (conversationId) => {
  if (!conversationId) return [];
  const { data } = await apiClient.get(`/conversations/${conversationId}/messages`);
  return data;
};

/**
 * Streams a customer support message response using Server-Sent Events (SSE).
 *
 * @param {Object} params
 * @param {string} params.message - Message content
 * @param {string} params.conversationId - Session conversation ID
 * @param {Function} onChunk - Callback for receiving text chunks
 * @returns {Promise<void>}
 */
export const streamChatMessage = async ({ message, conversationId, onChunk }) => {
  const url = `${API_BASE_URL}/chat/stream?user_id=${USER_ID}&organization_id=${ORGANIZATION_ID}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Streaming failed with status: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const chunk = line.replace(/^data: /, '');
        if (onChunk) onChunk(chunk);
      }
    }
  }

  if (buffer.startsWith('data: ')) {
    const chunk = buffer.replace(/^data: /, '');
    if (onChunk) onChunk(chunk);
  }
};


