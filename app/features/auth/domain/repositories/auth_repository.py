from abc import ABC, abstractmethod
from typing import Optional
from app.features.auth.domain.entities.app_user import AppUser


class IAuthRepository(ABC):
    @abstractmethod
    async def get_user(self, uid: str) -> Optional[AppUser]: ...

    @abstractmethod
    async def save_user(self, user: AppUser) -> AppUser: ...

    @abstractmethod
    async def save_fcm_token(self, uid: str, token: str) -> None: ...
