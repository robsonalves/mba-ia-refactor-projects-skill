import logging

from flask import jsonify
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException

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


class ForbiddenError(DomainError):
    status = 403


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def _domain(e):
        return jsonify({"error": str(e)}), e.status

    @app.errorhandler(MarshmallowValidationError)
    def _marshmallow(e):
        return jsonify({"error": e.messages}), 400

    @app.errorhandler(HTTPException)
    def _http(e):
        return jsonify({"error": e.description}), e.code or 500

    @app.errorhandler(Exception)
    def _generic(e):
        logger.exception("Unhandled exception")
        return jsonify({"error": "Erro interno do servidor"}), 500
