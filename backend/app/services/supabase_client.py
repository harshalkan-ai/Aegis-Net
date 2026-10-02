"""
AEGIS-NET Supabase Service Client.
Provides a managed client singleton and connection health checks.
"""

import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or initialize the singleton Supabase service-role client.
    """
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.error("Supabase URL or Service Role Key not configured.")
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured in settings.")
        
        try:
            _supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            )
            logger.info("Supabase client successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
            
    return _supabase_client


def check_supabase_health() -> Dict[str, Any]:
    """
    Validates active connection to the Supabase instance.
    Returns status dictionary with connection details, schema state, and latency.
    """
    import time
    start_time = time.perf_counter()
    
    try:
        client = get_supabase_client()
        # Probe query on agents table
        response = client.table("agents").select("id").limit(1).execute()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        return {
            "status": "connected",
            "schema_initialized": True,
            "latency_ms": latency_ms,
            "url": settings.SUPABASE_URL,
            "error": None,
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        error_str = str(e)
        
        # If Supabase replied with PostgREST schema cache error (table missing), connection is active
        if "PGRST205" in error_str or "Could not find the table" in error_str:
            return {
                "status": "connected",
                "schema_initialized": False,
                "latency_ms": latency_ms,
                "url": settings.SUPABASE_URL,
                "message": "Supabase connection active. Run 001_initial_schema.sql in Supabase SQL editor to initialize tables.",
                "error": None,
            }
            
        logger.warning(f"Supabase health check failed: {error_str}")
        return {
            "status": "unhealthy",
            "schema_initialized": False,
            "latency_ms": latency_ms,
            "url": settings.SUPABASE_URL,
            "error": error_str,
        }
