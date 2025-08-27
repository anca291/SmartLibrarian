# backend/routes/audio_routes.py
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from openai import OpenAI
import io, os, logging, traceback

router = APIRouter()
client = OpenAI()  # necesită OPENAI_API_KEY în env

@router.get("/ping")
def ping():
    return {"ok": True, "scope": "audio"}

# ---------- STT (Whisper) ----------
@router.post("/stt")
async def stt(file: UploadFile = File(...), language: str | None = None):
    try:
        raw = await file.read()
        # pregătește un file-like cu nume (SDK-ul se bazează pe extensie uneori)
        buf = io.BytesIO(raw)
        buf.name = file.filename or "speech.webm"

        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=buf,
            language=language  # "ro", "en", etc. (opțional)
        )
        text = getattr(resp, "text", "") or (resp.get("text", "") if isinstance(resp, dict) else "")
        return {"text": text}
    except Exception as e:
        logging.error("STT failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")

# ---------- TTS (streaming) ----------
@router.post("/tts")
async def tts(text: str = Form(...), voice: str = Form("alloy"), format: str = Form("mp3")):
    try:

        # OpenAI Python SDK: folosește with_streaming_response pentru fișiere mari/continue
        stream_ctx = client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",   # poți folosi și "tts-1" sau "tts-1-hd"
            voice=voice,
            input=text,
            response_format=format
        )

        def iter_chunks():
            with stream_ctx as response:
                for chunk in response.iter_bytes():
                    yield chunk

        media = f"audio/{'mpeg' if format == 'mp3' else format}"
        return StreamingResponse(iter_chunks(), media_type=media)

    except Exception as e:
        logging.error("TTS failed: %s\n%s", e, traceback.format_exc())
        # Hint util în logs dacă lipsește cheia
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            logging.error("OPENAI_API_KEY lipsește sau este invalid.")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")
