/**
 * User Types
 */

export interface User {
  id: string;
  username: string;
  email?: string;
  avatar_url?: string;
  github_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface UserPublic {
  id: string;
  username: string;
  email?: string;
  avatar_url?: string;
}

export interface UserCreate {
  username: string;
  email?: string;
  github_id?: number;
}

export interface UserUpdate {
  email?: string;
  avatar_url?: string;
}
