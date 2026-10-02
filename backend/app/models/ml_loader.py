"""
AEGIS-NET Machine Learning Model Loader
High-performance ONNX Runtime inference engine for Prompt Injection & Threat Detection.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

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
        weights_path = Path(weights_dir) if weights_dir else get_weights_path()
        model_path = weights_path / "model.onnx"

        if not model_path.is_file():
            raise FileNotFoundError(
                f"ONNX model file not found at {model_path}. "
                f"Please verify model weights exist in 'weights/'."
            )

        # Configure ONNX Runtime Session for ultra-low latency CPU execution (<40ms)
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session_options.intra_op_num_threads = 4
        session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        # Initialize tokenizer and ONNX Runtime inference session
        self.tokenizer = AutoTokenizer.from_pretrained(str(weights_path))
        self.session = ort.InferenceSession(
            str(model_path),
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )
        
        # Cache input names for fast lookup
        self.input_names = {inp.name for inp in self.session.get_inputs()}

    @classmethod
    def get_instance(cls, weights_dir: Optional[str] = None) -> "ThreatDetector":
        if cls._instance is None:
            cls._instance = cls(weights_dir)
        return cls._instance

    def predict_threat(self, text: str) -> float:
        """
        Tokenize input text, run ONNX inference, and return threat probability.
        
        Args:
            text: Input prompt or payload to analyze.
            
        Returns:
            Threat probability as a float between 0.0 and 1.0 (1.0 = highly malicious).
        """
        if not text or not text.strip():
            return 0.0

        # Tokenize input text (max_length=512, truncation=True, padding=True, numpy tensors)
        encoded_inputs = self.tokenizer(
            text,
            max_length=512,
            truncation=True,
            padding=True,
            return_tensors="np",
        )

        # Feed expected input tensors into ONNX session
        ort_inputs = {
            k: v for k, v in encoded_inputs.items() if k in self.input_names
        }

        # Run inference
        outputs = self.session.run(None, ort_inputs)
        logits = outputs[0]  # Shape: (1, 2) [SAFE, INJECTION]

        # Apply Softmax to obtain probabilities
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        probabilities = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

        # Index 1 corresponds to INJECTION / Threat class
        threat_score = float(probabilities[0, 1])
        return max(0.0, min(1.0, threat_score))


def predict_threat(text: str) -> float:
    """
    Convenience function to predict threat score using the singleton ThreatDetector.
    
    Args:
        text: Input prompt or payload.
        
    Returns:
        Threat probability score [0.0, 1.0].
    """
    detector = ThreatDetector.get_instance()
    return detector.predict_threat(text)
