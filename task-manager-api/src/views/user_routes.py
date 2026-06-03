from flask import Blueprint, jsonify

from src.controllers import task_controller, user_controller

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def list_users():
    data, status = user_controller.list_all()
    return jsonify(data), status


@user_bp.route("/users", methods=["POST"])
def create_user():
    data, status = user_controller.create()
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    data, status = user_controller.get_one(user_id)
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data, status = user_controller.update(user_id)
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    data, status = user_controller.delete(user_id)
    return jsonify(data), status


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    data, status = task_controller.by_user(user_id)
    return jsonify(data), status


@user_bp.route("/login", methods=["POST"])
def login():
    data, status = user_controller.login()
    return jsonify(data), status
