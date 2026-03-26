export interface TmdbSearchResult {
  id: number;
  title: string;
  poster_path: string | null;
  release_date: string;
  genre_ids: number[];
  overview: string;
}

export interface TmdbSearchResponse {
  results: TmdbSearchResult[];
  total_results: number;
  total_pages: number;
}

export interface TmdbCastMember {
  id: number;
  name: string;
  character: string;
  profile_path: string | null;
  order: number;
}

export interface TmdbCrewMember {
  id: number;
  name: string;
  job: string;
  department: string;
}

export interface TmdbMovieDetail {
  id: number;
  title: string;
  overview: string;
  poster_path: string | null;
  backdrop_path: string | null;
  release_date: string;
  runtime: number | null;
  vote_average: number;
  vote_count: number;
  genres: Array<{ id: number; name: string }>;
  credits: {
    cast: TmdbCastMember[];
    crew: TmdbCrewMember[];
  };
}
