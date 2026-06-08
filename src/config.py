import os
from dotenv import load_dotenv

load_dotenv()

MODEL       = os.getenv("CODEGEN_MODEL", "gemma4:e2b")
PROVIDER    = os.getenv("LLM_PROVIDER", "ollama").lower()
BASE_URL    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
QUALITY     = os.getenv("DEFAULT_QUALITY", "l")
FPS         = int(os.getenv("DEFAULT_FPS", "15"))
