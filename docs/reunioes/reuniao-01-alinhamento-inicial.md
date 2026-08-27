# Ata de Reunião 01 — Alinhamento de Escopo, Arquitetura e Stack

## 1. Informações Gerais
- **Data:** 05 de Agosto de 2026
- **Horário:** 19:30 - 21:00
- **Local / Plataforma:** Google Meet / Discord
- **Participantes:** Gabriel Salles, Abner Trindade e equipe de desenvolvimento

## 2. Pauta da Reunião
1. Definição do escopo do Projeto Integrador (Dashboard para Gestão Operacional e Financeira).
2. Escolha da stack tecnológica (Frontend React 19 + Tailwind v4, Backend FastAPI + SQLAlchemy 2.0 Async, Banco MySQL 8.0).
3. Concepção do modelo de negócio (Hub Empresarial + Hub Pessoal com alternador de planos).
4. Estruturação dos POPs para o módulo de IA (CFO Virtual com Gemini).
5. Definição da divisão de tarefas e cronograma de entregas conforme os templates do CEUB.

## 3. Decisões Tomadas
- Aprovada a adoção do design system Obsidian Flow (Glassmorphism e Dark Mode nativo).
- Definida a persistência em MySQL 8.0 com seed idempotente para facilitar a avaliação acadêmica.
- Aprovada a modelagem relacional separando dados corporativos (`company_id`) de dados pessoais (`owner_id`).
- Formalização das decisões em ADRs no repositório institucional.

## 4. Ações e Próximos Passos
| Tarefa | Responsável | Prazo |
|---|---|---|
| Criação dos modelos SQLAlchemy e migração das rotas de API | Gabriel Salles | Sprint 01 |
| Estruturação do Design System e Telas do Hub Empresarial/Pessoal | Abner Trindade | Sprint 01 |
| Preenchimento da documentação formal de Requisitos e Arquitetura no repositório CEUB | Equipe | Sprint 01 |
