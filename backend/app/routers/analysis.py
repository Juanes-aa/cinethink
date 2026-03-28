from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies.auth import get_current_user_id
from app.dependencies.supabase import get_supabase_client
from app.schemas.analysis import CreateSessionRequest, SessionListResponse, SessionResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    data: CreateSessionRequest,
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
) -> SessionResponse:
    movie_result = (
        client.table("movies_watched")
        .select("id, title, tmdb_id, poster_url")
        .eq("id", str(data.watched_movie_id))
        .eq("user_id", user_id)
        .execute()
    )
    if not movie_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Película no encontrada en tu lista",
        )
    movie: dict[str, object] = movie_result.data[0]

    insert_result = (
        client.table("analysis_sessions")
        .insert({"user_id": user_id, "movie_id": str(data.watched_movie_id)})
        .execute()
    )
    session: dict[str, object] = insert_result.data[0]

    client.table("movies_watched").update({"has_analysis": True}).eq(
        "id", str(data.watched_movie_id)
    ).execute()

    return SessionResponse(
        id=session["id"],
        user_id=session["user_id"],
        watched_movie_id=data.watched_movie_id,
        movie_title=str(movie["title"]),
        tmdb_id=int(str(movie["tmdb_id"])),
        poster_url=movie.get("poster_url") if movie.get("poster_url") is not None else None,
        status=str(session["status"]),
        started_at=session["started_at"],
        closed_at=session.get("closed_at"),
    )


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
) -> SessionListResponse:
    response = (
        client.table("analysis_sessions")
        .select("*, movies_watched(title, tmdb_id, poster_url)")
        .eq("user_id", user_id)
        .order("started_at", desc=True)
        .execute()
    )
    rows: list[dict[str, object]] = response.data
    sessions: list[SessionResponse] = [
        SessionResponse(
            id=row["id"],
            user_id=row["user_id"],
            watched_movie_id=row["movie_id"],
            movie_title=str(row["movies_watched"]["title"]),
            tmdb_id=int(str(row["movies_watched"]["tmdb_id"])),
            poster_url=row["movies_watched"].get("poster_url"),
            status=str(row["status"]),
            started_at=row["started_at"],
            closed_at=row.get("closed_at"),
        )
        for row in rows
    ]
    return SessionListResponse(sessions=sessions, total=len(sessions))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
) -> SessionResponse:
    response = (
        client.table("analysis_sessions")
        .select("*, movies_watched(title, tmdb_id, poster_url)")
        .eq("id", session_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada",
        )
    row: dict[str, object] = response.data[0]

    if row["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        )

    return SessionResponse(
        id=row["id"],
        user_id=row["user_id"],
        watched_movie_id=row["movie_id"],
        movie_title=str(row["movies_watched"]["title"]),
        tmdb_id=int(str(row["movies_watched"]["tmdb_id"])),
        poster_url=row["movies_watched"].get("poster_url"),
        status=str(row["status"]),
        started_at=row["started_at"],
        closed_at=row.get("closed_at"),
    )
