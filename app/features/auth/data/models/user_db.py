from uuid import UUID

from sqlalchemy import String, DateTime, func, Index, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database.session import Base


class User(Base):
    """
    Maps 1:1 to Flutter AppUser entity.
    uid = Google UID (same value Firebase used — migration is zero-effort).
    """
    __tablename__ = "users"

    uid: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    # role: student | advisor | subjectTeacher | hod
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="student")
    # Denormalized display strings, kept in sync with department_id/batch_id. Source of truth is the FK.
    dept: Mapped[str | None] = mapped_column(String(128), nullable=True)
    batch: Mapped[str | None] = mapped_column(String(32), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    college_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("departments.id", name="fk_users_department_id_departments"), nullable=True
    )
    batch_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("batches.id", name="fk_users_batch_id_batches"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_users_college_id", "college_id"),
        Index("ix_users_department_id", "department_id"),
        Index("ix_users_batch_id", "batch_id"),
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User uid={self.uid} email={self.email} role={self.role}>"
