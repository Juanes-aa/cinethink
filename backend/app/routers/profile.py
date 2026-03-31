import json

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies.auth import get_current_user_id
from app.dependencies.supabase import get_supabase_client
from app.schemas.profile import SemanticProfileResponse, TopItem

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/semantic", response_model=SemanticProfileResponse)
def get_semantic_profile(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
) -> SemanticProfileResponse:
    result = (
        supabase.table("user_profile")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        return SemanticProfileResponse(
            user_id=user_id,
            temas_frecuentes=[],
            directores_afines=[],
            narrativa_predominante=None,
            nivel_filosofico_promedio=None,
            total_sesiones_analizadas=0,
            has_profile=False,
        )

    row: dict[str, object] = result.data[0]

    raw_temas: list[list[object]] = json.loads(str(row["temas_frecuentes"]))
    temas: list[TopItem] = [
        TopItem(value=str(item[0]), count=int(str(item[1]))) for item in raw_temas
    ]

    raw_directores: list[list[object]] = json.loads(str(row["directores_afines"]))
    directores: list[TopItem] = [
        TopItem(value=str(item[0]), count=int(str(item[1]))) for item in raw_directores
    ]

    return SemanticProfileResponse(
        user_id=user_id,
        temas_frecuentes=temas,
        directores_afines=directores,
        narrativa_predominante=str(row["narrativa_predominante"]) if row.get("narrativa_predominante") is not None else None,
        nivel_filosofico_promedio=str(row["nivel_filosofico_promedio"]) if row.get("nivel_filosofico_promedio") is not None else None,
        total_sesiones_analizadas=int(str(row["total_sesiones_analizadas"])),
        has_profile=True,
    )
