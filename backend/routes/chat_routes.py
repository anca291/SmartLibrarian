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
    print(f"[BACKEND] Primit query de la frontend: {query}")

    results = embeddings_service.search_books(query)
    print(f"[BACKEND] Rezultate embeddings: {results}")

    if not results["ids"]:
        print("[BACKEND] Nu am găsit cărți potrivite.")
        return {"recommendation": "Nu am găsit nicio carte potrivită.", "full_summary": ""}

    title = results["ids"][0]
    context = results["documents"][0]
    print(f"[BACKEND] Titlu selectat: {title}")
    print(f"[BACKEND] Context pentru GPT: {context[:100]}...")

    recommendation = gpt_service.get_recommendation(context, query)
    print(f"[BACKEND] Recomandare GPT: {recommendation[:100]}...")

    full_summary = tools_service.get_summary_by_title(title)
    print(f"[BACKEND] Rezumat complet găsit: {full_summary[:100]}...")

    return {
        "recommendation": recommendation,
        "full_summary": full_summary
    }
