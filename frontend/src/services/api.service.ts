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

  // GitHub Issues endpoints
  async getGitHubIssues(repositoryId: string, state: "open" | "closed" | "all" = "open"): Promise<GitHubIssuesSyncResponse> {
    return this.request<GitHubIssuesSyncResponse>(`/github-issues/sync/${repositoryId}?state=${state}`);
  }

  async importGitHubIssue(repositoryId: string, issueNumber: number): Promise<GitHubIssueImportResponse> {
    return this.request<GitHubIssueImportResponse>(`/github-issues/import/${repositoryId}/${issueNumber}`, {
      method: "POST",
    });
  }

  async importAllGitHubIssues(repositoryId: string, state: "open" | "closed" | "all" = "open"): Promise<GitHubIssuesBulkImportResponse> {
    return this.request<GitHubIssuesBulkImportResponse>(`/github-issues/import-all/${repositoryId}?state=${state}`, {
      method: "POST",
    });
  }

  async createGitHubIssueFromTicket(ticketId: string): Promise<GitHubIssueCreateResponse> {
    return this.request<GitHubIssueCreateResponse>("/github-issues/create", {
      method: "POST",
      body: JSON.stringify({ ticket_id: ticketId }),
    });
  }

  // Copilot Development endpoints
  async startCopilotDevelopment(data: CopilotDevelopmentRequest): Promise<CopilotDevelopmentResponse> {
    return this.request<CopilotDevelopmentResponse>("/copilot/start-development", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async checkCopilotStatus(repositoryId: string): Promise<CopilotStatusResponse> {
    return this.request<CopilotStatusResponse>(`/copilot/check-copilot-status/${repositoryId}`);
  }
}

// Copilot Development types
export interface CopilotDevelopmentRequest {
  ticket_id: string;
  custom_instructions?: string;
  base_branch?: string;
  model?: string;
}

export interface CopilotDevelopmentResponse {
  success: boolean;
  ticket_id: string;
  issue_number?: number;
  issue_url?: string;
  message: string;
}

export interface CopilotStatusResponse {
  enabled: boolean;
  message: string;
}

// GitHub Issues types
export interface GitHubIssueUser {
  login: string;
  avatar_url: string;
}

export interface GitHubIssue {
  number: number;
  title: string;
  body: string;
  state: "open" | "closed";
  html_url: string;
  labels: string[];
  created_at: string;
  updated_at: string;
  user: GitHubIssueUser;
}

export interface GitHubIssueWithImportStatus {
  issue: GitHubIssue;
  is_imported: boolean;
  ticket_id: string | null;
}

export interface GitHubIssuesSyncResponse {
  success: boolean;
  repository_id: string;
  repository_name: string;
  issues: GitHubIssueWithImportStatus[];
  total: number;
  imported: number;
  not_imported: number;
}

export interface GitHubIssueImportResponse {
  success: boolean;
  ticket_id: string;
  issue_number: number;
  issue_url: string;
  message: string;
}

export interface GitHubIssuesBulkImportResponse {
  success: boolean;
  repository_id: string;
  repository_name: string;
  summary: {
    total_issues: number;
    imported: number;
    skipped: number;
    errors: number;
  };
  imported_tickets: Array<{
    issue_number: number;
    ticket_id: string;
    title: string;
  }>;
  skipped_issues: Array<{
    issue_number: number;
    ticket_id: string;
    reason: string;
  }>;
  errors: Array<{
    issue_number: number;
    error: string;
  }>;
}

export interface GitHubIssueCreateResponse {
  success: boolean;
  ticket_id: string;
  issue_number: number;
  issue_url: string;
  message: string;
}

export const apiClient = new ApiClient();
