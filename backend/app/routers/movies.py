from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies.auth import get_current_user_id
from app.dependencies.supabase import get_supabase_client
from app.schemas.movies import WatchedMovieCreate, WatchedMovieResponse

router = APIRouter(prefix="/movies", tags=["movies"])


@router.post("/watched", response_model=WatchedMovieResponse, status_code=201)
def add_watched_movie(
    data: WatchedMovieCreate,
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
) -> WatchedMovieResponse:
    row: dict[str, object] = {
        "user_id": user_id,
        "tmdb_id": data.tmdb_id,
        "title": data.title,
        "poster_url": data.poster_url,
        "release_year": data.release_year,
        "genre_ids": data.genre_ids,
        "initial_note": data.initial_note,
    }
    try:
        response = client.table("movies_watched").insert(row).execute()
    except Exception as exc:
        msg: str = str(exc).lower()
        if "duplicate" in msg or "unique" in msg or "23505" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Movie already in watched list",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al insertar película",
        ) from exc
    inserted: dict[str, object] = response.data[0]
    return WatchedMovieResponse.model_validate(inserted)


@router.get("/watched", response_model=list[WatchedMovieResponse])
def get_watched_movies(
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
) -> list[WatchedMovieResponse]:
    response = (
        client.table("movies_watched")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [WatchedMovieResponse.model_validate(row) for row in response.data]


@router.delete("/watched/{movie_id}", status_code=204)
def delete_watched_movie(
    movie_id: str,
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
) -> None:
    response = (
        client.table("movies_watched")
        .delete()
        .eq("id", movie_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Película no encontrada",
        )
