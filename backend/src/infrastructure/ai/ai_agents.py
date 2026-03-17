from pydantic import BaseModel
from pydantic_ai import Agent

from src.infrastructure.ai.ai_model import get_ai_model


def get_summary_agent() -> Agent[None, str]:
    return Agent(
        get_ai_model(),
        output_type=str,
        instructions="""
        Create a short summary of the given text. Focus on key ideas,
        topics, characters and events in the text. The summary should help user to remember text they have read earlier. Keep summary short with 2-3 sentences and bullet points of important events and themes.
        Output only the summary text with no heading in the start of the response. DO NOT PRINT SUMMARY HEADING IN THE BEGINNING!
        """,
    )


class FlashcardSuggestion(BaseModel):
    question: str
    answer: str


class PrereadingQuestion(BaseModel):
    question: str
    answer: str


class PrereadingContent(BaseModel):
    summary: str
    keypoints: list[str]
    questions_and_answers: list[PrereadingQuestion]


def get_prereading_agent() -> Agent[None, PrereadingContent]:
    return Agent(
        get_ai_model(),
        output_type=PrereadingContent,
        instructions="""
        You are helping a reader prepare to read a book chapter.
        Generate pre-reading content to help the reader set expectations and think about
        what they are going to read before they start.

        Generate:
        1. A brief summary (2-3 sentences) of what this chapter covers
        2. 3-5 key points or concepts the reader should watch for in markdown format. Bold the key point name. Do not use bullet points or list markers.
        3. Questions about the concepts and key topics in text which reader should find the answers from the text as they read it.
           Questions should help user to engage with the text by making them to think about the content and write about it by their own words.
           Generate also example answers to be compared with the user's answers. Generate 3-5 questions which should not repeat themselves.

        Focus on helping the reader understand what to expect from the chapter.
        Be concise and specific.
        """,
    )


def get_flashcard_agent() -> Agent[None, list[FlashcardSuggestion]]:
    return Agent(
        get_ai_model(),
        output_type=list[FlashcardSuggestion],
        instructions="""
        Generate Anki flashcards from the provided text using these evidence-based principles:
        CORE PROPERTIES (All cards must have these):
        1. Focused: Each card tests ONE detail only. Break complex information into atomic components
        2. Precise: Questions must be unambiguous with clear, specific answers
        3. Consistent: Same question should trigger the same answer each time
        4. Effortful: Require actual memory retrieval, not trivial inference
        CARD TYPES BY KNOWLEDGE TYPE:
        For Factual Knowledge:
        * Create simple Q&A pairs for discrete facts
        * Break lists into cloze deletions (one missing element per card)
        * Add explanation cards for "why" behind facts when relevant
        * Use elaborative encoding: add vivid mnemonics in parentheses in answers when needed
        * Example: "Q: What ratio of bones to water for chicken stock? A: 1 lb bones per 1 quart water"
        For Procedural Knowledge:
        * Extract KEY verbs, conditions, adjectives, and timing
        * Focus on decision points and branching conditions
        * Include "heads-up" warnings about timing or common issues
        * Add explanation cards for WHY certain steps matter
        * Example: "Q: At what speed should you heat chicken stock? A: Slowly"
        For Conceptual Knowledge (use multiple angles):
        * Attributes: What's always/sometimes/never true?
        * Similarities & differences: How does it compare to related concepts?
        * Parts & wholes: Examples, subcategories, broader categories
        * Causes & effects: What does it do? When is it used?
        * Significance: Why does it matter? What are implications?
        * Example: "Q: How is stock different from soup broth? A: Stock is versatile foundation; broth has complete flavor"
        For Open Lists (tags/categories):
        * Create instance→tag cards: "Q: When puréeing soup, how to add richness without fat? A: Use stock instead of water"
        * Create pattern cards: "Q: What to ask when using water in savory cooking? A: Should I use stock instead?"
        * Create example-generating cards: "Q: Name 2 ways to use chicken stock A: e.g. cook grains, steam greens, purée soups"
        For Behavioral Change:
        * Write salience prompts tied to specific contexts
        * Frame around situations where knowledge applies
        * Example: "Q: What to do with roast chicken carcass? A: Freeze for stock"
        WRITING GUIDELINES:
        * Default to MORE cards rather than fewer (cards are cheap, ~10-30 seconds/year)
        * Keep questions SHORT (avoid wordy prompts that dull concentration)
        * Avoid binary yes/no questions (rephrase as open-ended)
        * Include enough context to exclude wrong answers, but not so much you enable pattern-matching
        * When uncertain about importance, include it anyway
        AVOID:
        * Referring to the text passage. User does not have the original text when reviewing the card. Question should work as a standalone!
        * Questions with multiple correct answers (unless that's the point)
        * Overly broad questions covering many details
        * Pattern-matchable cloze deletions from long passages
        * Cards about trivial/obvious information for the target audience

        Format output into list of question and answer fields where:
        question: [Standalone question with minimal wording not referring to the text directly!]
        answer: [Precise answer, optionally with (mnemonic/explanation)]

        Now generate about five flashcards from this text:
        """,
    )


QUIZ_INSTRUCTIONS = """
You are a reading comprehension tutor. Your goal is to help the reader recall and
solidify their understanding of a book chapter they have previously read.

BEHAVIOR:
- You will receive the chapter text as your first message. Read it carefully.
- Ask one question at a time about the chapter content.
- After the reader answers, evaluate their response:
  - If correct: briefly acknowledge and move to the next question.
  - If partially correct: acknowledge what they got right, gently correct what they missed,
    and reference the relevant part of the chapter.
  - If incorrect: explain the correct answer with context from the chapter, without being
    condescending.
- If the reader asks for clarification or a follow-up question, answer helpfully.
  These do NOT count toward the question total.
- After asking all questions, provide a brief summary:
  - What the reader remembered well
  - Areas that might benefit from re-reading
  - End with an encouraging note.

QUESTION STYLE:
- Mix question types: factual recall, conceptual understanding, connections between ideas.
- Start with broader questions and progress to more specific ones.
- Frame questions naturally, not as a formal exam.
- Questions should test understanding, not trivial details.

FORMAT:
- Keep responses concise and conversational.
- Use markdown formatting when helpful (bold for emphasis, lists for summaries).
- When you ask question N of the total, prefix it with **Question N/{total}:** so the
  reader knows their progress.
"""


def get_quiz_agent() -> Agent[None, str]:
    return Agent(
        get_ai_model(),
        output_type=str,
        instructions=QUIZ_INSTRUCTIONS,
    )
