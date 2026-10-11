import re
import unicodedata

class KeywordGuard:
    def __init__(self, banned_keywords: list[str]):
        self.banned_keywords = [w.lower().strip() for w in banned_keywords]
    
    def _normalize_text(self, text: str) -> str:
        """Standardizes input to catch basic spacing and character bypasses."""
        
        #Convert Unicode to closest ASCII equivalent (e.g., accented characters) Ex: Hàck
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
 
        text = text.lower()

        #Remove common obfuscation characters (dots, dashes, spaces inside words) Ex: h.a.c.k
        #Note: Keeps single spaces between actual words
        cleaned_text = re.sub(r'[^a-z0-9\s]', '', text)
        return cleaned_text

    def check_query(self, user_query: str) -> dict:
        normalized_query = self._normalize_text(user_query)
        
        for word in self.banned_keywords:
            # \b ensures we match complete words, not substrings
            pattern = rf"\b{re.escape(word)}\b"
            if re.search(pattern, normalized_query):
                return {
                    "decision": "BLOCK",
                    "failed_rule": "Deterministic-Keyword",
                    "user_friendly_reason": "I cannot process this request due to system security policies. Please rephrase your question."
                }
                
        return {"decision": "ALLOW"}


banned_list = ["hack", "jailbreak", "bypass", "exploit"]
keyword_guard = KeywordGuard(banned_list)
