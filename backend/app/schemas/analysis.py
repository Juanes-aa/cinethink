from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


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


class SendMessageRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío")
        return v.strip()


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    session_id: UUID
    messages: list[MessageResponse]
