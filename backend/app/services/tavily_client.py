"""
AEGIS-NET Tavily Research Client.
Performs real web searches using Tavily API via backend environment key.
Never exposes API key to browser.
"""
import logging
import httpx
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger("aegis.tavily")

TAVILY_API_URL = "https://api.tavily.com/search"


def perform_tavily_search(query: str) -> Dict[str, Any]:
    """
    Perform a real web search via Tavily API using TAVILY_API_KEY from backend .env.
    """
    api_key = settings.TAVILY_API_KEY.strip() if settings.TAVILY_API_KEY else ""

    if not api_key:
        logger.warning("[TAVILY] TAVILY_API_KEY is not set in backend environment.")
        return {
            "query": query,
            "summary": "Tavily search API key is missing in backend environment (.env).",
            "sources": [],
            "error": "TAVILY_API_KEY missing",
            "status": "NO_API_KEY",
        }

    logger.info(f"[TAVILY] Initiating search for query: {query[:80]!r}")

    try:
        response = httpx.post(
            TAVILY_API_URL,
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": 5,
            },
            timeout=15.0,
        )

        if response.status_code == 200:
            data = response.json()
            raw_results = data.get("results", [])
            sources: List[Dict[str, Any]] = []

            for item in raw_results:
                sources.append({
                    "title": item.get("title", "Untitled Web Source"),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0),
                })

            summary = data.get(
                "answer",
                f"Tavily research completed. Found {len(sources)} relevant web sources for '{query}'."
            )

            logger.info(f"[TAVILY] Search successful. Retrieved {len(sources)} sources.")
            return {
                "query": query,
                "summary": summary,
                "sources": sources,
                "status": "COMPLETED",
            }
        else:
            err_text = f"Tavily API returned HTTP {response.status_code}: {response.text}"
            logger.error(f"[TAVILY] {err_text}")
            return {
                "query": query,
                "summary": f"Tavily API search error (HTTP {response.status_code}).",
                "sources": [],
                "error": err_text,
                "status": "FAILED",
            }

    except Exception as ex:
        logger.error(f"[TAVILY] Search exception: {ex}")
        return {
            "query": query,
            "summary": f"Tavily search execution failed: {str(ex)}",
            "sources": [],
            "error": str(ex),
            "status": "FAILED",
        }
