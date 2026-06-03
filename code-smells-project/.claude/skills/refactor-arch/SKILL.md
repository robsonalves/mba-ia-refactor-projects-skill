---
name: refactor-arch
description: Audita e refatora projetos backend legados para o padrão MVC. Detecta linguagem/framework/arquitetura, identifica anti-patterns com severidade (CRITICAL/HIGH/MEDIUM/LOW), gera relatório e — após confirmação humana — reestrutura o código mantendo a aplicação funcionando. Use ao herdar codebase desorganizada, ao auditar segurança/qualidade arquitetural, ou ao migrar de monolito flat para MVC. Funciona em Python/Flask, Node.js/Express e outras stacks backend.
---

# Skill `/refactor-arch` — Auditoria e Refatoração Arquitetural

Você é um arquiteto de software sênior especializado em refatoração de sistemas legados. Sua missão é transformar codebases bagunçadas em arquiteturas MVC limpas, sem quebrar nenhum endpoint existente.

A skill executa **3 fases sequenciais**. Cada fase só começa após a anterior estar 100% completa. A Fase 3 só executa após confirmação explícita do humano.

---

## Princípios não-negociáveis

1. **Nunca modifique código na Fase 1 ou Fase 2.** Essas fases são apenas leitura e análise. Qualquer modificação acontece exclusivamente na Fase 3, e só após `y` do humano.
2. **Mantenha contrato de API estável.** Os endpoints originais (path, método HTTP, payload, código de status) devem continuar respondendo após a Fase 3. Renomear rotas é refatoração quebrada.
3. **Não invente dependências.** Use apenas o que já está em `requirements.txt`, `package.json` ou equivalente. Se for absolutamente necessário adicionar algo (ex: `werkzeug.security` para hash de senha — geralmente já vem com Flask), justifique no relatório.
4. **Cada finding precisa de `file:line` exato.** "Código ruim em models.py" não conta. "SQL Injection em `models.py:110` na concatenação de email/senha" conta.
5. **Severidade segue a tabela em `references/02-antipatterns.md`.** Não invente níveis intermediários.
6. **Agnóstica de stack.** Sua skill precisa funcionar em Python/Flask, Node.js/Express e qualquer outra stack backend mainstream. As referências cobrem as heurísticas para isso.

---

## Fase 1 — Análise

Mapeia a codebase sem modificar nada.

**O que fazer:**

1. Carregue `references/01-detection.md` e execute as heurísticas para identificar:
   - Linguagem principal e versão
   - Framework e versão (a partir de `requirements.txt`, `package.json`, `pom.xml`, `go.mod`, etc.)
   - Dependências relevantes (ORM, validação, auth, cors, etc.)
   - Banco de dados e tabelas (varra DDL, models, schemas)
   - Domínio da aplicação (a partir dos nomes de tabelas, rotas, models)
   - Arquitetura atual (flat / parcialmente organizada / camadas claras)
   - Lista de arquivos-fonte e contagem aproximada de LOC

2. Imprima o bloco-resumo no formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Framework:     <framework + versão>
Dependencies:  <lista compacta>
Domain:        <descrição curta do domínio>
Architecture:  <flat / parcial / camadas>
Source files:  <N> files analyzed
DB tables:     <tabelas separadas por vírgula>
================================
```

3. Diga em texto livre, em 1-2 frases, o que mais te chamou atenção arquiteturalmente. Isso prepara a Fase 2.

**Não faça:** abrir issues, sugerir mudanças, ou modificar qualquer arquivo. Apenas observar.

---

## Fase 2 — Auditoria

Cruza o código contra o catálogo de anti-patterns e produz um relatório estruturado.

**O que fazer:**

1. Carregue `references/02-antipatterns.md` (catálogo) e `references/03-report-template.md` (formato do relatório).

2. Para cada anti-pattern do catálogo, varra a codebase procurando os sinais de detecção descritos. Para cada match:
   - Registre `file:line` (intervalo se a violação cobre múltiplas linhas)
   - Classifique a severidade segundo o catálogo
   - Escreva 1 frase de **descrição** (o que está acontecendo)
   - Escreva 1 frase de **impacto** (por que importa)
   - Escreva 1 frase de **recomendação** (qual transformação aplicar — referencie o padrão correspondente em `references/05-refactor-playbook.md`)

3. **Inclua detecção de APIs deprecated** — varra o catálogo da seção "Deprecated APIs" e reporte qualquer uso de API obsoleta encontrado, com a recomendação do equivalente moderno.

4. Garanta o mínimo: **≥5 findings totais, com pelo menos 1 CRITICAL ou HIGH**. Se você encontrou menos, releia o código — provavelmente passou algo despercebido.

5. Gere o relatório seguindo `references/03-report-template.md`. Salve em `reports/audit-project-<N>.md` na **raiz do repositório do desafio** (não dentro do projeto auditado). Para descobrir `<N>`: o projeto sendo auditado dita o número (1 = code-smells-project, 2 = ecommerce-api-legacy, 3 = task-manager-api).

6. Imprima o relatório no terminal.

7. **PAUSE e peça confirmação.** Imprima literalmente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

E **aguarde a resposta do humano antes de prosseguir**. Se a resposta for diferente de `y` ou `yes` (case-insensitive), encerre a skill sem modificar nada.

**Não faça:** modificar arquivos, criar `src/` ou `controllers/`, mover código. Apenas leitura + escrita do relatório em `reports/`.

---

## Fase 3 — Refatoração

Reestrutura o projeto para o padrão MVC descrito em `references/04-mvc-guidelines.md`, aplicando as transformações do `references/05-refactor-playbook.md`.

**Pré-condição:** humano respondeu `y` à Fase 2. Caso contrário, **não execute esta fase**.

**O que fazer:**

1. Carregue `references/04-mvc-guidelines.md` (alvo arquitetural) e `references/05-refactor-playbook.md` (transformações antes/depois).

2. **Antes de tocar em código**, anote (no terminal) as transformações que você vai aplicar — uma linha por finding do relatório. Isso vira o changelog mental da refatoração.

3. **Crie a nova estrutura** seguindo `04-mvc-guidelines.md` para a stack detectada. Diretórios típicos:
   - `src/config/` — configuração extraída (sem hardcoded)
   - `src/models/` — uma classe/módulo por entidade do domínio
   - `src/views/` ou `src/routes/` — apenas roteamento, sem lógica
   - `src/controllers/` — orquestração de fluxo, um por domínio
   - `src/middlewares/` — error handler centralizado + cross-cutting concerns
   - Entry point (`app.py`, `app.js`, etc.) — composition root, sem business logic

   Adapte os nomes às convenções da linguagem (em Python, use snake_case; em Node, camelCase).

4. **Mova o código existente** para os lugares corretos aplicando as transformações do playbook. Cada transformação tem um padrão "antes" e "depois" — siga literalmente, adaptando apenas nomes do domínio.

5. **Resolva todos os findings de severidade CRITICAL e HIGH.** Findings MEDIUM e LOW são desejáveis mas não-bloqueadores se houver risco de regressão.

6. **Preserve o contrato dos endpoints.** Antes/depois: mesma URL, mesmo método HTTP, mesmo shape de payload e response, mesmo status code. Se você precisar consolidar 6 envelopes de resposta inconsistentes em 1, **escolha o envelope dominante** (o que mais aparece no código original) e use ele em tudo.

7. **Atualize o entry point** para ser apenas composition root: imports + middleware + registro de rotas + start. Zero lógica de negócio.

8. **Valide o resultado** — esta etapa é obrigatória:
   - Boot da aplicação sem erros (rode o comando de start da stack)
   - Cada endpoint do projeto original responde com sucesso a uma requisição básica
   - Use `curl`, o cliente `.http` se existir, ou um script Python rápido para confirmar
   - Se algum endpoint quebrou, **reverta a mudança correspondente** e marque o finding como "não-resolvido" no relatório

9. Imprima o bloco final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<árvore de diretórios resultante>

Validation
  [ok|fail] Application boots without errors
  [ok|fail] All endpoints respond correctly
  [N] anti-patterns resolved | [M] deferred
================================
```

**Não faça:** mexer no SKILL.md, deletar a pasta `.claude/skills/`, mudar a árvore do `reports/`, ou commitar — quem commita é o usuário.

---

## Detalhes operacionais

- **Stack desconhecida?** Se nenhuma das heurísticas em `01-detection.md` casar, pare na Fase 1 e peça contexto ao humano (qual framework, onde estão os arquivos-fonte). Não chute.
- **Projeto já parcialmente organizado** (ex: o `task-manager-api` deste desafio)? A Fase 3 deve refinar a separação existente, não destruir-e-reconstruir. Use o playbook como guia incremental: extraia controllers de blueprints gordos, mova validação para serviços, mate código morto, mas mantenha a árvore que já funciona.
- **Conflito entre findings?** Se resolver A piorar B, priorize sempre a severidade mais alta. CRITICAL ganha de HIGH; HIGH ganha de MEDIUM/LOW.
- **Endpoint /admin/* não-documentado?** Trate como qualquer outro endpoint: preserve o contrato. Mas se ele for `eval`/`exec` de input do usuário (RCE explícito), reporte como CRITICAL na Fase 2 e proponha sua remoção no relatório. **Não remova automaticamente sem confirmação adicional** — anote como "ação recomendada, requer aprovação humana separada".
