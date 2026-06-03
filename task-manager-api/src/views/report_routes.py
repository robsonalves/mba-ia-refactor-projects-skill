from flask import Blueprint, jsonify

from src.controllers import report_controller

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
def summary():
    data, status = report_controller.summary()
    return jsonify(data), status


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id):
    data, status = report_controller.user_summary(user_id)
    return jsonify(data), status


@report_bp.route("/categories", methods=["GET"])
def list_categories():
    data, status = report_controller.list_categories()
    return jsonify(data), status


@report_bp.route("/categories", methods=["POST"])
def create_category():
    data, status = report_controller.create_category()
    return jsonify(data), status


@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    data, status = report_controller.update_category(cat_id)
    return jsonify(data), status


@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    data, status = report_controller.delete_category(cat_id)
    return jsonify(data), status
