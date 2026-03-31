import type { SemanticProfile } from '../types/profile'

const API_URL = import.meta.env.VITE_API_URL as string

export async function getSemanticProfile(token: string): Promise<SemanticProfile> {
  const response: Response = await fetch(`${API_URL}/profile/semantic`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Error al obtener perfil: HTTP ${response.status.toString()}`)
  }

  return (await response.json()) as SemanticProfile
}
