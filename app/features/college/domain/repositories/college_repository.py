from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.features.college.domain.entities.college import Batch, College, Department, UserScope
from app.features.college.domain.entities.user_scopes_result import UserScopesResult


class ICollegeRepository(ABC):
    @abstractmethod
    async def get_college(self, college_id: str) -> Optional[College]: ...

    @abstractmethod
    async def list_departments(self, college_id: str) -> list[Department]: ...

    @abstractmethod
    async def get_department(self, department_id: UUID) -> Optional[Department]: ...

    @abstractmethod
    async def list_batches(self, department_id: UUID) -> list[Batch]: ...

    @abstractmethod
    async def get_batch(self, batch_id: UUID) -> Optional[Batch]: ...

    @abstractmethod
    async def create_department(
        self,
        college_id: str,
        slug: str,
        name: str,
        code: Optional[str],
        created_by: Optional[str],
    ) -> Department: ...

    @abstractmethod
    async def seed_batches_for_department(
        self,
        department_id: UUID,
        start_year: int,
        count: int = 5,
    ) -> list[Batch]: ...

    @abstractmethod
    async def assign_student_scope(
        self,
        uid: str,
        college_id: str,
        access_code: Optional[str],
        department_id: UUID,
        batch_id: UUID,
    ) -> UserScope: ...

    @abstractmethod
    async def assign_staff_scope(
        self,
        uid: str,
        college_id: str,
        access_code: Optional[str],
        department_id: UUID,
        batch_id: Optional[UUID] = None,
    ) -> UserScope: ...

    @abstractmethod
    async def get_user_scopes(self, uid: str) -> UserScopesResult: ...
