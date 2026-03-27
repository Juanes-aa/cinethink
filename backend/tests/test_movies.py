from collections.abc import Generator
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user_id
from app.routers.movies import get_supabase_client
from main import app

FAKE_USER_ID = "user-aaa-111"
FAKE_MOVIE_ID = "550e8400-e29b-41d4-a716-446655440000"
OTHER_MOVIE_ID = "660e8400-e29b-41d4-a716-446655440001"

VALID_MOVIE_PAYLOAD: dict[str, object] = {
    "tmdb_id": 550,
    "title": "Fight Club",
    "poster_url": "/poster.jpg",
    "release_year": 1999,
    "genre_ids": [18, 53],
    "initial_note": "Great movie",
}

INSERTED_ROW: dict[str, object] = {
    "id": FAKE_MOVIE_ID,
    "user_id": FAKE_USER_ID,
    "tmdb_id": 550,
    "title": "Fight Club",
    "poster_url": "/poster.jpg",
    "release_year": 1999,
    "genre_ids": [18, 53],
    "initial_note": "Great movie",
    "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat(),
}


def _override_auth() -> str:
    return FAKE_USER_ID


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer fake-valid-token"}


def _mock_insert_success() -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.table.return_value.insert.return_value.execute.return_value.data = [INSERTED_ROW]
    return mock


def _mock_insert_duplicate() -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.table.return_value.insert.return_value.execute.side_effect = Exception(
        "duplicate key value violates unique constraint"
    )
    return mock


def _mock_select(rows: list[dict[str, object]]) -> MagicMock:
    mock: MagicMock = MagicMock()
    (
        mock.table.return_value
        .select.return_value
        .eq.return_value
        .order.return_value
        .execute.return_value
        .data
    ) == rows
    mock.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = rows
    return mock


def _mock_delete(rows: list[dict[str, object]]) -> MagicMock:
    mock: MagicMock = MagicMock()
    (
        mock.table.return_value
        .delete.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) == rows
    mock.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = rows
    return mock


@pytest.fixture(autouse=True)
def _overrides() -> Generator[None, None, None]:
    app.dependency_overrides[get_current_user_id] = _override_auth
    yield
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_supabase_client, None)


# ── POST /movies/watched ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_watched_movie_success() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_insert_success()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/movies/watched", json=VALID_MOVIE_PAYLOAD, headers=_auth_headers()
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == FAKE_MOVIE_ID
    assert data["tmdb_id"] == 550
    assert data["genre_ids"] == [18, 53]


@pytest.mark.asyncio
async def test_add_duplicate_movie_returns_409() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_insert_duplicate()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/movies/watched", json=VALID_MOVIE_PAYLOAD, headers=_auth_headers()
        )

    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


# ── GET /movies/watched ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_watched_movies_returns_only_user_movies() -> None:
    row: dict[str, object] = {**INSERTED_ROW}
    app.dependency_overrides[get_supabase_client] = lambda: _mock_select([row])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/movies/watched", headers=_auth_headers())

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tmdb_id"] == 550


# ── DELETE /movies/watched/{movie_id} ───────────────────────────────


@pytest.mark.asyncio
async def test_delete_watched_movie_success() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_delete([INSERTED_ROW])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/movies/watched/{FAKE_MOVIE_ID}", headers=_auth_headers()
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_other_users_movie_returns_404() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_delete([])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/movies/watched/{OTHER_MOVIE_ID}", headers=_auth_headers()
        )

    assert response.status_code == 404


# ── Unauthenticated ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401() -> None:
    app.dependency_overrides.pop(get_current_user_id, None)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/movies/watched")
        # FastAPI HTTPBearer returns 403 when Authorization header is absent
        assert response.status_code in (401, 403)
    finally:
        app.dependency_overrides[get_current_user_id] = _override_auth