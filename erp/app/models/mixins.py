from datetime import datetime, timezone

from sqlalchemy import DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ActiveMixin:
    """Soft archive flag used instead of hard deletion for master data."""
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
