import type { TmdbSearchResult } from "../../types/tmdb";
import { getPosterUrl } from "../../services/tmdb";

interface MovieCardProps {
  movie: TmdbSearchResult;
  onClick: (id: number) => void;
}

export default function MovieCard({ movie, onClick }: MovieCardProps) {
  const posterUrl = getPosterUrl(movie.poster_path, "w500");
  const year = movie.release_date ? movie.release_date.slice(0, 4) : "—";
  const firstGenre = movie.genre_ids.length > 0 ? movie.genre_ids[0] : null;

  return (
    <button
      type="button"
      onClick={() => { onClick(movie.id); }}
      className="group flex cursor-pointer flex-col overflow-hidden rounded-xl bg-gray-800 text-left shadow-lg transition hover:scale-[1.02] hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
    >
      {posterUrl ? (
        <img
          src={posterUrl}
          alt={movie.title}
          className="aspect-[2/3] w-full object-cover"
          loading="lazy"
        />
      ) : (
        <div className="flex aspect-[2/3] w-full items-center justify-center bg-gray-700 text-gray-400">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-16 w-16"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
            />
          </svg>
        </div>
      )}

      <div className="flex flex-1 flex-col gap-1 p-3">
        <h3 className="line-clamp-2 text-sm font-semibold text-white group-hover:text-indigo-300">
          {movie.title}
        </h3>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{year}</span>
          {firstGenre !== null && (
            <>
              <span className="text-gray-600">•</span>
              <span>Género {firstGenre.toString()}</span>
            </>
          )}
        </div>
      </div>
    </button>
  );
}
