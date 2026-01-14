from functools import lru_cache

from pydantic_ai.models.openai import Model, OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from src.config import get_settings

settings = get_settings()


def _get_model() -> Model:
    """
    Get Pydantic AI model depending on environment settings.
    """

    if settings.AI_PROVIDER == "ollama":
        if settings.AI_MODEL_NAME is None or settings.OPENAI_BASE_URL is None:
            raise Exception(
                "Please provide AI_MODEL_NAME and OPENAI_BASE_URL environment variables!"
            )
        return OpenAIChatModel(
            model_name=settings.AI_MODEL_NAME,
            provider=OllamaProvider(base_url=settings.OPENAI_BASE_URL),
        )

    if settings.AI_PROVIDER == "openai":
        if settings.AI_MODEL_NAME is None or settings.OPENAI_API_KEY is None:
            raise Exception(
                "Please provide AI_MODEL_NAME and OPENAI_API_KEY environment variables!"
            )
        return OpenAIChatModel(
            model_name=settings.AI_MODEL_NAME,
            provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY),
        )

    raise Exception("No such AI model provider available")


@lru_cache
def get_ai_model() -> Model:
    """
    Get cached AI model. This pattern allows us to lazily load the AI model only if AI features
    are enabled without having to worry about importing this or other AI related modules.
    """
    return _get_model()
