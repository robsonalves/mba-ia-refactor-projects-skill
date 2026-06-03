from src.config.database import get_db


def _build_pedidos_with_items(rows):
    pedidos_map = {}
    for r in rows:
        pid = r["pedido_id"]
        if pid not in pedidos_map:
            pedidos_map[pid] = {
                "id": pid,
                "usuario_id": r["usuario_id"],
                "status": r["status"],
                "total": r["total"],
                "criado_em": r["criado_em"],
                "itens": [],
            }
        if r["produto_id"] is not None:
            pedidos_map[pid]["itens"].append(
                {
                    "produto_id": r["produto_id"],
                    "produto_nome": r["produto_nome"] or "Desconhecido",
                    "quantidade": r["quantidade"],
                    "preco_unitario": r["preco_unitario"],
                }
            )
    return list(pedidos_map.values())


_JOIN_SQL = """
    SELECT
        p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
        i.produto_id, i.quantidade, i.preco_unitario,
        prod.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos prod ON prod.id = i.produto_id
"""


def find_all_with_items():
    cur = get_db().cursor()
    cur.execute(_JOIN_SQL + " ORDER BY p.id")
    return _build_pedidos_with_items(cur.fetchall())


def find_by_usuario(usuario_id):
    cur = get_db().cursor()
    cur.execute(_JOIN_SQL + " WHERE p.usuario_id = ? ORDER BY p.id", (usuario_id,))
    return _build_pedidos_with_items(cur.fetchall())


def create_with_items(usuario_id, itens_validados, total):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cur.lastrowid
    for item in itens_validados:
        cur.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )
        cur.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )
    db.commit()
    return pedido_id


def update_status(pedido_id, novo_status):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def summary_metrics():
    cur = get_db().cursor()
    cur.execute("SELECT COUNT(*) FROM pedidos")
    total = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento = cur.fetchone()[0] or 0
    cur.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status")
    por_status = {row[0]: row[1] for row in cur.fetchall()}
    return {
        "total_pedidos": total,
        "faturamento": faturamento,
        "por_status": por_status,
    }
