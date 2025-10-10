/**
 * API service layer for backend communication
 */

import { API_BASE_URL, API_ENDPOINTS } from '../config/constants';

/**
 * Check backend health
 * @returns {Promise<Object>} Health status response
 */
export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.HEALTH}`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

/**
 * Send a chat message to the backend
 * @param {string} message - The user's message
 * @param {Array} history - Conversation history
 * @returns {Promise<Object>} Chat response with reply
 */
export const sendChatMessage = async (message, history = []) => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHAT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        history,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `API error: ${response.status}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('Chat API error:', error);
    throw error;
  }
};

