from src.config.database import get_db


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def find_all():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM produtos")
    return [_row_to_dict(r) for r in cur.fetchall()]


def find_by_id(produto_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cur.fetchone()
    return _row_to_dict(row) if row else None


def insert(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cur.lastrowid


def update(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def delete(produto_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def search(termo=None, categoria=None, preco_min=None, preco_max=None):
    sql = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        sql += " AND (nome LIKE ? OR descricao LIKE ?)"
        like = f"%{termo}%"
        params.extend([like, like])
    if categoria:
        sql += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        sql += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        sql += " AND preco <= ?"
        params.append(preco_max)
    cur = get_db().cursor()
    cur.execute(sql, params)
    return [_row_to_dict(r) for r in cur.fetchall()]
