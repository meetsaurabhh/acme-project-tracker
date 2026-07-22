"""Application level errors.

Services raise these instead of HTTPException, so the business layer stays
independent of FastAPI. The API layer translates them into HTTP responses.
"""


class AppError(Exception):
    """Base class for every error this application raises deliberately."""

    status_code: int = 400
    message: str = "The request could not be completed."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError):
    """The requested record does not exist."""

    status_code = 404
    message = "The requested record was not found."


class ConflictError(AppError):
    """The request clashes with data that already exists."""

    status_code = 409
    message = "That record already exists."


class ValidationError(AppError):
    """The request is well formed but breaks a business rule."""

    status_code = 400
    message = "The submitted values are not valid."


class AuthenticationError(AppError):
    """The caller could not be identified."""

    status_code = 401
    message = "Sign in again - your session is not valid."


class AuthorizationError(AppError):
    """The caller is known but not allowed to do this."""

    status_code = 403
    message = "Your role does not permit this action."
