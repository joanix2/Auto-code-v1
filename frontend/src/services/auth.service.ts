import { apiClient } from "./api.service";
import type { UserLogin, UserCreate, TokenResponse, User } from "../types";

const TOKEN_KEY = "token";
const USER_KEY = "user";

class AuthService {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  }

  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  }

  getUser(): User | null {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  setUser(user: User): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  removeUser(): void {
    localStorage.removeItem(USER_KEY);
  }

  async login(username: string, password: string): Promise<TokenResponse> {
    const data: UserLogin = { username, password };
    const response = await apiClient.login(data);

    this.setToken(response.access_token);

    // Fetch and store user data
    const user = await apiClient.getCurrentUser();
    this.setUser(user);

    return response;
  }

  async register(username: string, password: string, email?: string, full_name?: string): Promise<TokenResponse> {
    const data: UserCreate = { username, password, email, full_name };
    const response = await apiClient.register(data);

    this.setToken(response.access_token);

    // Fetch and store user data
    const user = await apiClient.getCurrentUser();
    this.setUser(user);

    return response;
  }

  logout(): void {
    this.removeToken();
    this.removeUser();
  }

  async getCurrentUser(): Promise<User | null> {
    const token = this.getToken();
    if (!token) return null;

    try {
      const user = await apiClient.getCurrentUser();
      this.setUser(user);
      return user;
    } catch (error) {
      this.logout();
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

export const authService = new AuthService();
