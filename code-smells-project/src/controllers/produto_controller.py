from flask import request

from src.config.constants import CATEGORIAS_VALIDAS, PRODUTO_NOME_MAX, PRODUTO_NOME_MIN
from src.middlewares.error_handler import NotFoundError, ValidationError
from src.middlewares.response import ok
from src.models import produto_model


def _validate_payload(data, partial=False):
    if not data:
        raise ValidationError("Dados inválidos")

    if not partial or "nome" in data:
        nome = data.get("nome")
        if not nome:
            raise ValidationError("Nome é obrigatório")
        if not (PRODUTO_NOME_MIN <= len(nome) <= PRODUTO_NOME_MAX):
            raise ValidationError(
                f"Nome deve ter entre {PRODUTO_NOME_MIN} e {PRODUTO_NOME_MAX} caracteres"
            )
    if not partial or "preco" in data:
        preco = data.get("preco")
        if preco is None:
            raise ValidationError("Preço é obrigatório")
        if preco < 0:
            raise ValidationError("Preço não pode ser negativo")
    if not partial or "estoque" in data:
        estoque = data.get("estoque")
        if estoque is None:
            raise ValidationError("Estoque é obrigatório")
        if estoque < 0:
            raise ValidationError("Estoque não pode ser negativo")

    categoria = data.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")


def listar():
    return ok(produto_model.find_all())


def buscar(produto_id):
    produto = produto_model.find_by_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return ok(produto)


def criar():
    data = request.get_json()
    _validate_payload(data)
    novo_id = produto_model.insert(
        data["nome"],
        data.get("descricao", ""),
        data["preco"],
        data["estoque"],
        data.get("categoria", "geral"),
    )
    return ok({"id": novo_id}, status=201, mensagem="Produto criado")


def atualizar(produto_id):
    if produto_model.find_by_id(produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    data = request.get_json()
    _validate_payload(data)
    produto_model.update(
        produto_id,
        data["nome"],
        data.get("descricao", ""),
        data["preco"],
        data["estoque"],
        data.get("categoria", "geral"),
    )
    return ok(None, mensagem="Produto atualizado")


def deletar(produto_id):
    if produto_model.find_by_id(produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    produto_model.delete(produto_id)
    return ok(None, mensagem="Produto deletado")


def buscar_lista():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")
    if preco_min is not None:
        preco_min = float(preco_min)
    if preco_max is not None:
        preco_max = float(preco_max)
    resultados = produto_model.search(termo, categoria, preco_min, preco_max)
    return ok(resultados, total=len(resultados))
