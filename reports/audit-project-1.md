# Architecture Audit Report — code-smells-project

**Generated:** 2026-05-27T00:00:00Z
**Stack:** Python 3.9+ + Flask 3.1.1
**Files analyzed:** 4 | **LOC (approx):** 780
**Database:** SQLite — produtos, usuarios, pedidos, itens_pedido

---

## Phase 1 — Project Analysis

| Field | Value |
|---|---|
| Language | Python 3.9+ |
| Framework | Flask 3.1.1 |
| Dependencies | flask-cors 5.0.1 |
| Domain | API de E-commerce com produtos, usuários, pedidos e relatórios de vendas |
| Architecture | Flat — 4 arquivos no root, sem separação de camadas |
| Source files | app.py, controllers.py, models.py, database.py |
| DB tables | produtos, usuarios, pedidos, itens_pedido |

---

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 6 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | **12** |

---

## Findings

### [CRITICAL] SQL Injection em 100% das queries de dados

- **ID:** AP-001
- **File:** `models.py:28, 47-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 289-297`
- **Description:** Toda função de acesso a dados concatena variáveis diretamente em strings SQL — login (`models.py:110`), busca (`models.py:289-297`) e CRUD completo.
- **Impact:** Payload `' OR '1'='1` no login derruba autenticação; busca por categoria/preço aceita injeção arbitrária. Bypass de auth e exfiltração total dos dados.
- **Recommendation:** RP-001 — trocar todas as queries por placeholders parametrizados (`?, ?` no sqlite3).

### [CRITICAL] Endpoint `/admin/query` executa SQL arbitrário do request

- **ID:** AP-005
- **File:** `app.py:59-78`
- **Description:** Endpoint recebe `{"sql": "..."}` e roda direto no banco, sem autenticação nem validação.
- **Impact:** RCE no banco (drop tables, dump completo, leitura de hashes de senha). Maior risco da OWASP Top 10.
- **Recommendation:** RP-005 — remover o endpoint. Operações administrativas reais devem ser específicas, autenticadas e auditadas.

### [CRITICAL] Credenciais hardcoded + `DEBUG=True` em produção

- **ID:** AP-002 + AP-011
- **File:** `app.py:7-8, 88` + `controllers.py:288-289` + `database.py:76-79`
- **Description:** `SECRET_KEY = "minha-chave-super-secreta-123"` literal no source; ecoada na resposta de `/health`; `debug=True` ativado; senhas dos seeds (`admin123`, `123456`) em plaintext.
- **Impact:** Werkzeug debugger habilita RCE via PIN. SECRET_KEY no git permite forjar sessões. Vazamento via `/health`.
- **Recommendation:** RP-002 + RP-011 — extrair `SECRET_KEY`, `DEBUG`, `DB_PATH` para variáveis de ambiente em `src/config/settings.py`.

### [CRITICAL] God class `controllers.py` mistura 5 domínios + side effects

- **ID:** AP-003
- **File:** `controllers.py:1-292`
- **Description:** 17 handlers de produtos/usuários/pedidos/login/relatórios/health no mesmo arquivo. Notificações implementadas como `print()` (linhas 208-210, 248-250).
- **Impact:** Impossível testar em isolamento; qualquer mudança afeta tudo; merge conflicts perpétuos.
- **Recommendation:** RP-003 — separar em `src/controllers/produto_controller.py`, `usuario_controller.py`, `pedido_controller.py`, `login_controller.py`, `relatorio_controller.py`.

### [CRITICAL] Conexão de DB global mutável compartilhada entre threads

- **ID:** AP-006
- **File:** `database.py:4, 10`
- **Description:** `db_connection` em escopo de módulo, com `check_same_thread=False`.
- **Impact:** Corrompe WAL sob concorrência; commits cruzam requests; dados perdidos sob carga.
- **Recommendation:** RP-006 — usar `flask.g` para conexão por request, com `teardown_appcontext` fechando ao final.

### [CRITICAL] Senha em texto puro no schema e vazando em `GET /usuarios`

- **ID:** AP-004 + AP-007
- **File:** `database.py:31` + `models.py:83, 99` + `controllers.py:288-289`
- **Description:** Campo `senha TEXT` sem hash. `get_todos_usuarios` e `get_usuario_por_id` devolvem o campo em `to_dict()`. `/health` ecoa `secret_key`.
- **Impact:** Dump do banco = vazamento total de senhas. Listagem pública de usuários expõe todas as credenciais. Combinado com SQLi = comprometimento absoluto.
- **Recommendation:** RP-004 + RP-007 — usar `werkzeug.security.generate_password_hash` (PBKDF2) e remover `senha` de qualquer payload. Limpar `/health`.

### [HIGH] N+1 ao listar pedidos

- **ID:** AP-008
- **File:** `models.py:171-201, 203-233`
- **Description:** `get_pedidos_usuario` e `get_todos_pedidos` disparam 1 query de pedidos + N de itens + N×M de produtos.
- **Impact:** 100 pedidos com 5 itens = 600 queries; endpoint trava sob carga moderada.
- **Recommendation:** RP-008 — query única com `LEFT JOIN` em `pedidos + itens_pedido + produtos`, agrupando no Python.

### [HIGH] Lógica de negócio em controllers e em models

- **ID:** AP-009
- **File:** `controllers.py:208-210, 247-250` + `models.py:256-262`
- **Description:** Notificações (envio de email/SMS/push) implementadas como `print()` dentro de handlers. Tiers de desconto (`if faturamento > 10000`) dentro da função de acesso a dados.
- **Impact:** Regras de domínio acopladas a HTTP/SQL; impossível testar isoladamente; mudança de tier exige mexer no modelo.
- **Recommendation:** RP-009 — extrair `desconto_service`, `pedido_service`, `notification_service` em `src/services/`.

### [MEDIUM] Validação duplicada entre POST e PUT com drift

- **ID:** AP-013
- **File:** `controllers.py:30-54` vs `controllers.py:72-91`
- **Description:** `criar_produto` valida whitelist de categoria; `atualizar_produto` perdeu essa validação. Drift silencioso = bug real.
- **Impact:** Categoria inválida aceita no PUT mas rejeitada no POST. Quem refatorar sem perceber valida o caminho mais fraco.
- **Recommendation:** RP-013 — consolidar em schema único (`marshmallow` ou validação inline única).

### [MEDIUM] `except Exception` engolindo erros + vazando internals

- **ID:** AP-015
- **File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`
- **Description:** 16 routes retornam `jsonify({"erro": str(e)}), 500` — vazam nome de tabela e estrutura de queries.
- **Impact:** Mascara erros legítimos (4xx tratados como 5xx); expõe schema interno ao cliente; impossível debugar produção sem stack trace.
- **Recommendation:** RP-015 — error handler centralizado em `src/middlewares/error_handler.py` mapeando exceptions para HTTP corretamente.

### [LOW] Magic numbers e whitelists hardcoded

- **ID:** AP-014
- **File:** `controllers.py:47-50, 52, 242` + `models.py:257-262`
- **Description:** `< 2`, `> 200`, `["informatica", ...]`, status `["pendente", ...]`, tiers `10000/5000/1000`.
- **Impact:** Mudar 1 valor requer N edits sincronizados; esquecer 1 site = drift silencioso.
- **Recommendation:** RP-014 — extrair para `src/config/constants.py`.

### [LOW] `print()` como logger + envelope de resposta inconsistente

- **ID:** AP-017 + AP-018
- **File:** `controllers.py:8, 11, 57, 106, 149, 161, 179, 182, 208-210, 219, 248, 250`
- **Description:** Logs via `print()` sem timestamp/nível. Respostas em 6 shapes diferentes (`{dados, sucesso}`, `{erro}`, `{sucesso, mensagem}`, etc.).
- **Impact:** Clientes type-safe impossíveis; documentação OpenAPI vira ficção.
- **Recommendation:** RP-017 + RP-018 — `logging` module com formatador + envelope único `{data, error?}`.

---

## Deprecated APIs Detected

Nenhuma API deprecated detectada neste projeto.

---

## Refactoring Plan

| Ordem | Finding ID | Transformação | Risco de regressão |
|---|---|---|---|
| 1 | AP-002 + AP-011 | RP-002 + RP-011 — extrair `SECRET_KEY` e `DEBUG` para env | baixo |
| 2 | AP-005 | RP-005 — remover `/admin/query` e `/admin/reset-db` | baixo |
| 3 | AP-001 | RP-001 — queries parametrizadas em todas as funções | médio |
| 4 | AP-004 + AP-007 | RP-004 + RP-007 — hash de senha + limpar `/health` + remover senha de `to_dict` | médio |
| 5 | AP-003 | RP-003 — separar god class em controllers por domínio | alto |
| 6 | AP-006 | RP-006 — conexão `flask.g` por request | médio |
| 7 | AP-009 | RP-009 — extrair desconto/notificação para services | médio |
| 8 | AP-008 | RP-008 — JOIN único em queries de pedidos | médio |
| 9 | AP-013 | RP-013 — consolidar validação de produto | baixo |
| 10 | AP-015 | RP-015 — error handler centralizado | baixo |
| 11 | AP-014 | RP-014 — constantes em `config/constants.py` | baixo |
| 12 | AP-017 + AP-018 | RP-017 + RP-018 — logger + envelope único | baixo |

**Ordem recomendada:** primeiro CRITICAL de segurança (config, RCE, SQLi, senha), depois CRITICAL arquiteturais (god class, conexão DB), depois HIGH (services, N+1), por último MEDIUM/LOW (polish).

---

## Decisão

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```
