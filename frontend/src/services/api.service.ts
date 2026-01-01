/**
 * API Client Service
 * Centralized HTTP client for backend communication
 */

import type { User, UserCreate, TokenResponse, Repository, RepositoryCreate, RepositoryUpdate, Ticket, TicketCreate, TicketUpdate, HealthCheck, ApiError } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  private getAuthHeader(): Record<string, string> {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error: ApiError = await response.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return null as T;
      }

      return await response.json();
    } catch (error) {
      console.error("API request failed:", error);
      throw error;
    }
  }

  // Auth endpoints
  async login(username: string, password: string): Promise<TokenResponse> {
    return this.request<TokenResponse>("/users/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  async register(userData: UserCreate): Promise<User> {
    return this.request<User>("/users/", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/users/me");
  }

  // Users endpoints
  async getUsers(skip = 0, limit = 100): Promise<User[]> {
    return this.request<User[]>(`/users/?skip=${skip}&limit=${limit}`);
  }

  async getUser(userId: string): Promise<User> {
    return this.request<User>(`/users/${userId}`);
  }

  async updateUser(userId: string, userData: Partial<User>): Promise<User> {
    return this.request<User>(`/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(userId: string): Promise<void> {
    return this.request<void>(`/users/${userId}`, {
      method: "DELETE",
    });
  }

  // Repositories endpoints
  async getRepositories(skip = 0, limit = 100): Promise<Repository[]> {
    return this.request<Repository[]>(`/repositories/?skip=${skip}&limit=${limit}`);
  }

  async getRepository(repoId: string): Promise<Repository> {
    return this.request<Repository>(`/repositories/${repoId}`);
  }

  async createRepository(repoData: RepositoryCreate): Promise<Repository> {
    return this.request<Repository>("/repositories/", {
      method: "POST",
      body: JSON.stringify(repoData),
    });
  }

  async updateRepository(repoId: string, repoData: RepositoryUpdate): Promise<Repository> {
    return this.request<Repository>(`/repositories/${repoId}`, {
      method: "PUT",
      body: JSON.stringify(repoData),
    });
  }

  async deleteRepository(repoId: string): Promise<void> {
    return this.request<void>(`/repositories/${repoId}`, {
      method: "DELETE",
    });
  }

  // Tickets endpoints
  async getTickets(skip = 0, limit = 100): Promise<Ticket[]> {
    return this.request<Ticket[]>(`/tickets/?skip=${skip}&limit=${limit}`);
  }

  async getTicket(ticketId: string): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${ticketId}`);
  }

  async createTicket(ticketData: TicketCreate): Promise<Ticket> {
    return this.request<Ticket>("/tickets/", {
      method: "POST",
      body: JSON.stringify(ticketData),
    });
  }

  async updateTicket(ticketId: string, ticketData: TicketUpdate): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${ticketId}`, {
      method: "PUT",
      body: JSON.stringify(ticketData),
    });
  }

  async deleteTicket(ticketId: string): Promise<void> {
    return this.request<void>(`/tickets/${ticketId}`, {
      method: "DELETE",
    });
  }

  // Health check
  async healthCheck(): Promise<HealthCheck> {
    return this.request<HealthCheck>("/health");
  }
}

export const apiClient = new ApiClient();
export default apiClient;
