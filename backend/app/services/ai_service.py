import json
import logging
from collections import Counter
from datetime import datetime, timezone

from groq import Groq
from supabase import Client

logger: logging.Logger = logging.getLogger(__name__)


def build_analysis_prompt(
    movie_title: str,
    movie_overview: str,
    prior_sessions: list[dict[str, str]],
) -> str:
    base_prompt: str = (
        f"Eres un analista cinematográfico experto analizando '{movie_title}'.\n"
        f"Sinopsis: {movie_overview}\n\n"
        "Tu rol es ser un socio de pensamiento crítico, no un reseñador. "
        "Profundiza, no resumas. Haz preguntas que generen más preguntas. "
        "Conecta con otras obras cuando sea relevante. "
        "Estimula el pensamiento crítico del usuario."
    )

    if len(prior_sessions) >= 2:
        prior_context_lines: list[str] = [
            f"- {session['title']}: {session['main_themes']}"
            for session in prior_sessions
        ]
        prior_context_block: str = (
            "\n\n--- PELÍCULAS ANALIZADAS ANTERIORMENTE POR EL USUARIO ---\n"
            + "\n".join(prior_context_lines)
            + "\nCuando sea relevante y natural, menciona conexiones con estas películas.\n"
            "No forces conexiones que no existen.\n"
            "--- FIN DE CONTEXTO PREVIO ---"
        )
        return base_prompt + prior_context_block

    return base_prompt


async def extract_semantic_tags(
    session_id: str, supabase: Client, groq_client: Groq
) -> None:
    try:
        messages_result = (
            supabase.table("analysis_messages")
            .select("role, content")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        messages: list[dict[str, str]] = messages_result.data

        conversation_text: str = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in messages
        )

        base_prompt: str = (
            "Analyze this film analysis conversation and extract semantic tags.\n\n"
            f"CONVERSATION:\n{conversation_text}\n\n"
            "Respond with ONLY this JSON (no preamble, no markdown, no text before or after):\n"
            '{\n'
            '  "temas_principales": ["..."],\n'
            '  "tipo_narrativa": "...",\n'
            '  "dilemas_eticos": ["..."],\n'
            '  "directores_estilo_similar": ["..."],\n'
            '  "nivel_filosofico": "bajo|medio|alto",\n'
            '  "palabras_clave": ["..."]\n'
            '}'
        )

        tags: dict[str, object] = {}
        try:
            first_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": base_prompt}],
                stream=False,
            )
            raw: str = first_response.choices[0].message.content
            tags = json.loads(raw)
        except Exception:
            retry_prompt: str = (
                base_prompt
                + "\n\nIMPORTANT: respond with ONLY raw JSON, no text before or after."
            )
            try:
                retry_response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": retry_prompt}],
                    stream=False,
                )
                raw = retry_response.choices[0].message.content
                tags = json.loads(raw)
            except Exception as exc:
                logger.error(
                    "extract_semantic_tags: failed for session %s after retry: %s",
                    session_id,
                    exc,
                )
                return

        for key, value in tags.items():
            tag_value: str = (
                json.dumps(value) if isinstance(value, list) else str(value)
            )
            supabase.table("semantic_tags").insert(
                {
                    "session_id": session_id,
                    "tag_type": key,
                    "tag_value": tag_value,
                    "confidence": 1.0,
                }
            ).execute()

        session_result = (
            supabase.table("analysis_sessions")
            .select("user_id")
            .eq("id", session_id)
            .execute()
        )
        if session_result.data:
            user_id: str = str(session_result.data[0]["user_id"])
            build_user_profile(user_id, supabase)

    except Exception as exc:
        logger.error(
            "extract_semantic_tags: unexpected error for session %s: %s",
            session_id,
            exc,
        )
        return


def _mode(values: list[str]) -> str | None:
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def build_user_profile(user_id: str, supabase: Client) -> None:
    try:
        sessions_result = (
            supabase.table("analysis_sessions")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "closed")
            .execute()
        )
        if not sessions_result.data:
            return

        session_ids: list[str] = [s["id"] for s in sessions_result.data]
        tags_result = (
            supabase.table("semantic_tags")
            .select("tag_type, tag_value")
            .in_("session_id", session_ids)
            .execute()
        )

        temas: Counter[str] = Counter()
        directores: Counter[str] = Counter()
        narrativas: Counter[str] = Counter()
        nivel_filosofico_values: list[str] = []

        for tag in tags_result.data:
            if tag["tag_type"] == "temas_principales":
                items: list[str] = json.loads(tag["tag_value"])
                for item in items:
                    temas[item] += 1
            elif tag["tag_type"] == "directores_estilo_similar":
                items = json.loads(tag["tag_value"])
                for item in items:
                    directores[item] += 1
            elif tag["tag_type"] == "tipo_narrativa":
                narrativas[tag["tag_value"]] += 1
            elif tag["tag_type"] == "nivel_filosofico":
                nivel_filosofico_values.append(tag["tag_value"])

        profile_data: dict[str, object] = {
            "user_id": user_id,
            "temas_frecuentes": json.dumps(temas.most_common(10)),
            "directores_afines": json.dumps(directores.most_common(10)),
            "narrativa_predominante": narrativas.most_common(1)[0][0] if narrativas else None,
            "nivel_filosofico_promedio": _mode(nivel_filosofico_values),
            "total_sesiones_analizadas": len(session_ids),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        supabase.table("user_profile").upsert(profile_data, on_conflict="user_id").execute()

    except Exception as exc:
        logger.error(
            "build_user_profile: unexpected error for user %s: %s",
            user_id,
            exc,
        )
        return
