from fastapi import HTTPException, status


class ClassConnectException(Exception):
    """Base exception for all ClassConnect errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthException(ClassConnectException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class InvalidTokenException(ClassConnectException):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message, "INVALID_TOKEN")


class UserNotFoundException(ClassConnectException):
    def __init__(self, uid: str = ""):
        super().__init__(f"User not found: {uid}", "USER_NOT_FOUND")


class PermissionDeniedException(ClassConnectException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "PERMISSION_DENIED")


# HTTP shortcuts
def raise_401(detail: str = "Unauthorized") -> None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def raise_403(detail: str = "Forbidden") -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

def raise_404(detail: str = "Not found") -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
