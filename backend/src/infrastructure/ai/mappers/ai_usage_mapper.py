from src.domain.ai.entities.ai_usage_record import AIUsageRecord
from src.domain.common.value_objects.ids import AIUsageRecordId, UserId
from src.models import AIUsageRecord as AIUsageRecordORM


class AIUsageMapper:
    def to_orm(self, entity: AIUsageRecord) -> AIUsageRecordORM:
        return AIUsageRecordORM(
            id=entity.id.value if entity.id.value != 0 else None,
            user_id=entity.user_id.value,
            task_type=entity.task_type,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            model_name=entity.model_name,
            input_tokens=entity.input_tokens,
            output_tokens=entity.output_tokens,
            created_at=entity.created_at,
        )

    def to_domain(self, orm: AIUsageRecordORM) -> AIUsageRecord:
        return AIUsageRecord(
            id=AIUsageRecordId(orm.id),
            user_id=UserId(orm.user_id),
            task_type=orm.task_type,
            entity_type=orm.entity_type,
            entity_id=orm.entity_id,
            model_name=orm.model_name,
            input_tokens=orm.input_tokens,
            output_tokens=orm.output_tokens,
            created_at=orm.created_at,
        )
