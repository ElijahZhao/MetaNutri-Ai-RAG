"""Central configuration for Nutri-RAG pipeline.

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

# OpenAI-compatible provider profiles (keys read from .env, never committed)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "qwen")
LLM_PROFILES = {
    "qwen": {
        "base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "key_env": "DASHSCOPE_API_KEY",
        "model": "qwen-plus",
    },
    "deepseek": {
        "base": "https://api.deepseek.com",
        "key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
    },
    "glm": {
        "base": "https://ark.cn-beijing.volces.com/api/v3",
        "key_env": "ARK_API_KEY",
        "model": "glm-5-3-flash-260828",
    },
}

# Retrieval
COLLECTION = "nutri_kb"
# top_k=8 matches the NutriQA paper evaluation config (HybridRetriever, candidate pool max(k*4,20))
TOP_K = int(os.environ.get("TOP_K", "8"))
# keep a small margin so the prompt does not overflow
MAX_CONTEXT_CHARS = 4000

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
