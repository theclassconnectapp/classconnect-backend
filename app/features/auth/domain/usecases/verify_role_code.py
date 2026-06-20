"""
UseCase: VerifyRoleCode
Placeholder for advisor/hod invite code verification.
Phase 2 will move codes to DB with expiry.
"""
import os
from typing import Optional

# TODO Phase 2: move to DB with expiry + college scoping
ROLE_CODES: dict[str, str] = {
    os.environ.get("HOD_CODE", "HOD2025"): "hod",
    os.environ.get("TEACHER_CODE", "TEACH2025"): "subjectTeacher",
    os.environ.get("ADVISOR_CODE", "ADV2025"): "advisor",
}


def execute(code: str) -> Optional[str]:
    """Returns role string if code valid, else None."""
    return ROLE_CODES.get(code.strip().upper())
