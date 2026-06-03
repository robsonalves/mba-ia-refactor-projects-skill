from sqlalchemy.orm import joinedload

from src.config.database import db
from src.middlewares.error_handler import NotFoundError
from src.models.category import Category
from src.models.task import Task, _utcnow
from src.models.user import User
from src.schemas.task_schema import (
    normalize_tags,
    parse_due_date,
    task_create_schema,
    task_update_schema,
)


def _apply_payload(task, data):
    for field in ("title", "description", "status", "priority", "user_id", "category_id"):
        if field in data:
            setattr(task, field, data[field])
    if "due_date" in data:
        task.due_date = parse_due_date(data["due_date"])
    if "tags" in data:
        task.tags = normalize_tags(data["tags"])


def _validate_relations(data):
    if data.get("user_id") is not None:
        if not db.session.get(User, data["user_id"]):
            raise NotFoundError("Usuário não encontrado")
    if data.get("category_id") is not None:
        if not db.session.get(Category, data["category_id"]):
            raise NotFoundError("Categoria não encontrada")


def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    return [t.to_dict(include_overdue=True, include_relations=True) for t in tasks]


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    return task.to_dict(include_overdue=True)


def create_task(payload):
    data = task_create_schema.load(payload or {})
    _validate_relations(data)
    task = Task()
    _apply_payload(task, data)
    db.session.add(task)
    db.session.commit()
    return task.to_dict(include_overdue=True)


def update_task(task_id, payload):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    data = task_update_schema.load(payload or {})
    _validate_relations(data)
    _apply_payload(task, data)
    task.updated_at = _utcnow()
    db.session.commit()
    return task.to_dict(include_overdue=True)


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    db.session.delete(task)
    db.session.commit()


def search_tasks(query, status, priority, user_id):
    q = Task.query
    if query:
        like = f"%{query}%"
        q = q.filter(db.or_(Task.title.like(like), Task.description.like(like)))
    if status:
        q = q.filter(Task.status == status)
    if priority:
        try:
            q = q.filter(Task.priority == int(priority))
        except (TypeError, ValueError):
            pass
    if user_id:
        try:
            q = q.filter(Task.user_id == int(user_id))
        except (TypeError, ValueError):
            pass
    return [t.to_dict(include_overdue=True) for t in q.all()]


def task_stats():
    now = _utcnow()
    total = db.session.query(Task.id).count()
    by_status = {s: 0 for s in ("pending", "in_progress", "done", "cancelled")}
    for status, count in db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status):
        by_status[status] = count
    overdue = (
        db.session.query(Task.id)
        .filter(Task.due_date.isnot(None))
        .filter(Task.due_date < now)
        .filter(~Task.status.in_(("done", "cancelled")))
        .count()
    )
    done = by_status["done"]
    return {
        "total": total,
        "pending": by_status["pending"],
        "in_progress": by_status["in_progress"],
        "done": done,
        "cancelled": by_status["cancelled"],
        "overdue": overdue,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    tasks = Task.query.filter_by(user_id=user_id).all()
    return [t.to_dict(include_overdue=True) for t in tasks]
