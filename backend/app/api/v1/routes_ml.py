"""
AEGIS-NET ML Threat Engine API Routes.
Exposes ONNX Runtime health status and real-time threat detection inference endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from app.models.ml_loader import ThreatDetector

router = APIRouter(prefix="/ml", tags=["ML Threat Engine"])
logger = logging.getLogger(__name__)


class PredictRequest(BaseModel):
    payload: str


@router.get(
    "/status",
    summary="Get ONNX ML Model Status & Telemetry",
    description="Returns ONNX Runtime health state, latency, prediction count, and model metadata.",
)
async def get_ml_status() -> Dict[str, Any]:
    """Retrieve ML engine health info for UI debug panel."""
    detector = ThreatDetector.get_instance()
    return detector.get_status_info()


@router.post(
    "/predict",
    summary="Execute ONNX Threat Inference",
    description="Tokenizes payload and runs ONNX inference to compute prompt injection / threat score.",
)
async def predict_threat_endpoint(req: PredictRequest) -> Dict[str, Any]:
    """Run real ONNX model inference."""
    detector = ThreatDetector.get_instance()
    res = detector.predict_threat(req.payload)
    if res.get("status") == "MODEL ERROR" and "error" in res:
        logger.error(f"[ML API] Model error: {res.get('error')}")
    return res
