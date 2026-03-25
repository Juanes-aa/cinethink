from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from supabase_auth.errors import AuthApiError

from main import app


def _make_mock_client(scenario: str) -> MagicMock:
    mock_client: MagicMock = MagicMock()

    if scenario == "success":
        mock_user: MagicMock = MagicMock()
        mock_user.id = "fake-uuid-123"

        mock_admin_response: MagicMock = MagicMock()
        mock_admin_response.user = mock_user
        mock_client.auth.admin.create_user.return_value = mock_admin_response

        mock_session: MagicMock = MagicMock()
        mock_session.access_token = "fake-access"
        mock_session.refresh_token = "fake-refresh"

        mock_sign_in_response: MagicMock = MagicMock()
        mock_sign_in_response.session = mock_session
        mock_client.auth.sign_in_with_password.return_value = mock_sign_in_response

    elif scenario == "duplicate":
        mock_client.auth.admin.create_user.side_effect = AuthApiError(
            message="User already registered", status=422, code=None
        )

    return mock_client


@pytest.mark.asyncio
@patch("routers.auth._get_supabase_client")
async def test_register_success(mock_get_client: MagicMock) -> None:
    mock_get_client.return_value = _make_mock_client("success")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload: dict[str, str] = {
            "email": "new@example.com",
            "username": "testuser",
            "password": "securepass123",
        }
        response = await client.post("/auth/register", json=payload)

    assert response.status_code == 201
    data: dict[str, str] = response.json()
    assert data["user_id"] == "fake-uuid-123"
    assert data["email"] == "new@example.com"
    assert data["username"] == "testuser"
    assert data["access_token"] == "fake-access"
    assert data["refresh_token"] == "fake-refresh"


@pytest.mark.asyncio
@patch("routers.auth._get_supabase_client")
async def test_register_duplicate_email(mock_get_client: MagicMock) -> None:
    mock_get_client.return_value = _make_mock_client("duplicate")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload: dict[str, str] = {
            "email": "dup@example.com",
            "username": "user1",
            "password": "securepass123",
        }
        response = await client.post("/auth/register", json=payload)

    assert response.status_code == 400
    detail: str = response.json()["detail"].lower()
    assert "email" in detail


@pytest.mark.asyncio
async def test_register_short_password() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload: dict[str, str] = {
            "email": "shortpass@example.com",
            "username": "testuser2",
            "password": "1234567",  # 7 chars - too short
        }
        response = await client.post("/auth/register", json=payload)

    assert response.status_code == 400
    detail: str = response.json()["detail"].lower()
    assert "contraseña" in detail or "password" in detail