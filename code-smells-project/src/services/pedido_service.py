from src.middlewares.error_handler import ValidationError
from src.models import pedido_model
from src.config.database import get_db
from src.services import notification_service


def criar_pedido(usuario_id, itens):
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    db = get_db()
    cur = db.cursor()
    total = 0.0
    itens_validados = []
    for item in itens:
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if not produto_id or not quantidade:
            raise ValidationError("Item inválido: produto_id e quantidade são obrigatórios")
        cur.execute("SELECT nome, preco, estoque FROM produtos WHERE id = ?", (produto_id,))
        produto = cur.fetchone()
        if produto is None:
            raise ValidationError(f"Produto {produto_id} não encontrado")
        if produto["estoque"] < quantidade:
            raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * quantidade
        itens_validados.append(
            {
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": produto["preco"],
            }
        )

    pedido_id = pedido_model.create_with_items(usuario_id, itens_validados, total)
    notification_service.notificar_pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}
