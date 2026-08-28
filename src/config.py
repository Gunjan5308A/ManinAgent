import os
from dotenv import load_dotenv

load_dotenv()

# Legacy config (backward compatibility)
MODEL       = os.getenv("CODEGEN_MODEL", "gemma4:e2b")
PROVIDER    = os.getenv("LLM_PROVIDER", "ollama").lower()
BASE_URL    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
QUALITY     = os.getenv("DEFAULT_QUALITY", "l")
FPS         = int(os.getenv("DEFAULT_FPS", "15"))

# New multi-provider config
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# Provider-specific model defaults
OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
OPENAI_MODEL      = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_MODEL      = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
ANTHROPIC_MODEL   = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
GROQ_MODEL        = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TOGETHER_MODEL    = os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo")

# Provider-specific base URLs
OLLAMA_BASE_URL    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENAI_BASE_URL    = os.getenv("OPENAI_BASE_URL")  # Optional, for Azure/OpenAI-compatible
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")  # Optional
TOGETHER_BASE_URL  = os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1")

# Provider-specific API keys (from env)
OLLAMA_API_KEY     = os.getenv("OLLAMA_API_KEY")  # Not typically used
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY     = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
TOGETHER_API_KEY   = os.getenv("TOGETHER_API_KEY")

# Skill system config
USE_SKILLS = os.getenv("USE_SKILLS", "true").lower() == "true"
EXECUTOR_TYPE = os.getenv("EXECUTOR_TYPE", "thread")  # "thread" or "process"
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "3"))