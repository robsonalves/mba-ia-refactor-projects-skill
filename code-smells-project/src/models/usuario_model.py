from werkzeug.security import check_password_hash, generate_password_hash

from src.config.database import get_db


def _public_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def find_all():
    cur = get_db().cursor()
    cur.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_public_dict(r) for r in cur.fetchall()]


def find_by_id(usuario_id):
    cur = get_db().cursor()
    cur.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (usuario_id,))
    row = cur.fetchone()
    return _public_dict(row) if row else None


def insert(nome, email, senha, tipo="cliente"):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    db.commit()
    return cur.lastrowid


def authenticate(email, senha):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cur.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return _public_dict(row)
    return None
