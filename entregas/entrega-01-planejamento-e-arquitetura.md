# Entrega 01 — Planejamento, Arquitetura e MVP Operacional

## 1. Identificação
Entrega 01 — Planejamento, Arquitetura e MVP Operacional (TechConnect 2.0), submetida em agosto de 2026 na disciplina de Projeto Integrador (PI), curso de Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) — CEUB. Equipe: Gabriel Salles, Abner Trindade e o restante da equipe TechConnect.

## 2. Sprint relacionada
Consolidada a partir dos resultados da [Sprint 00](../sprints/sprint-00-planejamento.md) e da [Sprint 01](../sprints/sprint-01.md).

## 3. Escopo entregue

**Documentação:** especificação de requisitos funcionais (RF01 a RF15) e não funcionais (RNF01 a RNF08), o Documento de Arquitetura de Software (DAS) com modelo C4, diagrama entidade-relacionamento e especificação dos POPs de IA, e os registros de decisão ADR 001, ADR 002 e ADR 003.

**MVP funcional:** uma SPA em React 19, TypeScript, Tailwind v4 e o design system Obsidian Flow. No Hub Empresarial, dashboard com DRE e projeção D+90, Kanban com cronômetro e *Cost-per-Task*, gestão de equipe com CTC e histórico salarial, gestão de fornecedores, lançamentos financeiros e exportação. No Hub Pessoal, os 10 módulos de controle financeiro e produtividade pessoal. No backend, uma API REST assíncrona em FastAPI com SQLAlchemy 2.0 e autenticação JWT com Bcrypt, persistindo em MySQL 8.0 (cerca de 28 tabelas nesta entrega) com seed idempotente, tudo orquestrado por Docker Compose em 4 serviços isolados (frontend, API, banco e cache).

## 4. Links principais
- Repositório institucional (CEUB): [CAMPUSCEUB/ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL](https://github.com/CAMPUSCEUB/ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL) — código e documentação vivem aqui.
- Documentação de requisitos: [docs/requisitos.md](../docs/requisitos.md)
- Documento de arquitetura: [docs/arquitetura.md](../docs/arquitetura.md)

## 5. Critérios atendidos
- [x] Rastreabilidade entre os problemas identificados, os requisitos e o código implementado.
- [x] Arquitetura de software formalizada em diagramas e ADRs.
- [x] Repositório estruturado segundo os templates institucionais do CEUB.
- [x] Código-fonte versionado, documentado e pronto para execução via Docker.

## 6. Validação e testes realizados
Testes de API executados e validados via Swagger OpenAPI (`/docs`); testes de integração com o banco, cobrindo a criação automática de tabelas, a inserção do seed idempotente e a integridade dos relacionamentos (`ON DELETE SET NULL`); e um teste manual de ponta a ponta na interface, cobrindo login, navegação por papel, criação de cards, cronômetro e alternância entre PJ e PF.

## 7. Próximos passos
Integrar de fato a API do Gemini nos POPs de IA (hoje ainda respondem por palavras-chave) e detalhar as permissões de RBAC por endpoint — o que acabou sendo entregue, com limites próprios, na Sprint 02 (ver [ADR 004](../docs/decisoes/adr-004-permissoes-por-cargo-e-onboarding.md)).
