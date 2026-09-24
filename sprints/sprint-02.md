# Sprint 02 — Controle de Acesso por Cargo, Onboarding e Consolidação do Repositório

## 1. Identificação da sprint
Período de 08/09/2026 a 21/09/2026. Status: concluída (mergeada na `main` via pull request).

## 2. Objetivo da sprint
Tornar o controle de acesso configurável e efetivo no servidor (hierarquia de cargos), guiar a configuração inicial de uma empresa (onboarding), expor o estado das integrações e consolidar código e documentação neste repositório institucional, preservando todo o histórico de desenvolvimento.

## 3. Entregas e funcionalidades desenvolvidas

### 3.1 Backend
Nova tabela `role_permissions` e colunas `onboarding_completed`/`permissions_customized` em `companies` (29 tabelas no total). `app/core/permissions.py` centraliza a decisão em `get_allowed_modules`, com a dependência `require_module` aplicada em `employees`, `suppliers`, `financial`, `exports`, `ai` e nas rotas que alteram a empresa, devolvendo HTTP 403 de verdade. Endpoints novos: `GET/PUT /permissions/matrix`, `GET /permissions/mine`, `GET /system/integrations`, `POST /company/onboarding/complete` e `POST /auth/users`. No caminho, corrigimos `GET/PUT /auth/users` (que não tinham autorização nenhuma, permitindo escalação de privilégio), passamos a exigir `is_active`, filtramos a busca (`/search`) por módulo e tiramos do `/health` uma checagem de Redis que não refletia a realidade.

### 3.2 Frontend
Hook `usePermissions`, menu lateral e páginas protegidas por módulo. Abas de Hierarquia de Cargos e Conexões de API em Configurações, assistente de onboarding de 3 passos, e uma seção de Acessos ao Sistema na Gestão de Equipe.

### 3.3 Repositório e documentação
O histórico completo de desenvolvimento foi incorporado por merge, sem perder nenhum commit, com a autoria padronizada. README e `.gitignore` unificados, ADR 004 registrada, RF16–RF19 adicionados, matriz de atendimento criada em `docs/requisitos.md`, novo item MT-2 no backlog, e o histórico de planejamento das fases preservado em `docs/planejamento/`.

## 4. Limitações registradas nesta sprint
- MT-1: dados de negócio não são separados por empresa.
- MT-2: o Hub Pessoal não é isolado por usuário (usa um proprietário fixo, `usr-001`).
- SEC-3, SEC-4, AUTH-2, QA-1 e UX-1 estão detalhados no [BACKLOG](../docs/BACKLOG.md).

## 5. Evidências de conclusão
- Verificação ponta a ponta com os três papéis (Admin, Gerente, Funcionário): matriz de permissões, respostas 403, onboarding e criação de usuário.
- Build do frontend (`npm run build`) e backend subindo com seed automático.
- Especificação e plano em [docs/planejamento](../docs/planejamento); decisão registrada na [ADR 004](../docs/decisoes/adr-004-permissoes-por-cargo-e-onboarding.md).

## 6. Nota
O suporte a PostgreSQL/Supabase (ADR 005) e a correção do incidente de credencial associado (SEC-5) foram feitos dois dias depois do fechamento desta sprint, já direto na `main`, e estão registrados no [CHANGELOG](../CHANGELOG.md) e no [BACKLOG](../docs/BACKLOG.md).
