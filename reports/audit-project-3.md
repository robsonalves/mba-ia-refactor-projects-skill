# Architecture Audit Report — task-manager-api

**Generated:** 2026-05-27T00:00:00Z
**Stack:** Python 3.9+ + Flask 3.0 + SQLAlchemy 3.1
**Files analyzed:** 14 | **LOC (approx):** 900
**Database:** SQLite (`sqlite:///tasks.db`) — tasks, users, categories

---

## Phase 1 — Project Analysis

| Field | Value |
|---|---|
| Language | Python 3.9+ |
| Framework | Flask 3.0 + Flask-SQLAlchemy 3.1 + Flask-CORS 4.0 |
| Dependencies | marshmallow 3.20, requests 2.31, python-dotenv 1.0 |
| Domain | Task Manager — tasks, users, categories, com relatórios |
| Architecture | Parcialmente organizada — `models/`, `routes/`, `services/`, `utils/` mas lógica de negócio em routes |
| Source files | app.py, database.py, seed.py + models/, routes/, services/, utils/ |
| DB tables | tasks, users, categories |

---

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 5 |
| HIGH | 2 |
| MEDIUM | 3 |
| LOW | 3 |
| **Total** | **13** |

---

## Findings

### [CRITICAL] Hash de senha com MD5 sem salt

- **ID:** AP-004 + AP-DEP-004
- **File:** `models/user.py:29, 32`
- **Description:** `hashlib.md5(pwd.encode()).hexdigest()` para set/check. Sem salt — hashes iguais para senhas iguais entre users.
- **Impact:** MD5 quebrado desde 2004; rainbow tables públicas; ataque batch em todo o banco.
- **Recommendation:** RP-004 — usar `werkzeug.security.generate_password_hash` (PBKDF2) + remover `password` de qualquer serializer.

### [CRITICAL] `User.to_dict()` vaza hash de senha; rotas devolvem no payload

- **ID:** AP-004 + AP-007
- **File:** `models/user.py:16-25` + `routes/user_routes.py:85, 209`
- **Description:** `to_dict()` inclui `'password': self.password`. `POST /users`, `GET /users/<id>` e `POST /login` retornam o hash.
- **Impact:** Dump de listagem expõe credenciais completas. Combinado com MD5 = comprometimento de senhas.
- **Recommendation:** RP-004 + RP-007 — remover `password` do dict + criar `to_public_dict()` para serialização externa.

### [CRITICAL] "Fake JWT" como token de autenticação

- **ID:** AP-002
- **File:** `routes/user_routes.py:210`
- **Description:** `'token': 'fake-jwt-token-' + str(user.id)` — token É o user_id em texto puro.
- **Impact:** Impersonation trivial — qualquer cliente forja `fake-jwt-token-1` e entra como admin. Não há middleware verificando token.
- **Recommendation:** RP-002 — implementar JWT real (PyJWT) com chave assinada via env. Ou marcar como TODO e remover endpoint até implementação real.

### [CRITICAL] Credenciais SMTP hardcoded em código morto

- **ID:** AP-002
- **File:** `services/notification_service.py:7-10`
- **Description:** `email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'` no source. Service nunca é instanciado.
- **Impact:** Secret commitado mesmo sem uso ativo; sinal de outras credenciais possivelmente expostas; alvo fácil em rastreamento de leak.
- **Recommendation:** RP-002 — mover para `src/config/settings.py` lendo de env. Se service é morto, remover.

### [CRITICAL] `SECRET_KEY` hardcoded + DEBUG=True

- **ID:** AP-002 + AP-011
- **File:** `app.py:13, 34`
- **Description:** `'super-secret-key-123'` literal; `debug=True` em `__main__`.
- **Impact:** Werkzeug debugger habilita RCE via PIN; SECRET_KEY no git permite forjar sessões Flask.
- **Recommendation:** RP-002 + RP-011 — `SECRET_KEY` e `DEBUG` via env em `src/config/settings.py`.

### [HIGH] Lógica de negócio espalhada em routes em vez de controllers/services

- **ID:** AP-009
- **File:** `routes/task_routes.py:30-39, 71-80, 171-180, 273-298` + `routes/report_routes.py:14-101, 103-155`
- **Description:** Cálculo de `overdue` replicado 4×. Relatórios montados inline dentro de Blueprint. Sem camada de serviço.
- **Impact:** Mudança de regra exige atualizar N sites; impossível testar isoladamente; bugs por drift.
- **Recommendation:** RP-009 — extrair `task_service`, `report_service`, mover cálculo de overdue para método do Model.

### [HIGH] N+1 em listagens e relatórios

- **ID:** AP-008
- **File:** `routes/user_routes.py:22` + `routes/report_routes.py:55-68, 30-43`
- **Description:** `len(u.tasks)` dispara 1 query por user; `Task.query.all()` carrega tudo em memória para contar overdue; loop de users com `filter_by` interno no relatório de produtividade.
- **Impact:** Listagem com N users = N+1 queries; relatório de overdue = full table scan + filtro em Python.
- **Recommendation:** RP-008 — `joinedload`/`selectinload` para counts; `Task.query.filter(...).count()` para overdue.

### [MEDIUM] Validação duplicada e código morto em `utils/helpers.py`

- **ID:** AP-013
- **File:** `utils/helpers.py:57-108` (`process_task_data` nunca chamada) vs `routes/task_routes.py:92-114, 167-184`
- **Description:** `process_task_data` faz validação completa e ninguém usa. Routes reimplementam inline com drift entre POST e PUT.
- **Impact:** Caminho de update permite valores inválidos que POST rejeita; dois bancos de regras para sincronizar.
- **Recommendation:** RP-013 — schema único (`marshmallow.Schema` com `partial=True` para PUT) ou consolidar em service. Deletar utils duplicado.

### [MEDIUM] Whitelists e magic numbers repetidos em múltiplos arquivos

- **ID:** AP-014
- **File:** `routes/task_routes.py:110, 177` + `models/task.py:39` + `utils/helpers.py:75, 110` + `routes/user_routes.py:71, 120` + `utils/helpers.py:111`
- **Description:** `['pending', 'in_progress', 'done', 'cancelled']` em 4 lugares; roles em 2; priority range em 3.
- **Impact:** Adicionar status `archived` exige 4 edits sincronizados; esquecer 1 = bug.
- **Recommendation:** RP-014 — `src/config/constants.py` exportando `TASK_STATUSES`, `USER_ROLES`, `PRIORITY_RANGE`.

### [MEDIUM] `except:` bare engolindo qualquer erro

- **ID:** AP-015
- **File:** `routes/task_routes.py:62, 137, 204, 236` + `routes/user_routes.py:130, 149` + `routes/report_routes.py:186, 207, 222` + `utils/helpers.py:46-50, 88`
- **Description:** 11 sites com `except:` ou `except Exception` retornando 500 genérico.
- **Impact:** Mascara KeyboardInterrupt/SystemExit; impossível debugar produção; clientes recebem 500 para erros 4xx legítimos.
- **Recommendation:** RP-015 — error handler centralizado em `src/middlewares/error_handler.py` mapeando exceptions específicas.

### [LOW] `print()` como logger

- **ID:** AP-017
- **File:** `routes/task_routes.py:149, 153, 219, 234` + `routes/user_routes.py:83, 89, 147` + `services/notification_service.py:21, 24`
- **Description:** Logs via `print()` sem nível/timestamp/contexto estruturado.
- **Impact:** Sem ingestão em ELK/Datadog; sem filtragem por nível.
- **Recommendation:** RP-017 — `logging` module com formatter estruturado em `src/config/logging.py`.

### [LOW] Imports não usados em vários arquivos

- **ID:** AP-019
- **File:** `routes/task_routes.py:7` (`json, os, sys, time`) + `routes/user_routes.py:6` (`json`) + `utils/helpers.py:3-7` (`os, json, sys, math`)
- **Description:** Imports declarados sem uso.
- **Impact:** Cruft de desenvolvimento; ruído em review; sinal de baixa manutenção.
- **Recommendation:** RP-019 — remover. `ruff` ou `flake8` no CI previne reincidência.

### [LOW] `type(x) == list` e `count = count + 1` (idiomas não-pythônicos)

- **ID:** AP-019
- **File:** `routes/task_routes.py:141, 210` + `utils/helpers.py:103` + `routes/report_routes.py:37, 60-61, 121-130`
- **Description:** Idioma pré-PEP 8; checagem de tipo deveria ser `isinstance`; incremento deveria ser `+=`.
- **Impact:** Sinal de desenvolvedor inexperiente ou code-gen sem revisão.
- **Recommendation:** RP-019 — `ruff`/`flake8` corrige automaticamente.

---

## Deprecated APIs Detected

- **AP-DEP-004:** `models/user.py:29, 32` — `hashlib.md5(pwd.encode()).hexdigest()` → substituir por `werkzeug.security.generate_password_hash`.
- **AP-DEP-005:** `models/task.py:15-16, 38, 52` + `models/user.py:14` + `routes/*.py` — `datetime.utcnow()` deprecated em Python 3.12 → `datetime.now(timezone.utc)`.

---

## Refactoring Plan

| Ordem | Finding ID | Transformação | Risco |
|---|---|---|---|
| 1 | AP-002 + AP-011 | RP-002 + RP-011 — `SECRET_KEY`, `DEBUG`, DB_URL, SMTP via env | baixo |
| 2 | AP-004 + AP-007 | RP-004 + RP-007 — `generate_password_hash` + `to_public_dict` sem senha | médio |
| 3 | AP-002 (fake JWT) | RP-002 — substituir fake token por nota explícita de "auth não implementada" + remover senha do retorno | baixo |
| 4 | AP-009 | RP-009 — `task_service`, `report_service` extraindo overdue/stats | médio |
| 5 | AP-008 | RP-008 — `selectinload` em listings, `.count()` para overdue em SQL | médio |
| 6 | AP-013 | RP-013 — `marshmallow` schemas únicos para Task/User (POST + PUT partial) | médio |
| 7 | AP-014 | RP-014 — `src/config/constants.py` com TASK_STATUSES, USER_ROLES | baixo |
| 8 | AP-015 | RP-015 — error handler centralizado | baixo |
| 9 | AP-DEP-005 | RP-DEP — `datetime.now(timezone.utc)` em todos os models e routes | baixo |
| 10 | AP-017 + AP-019 | RP-017 + RP-019 — `logging` + remover imports não usados + idiomas modernos | baixo |

---

## Decisão

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```
