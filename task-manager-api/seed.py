"""Script para popular o banco com dados iniciais."""
from datetime import datetime, timedelta, timezone

from src.app import create_app
from src.config.database import db
from src.models.category import Category
from src.models.task import Task
from src.models.user import User

app = create_app()


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_data():
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = [
            User(name="João Silva", email="joao@email.com", role="admin"),
            User(name="Maria Santos", email="maria@email.com", role="user"),
            User(name="Pedro Oliveira", email="pedro@email.com", role="manager"),
        ]
        seed_passwords = ["1234", "abcd", "pass"]
        for user, pwd in zip(users, seed_passwords):
            user.set_password(pwd)
            db.session.add(user)
        db.session.commit()

        categories = [
            Category(name="Backend", description="Tarefas de backend", color="#3498db"),
            Category(name="Frontend", description="Tarefas de frontend", color="#2ecc71"),
            Category(name="DevOps", description="Tarefas de infraestrutura", color="#e74c3c"),
            Category(name="Bug", description="Correção de bugs", color="#e67e22"),
        ]
        for cat in categories:
            db.session.add(cat)
        db.session.commit()

        u1, u2, u3 = users
        c1, c2, c3, c4 = categories
        now = _utcnow()

        tasks_data = [
            {"title": "Implementar autenticação JWT", "description": "Adicionar autenticação real com JWT", "status": "pending", "priority": 1, "user_id": u1.id, "category_id": c1.id, "due_date": now - timedelta(days=3)},
            {"title": "Criar tela de login", "description": "Tela de login responsiva", "status": "in_progress", "priority": 2, "user_id": u2.id, "category_id": c2.id, "due_date": now + timedelta(days=5)},
            {"title": "Configurar CI/CD", "description": "Pipeline com GitHub Actions", "status": "done", "priority": 2, "user_id": u3.id, "category_id": c3.id, "tags": "devops,ci,github"},
            {"title": "Corrigir bug no filtro de busca", "description": "Filtro não funciona com caracteres especiais", "status": "pending", "priority": 1, "user_id": u1.id, "category_id": c4.id, "due_date": now - timedelta(days=1)},
            {"title": "Adicionar paginação na API", "description": "Endpoints retornam todos os registros", "status": "pending", "priority": 3, "user_id": u1.id, "category_id": c1.id, "due_date": now + timedelta(days=10)},
            {"title": "Escrever testes unitários", "description": "Cobertura mínima de 80%", "status": "pending", "priority": 2, "user_id": u2.id, "category_id": c1.id},
            {"title": "Documentar API com Swagger", "description": "Gerar documentação automática", "status": "cancelled", "priority": 4, "user_id": u3.id, "category_id": c1.id},
            {"title": "Refatorar models", "description": "Melhorar organização dos models", "status": "in_progress", "priority": 3, "user_id": u2.id, "category_id": c1.id, "tags": "refactor,tech-debt"},
            {"title": "Configurar monitoramento", "description": "Prometheus + Grafana", "status": "pending", "priority": 4, "user_id": u3.id, "category_id": c3.id, "due_date": now + timedelta(days=20)},
            {"title": "Melhorar validações de input", "description": "Usar marshmallow ou pydantic", "status": "pending", "priority": 3, "user_id": u1.id, "category_id": c1.id, "tags": "improvement,validation"},
        ]
        for td in tasks_data:
            db.session.add(Task(**td))
        db.session.commit()

        print(f"Seed concluído: {User.query.count()} usuários, {Category.query.count()} categorias, {Task.query.count()} tasks")


if __name__ == "__main__":
    seed_data()
