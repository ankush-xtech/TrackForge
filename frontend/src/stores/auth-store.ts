import { create } from "zustand";
import { apiClient } from "@/lib/api-client";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: string;
  avatar_url: string | null;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  // Actions
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    organization_name: string;
  }) => Promise<void>;
  fetchMe: () => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken:
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null,
  refreshToken:
    typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null,
  isLoading: false,
  error: null,
  isAuthenticated:
    typeof window !== "undefined" ? !!localStorage.getItem("access_token") : false,

  setTokens: (accessToken, refreshToken) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
    }
    set({ accessToken, refreshToken, isAuthenticated: true, error: null });
  },

  setUser: (user) => set({ user }),

  clearError: () => set({ error: null }),

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient.post("/auth/login", { email, password });
      get().setTokens(res.data.access_token, res.data.refresh_token);
      if (res.data.user) {
        set({ user: res.data.user });
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || "Login failed. Please try again.";
      set({ error: errorMessage, isAuthenticated: false });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient.post("/auth/register", data);
      get().setTokens(res.data.access_token, res.data.refresh_token);
      if (res.data.user) {
        set({ user: res.data.user });
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || "Registration failed. Please try again.";
      set({ error: errorMessage, isAuthenticated: false });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  fetchMe: async () => {
    const { accessToken } = get();
    if (!accessToken) {
      set({ isAuthenticated: false });
      return;
    }

    set({ isLoading: true });
    try {
      const res = await apiClient.get("/auth/me");
      set({ user: res.data, isAuthenticated: true, error: null });
    } catch (err: any) {
      set({ user: null, isAuthenticated: false });
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    // Stop any active timer before logging out
    try {
      const activeRes = await apiClient.get("/tracking/time-entries/active");
      if (activeRes.data) {
        await apiClient.patch(
          `/tracking/time-entries/${activeRes.data.id}/stop`,
          { end_time: new Date().toISOString() }
        );
      }
    } catch {
      // Best effort — if it fails, proceed with logout anyway
    }

    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      error: null,
    });
    if (typeof window !== "undefined") {
      window.location.href = "/auth/login";
    }
  },
}));
