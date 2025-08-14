import openai
import chromadb
from chromadb.utils import embedding_functions
from config import OPENAI_API_KEY, CHROMA_DB_PATH, BOOKS_FILE_TXT

class EmbeddingsService:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="books",
            embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
        )

    def load_and_index_books(self):
        with open(BOOKS_FILE_TXT, "r", encoding="utf-8") as f:
            data = f.read().split("## Title:")
            docs = []
            ids = []
            for idx, block in enumerate(data):
                block = block.strip()
                if not block:
                    continue
                lines = block.split("\n", 1)
                title = lines[0].strip()
                summary = lines[1].strip() if len(lines) > 1 else ""
                docs.append(summary)
                ids.append(title)
            self.collection.add(documents=docs, ids=ids)

    def search_books(self, query: str, top_k: int = 1):
        results = self.collection.query(query_texts=[query], n_results=top_k)
        return results
