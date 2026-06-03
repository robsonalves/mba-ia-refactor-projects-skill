import logging

from werkzeug.exceptions import HTTPException

from src.middlewares.response import err

logger = logging.getLogger(__name__)


class DomainError(Exception):
    status = 400


class NotFoundError(DomainError):
    status = 404


class ValidationError(DomainError):
    status = 400


class ConflictError(DomainError):
    status = 409


class UnauthorizedError(DomainError):
    status = 401


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def _domain(e):
        return err(str(e), status=e.status)

    @app.errorhandler(HTTPException)
    def _http(e):
        return err(e.description, status=e.code or 500)

    @app.errorhandler(Exception)
    def _generic(e):
        logger.exception("Unhandled exception")
        return err("Erro interno do servidor", status=500)
