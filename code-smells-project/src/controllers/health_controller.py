from flask import jsonify

from src.config.database import get_db


def check():
    cur = get_db().cursor()
    cur.execute("SELECT 1")
    cur.execute("SELECT COUNT(*) FROM produtos")
    produtos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cur.fetchone()[0]
    return jsonify(
        {
            "status": "ok",
            "database": "connected",
            "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            "versao": "1.0.0",
        }
    ), 200


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    ), 200
