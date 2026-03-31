from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user_id
from app.dependencies.groq_client import get_groq_client
from app.dependencies.supabase import get_supabase_client
from main import app

FAKE_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
FAKE_SESSION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

SESSION_ACTIVE: dict[str, object] = {
    "id": FAKE_SESSION_ID,
    "user_id": FAKE_USER_ID,
    "status": "active",
    "movie_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "movies_watched": {
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
    },
}

SESSION_CLOSED: dict[str, object] = {
    "id": FAKE_SESSION_ID,
    "user_id": FAKE_USER_ID,
    "status": "closed",
    "movie_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "movies_watched": {
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
    },
}

INSERTED_USER_MSG: dict[str, object] = {
    "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
    "session_id": FAKE_SESSION_ID,
    "role": "user",
    "content": "¿Qué simboliza el jabón en Fight Club?",
    "created_at": "2025-01-01T00:00:00+00:00",
}

INSERTED_ASSISTANT_MSG: dict[str, object] = {
    "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "session_id": FAKE_SESSION_ID,
    "role": "assistant",
    "content": "El jabón en Fight Club simboliza...",
    "created_at": "2025-01-01T00:00:01+00:00",
}


def _override_auth() -> str:
    return FAKE_USER_ID


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer fake-valid-token"}


def _mock_groq(content: str) -> MagicMock:
    mock: MagicMock = MagicMock()
    mock.chat.completions.create.return_value.choices[0].message.content = content
    return mock


def _mock_supabase_send_success() -> MagicMock:
    mock: MagicMock = MagicMock()

    insert_call_count: list[int] = [0]

    def table_side_effect(name: str) -> MagicMock:
        table_mock: MagicMock = MagicMock()
        if name == "analysis_sessions":
            table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
                SESSION_ACTIVE
            ]
            table_mock.select.return_value.eq.return_value.eq.return_value.neq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        elif name == "analysis_messages":
            table_mock.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []

            def insert_side_effect(payload: dict[str, object]) -> MagicMock:
                insert_call_count[0] += 1
                result: MagicMock = MagicMock()
                if insert_call_count[0] == 1:
                    result.execute.return_value.data = [INSERTED_USER_MSG]
                else:
                    result.execute.return_value.data = [INSERTED_ASSISTANT_MSG]
                return result

            table_mock.insert.side_effect = insert_side_effect
        elif name == "semantic_tags":
            table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        return table_mock

    mock.table.side_effect = table_side_effect
    return mock


def _mock_supabase_session_not_found() -> MagicMock:
    mock: MagicMock = MagicMock()
    session_table: MagicMock = MagicMock()
    session_table.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

    def table_side_effect(name: str) -> MagicMock:
        return session_table

    mock.table.side_effect = table_side_effect
    return mock


def _mock_supabase_session_closed() -> MagicMock:
    mock: MagicMock = MagicMock()
    session_table: MagicMock = MagicMock()
    session_table.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        SESSION_CLOSED
    ]

    def table_side_effect(name: str) -> MagicMock:
        return session_table

    mock.table.side_effect = table_side_effect
    return mock


def _mock_supabase_get_messages(
    session_rows: list[dict[str, object]],
    message_rows: list[dict[str, object]],
) -> MagicMock:
    mock: MagicMock = MagicMock()
    session_table: MagicMock = MagicMock()
    messages_table: MagicMock = MagicMock()

    session_table.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
        session_rows
    )
    messages_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = (
        message_rows
    )

    def table_side_effect(name: str) -> MagicMock:
        if name == "analysis_sessions":
            return session_table
        return messages_table

    mock.table.side_effect = table_side_effect
    return mock


@pytest.fixture(autouse=True)
def _overrides() -> Generator[None, None, None]:
    app.dependency_overrides[get_current_user_id] = _override_auth
    yield
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_supabase_client, None)
    app.dependency_overrides.pop(get_groq_client, None)


# ── POST /analysis/sessions/{session_id}/messages ───────────────────


@pytest.mark.asyncio
async def test_send_message_success() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_supabase_send_success()
    app.dependency_overrides[get_groq_client] = lambda: _mock_groq(
        "El jabón en Fight Club simboliza..."
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/analysis/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "¿Qué simboliza el jabón en Fight Club?"},
            headers=_auth_headers(),
        )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "assistant"
    assert data["content"]


@pytest.mark.asyncio
async def test_send_message_session_not_found() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_supabase_session_not_found()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/analysis/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "¿Qué simboliza el jabón en Fight Club?"},
            headers=_auth_headers(),
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message_session_closed() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_supabase_session_closed()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/analysis/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "¿Qué simboliza el jabón en Fight Club?"},
            headers=_auth_headers(),
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_send_message_empty_content() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/analysis/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": ""},
            headers=_auth_headers(),
        )

    assert response.status_code == 422


# ── GET /analysis/sessions/{session_id}/messages ────────────────────


@pytest.mark.asyncio
async def test_get_messages_success() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_supabase_get_messages(
        [SESSION_ACTIVE], [INSERTED_USER_MSG, INSERTED_ASSISTANT_MSG]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/analysis/sessions/{FAKE_SESSION_ID}/messages",
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"


@pytest.mark.asyncio
async def test_get_messages_session_not_found() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_supabase_get_messages([], [])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/analysis/sessions/{FAKE_SESSION_ID}/messages",
            headers=_auth_headers(),
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_messages_empty_conversation() -> None:
    app.dependency_overrides[get_supabase_client] = lambda: _mock_supabase_get_messages(
        [SESSION_ACTIVE], []
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/analysis/sessions/{FAKE_SESSION_ID}/messages",
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []
