from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Any = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

class NotFound(AppError):
    def __init__(self, message: str = "Data tidak ditemukan"):
        super().__init__(code="NOT_FOUND", message=message, status_code=404)

class Forbidden(AppError):
    def __init__(self, message: str = "Akses ditolak"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)

class Unauthorized(AppError):
    def __init__(self, code: str = "UNAUTHORIZED", message: str = "Tidak ada akses", details: Any = None):
        super().__init__(code=code, message=message, status_code=401, details=details)

class Conflict(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code=code, message=message, status_code=409)

class InvalidTransition(AppError):
    def __init__(self, state: str, event: str):
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message="Transisi status tidak valid",
            status_code=409,
            details={"state": state, "event": event}
        )

class ValidationFailed(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code=code, message=message, status_code=422)

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": "Validasi gagal", "details": exc.errors()}}
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        codes = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED"
        }
        code = codes.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": str(exc.detail), "details": None}}
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "CONFLICT", "message": "Konflik data", "details": None}}
        )
