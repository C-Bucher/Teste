# Entrega 01 — Planejamento, Arquitetura e MVP Operacional

## 1. Identificação
- **Título:** Entrega 01 — Planejamento, Arquitetura e MVP Operacional (TechConnect 2.0)
- **Data de Submissão:** Agosto / 2026
- **Curso / Turma:** Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) — CEUB
- **Disciplina:** Projeto Integrador (PI)
- **Equipe:** Gabriel Salles, Abner Trindade e equipe TechConnect

## 2. Sprint Relacionada
- Consolidada a partir dos resultados da [Sprint 00](../sprints/sprint-00-planejamento.md) e [Sprint 01](../sprints/sprint-01.md).

## 3. Escopo Entregue
1. **Documentação Acadêmica e Arquitetural Completa:**
   - Especificação de Requisitos Funcionais (RF01 a RF15) e Não-Funcionais (RNF01 a RNF08).
   - Documento de Arquitetura de Software (DAS) com Modelo C4, Diagrama Entidade-Relacionamento e especificações dos POPs de IA.
   - Registros de Decisões de Arquitetura (ADR 001, ADR 002 e ADR 003).
2. **Solução de Software Implementada (MVP Funcional):**
   - **Frontend:** SPA moderna em React 19 + TypeScript + Tailwind v4 + Obsidian Flow Design System.
   - **Hub Empresarial:** Dashboard com DRE e D+90, Kanban com cronômetro e *Cost-per-Task*, Gestão de Equipe com CTC e histórico salarial, Gestão de Fornecedores, Lançamentos Financeiros e Exportação.
   - **Hub Pessoal:** 10 módulos funcionais para controle de finanças e produtividade individual.
   - **Backend Assíncrono:** API REST em FastAPI com SQLAlchemy 2.0 Async, autenticação JWT com Bcrypt.
   - **Persistência Real:** Banco relacional MySQL 8.0 com ~28 tabelas e seed idempotente.
   - **Infraestrutura:** Docker Compose com 4 serviços isolados (Web, API, DB, Cache).

## 4. Links Principais
- **Repositório Institucional (CEUB):** [CAMPUSCEUB/ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL](https://github.com/CAMPUSCEUB/ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL)
- **Repositório do Código-Fonte:** [gabrielsalles-bit/TechConnect2.0](https://github.com/gabrielsalles-bit/TechConnect2.0)
- **Documentação de Requisitos:** [docs/requisitos.md](../docs/requisitos.md)
- **Documento de Arquitetura:** [docs/arquitetura.md](../docs/arquitetura.md)

## 5. Critérios Atendidos
- [x] Rastreabilidade entre problemas identificados, requisitos e código implementado.
- [x] Arquitetura de software formalizada em diagramas e ADRs.
- [x] Repositório estruturado segundo os templates institucionais do CEUB.
- [x] Código-fonte versionado, documentado e pronto para execução via Docker.

## 6. Validação e Testes Realizados
- **Testes de API:** Executados e validados via Swagger OpenAPI (`/docs`).
- **Testes de Integração com Banco:** Validação de criação automática de tabelas, inserção de seeds idempotentes e relacionamentos com integridade (`ON DELETE SET NULL`).
- **Testes de Interface:** Validação de fluxo de ponta a ponta (login, navegação por papéis, criação de cards, cronômetro, alternância PJ/PF).

## 7. Próximos Passos
- Refinar a integração com a API Gemini para os POPs de IA generativa em produção.
- Implementação de granularidade de permissões de RBAC diretamente em cada endpoint da API.
