/**
 * API URLs Helper
 * Centralized API endpoint URLs for easy management
 */

import { API_BASE_URL } from "../config/env";

export const API_URLS = {
  // Auth
  AUTH_GITHUB_LOGIN: `${API_BASE_URL}/auth/github/login`,
  AUTH_GITHUB_DISCONNECT: `${API_BASE_URL}/auth/github/disconnect`,

  // Repositories
  REPOSITORIES: `${API_BASE_URL}/repositories`,
  REPOSITORIES_SYNC: `${API_BASE_URL}/repositories/sync-github`,
  repository: (id: string | number) => `${API_BASE_URL}/repositories/${id}`,

  // Tickets
  TICKETS: `${API_BASE_URL}/tickets`,
  TICKETS_PROCESSING_START: `${API_BASE_URL}/tickets/processing/start`,
  TICKETS_REORDER: `${API_BASE_URL}/tickets/reorder`,
  ticket: (id: string | number) => `${API_BASE_URL}/tickets/${id}`,
  ticketsByRepository: (repositoryId: string | number) => `${API_BASE_URL}/tickets/repository/${repositoryId}`,
} as const;

export { API_BASE_URL };
