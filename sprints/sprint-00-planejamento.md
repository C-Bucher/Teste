# Sprint 00 — Planejamento e Concepção do Projeto

## 1. Contexto
Início do Projeto Integrador (PI) do curso de Análise e Desenvolvimento de Sistemas (ADS) no CEUB. A proposta é uma solução de gestão operacional e financeira voltada a PMEs, unindo acompanhamento de tarefas a relatórios financeiros preditivos e um módulo de IA.

## 2. Equipe
Curso de Tecnologia em Análise e Desenvolvimento de Sistemas (ADS), CEUB, disciplina de Projeto Integrador. Equipe: Gabriel Salles, Abner Trindade e o restante da equipe TechConnect.

## 3. Papéis
Product Owner e arquitetura ficaram com Gabriel Salles e Abner Trindade; desenvolvimento full stack, design system/UX e qualidade/documentação ficaram com a equipe como um todo.

## 4. Cadência escolhida
Sprints de 2 semanas, com reuniões semanais de alinhamento e sincronização do backlog, acompanhadas via GitHub Projects e issues vinculadas.

## 5. Problema
Definir com clareza a visão do produto, mapear os requisitos essenciais, especificar o modelo de dados unificado (PJ e PF) e escolher a stack tecnológica adequada para suportar concorrência e persistência relacional, com espaço para IA.

## 6. Objetivo
Entregar a especificação formal de requisitos, o Documento de Arquitetura de Software (DAS), a estrutura inicial dos repositórios e uma prova de conceito do design system Obsidian Flow.

## 7. Riscos mapeados
- Complexidade no cálculo de CTC e de *Cost-per-Task* em tempo real. Mitigação: modelagem matemática clara e testes de unidade nas rotas de cálculo.
- Vazamento acidental de credenciais sensíveis (chaves de API, JWT). Mitigação: uso obrigatório de `.env`, `.gitignore` rigoroso e remoção de segredos do código. (Esse risco de fato se concretizou depois — ver SEC-5 no [BACKLOG](../docs/BACKLOG.md).)
- Limitações de cota ou latência na API de IA. Mitigação: POPs com fallback determinístico local.

## 8. Backlog inicial
- [x] Documento de requisitos (`docs/requisitos.md`)
- [x] Especificação da arquitetura e modelo C4 (`docs/arquitetura.md`)
- [x] Criação do repositório institucional e alinhamento com os padrões do CEUB
- [x] Definição dos POPs de IA (CFO Virtual, Conciliação e Orçamentos)
- [x] Protótipo das telas principais no design system Obsidian Flow

## 9. Acordos de trabalho e Definition of Done (DoD)
Código formatado e tipado (TypeScript no frontend, Pydantic/Python no backend); toda decisão de arquitetura registrada em ADR; commits atômicos e descritivos.
