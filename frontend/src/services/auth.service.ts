/**
 * Authentication Service
 * Handles user authentication and token management
 */

import apiClient from "./api.service";
import type { User, UserCreate, TokenResponse } from "../types";

class AuthService {
  private readonly TOKEN_KEY = "token";
  private readonly USER_KEY = "user";

  /**
   * Login user with credentials
   */
  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await apiClient.login(username, password);

    if (response.access_token) {
      this.setToken(response.access_token);
    }

    if (response.user) {
      this.setUser(response.user);
    }

    return response;
  }

  /**
   * Register a new user
   */
  async register(userData: UserCreate): Promise<User> {
    const user = await apiClient.register(userData);

    // After registration, try to log in automatically
    if (user) {
      try {
        await this.login(userData.username, userData.password);
      } catch (error) {
        console.error("Auto-login after registration failed:", error);
      }
    }

    return user;
  }

  /**
   * Logout current user
   */
  logout(): void {
    this.removeToken();
    this.removeUser();
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    const token = this.getToken();
    if (!token) {
      return null;
    }

    try {
      const user = await apiClient.getCurrentUser();
      this.setUser(user);
      return user;
    } catch (error) {
      console.error("Failed to get current user:", error);
      this.logout();
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  /**
   * Get stored token
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Set token in storage
   */
  private setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Remove token from storage
   */
  private removeToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  /**
   * Get stored user
   */
  getUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) {
      return null;
    }

    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  /**
   * Set user in storage
   */
  private setUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  /**
   * Remove user from storage
   */
  private removeUser(): void {
    localStorage.removeItem(this.USER_KEY);
  }
}

export const authService = new AuthService();
export default authService;
