# Architecture Audit Report — ecommerce-api-legacy

**Generated:** 2026-05-27T00:00:00Z
**Stack:** JavaScript (Node.js) + Express 4.18
**Files analyzed:** 3 | **LOC (approx):** 180
**Database:** SQLite — users, courses, enrollments, payments, audit_logs

---

## Phase 1 — Project Analysis

| Field | Value |
|---|---|
| Language | JavaScript (Node.js) |
| Framework | Express 4.18+ |
| Dependencies | sqlite3 5.1+ |
| Domain | LMS (Learning Management System) — users, courses, enrollments, payments com checkout |
| Architecture | God class — `AppManager.js` faz schema + seed + routes + payment + audit |
| Source files | src/app.js, src/AppManager.js, src/utils.js |
| DB tables | users, courses, enrollments, payments, audit_logs |

---

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 4 |
| HIGH | 3 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | **11** |

---

## Findings

### [CRITICAL] God class `AppManager` mistura schema, rotas, payment, audit e callback hell

- **ID:** AP-003
- **File:** `src/AppManager.js:4-141`
- **Description:** Construtor abre DB; `initDb()` cria schema + semeia senha plaintext `'123'` (linha 18); `setupRoutes` registra 3 endpoints inline; checkout é pirâmide de callbacks de 7 níveis (linhas 28-78).
- **Impact:** Impossível testar em isolamento; mudança em qualquer endpoint exige mexer no arquivo inteiro.
- **Recommendation:** RP-003 — separar em `src/models/`, `src/controllers/`, `src/services/`, `src/routes/`.

### [CRITICAL] Credenciais hardcoded em produção (DB pass, chave Stripe live, SMTP, senha de seed)

- **ID:** AP-002
- **File:** `src/utils.js:1-7` + `src/AppManager.js:18, 68`
- **Description:** `paymentGatewayKey: "pk_live_1234567890abcdef"` no source; senha default `"123456"` em fallback do checkout; senha `'123'` no seed.
- **Impact:** Shape `pk_live_*` de chave Stripe dispararia cobranças reais. Rotação de chave exige rebuild. Senhas plaintext no seed combinadas com `badCrypto` reversível = comprometimento.
- **Recommendation:** RP-002 — extrair para `src/config/index.js` lendo de `process.env`. Adicionar `.env.example` documentando as chaves.

### [CRITICAL] Crypto fake + log de cartão e chave de pagamento em texto puro + gateway falso

- **ID:** AP-007 + AP-004
- **File:** `src/utils.js:17-23` + `src/AppManager.js:45-46`
- **Description:** `badCrypto` é base64 truncado determinístico sem salt (reversível por lookup). `console.log` na linha 45 expõe número de cartão + chave Stripe em todo checkout. Status decidido por `cc.startsWith("4")` — qualquer cartão começando com 4 é aprovado.
- **Impact:** Violação PCI-DSS (log de cartão); senha quebrada offline (badCrypto); aprovação de pagamento sem validação real.
- **Recommendation:** RP-007 (mask cartão antes de logar, remover chave de log) + RP-004 (bcrypt para senhas). Mock de gateway claramente isolado em service.

### [CRITICAL] DB em memória (`:memory:`) em entry point de produção

- **ID:** AP-006
- **File:** `src/AppManager.js:7`
- **Description:** `new sqlite3.Database(':memory:')` no construtor — dados somem em todo restart.
- **Impact:** Escala horizontal impossível; restart perde tudo; multi-instância sem coordenação.
- **Recommendation:** RP-006 — caminho do DB via `config.dbPath` lendo de `process.env.DB_PATH`.

### [HIGH] N+1 com contadores manuais de callback no `/financial-report`

- **ID:** AP-008
- **File:** `src/AppManager.js:80-129`
- **Description:** Query por curso, por matrícula, por usuário, por pagamento. Concorrência via decrementar `coursesPending`/`enrPending` sem Promise.all; sem propagação de erro.
- **Impact:** Endpoint trava silenciosamente em qualquer erro de DB; latência cresce O(cursos × matrículas × N).
- **Recommendation:** RP-008 — query única com `JOIN` de courses + enrollments + users + payments, agrupando no JS.

### [HIGH] Checkout sem transação — falha no meio deixa estado inconsistente

- **ID:** AP-010
- **File:** `src/AppManager.js:50-63`
- **Description:** Insert user → insert enrollment → insert payment → insert audit, todos em callbacks separados. Sem `BEGIN/COMMIT/ROLLBACK`.
- **Impact:** Se `INSERT payment` falhar, fica enrollment órfã sem pagamento. Cobrança duplicada em retry.
- **Recommendation:** RP-010 — envolver em `db.run("BEGIN")` / `COMMIT` / `ROLLBACK`. Service de pagamento atômico.

### [HIGH] Bug self-documented: `DELETE /api/users/:id` deixa órfãos

- **ID:** AP-012
- **File:** `src/AppManager.js:131-137`
- **Description:** Resposta literal: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` — o autor documentou o bug como mensagem de sucesso.
- **Impact:** Banco acumula órfãos; relatórios financeiros somam pagamentos de usuários inexistentes.
- **Recommendation:** RP-012 — `ON DELETE CASCADE` no schema ou deletar dependências em transação.

### [MEDIUM] Estado global mutável em `cache` e `totalRevenue`

- **ID:** AP-016
- **File:** `src/utils.js:9-10, 12-15, 25`
- **Description:** `let globalCache = {}` e `let totalRevenue = 0` em escopo de módulo, mutados por `logAndCache`. Sem TTL, sem evicção.
- **Impact:** Vazamento de memória; dados de tenant A aparecem para B; impossível escalar multi-processo.
- **Recommendation:** RP-016 — encapsular em service com lifecycle, ou Redis/lru-cache.

### [MEDIUM] Field names crípticos + validação mínima

- **ID:** AP-020
- **File:** `src/AppManager.js:29-35`
- **Description:** `req.body.usr, .eml, .pwd, .c_id, .card`; única validação é `if (!u || !e || !cid || !cc)`. Sem schema.
- **Impact:** API pública confusa; sem validação de formato (email, número de cartão, etc.).
- **Recommendation:** RP-020 — DTO/schema com Joi/zod normalizando para nomes completos.

### [LOW] API deprecated: `require('sqlite3').verbose()`

- **ID:** AP-019 + AP-DEP-001
- **File:** `src/AppManager.js:1`
- **Description:** `require('sqlite3').verbose()` — idioma pré-2018; método é no-op hoje.
- **Impact:** Sinal de zero manutenção; código vai acumular outros patterns obsoletos.
- **Recommendation:** RP-DEP — `require('sqlite3')` direto, ou migrar para `better-sqlite3`.

### [LOW] Respostas mixando text/plain e JSON, sem error handler global

- **ID:** AP-018
- **File:** `src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84, 135`
- **Description:** `res.send("Bad Request")` ↔ `res.status(200).json(...)` ↔ `res.send("Usuário deletado...")`. Cada `if(err)` retorna 500 manualmente.
- **Impact:** Clientes sem contrato consistente; sem middleware de error.
- **Recommendation:** RP-018 — envelope único `{data, error?}` + middleware `app.use(errorHandler)`.

---

## Deprecated APIs Detected

- **AP-DEP-001:** `src/AppManager.js:1` — `require('sqlite3').verbose()` → substituir por `require('sqlite3')` direto, ou `better-sqlite3` para API síncrona.
- **AP-DEP-002:** `src/AppManager.js:26` — `const self = this` antes de arrow function → eliminar, usar arrow functions que preservam `this` lexicamente.
- **AP-DEP-003:** `src/AppManager.js:37-77, 102-126` — pirâmide de callbacks → migrar para `async/await` com `util.promisify` ou `better-sqlite3`.

---

## Refactoring Plan

| Ordem | Finding ID | Transformação | Risco |
|---|---|---|---|
| 1 | AP-002 | RP-002 — secrets para `src/config/` lendo de env | baixo |
| 2 | AP-007 | RP-007 — mask cartão em log + remover chave Stripe de log | baixo |
| 3 | AP-006 | RP-006 — `dbPath` via env, persistente | baixo |
| 4 | AP-DEP-003 | RP-DEP — promisify queries com `util.promisify` | médio |
| 5 | AP-004 | RP-004 — `bcrypt` para hash de senha | médio |
| 6 | AP-003 | RP-003 — quebrar `AppManager` em models/controllers/services/routes | alto |
| 7 | AP-010 | RP-010 — transação atômica no checkout | médio |
| 8 | AP-012 | RP-012 — `ON DELETE CASCADE` no schema de enrollments/payments | baixo |
| 9 | AP-008 | RP-008 — JOIN único no `/financial-report` | médio |
| 10 | AP-016 | RP-016 — encapsular cache em service simples | baixo |
| 11 | AP-020 | RP-020 — schema de validação com Joi | médio |
| 12 | AP-018 + AP-DEP-001 + AP-DEP-002 | RP-018 + RP-DEP — envelope único, error handler, modernizar imports | baixo |

---

## Decisão

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```
