# ============================================================
# AETHER LINK - RESPONSE UTILITIES
# ============================================================

from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import status

# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_SUCCESS_MESSAGE = "Success"
DEFAULT_ERROR_MESSAGE = "An error occurred"


# ============================================================
# SUCCESS RESPONSES
# ============================================================

def success_response(
    data: Any = None,
    message: str = DEFAULT_SUCCESS_MESSAGE,
    status_code: int = status.HTTP_200_OK,
    request_id: Optional[str] = None,
    include_timestamp: bool = True,
) -> Dict[str, Any]:
    """
    Standard success response format.
    
    Args:
        data: Response data (can be dict, list, or any serializable object)
        message: Success message
        status_code: HTTP status code
        request_id: Request ID for tracing
        include_timestamp: Include timestamp in response
    
    Returns:
        Standardized success response
    
    Examples:
        >>> success_response({"user": {"id": 1, "name": "John"}})
        {
            "success": True,
            "message": "Success",
            "data": {"user": {"id": 1, "name": "John"}},
            "status_code": 200,
            "timestamp": "2024-01-01T12:00:00"
        }
    """
    response = {
        "success": True,
        "message": message,
        "status_code": status_code,
    }
    
    if data is not None:
        response["data"] = data
    
    if include_timestamp:
        response["timestamp"] = datetime.utcnow().isoformat()
    
    if request_id:
        response["request_id"] = request_id
    
    return response


def created_response(
    data: Any = None,
    message: str = "Created successfully",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 201 Created.
    
    Args:
        data: Created resource data
        message: Success message
        request_id: Request ID for tracing
    
    Returns:
        Standardized 201 response
    """
    return success_response(
        data=data,
        message=message,
        status_code=status.HTTP_201_CREATED,
        request_id=request_id,
    )


def accepted_response(
    data: Any = None,
    message: str = "Accepted",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 202 Accepted.
    
    Args:
        data: Response data
        message: Success message
        request_id: Request ID for tracing
    
    Returns:
        Standardized 202 response
    """
    return success_response(
        data=data,
        message=message,
        status_code=status.HTTP_202_ACCEPTED,
        request_id=request_id,
    )


def no_content_response(
    message: str = "Deleted successfully",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 204 No Content.
    
    Args:
        message: Success message
        request_id: Request ID for tracing
    
    Returns:
        Standardized 204 response
    """
    return success_response(
        data=None,
        message=message,
        status_code=status.HTTP_204_NO_CONTENT,
        request_id=request_id,
    )


# ============================================================
# ERROR RESPONSES
# ============================================================

def error_response(
    message: str = DEFAULT_ERROR_MESSAGE,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Any] = None,
    error_code: Optional[str] = None,
    request_id: Optional[str] = None,
    include_timestamp: bool = True,
) -> Dict[str, Any]:
    """
    Standard error response format.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details (for validation errors)
        error_code: Custom error code
        request_id: Request ID for tracing
        include_timestamp: Include timestamp in response
    
    Returns:
        Standardized error response
    
    Examples:
        >>> error_response("Invalid email format", 400)
        {
            "success": False,
            "error": {
                "code": 400,
                "message": "Invalid email format",
                "timestamp": "2024-01-01T12:00:00"
            }
        }
    """
    error = {
        "code": status_code,
        "message": message,
    }
    
    if include_timestamp:
        error["timestamp"] = datetime.utcnow().isoformat()
    
    if details is not None:
        error["details"] = details
    
    if error_code is not None:
        error["error_code"] = error_code
    
    if request_id is not None:
        error["request_id"] = request_id
    
    return {
        "success": False,
        "error": error,
    }


def validation_error_response(
    errors: List[Dict[str, Any]],
    message: str = "Validation error",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for validation errors (422).
    
    Args:
        errors: List of validation errors
        message: Error message
        request_id: Request ID for tracing
    
    Returns:
        Standardized 422 response
    
    Examples:
        >>> validation_error_response([
        ...     {"field": "email", "message": "Invalid email format"},
        ...     {"field": "password", "message": "Password too weak"}
        ... ])
        {
            "success": False,
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": [
                    {"field": "email", "message": "Invalid email format"},
                    {"field": "password", "message": "Password too weak"}
                ]
            }
        }
    """
    return error_response(
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=errors,
        request_id=request_id,
    )


def not_found_response(
    resource: str = "Resource",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 404 Not Found.
    
    Args:
        resource: Type of resource not found
        request_id: Request ID for tracing
    
    Returns:
        Standardized 404 response
    
    Examples:
        >>> not_found_response("User")
        {
            "success": False,
            "error": {
                "code": 404,
                "message": "User not found"
            }
        }
    """
    return error_response(
        message=f"{resource} not found",
        status_code=status.HTTP_404_NOT_FOUND,
        request_id=request_id,
    )


def unauthorized_response(
    message: str = "Unauthorized",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 401 Unauthorized.
    
    Args:
        message: Error message
        request_id: Request ID for tracing
    
    Returns:
        Standardized 401 response
    """
    return error_response(
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
        request_id=request_id,
    )


def forbidden_response(
    message: str = "Forbidden",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 403 Forbidden.
    
    Args:
        message: Error message
        request_id: Request ID for tracing
    
    Returns:
        Standardized 403 response
    """
    return error_response(
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
        request_id=request_id,
    )


def rate_limit_response(
    message: str = "Rate limit exceeded. Please try again later.",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 429 Too Many Requests.
    
    Args:
        message: Error message
        request_id: Request ID for tracing
    
    Returns:
        Standardized 429 response
    """
    return error_response(
        message=message,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        request_id=request_id,
    )


def server_error_response(
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Response for 500 Internal Server Error.
    
    Args:
        request_id: Request ID for tracing
    
    Returns:
        Standardized 500 response
    """
    return error_response(
        message="Internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


# ============================================================
# PAGINATED RESPONSES
# ============================================================

def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = DEFAULT_SUCCESS_MESSAGE,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Standard paginated response format.
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Items per page
        message: Success message
        request_id: Request ID for tracing
    
    Returns:
        Standardized paginated response
    
    Examples:
        >>> paginated_response([{"id": 1}, {"id": 2}], 10, 1, 20)
        {
            "success": True,
            "message": "Success",
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {
                "total": 10,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False
            },
            "timestamp": "2024-01-01T12:00:00"
        }
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    response = {
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if request_id:
        response["request_id"] = request_id
    
    return response


# ============================================================
# JSON RESPONSE HELPERS (For FastAPI endpoints)
# ============================================================

def json_success(
    data: Any = None,
    message: str = DEFAULT_SUCCESS_MESSAGE,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """
    FastAPI JSONResponse for success.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
    
    Returns:
        JSONResponse with success format
    """
    content = success_response(data=data, message=message, status_code=status_code)
    return JSONResponse(content=content, status_code=status_code)


def json_error(
    message: str = DEFAULT_ERROR_MESSAGE,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Any] = None,
) -> JSONResponse:
    """
    FastAPI JSONResponse for error.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        JSONResponse with error format
    """
    content = error_response(message=message, status_code=status_code, details=details)
    return JSONResponse(content=content, status_code=status_code)


def json_paginated(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = DEFAULT_SUCCESS_MESSAGE,
) -> JSONResponse:
    """
    FastAPI JSONResponse for paginated results.
    
    Args:
        items: List of items
        total: Total count
        page: Current page
        page_size: Items per page
        message: Success message
    
    Returns:
        JSONResponse with paginated format
    """
    content = paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        message=message,
    )
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Success responses
    'success_response',
    'created_response',
    'accepted_response',
    'no_content_response',
    
    # Error responses
    'error_response',
    'validation_error_response',
    'not_found_response',
    'unauthorized_response',
    'forbidden_response',
    'rate_limit_response',
    'server_error_response',
    
    # Paginated response
    'paginated_response',
    
    # FastAPI JSON helpers
    'json_success',
    'json_error',
    'json_paginated',
]