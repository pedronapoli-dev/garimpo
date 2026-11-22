from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel

from app.routers import assist, auth, invites, recommendations, tags, users, votes
from app.schemas import ErrorOut
from app.services.exceptions import (
    AlreadyReported,
    AssistDisabled,
    DomainError,
    DuplicateRecommendation,
    EmailTaken,
    InvalidCredentials,
    InvalidCursor,
    InvalidInvite,
    InvalidRecommendation,
    NotAuthenticated,
    NotAuthor,
    OwnRecommendation,
    RecommendationNotFound,
    UserNotFound,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotAuthenticated: status.HTTP_401_UNAUTHORIZED,
    InvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    NotAuthor: status.HTTP_403_FORBIDDEN,
    OwnRecommendation: status.HTTP_403_FORBIDDEN,
    UserNotFound: status.HTTP_404_NOT_FOUND,
    RecommendationNotFound: status.HTTP_404_NOT_FOUND,
    DuplicateRecommendation: status.HTTP_409_CONFLICT,
    EmailTaken: status.HTTP_409_CONFLICT,
    AlreadyReported: status.HTTP_409_CONFLICT,
    InvalidCursor: 422,
    InvalidRecommendation: 422,
    InvalidInvite: 422,
    AssistDisabled: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def camel_case_operation_id(route: APIRoute) -> str:
    """create_recommendation -> createRecommendation, used by the app's types."""
    first, *rest = route.name.split("_")
    return first + "".join(word.capitalize() for word in rest)


def error_response(status_code: int, error: ErrorOut) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content=error.model_dump(exclude_none=True)
    )


def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    error = ErrorOut(code=exc.code, message=exc.message, existing_id=exc.existing_id)
    return error_response(STATUS_BY_ERROR[type(exc)], error)


def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    ]
    error = ErrorOut(code="validation_error", message="; ".join(details))
    return error_response(422, error)


app = FastAPI(title="Garimpo", generate_unique_id_function=camel_case_operation_id)
app.add_exception_handler(DomainError, handle_domain_error)
app.add_exception_handler(RequestValidationError, handle_validation_error)
app.include_router(auth.router)
app.include_router(invites.router)
app.include_router(recommendations.router)
app.include_router(votes.router)
app.include_router(tags.router)
app.include_router(users.router)
app.include_router(assist.router)


class Health(BaseModel):
    status: str


@app.get("/health")
def health() -> Health:
    return Health(status="ok")
