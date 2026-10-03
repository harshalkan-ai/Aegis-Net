"""
AEGIS-NET Machine Learning Model Loader
High-performance ONNX Runtime inference engine for Prompt Injection & Threat Detection.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

logger = logging.getLogger("aegis.ml_loader")

# Resolve base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_WEIGHTS_DIR = BACKEND_DIR / "weights"


def get_weights_path() -> Path:
    """Locate the weights directory containing model.onnx and tokenizer files."""
    candidate_paths = [
        Path("weights"),
        DEFAULT_WEIGHTS_DIR,
        Path.cwd() / "weights",
        Path.cwd() / "backend" / "weights",
    ]
    for candidate in candidate_paths:
        model_file = candidate / "model.onnx"
        if model_file.is_file():
            return candidate.resolve()
    
    # Fallback to default directory
    return DEFAULT_WEIGHTS_DIR


class ThreatDetector:
    """Singleton Inference Engine for Threat & Prompt Injection Detection."""
    _instance: Optional["ThreatDetector"] = None

    def __new__(cls, weights_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(ThreatDetector, cls).__new__(cls)
            cls._instance._initialize(weights_dir)
        return cls._instance

    def _initialize(self, weights_dir: Optional[str] = None):
        self.weights_path = Path(weights_dir) if weights_dir else get_weights_path()
        self.model_path = self.weights_path / "model.onnx"
        self.status = "INITIALIZING"
        self.model_name = "DeBERTa-v3 Prompt Injection (ProtectAI)"
        self.runtime = "ONNX Runtime"
        self.last_latency_ms: Optional[float] = None
        self.last_prediction: Optional[float] = None
        self.total_predictions: int = 0
        self.errors: int = 0
        self.last_error: Optional[str] = None
        self.tokenizer = None
        self.session = None

        try:
            if not self.model_path.is_file():
                err = f"ONNX model file not found at {self.model_path}. Please verify weights exist."
                logger.error(err)
                self.status = "MODEL ERROR"
                self.last_error = err
                return

            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.intra_op_num_threads = 4
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

            self.tokenizer = AutoTokenizer.from_pretrained(str(self.weights_path))
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=session_options,
                providers=["CPUExecutionProvider"],
            )
            
            self.input_names = {inp.name for inp in self.session.get_inputs()}
            self.status = "MODEL ACTIVE"
            logger.info(f"ONNX Model successfully loaded from {self.model_path}")
        except Exception as e:
            self.status = "MODEL ERROR"
            self.last_error = str(e)
            self.errors += 1
            logger.error(f"Failed to initialize ONNX model: {e}")

    @classmethod
    def get_instance(cls, weights_dir: Optional[str] = None) -> "ThreatDetector":
        if cls._instance is None:
            cls._instance = cls(weights_dir)
        elif cls._instance.status == "MODEL ERROR":
            # Retry initialization if previously in error state
            cls._instance._initialize(weights_dir)
        return cls._instance

    def predict_threat(self, text: str) -> Dict[str, Any]:
        """
        Tokenize input text, run ONNX inference, and return threat probability and metadata.
        """
        start_time = time.perf_counter()
        
        if self.status != "MODEL ACTIVE" or self.session is None or self.tokenizer is None:
            self._initialize()
            if self.status != "MODEL ACTIVE":
                self.errors += 1
                return {
                    "threat_score": 0.0,
                    "status": "MODEL ERROR",
                    "error": self.last_error or "Model session not active",
                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                    "model_name": self.model_name,
                }

        if not text or not text.strip():
            return {
                "threat_score": 0.0,
                "status": "MODEL ACTIVE",
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "model_name": self.model_name,
            }

        try:
            encoded_inputs = self.tokenizer(
                text,
                max_length=512,
                truncation=True,
                padding=True,
                return_tensors="np",
            )

            ort_inputs = {
                k: v for k, v in encoded_inputs.items() if k in self.input_names
            }

            outputs = self.session.run(None, ort_inputs)
            logits = outputs[0]  # Shape: (1, 2) [SAFE, INJECTION]

            exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
            probabilities = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

            threat_score = float(probabilities[0, 1])
            threat_score = max(0.0, min(1.0, threat_score))

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            self.last_latency_ms = latency_ms
            self.last_prediction = threat_score
            self.total_predictions += 1

            return {
                "threat_score": threat_score,
                "status": "MODEL ACTIVE",
                "latency_ms": latency_ms,
                "model_name": self.model_name,
            }
        except Exception as e:
            self.status = "MODEL ERROR"
            self.last_error = str(e)
            self.errors += 1
            logger.error(f"ONNX Inference Error: {e}")
            return {
                "threat_score": 0.0,
                "status": "MODEL ERROR",
                "error": str(e),
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "model_name": self.model_name,
            }

    def get_status_info(self) -> Dict[str, Any]:
        """Returns health telemetry for the ML debug panel."""
        return {
            "model_name": self.model_name,
            "runtime": self.runtime,
            "status": self.status,
            "model_path": str(self.model_path),
            "last_latency_ms": self.last_latency_ms,
            "last_prediction": self.last_prediction,
            "total_predictions": self.total_predictions,
            "errors": self.errors,
            "last_error": self.last_error,
        }


def predict_threat(text: str) -> float:
    """Convenience function returning raw threat score float for risk engine."""
    detector = ThreatDetector.get_instance()
    res = detector.predict_threat(text)
    return res.get("threat_score", 0.0)
