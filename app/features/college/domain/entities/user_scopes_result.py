from dataclasses import dataclass
from typing import Literal

from app.features.college.domain.entities.college import UserScope


@dataclass(frozen=True)
class UserScopesResult:
    kind: Literal["locked", "staff"]
    scopes: list[UserScope]
