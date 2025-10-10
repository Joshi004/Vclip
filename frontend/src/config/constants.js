/**
 * Application configuration and constants
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8088';

// API Endpoints
export const API_ENDPOINTS = {
  HEALTH: '/health',
  CHAT: '/chat',
};

// UI Constants
export const UI_CONSTANTS = {
  MAX_MESSAGE_WIDTH: '70%',
  INPUT_MAX_ROWS: 4,
  CONTAINER_MAX_WIDTH: 'md',
};

// Message roles
export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
};

