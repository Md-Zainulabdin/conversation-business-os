import { create } from "zustand";

import { api } from "@/lib/api";

const TOKEN_COOKIE = "token";

function setCookie(name: string, value: string, days = 7) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

function deleteCookie(name: string) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

interface RegisterData {
  email: string;
  password: string;
  name: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface User {
  id: string;
  email: string;
  name: string;
  store_name?: string | null;
  currency?: string;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
  register: (data: RegisterData) => Promise<void>;
  login: (data: LoginData) => Promise<void>;
  fetchMe: () => Promise<void>;
  updateProfile: (data: Partial<Pick<User, "name" | "store_name" | "currency">>) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  user: null,
  loading: false,
  error: null,

  register: async (data) => {
    set({ loading: true, error: null });
    try {
      await api.post<User>("/auth/register", data);
      set({ loading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : "Registration failed",
        loading: false,
      });
    }
  },

  login: async (data) => {
    set({ loading: true, error: null });
    try {
      const { access_token } = await api.post<{
        access_token: string;
      }>("/auth/login", data);
      localStorage.setItem("token", access_token);
      setCookie(TOKEN_COOKIE, access_token);

      const user = await api.get<User>("/auth/me");
      set({ token: access_token, user, loading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : "Login failed",
        loading: false,
      });
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    deleteCookie(TOKEN_COOKIE);
    set({ token: null, user: null, error: null });
  },

  fetchMe: async () => {
    try {
      const user = await api.get<User>("/auth/me");
      set({ user, loading: false, error: null });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : "Failed to load user",
        loading: false,
      });
    }
  },

  updateProfile: async (data) => {
    set({ loading: true, error: null });
    try {
      const user = await api.patch<User>("/auth/me", data);
      set({ user, loading: false, error: null });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : "Failed to update profile",
        loading: false,
      });
    }
  },

  clearError: () => set({ error: null }),
}));
