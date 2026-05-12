"""Global error handling middleware."""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from typing import Union, Dict, Any

from backend.api.exceptions import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.

    Provides consistent error responses for all custom exceptions.
    """
    # Log based on severity
    if exc.status_code >= 500:
        logger.error(f"{exc.error_code}: {exc.message}", exc_info=True)
    elif exc.status_code >= 400:
        logger.warning(f"{exc.error_code}: {exc.message}")
    else:
        logger.info(f"{exc.error_code}: {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle uncaught exceptions globally.
    
    Returns a generic error message to avoid leaking internal details.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred. Please try again later.",
            "error_code": "INTERNAL_ERROR"
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle validation errors with detailed error messages.
    """
    errors = []
    
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error")
            })
    else:
        # Pydantic ValidationError
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error")
            })
    
    logger.warning(f"Validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


async def http_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle HTTP exceptions (from fastapi.HTTPException).
    """
    if not isinstance(exc, HTTPException):
        return await global_exception_handler(request, exc)

    # Log 5xx errors
    if exc.status_code >= 500:
        logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    else:
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Handle custom application exceptions (highest priority)
    app.add_exception_handler(AppException, app_exception_handler)

    # Handle validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Handle HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Handle all other uncaught exceptions (lowest priority)
    app.add_exception_handler(Exception, global_exception_handler)

    logger.info("Exception handlers registered")
