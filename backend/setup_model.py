import os
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

MODEL_ID = "ProtectAI/deberta-v3-base-prompt-injection-v2"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "weights")

def pull_and_export():
    print(f"[*] Starting download for: {MODEL_ID}")
    
    # 1. Download tokenizer
    print("[*] Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("[+] Tokenizer saved successfully.")

    # 2. Download and export ONNX model
    print("[*] Exporting model to ONNX format. This takes 1-2 minutes...")
    model = ORTModelForSequenceClassification.from_pretrained(
        MODEL_ID,
        export=True
    )
    model.save_pretrained(OUTPUT_DIR)
    print(f"[+] Complete. Weights saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    pull_and_export()