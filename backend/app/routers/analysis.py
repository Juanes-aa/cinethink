from fastapi import APIRouter, Depends, HTTPException, status
from groq import Groq
from supabase import Client

from app.dependencies.auth import get_current_user_id
from app.dependencies.groq_client import get_groq_client
from app.dependencies.supabase import get_supabase_client
from app.schemas.analysis import (
    ConversationResponse,
    CreateSessionRequest,
    MessageResponse,
    SendMessageRequest,
    SessionListResponse,
    SessionResponse,
)

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


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse, status_code=201)
def send_message(
    session_id: str,
    data: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
    groq: Groq = Depends(get_groq_client),
) -> MessageResponse:
    session_result = (
        client.table("analysis_sessions")
        .select("id, status")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not session_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada",
        )
    session: dict[str, object] = session_result.data[0]
    if session["status"] == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sesión cerrada",
        )

    history_result = (
        client.table("analysis_messages")
        .select("role, content")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    history: list[dict[str, str]] = history_result.data

    user_insert_result = (
        client.table("analysis_messages")
        .insert({"session_id": session_id, "role": "user", "content": data.content})
        .execute()
    )
    user_row: dict[str, object] = user_insert_result.data[0]

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "Eres un analista cinematográfico experto. Analiza películas con profundidad "
                "intelectual, explorando temas, simbolismo, dirección, actuaciones y contexto "
                "histórico. Sé preciso, perspicaz y estimula el pensamiento crítico del usuario."
            ),
        },
        *[{"role": row["role"], "content": row["content"]} for row in history],
        {"role": "user", "content": data.content},
    ]

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )
    assistant_content: str = response.choices[0].message.content

    assistant_insert_result = (
        client.table("analysis_messages")
        .insert({"session_id": session_id, "role": "assistant", "content": assistant_content})
        .execute()
    )
    assistant_row: dict[str, object] = assistant_insert_result.data[0]

    return MessageResponse(
        id=assistant_row["id"],
        session_id=assistant_row["session_id"],
        role=assistant_row["role"],
        content=assistant_row["content"],
        created_at=assistant_row["created_at"],
    )


@router.get("/sessions/{session_id}/messages", response_model=ConversationResponse)
def get_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    client: Client = Depends(get_supabase_client),
) -> ConversationResponse:
    session_result = (
        client.table("analysis_sessions")
        .select("id, status")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not session_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada",
        )

    messages_result = (
        client.table("analysis_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    rows: list[dict[str, object]] = messages_result.data

    return ConversationResponse(
        session_id=session_id,
        messages=[
            MessageResponse(
                id=row["id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ],
    )
