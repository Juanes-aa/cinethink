from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateSessionRequest(BaseModel):
    watched_movie_id: UUID


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    watched_movie_id: UUID
    movie_title: str
    tmdb_id: int
    poster_url: str | None
    status: str
    started_at: datetime
    closed_at: datetime | None

    model_config = ConfigDict(populate_by_name=True)


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
