from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    username: str
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    email: str
    username: str
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str


def _get_supabase_client() -> Client:
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(data: RegisterRequest) -> RegisterResponse:
    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener mínimo 8 caracteres",
        )

    if data.username.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario no puede estar vacío",
        )

    client: Client = _get_supabase_client()

    try:
        admin_response = client.auth.admin.create_user(
            {
                "email": data.email,
                "password": data.password,
                "email_confirm": True,
            }
        )
    except AuthApiError as exc:
        msg: str = str(exc).lower()
        if "already registered" in msg or "email" in msg or "duplicate" in msg:
            raise HTTPException(
                status_code=400,
                detail="Este email ya está registrado",
            ) from exc
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    user = admin_response.user
    if user is None:
        raise HTTPException(status_code=500, detail="No se pudo crear el usuario")

    user_id: str = str(user.id)
    try:
        client.table("profiles").upsert(
            {"id": user_id, "username": data.username}
        ).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar el perfil de usuario",
        ) from exc

    try:
        sign_in_response = client.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
    except AuthApiError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session = sign_in_response.session
    if session is None:
        raise HTTPException(status_code=500, detail="No se pudo crear la sesión")

    return RegisterResponse(
        user_id=user_id,
        email=data.email,
        username=data.username,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest) -> LoginResponse:
    client: Client = _get_supabase_client()

    try:
        sign_in_response = client.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
    except AuthApiError as exc:
        raise HTTPException(
            status_code=400, detail="Credenciales incorrectas"
        ) from exc

    session = sign_in_response.session
    if session is None:
        raise HTTPException(status_code=500, detail="No se pudo crear la sesión")

    user = sign_in_response.user
    if user is None:
        raise HTTPException(status_code=500, detail="No se pudo obtener el usuario")

    profile_response = (
        client.table("profiles")
        .select("username")
        .eq("id", str(user.id))
        .execute()
    )
    raw_username = profile_response.data[0].get("username") if profile_response.data else None
    username: str = raw_username if isinstance(raw_username, str) and raw_username.strip() != "" else data.email

    return LoginResponse(
        user_id=str(user.id),
        email=data.email,
        username=username,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(data: RefreshRequest) -> RefreshResponse:
    client: Client = _get_supabase_client()

    try:
        refresh_response = client.auth.refresh_session(data.refresh_token)
    except AuthApiError as exc:
        raise HTTPException(
            status_code=401, detail="Token inválido o expirado"
        ) from exc

    session = refresh_response.session
    if session is None:
        raise HTTPException(status_code=500, detail="No se pudo refrescar la sesión")

    return RefreshResponse(access_token=session.access_token)