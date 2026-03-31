import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { getSessionMessages, getSessions } from '../api/analysis'
import type { AnalysisMessage, SessionSummary } from '../types/analysis'

const timeFormatter = new Intl.DateTimeFormat('es-CO', {
  hour: '2-digit',
  minute: '2-digit',
})

export default function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const token = useAuthStore((state) => state.access_token)
  const navigate = useNavigate()

  const [messages, setMessages] = useState<AnalysisMessage[]>([])
  const [session, setSession] = useState<SessionSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [fetchTrigger, setFetchTrigger] = useState<number>(0)

  useEffect(() => {
    async function fetchData(): Promise<void> {
      if (!token || !sessionId) return

      try {
        setLoading(true)
        setError(null)

        const [messagesData, sessionsData] = await Promise.all([
          getSessionMessages(sessionId, token),
          getSessions(token),
        ])

        setMessages(messagesData)

        const currentSession = sessionsData.find((s) => s.id === sessionId)
        if (currentSession) {
          setSession(currentSession)
        }
      } catch {
        setError('Error al cargar la conversación.')
      } finally {
        setLoading(false)
      }
    }

    void fetchData()
  }, [token, sessionId, fetchTrigger])

  function handleContinueConversation(): void {
    if (session) {
      navigate(`/analysis/${session.movie_id}`)
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <div className="mb-6 h-5 w-32 animate-pulse rounded bg-gray-700" />
        <div className="space-y-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={`animate-pulse rounded-lg p-4 bg-gray-800 ${i % 2 === 0 ? 'mr-8' : 'ml-8'}`}
            >
              <div className="mb-2 h-3 w-24 rounded bg-gray-700" />
              <div className="h-4 w-full rounded bg-gray-700" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <button
          type="button"
          onClick={() => navigate('/history')}
          className="mb-4 inline-flex items-center text-sm text-gray-400 hover:text-white"
        >
          ← Volver al historial
        </button>
        <p className="mb-4 text-red-400">Error al cargar la conversación.</p>
        <button
          type="button"
          onClick={() => setFetchTrigger((n) => n + 1)}
          className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white transition hover:bg-indigo-500"
        >
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <button
        type="button"
        onClick={() => navigate('/history')}
        className="mb-4 inline-flex items-center text-sm text-gray-400 hover:text-white"
      >
        ← Volver al historial
      </button>

      {session && (
        <div className="mb-6">
          <h1 className="text-2xl font-bold">{session.movie_title}</h1>
          {session.status === 'active' && (
            <div className="mt-4 rounded-lg border border-yellow-700 bg-yellow-900/30 p-4">
              <p className="mb-3 text-yellow-300">Esta sesión está activa.</p>
              <button
                type="button"
                onClick={handleContinueConversation}
                className="rounded-lg bg-yellow-600 px-4 py-2 font-medium text-white transition hover:bg-yellow-500"
              >
                Continuar conversación
              </button>
            </div>
          )}
        </div>
      )}

      <div className="space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`rounded-lg p-4 ${
              message.role === 'user'
                ? 'ml-8 bg-indigo-900/50'
                : 'mr-8 bg-gray-800'
            }`}
          >
            <div className="mb-2 flex items-center justify-between">
              <span
                className={`text-xs font-medium ${
                  message.role === 'user' ? 'text-indigo-300' : 'text-gray-400'
                }`}
              >
                {message.role === 'user' ? 'Tú' : 'CineThink'}
              </span>
              <span className="text-xs text-gray-500">
                {timeFormatter.format(new Date(message.created_at))}
              </span>
            </div>
            <p className="whitespace-pre-wrap text-gray-200">{message.content}</p>
          </div>
        ))}

        {messages.length === 0 && (
          <p className="py-8 text-center text-gray-400">
            No hay mensajes en esta sesión.
          </p>
        )}
      </div>

      {session?.has_tags && (
        <div className="mt-8 rounded-lg border border-gray-700 bg-gray-800 p-4">
          <h2 className="mb-2 font-semibold text-white">Etiquetas extraídas</h2>
          <p className="text-sm text-gray-400">
            Etiquetas disponibles próximamente
          </p>
        </div>
      )}
    </div>
  )
}
