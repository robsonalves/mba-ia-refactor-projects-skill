from src.middlewares.response import ok
from src.services.relatorio_service import relatorio_vendas


def vendas():
    return ok(relatorio_vendas())
