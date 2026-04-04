"""Jobs domain exceptions."""

from src.domain.common.exceptions import EntityNotFoundError


class JobBatchNotFoundError(EntityNotFoundError):
    """Raised when a job batch cannot be found."""

    def __init__(self, batch_id: int) -> None:
        super().__init__("JobBatch", batch_id)
