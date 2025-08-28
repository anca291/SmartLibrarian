from __future__ import annotations

import io
import logging
import traceback
from typing import Iterator, Any, Optional, Dict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

router = APIRouter()
client = OpenAI()


def stream_chunks(stream_ctx: Any) -> Iterator[bytes]:
    with stream_ctx as response:
        for chunk in response.iter_bytes():
            yield chunk


@router.get("/ping")
def ping():
    return {"ok": True, "scope": "audio"}


# ---------- STT (Whisper) ----------
@router.post("/stt")
async def stt(file: UploadFile = File(...),  language: Optional[str] = None) -> Dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file upload: no filename provided.")
    if file.content_type not in ["audio/webm", "audio/wav", "audio/mpeg"]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    try:
        raw: bytes = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        buf = io.BytesIO(raw)
        buf.name = file.filename or "speech.webm"

        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=buf,
            language=language
        )
        text = getattr(resp, "text", "") or (resp.get("text", "") if isinstance(resp, dict) else "")
        return {"text": text}
    except Exception as e:
        logging.error("STT failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")


# ---------- TTS (streaming) ----------
@router.post("/tts")
async def tts(text: str = Form(...), voice: str = Form("alloy"), format: str = Form("mp3")) -> StreamingResponse:

    if not text.strip():
        raise HTTPException(status_code=400, detail="Text input is required.")
    if format not in ["mp3", "wav", "ogg"]:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")

    try:
        stream_ctx = client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
            response_format=format
        )

        media = f"audio/{'mpeg' if format == 'mp3' else format}"
        return StreamingResponse(stream_chunks(stream_ctx), media_type=media)

    except Exception as e:
        logging.error("TTS failed: %s\n%s", e, traceback.format_exc())
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            logging.error("OPENAI_API_KEY invalid.")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")
