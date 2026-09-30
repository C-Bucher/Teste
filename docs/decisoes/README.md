# Registros de Decisões Arquiteturais (ADRs)

Esta pasta reúne as decisões técnicas, de arquitetura e de design tomadas ao longo do desenvolvimento do TechConnect 2.0.

---

## Lista de ADRs

| ADR | Título | Status | Data |
|---|---|---|---|
| [ADR 001](adr-001-stack-fastapi-mysql-sqlalchemy.md) | Adoção de FastAPI, SQLAlchemy 2.0 Assíncrono e MySQL 8.0 | Aprovado | 2026-08-15 |
| [ADR 002](adr-002-arquitetura-hub-duplo-plan-scope.md) | Arquitetura de Hub Duplo com Controle por Plan Scope e RBAC | Aprovado | 2026-08-18 |
| [ADR 003](adr-003-design-system-obsidian-flow.md) | Design System Obsidian Flow e Stack Frontend (React 19 + Tailwind v4) | Aprovado | 2026-08-19 |
| [ADR 004](adr-004-permissoes-por-cargo-e-onboarding.md) | Permissões por Cargo, Onboarding e Painel de Integrações | Aprovado | 2026-09-21 |
| [ADR 005](adr-005-suporte-postgresql-supabase.md) | Suporte a PostgreSQL Gerenciado (Supabase) como Banco Padrão | Aprovado, com pendências (SEC-5, DB-5) | 2026-09-23 |
| [ADR 006](adr-006-isolamento-e-persistencia-operacional.md) | Isolamento de Dados e Persistência Operacional | Aceito | 2026-09-23 |
| [ADR 007](adr-007-endurecimento-autenticacao-migracoes-auditoria.md) | Endurecimento de Autenticação, Migrações Versionadas e Auditoria | Aceito | 2026-09-30 |

---

## Como criar um novo ADR
Copie o arquivo [template-adr.md](template-adr.md) para um novo arquivo sequencial (por exemplo, `adr-006-nome-do-topico.md`) e submeta via pull request para revisão da equipe.
