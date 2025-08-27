from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
import base64, io, logging, httpx

router = APIRouter()
client = OpenAI()

@router.post("/generate")
async def generate_image(prompt: str = Form(...), size: str = Form("1024x1024")):
    """
    Generează PNG dintr-un prompt text folosind gpt-image-1.
    Fără 'response_format' (serverul îl respinge); folosim b64_json implicit.
    """
    try:
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            n=1,
        )
        data = resp.data[0]

        # Varianta standard: b64_json (implicit)
        b64 = getattr(data, "b64_json", None)
        if b64:
            img_bytes = base64.b64decode(b64)
            return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")

        # Fallback (dacă API-ul ți-a returnat doar URL)
        url = getattr(data, "url", None)
        if url:
            with httpx.stream("GET", url, timeout=60.0) as r:
                r.raise_for_status()
                def gen():
                    for chunk in r.iter_bytes():
                        yield chunk
                return StreamingResponse(gen(), media_type="image/png")

        raise ValueError("No image payload (neither b64_json nor url) in response.")
    except Exception as e:
        logging.exception("Image generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")
