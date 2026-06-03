import logging

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("notificacao.email pedido=%s usuario=%s", pedido_id, usuario_id)
    logger.info("notificacao.sms pedido=%s usuario=%s", pedido_id, usuario_id)
    logger.info("notificacao.push pedido=%s", pedido_id)


def notificar_status_pedido(pedido_id, novo_status):
    logger.info("notificacao.status pedido=%s status=%s", pedido_id, novo_status)
