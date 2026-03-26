import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMovieSearch } from "../hooks/useMovieSearch";
import SearchBar from "../components/movies/SearchBar";
import MovieCard from "../components/movies/MovieCard";

function SkeletonCard() {
  return (
    <div className="flex flex-col overflow-hidden rounded-xl bg-gray-800 shadow-lg">
      <div className="aspect-[2/3] w-full animate-pulse bg-gray-700" />
      <div className="flex flex-col gap-2 p-3">
        <div className="h-4 w-3/4 animate-pulse rounded bg-gray-700" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-gray-700" />
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState<string>("");
  const { results, isLoading, error } = useMovieSearch(query);
  const navigate = useNavigate();

  const trimmedQuery = query.trim();
  const isQueryTooShort = trimmedQuery.length < 2;
  const hasSearched = !isQueryTooShort && !isLoading;
  const noResults = hasSearched && results.length === 0 && error === null;

  function handleMovieClick(id: number): void {
    navigate(`/movie/${id.toString()}`);
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-8 flex justify-center">
        <SearchBar value={query} onChange={setQuery} />
      </div>

      {error !== null && (
        <p className="text-center text-red-400">{error}</p>
      )}

      {isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {!isLoading && !error && results.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {results.map((movie) => (
            <MovieCard key={movie.id} movie={movie} onClick={handleMovieClick} />
          ))}
        </div>
      )}

      {noResults && (
        <p className="text-center text-gray-400">
          No encontramos películas para &apos;{trimmedQuery}&apos;. Intenta con otro título.
        </p>
      )}

      {isQueryTooShort && error === null && (
        <p className="text-center text-gray-500">Busca cualquier película para empezar.</p>
      )}
    </div>
  );
}
