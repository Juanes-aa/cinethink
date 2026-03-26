import { useEffect, useState } from "react";
import { useParams, useNavigate, Navigate } from "react-router-dom";
import type { TmdbMovieDetail } from "../types/tmdb";
import { getMovieDetail, getDirector, getPosterUrl } from "../services/tmdb";

function formatRuntime(minutes: number | null): string {
  if (minutes === null || minutes === 0) return "—";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h.toString()}h ${m.toString()}min`;
}

function DetailSkeleton() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-8 md:flex-row">
      <div className="aspect-[2/3] w-full max-w-xs animate-pulse rounded-xl bg-gray-700" />
      <div className="flex flex-1 flex-col gap-4">
        <div className="h-8 w-3/4 animate-pulse rounded bg-gray-700" />
        <div className="h-4 w-1/2 animate-pulse rounded bg-gray-700" />
        <div className="h-4 w-1/3 animate-pulse rounded bg-gray-700" />
        <div className="h-24 w-full animate-pulse rounded bg-gray-700" />
        <div className="h-4 w-1/4 animate-pulse rounded bg-gray-700" />
      </div>
    </div>
  );
}

export default function MovieDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const numericId = Number(id);
  const isValidId = id !== undefined && !Number.isNaN(numericId) && numericId > 0;

  const [movie, setMovie] = useState<TmdbMovieDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isValidId) return;

    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    getMovieDetail(numericId, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setMovie(data);
        }
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (!controller.signal.aborted) {
          const message =
            err instanceof Error
              ? err.message
              : "Error desconocido al cargar la película";
          setError(message);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [numericId, isValidId]);

  if (!isValidId) {
    return <Navigate to="/search" replace />;
  }

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (error !== null) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <p className="text-center text-red-400">{error}</p>
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => { navigate("/search"); }}
            className="text-indigo-400 transition hover:text-indigo-300"
          >
            &larr; Buscar otra película
          </button>
        </div>
      </div>
    );
  }

  if (movie === null) {
    return null;
  }

  const posterUrl = getPosterUrl(movie.poster_path, "w500");
  const year = movie.release_date ? movie.release_date.slice(0, 4) : "—";
  const director = getDirector(movie);
  const topCast = movie.credits.cast.slice(0, 5);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <button
        type="button"
        onClick={() => { navigate("/search"); }}
        className="mb-6 inline-flex items-center gap-1 text-indigo-400 transition hover:text-indigo-300"
      >
        &larr; Buscar otra película
      </button>

      <div className="flex flex-col gap-8 md:flex-row">
        <div className="w-full flex-shrink-0 md:w-72">
          {posterUrl ? (
            <img
              src={posterUrl}
              alt={movie.title}
              className="w-full rounded-xl shadow-lg"
            />
          ) : (
            <div className="flex aspect-[2/3] w-full items-center justify-center rounded-xl bg-gray-700 text-gray-400">
              Sin imagen
            </div>
          )}
        </div>

        <div className="flex flex-1 flex-col gap-4">
          <h1 className="text-3xl font-bold text-white">
            {movie.title}{" "}
            <span className="text-lg font-normal text-gray-400">({year})</span>
          </h1>

          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-400">
            <span>{formatRuntime(movie.runtime)}</span>
            <span className="text-gray-600">•</span>
            <span>TMDB {movie.vote_average.toFixed(1)}</span>
            <span className="text-gray-600">•</span>
            <span>
              {movie.genres.map((g) => g.name).join(", ") || "Sin género"}
            </span>
          </div>

          {movie.overview && (
            <div>
              <h2 className="mb-1 text-sm font-semibold uppercase tracking-wider text-gray-500">
                Sinopsis
              </h2>
              <p className="leading-relaxed text-gray-300">{movie.overview}</p>
            </div>
          )}

          {director !== null && (
            <div>
              <h2 className="mb-1 text-sm font-semibold uppercase tracking-wider text-gray-500">
                Director
              </h2>
              <p className="text-white">{director}</p>
            </div>
          )}

          {topCast.length > 0 && (
            <div>
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-gray-500">
                Reparto principal
              </h2>
              <ul className="space-y-1">
                {topCast.map((member) => (
                  <li key={member.id} className="text-sm text-gray-300">
                    <span className="font-medium text-white">{member.name}</span>
                    {member.character && (
                      <span className="text-gray-500"> como {member.character}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
