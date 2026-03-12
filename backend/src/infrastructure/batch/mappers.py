from src.domain.batch.entities.batch_item import BatchItem as DomainBatchItem
from src.domain.batch.entities.batch_item import BatchItemStatus
from src.domain.batch.entities.batch_job import BatchJob as DomainBatchJob
from src.domain.batch.entities.batch_job import BatchJobStatus
from src.domain.common.value_objects.ids import (
    BatchItemId,
    BatchJobId,
    BookId,
    UserId,
)
from src.models import BatchItem as BatchItemORM
from src.models import BatchJob as BatchJobORM


class BatchJobMapper:
    def to_domain(self, orm: BatchJobORM) -> DomainBatchJob:
        return DomainBatchJob.create_with_id(
            id=BatchJobId(orm.id),
            user_id=UserId(orm.user_id),
            book_id=BookId(orm.book_id),
            job_type=orm.job_type,
            status=BatchJobStatus(orm.status),
            total_items=orm.total_items,
            completed_items=orm.completed_items,
            failed_items=orm.failed_items,
            created_at=orm.created_at,
            completed_at=orm.completed_at,
        )

    def to_orm(self, entity: DomainBatchJob, orm: BatchJobORM | None = None) -> BatchJobORM:
        if orm is not None:
            orm.status = entity.status.value
            orm.total_items = entity.total_items
            orm.completed_items = entity.completed_items
            orm.failed_items = entity.failed_items
            orm.completed_at = entity.completed_at
            return orm

        return BatchJobORM(
            id=entity.id.value if entity.id.value != 0 else None,
            user_id=entity.user_id.value,
            book_id=entity.book_id.value,
            job_type=entity.job_type,
            status=entity.status.value,
            total_items=entity.total_items,
            completed_items=entity.completed_items,
            failed_items=entity.failed_items,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )


class BatchItemMapper:
    def to_domain(self, orm: BatchItemORM) -> DomainBatchItem:
        return DomainBatchItem.create_with_id(
            id=BatchItemId(orm.id),
            batch_job_id=BatchJobId(orm.batch_job_id),
            entity_type=orm.entity_type,
            entity_id=orm.entity_id,
            status=BatchItemStatus(orm.status),
            attempts=orm.attempts,
            error_message=orm.error_message,
            created_at=orm.created_at,
            completed_at=orm.completed_at,
        )

    def to_orm(self, entity: DomainBatchItem, orm: BatchItemORM | None = None) -> BatchItemORM:
        if orm is not None:
            orm.status = entity.status.value
            orm.attempts = entity.attempts
            orm.error_message = entity.error_message
            orm.completed_at = entity.completed_at
            return orm

        return BatchItemORM(
            id=entity.id.value if entity.id.value != 0 else None,
            batch_job_id=entity.batch_job_id.value,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            status=entity.status.value,
            attempts=entity.attempts,
            error_message=entity.error_message,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )
