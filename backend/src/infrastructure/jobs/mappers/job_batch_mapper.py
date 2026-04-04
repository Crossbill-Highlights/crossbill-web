"""Mapper between JobBatch domain entity and ORM model."""

from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchStatus, JobBatchType
from src.infrastructure.jobs.orm.job_batch_model import JobBatchModel


class JobBatchMapper:
    @staticmethod
    def to_domain(model: JobBatchModel) -> JobBatch:
        return JobBatch.create_with_id(
            id=JobBatchId(model.id),
            user_id=UserId(model.user_id),
            batch_type=JobBatchType(model.batch_type),
            reference_id=model.reference_id,
            total_jobs=model.total_jobs,
            completed_jobs=model.completed_jobs,
            failed_jobs=model.failed_jobs,
            status=JobBatchStatus(model.status),
            job_keys=list(model.job_keys),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_orm(entity: JobBatch, existing: JobBatchModel | None = None) -> JobBatchModel:
        model = existing or JobBatchModel()
        model.user_id = entity.user_id.value
        model.batch_type = entity.batch_type.value
        model.reference_id = entity.reference_id
        model.total_jobs = entity.total_jobs
        model.completed_jobs = entity.completed_jobs
        model.failed_jobs = entity.failed_jobs
        model.status = entity.status.value
        model.job_keys = list(entity.job_keys)
        return model
