/**
 * Central export for all types
 */

export * from './user';
export * from './repository';
export * from './issue';
export * from './message';
export * from './project';

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
