# Histórico de mudanças

Registre aqui as mudanças relevantes por sprint ou marco avaliativo.

## Sprint 00 - Planejamento

- Criação do repositório.
- Definição do problema, da equipe, dos papéis e do backlog inicial.

## Sprint 01 - MVP e Persistência Relacional

- Hub Empresarial e Hub Pessoal no frontend (React 19 + Tailwind v4, design Obsidian Flow).
- Backend FastAPI com SQLAlchemy 2.0 assíncrono, seed idempotente e Docker Compose (MySQL, Redis, backend, frontend).
- Segredos migrados para `.env`.

## Sprint 02 - Controle de Acesso por Cargo e Onboarding

- Hierarquia de cargos configurável com bloqueio real (HTTP 403) no servidor e nas páginas (RF16, [ADR 004](docs/decisoes/adr-004-permissoes-por-cargo-e-onboarding.md)).
- Onboarding guiado de 3 passos, painel de conexões de API e criação de logins pelo Admin (RF17–RF19).
- Correções de segurança em `/auth/users` (escalação de privilégio), `is_active` exigido, busca filtrada por módulo.
- Repositório consolidado: código e histórico completo incorporados, README e `.gitignore` unificados, documentação atualizada com a matriz de atendimento dos requisitos.
- Registradas como pendências: MT-1 (dados de negócio por empresa) e MT-2 (Hub Pessoal por usuário) — ver [BACKLOG](docs/BACKLOG.md).

