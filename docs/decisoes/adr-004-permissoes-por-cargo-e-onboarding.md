# ADR 004 — Permissões por Cargo, Onboarding e Painel de Integrações

## Status
Aprovado / Implementado (com limites registrados — ver Consequências)

## Data
2026-09-21

## Contexto
O ADR 002 definiu três papéis (`ADMIN`, `GERENTE`, `FUNCIONARIO`), mas o acesso era decidido por regras fixas no código e, em parte, apenas escondendo itens do menu no frontend. Faltavam: (1) o Admin decidir quais módulos cada cargo enxerga, (2) bloqueio efetivo no servidor, (3) um caminho guiado para configurar uma empresa nova e (4) visibilidade do estado das integrações (banco, IA). Uma revisão também encontrou que `GET/PUT /auth/users` permitiam escalação de privilégio.

## Decisão
1. **Três cargos fixos, permissões editáveis:** os cargos não são criados dinamicamente; o Admin edita, por empresa, uma matriz cargo × módulo (tabela `role_permissions`). Admin tem acesso total e não editável.
2. **Módulos:** `dashboard`, `kanban`, `equipe`, `financeiro`, `fornecedores`, `configuracoes`, `exportacao`, `ia`.
3. **Fonte única de decisão no backend:** `get_allowed_modules(user, db)`; dependência `require_module(chave)` devolve HTTP 403 quando o módulo não está liberado. O frontend (`usePermissions`) apenas reflete a decisão.
4. **Padrão até personalizar:** Gerente (tudo, exceto `configuracoes`) e Funcionário (`dashboard`, `kanban`) valem até a primeira matriz salva (`companies.permissions_customized`); depois, a matriz salva prevalece, mesmo que deixe um cargo sem módulos.
5. **Onboarding no primeiro login do Admin** (3 passos), controlado por `companies.onboarding_completed` e `POST /company/onboarding/complete`.
6. **Painel de conexões** somente leitura (`GET /system/integrations`): estado do banco e presença da chave da IA, sem expor segredos.
7. **Gestão de usuários endurecida:** Admin cria Gerente/Funcionário (`POST /auth/users`); listar/editar usuários é restrito ao Admin, à mesma empresa, a papéis permitidos e a colunas não sensíveis; `is_active` é exigido.

## Alternativas consideradas
- **Cargos totalmente dinâmicos (criar/renomear):** maior flexibilidade, porém exige reescrever o modelo de papéis e o RBAC existente; adiado.
- **Bloqueio apenas no frontend:** rejeitado — não protege a API.
- **Permissões por endpoint em vez de por módulo:** granularidade excessiva para o público-alvo (PMEs); módulos são compreensíveis para o Admin.

## Consequências
- **Positivas:** o bloqueio é verificável (403 real, testado ponta a ponta com os três papéis); a experiência de configuração é guiada; a escalação de privilégio em `/auth/users` foi fechada.
- **Limites conhecidos (não resolvidos por esta decisão):**
  - **MT-1:** dados de negócio (funcionários, lançamentos, Kanban, clientes, fornecedores) não são separados por empresa; as permissões o são.
  - **MT-2:** o Hub Pessoal usa um proprietário fixo (`usr-001`) em vez do usuário autenticado — a premissa de isolamento do ADR 002 ainda **não** é cumprida.
  - **SEC-3:** Kanban, clientes, notificações, planos, pagamentos e Hub Pessoal não têm gate por módulo; as permissões `dashboard` e `kanban` controlam só o menu.
  - Mudança de cargo reflete no menu somente após novo login (o backend reflete imediatamente) — SEC-4.

## Links relacionados
- Especificação: [docs/planejamento/specs/2026-09-08-role-permissions-onboarding-design.md](../planejamento/specs/2026-09-08-role-permissions-onboarding-design.md)
- Plano: [docs/planejamento/plans/2026-09-08-role-permissions-onboarding-plan.md](../planejamento/plans/2026-09-08-role-permissions-onboarding-plan.md)
- Requisitos: RF16–RF19 em [docs/requisitos.md](../requisitos.md)
- Backlog: [MT-1, MT-2, SEC-3, SEC-4, AUTH-2](../BACKLOG.md)
- Decisão anterior: [ADR 002](adr-002-arquitetura-hub-duplo-plan-scope.md)
