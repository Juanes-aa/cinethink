import os
from functools import lru_cache

from groq import Groq


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])
