from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user_id
from app.dependencies.supabase import get_supabase_client
from main import app

FAKE_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"


def _override_auth() -> str:
    return FAKE_USER_ID


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer fake-valid-token"}


@pytest.fixture(autouse=True)
def _overrides() -> Generator[None, None, None]:
    app.dependency_overrides[get_current_user_id] = _override_auth
    yield
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_supabase_client, None)


# ── TEST 1 — GET /profile/semantic sin perfil existente ──────────────


@pytest.mark.asyncio
async def test_get_semantic_profile_no_profile() -> None:
    mock: MagicMock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    app.dependency_overrides[get_supabase_client] = lambda: mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/profile/semantic", headers=_auth_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["has_profile"] is False
    assert data["temas_frecuentes"] == []
    assert data["directores_afines"] == []
    assert data["narrativa_predominante"] is None
    assert data["nivel_filosofico_promedio"] is None
    assert data["total_sesiones_analizadas"] == 0


# ── TEST 2 — GET /profile/semantic con perfil existente ──────────────


@pytest.mark.asyncio
async def test_get_semantic_profile_with_profile() -> None:
    profile_row: dict[str, object] = {
        "user_id": FAKE_USER_ID,
        "temas_frecuentes": '[["identidad", 3], ["memoria", 2]]',
        "directores_afines": '[["Tarkovsky", 2]]',
        "narrativa_predominante": "no lineal",
        "nivel_filosofico_promedio": "alto",
        "total_sesiones_analizadas": 3,
    }

    mock: MagicMock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        profile_row
    ]

    app.dependency_overrides[get_supabase_client] = lambda: mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/profile/semantic", headers=_auth_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["has_profile"] is True
    assert data["temas_frecuentes"][0]["value"] == "identidad"
    assert data["temas_frecuentes"][0]["count"] == 3
    assert data["temas_frecuentes"][1]["value"] == "memoria"
    assert data["directores_afines"][0]["value"] == "Tarkovsky"
    assert data["narrativa_predominante"] == "no lineal"
    assert data["nivel_filosofico_promedio"] == "alto"
    assert data["total_sesiones_analizadas"] == 3


# ── TEST 3 — build_user_profile con sesiones y tags reales ───────────


def test_build_user_profile_with_data() -> None:
    from app.services.ai_service import build_user_profile

    upsert_calls: list[dict[str, object]] = []

    def table_side_effect(table_name: str) -> MagicMock:
        table_mock: MagicMock = MagicMock()
        if table_name == "analysis_sessions":
            table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
                {"id": "sess-0001"},
                {"id": "sess-0002"},
            ]
        elif table_name == "semantic_tags":
            table_mock.select.return_value.in_.return_value.execute.return_value.data = [
                {"tag_type": "temas_principales", "tag_value": '["identidad", "tiempo"]'},
                {"tag_type": "directores_estilo_similar", "tag_value": '["Tarkovsky"]'},
                {"tag_type": "temas_principales", "tag_value": '["identidad"]'},
            ]
        elif table_name == "user_profile":

            def track_upsert(*args: object, **kwargs: object) -> MagicMock:
                upsert_calls.append({"args": args, "kwargs": kwargs})
                return MagicMock()

            table_mock.upsert.side_effect = track_upsert
        return table_mock

    mock_supabase: MagicMock = MagicMock()
    mock_supabase.table.side_effect = table_side_effect

    build_user_profile(FAKE_USER_ID, mock_supabase)

    assert len(upsert_calls) == 1


# ── TEST 4 — build_user_profile sin sesiones cerradas no hace upsert ─


def test_build_user_profile_no_sessions() -> None:
    from app.services.ai_service import build_user_profile

    upsert_calls: list[dict[str, object]] = []

    def table_side_effect(table_name: str) -> MagicMock:
        table_mock: MagicMock = MagicMock()
        if table_name == "analysis_sessions":
            table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        elif table_name == "user_profile":

            def track_upsert(*args: object, **kwargs: object) -> MagicMock:
                upsert_calls.append({"args": args, "kwargs": kwargs})
                return MagicMock()

            table_mock.upsert.side_effect = track_upsert
        return table_mock

    mock_supabase: MagicMock = MagicMock()
    mock_supabase.table.side_effect = table_side_effect

    build_user_profile(FAKE_USER_ID, mock_supabase)

    assert len(upsert_calls) == 0
