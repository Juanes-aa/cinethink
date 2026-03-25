from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="CineThink API")


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