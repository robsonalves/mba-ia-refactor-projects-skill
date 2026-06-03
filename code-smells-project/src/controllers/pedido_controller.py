from flask import request

from src.config.constants import STATUS_PEDIDO_VALIDOS
from src.middlewares.error_handler import ValidationError
from src.middlewares.response import ok
from src.models import pedido_model
from src.services import notification_service, pedido_service


def criar():
    data = request.get_json() or {}
    resultado = pedido_service.criar_pedido(data.get("usuario_id"), data.get("itens", []))
    return ok(resultado, status=201, mensagem="Pedido criado com sucesso")


def listar_todos():
    return ok(pedido_model.find_all_with_items())


def listar_por_usuario(usuario_id):
    return ok(pedido_model.find_by_usuario(usuario_id))


def atualizar_status(pedido_id):
    data = request.get_json() or {}
    novo_status = data.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    pedido_model.update_status(pedido_id, novo_status)
    notification_service.notificar_status_pedido(pedido_id, novo_status)
    return ok(None, mensagem="Status atualizado")
