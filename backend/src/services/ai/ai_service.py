from src.services.ai.ai_agents import get_summary_agent


async def get_ai_summary_from_text(content: str) -> str:  # SummaryAgentModel:
    agent = get_summary_agent()

    result = await agent.run(content)
    print(result.usage())
    return result.output
