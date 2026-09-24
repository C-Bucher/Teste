# Backlog — TechConnect 2.0

> Backlog oficial do projeto, consolidado a partir dos planos de execução já concluídos ([docs/planejamento/plans/](planejamento/plans/)), dos registros de andamento e revisão de cada fase (arquivos de trabalho locais, não versionados) e do [registro de alterações](registro-de-alteracoes-para-documentacao.md). Cada item foi conferido contra o código em 2026-09-21, com um checkpoint adicional em 2026-09-23 para a integração com Supabase.
>
> **Última atualização (2026-09-21):** entrega do plano de hierarquia de cargos/onboarding e revisão final do branch. SEC-1 passa a concluído, com ressalvas explícitas; ficam abertos MT-1 (dados de negócio compartilhados entre empresas — o maior limite atual do produto), SEC-3, SEC-4, AUTH-2, QA-1 e UX-1.
>
> **Checkpoint 2026-09-23:** o commit `913f78d`, feito direto na `main` e fora do fluxo de `issue`/`branch`/PR descrito no [CONTRIBUTING](../CONTRIBUTING.md), integrou suporte a PostgreSQL gerenciado via Supabase e resolveu a parte de `.env`/`load_dotenv()` do item DB-1. O mesmo commit expôs credenciais reais em texto puro no `README.md`; um commit seguinte (`3210242`) as substituiu por placeholders. Ficam abertos SEC-5 (rotação de credenciais pendente, por decisão da equipe) e DB-5 (a troca de banco entre Supabase, MySQL e SQLite não é automática).
>
> Legenda de status: 🔲 aberto · 🔷 em andamento · ✅ concluído · ⏸️ pausado/bloqueado. Prioridade: P0 (crítico/segurança), P1 (alta), P2 (média), P3 (baixa/dívida técnica).

---

## P0 — Crítico (segurança e integridade de dados)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| MT-1 | Dados de negócio não são separados por empresa | Só `companies`, `users` e `role_permissions` são escopados por `company_id`. Funcionários, lançamentos financeiros, Kanban (projetos/cartões), clientes, fornecedores, notificações e exportações são um único conjunto de dados global: uma empresa recém-cadastrada enxerga os lançamentos, projetos e a receita da empresa de demonstração (comprovado no teste de ponta a ponta). Só `EmployeeModel` tem coluna `company_id` (nula e nunca preenchida); os demais modelos nem têm a coluna. Correção real = migração + `company_id` em ~6 modelos + filtro em todas as consultas (fase de vários dias). Por ora, o sistema não deve ser descrito como multiempresa isolado. | 🔲 | revisão final 2026-09-21 (I1), e2e Task 14 |
| MT-2 | Hub Pessoal não é isolado por usuário | `app/api/v1/endpoints/personal.py` filtra e grava usando a constante de módulo `_OWNER_ID = "usr-001"`, não o usuário autenticado. Todas as tabelas pessoais têm `owner_id` (FK para `users`), mas ele nunca recebe o usuário logado: Admin, Gerente e Funcionário enxergam e alteram os mesmos dados pessoais (comprovado: os 3 logins listam os mesmos 4 lançamentos). Correção = trocar `_OWNER_ID` por `u.id` do `get_current_user` em todos os handlers + migração/seed por usuário + teste de isolamento. Por ora, o Hub Pessoal não deve ser descrito como privado por usuário — isso contradiz a premissa da ADR-002. | 🔲 | verificação pré-publicação 2026-09-21 |
| SEC-1 | RBAC nos endpoints da API | Resolvido para o escopo do plano: `role_permissions` (por empresa/cargo/módulo) + `require_module(...)` retornam 403 real nos routers de equipe, fornecedores, financeiro, exportação, IA e nas rotas de configuração que alteram dados; empresas ainda não customizadas usam os padrões (Gerente: 7 módulos; Funcionário: dashboard e kanban); o frontend agora guarda cada página pelo módulo concedido (conceder e revogar funcionam), e a busca global filtra resultados pelos módulos do usuário. Ressalvas: `kanban`, `clients`, `notifications`, `plans`, `payments` e `personal` não têm gate por módulo (ver SEC-3); as permissões `dashboard` e `kanban` da matriz só afetam o menu. Também corrigido no caminho: `GET/PUT /auth/users` não tinham autorização alguma (qualquer usuário podia se promover a ADMIN) — agora só admin, restrito à própria empresa, com lista de cargos permitidos. | ✅ | Plano `2026-09-08-role-permissions-onboarding`; commits `446dbcd`…`b050a80`, `ecab7fa`, `2dff90c` |
| SEC-3 | Rotas sem gate de módulo | `kanban`, `clients`, `notifications`, `plans`, `payments`, `personal` são acessíveis a qualquer usuário autenticado; `notifications` devolve mensagens globais que citam valores financeiros (mesma causa raiz de MT-1). Decidir por rota o módulo exigido ou registrar como intencional. Permissões `dashboard`/`kanban` da matriz são só de menu. | 🔲 | revisão final (C3/I3) |
| SEC-4 | Endurecimento básico de autenticação | `SECRET_KEY` tem valor padrão inseguro quando a variável de ambiente falta; sem política de senha; sem limite de tentativas em `/auth/login`; token dura 480 min e mudança de cargo só reflete no menu após novo login (o backend já reflete na hora). | 🔲 | revisão final |
| SEC-5 | Credenciais reais commitadas em texto puro | O commit `913f78d` colou no `README.md` a senha real do banco Supabase, a `SUPABASE_ANON_KEY` real e um `SECRET_KEY` real, em vez de placeholders. O commit `3210242` substituiu os valores por placeholders no `README`, mas os valores antigos continuam válidos e visíveis no histórico do Git — a equipe decidiu, em 2026-09-23, não rotacioná-los por ora. Enquanto isso não acontecer, quem tiver acesso ao histórico do repositório (todos os membros da organização, não só a equipe) pode ler e usar essas credenciais. Rotação recomendada no painel do Supabase (Database → Reset database password; regenerar a `anon key`) e, depois, reescrita do histórico para remover o valor. | 🔲 | commit `913f78d` (exposição), `3210242` (mitigação parcial no README) |
| DB-1 | Alinhar banco + persistência confiável | ~~Arquivo `.db` versionado no git.~~ Resolvido: `techconnect.db` saiu do Git e `*.db` está no `.gitignore` (commit `e4108b8`). ~~`.env` não carregado fora do Docker.~~ Resolvido: `load_dotenv()` adicionado em `app/core/config.py` e `app/db/session.py` (commit `913f78d`). Ainda aberto: SQLite continua com caminho relativo (`./techconnect.db`), sensível ao diretório de onde o `uvicorn` é iniciado. | 🔷 | diagnóstico 2026-09-03; `load_dotenv()` resolvido em 2026-09-23 |
| DB-2 | Persistir assinatura/pagamento + registro | `payments.py` (`SUBSCRIPTIONS_DB`, `INVOICES_DB`) e `plans.py` seguem listas/dicts em memória — assinatura do plano escolhido ainda não persiste. ~~`POST /auth/register` não cria a empresa.~~ Resolvido: o registro cria uma `CompanyModel` própria e associa o admin a ela (`446dbcd`). Isso isola só a linha da empresa, os usuários e as permissões — ver **MT-1** para os dados de negócio. | 🔷 | `payments.py` (aberto), `auth.py` (empresa: resolvido) |
| DB-5 | Troca de banco não é automática entre Supabase/MySQL/SQLite | `.env.example` ativa por padrão a `DATABASE_URL` do Supabase (Postgres). O `docker-compose.yml` repassa `DATABASE_URL=${DATABASE_URL}` do `.env` ao container do backend sem sobrescrever para o `db` (MySQL) local — quem seguir "Opção 2 — Docker Compose" sem editar manualmente essa linha faz o backend em Docker tentar conectar no Supabase, não no MySQL que o próprio Compose acabou de subir. Da mesma forma, o fallback SQLite só ocorre se a linha `DATABASE_URL` for comentada/removida por completo, não basta "não ter `.env`". Documentado no README; falta automatizar (ex.: `docker-compose.override.yml` ou checagem no `entrypoint`). | 🔲 | achado na revisão de 2026-09-23 (`.env.example`, `docker-compose.yml`) |
| SEC-2 | Auditoria e conformidade LGPD | Nenhuma trilha de auditoria (quem alterou o quê e quando), sem base para conformidade com LGPD. | 🔲 | registro §9 |

---

## P1 — Alta (funcionalidade essencial incompleta)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| IA-1 | Integração real de IA generativa | CFO Virtual, CFO Pessoal, Conciliação e Gerador de Orçamentos respondem por palavra-chave em `ai.py`. A `GEMINI_API_KEY` já está configurada na infra, mas não é usada. Histórico do CFO (`GET /ai/history`) sempre retorna vazio, e a resposta de `/ai/chat` informa um modelo (`gemini-2.5-flash`) e um consumo de tokens fixos que não correspondem a nenhuma chamada real. | 🔲 | registro §9, `ai.py` |
| AUTH-1 | Autenticação de dois fatores (2FA) | O campo `mfa_enabled` existe no `UserModel` e o login aceita `mfa_code`, mas não há fluxo de ativação nem verificação real. | 🔲 | registro §9 |
| EXP-1 | Exportação nunca conclui | ~~Relatórios ficavam presos em "PROCESSANDO".~~ Resolvido: `exports.py` gera um arquivo real em `uploads/` e `GET /download/{eid}` o serve pelo mount `/uploads` (commit `761afd4`). O conteúdo ainda é um CSV de exemplo, não os dados reais do relatório escolhido. | ✅ | Revisado e commitado 2026-09-18 |
| CFG-1 | Configurações que não persistem | `PUT /company/calendar` (calendário de trabalho) e `GET /company/ctc-params` retornam dicts fixos calculados na hora — não gravam nada, não sobrevivem nem a um reload. Preferências de notificação idem. | 🔲 | task-4-report, `company.py`, `notifications.py` |

---

## P2 — Média (lacunas de UI / comportamento)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| EQ-1 | Botões do menu "kebab" na Gestão de Equipe | ~~Menu de ações (⋮) sem handler ligado.~~ Resolvido: o menu `more_vert` na visão em cartões já dispara `handleViewHistory`/`handleEdit`/`handleTerminate`; a visão em lista também tem os três botões ligados. | ✅ | Verificado 2026-09-10 em `GestaoEquipe.tsx` |
| KAN-1 | Excluir cartão no Kanban | O endpoint `DELETE /kanban/cards/{cid}` já existe e funciona (`kanban.py`), mas ainda não há botão/ação na UI que o chame — `Kanban.tsx` não tem nenhuma chamada `api.delete` para cartões. | 🔲 | Verificado 2026-09-10 |
| FIN-1 | DRE — composição por categoria | ~~Trechos hardcoded.~~ Resolvido: `GET /financial/dre` agora agrega receitas e despesas por categoria a partir dos lançamentos reais do banco (`receitas_map`/`despesas_map` em `financial.py`), sem valores fixos. | ✅ | Verificado 2026-09-10 em `financial.py` |
| NAV-1 | Guarda de rota do Hub Pessoal | Rotas `/pessoal/:tab` são protegidas só no nível de navegação, não de rota. Slug de aba inválido não redireciona a URL. `plan_scope` não é checado por rota. | 🔲 | progress.md revisão final |
| AUTH-2 | Gestão de acessos: regras de negócio faltando | Um admin pode se auto-rebaixar ou desativar o último admin da empresa (sem caminho de recuperação pela API); `PUT /auth/users` com `email` duplicado provavelmente retorna 500; usuários criados não podem ser editados/desativados pela interface (só listar e criar); IDs `usr-NNN`/`cmp-NNN` por contagem colidem após exclusões. | 🔲 | revisões das Tasks 1, 7 e 13b |
| UX-1 | Polimento do onboarding e das permissões | Passo 1 do assistente abre vazio (não pré-preenche com os dados do cadastro); "Salvar Permissões" é um botão separado de "Próximo" (sem salvar, valem os padrões); menu do Layout pisca por um instante ao trocar de página; erro ao carregar a lista de acessos só vai para o console; botão/FAB da IA aparece mesmo sem o módulo `ia`. | 🔲 | revisões das Tasks 11/13, e2e Task 14, revisão final (M3) |
| QA-1 | Sem testes automatizados | Nenhuma funcionalidade tem teste automático — toda verificação foi manual (curl/navegador) e por revisão de código. Atenção: `npx tsc --noEmit` **não verifica nada** neste repositório (o `tsconfig.json` raiz só tem `references`); use `npm run build` ou `npx tsc -p tsconfig.app.json --noEmit`. Além disso, `npm run lint` ainda reporta 58 erros e 3 avisos pré-existentes (maioria de tipagem `any` e regras de hooks), que não bloqueiam o build. | 🔲 | revisão final |
| API-1 | `id` do payload sobrescreve o gerado | Vários POST/PUT (`clients.py`, `company.py`, `employees.py`, `financial.py`, `kanban.py`, `notifications.py`, `suppliers.py`) ainda montam o dict como `{"id": gerado, **d}`, então um `id` vindo do corpo sobrescreve o gerado pelo servidor. | 🔲 | Verificado 2026-09-10 — ainda presente em 7 endpoints |

---

## P3 — Baixa (cosmético e dívida técnica)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| CSS-1 | Token `--color-warning-container` ausente | Referenciado pela tag de prioridade "ALTA" no Kanban (`Kanban.tsx`) e pelos toasts de aviso (`ToastContext.tsx`), mas nunca definido em `frontend/src/index.css`. | 🔲 | progress.md Task 23 |
| CSS-2 | Contraste das colunas do Kanban | O tema quase-preto comprime as razões de contraste WCAG. Fechar mais exige um novo token mais claro que `surface-container-highest` no design system. | 🔲 | task-23-report |
| SEED-1 | Dados de seed "envelhecem" | As datas do seed são congeladas na primeira execução (o mock antigo recalculava a cada request). Com o tempo, o seed fica com datas defasadas. | 🔲 | progress-db (nota) |
| DB-3 | Sem caminho de migração de schema | `Base.metadata.create_all` cria tabelas novas mas não faz `ALTER` em tabelas existentes. Qualquer coluna nova exige recriar o banco ou migração manual. | 🔲 | revisão final DB |
| DB-4 | Limpeza pós-migração MySQL | `pool_recycle` e FK `ON DELETE SET NULL` já tratados; `app/db/database.py` confirmado removido, sem referências residuais. Falta só a segunda parte: `GET /kanban/projects/{pid}/board` ainda faz uma query por coluna e outra por cartão dentro de loops (N+1), sem `selectinload`/joins. | 🔲 | Verificado 2026-09-10 em `kanban.py::get_board` |

---

## Documentação formal pendente

A partir de [registro-de-alteracoes-para-documentacao.md](registro-de-alteracoes-para-documentacao.md).
Trabalho de reescrita do Escopo / ERS / DAS oficiais:

| ID | Documento | O que atualizar |
|----|-----------|-----------------|
| DOC-1 | Escopo | Modelo de 3 planos (Pessoal / Empresarial / Completo) como novo requisito de negócio; confirmar lista de módulos dos dois Hubs. |
| DOC-2 | ERS | Requisitos funcionais detalhados de cada módulo (CTC, fluxo de caixa D+90, timer em cartão, 10 módulos do Hub Pessoal); requisitos não-funcionais de segurança (segredos fora do código); lista honesta de lacunas (itens P0/P1 deste backlog) como "fora do escopo desta entrega". |
| DOC-3 | DAS | Arquitetura de persistência (SQLAlchemy async, 29 tabelas, seed idempotente); diagrama de implantação com os 4 containers Docker + MySQL; sistema de design de frontend "Obsidian Flow" (rotas por módulo, não abas). |

---

## Concluído (histórico)

Referência do que já foi entregue. Todos os planos em [docs/planejamento/plans/](planejamento/plans/) estão concluídos e aprovados, segundo os registros de andamento de cada fase:

- ✅ **Expansão do frontend** (22 tasks, mais o redesign visual do Kanban): os 10 módulos do Hub Empresarial e do Hub Pessoal, o modelo de conta por plano, tudo passou por QA manual com os 3 papéis.
- ✅ **Correções de design**: a colisão de `max-w` do Tailwind foi resolvida, e o Hub Pessoal ganhou rotas próprias com um alternador Empresarial/Pessoal.
- ✅ **Persistência real** (16 tasks). Saímos de listas em memória para SQLAlchemy async: 28 modelos ORM, seed idempotente e 13 routers migrados.
- ✅ **Troca para MySQL**, via Docker Compose, com MySQL 8 real, segredos fora do compose, `pool_recycle`/`pool_pre_ping`, FK `ON DELETE SET NULL` e e-mail tratado como case-insensitive.
- ✅ **Revisão de segurança**: credenciais tiradas do código-fonte, histórico do Git reescrito e `SECRET_KEY` rotacionada.
- ✅ **Menu de ações da Gestão de Equipe** (EQ-1). Os botões de Histórico, Editar e Desligar já funcionam tanto na visão em lista quanto no menu "⋮" da visão em cartões.
- ✅ **DRE por categoria real** (FIN-1): `GET /financial/dre` passou a agregar receitas e despesas por categoria direto dos lançamentos do banco, sem valores fixos no código.
- ✅ **Limpeza de `app/db/database.py`** (parte de DB-4). O arquivo legado saiu sem deixar referência pendente; só falta resolver o N+1 de `get_board`.
- ✅ **Hierarquia de cargos, painel de conexões e onboarding** (plano `2026-09-08`, cerca de 17 tasks mais os ajustes da revisão final). Permissões configuráveis por empresa com bloqueio real (403) no backend e nas páginas, abas de Hierarquia de Cargos e Conexões de API em Configurações, assistente de 3 passos no primeiro login do admin, criação de logins de Gerente/Funcionário, e o fechamento de `GET/PUT /auth/users` (que antes permitia escalação de privilégio). O limite conhecido que ficou dessa entrega é o MT-1 — ver [spec](planejamento/specs/2026-09-08-role-permissions-onboarding-design.md) e [plano](planejamento/plans/2026-09-08-role-permissions-onboarding-plan.md).
- ✅ **Notificações, busca global e exportação de verdade** (`761afd4`): toasts e modal de confirmação no lugar de `alert()`/`confirm()`, busca do topo ligada ao `/search/`, e exportação que efetivamente gera um arquivo.
