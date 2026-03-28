from collections.abc import Generator
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user_id
from app.dependencies.supabase import get_supabase_client
from main import app

FAKE_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
FAKE_SESSION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
FAKE_MOVIE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
OTHER_USER_ID = "bbbbbbbb-0000-0000-0000-000000000002"

_STARTED_AT: str = datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat()

MOVIE_ROW: dict[str, object] = {
    "id": FAKE_MOVIE_ID,
    "title": "Fight Club",
    "tmdb_id": 550,
    "poster_url": "/poster.jpg",
}

SESSION_INSERT_ROW: dict[str, object] = {
    "id": FAKE_SESSION_ID,
    "user_id": FAKE_USER_ID,
    "movie_id": FAKE_MOVIE_ID,
    "status": "active",
    "started_at": _STARTED_AT,
    "closed_at": None,
}

SESSION_ROW_WITH_MOVIE: dict[str, object] = {
    "id": FAKE_SESSION_ID,
    "user_id": FAKE_USER_ID,
    "movie_id": FAKE_MOVIE_ID,
    "status": "active",
    "started_at": _STARTED_AT,
    "closed_at": None,
    "movies_watched": {
        "title": "Fight Club",
        "tmdb_id": 550,
        "poster_url": "/poster.jpg",
    },
}

SESSION_ROW_OTHER_USER: dict[str, object] = {
    **SESSION_ROW_WITH_MOVIE,
    "user_id": OTHER_USER_ID,
}


def _override_auth() -> str:
    return FAKE_USER_ID


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer fake-valid-token"}


def _mock_create_session_success() -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        MOVIE_ROW
    ]
    mock.table.return_value.insert.return_value.execute.return_value.data = [
        SESSION_INSERT_ROW
    ]
    return mock


def _mock_movie_not_found() -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    return mock


def _mock_list_sessions(rows: list[dict[str, object]]) -> MagicMock:
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


def _mock_get_session(rows: list[dict[str, object]]) -> MagicMock:
    mock: MagicMock = MagicMock()
    (
        mock.table.return_value
        .select.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) == rows
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = rows
    return mock


@pytest.fixture(autouse=True)
def _overrides() -> Generator[None, None, None]:
    app.dependency_overrides[get_current_user_id] = _override_auth
    yield
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_supabase_client, None)


# ── POST /analysis/sessions ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_session_success() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_create_session_success()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/analysis/sessions",
            json={"watched_movie_id": FAKE_MOVIE_ID},
            headers=_auth_headers(),
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == FAKE_SESSION_ID
    assert data["watched_movie_id"] == FAKE_MOVIE_ID


@pytest.mark.asyncio
async def test_create_session_movie_not_found() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_movie_not_found()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/analysis/sessions",
            json={"watched_movie_id": FAKE_MOVIE_ID},
            headers=_auth_headers(),
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_session_movie_belongs_to_other_user() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_movie_not_found()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/analysis/sessions",
            json={"watched_movie_id": FAKE_MOVIE_ID},
            headers=_auth_headers(),
        )

    assert response.status_code == 404


# ── GET /analysis/sessions ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_sessions_empty() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_list_sessions([])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/analysis/sessions", headers=_auth_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["sessions"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_sessions_with_data() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_list_sessions(
        [SESSION_ROW_WITH_MOVIE]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/analysis/sessions", headers=_auth_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["sessions"][0]["movie_title"] == "Fight Club"


# ── GET /analysis/sessions/{session_id} ─────────────────────────────


@pytest.mark.asyncio
async def test_get_session_success() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_get_session(
        [SESSION_ROW_WITH_MOVIE]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/analysis/sessions/{FAKE_SESSION_ID}", headers=_auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["id"] == FAKE_SESSION_ID


@pytest.mark.asyncio
async def test_get_session_not_found() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_get_session([])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/analysis/sessions/{FAKE_SESSION_ID}", headers=_auth_headers()
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_wrong_user() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_get_session(
        [SESSION_ROW_OTHER_USER]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/analysis/sessions/{FAKE_SESSION_ID}", headers=_auth_headers()
        )

    assert response.status_code == 403
