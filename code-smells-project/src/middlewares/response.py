from flask import jsonify


def ok(dados=None, status=200, **extra):
    body = {"dados": dados, "sucesso": True}
    body.update(extra)
    return jsonify(body), status


def err(message, status=400):
    return jsonify({"erro": message, "sucesso": False}), status
