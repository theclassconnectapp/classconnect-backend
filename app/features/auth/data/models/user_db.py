from sqlalchemy import String, DateTime, func, Index
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
    dept: Mapped[str | None] = mapped_column(String(128), nullable=True)
    batch: Mapped[str | None] = mapped_column(String(32), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    college_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
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
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User uid={self.uid} email={self.email} role={self.role}>"
