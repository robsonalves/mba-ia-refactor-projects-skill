# 05 — Playbook de Refatoração

Padrões concretos de transformação. Cada entrada (`RP-NNN`) tem:
- **Aplica-se a:** qual anti-pattern do catálogo (`AP-NNN`)
- **Antes:** snippet do problema
- **Depois:** snippet da solução
- **Notas:** edge cases, ordem de operações

> **Cobertura mínima:** ≥8 transformações com exemplos antes/depois. Quando for executar a Fase 3, leia a entrada correspondente ao finding e aplique o padrão literalmente, adaptando apenas nomes do domínio.

---

## RP-001 — Queries parametrizadas (resolve AP-001 SQL Injection)

**Antes (Python + sqlite3):**
```python
def login_usuario(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
    )
```

**Depois:**
```python
def login_usuario(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha)
    )
```

**Antes (Node.js + sqlite3):**
```javascript
db.run(`SELECT * FROM users WHERE id = ${userId}`, callback);
```

**Depois:**
```javascript
db.run("SELECT * FROM users WHERE id = ?", [userId], callback);
```

**Notas:**
- Para `IN (...)` dinâmico: gere placeholders `?,?,?` programaticamente, não interpole.
- Para `LIKE`: passe o `%` no parâmetro, não no SQL — `("%" + termo + "%",)`.
- `ORDER BY` não aceita placeholder em alguns drivers — use whitelist de colunas válidas antes de interpolar.

---

## RP-002 — Secrets via env (resolve AP-002 credenciais hardcoded)

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Depois:**
```python
# src/config/settings.py
import os

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não definida no ambiente")
```

```python
# src/app.py
from config.settings import SECRET_KEY
app.config["SECRET_KEY"] = SECRET_KEY
```

**Adicione `.env.example` na raiz do projeto:**
```bash
# .env.example
SECRET_KEY=
DATABASE_URL=sqlite:///app.db
DEBUG=false
```

**Notas:**
- Nunca deixe valor default para `SECRET_KEY`. Falhar no boot é melhor que rodar com chave fraca.
- Em CI, leia de secret manager (GitHub Actions secrets, AWS Secrets Manager, Vault).
- Para Node: use `dotenv` (`require('dotenv').config()`) ou variáveis nativas do shell.

---

## RP-003 — Quebrar god class (resolve AP-003)

**Antes:** `controllers.py` com 17 handlers de 5 domínios.

**Depois:**
```
src/controllers/
├── produto_controller.py      # 5 handlers (CRUD + busca)
├── usuario_controller.py      # 3 handlers (CRUD)
├── pedido_controller.py       # 4 handlers (CRUD + status)
├── login_controller.py        # 1 handler
└── relatorio_controller.py    # 1 handler
```

**Estratégia de migração (ordem importa):**

1. Liste todos os handlers no arquivo monolítico.
2. Agrupe por domínio (use o prefixo da URL ou o nome da função como pista: `criar_produto`, `listar_produtos` → `produto_controller`).
3. Crie um arquivo por domínio em `src/controllers/`.
4. Mova as funções **uma de cada vez**, ajustando imports.
5. Para cada handler movido, atualize o registro em `src/views/routes.py`.
6. Rode `python -c "from src.app import create_app; create_app()"` para garantir que importações ainda funcionam.
7. Quando todos os handlers tiverem migrado, delete o `controllers.py` original.

**Notas:**
- Não esqueça de mover funções auxiliares que só servem a um domínio.
- Funções auxiliares compartilhadas vão para `src/services/` ou `src/utils/`.

---

## RP-004 — Hash de senha seguro (resolve AP-004)

**Antes (Python — MD5 sem salt):**
```python
import hashlib

def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

**Depois (usando `werkzeug.security`, já vem com Flask):**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

**Antes (Node.js — base64 fake):**
```javascript
function badCrypto(pwd) {
    return Buffer.from(pwd).toString('base64').substring(0, 10);
}
```

**Depois (usando `bcrypt`, npm package padrão):**
```javascript
const bcrypt = require('bcrypt');

async function hashPassword(pwd) {
    return bcrypt.hash(pwd, 10);
}

async function verifyPassword(pwd, hash) {
    return bcrypt.compare(pwd, hash);
}
```

**Remoção obrigatória:** tire `password` de qualquer `to_dict()`, serializer ou resposta de API.

**Notas:**
- Migração de senhas legadas: ao próximo login bem-sucedido, regere o hash com algoritmo novo e salve. Não exija reset universal a menos que o vazamento já tenha acontecido.
- `werkzeug.security` usa PBKDF2 por padrão. Configurável para `scrypt`/`argon2`.

---

## RP-005 — Remover endpoint de SQL/eval arbitrário (resolve AP-005)

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)
    return jsonify(cursor.fetchall()), 200
```

**Depois:**
```python
# Endpoint removido por completo.
# Operações administrativas legítimas (reset de dados, migração) ficam atrás de:
#   - autenticação obrigatória + RBAC (role=admin)
#   - audit log de cada chamada
#   - escopo restrito a operações específicas, nunca SQL livre
```

**Se o endpoint for indispensável** (raríssimo), exponha operações específicas:

```python
@admin_bp.route("/admin/reset", methods=["POST"])
@require_admin
def reset_data():
    audit_log.write(f"admin reset by {current_user.id}")
    db.execute("DELETE FROM ...")
    return jsonify({"status": "ok"}), 200
```

**Notas:**
- Confirmar com humano antes de remover, mesmo na Fase 3 — pode haver consumidor interno desconhecido.

---

## RP-006 — Conexão de DB segura por thread/request (resolve AP-006)

**Antes (Python — singleton global):**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

**Depois (Flask `g` por-request):**
```python
from flask import g
import sqlite3

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(settings.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

**Antes (Node.js — `:memory:` em prod):**
```javascript
this.db = new sqlite3.Database(':memory:');
```

**Depois (path persistente via config):**
```javascript
const { config } = require('./config');
this.db = new sqlite3.Database(config.dbPath);
```

**Notas:**
- Para SQLite em produção real, considere migrar para Postgres (sqlite não suporta múltiplos writers concorrentes bem).
- Em Node assíncrono, prefira `better-sqlite3` ou um pool (`pg.Pool`).

---

## RP-007 — Não logar dados sensíveis (resolve AP-007)

**Antes:**
```javascript
console.log(`Processando cartão ${cardNumber} na chave ${paymentKey}`);
```

**Depois:**
```javascript
console.log(`Processando cartão ****${cardNumber.slice(-4)}`);
// chave de pagamento nunca aparece em log
```

**Antes (endpoint `/health` vazando secret):**
```python
return jsonify({
    "status": "ok",
    "secret_key": "minha-chave-super-secreta-123",
    "debug": True,
    "db_path": "loja.db"
}), 200
```

**Depois:**
```python
return jsonify({
    "status": "ok",
    "database": "connected",
    "version": settings.APP_VERSION
}), 200
```

**Notas:**
- Mantenha lista negra de campos: `password`, `pass`, `pwd`, `token`, `secret`, `card`, `cvv`, `ssn`, `cpf`.
- Adicione middleware/filter que redatasse logs (lib `pino-redact` para Node, `structlog` com processador custom para Python).

---

## RP-008 — Eliminar N+1 (resolve AP-008)

**Antes (loop disparando query por iteração):**
```python
def get_pedidos_usuario(usuario_id):
    pedidos = cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    result = []
    for pedido in pedidos:
        itens = cursor.execute("SELECT * FROM itens WHERE pedido_id = ?", (pedido["id"],)).fetchall()
        for item in itens:
            produto = cursor.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
            # ...
```

**Depois (1 JOIN):**
```python
def get_pedidos_usuario(usuario_id):
    rows = cursor.execute("""
        SELECT p.id AS pedido_id, p.status, p.total, p.criado_em,
               i.produto_id, i.quantidade, i.preco_unitario,
               prod.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos prod ON prod.id = i.produto_id
        WHERE p.usuario_id = ?
        ORDER BY p.id
    """, (usuario_id,)).fetchall()
    return agrupar_por_pedido(rows)
```

**Depois (SQLAlchemy + joinedload):**
```python
from sqlalchemy.orm import joinedload

pedidos = Pedido.query.options(
    joinedload(Pedido.itens).joinedload(ItemPedido.produto)
).filter_by(usuario_id=usuario_id).all()
```

**Depois (Node + Promise.all):**
```javascript
async function getFinancialReport() {
    const courses = await db.all("SELECT * FROM courses");
    const reports = await Promise.all(courses.map(async c => {
        const data = await db.all(`
            SELECT u.name, p.amount, p.status
            FROM enrollments e
            JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            WHERE e.course_id = ?
        `, [c.id]);
        return { course: c.title, students: data };
    }));
    return reports;
}
```

**Notas:**
- Para 1 query, ferramentas como `EXPLAIN ANALYZE` confirmam o ganho.
- Em ORM, `selectinload` (1+N queries em batch) é alternativa quando JOIN gera linhas demais.

---

## RP-009 — Extrair lógica de negócio para services (resolve AP-009)

**Antes (controller com regra de desconto):**
```python
def relatorio_vendas():
    # ... busca dados ...
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02
    return jsonify({"desconto": desconto, ...})
```

**Depois (service isolado):**
```python
# src/services/desconto_service.py
TIERS = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]

def calcular_desconto(faturamento: float) -> float:
    for limite, taxa in TIERS:
        if faturamento > limite:
            return round(faturamento * taxa, 2)
    return 0.0
```

```python
# src/controllers/relatorio_controller.py
from services import desconto_service

def relatorio_vendas():
    dados = relatorio_service.gerar(get_db())
    dados["desconto"] = desconto_service.calcular_desconto(dados["faturamento"])
    return jsonify({"data": dados}), 200
```

**Ganho:** `desconto_service.calcular_desconto` agora é testável isoladamente. Mudar tier vira 1 linha em `TIERS`, não 1 if-else aninhado.

---

## RP-010 — Transação atômica em operação multi-step (resolve AP-010)

**Antes (Node — sequência de callbacks sem transação):**
```javascript
db.run("INSERT INTO users (...) VALUES (...)", [...], (err) => {
    db.run("INSERT INTO enrollments (...) VALUES (...)", [...], (err) => {
        db.run("INSERT INTO payments (...) VALUES (...)", [...], (err) => {
            // se este último falhar, user+enrollment ficam órfãos
        });
    });
});
```

**Depois (Node — sqlite3 com BEGIN/COMMIT):**
```javascript
async function checkout(userData, courseId, cardData) {
    await db.run("BEGIN TRANSACTION");
    try {
        const { lastID: userId } = await db.run("INSERT INTO users (...) VALUES (...)", userData);
        const { lastID: enrId } = await db.run("INSERT INTO enrollments (...) VALUES (...)", [userId, courseId]);
        await db.run("INSERT INTO payments (...) VALUES (...)", [enrId, ...]);
        await db.run("COMMIT");
        return { userId, enrollmentId: enrId };
    } catch (err) {
        await db.run("ROLLBACK");
        throw err;
    }
}
```

**Depois (Python — SQLAlchemy):**
```python
def criar_pedido_completo(usuario_id, itens):
    with db.session.begin():  # auto-commit ao sair, rollback em exception
        pedido = Pedido(usuario_id=usuario_id)
        db.session.add(pedido)
        db.session.flush()  # gera pedido.id sem commit
        for item in itens:
            db.session.add(ItemPedido(pedido_id=pedido.id, **item))
        db.session.add(AuditLog(action=f"pedido_criado:{pedido.id}"))
    return pedido
```

**Notas:**
- SQLite suporta transações via `BEGIN/COMMIT/ROLLBACK`. PostgreSQL/MySQL idem.
- Para Mongo, use `session.startTransaction()` (replicaset obrigatório).

---

## RP-011 — DEBUG via env (resolve AP-011)

**Antes:**
```python
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois:**
```python
# src/config/settings.py
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

```python
# src/app.py
app.config["DEBUG"] = settings.DEBUG
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
```

**Notas:**
- `app.run()` sem `debug=True` desabilita Werkzeug debugger.
- Para Node: `NODE_ENV !== 'production'` para detalhes; nunca expor stack trace em produção.

---

## RP-012 — Cascade delete via schema/ORM (resolve AP-012)

**Antes (SQLAlchemy sem cascade):**
```python
class User(db.Model):
    tasks = db.relationship('Task', backref='user')
```

**Depois:**
```python
class User(db.Model):
    tasks = db.relationship('Task', backref='user', cascade='all, delete-orphan')
```

**Antes (SQL bruto sem ON DELETE):**
```sql
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    course_id INTEGER REFERENCES courses(id)
);
```

**Depois:**
```sql
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT
);
```

**Notas:**
- `CASCADE` para dependências (matrículas somem se user some).
- `RESTRICT`/`NO ACTION` para entidades de referência (não deixar deletar curso com matrículas ativas).
- SQLite só respeita `ON DELETE CASCADE` se `PRAGMA foreign_keys = ON` for executado na conexão.

---

## RP-013 — Schema único de validação (resolve AP-013)

**Antes (validação inline duplicada entre POST e PUT):**
```python
@bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if 'priority' in data and (data['priority'] < 1 or data['priority'] > 5):
        return jsonify({'error': 'invalid priority'}), 400
    # ... etc

@bp.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    data = request.get_json()
    # esqueceu a validação de priority — drift silencioso
```

**Depois (schema com marshmallow):**
```python
# src/schemas/task_schema.py
from marshmallow import Schema, fields, validate

class TaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    priority = fields.Int(validate=validate.Range(min=1, max=5))
    status = fields.Str(validate=validate.OneOf(['pending', 'in_progress', 'done', 'cancelled']))

create_schema = TaskSchema()
update_schema = TaskSchema(partial=True)  # todos opcionais para PUT
```

```python
@bp.route('/tasks', methods=['POST'])
def create_task():
    data = create_schema.load(request.get_json())
    return task_service.create(data)

@bp.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    data = update_schema.load(request.get_json())
    return task_service.update(id, data)
```

**Equivalentes em outras stacks:** `pydantic` (Python), `joi`/`zod` (Node), `class-validator` (NestJS).

---

## RP-014 — Constantes nomeadas (resolve AP-014)

**Antes (whitelists inline em 4 lugares):**
```python
# routes/task_routes.py:110
if status not in ['pending', 'in_progress', 'done', 'cancelled']:
    return error('status inválido')

# routes/task_routes.py:177 — mesma lista, duplicada
if data['status'] not in ['pending', 'in_progress', 'done', 'cancelled']:
    ...

# models/task.py:39 — mais uma vez
valid = ['pending', 'in_progress', 'done', 'cancelled']

# utils/helpers.py:75
valid_statuses = ['pending', 'in_progress', 'done', 'cancelled']
```

**Depois (constante única):**
```python
# src/domain/constants.py
TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
TASK_PRIORITY_MIN = 1
TASK_PRIORITY_MAX = 5
USER_ROLES = ('user', 'admin', 'manager')
```

```python
# routes, models, schemas — todos importam de constants.py
from domain.constants import TASK_STATUSES

if status not in TASK_STATUSES:
    raise ValidationError('status inválido')
```

**Notas:**
- Tuple, não list — imutável.
- Para tiers de desconto, use lista de tuplas com semântica clara: `TIERS = [(10000, 0.10), ...]`.

---

## RP-015 — Error handler centralizado (resolve AP-015)

**Antes (cada handler com `except Exception` próprio):**
```python
def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        return jsonify({"data": produtos}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500  # vaza estrutura interna
```

**Depois (raise + handler centralizado):**
```python
# src/middlewares/error_handler.py
import logging
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(e):
        return jsonify({"error": e.messages}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return jsonify({"error": str(e)}), 404

    @app.errorhandler(HTTPException)
    def handle_http(e):
        return jsonify({"error": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_generic(e):
        logger.exception("Unhandled exception")
        return jsonify({"error": "Internal server error"}), 500
```

```python
# controller fica limpo
def listar_produtos():
    produtos = produto_service.find_all()
    return jsonify({"data": produtos}), 200
```

**Notas:**
- Logue stack trace internamente; resposta ao cliente é genérica.
- Defina exceções customizadas no domínio (`NotFoundError`, `ConflictError`) — handler mapeia para HTTP.

---

## RP-016 — Eliminar estado global mutável (resolve AP-016)

**Antes:**
```javascript
// utils.js
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    globalCache[key] = data;
}

module.exports = { globalCache, totalRevenue, logAndCache };
```

**Depois (Redis ou DB):**
```javascript
// src/services/cache_service.js
const redis = require('redis').createClient(config.redisUrl);

async function set(key, value, ttlSeconds = 3600) {
    await redis.setEx(key, ttlSeconds, JSON.stringify(value));
}

async function get(key) {
    const v = await redis.get(key);
    return v ? JSON.parse(v) : null;
}

module.exports = { set, get };
```

**Alternativa simples (se não houver Redis disponível): `lru-cache` em memória, encapsulado:**
```javascript
const LRU = require('lru-cache');
const cache = new LRU({ max: 1000, ttl: 1000 * 60 * 15 }); // 15min

module.exports = { cache };
```

**Notas:**
- Cache global compartilhado entre tenants é vetor de info leak.
- Métricas como `totalRevenue` devem ser query agregada no DB (`SELECT SUM(amount) ...`), não contador em memória.

---

## RP-017 — Logger estruturado (resolve AP-017)

**Antes:**
```python
print("Listando " + str(len(produtos)) + " produtos")
print("ERRO: " + str(e))
```

**Depois (Python logging):**
```python
# src/config/logging.py
import logging
import sys

def setup_logging(level="INFO"):
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stdout,
    )

# nos controllers:
logger = logging.getLogger(__name__)
logger.info("listing %d produtos", len(produtos))
logger.exception("erro ao processar")  # inclui stack trace
```

**Antes (Node):**
```javascript
console.log(`Processando checkout para ${userId}`);
```

**Depois (Node + pino):**
```javascript
const pino = require('pino');
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

logger.info({ userId, courseId }, 'processando checkout');
```

**Notas:**
- JSON structured logs facilitam ingestão em ELK/Datadog/CloudWatch.
- Níveis: `debug` (verboso), `info` (eventos), `warn` (situação suspeita), `error` (falha que requer atenção).

---

## RP-018 — Envelope de resposta consistente (resolve AP-018)

**Antes (6 shapes diferentes):**
```python
return jsonify({"dados": produtos, "sucesso": True}), 200
return jsonify({"erro": "..."}), 500
return jsonify({"dados": [], "sucesso": True, "total": 0}), 200
return jsonify({"sucesso": True, "mensagem": "..."}), 200
```

**Depois (1 envelope):**
```python
# src/middlewares/response.py
def ok(data=None, meta=None, status=200):
    body = {"data": data}
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status

def err(message, status=400, details=None):
    body = {"error": {"message": message}}
    if details is not None:
        body["error"]["details"] = details
    return jsonify(body), status
```

```python
# controllers
return ok([p.to_dict() for p in produtos])
return ok({"id": novo_id}, status=201)
return err("Produto não encontrado", status=404)
```

**Notas:**
- Escolha o envelope dominante do código original e padronize para ele — preserva contrato.
- Documente em OpenAPI/Swagger.

---

## RP-019 — Idiomas modernos + limpeza (resolve AP-019)

**Antes:**
```python
import json, os, sys, time  # nada disso usado
# ...
if type(tags) == list:
    result['tags'] = ','.join(tags)
# ...
count = count + 1
```

**Depois:**
```python
# imports só do que usa
from datetime import datetime
# ...
if isinstance(tags, list):
    result['tags'] = ','.join(tags)
# ...
count += 1
```

**Antes (Node — `var self = this`):**
```javascript
setupRoutes(app) {
    const self = this;
    app.get('/x', function(req, res) {
        self.db.run(...);
    });
}
```

**Depois (arrow function preserva `this`):**
```javascript
setupRoutes(app) {
    app.get('/x', (req, res) => {
        this.db.run(...);
    });
}
```

**Notas:**
- Rode `ruff`, `flake8`, `eslint --fix` para varredura automática.
- Removal de imports não usados costuma quebrar nada — é seguro.

---

## RP-020 — Nomes claros via DTO (resolve AP-020)

**Antes:**
```javascript
let u = req.body.usr;
let e = req.body.eml;
let p = req.body.pwd;
let cid = req.body.c_id;
let cc = req.body.card;
```

**Depois (DTO/schema com nomes completos):**
```javascript
// src/schemas/checkout_schema.js
const Joi = require('joi');

const checkoutSchema = Joi.object({
    userName: Joi.string().required(),
    email: Joi.string().email().required(),
    password: Joi.string().min(8).required(),
    courseId: Joi.number().integer().positive().required(),
    cardNumber: Joi.string().creditCard().required(),
});

// controller
const { value } = checkoutSchema.validate(req.body);
const { userName, email, password, courseId, cardNumber } = value;
```

**Notas:**
- API externa não precisa mudar — DTO pode mapear `usr → userName` na validação. Mas considere documentar e versionar a API se for revisar nomes.

---

## RP-DEP-001 a RP-DEP-008 — Substituições de APIs deprecated

Para cada `AP-DEP-NNN` do catálogo, a transformação é direta — basta trocar a API:

| Deprecated | Substituir por |
|---|---|
| `require('sqlite3').verbose()` | `require('sqlite3')` ou `better-sqlite3` |
| `const self = this` | arrow functions |
| Callback hell | `async/await` com Promise |
| `hashlib.md5/sha1` para senha | `werkzeug.security.generate_password_hash` / `bcrypt` |
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| `new Buffer(...)` | `Buffer.from(...)` / `Buffer.alloc(...)` |
| `body-parser` standalone | `express.json()` / `express.urlencoded()` |
| `request` (npm) | `fetch` nativo / `axios` / `got` |

---

## Ordem de execução recomendada para Fase 3

Aplicar transformações em ordem decrescente de risco:

1. **Extrair config** (RP-002, RP-011) — baixo risco, libera os outros passos.
2. **Resolver SQLi e queries parametrizadas** (RP-001) — vetor de ataque crítico, mas mudança mecânica.
3. **Remover endpoints de SQL/eval arbitrário** (RP-005) — pedir confirmação extra.
4. **Hash de senha + remover senha de responses** (RP-004, RP-007) — antes de criar novos handlers que dependam disso.
5. **Quebrar god class em controllers por domínio** (RP-003) — depois que config/security está em ordem.
6. **Extrair lógica de negócio para services** (RP-009) — usa controllers já separados.
7. **Eliminar N+1, adicionar transações** (RP-008, RP-010) — performance e consistência.
8. **Validação centralizada + constants + error handler** (RP-013, RP-014, RP-015) — pavimenta o caminho.
9. **Envelope de resposta + logger estruturado + cleanup** (RP-018, RP-017, RP-019, RP-020) — polish.

Entre cada etapa, **rode os testes/endpoints** para confirmar que não quebrou nada.
