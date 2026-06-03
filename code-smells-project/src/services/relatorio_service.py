from src.models import pedido_model
from src.services.desconto_service import calcular_desconto


def relatorio_vendas():
    metrics = pedido_model.summary_metrics()
    faturamento = metrics["faturamento"]
    desconto = calcular_desconto(faturamento)
    total = metrics["total_pedidos"]
    return {
        "total_pedidos": total,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": desconto,
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": metrics["por_status"].get("pendente", 0),
        "pedidos_aprovados": metrics["por_status"].get("aprovado", 0),
        "pedidos_cancelados": metrics["por_status"].get("cancelado", 0),
        "ticket_medio": round(faturamento / total, 2) if total > 0 else 0,
    }
