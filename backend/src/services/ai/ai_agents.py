from pydantic_ai import Agent

from src.services.ai.ai_model import get_ai_model


def get_summary_agent() -> Agent[None, str]:
    return Agent(
        get_ai_model(),
        output_type=str,
        instructions="""
        Create a short summary of the given text. Focus on key ideas,
        topics, characters and events in the text. The summary should help user to remember text they have read earlier. Keep summary short with 2-3 sentences and bullet points of important events and themes.
        Output only the summary text with no heading in the start of the response.
        """,
    )
