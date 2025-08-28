# backend/services/tools_service.py (sau unde ai clasa)
import json
import os
from typing import Dict, List, Union
from config import BOOKS_FILE_JSON

TitleT = Union[str, List[str]]

class ToolsService:
    def __init__(self):
        if not os.path.exists(BOOKS_FILE_JSON):
            raise FileNotFoundError(f"JSON file not found: {BOOKS_FILE_JSON}")
        with open(BOOKS_FILE_JSON, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            self.data: Dict[str, str] = raw
        elif isinstance(raw, list):
            mapped: Dict[str, str] = {}
            for item in raw:
                if isinstance(item, dict):
                    t = item.get("title") or item.get("name") or item.get("book") or ""
                    s = item.get("summary") or item.get("synopsis") or item.get("desc") or ""
                    if t and s:
                        mapped[str(t)] = str(s)
            self.data = mapped
        else:
            self.data = {}
        self._lower_index = {self._norm_key(k).lower(): k for k in self.data.keys()}

    @staticmethod
    def _norm_key(s: str) -> str:
        return s.replace("’", "\'").replace("“", "\"").replace("”", "\"").strip()

    @staticmethod
    def _to_title_str(title: TitleT) -> str:
        if isinstance(title, list):
            title = title[0] if title else ""
        return str(title)

    def get_summary_by_title(self, title: TitleT) -> str:
        DEFAULT = "No full summary available for this book."
        t = self._to_title_str(title)
        if not t:
            return DEFAULT
        t_norm = self._norm_key(t)
        if t_norm in self.data:
            return self.data[t_norm]
        lower = t_norm.lower()
        if lower in self._lower_index:
            original_key = self._lower_index[lower]
            return self.data[original_key]
        for k in self.data.keys():
            if lower in self._norm_key(k).lower() or self._norm_key(k).lower() in lower:
                return self.data[k]
        return DEFAULT
