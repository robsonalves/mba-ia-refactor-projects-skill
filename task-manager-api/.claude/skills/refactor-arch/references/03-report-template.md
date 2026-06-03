# 03 — Template do Relatório de Auditoria

Use este formato exato para salvar a saída da Fase 2 em `reports/audit-project-<N>.md`. **Não altere os títulos das seções nem a ordem dos campos** — o template é o contrato.

---

## Template (copie e preencha)

```markdown
# Architecture Audit Report — <nome do projeto>

**Generated:** <data ISO 8601>
**Stack:** <linguagem> + <framework>
**Files analyzed:** <N> | **LOC (approx):** <total>
**Database:** <tipo + tabelas>

---

## Phase 1 — Project Analysis

| Field | Value |
|---|---|
| Language | <linguagem + versão> |
| Framework | <framework + versão> |
| Dependencies | <lista compacta, vírgula-separada> |
| Domain | <descrição em 1 frase> |
| Architecture | <flat / parcial / camadas — com justificativa em 1 frase> |
| Source files | <lista de paths relativos> |
| DB tables | <vírgula-separada> |

---

## Summary

| Severity | Count |
|---|---|
| CRITICAL | <N> |
| HIGH | <N> |
| MEDIUM | <N> |
| LOW | <N> |
| **Total** | **<N>** |

---

## Findings

> Ordenados por severidade descendente: CRITICAL → HIGH → MEDIUM → LOW. Dentro de cada severidade, ordene por arquivo e linha.

### [CRITICAL] <título curto do anti-pattern>

- **ID:** AP-NNN (do catálogo `02-antipatterns.md`)
- **File:** `<path>:<linha ou intervalo>`
- **Description:** <1 frase do que está acontecendo no código>
- **Impact:** <1 frase de por que importa — risco real, não teórico>
- **Recommendation:** <transformação do playbook `05-refactor-playbook.md` — referencie `RP-NNN`>

### [CRITICAL] <segundo finding crítico>

- **ID:** AP-NNN
- **File:** `<path>:<linha>`
- **Description:** ...
- **Impact:** ...
- **Recommendation:** RP-NNN

<...repetir para cada finding CRITICAL...>

### [HIGH] <título>

- **ID:** AP-NNN
- **File:** `<path>:<linha>`
- **Description:** ...
- **Impact:** ...
- **Recommendation:** RP-NNN

<...HIGH, MEDIUM, LOW na mesma ordem...>

---

## Deprecated APIs Detected

> Liste sob este header **somente** os findings da seção "Deprecated APIs" do catálogo (AP-DEP-*). Se nenhuma API deprecated foi encontrada, escreva `Nenhuma`.

- **AP-DEP-NNN:** `<arquivo>:<linha>` — `<API atual>` → substituir por `<API moderna>`

---

## Refactoring Plan

> Plano de execução proposto para Fase 3. **Ainda não é a refatoração** — é a lista do que vai ser feito, com qual padrão do playbook, em qual ordem. O humano usa essa seção para decidir se autoriza Fase 3.

| Ordem | Finding ID | Transformação (do playbook) | Risco de regressão |
|---|---|---|---|
| 1 | AP-NNN | RP-NNN — <descrição curta> | <baixo/médio/alto> |
| 2 | ... | ... | ... |

**Ordem recomendada:**

1. Resolver primeiro CRITICAL de segurança (credenciais, SQLi, RCE)
2. Em seguida CRITICAL arquiteturais (god class, estado global)
3. Depois HIGH (N+1, transações, lógica fora do lugar)
4. MEDIUM e LOW se não houver risco de regressão

---

## Decisão

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

> A skill pausa aqui e aguarda input do humano. Resposta diferente de `y` ou `yes` encerra sem modificar nada.
```

---

## Regras do template

1. **Não invente seções.** Use exatamente os títulos acima. Ferramentas downstream (CI, automation, geração de PR) podem depender desse formato.
2. **Ordem dos findings é mandatória.** CRITICAL → HIGH → MEDIUM → LOW. Dentro de cada bucket, ordene por path do arquivo e depois por número de linha.
3. **Cada finding precisa do bloco completo** (ID, File, Description, Impact, Recommendation). Faltar qualquer campo invalida o finding para o checklist do desafio.
4. **Use IDs consistentes** — o ID do anti-pattern (`AP-NNN`) liga o relatório ao catálogo; o ID da transformação (`RP-NNN`) liga ao playbook. Isso permite cross-reference e auditoria do que foi/não foi resolvido.
5. **Linhas em `File:`** podem ser:
   - Linha única: `models.py:110`
   - Intervalo: `models.py:28-49`
   - Múltiplas linhas no mesmo arquivo: `models.py:28, 47-49, 110`
   - Arquivo inteiro (quando o problema é estrutural): `models.py:1-350`
6. **Plain markdown.** Sem HTML, sem componentes especiais, sem emoji. O relatório precisa ser legível em `cat`, no GitHub, no VS Code.
7. **`reports/audit-project-<N>.md`** — sempre na raiz do repo do desafio. `<N>` é 1, 2 ou 3 conforme o projeto. Sobrescreva se já existir (cada execução = uma versão).

---

## Exemplo mínimo (referência rápida)

```markdown
# Architecture Audit Report — code-smells-project

**Generated:** 2026-06-03T10:00:00Z
**Stack:** Python + Flask 3.1.1
**Files analyzed:** 4 | **LOC (approx):** 780
**Database:** SQLite — produtos, usuarios, pedidos, itens_pedido

## Phase 1 — Project Analysis

| Field | Value |
|---|---|
| Language | Python 3.9+ |
| Framework | Flask 3.1.1 |
| Dependencies | flask-cors |
| Domain | API de E-commerce com produtos, usuários, pedidos e relatórios |
| Architecture | Flat — 4 arquivos no root, sem separação de camadas |
| Source files | app.py, controllers.py, models.py, database.py |
| DB tables | produtos, usuarios, pedidos, itens_pedido |

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 6 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | **12** |

## Findings

### [CRITICAL] SQL Injection em queries de usuário

- **ID:** AP-001
- **File:** `models.py:110`
- **Description:** `login_usuario` concatena email/senha diretamente na query SQL.
- **Impact:** payload `' OR '1'='1` derruba autenticação inteira. Bypass total de login.
- **Recommendation:** RP-001 — trocar por `cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))`.

### [CRITICAL] Endpoint /admin/query executa SQL arbitrário

- **ID:** AP-005
- **File:** `app.py:59-78`
- **Description:** endpoint recebe `{"sql": "..."}` e roda direto no banco sem auth.
- **Impact:** RCE no banco. Dump completo + drop de tabelas trivial.
- **Recommendation:** RP-005 — remover o endpoint. Operações admin reais devem ser específicas, autenticadas e auditadas.

<...continua para os demais findings...>

## Deprecated APIs Detected

Nenhuma API deprecated detectada neste projeto.

## Refactoring Plan

| Ordem | Finding ID | Transformação | Risco |
|---|---|---|---|
| 1 | AP-002 | RP-002 — extrair SECRET_KEY para env var | baixo |
| 2 | AP-005 | RP-005 — remover /admin/query | baixo |
| 3 | AP-001 | RP-001 — queries parametrizadas | médio |
| 4 | AP-003 | RP-003 — quebrar god class em controllers por domínio | alto |
| ... | ... | ... | ... |

## Decisão

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
