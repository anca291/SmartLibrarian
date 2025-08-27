from __future__ import annotations

import logging
import time
from typing import List, Literal, Optional

from openai import OpenAI
from config import OPENAI_API_KEY

# Optional: langdetect is best-effort; we fallback to EN on errors
try:
    from langdetect import detect as _langdetect_detect  # type: ignore
except Exception:  # pragma: no cover
    _langdetect_detect = None  # type: ignore

logger = logging.getLogger("smart_librarian.gpt")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

Lang = Literal["ro", "en"]


class GPTService:
    """
    Small wrapper around OpenAI Chat Completions for book recommendations.
    - Uses new SDK.
    - English logs.
    - Retries on transient errors.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 600,
        request_timeout: int = 30,  # seconds
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self.client = OpenAI(api_key=api_key or OPENAI_API_KEY)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds

    # -------- Language helpers --------
    @staticmethod
    def _normalize_lang(code: str) -> Lang:
        return "ro" if code.lower().startswith("ro") else "en"

    def detect_language(self, text: str) -> Lang:
        if _langdetect_detect:
            try:
                return self._normalize_lang(_langdetect_detect(text))
            except Exception as e:  # keep service resilient
                logger.warning("Language detection failed, falling back to EN: %s", e)
        return "en"

    # -------- Prompting --------
    def _build_messages(self, lang: Lang, context: str, query: str) -> List[dict]:
        """Builds a compact, context-aware prompt that stays helpful and concise."""
        if lang == "ro":
            system = (
                "Ești un bibliotecar asistent. Răspunzi întotdeauna în română, concis (1–3 propoziții). "
                "Folosește contextele furnizate (posibil mai multe cărți). "
                "Indică titlurile relevante când recomanzi. Dacă informația lipsește, cere o clarificare scurtă. "
                "Evită frazele sablon; sună natural și util."
            )
            user = (
                f"Context (posibil multiple fragmente 'Titlu: rezumat'):\n{context or '(fără context)'}\n\n"
                f"Întrebare utilizator: {query}\n\n"
                "Instrucțiuni: Răspunde concis. Dacă sunt mai multe potriviri, oferă 1–2 opțiuni relevante."
            )
        else:
            system = (
                "You are a librarian assistant. Always reply in English, concisely (1–3 sentences). "
                "Use the provided contexts (possibly multiple books). "
                "Mention relevant titles when recommending. If information is insufficient, ask a brief clarification. "
                "Avoid canned phrasing; sound natural and helpful."
            )
            user = (
                f"Context (possibly multiple 'Title: summary' snippets):\n{context or '(no context)'}\n\n"
                f"User question: {query}\n\n"
                "Instructions: Be concise. If several matches exist, offer 1–2 relevant options."
            )
        return [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]

    # -------- Public API --------
    def get_recommendation(self, context: str, query: str) -> str:
        """
        Generate a short, context-aware recommendation.
        Retries on transient failures and returns a safe fallback on empty content.
        """
        lang = self.detect_language(query)
        messages = self._build_messages(lang, context, query)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.request_timeout,  # SDK forwards to httpx timeout
                )
                content = (resp.choices[0].message.content or "").strip()
                if content:
                    return content

                logger.warning("Empty content from model (attempt %d/%d).", attempt, self.max_retries)
            except Exception as e:
                last_error = e
                logger.warning("Chat completion failed (attempt %d/%d): %s", attempt, self.max_retries, e)

            # backoff before next try (except after final attempt)
            if attempt < self.max_retries:
                time.sleep(self.retry_backoff_seconds * attempt)

        # Fallback safe response if all retries failed or content empty
        logger.error("Exhausted retries for chat completion. Returning fallback. Last error: %s", last_error)
        if lang == "ro":
            return "Nu am putut genera o recomandare în acest moment. Poți reformula întrebarea sau specifica un autor/gen?"
        return "I couldn’t generate a recommendation right now. Please rephrase your question or specify an author/genre."
