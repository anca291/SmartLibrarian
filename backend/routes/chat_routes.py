from __future__ import annotations

import logging
import re
from typing import Literal, Tuple

from fastapi import APIRouter, HTTPException
from langdetect import detect, LangDetectException
from openai import OpenAI

from services.embeddings_service import EmbeddingsService
from services.gpt_service import GPTService
from services.tools_service import ToolsService


# ===== logging =====
logger = logging.getLogger("smart_librarian.chat")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

# ===== OpenAI client & modele =====
client = OpenAI()
CHAT_MODEL = "gpt-4o-mini"
MODERATION_MODEL = "omni-moderation-latest"

# ====================Router & Services====================
router = APIRouter()
embeddings_service = EmbeddingsService()
gpt_service = GPTService()
tools_service = ToolsService()


# ===== Language =====
def detect_language(text: str) -> Literal["ro", "en"]:
    try:
        lang = detect(text)
        return "ro" if lang == "ro" else "en"
    except LangDetectException:
        return "en"


BAD_WORDS_RO = [
    r"\b(doamne[-\s]?iart[ăa]-m[ăa])\b",
    r"\b(d[aă]r[aă]c|naib[ăa])\b",
    r"\b(p[\*\W_]*l[ăa])\b",
    r"\b(fut[\w\*\-]*)\b",
    r"\bm[ăa]t[\w\*\-]*\b",
]
BAD_WORDS_EN = [
    r"\b(fuck[\w\-\*]*)\b",
    r"\b(shit[\w\-\*]*)\b",
    r"\b(bitch[\w\-\*]*)\b",
    r"\b(asshole|dick|bastard)\b",
]

RE_BAD_RO = re.compile("|".join(BAD_WORDS_RO), flags=re.IGNORECASE | re.UNICODE)
RE_BAD_EN = re.compile("|".join(BAD_WORDS_EN), flags=re.IGNORECASE | re.UNICODE)


def contains_inappropriate(text: str, lang: Literal["ro", "en"]) -> bool:
    if lang == "ro":
        return bool(RE_BAD_RO.search(text))
    return bool(RE_BAD_EN.search(text))


# ===== Moderare + cenzurare ușoară RO =====
_RO_PROFANITY = [
    # listă concisă; se poate extinde la nevoie
    r"\b(dracu|naiba|p\*?la|futu|bafta-naibii|m\*?sa)\b",
]
_RO_PROFANITY_RE = re.compile("|".join(_RO_PROFANITY), flags=re.IGNORECASE)


def moderate_and_sanitize(query: str) -> Tuple[bool, str]:
    """
    Returnează (is_flagged, sanitized_query).
    Folosește întâi modelul de moderare; apoi o cenzură ușoară pentru termeni RO.
    """
    try:
        mod = client.moderations.create(model=MODERATION_MODEL, input=query)
        is_flagged = bool(mod.results[0].flagged)
    except Exception as e:
        logger.warning("Moderation API failed: %s", e)
        is_flagged = False  # fail-open ca să nu blocăm utilizatorul

    # cenzură ușoară; nu eliminăm mesajul, doar mascăm
    sanitized = _RO_PROFANITY_RE.sub(lambda m: m.group(0)[0] + "…", query)
    return is_flagged, sanitized


# ===== Clasificare intenție (fără reguli hardcodate) =====
def classify_intent(query: str, lang: Literal["ro", "en"]) -> Literal["small_talk", "book_request", "other"]:
    system = (
        "You label user intent as JSON with a single key 'intent' in {'small_talk','book_request','other'}.\n"
        "Consider 'small_talk' for greetings, chitchat (e.g., 'buna', 'ce faci', 'hello', 'how are you').\n"
        "Consider 'book_request' for queries asking for book ideas, summaries, genres, authors, themes, etc."
    )
    user = f"Language={lang}. Query={query}"
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.0,
            max_tokens=20,
            response_format={"type": "json_object"},
        )
        intent = resp.choices[0].message.parsed.get("intent")  # .parsed este populat când response_format e json_object
        if intent in {"small_talk", "book_request", "other"}:
            return intent  # type: ignore
    except Exception as e:
        logger.warning("Intent classify failed: %s", e)
    return "other"


# ===== Răspuns prietenos generat (fără texte predefinite) =====
def friendly_reply(query: str, lang: Literal["ro", "en"]) -> str:
    system_ro = (
        "Ești un bibliotecar prietenos. Răspunde foarte scurt (max 1-2 propoziții), cald, natural și adresativ. "
        "Încheie cu o întrebare utilă legată de lectură (ex: ce gen cauți azi?). Nu folosi texte prestabilite."
    )
    system_en = (
        "You are a friendly librarian. Reply very briefly (max 1-2 sentences), warm, natural, and engaging. "
        "End with a helpful reading-related question (e.g., what genre today?). Do not use canned phrases."
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
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Small-talk generation failed: %s", e)
        # fallback minimal, dar încă fără template fix
        return "Salut! Ce ți-ar plăcea să citești astăzi?" if lang == "ro" \
            else "Hi! What would you like to read today?"


@router.post("/chat")
def chat(query: str):
    lang = detect_language(query)
    logger.info("[BACKEND] Received query (%s): %s", lang, query)
    if contains_inappropriate(query, lang):
        if lang == "ro":
            return {
                "recommendation": "Mesajul conține termeni nepotriviți. Îl poți reformula, te rog?",
                "full_summary": ""
            }
        else:
            return {
                "recommendation": "Your message includes inappropriate terms. Could you rephrase it, please?",
                "full_summary": ""
            }

    # moderare & cenzurare
    flagged, sanitized = moderate_and_sanitize(query)
    if flagged:
        # nu blocăm complet; cerem reformulare politicoasă
        if lang == "ro":
            return {"recommendation": "Mesajul tău conține termeni sensibili. Îl poți reformula, te rog?",
                    "full_summary": ""}
        return {"recommendation": "Your message includes sensitive terms. Could you rephrase it, please?",
                "full_summary": ""}

    # small talk?
    intent = classify_intent(sanitized, lang)
    if intent == "small_talk":
        return {"recommendation": friendly_reply(sanitized, lang), "full_summary": ""}

    # cerere de carte? dacă nu e clar, încercăm oricum (nu mai forțăm cuv. cheie 'carte/book')
    try:
        results = embeddings_service.search_books(sanitized)
        logger.info("[BACKEND] Embeddings results: %s", results)
    except Exception as e:
        logger.exception("Embeddings search failed")
        raise HTTPException(status_code=500, detail="A apărut o eroare la căutarea cărților.") from e

    if not results or not results.get("ids"):
        if lang == "ro":
            return {"recommendation": "Nu am găsit potriviri. Încerci cu un autor, gen sau temă?",
                    "full_summary": ""}
        return {"recommendation": "I couldn't find a match. Try with an author, genre, or theme?",
                "full_summary": ""}

    # titlu & context din vector search (IDs și documents pot fi liste de liste)
    title = results["ids"][0][0] if isinstance(results["ids"][0], list) else results["ids"][0]
    context = results["documents"][0][0] if isinstance(results["documents"][0], list) else results["documents"][0]
    logger.info("[BACKEND] Selected title: %s", title)

    # recomandare cu modelul tău gpt_service (presupunând că folosește SDK nou)
    try:
        recommendation = gpt_service.get_recommendation(context, sanitized)
    except Exception as e:
        logger.exception("LLM recommendation failed")
        raise HTTPException(status_code=500, detail="A apărut o eroare la generarea răspunsului.") from e

    # dacă utilizatorul cere rezumat complet, extragem din ToolsService
    qlow = sanitized.lower()
    wants_full = any(k in qlow for k in ["rezumat complet", "rezumatul complet", "full summary", "complete summary"])
    full_summary = ""
    if wants_full:
        try:
            full_summary = tools_service.get_summary_by_title(title)
        except Exception as e:
            logger.warning("Full summary not available: %s", e)
            full_summary = ""

    return {"recommendation": recommendation, "full_summary": full_summary}
