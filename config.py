import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

# Agent
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 3))
TOP_K = int(os.getenv("TOP_K", 5))

# FAISS paths
INDEX_FILE = os.getenv("INDEX_FILE", "faiss.index")
META_FILE = os.getenv("META_FILE", "metadata.json")
