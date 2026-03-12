"""AI model factory for batch processing.

Reads batch-specific settings (BATCH_AI_PROVIDER, BATCH_AI_MODEL_NAME)
with fallback to the main AI settings (AI_PROVIDER, AI_MODEL_NAME).
"""

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import Model, OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from src.config import get_settings


def get_batch_ai_model() -> Model:
    """Get the AI model configured for batch processing.

    Resolution order:
    1. BATCH_AI_PROVIDER / BATCH_AI_MODEL_NAME (batch-specific)
    2. AI_PROVIDER / AI_MODEL_NAME (main app settings, fallback)
    """
    settings = get_settings()

    provider = settings.BATCH_AI_PROVIDER or settings.AI_PROVIDER
    model_name = settings.BATCH_AI_MODEL_NAME or settings.AI_MODEL_NAME

    if provider is None or model_name is None:
        raise RuntimeError(
            "Batch AI model not configured. Set BATCH_AI_PROVIDER/BATCH_AI_MODEL_NAME "
            "or AI_PROVIDER/AI_MODEL_NAME."
        )

    if provider == "ollama":
        return OpenAIChatModel(
            model_name, provider=OllamaProvider(base_url=settings.OPENAI_BASE_URL)
        )
    if provider == "openai":
        return OpenAIChatModel(model_name, provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY))
    if provider == "anthropic":
        return AnthropicModel(
            model_name, provider=AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
        )
    if provider == "google":
        return GoogleModel(model_name, provider=GoogleProvider(api_key=settings.GEMINI_API_KEY))
    raise RuntimeError(f"Unknown batch AI provider: {provider}")
