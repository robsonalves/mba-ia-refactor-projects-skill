from flask import Blueprint, jsonify

from src.controllers import task_controller

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
def list_tasks():
    data, status = task_controller.list_all()
    return jsonify(data), status


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    data, status = task_controller.create()
    return jsonify(data), status


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    data, status = task_controller.get_one(task_id)
    return jsonify(data), status


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data, status = task_controller.update(task_id)
    return jsonify(data), status


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    data, status = task_controller.delete(task_id)
    return jsonify(data), status


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    data, status = task_controller.search()
    return jsonify(data), status


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    data, status = task_controller.stats()
    return jsonify(data), status
