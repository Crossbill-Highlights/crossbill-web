from pydantic import BaseModel
from pydantic_ai import Agent

from src.services.ai.ai_model import ai_model


class SummaryAgentModel(BaseModel):
    summary: str


def get_summary_agent() -> Agent[None, str]:
    return Agent(
        ai_model,
        output_type=str,  # SummaryAgentModel,
        instructions="""
        You are given a content of user's last reading session from their book.
        Create concise summary of the read content to help user remember what they read. List key ideas,
        topics or events in the content and brief summary of the theme.
        """,
    )
