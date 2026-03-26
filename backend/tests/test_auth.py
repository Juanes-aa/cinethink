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


# ── Login tests ──────────────────────────────────────────────────────


def _make_login_mock_client(scenario: str) -> MagicMock:
    mock_client: MagicMock = MagicMock()

    if scenario == "success":
        mock_user: MagicMock = MagicMock()
        mock_user.id = "login-uuid-456"
        mock_user.email = "user@example.com"

        mock_session: MagicMock = MagicMock()
        mock_session.access_token = "login-access-token"
        mock_session.refresh_token = "login-refresh-token"

        mock_sign_in_response: MagicMock = MagicMock()
        mock_sign_in_response.session = mock_session
        mock_sign_in_response.user = mock_user
        mock_client.auth.sign_in_with_password.return_value = mock_sign_in_response

        mock_profile_row: dict[str, str] = {"username": "testuser"}
        mock_execute: MagicMock = MagicMock()
        mock_execute.data = [mock_profile_row]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_execute

    elif scenario == "wrong_credentials":
        mock_client.auth.sign_in_with_password.side_effect = AuthApiError(
            message="Invalid login credentials", status=400, code=None
        )

    return mock_client


@pytest.mark.asyncio
@patch("routers.auth._get_supabase_client")
async def test_login_success(mock_get_client: MagicMock) -> None:
    mock_get_client.return_value = _make_login_mock_client("success")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload: dict[str, str] = {
            "email": "user@example.com",
            "password": "securepass123",
        }
        response = await client.post("/auth/login", json=payload)

    assert response.status_code == 200
    data: dict[str, str] = response.json()
    assert data["user_id"] == "login-uuid-456"
    assert data["email"] == "user@example.com"
    assert data["username"] == "testuser"
    assert data["access_token"] == "login-access-token"
    assert data["refresh_token"] == "login-refresh-token"


@pytest.mark.asyncio
@patch("routers.auth._get_supabase_client")
async def test_login_wrong_credentials(mock_get_client: MagicMock) -> None:
    mock_get_client.return_value = _make_login_mock_client("wrong_credentials")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload: dict[str, str] = {
            "email": "wrong@example.com",
            "password": "wrongpassword",
        }
        response = await client.post("/auth/login", json=payload)

    assert response.status_code == 400
    detail: str = response.json()["detail"].lower()
    assert "credenciales" in detail


# ── Refresh tests ────────────────────────────────────────────────────


def _make_refresh_mock_client(scenario: str) -> MagicMock:
    mock_client: MagicMock = MagicMock()

    if scenario == "success":
        mock_session: MagicMock = MagicMock()
        mock_session.access_token = "new-access-token"

        mock_refresh_response: MagicMock = MagicMock()
        mock_refresh_response.session = mock_session
        mock_client.auth.refresh_session.return_value = mock_refresh_response

    elif scenario == "invalid":
        mock_client.auth.refresh_session.side_effect = AuthApiError(
            message="Invalid refresh token", status=401, code=None
        )

    return mock_client


@pytest.mark.asyncio
@patch("routers.auth._get_supabase_client")
async def test_refresh_success(mock_get_client: MagicMock) -> None:
    mock_get_client.return_value = _make_refresh_mock_client("success")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload: dict[str, str] = {"refresh_token": "valid-refresh-token"}
        response = await client.post("/auth/refresh", json=payload)

    assert response.status_code == 200
    data: dict[str, str] = response.json()
    assert data["access_token"] == "new-access-token"


@pytest.mark.asyncio
@patch("routers.auth._get_supabase_client")
async def test_refresh_invalid_token(mock_get_client: MagicMock) -> None:
    mock_get_client.return_value = _make_refresh_mock_client("invalid")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload: dict[str, str] = {"refresh_token": "expired-token"}
        response = await client.post("/auth/refresh", json=payload)

    assert response.status_code == 401