import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { useLibraryStore } from "../stores/libraryStore";
import type { WatchedMovie } from "../types/library";

const POSTER_FALLBACK_CLASS =
  "flex aspect-[2/3] w-full items-center justify-center rounded-t-lg bg-gray-700 text-sm text-gray-400";

export default function LibraryPage() {
  const token = useAuthStore((state) => state.access_token);
  const movies = useLibraryStore((state) => state.movies);
  const isLoading = useLibraryStore((state) => state.isLoading);
  const error = useLibraryStore((state) => state.error);
  const fetchMovies = useLibraryStore((state) => state.fetchMovies);
  const removeMovie = useLibraryStore((state) => state.removeMovie);

  const [genreFilter, setGenreFilter] = useState<number | null>(null);
  const [yearFilter, setYearFilter] = useState<number | null>(null);

  useEffect(() => {
    if (token !== null) {
      void fetchMovies(token);
    }
  }, [token, fetchMovies]);

  const uniqueGenres: number[] = useMemo(() => {
    const genreSet = new Set<number>();
    for (const m of movies) {
      for (const g of m.genre_ids) {
        genreSet.add(g);
      }
    }
    return Array.from(genreSet).sort((a, b) => a - b);
  }, [movies]);

  const uniqueYears: number[] = useMemo(() => {
    const yearSet = new Set<number>();
    for (const m of movies) {
      if (m.release_year !== null) {
        yearSet.add(m.release_year);
      }
    }
    return Array.from(yearSet).sort((a, b) => b - a);
  }, [movies]);

  const filteredMovies: WatchedMovie[] = useMemo(() => {
    let result = movies;
    if (genreFilter !== null) {
      result = result.filter((m) => m.genre_ids.includes(genreFilter));
    }
    if (yearFilter !== null) {
      result = result.filter((m) => m.release_year === yearFilter);
    }
    return result;
  }, [movies, genreFilter, yearFilter]);

  function handleDelete(movie: WatchedMovie): void {
    if (token === null) return;
    const confirmed = window.confirm(
      `¿Eliminar "${movie.title}" de tu biblioteca?`
    );
    if (confirmed) {
      void removeMovie(token, movie.id);
    }
  }

  function handleGenreChange(e: React.ChangeEvent<HTMLSelectElement>): void {
    const value = e.target.value;
    setGenreFilter(value === "" ? null : Number(value));
  }

  function handleYearChange(e: React.ChangeEvent<HTMLSelectElement>): void {
    const value = e.target.value;
    setYearFilter(value === "" ? null : Number(value));
  }

  if (isLoading && movies.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-indigo-400" />
      </div>
    );
  }

  if (error !== null) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8">
        <p className="text-center text-red-400">{error}</p>
      </div>
    );
  }

  if (movies.length === 0) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-20 text-center">
        <p className="text-lg text-gray-400">
          Aún no has marcado ninguna película como vista
        </p>
        <Link
          to="/search"
          className="mt-4 inline-block text-indigo-400 transition hover:text-indigo-300"
        >
          Buscar películas &rarr;
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-white">Mi biblioteca</h1>

      <div className="mb-6 flex flex-wrap items-center gap-4">
        <select
          value={genreFilter === null ? "" : genreFilter.toString()}
          onChange={handleGenreChange}
          className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
        >
          <option value="">Todos los géneros</option>
          {uniqueGenres.map((gId) => (
            <option key={gId} value={gId.toString()}>
              Género {gId.toString()}
            </option>
          ))}
        </select>

        <select
          value={yearFilter === null ? "" : yearFilter.toString()}
          onChange={handleYearChange}
          className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
        >
          <option value="">Todos los años</option>
          {uniqueYears.map((y) => (
            <option key={y} value={y.toString()}>
              {y.toString()}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {filteredMovies.map((movie) => (
          <div
            key={movie.id}
            className="group relative overflow-hidden rounded-lg bg-gray-800 shadow-lg"
          >
            <Link to={`/movie/${movie.tmdb_id.toString()}`}>
              {movie.poster_url !== null ? (
                <img
                  src={movie.poster_url}
                  alt={movie.title}
                  className="aspect-[2/3] w-full rounded-t-lg object-cover"
                />
              ) : (
                <div className={POSTER_FALLBACK_CLASS}>Sin imagen</div>
              )}
            </Link>

            <div className="p-3">
              <h3 className="truncate text-sm font-semibold text-white">
                {movie.title}
              </h3>
              {movie.release_year !== null && (
                <p className="text-xs text-gray-400">
                  {movie.release_year.toString()}
                </p>
              )}
              {movie.initial_note !== null && movie.initial_note !== "" && (
                <p className="mt-1 line-clamp-2 text-xs text-gray-500">
                  {movie.initial_note}
                </p>
              )}

              <button
                type="button"
                onClick={() => { handleDelete(movie); }}
                className="mt-2 text-xs text-red-400 transition hover:text-red-300"
              >
                Eliminar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
