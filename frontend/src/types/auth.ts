export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  user_id: string;
  email: string;
  username: string;
  access_token: string;
  refresh_token: string;
}

export interface AuthError {
  detail: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshResponse {
  access_token: string;
}
