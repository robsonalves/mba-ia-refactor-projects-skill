# 01 — Detecção de Stack e Mapeamento de Arquitetura

Heurísticas para Fase 1. Use na ordem listada — pare assim que casar.

---

## Detecção de linguagem e framework

A detecção segue uma cadeia de evidências: manifesto de dependências → entry point → imports/requires nos arquivos-fonte. Use múltiplos sinais antes de cravar.

### Python

| Sinal | Interpretação |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | Linguagem: **Python**. Leia o manifesto para versão. |
| `flask` listado nas dependências | Framework: **Flask**. Versão na linha do manifesto. |
| `from flask import` em algum `.py` | Confirma Flask. |
| `fastapi` listado | Framework: **FastAPI**. |
| `django` listado + `manage.py` na raiz | Framework: **Django**. |
| `flask-sqlalchemy`, `sqlalchemy` | ORM SQLAlchemy. Procure `db.Model` ou `Base = declarative_base()`. |
| `marshmallow`, `pydantic` | Validação/serialização. |
| `flask-cors`, `flask-jwt-extended` | Sinais de auth/cors customizados. |

### Node.js / TypeScript

| Sinal | Interpretação |
|---|---|
| `package.json` | Linguagem: **JavaScript** (ou **TypeScript** se houver `tsconfig.json` ou `.ts` na fonte). |
| `"express"` em `dependencies` | Framework: **Express**. |
| `"@nestjs/core"` | Framework: **NestJS**. |
| `"fastify"` | Framework: **Fastify**. |
| `"koa"` | Framework: **Koa**. |
| `require('express')` ou `import express from 'express'` | Confirma Express. |
| `sqlite3`, `pg`, `mysql2`, `mongoose`, `prisma`, `typeorm`, `sequelize` | Banco/ORM. |

### Outras stacks (use a mesma lógica)

- **Go:** `go.mod` na raiz → linguagem Go. `gin-gonic/gin`, `labstack/echo`, `gofiber/fiber` → framework correspondente.
- **Java:** `pom.xml` (Maven) ou `build.gradle` (Gradle). `spring-boot-starter-web` → Spring Boot.
- **Ruby:** `Gemfile`. `rails` → Rails. `sinatra` → Sinatra.
- **PHP:** `composer.json`. `laravel/framework` → Laravel. `symfony/framework-bundle` → Symfony.
- **C#:** `*.csproj`. `Microsoft.AspNetCore` → ASP.NET Core.

Se nenhuma das heurísticas casar, **pare e pergunte** ao humano qual é a stack. Não chute.

---

## Detecção de banco de dados

Procure em ordem:

1. **Manifesto:** drivers de DB nas dependências (`sqlite3`, `psycopg2`, `pymysql`, `pg`, `mysql2`, `mongoose`).
2. **String de conexão:** procure por `sqlite:///`, `postgresql://`, `mysql://`, `mongodb://` em arquivos `.env*`, `config.py`, `settings.py`, ou em `os.environ.get` / `process.env`.
3. **DDL:** procure por `CREATE TABLE`, `CREATE SCHEMA`, ou definições de model (`db.Model`, `class.*extends Model`, `@Entity`).
4. **Arquivo `.db`, `.sqlite`, `.sqlite3`** na raiz indica SQLite.

**Tabelas:** liste-as a partir do DDL (`CREATE TABLE <nome>`) ou da definição dos models (`__tablename__ = 'nome'`, `@Entity('nome')`). Reporte os nomes literais.

---

## Classificação de arquitetura atual

Categorize o projeto em uma das três faixas. Use os critérios abaixo:

### Flat (monolítica)

Sinais:
- Tudo na raiz (`app.py` + `controllers.py` + `models.py` no mesmo nível) ou tudo em 1 arquivo
- Sem diretórios `src/`, `app/`, ou equivalente
- Routes + business logic + acesso a dados no mesmo arquivo
- Sem separação por domínio (1 arquivo para produtos, usuários, pedidos juntos)

Exemplo deste desafio: `code-smells-project/`.

### Parcialmente organizada

Sinais:
- Tem alguns diretórios (`models/`, `routes/`, `services/`, `utils/`) mas a separação é superficial
- Lógica de negócio vazou para routes ou models
- Validação duplicada em vários sites
- Services definidos mas não usados (código morto)
- Blueprints/routers grandes (>200 linhas) misturando múltiplos endpoints

Exemplo deste desafio: `task-manager-api/`.

### God class

Sinais:
- 1-3 arquivos concentrando schema + routes + business logic + side effects
- Constructor que abre DB, cria schema, semeia dados e registra rotas
- Funções/métodos com >100 linhas e múltiplas responsabilidades
- Callback hell ou aninhamento profundo de blocos

Exemplo deste desafio: `ecommerce-api-legacy/`.

---

## Detecção de domínio

Determine o domínio da aplicação a partir de **3 fontes triangulares**:

1. **Nomes de tabelas:** `users`, `courses`, `enrollments`, `payments` → LMS / e-learning. `produtos`, `pedidos`, `itens_pedido` → e-commerce. `tasks`, `users`, `categories` → task manager.
2. **Paths das rotas:** `/checkout`, `/enrollments`, `/courses` confirmam LMS com checkout. `/produtos`, `/pedidos` confirmam e-commerce.
3. **Strings de seed/log:** mensagens em PT-BR podem revelar domínio ("ENVIANDO EMAIL: Pedido criado", "Notebook Gamer").

Escreva o domínio em **1 frase**, citando as entidades principais. Ex: *"API de E-commerce com produtos, usuários, pedidos e relatórios de vendas"*.

---

## Contagem de arquivos-fonte

Conte apenas arquivos de código da aplicação (`.py`, `.js`, `.ts`, `.go`, etc.). **Exclua:**

- `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `dist/`, `build/`
- Arquivos de configuração (`.gitignore`, `package-lock.json`, `requirements.txt`)
- Migrations geradas automaticamente (mas conte arquivos de schema escritos à mão)
- Testes (`tests/`, `test_*.py`, `*.test.js`) — mas mencione separadamente se existirem

Reporte o total e, se útil, a soma aproximada de LOC (use `wc -l` ou equivalente).

---

## Sinais que indicam código morto

A Fase 1 não precisa listar código morto exaustivamente, mas vale anotar mentalmente para a Fase 2:

- Funções/classes definidas mas nunca importadas em lugar nenhum
- Imports não utilizados (Python: variável definida mas não referenciada; JS: `import` sem uso)
- Services com nome ambicioso (`NotificationService`, `EmailService`) que ninguém instancia
- Endpoints comentados ou com `TODO`/`FIXME` antigos

---

## Saída esperada da Fase 1

Imprima o bloco-resumo no formato exato do `SKILL.md`. Depois, em 1-2 frases livres, escreva o que mais te chamou atenção arquiteturalmente — isso prepara o humano para a Fase 2 e ajuda você a focar a auditoria.
