import json
import logging
import os

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from config import CHROMA_DB_PATH, BOOKS_FILE_TXT, BOOKS_FILE_JSON, OPENAI_API_KEY


logger = logging.getLogger("smart_librarian.embeddings")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


class EmbeddingsService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.embedding_fn = OpenAIEmbeddingFunction(
            model_name="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )
        self.collection = self.client.get_or_create_collection(
            name="books", embedding_function=self.embedding_fn
        )
        if self.collection.count() == 0:
            logger.info("No embeds loaded. Starting indexing from JSON...")
            self._index_books()
            logger.info("Embeddings generated and saved.")
        else:
            logger.info("Already existing embeddings (%s documents).", self.collection.count())

    def _index_books(self):
        if not os.path.exists(BOOKS_FILE_JSON):
            raise FileNotFoundError(f"JSON file not found: {BOOKS_FILE_JSON}")
        with open(BOOKS_FILE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        ids, docs, metadatas = [], [], []
        for idx, (title, summary) in enumerate(data.items()):
            if not summary:
                continue
            ids.append(str(idx))
            docs.append(summary)
            metadatas.append({"title": title})

        self.collection.add(documents=docs, ids=ids, metadatas=metadatas)

    def search_books(self, query: str, top_k: int = 3) -> dict:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        ids = (results.get("ids") or [[]])[0] or []
        docs = (results.get("documents") or [[]])[0] or []
        metas = (results.get("metadatas") or [[]])[0] or []
        titles = []
        context_parts = []
        for i in range(min(len(ids), len(docs))):
            meta = metas[i] if i < len(metas) else None
            title = str(meta["title"]) if isinstance(meta, dict) and meta.get("title") else str(ids[i]) or f"Result {i + 1}"
            titles.append(title)
            context_parts.append(f"{title}: {docs[i]}")
        context = "\n---\n".join(context_parts)
        return {"ids": ids, "documents": docs, "metadatas": metas, "titles": titles, "context": context}

    # Optional: load from TXT file with "Title:" and summary blocks
    def load_and_index_books(self):
        """Încarcă cărțile din book_summaries.txt și creează embeddings."""
        with open(BOOKS_FILE_TXT, "r", encoding="utf-8") as f:
            data = f.read().split("Title:")
            docs, ids = [], []
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
