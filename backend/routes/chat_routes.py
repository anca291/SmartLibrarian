# backend/routes/chat_routes.py
from __future__ import annotations

import json
import logging
from typing import Dict, List, Literal

from fastapi import APIRouter, HTTPException, Query
from openai import OpenAI

# Internal services
from services.embeddings_service import EmbeddingsService
from services.gpt_service import GPTService
from services.tools_service import ToolsService

# Local inappropriate-language filter (hardcoded lists, see backend/utils/badwords.py)
from utils.badwords import badwords

# Optional language detection
try:
    from langdetect import detect as _langdetect_detect  # type: ignore
except Exception:  # pragma: no cover
    _langdetect_detect = None  # type: ignore

# ----------------------------
# Config & infra
# ----------------------------
logger = logging.getLogger("smart_librarian.chat")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

client = OpenAI()  # reads OPENAI_API_KEY from env/.env
CHAT_MODEL = "gpt-4o-mini"

router = APIRouter()

embeddings_service = EmbeddingsService()
gpt_service = GPTService()
tools_service = ToolsService()

Lang = Literal["ro", "en"]


# ----------------------------
# Language utils
# ----------------------------
def detect_language(text: str) -> Lang:
    """Detect RO/EN; prefer langdetect, else heuristic."""
    if _langdetect_detect:
        try:
            code = _langdetect_detect(text)
            return "ro" if code == "ro" else "en"
        except Exception:
            pass
    lowered = text.lower()
    if any(tok in lowered for tok in [" ce ", " cum ", " carte", " rezumat", "autor", "buna", "salut"]):
        return "ro"
    return "en"


# ----------------------------
# Intent classification & small talk
# ----------------------------
def classify_intent(query: str, lang: Lang) -> Literal["small_talk", "book_request", "other"]:
    """Classify user intent with LLM, fallback to regex greetings."""
    system = (
        "Return ONLY a JSON object with a single key 'intent' whose value is one of: "
        "'small_talk','book_request','other'. "
        "Classify greetings/chitchat as 'small_talk' and anything about books (ideas, summaries, genres, authors, themes) as 'book_request'."
    )
    user_msg = f"Language={lang}. Query={query}"
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user_msg}],
            temperature=0.0,
            max_tokens=20,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or ""
        data = json.loads(content)
        intent = (data.get("intent") or "").strip()
        if intent in {"small_talk", "book_request", "other"}:
            return intent  # type: ignore[return-value]
    except Exception as e:
        logger.warning("Intent classification failed: %s", e)

    # fallback simple regex for greetings
    import re
    GREETING_RO = r"\b(bun[aă]|salut(are)?|hei|ceau|ce\s+faci|ce\s+mai\s+faci)\b"
    GREETING_EN = r"\b(hi|hello|hey|how\s+are\s+you|what's\s+up)\b"
    pat = re.compile(GREETING_RO if lang == "ro" else GREETING_EN, re.IGNORECASE)
    if pat.search(query.strip()):
        return "small_talk"

    return "other"


def friendly_reply(query: str, lang: Lang) -> str:
    """Short, friendly small-talk reply (no hardcoded templates)."""
    system_ro = (
        "Ești un bibliotecar prietenos. Răspunde foarte concis (max 2 propoziții), cald și natural. "
        "Încheie cu o întrebare legată de lectură (de ex.: ce gen cauți azi?)."
    )
    system_en = (
        "You are a friendly librarian. Reply briefly (max 2 sentences), warm and natural. "
        "End with a helpful reading-related question (e.g., what genre are you into today?)."
    )
    system = system_ro if lang == "ro" else system_en
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": query}],
            temperature=0.7,
            max_tokens=60,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error("Small-talk generation failed: %s", e)
        return "Salut! Ce ți-ar plăcea să citești astăzi?" if lang == "ro" \
               else "Hi! What would you like to read today?"


# ----------------------------
# Healthcheck
# ----------------------------
@router.get("/ping")
def ping() -> Dict[str, str]:
    return {"status": "ok"}


# ----------------------------
# Main endpoint
# ----------------------------
@router.post("/chat")
def chat(query: str = Query(..., min_length=1)) -> Dict[str, str]:
    lang = detect_language(query)
    logger.info("Received query (%s): %s", lang, query)

    # 1) Inappropriate language filter — STOP before embeddings/LLM
    if badwords.contains(query, "ro" if lang == "ro" else "en"):
        masked = badwords.mask(query, "ro" if lang == "ro" else "en")
        logger.warning("Blocked query due to inappropriate language: %s", masked)
        if lang == "ro":
            return {
                "recommendation": "Mesajul tău conține termeni nepotriviți. Îl poți reformula, te rog?",
                "full_summary": ""
            }
        return {
            "recommendation": "Your message contains inappropriate terms. Please rephrase politely.",
            "full_summary": ""
        }

    # 2) Small-talk
    intent = classify_intent(query, lang)
    if intent == "small_talk":
        return {"recommendation": friendly_reply(query, lang), "full_summary": ""}

    # 3) Semantic retrieval (ChromaDB)
    try:
        results = embeddings_service.search_books(query)
        logger.info("Embeddings results: %s", {k: v for k, v in results.items() if k != "documents"})
    except Exception as e:
        logger.exception("Embeddings search failed: %s", e)
        raise HTTPException(status_code=500, detail="An error occurred while searching for books.")

    if not results or not results.get("ids"):
        logger.info("No results from semantic search.")
        if lang == "ro":
            return {"recommendation": "Nu am găsit potriviri. Încearcă un autor, gen sau temă.",
                    "full_summary": ""}
        return {"recommendation": "I couldn't find a match. Try an author, genre, or theme.",
                "full_summary": ""}

    context: str = results.get("context", "") or ""
    readable_titles: list[str] = results.get("titles") or []

    logger.info("Selected titles: %s", readable_titles)

    # 4) GPT recommendation
    try:
        recommendation = gpt_service.get_recommendation(context, query)
    except Exception as e:
        logger.exception("LLM recommendation failed: %s", e)
        raise HTTPException(status_code=500, detail="An error occurred while generating the recommendation.")

    # 5) Full summary if requested
    qlow = query.lower()
    wants_full = any(k in qlow for k in ["rezumat complet", "rezumatul complet", "full summary", "complete summary"])
    full_summary = ""
    if wants_full and readable_titles:
        try:
            full_summary = tools_service.get_summary_by_title(readable_titles[0])
        except Exception as e:
            logger.warning("Full summary not available for %s: %s", readable_titles[0], e)
            full_summary = ""

    return {"recommendation": recommendation, "full_summary": full_summary}
