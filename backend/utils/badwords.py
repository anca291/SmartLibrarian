# backend/utils/badwords.py
import re
from typing import Dict, Optional, Literal

Lang = Literal["ro", "en"]

class BadWordsLoader:
    """
    Simple bad words loader that keeps regex patterns in memory.
    Does NOT load from files anymore.
    Supports wildcard '*' transformed into \w*.
    """

    def __init__(self):
        # --- Hardcoded bad words lists (extend as needed) ---
        bad_words_ro = [
            "dracu", "naiba", "p*la", "fut*", "m*sa", "m*ta"
        ]
        bad_words_en = [
            "fuck*", "shit*", "bitch", "asshole", "dick", "bastard"
        ]

        self._patterns: Dict[Lang, Optional[re.Pattern]] = {
            "ro": self._compile(bad_words_ro),
            "en": self._compile(bad_words_en),
        }

    @staticmethod
    def _compile(words: list[str]) -> Optional[re.Pattern]:
        cleaned = []
        for w in words:
            if not w.strip():
                continue
            # support wildcard '*'
            w = re.escape(w).replace(r"\*", r"\w*")
            cleaned.append(rf"\b{w}\b")
        if not cleaned:
            return None
        return re.compile("|".join(cleaned), flags=re.IGNORECASE | re.UNICODE)

    def contains(self, text: str, lang: Lang) -> bool:
        pat = self._patterns.get(lang)
        return bool(pat and pat.search(text))

    def mask(self, text: str, lang: Lang) -> str:
        pat = self._patterns.get(lang)
        if not pat:
            return text
        def _mask(m: re.Match) -> str:
            s = m.group(0)
            return s[0] + "…"
        return pat.sub(_mask, text)


# Global instance
badwords = BadWordsLoader()
