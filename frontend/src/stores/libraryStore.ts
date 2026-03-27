import { create } from "zustand";
import type { WatchedMovie, WatchedMoviePayload } from "../types/library";
import { addWatchedMovie, getWatchedMovies, deleteWatchedMovie } from "../services/library";

interface LibraryState {
  movies: WatchedMovie[];
  isLoading: boolean;
  error: string | null;
  fetchMovies: (token: string) => Promise<void>;
  addMovie: (token: string, payload: WatchedMoviePayload) => Promise<string | undefined>;
  removeMovie: (token: string, id: string) => Promise<void>;
}

export const useLibraryStore = create<LibraryState>((set) => ({
  movies: [],
  isLoading: false,
  error: null,

  fetchMovies: async (token: string): Promise<void> => {
    set({ isLoading: true, error: null });
    try {
      const movies: WatchedMovie[] = await getWatchedMovies(token);
      set({ movies, isLoading: false });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Error desconocido al cargar películas";
      set({ error: message, isLoading: false });
    }
  },

  addMovie: async (token: string, payload: WatchedMoviePayload): Promise<string | undefined> => {
    set({ isLoading: true, error: null });
    try {
      const newMovie: WatchedMovie = await addWatchedMovie(token, payload);
      set((state) => ({ movies: [newMovie, ...state.movies], isLoading: false }));
      return undefined;
    } catch (err: unknown) {
      set({ isLoading: false });
      if (err instanceof Error && err.message === "ALREADY_WATCHED") {
        return "ALREADY_WATCHED";
      }
      throw err;
    }
  },

  removeMovie: async (token: string, id: string): Promise<void> => {
    set({ isLoading: true, error: null });
    try {
      await deleteWatchedMovie(token, id);
      set((state) => ({
        movies: state.movies.filter((m) => m.id !== id),
        isLoading: false,
      }));
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Error desconocido al eliminar película";
      set({ error: message, isLoading: false });
    }
  },
}));
