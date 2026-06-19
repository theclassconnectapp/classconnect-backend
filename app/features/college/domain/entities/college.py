from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class College:
    id: str
    name: str
    code: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class Department:
    id: UUID
    college_id: str
    slug: str
    name: str
    code: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None


@dataclass(frozen=True)
class Batch:
    id: UUID
    department_id: UUID
    label: str
    start_year: int
    end_year: int
    archived: bool = False
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class UserScope:
    id: Optional[UUID]
    uid: str
    college_id: str
    department_id: UUID
    batch_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
