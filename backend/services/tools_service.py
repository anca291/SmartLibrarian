# backend/services/tools_service.py (sau unde ai clasa)
import json
import os
from typing import Any, Dict, List, Union
from config import BOOKS_FILE_JSON  # păstrează cum ai tu; dacă rulezi cu backend.main, folosește: from backend.config import BOOKS_FILE_JSON

TitleT = Union[str, List[str]]

class ToolsService:
    def __init__(self):
        path = BOOKS_FILE_JSON
        if not os.path.exists(path):
            raise FileNotFoundError(f"Nu găsesc fișierul JSON: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Acceptă fie dict{titlu: rezumat}, fie listă de obiecte
        if isinstance(raw, dict):
            self.data: Dict[str, str] = raw
        elif isinstance(raw, list):
            # încearcă să mapezi la {titlu: rezumat}
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

        # precompute pentru căutări insensibile la caz
        self._lower_index = {self._norm_key(k).lower(): k for k in self.data.keys()}

    @staticmethod
    def _norm_key(s: str) -> str:
        # normalizează ghilimele, spații și caz
        return (
            s.replace("’", "'")
             .replace("“", '"')
             .replace("”", '"')
             .strip()
        )

    @staticmethod
    def _to_title_str(title: TitleT) -> str:
        # Acceptă listă sau string; ia primul element dacă e listă
        if isinstance(title, list):
            title = title[0] if title else ""
        return str(title)

    def get_summary_by_title(self, title: TitleT) -> str:
        DEFAULT = "Nu am găsit un rezumat complet pentru această carte."

        t = self._to_title_str(title)
        if not t:
            return DEFAULT

        t_norm = self._norm_key(t)

        # 1) potrivire exactă (cheie așa cum e în fișier)
        if t_norm in self.data:
            return self.data[t_norm]

        # 2) potrivire case-insensitive
        lower = t_norm.lower()
        if lower in self._lower_index:
            original_key = self._lower_index[lower]
            return self.data[original_key]

        # 3) potrivire parțială (conține) insensibilă la caz
        for k in self.data.keys():
            if lower in self._norm_key(k).lower() or self._norm_key(k).lower() in lower:
                return self.data[k]

        return DEFAULT
