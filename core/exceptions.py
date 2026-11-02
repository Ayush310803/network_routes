from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, code: str):
        self.status_code = status_code
        self.message = message
        self.code = code


def error_response(status_code: int, message: str, code: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message, "code": code})


async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status_code, exc.message, exc.code)


# The spec lists 400 for missing or invalid fields, so FastAPI's default 422 is replaced.
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    error = exc.errors()[0]
    field = ".".join(str(part) for part in error["loc"] if part not in ("body", "query", "path"))
    message = f"{field}: {error['msg']}" if field else error["msg"]
    return error_response(400, message, "VALIDATION_ERROR")


async def handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return error_response(exc.status_code, str(exc.detail), "HTTP_ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(HTTPException, handle_http_error)
