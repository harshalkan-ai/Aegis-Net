"""
AEGIS-NET Tavily Research Client.
Performs real web searches using Tavily API via backend environment key.
<<<<<<< HEAD
Never exposes API key to browser or logs.
"""
import logging
from typing import Dict, Any, List, Optional
import httpx

=======
Never exposes API key to browser.
"""
import logging
import httpx
from typing import Dict, Any, List
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
from app.core.config import settings

logger = logging.getLogger("aegis.tavily")

TAVILY_API_URL = "https://api.tavily.com/search"


<<<<<<< HEAD
def get_tavily_api_key() -> str:
    """Retrieve TAVILY_API_KEY from backend settings or environment."""
    key = settings.TAVILY_API_KEY
    if not key or not str(key).strip():
        # Secondary fallback directly to os.environ if needed
        import os
        key = os.environ.get("TAVILY_API_KEY", "")
    return str(key).strip() if key else ""


def check_tavily_key_loaded() -> bool:
    """Check if Tavily API key is loaded without revealing it."""
    key = get_tavily_api_key()
    has_key = bool(key)
    logger.info(f"Tavily API key loaded: {'YES' if has_key else 'NO'}")
    return has_key


def perform_tavily_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Perform a real web search via Tavily API using TAVILY_API_KEY from backend .env.
    Uses official TavilyClient SDK with robust error handling and safe logging.
    """
    api_key = get_tavily_api_key()

    if not api_key:
        logger.warning("Tavily API key loaded: NO")
        safe_err = "Tavily search API key is missing. Please configure TAVILY_API_KEY in backend environment (.env)."
        logger.warning(f"Tavily request failed: {safe_err}")
        return {
            "query": query,
            "summary": safe_err,
            "sources": [],
            "error": safe_err,
            "status": "NO_API_KEY",
        }

    logger.info("Tavily API key loaded: YES")
    logger.info("Tavily request started")

    clean_query = query.strip() if query else ""
    if not clean_query:
        safe_err = "Research query must not be empty."
        logger.warning(f"Tavily request failed: {safe_err}")
        return {
            "query": query,
            "summary": safe_err,
            "sources": [],
            "error": safe_err,
            "status": "FAILED",
        }

    # 1. Try official TavilyClient SDK
    try:
        from tavily import TavilyClient
        import tavily.errors as tavily_errors

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=clean_query,
            search_depth="basic",
            include_answer=True,
            max_results=max_results,
        )

        # Parse response
        if not isinstance(response, dict):
            raise ValueError("Malformed Tavily search response: expected JSON object")

        raw_results = response.get("results", [])
        if not isinstance(raw_results, list):
            raw_results = []

        sources: List[Dict[str, Any]] = []
        for item in raw_results:
            if isinstance(item, dict):
                sources.append({
                    "title": item.get("title") or "Untitled Web Source",
                    "url": item.get("url") or "",
                    "content": item.get("content") or "",
                    "score": float(item.get("score") or 0.0),
                })

        summary = response.get("answer") or (
            f"Tavily research completed. Found {len(sources)} relevant web sources for '{clean_query}'."
            if sources else f"No search results returned for query '{clean_query}'."
        )

        logger.info("Tavily request succeeded")
        return {
            "query": clean_query,
            "summary": summary,
            "sources": sources,
            "status": "COMPLETED",
        }

    except Exception as e:
        error_type = type(e).__name__

        # Map to safe human-readable error messages without leaking the key
        if "InvalidAPIKey" in error_type or "Invalid API key" in str(e):
            safe_err = "Tavily authentication failed: Invalid API key."
        elif "MissingAPIKey" in error_type:
            safe_err = "Tavily authentication failed: API key missing."
        elif "UsageLimit" in error_type or "limit exceeded" in str(e).lower() or "quota" in str(e).lower():
            safe_err = "Tavily API rate limit exceeded or credit quota exhausted."
        elif "Timeout" in error_type:
            safe_err = "Tavily search request timed out."
        elif "Forbidden" in error_type:
            safe_err = "Tavily API access forbidden for this key."
        elif "BadRequest" in error_type:
            safe_err = f"Tavily API rejected the request: {str(e)[:120]}"
        else:
            # Fallback to direct HTTP attempt if SDK failed for an unexpected library reason
            try:
                logger.info("Attempting direct HTTP fallback for Tavily search...")
                http_res = httpx.post(
                    TAVILY_API_URL,
                    json={
                        "api_key": api_key,
                        "query": clean_query,
                        "search_depth": "basic",
                        "include_answer": True,
                        "max_results": max_results,
                    },
                    timeout=15.0,
                )
                if http_res.status_code == 200:
                    data = http_res.json()
                    raw_results = data.get("results", []) if isinstance(data, dict) else []
                    sources = [
                        {
                            "title": item.get("title") or "Untitled Web Source",
                            "url": item.get("url") or "",
                            "content": item.get("content") or "",
                            "score": float(item.get("score") or 0.0),
                        }
                        for item in raw_results if isinstance(item, dict)
                    ]
                    summary = (data.get("answer") if isinstance(data, dict) else None) or (
                        f"Tavily research completed. Found {len(sources)} relevant web sources for '{clean_query}'."
                    )
                    logger.info("Tavily request succeeded")
                    return {
                        "query": clean_query,
                        "summary": summary,
                        "sources": sources,
                        "status": "COMPLETED",
                    }
                elif http_res.status_code == 401:
                    safe_err = "Tavily authentication failed: Invalid API key (HTTP 401)."
                elif http_res.status_code == 429:
                    safe_err = "Tavily API rate limit or usage quota exceeded (HTTP 429)."
                else:
                    safe_err = f"Tavily API returned HTTP status {http_res.status_code}."
            except Exception as http_ex:
                safe_err = f"Tavily network connection failure: {type(http_ex).__name__}"

        logger.error(f"Tavily request failed: {safe_err}")
        return {
            "query": clean_query,
            "summary": f"Tavily research failed: {safe_err}",
            "sources": [],
            "error": safe_err,
            "status": "FAILED",
        }


def test_tavily_connection() -> Dict[str, Any]:
    """
    Execute a minimal health-check search against Tavily to verify connectivity and API key validity.
    Returns safe status without exposing the key.
    """
    logger.info("Running Tavily health probe...")
    res = perform_tavily_search("connectivity test", max_results=1)
    if res.get("status") == "COMPLETED":
        count = len(res.get("sources", []))
        return {
            "success": True,
            "message": f"Tavily search service is healthy and operational. Verified {count} search results.",
            "result_count": count,
        }
    else:
        err = res.get("error") or res.get("summary") or "Unknown Tavily failure"
        return {
            "success": False,
            "message": f"Tavily health check failed: {err}",
            "result_count": 0,
        }
=======
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
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
