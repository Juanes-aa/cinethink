import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { getSessions, deleteSession } from '../api/analysis'
import type { SessionSummary } from '../types/analysis'

const dateFormatter = new Intl.DateTimeFormat('es-ES', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

export default function HistoryPage() {
  const token = useAuthStore((state) => state.access_token)
  const navigate = useNavigate()

  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSessions(): Promise<void> {
      if (!token) return

      try {
        setLoading(true)
        const data = await getSessions(token)
        const sorted = [...data].sort(
          (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        )
        setSessions(sorted)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido')
      } finally {
        setLoading(false)
      }
    }

    void fetchSessions()
  }, [token])

  async function handleDelete(sessionId: string): Promise<void> {
    if (!token) return

    const confirmed = window.confirm('¿Estás seguro de que deseas eliminar esta sesión?')
    if (!confirmed) return

    try {
      await deleteSession(sessionId, token)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al eliminar')
    }
  }

  function handleSessionClick(sessionId: string): void {
    navigate(`/history/${sessionId}`)
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Historial de análisis</h1>
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Historial de análisis</h1>
        <p className="text-red-400">{error}</p>
      </div>
    )
  }

  if (sessions.length === 0) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Historial de análisis</h1>
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-8 text-center">
          <p className="mb-4 text-gray-300">
            Aún no has analizado ninguna película. Ve a tu biblioteca para empezar.
          </p>
          <Link
            to="/library"
            className="inline-block rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white transition hover:bg-indigo-500"
          >
            Ir a mi biblioteca
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">Historial de análisis</h1>

      <div className="space-y-4">
        {sessions.map((session) => (
          <div
            key={session.id}
            className="flex cursor-pointer items-center gap-4 rounded-lg border border-gray-700 bg-gray-800 p-4 transition hover:border-gray-600"
            onClick={() => handleSessionClick(session.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                handleSessionClick(session.id)
              }
            }}
            role="button"
            tabIndex={0}
          >
            <div className="h-20 w-14 flex-shrink-0 overflow-hidden rounded bg-gray-700">
              {session.movie_poster_url ? (
                <img
                  src={`https://image.tmdb.org/t/p/w92${session.movie_poster_url}`}
                  alt={session.movie_title}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-xs text-gray-500">
                  Sin imagen
                </div>
              )}
            </div>

            <div className="flex-1">
              <h2 className="font-semibold text-white">{session.movie_title}</h2>
              <p className="text-sm text-gray-400">
                {dateFormatter.format(new Date(session.started_at))}
              </p>
              <div className="mt-2 flex gap-2">
                <span
                  className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
                    session.status === 'active'
                      ? 'bg-green-900 text-green-300'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  {session.status === 'active' ? 'Activa' : 'Cerrada'}
                </span>
                {session.has_tags && (
                  <span className="inline-block rounded bg-indigo-900 px-2 py-0.5 text-xs font-medium text-indigo-300">
                    Con etiquetas
                  </span>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                void handleDelete(session.id)
              }}
              className="rounded p-2 text-gray-400 transition hover:bg-gray-700 hover:text-red-400"
              aria-label="Eliminar sesión"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
