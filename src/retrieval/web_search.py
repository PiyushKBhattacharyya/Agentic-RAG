from __future__ import annotations
from typing import List, Dict
from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 3) -> List[Dict]:
    results: List[Dict] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "href": r.get("href"),
                    "snippet": r.get("body"),
                })
    except Exception as e:
        # Fail silently for demo stability; return empty results
        results.append({"title": "search_error", "href": "", "snippet": str(e)})
    return results