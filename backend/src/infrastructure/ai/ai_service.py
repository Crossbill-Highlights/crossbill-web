from src.application.learning.protocols.ai_flashcard_service import AIFlashcardSuggestion
from src.application.reading.protocols.ai_prereading_service import PrereadingResult
from src.infrastructure.ai.ai_agents import (
    get_flashcard_agent,
    get_prereading_agent,
    get_summary_agent,
)


class AIService:
    async def generate_summary(self, content: str) -> str:
        agent = get_summary_agent()
        result = await agent.run(content)
        return result.output

    async def generate_prereading(self, content: str) -> PrereadingResult:
        agent = get_prereading_agent()
        result = await agent.run(content[:10000])
        return PrereadingResult(summary=result.output.summary, keypoints=result.output.keypoints)

    async def generate_flashcard_suggestions(self, content: str) -> list[AIFlashcardSuggestion]:
        agent = get_flashcard_agent()
        result = await agent.run(content)
        return [AIFlashcardSuggestion(question=s.question, answer=s.answer) for s in result.output]
