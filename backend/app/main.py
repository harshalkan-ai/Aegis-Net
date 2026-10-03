"""
AEGIS-NET Backend Application Entrypoint.
Initializes FastAPI, lifespan events, CORS middleware, and system health monitoring.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from typing import Dict, Any

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.supabase_client import check_supabase_health
from app.api.v1.routes_agents import router as agents_router
from app.api.v1.routes_proxy import router as proxy_router
from app.api.v1.routes_context import router as context_router
from app.api.v1.routes_policy import router as policy_router
from app.api.v1.routes_containment import router as containment_router
from app.api.v1.routes_graph import router as graph_router
from app.api.v1.routes_incidents import router as incidents_router
from app.api.v1.routes_audit import router as audit_router
from app.api.v1.routes_forensics import router as forensics_router
from app.api.v1.routes_ml import router as ml_router
from app.api.v1.routes_research import router as research_router
from app.api.v1.routes_workspace import router as workspace_router
from app.api.v1.routes_sandbox import router as sandbox_router
from app.api.v1.routes_deployer import router as deployer_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("aegis.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management:
    Initializes models, database connections, and logs readiness.
    """
    logger.info("Initializing AEGIS-NET Security Engine...")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Version: {settings.VERSION}")
    
    # Test DB connectivity on startup without blocking boot if offline
    db_status = check_supabase_health()
    if db_status.get("status") == "connected":
        logger.info(f"Supabase connection verified (latency: {db_status.get('latency_ms')}ms)")
    else:
        logger.warning(f"Supabase connection warning on boot: {db_status.get('error')}")

    yield

    logger.info("Shutting down AEGIS-NET Security Engine...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Zero-Trust ML Security Proxy & Automated Forensics Engine for Autonomous Agents",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
app.include_router(proxy_router, prefix=settings.API_V1_PREFIX)
app.include_router(context_router, prefix=settings.API_V1_PREFIX)
app.include_router(policy_router, prefix=settings.API_V1_PREFIX)
app.include_router(containment_router, prefix=settings.API_V1_PREFIX)
app.include_router(graph_router, prefix=settings.API_V1_PREFIX)
app.include_router(incidents_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)
app.include_router(forensics_router, prefix=settings.API_V1_PREFIX)
app.include_router(ml_router, prefix=settings.API_V1_PREFIX)
app.include_router(research_router, prefix=settings.API_V1_PREFIX)
app.include_router(workspace_router, prefix=settings.API_V1_PREFIX)
app.include_router(sandbox_router, prefix=settings.API_V1_PREFIX)
app.include_router(deployer_router, prefix=settings.API_V1_PREFIX)

from app.services.tavily_client import test_tavily_connection


@app.get("/api/tavily/test", tags=["Research"], summary="Tavily Health Probe")
@app.get("/api/v1/tavily/test", tags=["Research"], summary="Tavily Health Probe (v1)")
async def test_tavily_endpoint() -> Dict[str, Any]:
    """Test Tavily API connectivity and key validity."""
    return test_tavily_connection()



@app.get(
    "/health",
    tags=["System"],
    summary="Application Health Probe",
    response_model=Dict[str, Any],
)
async def health_check():
    """Returns general application health and current UTC timestamp."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/health/db",
    tags=["System"],
    summary="Supabase Database Health Probe",
    response_model=Dict[str, Any],
)
async def health_db_check():
    """Validates active connection to Supabase instance."""
    db_health = check_supabase_health()
    status_code = (
        status.HTTP_200_OK
        if db_health.get("status") == "connected"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "status": db_health.get("status"),
            "schema_initialized": db_health.get("schema_initialized", False),
            "latency_ms": db_health.get("latency_ms"),
            "url": db_health.get("url"),
            "message": db_health.get("message"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": db_health.get("error"),
        },
    )


@app.get("/", tags=["System"])
async def root():
    """Root landing endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
    }
