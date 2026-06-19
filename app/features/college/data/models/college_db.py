from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_colleges_active", "active"),
    )

    def __repr__(self) -> str:
        return f"<College id={self.id} name={self.name}>"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    college_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("colleges.id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        UniqueConstraint("college_id", "slug", name="uq_departments_college_slug"),
        Index("ix_departments_college_id", "college_id"),
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} college_id={self.college_id} slug={self.slug}>"


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    department_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(32), nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("end_year = start_year + 4", name="ck_batches_four_year_window"),
        UniqueConstraint("department_id", "start_year", "end_year", name="uq_batches_department_years"),
        Index("ix_batches_department_id", "department_id"),
    )

    def __repr__(self) -> str:
        return f"<Batch id={self.id} department_id={self.department_id} label={self.label}>"
