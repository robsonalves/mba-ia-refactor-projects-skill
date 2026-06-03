from flask import request

from src.middlewares.error_handler import UnauthorizedError, ValidationError
from src.middlewares.response import ok
from src.models import usuario_model


def login():
    data = request.get_json() or {}
    email = data.get("email", "")
    senha = data.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    usuario = usuario_model.authenticate(email, senha)
    if not usuario:
        raise UnauthorizedError("Email ou senha inválidos")
    return ok(usuario, mensagem="Login OK")
