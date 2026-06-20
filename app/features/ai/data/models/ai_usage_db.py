from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base


class AiUsage(Base):
    __tablename__ = "ai_usage"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    uid: Mapped[str] = mapped_column(String(128), ForeignKey("users.uid"), nullable=False)
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_ai_usage_uid", "uid"),
    )

    def __repr__(self) -> str:
        return f"<AiUsage id={self.id} uid={self.uid} used_at={self.used_at}>"
