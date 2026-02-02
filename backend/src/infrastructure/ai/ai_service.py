from src.infrastructure.ai.ai_agents import (
    FlashcardSuggestion,
    get_flashcard_agent,
    get_summary_agent,
)


async def get_ai_summary_from_text(content: str) -> str:  # SummaryAgentModel:
    agent = get_summary_agent()

    result = await agent.run(content)
    return result.output


async def get_ai_flashcard_suggestions_from_text(
    content: str,
) -> list[FlashcardSuggestion]:  # SummaryAgentModel:
    agent = get_flashcard_agent()

    result = await agent.run(content)
    return result.output
