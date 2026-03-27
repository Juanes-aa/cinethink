from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WatchedMovieCreate(BaseModel):
    tmdb_id: int
    title: str
    poster_url: str | None
    release_year: int | None
    genre_ids: list[int]
    initial_note: str | None = None


class WatchedMovieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tmdb_id: int
    title: str
    poster_url: str | None
    release_year: int | None
    genre_ids: list[int]
    initial_note: str | None
    created_at: datetime
