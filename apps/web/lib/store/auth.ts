import { create } from "zustand";

import { api } from "@/lib/api";

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
  id: number;
  email: string;
  name: string;
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
    set({ token: null, user: null, error: null });
  },

  clearError: () => set({ error: null }),
}));
