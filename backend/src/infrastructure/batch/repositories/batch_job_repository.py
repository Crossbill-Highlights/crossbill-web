from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.batch.entities.batch_item import BatchItem as DomainBatchItem
from src.domain.batch.entities.batch_item import BatchItemStatus
from src.domain.batch.entities.batch_job import BatchJob as DomainBatchJob
from src.domain.batch.entities.batch_job import BatchJobStatus
from src.domain.common.value_objects.ids import BatchJobId, BookId, UserId
from src.infrastructure.batch.mappers import BatchItemMapper, BatchJobMapper
from src.models import BatchItem as BatchItemORM
from src.models import BatchJob as BatchJobORM


class BatchJobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.job_mapper = BatchJobMapper()
        self.item_mapper = BatchItemMapper()

    async def save_job(self, job: DomainBatchJob) -> DomainBatchJob:
        if job.id.value != 0:
            # Update existing
            result = await self.db.execute(
                select(BatchJobORM).where(BatchJobORM.id == job.id.value)
            )
            existing_orm = result.scalar_one_or_none()
            if existing_orm is not None:
                self.job_mapper.to_orm(job, existing_orm)
                await self.db.commit()
                await self.db.refresh(existing_orm)
                return self.job_mapper.to_domain(existing_orm)

        # Insert new
        orm = self.job_mapper.to_orm(job)
        self.db.add(orm)
        await self.db.commit()
        await self.db.refresh(orm)
        return self.job_mapper.to_domain(orm)

    async def save_item(self, item: DomainBatchItem) -> DomainBatchItem:
        if item.id.value != 0:
            result = await self.db.execute(
                select(BatchItemORM).where(BatchItemORM.id == item.id.value)
            )
            existing_orm = result.scalar_one_or_none()
            if existing_orm is not None:
                self.item_mapper.to_orm(item, existing_orm)
                await self.db.commit()
                await self.db.refresh(existing_orm)
                return self.item_mapper.to_domain(existing_orm)

        orm = self.item_mapper.to_orm(item)
        self.db.add(orm)
        await self.db.commit()
        await self.db.refresh(orm)
        return self.item_mapper.to_domain(orm)

    async def save_items(self, items: list[DomainBatchItem]) -> list[DomainBatchItem]:
        orms = [self.item_mapper.to_orm(item) for item in items]
        self.db.add_all(orms)
        await self.db.commit()
        for orm in orms:
            await self.db.refresh(orm)
        return [self.item_mapper.to_domain(orm) for orm in orms]

    async def get_job(self, job_id: BatchJobId) -> DomainBatchJob | None:
        result = await self.db.execute(select(BatchJobORM).where(BatchJobORM.id == job_id.value))
        orm = result.scalar_one_or_none()
        return self.job_mapper.to_domain(orm) if orm else None

    async def get_job_items(self, job_id: BatchJobId) -> list[DomainBatchItem]:
        result = await self.db.execute(
            select(BatchItemORM).where(BatchItemORM.batch_job_id == job_id.value)
        )
        return [self.item_mapper.to_domain(orm) for orm in result.scalars().all()]

    async def get_pending_items(self, job_id: BatchJobId) -> list[DomainBatchItem]:
        result = await self.db.execute(
            select(BatchItemORM).where(
                BatchItemORM.batch_job_id == job_id.value,
                BatchItemORM.status == BatchItemStatus.PENDING.value,
            )
        )
        return [self.item_mapper.to_domain(orm) for orm in result.scalars().all()]

    async def find_active_job(
        self, user_id: UserId, book_id: BookId, job_type: str
    ) -> DomainBatchJob | None:
        result = await self.db.execute(
            select(BatchJobORM).where(
                BatchJobORM.user_id == user_id.value,
                BatchJobORM.book_id == book_id.value,
                BatchJobORM.job_type == job_type,
                BatchJobORM.status.in_(
                    [
                        BatchJobStatus.PENDING.value,
                        BatchJobStatus.PROCESSING.value,
                    ]
                ),
            )
        )
        orm = result.scalar_one_or_none()
        return self.job_mapper.to_domain(orm) if orm else None
