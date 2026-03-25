import type { RegisterRequest, AuthResponse, AuthError } from "../types/auth";

const API_URL: string = import.meta.env.VITE_API_URL as string;

export async function registerUser(data: RegisterRequest): Promise<AuthResponse> {
  const response: Response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorBody: AuthError = (await response.json()) as AuthError;
    throw new Error(errorBody.detail);
  }

  const result: AuthResponse = (await response.json()) as AuthResponse;
  return result;
}
