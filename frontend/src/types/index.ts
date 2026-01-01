/**
 * Type definitions for the application
 */

export interface User {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserCreate {
  username: string;
  password: string;
  email?: string;
  name?: string;
  full_name?: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Repository {
  id: string;
  name: string;
  description?: string;
  url?: string;
  owner_id: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface RepositoryCreate {
  name: string;
  description?: string;
  url?: string;
}

export interface RepositoryUpdate {
  name?: string;
  description?: string;
  url?: string;
  is_active?: boolean;
}

export interface Ticket {
  id: string;
  title: string;
  description: string;
  repository_id: string;
  status: TicketStatus;
  priority: TicketPriority;
  ticket_type: TicketType;
  assignee_id?: string;
  created_by_id: string;
  created_at: string;
  updated_at?: string;
}

export interface TicketCreate {
  title: string;
  description: string;
  repository_id: string;
  priority?: TicketPriority;
  ticket_type?: TicketType;
  status?: TicketStatus;
}

export interface TicketUpdate {
  title?: string;
  description?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  ticket_type?: TicketType;
  assignee_id?: string;
}

export enum TicketStatus {
  OPEN = "open",
  IN_PROGRESS = "in_progress",
  CLOSED = "closed",
  CANCELLED = "cancelled",
}

export enum TicketPriority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum TicketType {
  FEATURE = "feature",
  BUG = "bug",
  ENHANCEMENT = "enhancement",
  DOCUMENTATION = "documentation",
}

export interface HealthCheck {
  status: string;
  database: {
    neo4j: string;
  };
}

export interface ApiError {
  detail: string;
  status?: number;
}
