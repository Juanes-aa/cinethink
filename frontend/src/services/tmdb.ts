import type { TmdbSearchResponse, TmdbSearchResult, TmdbMovieDetail } from "../types/tmdb";

const TMDB_BASE_URL = "https://api.themoviedb.org/3";
const TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p";

const rawKey: string | undefined = import.meta.env.VITE_TMDB_API_KEY;

if (!rawKey) {
  throw new Error(
    "[CineThink] La variable de entorno VITE_TMDB_API_KEY no está definida. " +
      "Crea un archivo frontend/.env.local con VITE_TMDB_API_KEY=tu_api_key."
  );
}

const TMDB_API_KEY: string = rawKey;

if (!TMDB_API_KEY) {
  throw new Error(
    "[CineThink] La variable de entorno VITE_TMDB_API_KEY no está definida. " +
      "Crea un archivo frontend/.env.local con VITE_TMDB_API_KEY=tu_api_key."
  );
}

export function getPosterUrl(
  posterPath: string | null,
  size: "w200" | "w500" | "original" = "w500"
): string | null {
  if (posterPath === null) {
    return null;
  }
  return `${TMDB_IMAGE_BASE}/${size}${posterPath}`;
}

export async function searchMovies(
  query: string,
  signal?: AbortSignal
): Promise<TmdbSearchResult[]> {
  if (query.trim() === "") {
    return [];
  }

  const url = `${TMDB_BASE_URL}/search/movie?api_key=${TMDB_API_KEY}&language=es-ES&query=${encodeURIComponent(query)}`;
  const response = await fetch(url, { signal });

  if (!response.ok) {
    throw new Error(`Error al buscar películas: HTTP ${response.status.toString()}`);
  }

  const data = (await response.json()) as TmdbSearchResponse;
  return data.results;
}

export async function getMovieDetail(
  id: number,
  signal?: AbortSignal
): Promise<TmdbMovieDetail> {
  const url = `${TMDB_BASE_URL}/movie/${id.toString()}?api_key=${TMDB_API_KEY}&language=es-ES&append_to_response=credits`;
  const response = await fetch(url, { signal });

  if (!response.ok) {
    throw new Error(`Error al obtener detalle de película: HTTP ${response.status.toString()}`);
  }

  const data = (await response.json()) as TmdbMovieDetail;
  return data;
}

export function getDirector(movie: TmdbMovieDetail): string | null {
  const director = movie.credits.crew.find((member) => member.job === "Director");
  return director ? director.name : null;
}
