import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Sends a customer support message to the backend.
 *
 * @param {Object} params
 * @param {string} params.message - Message content from customer
 * @param {string} params.conversationId - Session conversation ID
 * @returns {Promise<{ response: string }>} API response payload
 */
export const sendChatMessage = async ({ message, conversationId }) => {
  const payload = {
    message,
    conversation_id: conversationId,
  };
  
  const { data } = await apiClient.post('/chat', payload);
  return data;
};
