# Registros de Decisões Arquiteturais (ADRs)

Esta pasta documenta o histórico de decisões técnicas, de arquitetura e de design tomadas ao longo da concepção e evolução do **TechConnect 2.0**.

---

## 📋 Lista de ADRs

| ADR | Título | Status | Data |
|---|---|---|---|
| [ADR 001](adr-001-stack-fastapi-mysql-sqlalchemy.md) | Adoção de FastAPI, SQLAlchemy 2.0 Assíncrono e MySQL 8.0 | Aprovado | 2026-08-15 |
| [ADR 002](adr-002-arquitetura-hub-duplo-plan-scope.md) | Arquitetura de Hub Duplo com Controle por Plan Scope e RBAC | Aprovado | 2026-08-18 |
| [ADR 003](adr-003-design-system-obsidian-flow.md) | Design System Obsidian Flow e Stack Frontend (React 19 + Tailwind v4) | Aprovado | 2026-08-19 |
| [ADR 004](adr-004-permissoes-por-cargo-e-onboarding.md) | Permissões por Cargo, Onboarding e Painel de Integrações | Aprovado | 2026-09-21 |
| [ADR 005](adr-005-suporte-postgresql-supabase.md) | Suporte a PostgreSQL Gerenciado (Supabase) como Banco Padrão | Aprovado, com pendências (SEC-5, DB-5) | 2026-09-23 |

---

## 📝 Como Criar um Novo ADR
Para propor uma nova decisão arquitetural, copie o arquivo [template-adr.md](template-adr.md) para um novo arquivo sequencial (ex: `adr-004-nome-do-topico.md`) e submeta via Pull Request para revisão da equipe.
