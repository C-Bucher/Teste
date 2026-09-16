# TechConnect 2.0 — Dashboard para Gestão Operacional & CFO Virtual IA

Repositório institucional de Projeto Integrador do curso de Análise e Desenvolvimento de Sistemas (ADS) — CEUB.

> **Professor(a):** Repositório estruturado conforme as diretrizes institucionais do CEUB, contendo rastreabilidade total de requisitos, arquitetura técnica, ADRs (Architecture Decision Records), histórico de sprints e registros de entregas.
>
> **Estudante:** Consulte o backlog, as especificações arquiteturais e o guia de execução do sistema em [docs/arquitetura.md](docs/arquitetura.md) e [docs/requisitos.md](docs/requisitos.md).

---

## 📌 Identificação do Repositório

| Campo | Informação |
|---|---|
| **Instituição** | Centro Universitário de Brasília — CEUB |
| **Curso** | Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) |
| **Disciplina** | Projeto Integrador (PI) |
| **Organização no GitHub** | CampusCEUB |
| **Repositório Institucional** | `ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL` |
| **Repositório da Solução (Código)** | [gabrielsalles-bit/TechConnect2.0](https://github.com/gabrielsalles-bit/TechConnect2.0) |
| **Nome da Solução** | TechConnect 2.0 — CFO Virtual & Gestão Operacional |
| **Equipe** | Equipe TechConnect (Gabriel Salles, Abner Trindade , Caio Alexandre, Andrei Maciel) |

---

## 🎯 Problema

Pequenas e Médias Empresas (PMEs) e profissionais autônomos enfrentam sérias dificuldades para manter o controle sincronizado entre a **operação diária** (projetos, tarefas, tempo de equipe, fornecedores) e o **impacto financeiro** (fluxo de caixa, DRE, custo real por tarefa - *Cost-per-Task* e cálculo de CTC/encargos). A fragmentação de dados em planilhas desconexas resulta em:
1. Desconhecimento do custo operacional real por projeto ou cliente.
2. Dificuldade na tomada de decisões financeiras estratégicas em tempo hábil.
3. Mistura frequente entre as finanças da pessoa jurídica (PJ) e da pessoa física (PF).

---

## 💡 Solução Proposta

O **TechConnect 2.0** é uma plataforma integrada de gestão operacional e financeira inteligente que une:
- **Hub Empresarial (ERP para PMEs):** Dashboard executivo com DRE e Fluxo de Caixa D+90, quadro Kanban de projetos com cálculo de *Cost-per-Task* e cronômetro em tempo real, Gestão de Equipes com cálculo de CTC (Custo Total ao Colaborador) e histórico salarial, Gestão de Fornecedores, Lançamentos Financeiros e Exportação de Relatórios.
- **Hub Pessoal (Finanças Pessoais):** Módulos completos de Visão Geral, Contas & Cartões, Orçamentos, Metas, Dívidas/Parcelamentos, Assinaturas Recorrentes, Divisão de Despesas (*Split*) e OKRs/Timeboxes.
- **Módulo de IA (CFO Virtual):** Módulo de IA baseado em POPs (Procedimentos Operacionais Padrão) e Google Gemini para análise de DRE, detecção de desvios operacionais e geração de orçamentos.
- **Design System Obsidian Flow:** Interface moderna em Dark Mode / Glassmorphism de alta produtividade (React 19 + Tailwind CSS v4 + Framer Motion).
- **Arquitetura Escalável & Segura:** Backend assíncrono em FastAPI + SQLAlchemy 2.0, persistência relacional em MySQL 8.0 real, cache Redis e orquestração completa via Docker Compose.

---

## 🗂 Estrutura deste Repositório

| Item | Descrição | Link |
|---|---|---|
| **Requisitos** | Requisitos Funcionais, Não-Funcionais e Critérios de Aceitação | [docs/requisitos.md](docs/requisitos.md) |
| **Arquitetura** | Modelo C4, Componentes, Diagrama de Dados e Decisões Técnicas | [docs/arquitetura.md](docs/arquitetura.md) |
| **Decisões Arquiteturais (ADRs)** | Registros de decisões de arquitetura e tecnologia | [docs/decisoes/README.md](docs/decisoes/README.md) |
| **Sprints** | Planejamento, acompanhamento e Definition of Done das Sprints | [sprints/README.md](sprints/README.md) |
| **Entregas** | Relatórios de entregas avaliativas e evidências | [entregas/README.md](entregas/README.md) |
| **Reuniões** | Atas e alinhamentos de equipe | [docs/reunioes/README.md](docs/reunioes/README.md) |

---

## 🚀 Como Executar a Aplicação (TechConnect 2.0)

A implementação completa do sistema encontra-se no repositório da solução. Para execução rápida via Docker:

```bash
# 1. Clonar o repositório da solução
git clone https://github.com/gabrielsalles-bit/TechConnect2.0.git
cd TechConnect2.0

# 2. Configurar variáveis de ambiente
cp .env.example .env

# 3. Subir todos os serviços (MySQL, Redis, Backend FastAPI e Frontend React)
docker-compose up -d
```

Acessos:
- **Frontend Web:** `http://localhost:5173`
- **Backend API Docs (Swagger):** `http://localhost:8000/docs`
- **Credenciais de Teste:** `admin@techconnect.com.br` / `Admin@123`
