/**
 * Application configuration
 * Centralized environment variables and constants
 */

// API Base URL - use VITE_API_URL from env, or detect from window location in production
const getApiUrl = (): string => {
  // If VITE_API_URL is set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // In production (when served from the same domain), use relative path or detected host
  if (import.meta.env.PROD) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000/api`;
  }

  // Development fallback
  return "http://localhost:8000/api";
};

export const API_URL = getApiUrl();
export const API_BASE_URL = API_URL; // Alias for compatibility

// Other configuration
export const APP_NAME = "AutoCode";
export const APP_VERSION = "1.0.0";

// API endpoints
export const API_ENDPOINTS = {
  // Auth
  AUTH_REGISTER: "/users/register",
  AUTH_LOGIN: "/users/login",
  AUTH_ME: "/users/me",

  // Users
  USERS: "/users",

  // Repositories
  REPOSITORIES: "/repositories",

  // Tickets
  TICKETS: "/tickets",
} as const;

// Build full API URL
export const buildApiUrl = (endpoint: string): string => {
  return `${API_URL}${endpoint}`;
};

export default {
  API_URL,
  APP_NAME,
  APP_VERSION,
  API_ENDPOINTS,
  buildApiUrl,
};
