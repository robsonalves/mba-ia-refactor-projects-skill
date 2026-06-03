# 02 — Catálogo de Anti-Patterns

Catálogo de referência para Fase 2. Cada entrada tem:
- **Sinais de detecção** (regex/grep-friendly quando possível)
- **Severidade fixa** segundo a escala do desafio
- **Por que importa** (impacto)
- **Recomendação** (referência ao playbook `05-refactor-playbook.md`)

Severidades disponíveis: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. Não invente níveis intermediários.

> **Cobertura mínima:** este catálogo precisa ter ≥8 anti-patterns distribuídos pelas 4 severidades + uma seção dedicada a APIs deprecated. Se você inferir um anti-pattern novo durante a Fase 2 que não esteja aqui, reporte-o mas use a severidade equivalente mais próxima.

---

## CRITICAL

### AP-001 — SQL Injection (concatenação de strings em queries)

**Sinais de detecção:**
- Python: `cursor.execute("SELECT ... " + variavel)`, `f"... WHERE id = {id}"` dentro de `execute(...)`, `"... " % (param,)`, `"... ".format(param)` dentro de `execute(...)`
- Node.js: `db.run("... " + variable)`, template literal `\`... ${var}\`` dentro de `db.run/get/all`
- Qualquer linguagem: concatenação de input do usuário direto em SQL sem placeholder (`?`, `$1`, `:name`)

**Impacto:** bypass de autenticação, leitura/escrita arbitrária no banco, exfiltração de dados. Combinado com endpoint admin sem auth = comprometimento total.

**Recomendação:** trocar por queries parametrizadas. Ver Playbook `RP-001`.

---

### AP-002 — Credenciais e secrets hardcoded

**Sinais de detecção:**
- `SECRET_KEY = "..."`, `API_KEY = "..."`, `password = "..."`, `dbPass = "..."` com literal string no source
- Padrões: `pk_live_*`, `sk_live_*` (Stripe), `AKIA*` (AWS), `ghp_*` (GitHub)
- Senhas em arquivos de seed/setup (`'admin123'`, `'123456'`, `'senha123'`)
- Endpoint que devolve `secret_key` em payload (`/health`, `/debug`, etc.)

**Impacto:** exposição imediata em git público. Rotação requer rebuild. Logs com cartão/token violam PCI-DSS / LGPD / GDPR.

**Recomendação:** extrair para `config/` lendo de `os.environ` / `process.env`. Adicionar `.env.example` documentando as chaves. Ver Playbook `RP-002`.

---

### AP-003 — God Class / God Module

**Sinais de detecção:**
- 1 arquivo com >200 linhas e múltiplas responsabilidades: schema + routes + business logic + side effects
- 1 classe cujo constructor abre DB, cria tabelas, semeia dados e registra rotas
- 1 arquivo agrupando handlers de >2 domínios diferentes (ex: produtos + usuários + pedidos)
- Métodos/funções >100 linhas

**Impacto:** impossível testar em isolamento; qualquer mudança afeta tudo; merge conflicts perpétuos.

**Recomendação:** separar por responsabilidade e domínio. Models por entidade; controllers por domínio; routes apenas para roteamento. Ver Playbook `RP-003`.

---

### AP-004 — Senha em texto puro ou hash quebrado

**Sinais de detecção:**
- Schema com `senha TEXT`, `password TEXT/VARCHAR` sem hash
- `hashlib.md5(...)`, `hashlib.sha1(...)` para senha
- Comparação de senha direta (`pwd == stored`) sem `secrets.compare_digest` ou equivalente
- `password` campo retornado em `to_dict()`/resposta de API
- Hash determinístico sem salt (`base64`, `hex` simples)

**Impacto:** dump do banco = vazamento total de senhas. MD5/SHA1 são quebrados via rainbow tables públicas. Hash sem salt permite ataque batch.

**Recomendação:** trocar por `bcrypt`, `argon2`, ou `werkzeug.security.generate_password_hash`. Remover senha de qualquer `to_dict`/serializer. Ver Playbook `RP-004`.

---

### AP-005 — Endpoint executando SQL/eval arbitrário do request

**Sinais de detecção:**
- Endpoint `/admin/query`, `/eval`, `/exec` que aceita string e roda no DB ou no interpretador
- `cursor.execute(request.get_json()["sql"])`
- `eval(req.body.code)`, `exec(...)`, `Function(...)(req.body.fn)`

**Impacto:** RCE explícito. Maior risco crítico da OWASP Top 10.

**Recomendação:** remover o endpoint completamente. Se houver necessidade administrativa real, expor operações específicas (não SQL arbitrário) atrás de auth + RBAC + audit log. Ver Playbook `RP-005`.

---

### AP-006 — DB / Estado global mutável compartilhado entre threads

**Sinais de detecção:**
- Python: conexão SQLite com `check_same_thread=False` em escopo de módulo
- Node.js: `let cache = {}`, `let totalRevenue = 0` no escopo de módulo, exportado e mutado em múltiplos sites
- Singleton de DB sem pool nem context manager
- Banco em memória (`:memory:`) em entry point de produção

**Impacto:** race conditions silenciosas; commits cruzam requests; dados perdidos em restart (memory DB); escala horizontal impossível.

**Recomendação:** pool de conexão por request (Flask: `g`/factory; Node: instância única + pool; Django: já feito pelo ORM). Ver Playbook `RP-006`.

---

### AP-007 — Log de dados sensíveis (cartão, token, senha, secret)

**Sinais de detecção:**
- `console.log(\`... ${cardNumber} ...\`)`, `console.log(card)`
- `print(secret_key)`, `print(token)`
- Endpoint que devolve `secret_key`, `debug`, `db_path` em payload (`/health`)
- Logger com `password=...`, `card=...` no string format

**Impacto:** violação PCI-DSS (cartão), LGPD (dados pessoais), GDPR. Logs raramente são apagados — exposição persistente.

**Recomendação:** mask antes de logar (`card[-4:]` apenas), nunca logar token/secret/senha; remover de `/health`. Ver Playbook `RP-007`.

---

## HIGH

### AP-008 — N+1 Query

**Sinais de detecção:**
- Loop sobre resultado de query principal, com nova query dentro do loop:
  ```python
  for pedido in pedidos:
      itens = cursor.execute("SELECT * FROM itens WHERE pedido_id = " + str(pedido.id))
  ```
- ORM: `for u in users: u.tasks` (lazy loading sem eager)
- Callback aninhado disparando `db.get(...)` por item da lista anterior

**Impacto:** latência cresce linearmente com volume; endpoint trava em produção; custo de DB explode.

**Recomendação:** JOIN único, `eager loading` (SQLAlchemy `joinedload`), `Promise.all` com batch, ou query agregada. Ver Playbook `RP-008`.

---

### AP-009 — Lógica de negócio fora do lugar (no controller, no model, no route)

**Sinais de detecção:**
- Controllers/routes contendo cálculo de desconto, regras de pricing, decisão de notificação, validação de regras de domínio
- Models de acesso a dados com `if faturamento > 10000: desconto = ...`
- Routes com mais de 30 linhas e múltiplos `if` aninhados

**Impacto:** lógica duplicada entre endpoints; impossível testar regras isoladamente; bugs por drift entre POST e PUT.

**Recomendação:** extrair para camada de serviço (`services/`) ou casos de uso. Controller orquestra; service decide. Ver Playbook `RP-009`.

---

### AP-010 — Transação ausente em operação multi-step

**Sinais de detecção:**
- Sequência de `INSERT`/`UPDATE` sem `BEGIN` / commit explícito ao fim
- Callback hell em Node onde cada etapa é independente (`insert user` → `insert payment` → `insert audit`)
- Operação que cria entidades relacionadas (matrícula + pagamento, pedido + itens) sem transação

**Impacto:** estado inconsistente em caso de falha parcial. Em fluxo de pagamento, ou cobra sem entregar, ou entrega sem cobrar.

**Recomendação:** envolver em transação. ORM: `with db.session.begin():`. SQL bruto: `BEGIN ... COMMIT/ROLLBACK`. Ver Playbook `RP-010`.

---

### AP-011 — DEBUG=True / verbose logging em produção

**Sinais de detecção:**
- `app.run(debug=True)` (Flask)
- `app.config['DEBUG'] = True` literal
- `NODE_ENV` não checado, `morgan('dev')` sem condicional
- `console.log` espalhado em hot paths

**Impacto:** Werkzeug debugger expõe RCE via PIN do debugger. Stack traces vazam estrutura do código.

**Recomendação:** ler de env var, default `False`. Ver Playbook `RP-011`.

---

### AP-012 — Cascade delete manual / órfãos não tratados

**Sinais de detecção:**
- `DELETE FROM users WHERE id = ?` sem ON DELETE CASCADE no schema e sem deletar dependências no código
- Comentários explícitos: "deixei sujo no banco", "TODO: limpar"
- Models sem `cascade='all, delete-orphan'` em relações 1:N

**Impacto:** banco enche de registros órfãos; relatórios e listagens quebram com `JOIN NULL`.

**Recomendação:** definir cascade no schema (`ON DELETE CASCADE`) ou no ORM (`cascade='all, delete-orphan'`). Ver Playbook `RP-012`.

---

## MEDIUM

### AP-013 — Validação duplicada com drift entre POST e PUT

**Sinais de detecção:**
- Handler de POST e PUT validando os mesmos campos com lógicas diferentes
- Checks de whitelist (categoria, status, role) presentes em um e ausentes no outro
- `process_*_data()` em `utils/` que ninguém chama, enquanto routes reimplementam validação inline

**Impacto:** bugs reais (não só smell): campo inválido aceito no PUT mas rejeitado no POST. Refatorar valida o caminho mais fraco.

**Recomendação:** consolidar validação em schema único (marshmallow, pydantic, joi, zod, class-validator). Ver Playbook `RP-013`.

---

### AP-014 — Magic numbers e whitelists hardcoded em múltiplos sites

**Sinais de detecção:**
- Constantes literais em condições: `if priority < 1 or priority > 5`, `if price > 10000`
- Listas literais repetidas: `['pending', 'in_progress', 'done', 'cancelled']` em >1 arquivo
- Tiers de desconto: `if faturamento > 10000: ... elif > 5000: ...`

**Impacto:** mudar 1 valor requer N edits sincronizados. Esquecer 1 site = drift silencioso.

**Recomendação:** extrair para constantes nomeadas em `config/` ou `domain/constants/`. Ver Playbook `RP-014`.

---

### AP-015 — `except Exception` / `except:` engolindo erros

**Sinais de detecção:**
- Python: `except Exception as e: return jsonify({"erro": str(e)}), 500` ou `except:` sem tipo
- Node.js: `(err) => res.status(500).send(err.message)` sem distinguir tipos
- Catch que sempre retorna 500, sem diferenciar 4xx vs 5xx
- Mensagens de erro com `str(e)` vazando nomes de tabela/coluna

**Impacto:** mascara KeyboardInterrupt e SystemExit; vaza estrutura interna ao cliente; impossível debugar produção (sem stack trace).

**Recomendação:** error handler centralizado com mapeamento por tipo. Logar stack trace internamente, retornar mensagem genérica ao cliente. Ver Playbook `RP-015`.

---

### AP-016 — Estado global em escopo de módulo (cache, contadores)

**Sinais de detecção:**
- `let globalCache = {}` exportado e mutado por funções
- `total_revenue = 0` em escopo de módulo, mutado por handlers
- Singleton sem inicialização lazy nem TTL

**Impacto:** vazamento de memória; dados de um tenant aparecem para outro; impossível escalar para múltiplos processos.

**Recomendação:** mover para storage adequado (Redis para cache, DB para contadores agregados) ou encapsular em classe com lifecycle. Ver Playbook `RP-016`.

---

## LOW

### AP-017 — `print()` / `console.log()` como logger

**Sinais de detecção:**
- `print(...)` em código de produção (não em script de seed/CLI)
- `console.log(...)` em handlers Express/NestJS
- Ausência de `logging`/`pino`/`winston`/`structlog` em código não-trivial

**Impacto:** logs não estruturados; sem níveis (info/warn/error); sem timestamp consistente; difícil filtrar.

**Recomendação:** usar logger da stack (`logging` em Python; `pino`/`winston` em Node). Ver Playbook `RP-017`.

---

### AP-018 — Envelope de resposta inconsistente

**Sinais de detecção:**
- Mesmo endpoint às vezes retorna `{dados, sucesso}`, às vezes `{erro}`, às vezes `string`
- Mistura de `res.send("string")` e `res.json({...})`
- 4+ shapes diferentes no mesmo controller

**Impacto:** clientes type-safe impossíveis; documentação OpenAPI vira ficção; testes frágeis.

**Recomendação:** padronizar 1 envelope (ex: `{data, error?, meta?}`). Ver Playbook `RP-018`.

---

### AP-019 — Imports não usados + idiomas obsoletos

**Sinais de detecção:**
- Python: `import json, os, sys, time` sem uso visível
- Node.js: `var self = this` antes de arrow functions
- `type(x) == list` em Python (deveria ser `isinstance(x, list)`)
- `count = count + 1` em vez de `count += 1`

**Impacto:** ruído na review; sinal de zero manutenção; cruft acumulado.

**Recomendação:** linter (ruff/flake8 em Python; eslint em Node) + remover. Ver Playbook `RP-019`.

---

### AP-020 — Field names crípticos / inconsistentes

**Sinais de detecção:**
- `req.body.usr, .eml, .pwd, .c_id, .card` (abreviação agressiva)
- Mistura de `camelCase` e `snake_case` no mesmo payload
- Nomes sem contexto: `data`, `info`, `obj`, `tmp`

**Impacto:** API pública confusa; clientes erram na integração; documentação requer glossário.

**Recomendação:** normalizar nomes na borda do sistema (DTO/schema). Ver Playbook `RP-020`.

---

## Deprecated APIs

Detecte uso de APIs obsoletas e recomende o equivalente moderno. **Esta seção é obrigatória — sempre varra em busca destes sinais.**

### AP-DEP-001 — `sqlite3.verbose()` em Node.js

**Sinal:** `require('sqlite3').verbose()`

**Status:** No-op desde 2018. Mantido apenas por compat.

**Substituir por:** `require('sqlite3')` (sem `.verbose()`), ou migrar para `better-sqlite3` (síncrono, sem callback hell).

---

### AP-DEP-002 — `var self = this` antes de arrow functions

**Sinal:** `const self = this;` ou `var self = this;` em código pós-ES6

**Status:** Workaround pré-2015 para callbacks que perdiam `this`.

**Substituir por:** arrow functions, que preservam `this` lexicamente.

---

### AP-DEP-003 — Callback-based APIs em vez de async/await

**Sinal:** `db.run(sql, params, function(err) { ... db.run(...) })` aninhado em pirâmide

**Status:** Idioma pré-2017. Hoje todas as libs de DB Node têm versão `Promise` ou wrapper `util.promisify`.

**Substituir por:** `async/await` com lib que retorne Promise (`better-sqlite3`, `pg`, `mysql2/promise`).

---

### AP-DEP-004 — `hashlib.md5` / `hashlib.sha1` para senha

**Sinal:** `hashlib.md5(pwd.encode()).hexdigest()`, `hashlib.sha1(...)`

**Status:** Quebrados desde 2004 (MD5) e 2017 (SHA-1). NIST proibiu uso para senha.

**Substituir por:** `werkzeug.security.generate_password_hash` (PBKDF2 com salt), `bcrypt`, `argon2-cffi`.

---

### AP-DEP-005 — `datetime.utcnow()` em Python 3.12+

**Sinal:** `datetime.utcnow()`

**Status:** Deprecated em Python 3.12, removal planejado.

**Substituir por:** `datetime.now(datetime.UTC)` ou `datetime.now(timezone.utc)`.

---

### AP-DEP-006 — `Buffer` constructor sem método estático

**Sinal:** `new Buffer(string)` ou `new Buffer(size)` em Node.js

**Status:** Deprecated desde Node 6 (2016). Vetor de vulnerabilidade.

**Substituir por:** `Buffer.from(string)`, `Buffer.alloc(size)`.

---

### AP-DEP-007 — `body-parser` standalone com Express ≥ 4.16

**Sinal:** `const bodyParser = require('body-parser'); app.use(bodyParser.json())`

**Status:** Body-parser foi reintegrado ao Express 4.16+.

**Substituir por:** `app.use(express.json())`, `app.use(express.urlencoded({extended: true}))`.

---

### AP-DEP-008 — `request` (npm) — biblioteca arquivada

**Sinal:** `require('request')` ou `import request from 'request'`

**Status:** Arquivada em 2020. Sem patches de segurança.

**Substituir por:** `fetch` (nativo Node 18+), `axios`, ou `got`.

---

## Como reportar findings

Cada finding na Fase 2 deve seguir o formato do template `03-report-template.md`:

```
### [SEVERIDADE] <título curto do anti-pattern>
**ID:** AP-NNN (do catálogo)
**File:** <path>:<linha ou intervalo>
**Description:** <1 frase do que está acontecendo>
**Impact:** <1 frase de por que importa>
**Recommendation:** <transformação do playbook RP-NNN>
```

Findings ordenados por severidade descendente: CRITICAL → HIGH → MEDIUM → LOW.
