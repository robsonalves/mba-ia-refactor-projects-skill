from flask import request

from src.services import task_service


def list_all():
    return task_service.list_tasks(), 200


def get_one(task_id):
    return task_service.get_task(task_id), 200


def create():
    return task_service.create_task(request.get_json()), 201


def update(task_id):
    return task_service.update_task(task_id, request.get_json()), 200


def delete(task_id):
    task_service.delete_task(task_id)
    return {"message": "Task deletada com sucesso"}, 200


def search():
    return task_service.search_tasks(
        request.args.get("q", ""),
        request.args.get("status", ""),
        request.args.get("priority", ""),
        request.args.get("user_id", ""),
    ), 200


def stats():
    return task_service.task_stats(), 200


def by_user(user_id):
    return task_service.get_user_tasks(user_id), 200
