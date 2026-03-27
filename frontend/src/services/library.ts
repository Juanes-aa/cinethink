import type { WatchedMovie, WatchedMoviePayload } from "../types/library";

const API_URL: string = import.meta.env.VITE_API_URL as string;

export async function addWatchedMovie(
  token: string,
  payload: WatchedMoviePayload
): Promise<WatchedMovie> {
  const response: Response = await fetch(`${API_URL}/movies/watched`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (response.status === 409) {
    throw new Error("ALREADY_WATCHED");
  }

  if (!response.ok) {
    throw new Error(`Error al agregar película: HTTP ${response.status.toString()}`);
  }

  const result: WatchedMovie = (await response.json()) as WatchedMovie;
  return result;
}

export async function getWatchedMovies(token: string): Promise<WatchedMovie[]> {
  const response: Response = await fetch(`${API_URL}/movies/watched`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Error al obtener películas: HTTP ${response.status.toString()}`);
  }

  const result: WatchedMovie[] = (await response.json()) as WatchedMovie[];
  return result;
}

export async function deleteWatchedMovie(token: string, id: string): Promise<void> {
  const response: Response = await fetch(`${API_URL}/movies/watched/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Error al eliminar película: HTTP ${response.status.toString()}`);
  }
}
