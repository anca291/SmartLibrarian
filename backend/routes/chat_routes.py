
from fastapi import APIRouter
from services.embeddings_service import EmbeddingsService
from services.gpt_service import GPTService
from services.tools_service import ToolsService

router = APIRouter()
embeddings_service = EmbeddingsService()
gpt_service = GPTService()
tools_service = ToolsService()

@router.post("/chat")
def chat(query: str):
    results = embeddings_service.search_books(query)
    if not results["ids"]:
        return {"response": "Nu am găsit nicio carte potrivită."}

    title = results["ids"][0]
    context = results["documents"][0]

    recommendation = gpt_service.get_recommendation(context, query)
    full_summary = tools_service.get_summary_by_title(title)

    return {
        "recommendation": recommendation,
        "full_summary": full_summary
    }
