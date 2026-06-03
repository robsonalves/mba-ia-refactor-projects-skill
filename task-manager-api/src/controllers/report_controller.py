from flask import request

from src.middlewares.error_handler import ValidationError
from src.services import report_service


def summary():
    return report_service.summary_report(), 200


def user_summary(user_id):
    return report_service.user_report(user_id), 200


def list_categories():
    return report_service.list_categories(), 200


def create_category():
    payload = request.get_json() or {}
    if not payload.get("name"):
        raise ValidationError("Nome é obrigatório")
    return report_service.create_category(payload), 201


def update_category(cat_id):
    return report_service.update_category(cat_id, request.get_json() or {}), 200


def delete_category(cat_id):
    report_service.delete_category(cat_id)
    return {"message": "Categoria deletada"}, 200
