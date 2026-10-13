"""
Kokoro (心) Domain Exceptions
Clean Architecture Domain Layer: Centralized domain errors mapping cleanly to HTTP semantics.
Complies with AGENTS.md Rule "Zero Magic Numbers" & "Error Handling".
"""

from starlette import status


class KokoroDomainError(Exception):
    """Base domain exception for all Kokoro business logic violations."""
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str = "Lỗi xử lý nghiệp vụ 🌸", status_code: int = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class EntryNotFoundError(KokoroDomainError):
    """Raised when an entry does not exist or does not belong to the user."""
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, message_or_id: str | int = "Không tìm thấy bài viết hoặc bạn không có quyền truy cập."):
        if isinstance(message_or_id, int):
            msg = f"Không tìm thấy bài viết #{message_or_id} hoặc bạn không có quyền truy cập."
        else:
            msg = str(message_or_id)
        super().__init__(msg, status.HTTP_404_NOT_FOUND)


class CategoryNotFoundError(KokoroDomainError):
    """Raised when a category does not exist."""
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, message_or_id: str | int = "Không tìm thấy danh mục."):
        if isinstance(message_or_id, int):
            msg = f"Không tìm thấy danh mục #{message_or_id}."
        else:
            msg = str(message_or_id)
        super().__init__(msg, status.HTTP_404_NOT_FOUND)


class CategoryDuplicateError(KokoroDomainError):
    """Raised when attempting to create a category with an already existing name."""
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, name_or_msg: str = "Tên danh mục đã tồn tại."):
        msg = f"Tên danh mục '{name_or_msg}' đã tồn tại 🌸" if not name_or_msg.startswith("Tên danh mục") and not name_or_msg.startswith("Danh mục") else name_or_msg
        super().__init__(msg, status.HTTP_409_CONFLICT)


class TagNotFoundError(KokoroDomainError):
    """Raised when a tag is not found."""
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, tag_or_msg: str = "Không tìm thấy thẻ chủ đề."):
        msg = f"Không tìm thấy thẻ chủ đề '{tag_or_msg}'." if not tag_or_msg.startswith("Không tìm thấy") else tag_or_msg
        super().__init__(msg, status.HTTP_404_NOT_FOUND)


class InvalidInputError(KokoroDomainError):
    """Raised when user input violates validation rules."""
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str = "Dữ liệu nhập vào không hợp lệ."):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class UnauthorizedError(KokoroDomainError):
    """Raised when user is unauthenticated or session expired."""
    status_code: int = status.HTTP_401_UNAUTHORIZED

    def __init__(self, message: str = "Vui lòng đăng nhập để tiếp tục 🌸"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)
