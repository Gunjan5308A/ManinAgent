import re
import os
from src.provider import create_llm_from_env, ask_with_provider, ProviderConfig, get_provider
from src.config import (
    PROVIDER, MODEL, BASE_URL, MAX_RETRIES,
    LLM_TEMPERATURE,
    OLLAMA_MODEL, OPENAI_MODEL, GOOGLE_MODEL, ANTHROPIC_MODEL, GROQ_MODEL, TOGETHER_MODEL,
    OLLAMA_BASE_URL, OPENAI_BASE_URL, ANTHROPIC_BASE_URL, TOGETHER_BASE_URL,
    OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY
)


def _get_model_for_provider(provider: str) -> str:
    models = {
        "ollama": OLLAMA_MODEL,
        "openai": OPENAI_MODEL,
        "google": GOOGLE_MODEL,
        "anthropic": ANTHROPIC_MODEL,
        "groq": GROQ_MODEL,
        "together": TOGETHER_MODEL,
    }
    return models.get(provider.lower(), MODEL)


def _get_base_url_for_provider(provider: str) -> str | None:
    urls = {
        "ollama": OLLAMA_BASE_URL,
        "openai": OPENAI_BASE_URL,
        "anthropic": ANTHROPIC_BASE_URL,
        "together": TOGETHER_BASE_URL,
    }
    return urls.get(provider.lower())


def _get_api_key_for_provider(provider: str) -> str | None:
    keys = {
        "openai": OPENAI_API_KEY,
        "google": GOOGLE_API_KEY,
        "anthropic": ANTHROPIC_API_KEY,
        "groq": GROQ_API_KEY,
        "together": TOGETHER_API_KEY,
    }
    return keys.get(provider.lower())


def _build_config(provider: str = None, model: str = None, base_url: str = None, api_key: str = None) -> ProviderConfig:
    provider = provider or PROVIDER
    return ProviderConfig(
        name=provider,
        model=model or _get_model_for_provider(provider),
        base_url=base_url or _get_base_url_for_provider(provider),
        api_key=api_key or _get_api_key_for_provider(provider),
        temperature=LLM_TEMPERATURE,
    )


def ask(prompt: str, system: str, model: str = None, base_url: str = None) -> str:
    """Legacy interface - uses default provider from config."""
    config = _build_config(model=model, base_url=base_url)
    return ask_with_provider(prompt, system, config)


def ask_with_config(prompt: str, system: str, config: ProviderConfig) -> str:
    """New interface - uses explicit provider config."""
    return ask_with_provider(prompt, system, config)


def extract_code(text: str) -> str:
    text = re.sub(r"xxx.*?xxx", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"```(?:python|json)?\s*(.*?)(?:```|$)", r"\1", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()