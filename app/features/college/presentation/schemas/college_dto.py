from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class CollegeSchema(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentSchema(BaseModel):
    id: UUID
    college_id: str
    slug: str
    name: str
    code: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class BatchSchema(BaseModel):
    id: UUID
    department_id: UUID
    label: str
    start_year: int
    end_year: int
    archived: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserScopeSchema(BaseModel):
    id: Optional[UUID] = None
    uid: str
    college_id: str
    department_id: UUID
    batch_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateDepartmentRequest(BaseModel):
    college_id: str
    slug: str
    name: str
    code: Optional[str] = None

    @field_validator("college_id", "slug", "name")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("value cannot be empty")
        return v.strip()


class AssignStudentScopeRequest(BaseModel):
    uid: str
    college_id: str
    department_id: UUID
    batch_id: UUID

    @field_validator("uid", "college_id")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("value cannot be empty")
        return v.strip()


class AssignStaffScopeRequest(BaseModel):
    uid: str
    college_id: str
    department_id: UUID
    batch_id: Optional[UUID] = None

    @field_validator("uid", "college_id")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("value cannot be empty")
        return v.strip()


class UserScopesResponse(BaseModel):
    kind: Literal["locked", "staff"]
    scopes: list[UserScopeSchema]

    class Config:
        from_attributes = True
