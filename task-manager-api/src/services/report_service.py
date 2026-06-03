from datetime import timedelta

from sqlalchemy.orm import joinedload

from src.config.database import db
from src.middlewares.error_handler import NotFoundError
from src.models.category import Category
from src.models.task import Task, _utcnow
from src.models.user import User


def _counts_by(column):
    return {value: count for value, count in db.session.query(column, db.func.count(Task.id)).group_by(column)}


def summary_report():
    now = _utcnow()
    seven_days_ago = now - timedelta(days=7)

    by_status = {s: 0 for s in ("pending", "in_progress", "done", "cancelled")}
    by_status.update(_counts_by(Task.status))
    by_priority_raw = _counts_by(Task.priority)
    by_priority = {
        "critical": by_priority_raw.get(1, 0),
        "high": by_priority_raw.get(2, 0),
        "medium": by_priority_raw.get(3, 0),
        "low": by_priority_raw.get(4, 0),
        "minimal": by_priority_raw.get(5, 0),
    }

    overdue_tasks = (
        Task.query.filter(Task.due_date.isnot(None))
        .filter(Task.due_date < now)
        .filter(~Task.status.in_(("done", "cancelled")))
        .all()
    )
    overdue_list = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "days_overdue": (now - t.due_date).days,
        }
        for t in overdue_tasks
    ]

    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(Task.status == "done", Task.updated_at >= seven_days_ago).count()

    user_rows = (
        db.session.query(
            User.id,
            User.name,
            db.func.count(Task.id).label("total"),
            db.func.sum(db.case((Task.status == "done", 1), else_=0)).label("completed"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
        .all()
    )
    user_stats = []
    for row in user_rows:
        total = row.total or 0
        completed = row.completed or 0
        user_stats.append(
            {
                "user_id": row.id,
                "user_name": row.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round((completed / total) * 100, 2) if total > 0 else 0,
            }
        )

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": db.session.query(Task.id).count(),
            "total_users": db.session.query(User.id).count(),
            "total_categories": db.session.query(Category.id).count(),
        },
        "tasks_by_status": by_status,
        "tasks_by_priority": by_priority,
        "overdue": {"count": len(overdue_list), "tasks": overdue_list},
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    rows = (
        db.session.query(
            db.func.count(Task.id).label("total"),
            db.func.sum(db.case((Task.status == "done", 1), else_=0)).label("done"),
            db.func.sum(db.case((Task.status == "pending", 1), else_=0)).label("pending"),
            db.func.sum(db.case((Task.status == "in_progress", 1), else_=0)).label("in_progress"),
            db.func.sum(db.case((Task.status == "cancelled", 1), else_=0)).label("cancelled"),
            db.func.sum(db.case((Task.priority <= 2, 1), else_=0)).label("high_priority"),
        )
        .filter(Task.user_id == user_id)
        .one()
    )
    now = _utcnow()
    overdue = (
        Task.query.filter(Task.user_id == user_id)
        .filter(Task.due_date.isnot(None))
        .filter(Task.due_date < now)
        .filter(~Task.status.in_(("done", "cancelled")))
        .count()
    )

    total = rows.total or 0
    done = rows.done or 0
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": rows.pending or 0,
            "in_progress": rows.in_progress or 0,
            "cancelled": rows.cancelled or 0,
            "overdue": overdue,
            "high_priority": rows.high_priority or 0,
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        },
    }


def list_categories():
    rows = (
        db.session.query(Category, db.func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .all()
    )
    return [{**cat.to_dict(), "task_count": task_count} for cat, task_count in rows]


def create_category(payload):
    if not payload or not payload.get("name"):
        raise NotFoundError  # handled by caller; raise ValidationError instead
    cat = Category(
        name=payload["name"],
        description=payload.get("description", ""),
        color=payload.get("color", "#000000"),
    )
    db.session.add(cat)
    db.session.commit()
    return cat.to_dict()


def update_category(cat_id, payload):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError("Categoria não encontrada")
    for field in ("name", "description", "color"):
        if field in payload:
            setattr(cat, field, payload[field])
    db.session.commit()
    return cat.to_dict()


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError("Categoria não encontrada")
    db.session.delete(cat)
    db.session.commit()
