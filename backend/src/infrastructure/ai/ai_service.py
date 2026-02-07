from src.infrastructure.ai.ai_agents import (
    FlashcardSuggestion,
    PrereadingContent,
    get_flashcard_agent,
    get_prereading_agent,
    get_summary_agent,
)


async def get_ai_summary_from_text(content: str) -> str:  # SummaryAgentModel:
    agent = get_summary_agent()

    result = await agent.run(content)
    return result.output


async def get_ai_prereading_from_text(content: str) -> PrereadingContent:
    agent = get_prereading_agent()

    result = await agent.run(content[:10000])  # Limit for token efficiency
    return result.output


async def get_ai_flashcard_suggestions_from_text(
    content: str,
) -> list[FlashcardSuggestion]:  # SummaryAgentModel:
    agent = get_flashcard_agent()

    result = await agent.run(content)
    return result.output
