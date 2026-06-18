from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

VALID_ROLES = {"student", "advisor", "subjectTeacher", "hod"}


class AppUserSchema(BaseModel):
    uid: str
    name: str
    email: str
    role: str
    dept: Optional[str] = None
    batch: Optional[str] = None
    photo_url: Optional[str] = None
    college_id: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False
    user: AppUserSchema


class RefreshRequest(BaseModel):
    refresh_token: str

    @field_validator("refresh_token")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("refresh_token cannot be empty")
        return v


class GoogleAuthRequest(BaseModel):
    id_token: str
    college_id: Optional[str] = None

    @field_validator("id_token")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("id_token cannot be empty")
        return v


class SaveUserRequest(BaseModel):
    uid: str
    name: str
    email: str
    role: str
    dept: Optional[str] = None
    batch: Optional[str] = None
    photo_url: Optional[str] = None
    college_id: Optional[str] = None

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"role must be one of {VALID_ROLES}")
        return v

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()


class FcmTokenRequest(BaseModel):
    uid: str
    token: str

    @field_validator("token")
    @classmethod
    def token_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("FCM token cannot be empty")
        return v
