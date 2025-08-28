from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Literal

from fastapi import APIRouter, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from services.embeddings_service import EmbeddingsService
from services.gpt_service import GPTService
from services.tools_service import ToolsService
from utils.badwords import badwords

try:
    from langdetect import detect as _langdetect_detect  # type: ignore
    from langdetect.lang_detect_exception import LangDetectException  # type: ignore
except ImportError:  # pragma: no cover
    _langdetect_detect = None  # type: ignore
    LangDetectException = Exception

logger = logging.getLogger("smart_librarian.chat")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

client = OpenAI()
CHAT_MODEL = "gpt-4o-mini"
router = APIRouter()

embeddings_service = EmbeddingsService()
gpt_service = GPTService()
tools_service = ToolsService()

Lang = Literal["ro", "en"]


def detect_language(text: str) -> Lang:
    if _langdetect_detect:
        try:
            code = _langdetect_detect(text)
            return "ro" if code == "ro" else "en"
        except LangDetectException as e:
            logger.error("Language detection error: %s", e)
    lowered = text.lower()
    if any(tok in lowered for tok in [" ce ", " cum ", " carte", " rezumat", "autor", "buna", "salut"]):
        return "ro"
    return "en"


def classify_intent(query: str, lang: Lang) -> Literal["small_talk", "book_request", "other"]:
    system = (
        "Return ONLY a JSON object with a single key `intent` whose value is one of: "
        "`small_talk`,`book_request`,`other`. "
        "Classify greetings/chitchat as `small_talk` and anything about books as `book_request`."
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
    except OpenAIError as e:
        logger.warning("Intent classification error: %s", e)

    greeting_regex = r"\b(bun[aă]|salut(are)?|hei|ceau|ce\s+faci|ce\s+mai\s+faci)\b" if lang == "ro" \
        else r"\b(hi|hello|hey|how\s+are\s+you|what's\s+up)\b"
    if re.search(greeting_regex, query.strip(), re.IGNORECASE):
        return "small_talk"
    return "other"


def get_friendly_reply(query: str, lang: Lang) -> str:
    system_prompt = (
        "Ești un bibliotecar prietenos. Răspunde foarte concis (max 2 propoziții), cald și natural. "
        "Încheie cu o întrebare legată de lectură (de ex.: ce gen cauți azi?)."
        if lang == "ro" else
        "You are a friendly librarian. Reply briefly (max 2 sentences), warm and natural. "
        "End with a helpful reading-related question (e.g., what genre are you into today?)."
    )
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": query}],
            temperature=0.7,
            max_tokens=60,
        )
        return (resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        logger.error("Small-talk generation failed: %s", e)
        return "Salut! Ce ți-ar plăcea să citești astăzi?" if lang == "ro" else "Hi! What would you like to read today?"


def get_semantic_results(query: str) -> Dict[str, any]:
    try:
        results = embeddings_service.search_books(query)
        logger.info("Embeddings results: %s", {k: v for k, v in results.items() if k != "documents"})
        return results
    except Exception as e:
        logger.exception("Embeddings search failed: %s", e)
        raise HTTPException(status_code=500, detail="Error searching for books.")


def get_gpt_recommendation(context: str, query: str) -> str:
    try:
        return gpt_service.get_recommendation(context, query)
    except OpenAIError as e:
        logger.exception("LLM recommendation failed: %s", e)
        raise HTTPException(status_code=500, detail="Error generating recommendation.")


def get_full_summary(query: str, titles: List[str], lang: Lang) -> str:
    qlow = query.lower()
    wants_full = any(k in qlow for k in ["rezumat complet", "rezumatul complet", "full summary", "complete summary"])
    full_summary = ""
    if wants_full and titles:
        try:
            full_summary = tools_service.get_summary_by_title(titles[0])
        except Exception as e:
            logger.warning("Full summary not available for %s: %s", titles[0], e)
    return full_summary


# -------- API routes --------
@router.get("/ping")
def ping() -> Dict[str, str]:
    return {"status": "ok"}


class ChatRequest(BaseModel):
    query: str


@router.post("/chat")
def chat(request: ChatRequest) -> Dict[str, str]:
    query = request.query
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    lang = detect_language(query)
    logger.info("Received query (%s): %s", lang, query)

    if badwords.contains(query, "ro" if lang == "ro" else "en"):
        masked = badwords.mask(query, "ro" if lang == "ro" else "en")
        logger.warning("Blocked query due to inappropriate language: %s", masked)
        recommendation = (
            "Mesajul tău conține termeni nepotriviți. Îl poți reformula, te rog?" if lang == "ro" else
            "Your message contains inappropriate terms. Please rephrase politely."
        )
        return {"recommendation": recommendation, "full_summary": ""}
    logger.info("Query passed inappropriate language filter.")

    intent = classify_intent(query, lang)
    if intent == "small_talk":
        return {"recommendation": get_friendly_reply(query, lang), "full_summary": ""}

    results = get_semantic_results(query)
    if not results or not results.get("ids"):
        logger.info("No results from semantic search.")
        recommendation = (
            "Nu am găsit potriviri. Încearcă un autor, gen sau temă." if lang == "ro"
            else "I couldn't find a match. Try an author, genre, or theme."
        )
        return {"recommendation": recommendation, "full_summary": ""}

    context: str = results.get("context", "") or ""
    readable_titles: List[str] = results.get("titles") or []
    logger.info("Selected titles: %s", readable_titles)

    recommendation = get_gpt_recommendation(context, query)

    full_summary = get_full_summary(query, readable_titles, lang)

    return {"recommendation": recommendation, "full_summary": full_summary}
