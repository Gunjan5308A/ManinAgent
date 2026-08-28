from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
import os


@dataclass
class ProviderConfig:
    name: str
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.0
    extra_params: dict = field(default_factory=dict)

    def get_base_url(self) -> Optional[str]:
        return self.base_url or os.getenv(f"{self.name.upper()}_BASE_URL")

    def get_api_key(self) -> Optional[str]:
        return self.api_key or os.getenv(f"{self.name.upper()}_API_KEY")


class LLMProvider(ABC):
    @abstractmethod
    def create_llm(self, config: ProviderConfig) -> BaseChatModel:
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        pass


class OllamaProvider(LLMProvider):
    def create_llm(self, config: ProviderConfig) -> BaseChatModel:
        from langchain_ollama import ChatOllama
        base_url = config.get_base_url() or "http://localhost:11434"
        return ChatOllama(
            model=config.model,
            base_url=base_url,
            temperature=config.temperature,
            **config.extra_params
        )

    def get_default_model(self) -> str:
        return "gemma4:e2b"


class OpenAIProvider(LLMProvider):
    def create_llm(self, config: ProviderConfig) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        api_key = config.get_api_key()
        base_url = config.get_base_url()
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            **config.extra_params
        }
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    def get_default_model(self) -> str:
        return "gpt-4o-mini"


class GoogleAIProvider(LLMProvider):
    def create_llm(self, config: ProviderConfig) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = config.get_api_key()
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            **config.extra_params
        }
        if api_key:
            kwargs["google_api_key"] = api_key
        return ChatGoogleGenerativeAI(**kwargs)

    def get_default_model(self) -> str:
        return "gemini-1.5-flash"


class AnthropicProvider(LLMProvider):
    def create_llm(self, config: ProviderConfig) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic
        api_key = config.get_api_key()
        base_url = config.get_base_url()
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            **config.extra_params
        }
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    def get_default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"


class GroqProvider(LLMProvider):
    def create_llm(self, config: ProviderConfig) -> BaseChatModel:
        from langchain_groq import ChatGroq
        api_key = config.get_api_key()
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            **config.extra_params
        }
        if api_key:
            kwargs["groq_api_key"] = api_key
        return ChatGroq(**kwargs)

    def get_default_model(self) -> str:
        return "llama-3.3-70b-versatile"


class TogetherAIProvider(LLMProvider):
    def create_llm(self, config: ProviderConfig) -> BaseChatModel:
        from langchain_together import ChatTogether
        api_key = config.get_api_key()
        base_url = config.get_base_url() or "https://api.together.xyz/v1"
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            **config.extra_params
        }
        if api_key:
            kwargs["together_api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        return ChatTogether(**kwargs)

    def get_default_model(self) -> str:
        return "meta-llama/Llama-3.3-70B-Instruct-Turbo"


PROVIDER_REGISTRY: dict[str, LLMProvider] = {
    "ollama": OllamaProvider(),
    "openai": OpenAIProvider(),
    "google": GoogleAIProvider(),
    "anthropic": AnthropicProvider(),
    "groq": GroqProvider(),
    "together": TogetherAIProvider(),
}


def get_provider(name: str) -> LLMProvider:
    provider = PROVIDER_REGISTRY.get(name.lower())
    if not provider:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDER_REGISTRY.keys())}")
    return provider


def create_llm(config: ProviderConfig) -> BaseChatModel:
    provider = get_provider(config.name)
    return provider.create_llm(config)


def create_llm_from_env(provider_name: str = None, model: str = None, base_url: str = None, api_key: str = None) -> BaseChatModel:
    """Create LLM from environment variables with optional overrides."""
    provider_name = provider_name or os.getenv("LLM_PROVIDER", "ollama").lower()
    provider = get_provider(provider_name)
    
    config = ProviderConfig(
        name=provider_name,
        model=model or os.getenv(f"{provider_name.upper()}_MODEL", provider.get_default_model()),
        base_url=base_url or os.getenv(f"{provider_name.upper()}_BASE_URL"),
        api_key=api_key or os.getenv(f"{provider_name.upper()}_API_KEY"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
    )
    return provider.create_llm(config)


def ask_with_provider(prompt: str, system: str, config: ProviderConfig) -> str:
    """Ask LLM using specific provider config."""
    chain = ChatPromptTemplate.from_messages([
        ("system", system),
        ("user", "{p}")
    ]) | create_llm(config)
    return chain.invoke({"p": prompt}).content