"""Quiz session endpoints for chapter-based AI quizzes."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.learning.use_cases.quiz.send_quiz_message_use_case import (
    SendQuizMessageUseCase,
)
from src.application.learning.use_cases.quiz.start_quiz_session_use_case import (
    StartQuizSessionUseCase,
)
from src.core import container
from src.domain.common.exceptions import DomainError
from src.domain.identity.entities.user import User
from src.domain.common.exceptions import ValidationError
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.learning.schemas.quiz_schemas import (
    CreateQuizSessionResponse,
    SendQuizMessageRequest,
    SendQuizMessageResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["quiz"])


@router.post(
    "/chapters/{chapter_id}/quiz-sessions",
    response_model=CreateQuizSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_ai_enabled
async def create_quiz_session(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: StartQuizSessionUseCase = Depends(
        inject_use_case(container.learning.start_quiz_session_use_case)
    ),
) -> CreateQuizSessionResponse:
    """Start a new quiz session for a chapter."""
    try:
        session_id, first_question = await use_case.start(chapter_id, current_user.id.value)
        return CreateQuizSessionResponse(session_id=session_id, message=first_question)
    except (DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            "failed_to_create_quiz_session",
            chapter_id=chapter_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/quiz-sessions/{session_id}/messages",
    response_model=SendQuizMessageResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def send_quiz_message(
    session_id: int,
    body: SendQuizMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: SendQuizMessageUseCase = Depends(
        inject_use_case(container.learning.send_quiz_message_use_case)
    ),
) -> SendQuizMessageResponse:
    """Send a message to an existing quiz session."""
    try:
        ai_response = await use_case.send(session_id, body.message, current_user.id.value)
        return SendQuizMessageResponse(message=ai_response)
    except (DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            "failed_to_send_quiz_message",
            session_id=session_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
