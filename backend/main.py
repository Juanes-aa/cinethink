from dotenv import load_dotenv
load_dotenv()  # PRIMERO, antes de cualquier import propio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os

from routers.auth import router as auth_router
from app.routers.movies import router as movies_router

app = FastAPI(title="CineThink API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "https://cinethink.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(movies_router)


def get_supabase_client() -> Client:
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db_check() -> dict[str, str]:
    client: Client = get_supabase_client()
    client.table("profiles").select("id").limit(1).execute()
    return {"status": "ok", "db": "connected"}