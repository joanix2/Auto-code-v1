import type { User, Repository, Ticket, UserLogin, UserCreate, TokenResponse, TicketCreate, Message, MessageCreate } from "../types";
import { API_BASE_URL } from "../config/env";

class ApiClient {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...this.getAuthHeader(),
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Auth endpoints
  async login(data: UserLogin): Promise<TokenResponse> {
    return this.request<TokenResponse>("/users/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async register(data: UserCreate): Promise<TokenResponse> {
    return this.request<TokenResponse>("/users/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/users/me");
  }

  // Repository endpoints
  async getRepositories(): Promise<Repository[]> {
    return this.request<Repository[]>("/repositories");
  }

  async getRepository(id: string): Promise<Repository> {
    return this.request<Repository>(`/repositories/${id}`);
  }

  async createRepository(data: Partial<Repository>): Promise<Repository> {
    return this.request<Repository>("/repositories", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateRepository(id: string, data: Partial<Repository>): Promise<Repository> {
    return this.request<Repository>(`/repositories/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteRepository(id: string): Promise<void> {
    return this.request<void>(`/repositories/${id}`, {
      method: "DELETE",
    });
  }

  // Ticket endpoints
  async getTickets(): Promise<Ticket[]> {
    return this.request<Ticket[]>("/tickets");
  }

  async getTicket(id: string): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${id}`);
  }

  async createTicket(data: TicketCreate): Promise<Ticket> {
    return this.request<Ticket>("/tickets", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateTicket(id: string, data: Partial<Ticket>): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteTicket(id: string): Promise<void> {
    return this.request<void>(`/tickets/${id}`, {
      method: "DELETE",
    });
  }

  // Message endpoints
  async getTicketMessages(ticketId: string): Promise<Message[]> {
    return this.request<Message[]>(`/messages/ticket/${ticketId}`);
  }

  async createMessage(data: MessageCreate): Promise<Message> {
    return this.request<Message>("/messages", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient();
