"""Mapper for ChapterPrereadingContent ORM ↔ Domain conversion."""

from src.domain.common.value_objects.ids import ChapterId, PrereadingContentId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
    PrereadingQuestion,
)
from src.models import ChapterPrereadingContent as PrereadingContentORM


class ChapterPrereadingMapper:
    """Mapper between ChapterPrereadingContent domain entity and ORM model."""

    def to_domain(self, orm: PrereadingContentORM) -> ChapterPrereadingContent:
        """Convert ORM model to domain entity."""
        return ChapterPrereadingContent.create_with_id(
            id=PrereadingContentId(orm.id),
            chapter_id=ChapterId(orm.chapter_id),
            questions=[
                PrereadingQuestion(
                    question=q["question"],
                    answer=q["answer"],
                    user_answer=q.get("user_answer", ""),
                )
                for q in orm.questions
            ],
            summary=orm.summary,
            keypoints=orm.keypoints,
            generated_at=orm.generated_at,
            ai_model=orm.ai_model,
        )

    def to_orm(
        self, entity: ChapterPrereadingContent, orm: PrereadingContentORM | None = None
    ) -> PrereadingContentORM:
        """Convert domain entity to ORM model."""
        questions = [
            {"question": q.question, "answer": q.answer, "user_answer": q.user_answer}
            for q in entity.questions
        ]

        if orm:
            orm.chapter_id = entity.chapter_id.value
            orm.summary = entity.summary
            orm.keypoints = entity.keypoints
            orm.questions = questions
            orm.generated_at = entity.generated_at
            orm.ai_model = entity.ai_model
            return orm

        return PrereadingContentORM(
            id=entity.id.value if entity.id.value != 0 else None,
            chapter_id=entity.chapter_id.value,
            summary=entity.summary,
            keypoints=entity.keypoints,
            questions=questions,
            generated_at=entity.generated_at,
            ai_model=entity.ai_model,
        )
