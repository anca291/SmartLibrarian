import json
from config import BOOKS_FILE_JSON

class ToolsService:
    def __init__(self):
        with open(BOOKS_FILE_JSON, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def get_summary_by_title(self, title: str) -> str:
        return self.data.get(title, "Nu am găsit un rezumat complet pentru această carte.")
