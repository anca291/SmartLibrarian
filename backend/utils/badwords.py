# backend/utils/badwords.py
from __future__ import annotations
import time
import re
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Literal
from config import BADWORDS_DIR

Lang = Literal["ro", "en"]

class BadWordsLoader:
    """
    Încarcă listele din fișiere text și face hot-reload:
    - verifică mtimes periodic (refresh_seconds)
    - suportă wildcard-ul '*' în fișiere (transformat în \w*)
    """
    def __init__(self, base_dir: str, refresh_seconds: float = 2.0):
        self.dir = Path(base_dir)
        self.refresh_seconds = refresh_seconds
        self._last_check = 0.0
        self._mtimes: Dict[str, float] = {}
        self._patterns: Dict[Lang, Optional[re.Pattern]] = {"ro": None, "en": None}
        self._lock = Lock()
        self.ensure_loaded(force=True)

    def _file_for(self, lang: Lang) -> Path:
        return self.dir / f"bad_words_{lang}.txt"

    @staticmethod
    def _compile(words: List[str]) -> Optional[re.Pattern]:
        cleaned: List[str] = []
        for w in words:
            w = w.strip()
            if not w or w.startswith("#"):
                continue
            # transformă wildcard-ul simplu '*' în \w*
            w = re.escape(w).replace(r"\*", r"\w*")
            cleaned.append(rf"\b{w}\b")
        if not cleaned:
            return None
        pattern = "|".join(cleaned)
        return re.compile(pattern, flags=re.IGNORECASE | re.UNICODE)

    def _load_file(self, lang: Lang) -> Optional[re.Pattern]:
        p = self._file_for(lang)
        if not p.exists():
            return None
        content = p.read_text(encoding="utf-8").splitlines()
        return self._compile(content)

    def _needs_reload(self) -> bool:
        now = time.time()
        if (now - self._last_check) < self.refresh_seconds:
            return False
        # dacă orice mtime s-a schimbat, reîncărcăm
        for lang in ("ro", "en"):
            p = self._file_for(lang)  # type: ignore[arg-type]
            m = p.stat().st_mtime if p.exists() else 0.0
            if self._mtimes.get(lang) != m:
                return True
        return False

    def ensure_loaded(self, force: bool = False) -> None:
        with self._lock:
            if not force and not self._needs_reload():
                return
            for lang in ("ro", "en"):
                pat = self._load_file(lang)  # type: ignore[arg-type]
                self._patterns[lang] = pat  # type: ignore[index]
                p = self._file_for(lang)    # type: ignore[arg-type]
                self._mtimes[lang] = p.stat().st_mtime if p.exists() else 0.0
            self._last_check = time.time()

    def contains(self, text: str, lang: Lang) -> bool:
        self.ensure_loaded()
        pat = self._patterns[lang]
        return bool(pat and pat.search(text))

    def mask(self, text: str, lang: Lang) -> str:
        self.ensure_loaded()
        pat = self._patterns[lang]
        if not pat:
            return text
        def _mask(m: re.Match) -> str:
            s = m.group(0)
            return s[0] + "…"
        return pat.sub(_mask, text)


# instanță globală
badwords = BadWordsLoader(BADWORDS_DIR)
