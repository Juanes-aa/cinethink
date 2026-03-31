import type { SessionSummary, AnalysisMessage } from '../types/analysis'

const API_URL: string = import.meta.env.VITE_API_URL as string

interface SessionsResponse {
  sessions: SessionSummary[]
  total: number
}

interface MessagesResponse {
  session_id: string
  messages: AnalysisMessage[]
}

export async function getSessions(token: string): Promise<SessionSummary[]> {
  const response: Response = await fetch(`${API_URL}/analysis/sessions`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Error al obtener sesiones: HTTP ${response.status.toString()}`)
  }

  const result: SessionsResponse = (await response.json()) as SessionsResponse
  return result.sessions
}

export async function getSessionMessages(
  sessionId: string,
  token: string
): Promise<AnalysisMessage[]> {
  const response: Response = await fetch(
    `${API_URL}/analysis/sessions/${sessionId}/messages`,
    {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )

  if (!response.ok) {
    throw new Error(`Error al obtener mensajes: HTTP ${response.status.toString()}`)
  }

  const result: MessagesResponse = (await response.json()) as MessagesResponse
  return result.messages
}

export async function deleteSession(sessionId: string, token: string): Promise<void> {
  const response: Response = await fetch(
    `${API_URL}/analysis/sessions/${sessionId}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )

  if (!response.ok) {
    throw new Error(`Error al eliminar sesión: HTTP ${response.status.toString()}`)
  }
}
