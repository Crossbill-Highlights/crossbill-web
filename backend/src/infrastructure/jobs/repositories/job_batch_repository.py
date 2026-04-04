"""SQLAlchemy repository for job batches."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch
from src.infrastructure.jobs.mappers.job_batch_mapper import JobBatchMapper
from src.infrastructure.jobs.orm.job_batch_model import JobBatchModel


class JobBatchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save(self, batch: JobBatch) -> JobBatch:
        existing_model: JobBatchModel | None = None
        if batch.id.value > 0:
            existing_model = await self._db.get(JobBatchModel, batch.id.value)

        model = JobBatchMapper.to_orm(batch, existing_model)
        if not existing_model:
            self._db.add(model)

        await self._db.commit()
        await self._db.refresh(model)
        return JobBatchMapper.to_domain(model)

    async def find_by_id(self, batch_id: JobBatchId, user_id: UserId) -> JobBatch | None:
        result = await self._db.execute(
            select(JobBatchModel).where(
                JobBatchModel.id == batch_id.value,
                JobBatchModel.user_id == user_id.value,
            )
        )
        model = result.scalar_one_or_none()
        return JobBatchMapper.to_domain(model) if model else None

    async def find_by_id_internal(self, batch_id: JobBatchId) -> JobBatch | None:
        result = await self._db.execute(
            select(JobBatchModel).where(JobBatchModel.id == batch_id.value)
        )
        model = result.scalar_one_or_none()
        return JobBatchMapper.to_domain(model) if model else None

    async def find_by_reference(
        self, batch_type: str, reference_id: str, user_id: UserId
    ) -> list[JobBatch]:
        result = await self._db.execute(
            select(JobBatchModel)
            .where(
                JobBatchModel.batch_type == batch_type,
                JobBatchModel.reference_id == reference_id,
                JobBatchModel.user_id == user_id.value,
            )
            .order_by(JobBatchModel.created_at.desc())
        )
        return [JobBatchMapper.to_domain(m) for m in result.scalars().all()]
