# 04 — Guidelines do Padrão MVC Alvo

Define a arquitetura-alvo da Fase 3. Use como contrato: ao final da refatoração, o projeto **deve** respeitar todas as regras abaixo.

---

## Estrutura de diretórios canônica

```
<projeto>/
├── src/
│   ├── config/             # Configuração extraída (env vars, settings)
│   │   └── settings.py     # ou settings.js, .env loader
│   │
│   ├── models/             # Camada Model — representação de dados do domínio
│   │   ├── <entidade1>_model.py
│   │   └── <entidade2>_model.py
│   │
│   ├── views/              # Camada View — em APIs REST: serializers/schemas
│   │   └── routes.py       # OU separe em src/routes/ se preferir
│   │   (em frontend web tradicional, aqui ficam templates HTML)
│   │
│   ├── controllers/        # Camada Controller — orquestração de fluxo
│   │   ├── <dominio1>_controller.py
│   │   └── <dominio2>_controller.py
│   │
│   ├── services/           # Lógica de domínio reutilizável (opcional, mas recomendado)
│   │   └── <regra>_service.py
│   │
│   ├── middlewares/        # Cross-cutting concerns
│   │   └── error_handler.py
│   │
│   └── app.py              # Composition root: imports + DI + start
│
├── tests/                  # Testes (preservar se já existirem)
├── requirements.txt        # ou package.json, etc.
└── README.md
```

**Adaptações por linguagem:**

- **Node.js:** use camelCase (`userController.js`, `productModel.js`). Diretórios em snake_case ou kebab-case (`user-routes/`).
- **Python:** use snake_case (`user_controller.py`, `product_model.py`). PEP 8.
- **TypeScript:** geralmente camelCase, mas `kebab-case.ts` também é aceito. Mantenha consistência com o que já existe.

---

## Responsabilidades de cada camada

Cada camada tem uma única responsabilidade. Se você está escrevendo código que não cabe em nenhuma destas definições, está no lugar errado.

### `config/` — Configuração

**Faz:**
- Lê variáveis de ambiente (`os.environ`, `process.env`)
- Centraliza secrets, URLs, ports, feature flags
- Provê valores tipados/validados para o resto da app

**Não faz:**
- Não tem lógica de negócio
- Não toca em banco
- Não importa de `controllers/` ou `services/`

**Exemplo (Python):**
```python
# src/config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

    if SECRET_KEY is None:
        raise RuntimeError("SECRET_KEY não definida")

settings = Settings()
```

---

### `models/` — Camada Model

**Faz:**
- Representa entidades do domínio (Produto, Usuário, Pedido)
- Define schema/tabela do banco (DDL em ORM, ou queries CRUD encapsuladas em SQL bruto)
- Métodos de **dados** apenas: `to_dict()`, `from_db_row()`, validação de campos próprios (não regras de negócio cruzadas)

**Não faz:**
- Não decide regras de negócio (descontos, notificações, fluxos)
- Não fala com HTTP (`request`, `response`, `jsonify`)
- Não conhece outros models — relação por FK/ID, não por instância acoplada quando possível

**Exemplo:**
```python
# src/models/produto_model.py
class Produto:
    def __init__(self, id, nome, preco, estoque, categoria):
        self.id = id
        self.nome = nome
        self.preco = preco
        self.estoque = estoque
        self.categoria = categoria

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "preco": self.preco, ...}

    @staticmethod
    def find_by_id(db, id):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
        row = cursor.fetchone()
        return Produto.from_row(row) if row else None
```

---

### `views/` ou `routes/` — Camada View

Em APIs REST, **View ≈ Routing**: apenas roteamento e serialização de payload de saída.

**Faz:**
- Define paths e métodos HTTP
- Chama o controller correspondente
- Serializa a resposta (se necessário)

**Não faz:**
- Não valida payload (vai para controller/schema)
- Não toca em banco
- Não decide nada — só roteia

**Exemplo (Flask):**
```python
# src/views/routes.py
from flask import Blueprint
from controllers import produto_controller, usuario_controller

api = Blueprint("api", __name__)

api.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
api.add_url_rule("/produtos", "criar_produto", produto_controller.criar, methods=["POST"])
api.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar, methods=["GET"])
```

---

### `controllers/` — Camada Controller

**Faz:**
- Recebe request (extrai params/body)
- Valida input (delegando para schema, se aplicável)
- Chama serviços/models para executar a operação
- Monta resposta padronizada
- Retorna status code apropriado

**Não faz:**
- Não tem regras de domínio (calcular desconto é serviço, não controller)
- Não tem SQL bruto (model encapsula)
- Não tem >50 linhas por handler — se passar disso, extrair para service

**Exemplo:**
```python
# src/controllers/produto_controller.py
from flask import request, jsonify
from models.produto_model import Produto
from middlewares.error_handler import handle_error

def listar():
    produtos = Produto.find_all(get_db())
    return jsonify({"data": [p.to_dict() for p in produtos]}), 200

def criar():
    data = ProdutoSchema().load(request.get_json())  # validação
    produto = produto_service.criar(data)
    return jsonify({"data": produto.to_dict()}), 201
```

---

### `services/` — Lógica de domínio (opcional mas recomendado)

**Faz:**
- Regras de negócio: cálculo de desconto, fluxo de pagamento, decisão de notificação
- Coordena múltiplos models em uma transação
- Reutilizável entre controllers

**Não faz:**
- Não conhece HTTP
- Não acessa `request`/`response` diretamente

**Exemplo:**
```python
# src/services/pedido_service.py
def criar_pedido(usuario_id, itens):
    with db.session.begin():
        pedido = Pedido(usuario_id=usuario_id, status="pendente")
        for item in itens:
            produto = Produto.find_by_id(item["produto_id"])
            if produto.estoque < item["quantidade"]:
                raise EstoqueInsuficienteError(produto)
            pedido.adicionar_item(produto, item["quantidade"])
            produto.estoque -= item["quantidade"]
        db.session.add(pedido)
        notification_service.notificar_pedido_criado(pedido)
    return pedido
```

---

### `middlewares/` — Cross-cutting concerns

**Faz:**
- Error handler centralizado (mapeia exceptions para status code + mensagem)
- Logging de requests (se aplicável)
- Auth/auth-checks
- CORS

**Exemplo de error handler centralizado (Flask):**
```python
# src/middlewares/error_handler.py
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return jsonify({"error": str(e)}), 404

    @app.errorhandler(Exception)
    def handle_generic(e):
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "Internal server error"}), 500
```

---

### Entry point (`app.py` / `app.js`) — Composition Root

**Faz:**
- Cria a instância da aplicação (Flask, Express)
- Lê configuração (`from config import settings`)
- Registra middlewares (CORS, error handler, logging)
- Registra blueprints/routers
- Inicia o servidor (`app.run` / `app.listen`)

**Não faz:**
- **Zero lógica de negócio**
- Zero endpoint inline (mover tudo para `routes/`)
- Zero SQL

**Exemplo (Flask):**
```python
# src/app.py
from flask import Flask
from flask_cors import CORS

from config.settings import settings
from views.routes import api
from middlewares.error_handler import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    CORS(app)
    register_error_handlers(app)
    app.register_blueprint(api)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
```

---

## Princípios SOLID aplicados

- **S (SRP):** cada arquivo/classe tem uma responsabilidade. Se "produto controller" também trata pedidos, está errado.
- **O (OCP):** novos endpoints adicionam novos arquivos, não modificam existentes. Catálogo de validações abre via schema, não via `if`.
- **L (LSP):** subclasses honram contrato do pai. Sem checks de tipo concreto em runtime.
- **I (ISP):** clientes não dependem de métodos que não usam. Separe interfaces grandes (em Python: protocolos via `typing.Protocol`).
- **D (DIP):** controllers dependem de abstrações (services), não de SQL direto. Injete via parâmetro ou container.

---

## Regras de contrato preservadas

Refatorar não muda comportamento externo. Após Fase 3:

1. **URLs idênticas:** `/produtos/123` continua sendo `/produtos/123`, não `/api/v1/products/123`.
2. **Métodos HTTP idênticos:** GET continua GET, POST continua POST.
3. **Payloads de request idênticos:** se a API original aceitava `{"nome": "..."}`, continue aceitando.
4. **Shape do response:** se 6 envelopes diferentes existiam, padronize **para o envelope dominante** (o mais comum no código original). Não invente um novo formato.
5. **Status codes:** 200, 201, 400, 404, 500 — preserve o mapeamento original. Se o original sempre retornava 500 (mesmo para erros de validação), corrija para 400 — isso é uma melhoria justificada, não uma quebra.

---

## Saída final da Fase 3

Ao concluir a refatoração, a árvore final do projeto deve:

- [ ] Ter `src/config/` (ou equivalente) com configuração extraída
- [ ] Ter `src/models/` com 1 arquivo por entidade
- [ ] Ter `src/views/` (ou `src/routes/`) apenas com roteamento
- [ ] Ter `src/controllers/` com 1 arquivo por domínio
- [ ] Ter `src/middlewares/error_handler.*` centralizado
- [ ] Ter entry point limpo (composition root)
- [ ] Bootar sem erro com o comando original (`python app.py`, `npm start`, etc.)
- [ ] Responder a todos os endpoints originais

Esses 8 itens são o checklist que a skill imprime no bloco final da Fase 3.
