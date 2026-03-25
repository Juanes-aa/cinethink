import { create } from "zustand";

interface AuthUser {
  user_id: string;
  email: string;
  username: string;
}

interface AuthState {
  user: AuthUser | null;
  access_token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: AuthUser, access_token: string, refresh_token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  access_token: null,
  isAuthenticated: false,

  setAuth: (user: AuthUser, access_token: string, refresh_token: string) => {
    localStorage.setItem("ct_refresh_token", refresh_token);
    set({ user, access_token, isAuthenticated: true });
  },

  clearAuth: () => {
    localStorage.removeItem("ct_refresh_token");
    set({ user: null, access_token: null, isAuthenticated: false });
  },
}));
