from flask import request

from src.middlewares.error_handler import NotFoundError, ValidationError
from src.middlewares.response import ok
from src.models import usuario_model


def listar():
    return ok(usuario_model.find_all())


def buscar(usuario_id):
    usuario = usuario_model.find_by_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return ok(usuario)


def criar():
    data = request.get_json() or {}
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    novo_id = usuario_model.insert(nome, email, senha)
    return ok({"id": novo_id}, status=201)
