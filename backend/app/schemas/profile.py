from pydantic import BaseModel


class TopItem(BaseModel):
    value: str
    count: int


class SemanticProfileResponse(BaseModel):
    user_id: str
    temas_frecuentes: list[TopItem]
    directores_afines: list[TopItem]
    narrativa_predominante: str | None
    nivel_filosofico_promedio: str | None
    total_sesiones_analizadas: int
    has_profile: bool
