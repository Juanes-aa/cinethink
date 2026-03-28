import json
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user_id
from app.dependencies.groq_client import get_groq_client
from app.dependencies.supabase import get_supabase_client
from app.services.ai_service import extract_semantic_tags
from main import app

FAKE_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
FAKE_SESSION_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
OTHER_USER_ID = "bbbbbbbb-0000-0000-0000-000000000002"

SESSION_ACTIVE: dict[str, object] = {
    "id": FAKE_SESSION_ID,
    "user_id": FAKE_USER_ID,
    "status": "active",
}

SESSION_CLOSED: dict[str, object] = {
    "id": FAKE_SESSION_ID,
    "user_id": FAKE_USER_ID,
    "status": "closed",
}

SESSION_OTHER_USER: dict[str, object] = {
    "id": FAKE_SESSION_ID,
    "user_id": OTHER_USER_ID,
    "status": "active",
}

USER_MESSAGE: dict[str, object] = {
    "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "session_id": FAKE_SESSION_ID,
    "role": "user",
    "content": "¿Qué simboliza el jabón en Fight Club?",
    "created_at": "2025-01-01T00:00:00+00:00",
}

ASSISTANT_MESSAGE: dict[str, object] = {
    "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    "session_id": FAKE_SESSION_ID,
    "role": "assistant",
    "content": "El jabón simboliza la purificación y la decadencia...",
    "created_at": "2025-01-01T00:00:01+00:00",
}

VALID_TAGS_JSON: str = json.dumps(
    {
        "temas_principales": ["consumismo", "identidad"],
        "tipo_narrativa": "drama psicológico",
        "dilemas_eticos": ["violencia como liberación"],
        "directores_estilo_similar": ["David Fincher"],
        "nivel_filosofico": "alto",
        "palabras_clave": ["jabón", "Tyler Durden"],
    }
)


def _override_auth() -> str:
    return FAKE_USER_ID


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer fake-valid-token"}


def _make_sessions_table(session_rows: list[dict[str, object]]) -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.select.return_value.eq.return_value.execute.return_value.data = session_rows
    return mock


def _make_messages_table(
    user_rows: list[dict[str, object]],
    all_rows: list[dict[str, object]],
) -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
        user_rows
    )
    mock.select.return_value.eq.return_value.order.return_value.execute.return_value.data = (
        all_rows
    )
    return mock


def _make_supabase_for_endpoint(
    session_rows: list[dict[str, object]],
    user_msg_rows: list[dict[str, object]],
    all_msg_rows: list[dict[str, object]] | None = None,
) -> MagicMock:
    supabase: MagicMock = MagicMock()
    sessions_table = _make_sessions_table(session_rows)
    messages_table = _make_messages_table(user_msg_rows, all_msg_rows or [])
    semantic_table: MagicMock = MagicMock()

    def _router(name: str) -> MagicMock:
        if name == "analysis_sessions":
            return sessions_table
        if name == "analysis_messages":
            return messages_table
        return semantic_table

    supabase.table.side_effect = _router
    return supabase


def _make_groq_valid() -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.chat.completions.create.return_value.choices[0].message.content = (
        VALID_TAGS_JSON
    )
    return mock


def _make_groq_failing() -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.chat.completions.create.side_effect = Exception("Groq unavailable")
    return mock


@pytest.fixture(autouse=True)
def _overrides() -> Generator[None, None, None]:
    app.dependency_overrides[get_current_user_id] = _override_auth
    yield
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_supabase_client, None)
    app.dependency_overrides.pop(get_groq_client, None)


# ── Test 1: Successful close ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_session_success() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _make_supabase_for_endpoint(
        [SESSION_ACTIVE], [USER_MESSAGE]
    )
    app.dependency_overrides[get_groq_client] = lambda: _make_groq_failing()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/analysis/sessions/{FAKE_SESSION_ID}/close",
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == FAKE_SESSION_ID
    assert data["status"] == "closed"
    assert data["closed_at"] is not None


# ── Test 2: Session already closed → 409 ────────────────────────────


@pytest.mark.asyncio
async def test_close_session_already_closed() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _make_supabase_for_endpoint(
        [SESSION_CLOSED], []
    )
    app.dependency_overrides[get_groq_client] = lambda: _make_groq_failing()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/analysis/sessions/{FAKE_SESSION_ID}/close",
            headers=_auth_headers(),
        )

    assert response.status_code == 409


# ── Test 3: Session belongs to another user → 403 ───────────────────


@pytest.mark.asyncio
async def test_close_session_wrong_user() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _make_supabase_for_endpoint(
        [SESSION_OTHER_USER], []
    )
    app.dependency_overrides[get_groq_client] = lambda: _make_groq_failing()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/analysis/sessions/{FAKE_SESSION_ID}/close",
            headers=_auth_headers(),
        )

    assert response.status_code == 403


# ── Test 4: Session not found → 404 ─────────────────────────────────


@pytest.mark.asyncio
async def test_close_session_not_found() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _make_supabase_for_endpoint(
        [], []
    )
    app.dependency_overrides[get_groq_client] = lambda: _make_groq_failing()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/analysis/sessions/{FAKE_SESSION_ID}/close",
            headers=_auth_headers(),
        )

    assert response.status_code == 404


# ── Test 5: Session has no user messages → 400 ──────────────────────


@pytest.mark.asyncio
async def test_close_session_no_messages() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _make_supabase_for_endpoint(
        [SESSION_ACTIVE], []
    )
    app.dependency_overrides[get_groq_client] = lambda: _make_groq_failing()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/analysis/sessions/{FAKE_SESSION_ID}/close",
            headers=_auth_headers(),
        )

    assert response.status_code == 400


# ── Test 6: extract_semantic_tags — Groq returns valid JSON ──────────


@pytest.mark.asyncio
async def test_extract_semantic_tags_success() -> None:
    messages_table: MagicMock = MagicMock()
    messages_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        USER_MESSAGE,
        ASSISTANT_MESSAGE,
    ]

    semantic_table: MagicMock = MagicMock()
    inserted_rows: list[dict[str, object]] = []

    def _capture_insert(data: dict[str, object]) -> MagicMock:
        inserted_rows.append(data)
        result: MagicMock = MagicMock()
        result.execute.return_value.data = [{"id": "new-tag-id"}]
        return result

    semantic_table.insert.side_effect = _capture_insert

    supabase_mock: MagicMock = MagicMock()

    def _router(name: str) -> MagicMock:
        if name == "analysis_messages":
            return messages_table
        return semantic_table

    supabase_mock.table.side_effect = _router

    await extract_semantic_tags(FAKE_SESSION_ID, supabase_mock, _make_groq_valid())

    assert len(inserted_rows) == 6
    tag_types: set[object] = {row["tag_type"] for row in inserted_rows}
    assert "temas_principales" in tag_types
    assert "tipo_narrativa" in tag_types
    assert "dilemas_eticos" in tag_types
    assert "directores_estilo_similar" in tag_types
    assert "nivel_filosofico" in tag_types
    assert "palabras_clave" in tag_types
    for row in inserted_rows:
        assert "tag_value" in row
        assert row["session_id"] == FAKE_SESSION_ID
        assert row["confidence"] == 1.0


# ── Test 7: extract_semantic_tags — Groq fails twice → no exception ──


@pytest.mark.asyncio
async def test_extract_semantic_tags_groq_fails_twice() -> None:
    messages_table: MagicMock = MagicMock()
    messages_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        USER_MESSAGE,
    ]

    semantic_table: MagicMock = MagicMock()
    supabase_mock: MagicMock = MagicMock()

    def _router(name: str) -> MagicMock:
        if name == "analysis_messages":
            return messages_table
        return semantic_table

    supabase_mock.table.side_effect = _router

    await extract_semantic_tags(FAKE_SESSION_ID, supabase_mock, _make_groq_failing())

    semantic_table.insert.assert_not_called()
