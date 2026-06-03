from flask import request

from src.services import user_service


def list_all():
    return user_service.list_users(), 200


def get_one(user_id):
    return user_service.get_user(user_id), 200


def create():
    return user_service.create_user(request.get_json()), 201


def update(user_id):
    return user_service.update_user(user_id, request.get_json()), 200


def delete(user_id):
    user_service.delete_user(user_id)
    return {"message": "Usuário deletado com sucesso"}, 200


def login():
    return user_service.login(request.get_json()), 200
