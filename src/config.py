"""Central configuration for nutri-rag pipeline.

All tunable knobs live here. Values are read from environment where sensible.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
ENV_FILE = ROOT / ".env"

# Embedding (Alibaba Bailian, OpenAI-compatible endpoint)
EMB_MODEL = os.environ.get("EMB_MODEL", "text-embedding-v3")
EMB_DIM = 1024

# Generation LLM (Bailian qwen series)
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 512

# Retrieval
COLLECTION = "nutri_kb"
TOP_K = int(os.environ.get("TOP_K", "6"))
# keep a small margin so the prompt does not overflow
MAX_CONTEXT_CHARS = 4000

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
