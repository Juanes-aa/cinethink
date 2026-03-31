import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { getSemanticProfile } from '../api/profile'
import type { SemanticProfile, TopItem } from '../types/profile'

export default function ProfilePage() {
  const token = useAuthStore((state) => state.access_token)

  const [profile, setProfile] = useState<SemanticProfile | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [fetchTrigger, setFetchTrigger] = useState<number>(0)

  useEffect(() => {
    async function fetchProfile(): Promise<void> {
      if (!token) return

      try {
        setLoading(true)
        setError(null)
        const data = await getSemanticProfile(token)
        setProfile(data)
      } catch {
        setError('Error al cargar el perfil.')
      } finally {
        setLoading(false)
      }
    }

    void fetchProfile()
  }, [token, fetchTrigger])

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Perfil semántico</h1>
        <div className="space-y-6">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-lg border border-gray-700 bg-gray-800 p-6"
            >
              <div className="mb-4 h-4 w-40 rounded bg-gray-700" />
              <div className="space-y-2">
                <div className="h-3 w-full rounded bg-gray-700" />
                <div className="h-3 w-5/6 rounded bg-gray-700" />
                <div className="h-3 w-4/6 rounded bg-gray-700" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Perfil semántico</h1>
        <p className="mb-4 text-red-400">Error al cargar el perfil.</p>
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

  if (!profile || !profile.has_profile) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Perfil semántico</h1>
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-8 text-center">
          <p className="mb-2 text-lg font-semibold text-gray-200">
            Aún no tienes un perfil semántico.
          </p>
          <p className="mb-6 text-sm text-gray-400">
            Analiza tu primera película para empezar a construirlo.
          </p>
          <Link
            to="/library"
            className="inline-block rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white transition hover:bg-indigo-500"
          >
            Ir a tu biblioteca
          </Link>
        </div>
      </div>
    )
  }

  const maxCount: number =
    profile.temas_frecuentes.length > 0 ? profile.temas_frecuentes[0].count : 1

  const remaining: number = Math.max(0, 5 - profile.total_sesiones_analizadas)

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">Perfil semántico</h1>

      {/* Indicador de progreso */}
      <div className="mb-6 rounded-lg border border-indigo-800 bg-indigo-950 px-5 py-4">
        <p className="text-sm text-indigo-200">
          Has analizado{' '}
          <span className="font-semibold text-white">
            {profile.total_sesiones_analizadas}
          </span>{' '}
          {profile.total_sesiones_analizadas === 1 ? 'película' : 'películas'}.
        </p>
        {remaining > 0 && (
          <p className="mt-1 text-sm text-indigo-400">
            Analiza {remaining} más para un perfil más preciso.
          </p>
        )}
      </div>

      {/* Temas frecuentes */}
      {profile.temas_frecuentes.length > 0 && (
        <section className="mb-6 rounded-lg border border-gray-700 bg-gray-800 p-5">
          <h2 className="mb-4 text-lg font-semibold text-white">Temas frecuentes</h2>
          <div className="space-y-3">
            {profile.temas_frecuentes.map((item: TopItem) => {
              const pct: number = Math.round((item.count / maxCount) * 100)
              return (
                <div key={item.value}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="capitalize text-gray-200">{item.value}</span>
                    <span className="text-gray-400">{item.count}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-gray-700">
                    <div
                      className="h-2 rounded-full bg-indigo-500"
                      style={{ width: `${pct.toString()}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Directores afines */}
      {profile.directores_afines.length > 0 && (
        <section className="mb-6 rounded-lg border border-gray-700 bg-gray-800 p-5">
          <h2 className="mb-4 text-lg font-semibold text-white">Directores afines</h2>
          <ul className="space-y-2">
            {profile.directores_afines.map((item: TopItem) => (
              <li key={item.value} className="text-sm text-gray-300">
                <span className="font-medium text-white">{item.value}</span>{' '}
                <span className="text-gray-400">
                  ({item.count} {item.count === 1 ? 'mención' : 'menciones'})
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Datos del perfil */}
      <section className="rounded-lg border border-gray-700 bg-gray-800 p-5">
        <h2 className="mb-4 text-lg font-semibold text-white">Datos del perfil</h2>
        <dl className="space-y-3">
          <div className="flex justify-between text-sm">
            <dt className="text-gray-400">Narrativa predominante</dt>
            <dd className="font-medium text-white">
              {profile.narrativa_predominante ?? '—'}
            </dd>
          </div>
          <div className="flex justify-between text-sm">
            <dt className="text-gray-400">Nivel filosófico promedio</dt>
            <dd className="font-medium text-white">
              {profile.nivel_filosofico_promedio ?? '—'}
            </dd>
          </div>
        </dl>
      </section>
    </div>
  )
}
