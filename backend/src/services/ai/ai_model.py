from functools import lru_cache

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import Model, OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from src.config import get_settings

settings = get_settings()


def _get_model() -> Model:
    """
    Get Pydantic AI model depending on environment settings.
    """

    if settings.AI_PROVIDER == "ollama":
        # These assertions are guaranteed by the settings validator
        assert settings.AI_MODEL_NAME is not None
        assert settings.OPENAI_BASE_URL is not None
        return OpenAIChatModel(
            model_name=settings.AI_MODEL_NAME,
            provider=OllamaProvider(base_url=settings.OPENAI_BASE_URL),
        )

    if settings.AI_PROVIDER == "openai":
        # These assertions are guaranteed by the settings validator
        assert settings.AI_MODEL_NAME is not None
        assert settings.OPENAI_API_KEY is not None
        return OpenAIChatModel(
            model_name=settings.AI_MODEL_NAME,
            provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY),
        )

    if settings.AI_PROVIDER == "anthropic":
        # These assertions are guaranteed by the settings validator
        assert settings.AI_MODEL_NAME is not None
        assert settings.ANTHROPIC_API_KEY is not None
        return AnthropicModel(
            model_name=settings.AI_MODEL_NAME,
            provider=AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY),
        )

    if settings.AI_PROVIDER == "google":
        # These assertions are guaranteed by the settings validator
        assert settings.AI_MODEL_NAME is not None
        assert settings.GEMINI_API_KEY is not None
        return GoogleModel(
            model_name=settings.AI_MODEL_NAME,
            provider=GoogleProvider(api_key=settings.GEMINI_API_KEY),
        )
    raise Exception("No such AI model provider available")


@lru_cache
def get_ai_model() -> Model:
    """
    Get cached AI model. This pattern allows us to lazily load the AI model only if AI features
    are enabled without having to worry about importing this or other AI related modules.
    """
    return _get_model()
