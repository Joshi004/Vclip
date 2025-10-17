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
 * @param {string|null} sessionId - Optional session ID
 * @returns {Promise<Object>} Chat response with reply, session_id, and context_used
 */
export const sendChatMessage = async (message, sessionId = null) => {
  try {
    const payload = { message };
    
    // Include session_id if provided
    if (sessionId) {
      payload.session_id = sessionId;
    }

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHAT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
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

/**
 * Create a new session
 * @returns {Promise<Object>} Session response with session_id
 */
export const createSession = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.SESSIONS}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Create session failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Create session error:', error);
    throw error;
  }
};

/**
 * Get all sessions
 * @param {number} limit - Maximum number of sessions
 * @returns {Promise<Object>} List of sessions
 */
export const getSessions = async (limit = 20) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}${API_ENDPOINTS.SESSIONS}?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`Get sessions failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Get sessions error:', error);
    throw error;
  }
};

/**
 * Get messages for a session
 * @param {string} sessionId - Session UUID
 * @returns {Promise<Object>} Session messages
 */
export const getSessionMessages = async (sessionId) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}${API_ENDPOINTS.SESSIONS}/${sessionId}/messages`
    );

    if (!response.ok) {
      throw new Error(`Get session messages failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Get session messages error:', error);
    throw error;
  }
};

/**
 * Delete a session
 * @param {string} sessionId - Session UUID
 * @returns {Promise<void>}
 */
export const deleteSession = async (sessionId) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}${API_ENDPOINTS.SESSIONS}/${sessionId}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok && response.status !== 204) {
      throw new Error(`Delete session failed: ${response.status}`);
    }
  } catch (error) {
    console.error('Delete session error:', error);
    throw error;
  }
};

