from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base


class UserScope(Base):
    __tablename__ = "user_scopes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    uid: Mapped[str] = mapped_column(
        String(128), ForeignKey("users.uid", ondelete="CASCADE"), nullable=False
    )
    college_id: Mapped[str] = mapped_column(String(128), ForeignKey("colleges.id"), nullable=False)
    department_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    batch_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("batches.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_user_scopes_uid", "uid"),
        Index("ix_user_scopes_department_id", "department_id"),
        Index("ix_user_scopes_batch_id", "batch_id"),
    )

    def __repr__(self) -> str:
        return f"<UserScope id={self.id} uid={self.uid} department_id={self.department_id}>"
