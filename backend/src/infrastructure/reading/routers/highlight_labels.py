"""Router for highlight label management."""

from fastapi import APIRouter, Depends

from src.application.reading.use_cases.highlight_labels.create_global_highlight_label_use_case import (
    CreateGlobalHighlightLabelUseCase,
)
from src.application.reading.use_cases.highlight_labels.get_book_highlight_labels_use_case import (
    GetBookHighlightLabelsUseCase,
)
from src.application.reading.use_cases.highlight_labels.get_global_highlight_labels_use_case import (
    GetGlobalHighlightLabelsUseCase,
)
from src.application.reading.use_cases.highlight_labels.update_highlight_label_use_case import (
    UpdateHighlightLabelUseCase,
)
from src.core import container
from src.domain.identity.entities.user import User
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.reading.schemas.highlight_schemas import (
    HighlightLabelCreate,
    HighlightLabelInBook,
    HighlightLabelUpdate,
)

router = APIRouter(tags=["highlight-labels"])


@router.get("/books/{book_id}/highlight-labels", response_model=list[HighlightLabelInBook])
def get_book_highlight_labels(
    book_id: int,
    current_user: User = Depends(get_current_user),
    use_case: GetBookHighlightLabelsUseCase = Depends(
        inject_use_case(container.get_book_highlight_labels_use_case)
    ),
) -> list[HighlightLabelInBook]:
    """Get all highlight labels for a book with resolved labels."""
    results = use_case.execute(book_id=book_id, user_id=current_user.id.value)
    return [
        HighlightLabelInBook(
            id=style.id.value,
            device_color=style.device_color,
            device_style=style.device_style,
            label=resolved.label,
            ui_color=resolved.ui_color,
            label_source=resolved.source,
            highlight_count=count,
        )
        for style, resolved, count in results
    ]


@router.patch("/highlight-labels/{style_id}", response_model=HighlightLabelInBook)
def update_highlight_label(
    style_id: int,
    body: HighlightLabelUpdate,
    current_user: User = Depends(get_current_user),
    use_case: UpdateHighlightLabelUseCase = Depends(
        inject_use_case(container.update_highlight_label_use_case)
    ),
) -> HighlightLabelInBook:
    """Update label and/or ui_color on a highlight style."""
    style = use_case.execute(
        style_id=style_id,
        user_id=current_user.id.value,
        label=body.label,
        ui_color=body.ui_color,
    )
    return HighlightLabelInBook(
        id=style.id.value,
        device_color=style.device_color,
        device_style=style.device_style,
        label=style.label,
        ui_color=style.ui_color,
        label_source="book" if style.book_id else "global",
        highlight_count=0,
    )


@router.get("/highlight-labels/global", response_model=list[HighlightLabelInBook])
def get_global_highlight_labels(
    current_user: User = Depends(get_current_user),
    use_case: GetGlobalHighlightLabelsUseCase = Depends(
        inject_use_case(container.get_global_highlight_labels_use_case)
    ),
) -> list[HighlightLabelInBook]:
    """Get all global default highlight labels."""
    styles = use_case.execute(user_id=current_user.id.value)
    return [
        HighlightLabelInBook(
            id=s.id.value,
            device_color=s.device_color,
            device_style=s.device_style,
            label=s.label,
            ui_color=s.ui_color,
            label_source="global",
            highlight_count=0,
        )
        for s in styles
    ]


@router.post("/highlight-labels/global", response_model=HighlightLabelInBook, status_code=201)
def create_global_highlight_label(
    body: HighlightLabelCreate,
    current_user: User = Depends(get_current_user),
    use_case: CreateGlobalHighlightLabelUseCase = Depends(
        inject_use_case(container.create_global_highlight_label_use_case)
    ),
) -> HighlightLabelInBook:
    """Create a global default highlight label."""
    style = use_case.execute(
        user_id=current_user.id.value,
        device_color=body.device_color,
        device_style=body.device_style,
        label=body.label,
        ui_color=body.ui_color,
    )
    return HighlightLabelInBook(
        id=style.id.value,
        device_color=style.device_color,
        device_style=style.device_style,
        label=style.label,
        ui_color=style.ui_color,
        label_source="global",
        highlight_count=0,
    )
