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
        user_id=str(user.id),
        email=data.email,
        username=data.username,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )