from src.config.database import db
from src.middlewares.error_handler import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
)
from src.models.task import Task
from src.models.user import User
from src.schemas.user_schema import login_schema, user_create_schema, user_update_schema


def list_users():
    pairs = (
        db.session.query(User, db.func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .all()
    )
    return [{**user.to_public_dict(), "task_count": task_count} for user, task_count in pairs]


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    data = user.to_public_dict()
    data["tasks"] = [t.to_dict(include_overdue=True) for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(payload):
    data = user_create_schema.load(payload or {})
    if User.query.filter_by(email=data["email"]).first():
        raise ConflictError("Email já cadastrado")
    user = User(name=data["name"], email=data["email"], role=data.get("role", "user"))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return user.to_public_dict()


def update_user(user_id, payload):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    data = user_update_schema.load(payload or {})
    if "email" in data and data["email"] != user.email:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            raise ConflictError("Email já cadastrado")
        user.email = data["email"]
    for field in ("name", "role", "active"):
        if field in data:
            setattr(user, field, data[field])
    if "password" in data:
        user.set_password(data["password"])
    db.session.commit()
    return user.to_public_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()


def login(payload):
    data = login_schema.load(payload or {})
    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        raise UnauthorizedError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")
    return {
        "message": "Login realizado com sucesso",
        "user": user.to_public_dict(),
        "auth_note": "auth ainda não implementada — endpoint retorna usuário, mas não emite token de sessão",
    }
