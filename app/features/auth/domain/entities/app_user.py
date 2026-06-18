from dataclasses import dataclass
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    student = "student"
    advisor = "advisor"
    subject_teacher = "subjectTeacher"
    hod = "hod"


@dataclass(frozen=True)
class AppUser:
    uid: str
    name: str
    email: str
    role: UserRole
    dept: Optional[str] = None
    batch: Optional[str] = None
    photo_url: Optional[str] = None
    college_id: Optional[str] = None
