from pydantic_ai.models.openai import Model, OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.config import get_settings

settings = get_settings()


def get_model() -> Model:
    """
    Get Pydantic AI model depending on environment settings.
    """

    if settings.AI_MODEL_NAME is None or settings.OPENAI_BASE_URL is None:
        raise Exception("Please provide AI_MODEL_NAME and OPENAI_BASE_URL environment variables!")

    if settings.AI_PROVIDER == "ollama":
        return OpenAIChatModel(
            model_name=settings.AI_MODEL_NAME,
            provider=OllamaProvider(base_url=settings.OPENAI_BASE_URL),
        )

    raise Exception("No such AI model provider available")


ai_model = get_model()
