export interface WatchedMovie {
  id: string;
  tmdb_id: number;
  title: string;
  poster_url: string | null;
  release_year: number | null;
  genre_ids: number[];
  initial_note: string | null;
  created_at: string;
}

export interface WatchedMoviePayload {
  tmdb_id: number;
  title: string;
  poster_url: string | null;
  release_year: number | null;
  genre_ids: number[];
  initial_note?: string;
}
