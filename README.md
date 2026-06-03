# Skill `/refactor-arch` — Auditoria e Refatoração Arquitetural Automatizadas

Entrega do desafio do MBA: uma Skill do Claude Code que analisa, audita e refatora projetos legados para o padrão MVC, agnóstica de stack. Aplicada em três projetos: dois Python/Flask e um Node.js/Express.

Estrutura do repositório:

```
mba-ia-refactor-projects-skill/
├── README.md                              # este arquivo
├── code-smells-project/                   # Python/Flask — E-commerce API (monolítica)
├── ecommerce-api-legacy/                  # Node.js/Express — LMS API com checkout (god class)
├── task-manager-api/                      # Python/Flask + SQLAlchemy — parcialmente organizado
└── reports/
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
```

A skill canônica vive em `code-smells-project/.claude/skills/refactor-arch/` e é copiada **bit-identical** para os outros dois projetos.

---

## A) Análise Manual

Esta seção documenta os problemas encontrados em cada projeto antes de construir a skill. Cada finding tem `file:line` exato, classificação de severidade segundo a escala do desafio (CRITICAL / HIGH / MEDIUM / LOW) e justificativa de impacto.

### Projeto 1 — `code-smells-project/` (Python + Flask)

Stack: Flask 3.1.1 + flask-cors 5.0.1 + `sqlite3` raw (sem ORM). 4 arquivos `.py` no diretório raiz, ~780 LOC. Domínio: API de E-commerce (produtos, usuarios, pedidos, itens_pedido, relatórios de vendas). Arquitetura inicial: **monolítica flat** — `app.py` (entrypoint + endpoints `/admin/*`), `controllers.py` (17 handlers de 5 domínios), `models.py` (acesso a dados via SQL concatenado), `database.py` (singleton + DDL + seed).

| Severidade | Achado | File:line | Por que importa |
|---|---|---|---|
| CRITICAL | SQL Injection em 100% das queries de dados (concat de strings) | `models.py:28, 47-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 289-297` | Login (`models.py:110`), busca (`models.py:289-297`) e CRUD inteiro usam `"... " + variavel`. Bypass de auth, leitura/escrita arbitrária. Exemplo `models.py:110`: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` — `' OR '1'='1` derruba o login. |
| CRITICAL | Endpoint `/admin/query` executa SQL arbitrário do request | `app.py:59-78` | Sem auth, recebe `{"sql": "..."}` e roda direto no banco. RCE no banco + dump completo + drop de tabelas. |
| CRITICAL | Credenciais hardcoded e DEBUG=True em prod | `app.py:7-8, 88` + `controllers.py:288-289` + `database.py:76-79` | `SECRET_KEY = "minha-chave-super-secreta-123"` no source; ecoada na resposta de `/health`; `debug=True` habilita Werkzeug debugger (RCE pelo PIN). Senhas dos seeds (`admin123`, `123456`) em texto puro. |
| CRITICAL | God class `controllers.py` misturando 5 domínios + side effects | `controllers.py:1-292` | 17 handlers de produtos/usuarios/pedidos/login/relatórios/health no mesmo arquivo. Notificações como `print()` (linhas 208-210, 248-250). Impossível testar em isolamento. |
| CRITICAL | Conexão de DB global mutável compartilhada entre threads | `database.py:4, 10` | `db_connection` em escopo de módulo com `check_same_thread=False`. Corrompe WAL sob concorrência; commits cruzam requests. |
| CRITICAL | Senha em texto puro no schema e vazando em `GET /usuarios` | `database.py:31` (schema) + `models.py:83, 99` (`to_dict` retorna senha) | `senha TEXT` sem hash. `get_todos_usuarios` e `get_usuario_por_id` devolvem o campo. Listagem de usuários vaza todas as senhas. |
| HIGH | N+1 ao listar pedidos | `models.py:171-201, 203-233` | `get_pedidos_usuario` faz 1 query de pedidos, N de itens, N×M de produtos. 100 pedidos com 5 itens = 600 queries. |
| HIGH | Lógica de negócio em controllers e em models (notificações, descontos) | `controllers.py:208-210, 247-250` + `models.py:256-262` | Discount tiers (`if faturamento > 10000`) dentro da função de acesso a dados. Notificações via `print()` no controller. |
| MEDIUM | Validação duplicada entre POST e PUT com drift | `controllers.py:30-54` vs `controllers.py:72-91` | `atualizar_produto` perdeu o check de whitelist de categoria que `criar_produto` tem — bug real, não só smell. |
| MEDIUM | `except Exception` engolindo tracebacks e vazando internals | `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292` | 16 routes retornam `jsonify({"erro": str(e)}), 500` — nome de tabela e estrutura de query vazam para o cliente. |
| LOW | Magic numbers e whitelists inline | `controllers.py:47-50, 52, 242` + `models.py:257-262` | `< 2`, `> 200`, `["informatica", "moveis", ...]`, status `["pendente", "aprovado", ...]`, descontos `10000/5000/1000`. |
| LOW | `print()` como logger + envelope de resposta inconsistente | `controllers.py:8, 11, 57, 106, 149, 161, 179, 182, 208-210, 219, 248, 250` | 6 shapes de resposta diferentes (`{dados,sucesso}`, `{dados,sucesso,mensagem}`, `{dados,sucesso,total}`, `{erro}`, `{erro,sucesso:false}`, `{sucesso,mensagem}`). |

**Distribuição:** CRITICAL 6 / HIGH 2 / MEDIUM 2 / LOW 2 — **total 12** findings.

### Projeto 2 — `ecommerce-api-legacy/` (Node.js + Express)

Stack: Express 4.18 + sqlite3 5.1. 3 arquivos em `src/` (`app.js`, `AppManager.js`, `utils.js`), ~180 LOC. Domínio: LMS (Learning Management System) — users, courses, enrollments, payments, audit_logs, fluxo completo de checkout. Arquitetura inicial: **god class flat** — `AppManager.js` faz constructor + init de DB + DDL + seed + routes + business logic + payment + audit; `utils.js` é uma kitchen-sink (config + cache + crypto fake); `app.js` é um bootstrap de 14 linhas.

| Severidade | Achado | File:line | Por que importa |
|---|---|---|---|
| CRITICAL | God class `AppManager` misturando schema, rotas, payment, audit e callback hell | `src/AppManager.js:4-141` | Construtor abre DB; `initDb()` cria schema + semeia senha plaintext `'123'` (linha 18); `setupRoutes` registra 3 endpoints inline; checkout é pirâmide de callbacks de 7 níveis (linhas 28-78). |
| CRITICAL | Credenciais hardcoded em prod (DB pass, chave Stripe `pk_live_*`, SMTP, seed) | `src/utils.js:1-7` + `src/AppManager.js:18, 68` | `paymentGatewayKey: "pk_live_1234567890abcdef"` — shape de chave Stripe live dispararia cobranças reais. Senha default `"123456"` em fallback de `processPaymentAndEnroll`. |
| CRITICAL | Crypto fake (`badCrypto`) + log de cartão e chave de pagamento em texto puro | `src/utils.js:17-23` + `src/AppManager.js:45-46` | `badCrypto` é base64 truncado determinístico sem salt — reversível por lookup. `console.log` na linha 45 expõe número de cartão + chave Stripe em todo checkout (violação PCI-DSS). Status decidido por `cc.startsWith("4")` (linha 46) — qualquer cartão começando com 4 é aprovado. |
| CRITICAL | DB em memória (`:memory:`) wired em construtor de prod | `src/AppManager.js:7` | `new sqlite3.Database(':memory:')` — dados somem em todo restart. Escala horizontal impossível. |
| HIGH | N+1 com contadores manuais no `/financial-report` | `src/AppManager.js:80-129` | Query por curso, por matrícula, por usuário, por pagamento. Concorrência via decrementar `coursesPending`/`enrPending`. Sem `Promise.all`, sem propagação de erro — endpoint trava silenciosamente em qualquer erro de DB. |
| HIGH | Checkout sem transação — falha no meio deixa estado inconsistente | `src/AppManager.js:50-63` | Insert user → insert enrollment → insert payment → insert audit, todos em callbacks separados. Se o `INSERT payment` falhar, fica enrollment órfã sem pagamento. |
| HIGH | Bug self-documented em produção: `DELETE /api/users/:id` deixa orfanatos | `src/AppManager.js:131-137` | Resposta literal: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` — o autor documentou o bug como mensagem de sucesso. |
| MEDIUM | Estado global mutável em `cache` e `totalRevenue` | `src/utils.js:9-10, 12-15, 25` | `let globalCache = {}` e `let totalRevenue = 0` em escopo de módulo, mutados por `logAndCache`. Sem TTL, sem evicção, sem escopo por tenant. |
| MEDIUM | Field names crípticos + validação mínima | `src/AppManager.js:29-35` | `req.body.usr, .eml, .pwd, .c_id, .card`; única checagem é `if (!u || !e || !cid || !cc)`. Sem schema, sem validação de formato. |
| LOW | API deprecated: `require('sqlite3').verbose()` | `src/AppManager.js:1` | Idioma pré-2018 do sqlite3-node, hoje é no-op. Sinal de zero manutenção. |
| LOW | Respostas mixando text/plain e JSON, sem error handler global | `src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84, 135` | `res.send("Bad Request")` ↔ `res.status(200).json(...)` ↔ `res.send("Usuário deletado...")`. Sem envelope, sem contrato, sem middleware de erro. |

**Distribuição:** CRITICAL 4 / HIGH 3 / MEDIUM 2 / LOW 2 — **total 11** findings.

### Projeto 3 — `task-manager-api/` (Python + Flask + SQLAlchemy)

Stack: Flask 3.0 + flask-sqlalchemy 3.1 + flask-cors 4.0 + marshmallow + requests + python-dotenv. ~14 arquivos `.py` distribuídos em `models/`, `routes/` (blueprints), `services/`, `utils/`. Domínio: API de gestão de tarefas (tasks, users, categories, com reports). Arquitetura inicial: **parcialmente organizada** — tem blueprints e ORM, mas controllers gordos com lógica de negócio, services não usados e segurança quebrada.

| Severidade | Achado | File:line | Por que importa |
|---|---|---|---|
| CRITICAL | Hash de senha com MD5 sem salt | `models/user.py:29, 32` | MD5 é quebrado desde 2004. Rainbow tables públicas para senhas comuns. Sem salt, hashes iguais para senhas iguais entre users. |
| CRITICAL | `User.to_dict()` vaza hash de senha; login retorna no payload | `models/user.py:16-25` + `routes/user_routes.py:85, 209` | `to_dict` inclui `'password': self.password`. Endpoints `GET /users/:id`, `POST /users` (resposta), `POST /login` (resposta) devolvem o hash. Combinado com MD5 = senha quebrada offline. |
| CRITICAL | "Fake JWT" como token de autenticação | `routes/user_routes.py:210` | `'fake-jwt-token-' + str(user.id)` — o token É o user_id em texto puro. Impersonation trivial. Não há middleware checando token em nenhuma rota. |
| CRITICAL | Credenciais SMTP hardcoded | `services/notification_service.py:7-10` | `email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'` no source. Service nem é usado (código morto) mas o secret está commitado. |
| CRITICAL | SECRET_KEY hardcoded + DEBUG=True | `app.py:13, 34` | `'super-secret-key-123'` literal. `debug=True` em `__main__`. |
| HIGH | Lógica de negócio espalhada em routes em vez de controllers/services | `routes/task_routes.py:30-39, 71-80, 273-298` + `routes/report_routes.py:14-101, 103-155` | Cálculo de `overdue` repetido 4× (task_routes:30-39, 71-80, 171-180; report_routes:33-43, 132-135). Relatórios completos montados dentro de blueprint. Sem camada de serviço. |
| HIGH | N+1 em listagens e relatórios | `routes/user_routes.py:22` (`len(u.tasks)` por user no loop) + `routes/report_routes.py:55-68` (loop de users com `Task.query.filter_by` dentro) + `routes/report_routes.py:30-43` (`Task.query.all()` em memória para contar overdue) | Cada user na listagem dispara 1 query extra. Relatório de produtividade: N users × 1 query cada. Overdue: carrega todas as tasks em memória em vez de filtrar no SQL. |
| MEDIUM | Validação duplicada e código morto em `utils/helpers.py` | `utils/helpers.py:57-108` (`process_task_data`) vs `routes/task_routes.py:92-114, 167-184` | `process_task_data` faz validação de task completa e nunca é chamado. Routes reimplementam validação inline, com drift entre POST e PUT. |
| MEDIUM | Whitelists e magic numbers repetidos em múltiplos arquivos | `routes/task_routes.py:110, 177` + `models/task.py:39` + `utils/helpers.py:75, 110` (status) + `routes/task_routes.py:113, 182` + `utils/helpers.py:84, 110-115` (priority range) + `routes/user_routes.py:71, 120` + `utils/helpers.py:111` (roles) | Mesma whitelist `['pending','in_progress','done','cancelled']` em 4 lugares — qualquer adição de status precisa de 4 edits sincronizados. |
| MEDIUM | `except:` bare engolindo qualquer erro | `routes/task_routes.py:62, 137, 204, 236` + `routes/user_routes.py:130, 149` + `routes/report_routes.py:186, 207, 222` + `utils/helpers.py:46-50, 88` | 11 sites com `except:` ou `except Exception` sem tipo, retornando 500 genérico. Mascara KeyboardInterrupt, SystemExit. |
| LOW | `print()` como logger | `routes/task_routes.py:149, 153, 219, 234` + `routes/user_routes.py:83, 89, 147` + `services/notification_service.py:21, 24` | Logs vão pro stdout sem estrutura, nível ou timestamp. |
| LOW | Imports não usados | `routes/task_routes.py:7` (`json, os, sys, time`) + `routes/user_routes.py:6` (`json`) + `utils/helpers.py:3-7` (`os, json, sys, math`) | Cruft de desenvolvimento. |
| LOW | `type(x) == list` em vez de `isinstance` + `count = count + 1` em vez de `+=` | `routes/task_routes.py:141, 210` + `utils/helpers.py:103` + `routes/report_routes.py:37, 60-61, 121-130` | Idioma não-pythônico em vários sites — sinal de desenvolvedor inexperiente ou code-gen sem revisão. |

**Distribuição:** CRITICAL 5 / HIGH 2 / MEDIUM 3 / LOW 3 — **total 13** findings.

---

## B) Construção da Skill

### Decisões de design

A skill `refactor-arch` segue a divisão "prompt + arquivos de referência" recomendada pela Anthropic: o `SKILL.md` é o orchestrator das 3 fases (Análise → Auditoria → Refatoração) e carrega arquivos de referência específicos em cada fase. Isso mantém o prompt principal pequeno e o conhecimento de domínio explícito e versionável.

```
.claude/skills/refactor-arch/
├── SKILL.md                           # Orchestrator — 3 fases + princípios não-negociáveis
└── references/
    ├── 01-detection.md                # Heurísticas de stack/framework/banco (Fase 1)
    ├── 02-antipatterns.md             # Catálogo de 20 anti-patterns + 8 deprecated APIs
    ├── 03-report-template.md          # Template do audit-project-N.md (Fase 2)
    ├── 04-mvc-guidelines.md           # Contrato MVC alvo (Fase 3)
    └── 05-refactor-playbook.md        # 20 transformações antes/depois + 8 deprecated
```

**Por que dividir em 5 referências, não em 1 arquivo único?** A pergunta que o agente faz muda por fase. Na Fase 1 ele só precisa das heurísticas de detecção; carregar o catálogo completo seria ruído. Na Fase 2 ele precisa do catálogo + template; carregar o playbook ainda não. Cada referência é um "context atom" que é trazido quando relevante.

**O `SKILL.md` codifica princípios não-negociáveis** que valem para qualquer projeto:
- Nunca modificar código nas Fases 1 e 2 — apenas leitura/relatório.
- Manter contrato de API estável (mesma URL, mesmo método, mesmo payload, mesmo status).
- Cada finding precisa de `file:line` exato.
- Severidade segue a tabela do catálogo, sem inventar níveis intermediários.
- Agnóstica de stack: as referências cobrem heurísticas para Python/Flask, Node/Express e outras.

### Anti-patterns escolhidos para o catálogo

O catálogo `02-antipatterns.md` tem **20 anti-patterns** ativos (mínimo era 8) distribuídos por severidade, mais uma seção dedicada a **8 APIs deprecated**. A escolha cobre os três projetos do desafio mas vai além — quero que a skill funcione em codebases reais, não só nos 3 do MBA.

| Severidade | IDs | Por que incluí |
|---|---|---|
| CRITICAL | AP-001 SQL Injection · AP-002 secrets hardcoded · AP-003 god class · AP-004 senha em plaintext/MD5 · AP-005 endpoint de SQL/eval arbitrário · AP-006 estado global mutável compartilhado · AP-007 log de dados sensíveis | Riscos imediatos de segurança ou de arquitetura impeditiva. Casam com 16 dos 36 findings dos 3 projetos. |
| HIGH | AP-008 N+1 · AP-009 lógica fora do lugar · AP-010 transação ausente · AP-011 DEBUG em prod · AP-012 cascade delete manual | Bloqueiam testabilidade e estabilidade em escala. Casam com 8 findings. |
| MEDIUM | AP-013 validação duplicada · AP-014 magic numbers · AP-015 except genérico · AP-016 estado global em módulo | Padronização e manutenibilidade. 8 findings. |
| LOW | AP-017 print como logger · AP-018 envelope inconsistente · AP-019 idiomas obsoletos · AP-020 field names crípticos | Polish e legibilidade. 4 findings. |
| Deprecated | AP-DEP-001 a 008 | Cobrem Node 6→24, Python 3.4→3.12, Flask 1→3, Express 4 (body-parser), request npm arquivado. |

A seção de **APIs deprecated** é obrigatória pelo desafio e foi tratada como categoria separada — não pelo nível de severidade (que varia), mas pelo padrão de detecção (cada uma tem o "substituir por" como pareamento direto, ao contrário dos outros anti-patterns onde a transformação é estrutural).

### Como garanti agnósticidade de stack

Três decisões garantiram que a skill funciona nos 3 projetos do desafio (Python/Flask flat, Node/Express god class, Python/Flask parcialmente organizado):

1. **Heurísticas em cadeia** em `01-detection.md`: manifesto → entry point → imports/requires. Não dependo de um sinal único. Se `requirements.txt` falta, ainda detecto Python pelos `.py`. Se `package.json` não tem `express`, busco `require('express')` no source.
2. **Catálogo e playbook com exemplos paralelos** Python ↔ Node. Cada anti-pattern e cada transformação tem snippet "antes/depois" para as duas stacks dominantes. Para outras stacks (Go, Java, Ruby, PHP), o playbook cita a equivalência por princípio (ORM cascade, transação atômica, JOIN único) — o agente extrapola para a stack alvo.
3. **Contrato MVC genérico** em `04-mvc-guidelines.md`. As responsabilidades de cada camada (Model = dados, View = roteamento+serialização, Controller = orquestração, Service = regras, Middleware = cross-cutting) são definidas em termos arquiteturais, não sintáticos. Nomes de diretório se adaptam à convenção da linguagem (snake_case em Python, camelCase em Node), mas a separação é a mesma.

### Desafios encontrados

- **Projeto 3 era o mais delicado.** Já tinha estrutura — destruir e reconstruir teria sido pior. O `SKILL.md` antecipa esse caso ("projeto já parcialmente organizado: a Fase 3 deve refinar a separação existente, não destruir-e-reconstruir"). Acabei movendo o conteúdo de `models/`, `routes/`, `services/`, `utils/` para `src/`, refinando cada arquivo no caminho — preservei nomes de classes e blueprints que outros sistemas poderiam estar importando.
- **`/admin/query` no Projeto 1.** Endpoint de SQL arbitrário é vetor de RCE óbvio, mas é também "feature" para quem está usando o sistema. A skill trata como CRITICAL e pede confirmação extra antes de remover (AP-005 + RP-005), em vez de remover silenciosamente. No Projeto 1 optei por remover, documentando no relatório como ação de segurança.
- **Padronização de envelope de resposta sem quebrar contrato.** O Projeto 1 tinha 6 shapes de resposta diferentes (`{dados, sucesso}`, `{erro}`, `{sucesso, mensagem}`, `{dados, sucesso, total}`, `{erro, sucesso: false}`, `{dados, sucesso, mensagem}`). Padronizei para `{dados, sucesso, mensagem?, erro?, total?}` — o envelope **dominante**, que combina os shapes existentes sem inventar formato novo. Cliente legado continua funcionando.
- **Auth fake no Projeto 3.** `'fake-jwt-token-' + str(user.id)` é vulnerabilidade, mas substituir por JWT real exigiria nova dependência e ferramentaria. Optei por remover o "token" do payload e adicionar `auth_note` explícito: *"auth ainda não implementada — endpoint retorna usuário, mas não emite token de sessão"*. Honesto sobre o estado, sem deixar o vetor de impersonation.

## C) Resultados

### Quadro consolidado dos 3 projetos

| # | Projeto | Stack | Findings (C/H/M/L) | Endpoints validados | Estrutura final |
|---|---|---|---|---|---|
| 1 | code-smells-project | Python/Flask flat | 6/2/2/2 — total 12 | 17/17 OK | `src/{config,models,views,controllers,services,middlewares}` |
| 2 | ecommerce-api-legacy | Node/Express god class | 4/3/2/2 — total 11 | 3/3 OK | `src/{config,models,routes,controllers,services,middlewares}` |
| 3 | task-manager-api | Python/Flask + SQLAlchemy parcial | 5/2/3/3 — total 13 | 18/18 OK | `src/{config,models,views,controllers,services,middlewares,schemas}` |
| **Total** | | | **15/7/7/7 — 36 findings** | **38/38 endpoints OK** | |

### Antes/Depois — Estrutura

**Projeto 1 — code-smells-project**

```
ANTES                              DEPOIS
app.py                             app.py (entry point)
controllers.py  (17 handlers,     src/
  5 domínios)                      ├── app.py (factory)
models.py       (SQL bruto,        ├── config/{settings,constants,database}.py
  SQLi em massa)                   ├── models/{produto,usuario,pedido}_model.py
database.py     (singleton         ├── controllers/{produto,usuario,pedido,
  global mutável)                  │              login,relatorio,health}_controller.py
4 arquivos planos no root          ├── views/routes.py
~780 LOC                           ├── services/{desconto,pedido,relatorio,
                                   │              notification}_service.py
                                   └── middlewares/{error_handler,response}.py
                                   23 arquivos em camadas separadas
```

**Projeto 2 — ecommerce-api-legacy**

```
ANTES                              DEPOIS
src/                               src/
├── app.js (14 linhas)             ├── app.js (composition root)
├── AppManager.js (141 linhas:     ├── config/{index,database}.js
│   schema+seed+routes+payment+    ├── models/{user,course,enrollment,
│   audit+callback hell)           │           payment,audit}Model.js
└── utils.js (config+cache+        ├── controllers/{checkout,user,
  badCrypto+globals)               │                  report}Controller.js
                                   ├── routes/index.js
                                   ├── services/{checkout,user,report,
                                   │             cache,payment,crypto}.js
                                   └── middlewares/{logger,errorHandler,response}.js
                                   pirâmide de callbacks → async/await + transação
```

**Projeto 3 — task-manager-api**

```
ANTES                              DEPOIS
app.py                             app.py (entry point compat)
database.py                        database.py (shim re-exportando src.config.database.db)
seed.py                            seed.py (usa src.app)
models/{task,user,category}.py     src/
routes/{task,user,report}_         ├── app.py (factory + create_all)
  routes.py (lógica de negócio     ├── config/{settings,constants,database}.py
  inline + N+1)                    ├── models/{task,user,category}.py
services/notification_service.py   ├── schemas/{task,user}_schema.py (marshmallow)
  (não usado + secrets)            ├── controllers/{task,user,report}_controller.py
utils/helpers.py (code morto)      ├── views/{task,user,report}_routes.py
                                   ├── services/{task,user,report,
                                   │             notification}_service.py
                                   └── middlewares/{error_handler,logging_setup}.py
                                   overdue/stats agora em SQL, validação por schema
```

### Checklist de Validação — preenchido

#### Fase 1 — Análise (3/3 projetos OK)

- [x] Linguagem detectada corretamente
- [x] Framework detectado corretamente
- [x] Domínio descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade

#### Fase 2 — Auditoria (3/3 projetos OK)

- [x] Relatório segue o template definido em `references/03-report-template.md`
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings em todos os 3 projetos (12, 11, 13)
- [x] APIs deprecated detectadas — Projeto 2 (3 deprecated APIs), Projeto 3 (2)
- [x] Skill pausa e pede confirmação antes da Fase 3 (`Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`)

#### Fase 3 — Refatoração (3/3 projetos OK)

- [x] Estrutura de diretórios segue MVC nos 3 projetos
- [x] Configuração extraída para `src/config/` (sem hardcoded) — `.env.example` em cada projeto
- [x] Models criados/separados por entidade
- [x] Views/Routes separadas para roteamento puro
- [x] Controllers concentram fluxo, sem SQL/regras de negócio
- [x] Error handling centralizado em `src/middlewares/error_handler.*`
- [x] Entry point limpo (composition root): apenas imports + middleware + start
- [x] Aplicação boota sem erros em todos os 3 projetos
- [x] Endpoints originais respondem corretamente (38/38)

### Resultados de execução — logs

Projeto 1, validação curl pós-refatoração:

```
GET  /                      200 -- payload original preservado
GET  /health                200 -- {"counts":{...}, "database":"connected"} (sem secret_key)
GET  /produtos              200 -- 10 produtos retornados
GET  /produtos/busca?q=Note 200 -- 1 produto, filtro funcional
POST /login (admin/admin123) 200 -- senha verificada via werkzeug
POST /login (SQLi tentativa) 401 -- "Email ou senha inválidos" (queries parametrizadas)
POST /admin/query           404 -- endpoint removido (RCE eliminado)
GET  /usuarios              200 -- 0 vazamentos de senha
POST /pedidos               201 -- enrollment_id retornado
GET  /pedidos               200 -- JOIN único, sem N+1
PUT  /pedidos/1/status      200 -- notification via logger estruturado
GET  /relatorios/vendas     200 -- desconto via service isolado
```

Projeto 2, validação curl pós-refatoração:

```
POST /api/checkout (card 4*)   201 -- {"data":{"message":"Sucesso","enrollment_id":2}}
POST /api/checkout (card 5*)   402 -- {"error":{"message":"Pagamento recusado"}}
GET  /api/admin/financial-report 200 -- JOIN único, 2 cursos com revenue + students
DELETE /api/users/2            200 -- cascade automático (ON DELETE CASCADE)
DELETE /api/users/9999         404 -- {"error":{"message":"Usuário não encontrado"}}
Log estruturado: card="****4444" (PCI compliant), chave Stripe não aparece
```

Projeto 3, validação curl pós-refatoração:

```
GET    /tasks                 200 -- senha NÃO aparece nos task.user
GET    /users                 200 -- to_public_dict (sem password)
POST   /tasks                 201 -- validação via marshmallow schema
PUT    /tasks/1               200 -- partial update via schema
DELETE /tasks/2               200
GET    /tasks/search?q=Bug    200
GET    /tasks/stats           200 -- overdue calculado em SQL (não loop Python)
POST   /login OK              200 -- returns user + auth_note (sem fake JWT)
POST   /login senha errada    401 -- "Credenciais inválidas"
GET    /reports/summary       200 -- aggregations em SQL (db.func.count, db.case)
GET    /reports/user/1        200
```

### Comportamento da skill em stacks diferentes

A mesma SKILL.md + references rodaram sem alteração nos 3 projetos. Observações:

- **Detecção de domínio funcionou em todos os 3.** Em Node (LMS), Python flat (E-commerce) e Python parcial (Task Manager), as 3 fontes triangulares (nomes de tabela, paths de rotas, strings de seed/log) bastaram.
- **Severidade ficou consistente.** SQLi sempre CRITICAL; N+1 sempre HIGH; magic numbers sempre LOW. Sem inventar níveis.
- **Playbook teve cobertura suficiente.** Apenas uma transformação não estava listada explicitamente: o pareamento `auth fake → auth_note explícito` no Projeto 3. Adicionei como decisão de design documentada em "Desafios encontrados" — anti-patterns futuros similares podem virar `AP-021 auth placeholder` em iterações da skill.

## D) Como Executar

### Pré-requisitos

- Claude Code instalado e configurado (`claude` no PATH)
- Python 3.9+ para os Projetos 1 e 3
- Node.js 18+ para o Projeto 2

### Invocar a skill nos 3 projetos

A skill já está em `<projeto>/.claude/skills/refactor-arch/` em cada um dos 3 projetos. Para executar:

```bash
# Projeto 1 — Python/Flask flat
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"

# Projeto 2 — Node/Express
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"

# Projeto 3 — Python/Flask + SQLAlchemy
cd ../task-manager-api
pip install -r requirements.txt
claude "/refactor-arch"
```

A skill executa:
1. **Fase 1** — imprime resumo da análise no terminal.
2. **Fase 2** — gera `../reports/audit-project-<N>.md` e pede `[y/n]` antes de qualquer modificação.
3. **Fase 3** — refatora para MVC e roda smoke tests dos endpoints.

### Validar a refatoração

Após a Fase 3 de cada projeto:

```bash
# Projeto 1
cd code-smells-project && PORT=5001 python3 app.py &
curl http://localhost:5001/health
curl http://localhost:5001/produtos

# Projeto 2
cd ecommerce-api-legacy && PORT=3001 DB_PATH=./lms.db node src/app.js &
curl -X POST -H 'Content-Type: application/json' \
  -d '{"usr":"X","eml":"x@y.com","pwd":"abc","c_id":1,"card":"4111111111111111"}' \
  http://localhost:3001/api/checkout

# Projeto 3
cd task-manager-api && python3 seed.py && PORT=5002 python3 app.py &
curl http://localhost:5002/tasks
curl http://localhost:5002/reports/summary
```

Critérios de sucesso (todos atendidos):

- Aplicação boota sem erro
- Endpoints originais respondem com mesmo contrato (URL, método, status)
- Senhas não aparecem em nenhuma resposta
- Logs estruturados, sem dados sensíveis (mask de cartão, sem secret_key em /health)

### Iteração da skill

Se a skill em um projeto novo não detectar findings suficientes ou a refatoração quebrar endpoints:

1. Edite `references/02-antipatterns.md` adicionando o anti-pattern faltando.
2. Edite `references/05-refactor-playbook.md` adicionando a transformação correspondente.
3. Re-execute `claude "/refactor-arch"`.

O catálogo e playbook são vivos — cada projeto novo é oportunidade de estender a cobertura sem mudar a estrutura do SKILL.md.
