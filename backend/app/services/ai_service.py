import json
import logging

from groq import Groq
from supabase import Client

logger: logging.Logger = logging.getLogger(__name__)


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

    except Exception as exc:
        logger.error(
            "extract_semantic_tags: unexpected error for session %s: %s",
            session_id,
            exc,
        )
        return
