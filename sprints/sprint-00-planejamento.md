# Sprint 00 — Planejamento e Concepção do Projeto

## 1. Contexto
Início do Projeto Integrador (PI) do curso de Análise e Desenvolvimento de Sistemas (ADS) no CEUB. A proposta é desenvolver uma solução integrada de gestão operacional e financeira com foco em PMEs, suprindo a carência de ferramentas que unam acompanhamento ágil de tarefas a relatórios financeiros preditivos e inteligência artificial.

## 2. Equipe
- **Curso:** Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) — CEUB
- **Disciplina:** Projeto Integrador
- **Membros:** Gabriel Salles, Abner Trindade e equipe de desenvolvimento

## 3. Papéis
- **Product Owner & Arquitetura:** Gabriel Salles / Abner Trindade
- **Desenvolvimento Full Stack:** Equipe TechConnect
- **Design System & UX:** Equipe TechConnect
- **Qualidade e Documentação:** Equipe TechConnect

## 4. Cadência Escolhida
- **Duração da Sprint:** 2 semanas
- **Checkpoints:** Reuniões semanais de alinhamento e sincronização de backlog
- **Acompanhamento:** GitHub Projects e issues vinculadas

## 5. Problema
Definir com clareza a visão do produto, mapear os requisitos essenciais, especificar o modelo de dados unificado (PJ e PF) e estabelecer a stack tecnológica mais adequada para suportar alta concorrência e persistência relacional com IA.

## 6. Objetivo
Entregar a especificação formal de requisitos, o Documento de Arquitetura de Software (DAS), a estrutura inicial dos repositórios e a prova de conceito do design system Obsidian Flow.

## 7. Riscos Mapeados
- **Risco 01:** Complexidade no cálculo de CTC e *Cost-per-Task* em tempo real.  
  *Mitigação:* Modelagem matemática clara e testes de unidade nas rotas de cálculo.
- **Risco 02:** Vazamento acidental de credenciais sensíveis (chaves de API e JWT).  
  *Mitigação:* Adoção mandatória de `.env`, `.gitignore` rigoroso e remoção de segredos do código.
- **Risco 03:** Limitações de cota ou latência na API de IA.  
  *Mitigação:* Implementação de POPs com fallback determinístico local.

## 8. Backlog Inicial
- [x] Elaboração do documento de requisitos (`docs/requisitos.md`)
- [x] Especificação da arquitetura e modelo C4 (`docs/arquitetura.md`)
- [x] Criação do repositório institucional e alinhamento com os padrões do CEUB
- [x] Definição dos POPs de IA (CFO Virtual, Conciliação e Orçamentos)
- [x] Prototipação das telas principais no Design System Obsidian Flow

## 9. Acordos de Trabalho e Definition of Done (DoD)
- Código formatado e tipado (TypeScript no Frontend, Pydantic/Python no Backend).
- Toda decisão de arquitetura deve ser documentada em ADR.
- Commits atômicos e descritivos.
