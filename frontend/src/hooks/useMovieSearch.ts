import { useEffect, useRef, useState } from "react";
import type { TmdbSearchResult } from "../types/tmdb";
import { searchMovies } from "../services/tmdb";

interface UseMovieSearchReturn {
  results: TmdbSearchResult[];
  isLoading: boolean;
  error: string | null;
}

export function useMovieSearch(query: string): UseMovieSearchReturn {
  const [results, setResults] = useState<TmdbSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    setIsLoading(true);

    const timerId = setTimeout(() => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      searchMovies(query, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) {
            setResults(data);
            setError(null);
          }
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === "AbortError") {
            return;
          }
          if (!controller.signal.aborted) {
            // Traducir errores de red a mensajes útiles en español
            let message = "Error desconocido al buscar películas";
            if (err instanceof TypeError && err.message === "Failed to fetch") {
              message = "No se pudo conectar. Verifica tu conexión a internet.";
            } else if (err instanceof Error) {
              message = err.message;
            }
            setError(message);
            setResults([]);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsLoading(false);
          }
        });
    }, 300);

    return () => {
      clearTimeout(timerId);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [query]);

  return { results, isLoading, error };
}
