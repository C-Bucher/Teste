# Sprint 02 — Controle de Acesso por Cargo, Onboarding e Consolidação do Repositório

## 1. Identificação da Sprint
- **Período:** 08/09/2026 a 21/09/2026
- **Status:** Em revisão (Pull Request aguardando aprovação da equipe)

## 2. Objetivo da Sprint
Tornar o controle de acesso configurável e efetivo no servidor (hierarquia de cargos), guiar a configuração inicial de uma empresa (onboarding), expor o estado das integrações e consolidar código e documentação neste repositório institucional, preservando todo o histórico de desenvolvimento.

## 3. Entregas e Funcionalidades Desenvolvidas

### 3.1 Backend
- Tabela `role_permissions` e colunas `onboarding_completed` / `permissions_customized` em `companies` (29 tabelas no total).
- `app/core/permissions.py` com fonte única `get_allowed_modules` e dependência `require_module`, aplicadas em `employees`, `suppliers`, `financial`, `exports`, `ai` e nas rotas que alteram a empresa (HTTP 403 real).
- Endpoints `GET/PUT /permissions/matrix`, `GET /permissions/mine`, `GET /system/integrations`, `POST /company/onboarding/complete` e `POST /auth/users`.
- Correções de segurança: `GET/PUT /auth/users` restritos ao Admin da mesma empresa (fim da escalação de privilégio), `is_active` exigido, busca (`/search`) filtrada por módulo, `/health` sem checagem falsa de Redis.

### 3.2 Frontend
- Hook `usePermissions`, menu lateral e páginas guardadas por módulo.
- Abas *Hierarquia de Cargos* e *Conexões de API* em Configurações; assistente de onboarding de 3 passos; seção *Acessos ao Sistema* na Gestão de Equipe.

### 3.3 Repositório e documentação
- Histórico completo do desenvolvimento incorporado por merge (nenhum commit perdido); autoria padronizada.
- README unificado, `.gitignore` unificado, ADR 004, RF16–RF19, matriz de atendimento em `docs/requisitos.md`, novo item de backlog MT-2, planejamento das fases em `docs/planejamento/`.

## 4. Limitações Registradas nesta Sprint (transparência)
- **MT-1:** dados de negócio não são separados por empresa.
- **MT-2:** Hub Pessoal não é isolado por usuário (proprietário fixo `usr-001`).
- **SEC-3 / SEC-4 / AUTH-2 / QA-1 / UX-1:** ver [BACKLOG](../docs/BACKLOG.md).

## 5. Evidências de Conclusão
- Verificação ponta a ponta com os três papéis (Admin, Gerente, Funcionário): matriz de permissões, respostas 403, onboarding e criação de usuário.
- Build do frontend (`npm run build`) e backend iniciando com seed automático.
- Especificação e plano: [docs/planejamento](../docs/planejamento) · Decisão: [ADR 004](../docs/decisoes/adr-004-permissoes-por-cargo-e-onboarding.md).
