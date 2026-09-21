# TechConnect 2.0 — Dashboard para Gestão Operacional & CFO Virtual IA

Repositório institucional de Projeto Integrador do curso de Análise e Desenvolvimento de Sistemas (ADS) — CEUB. Contém **o código-fonte completo da solução** e toda a documentação de engenharia (requisitos, arquitetura, ADRs, sprints e entregas).

> **Professor(a):** Repositório estruturado conforme as diretrizes institucionais do CEUB, com rastreabilidade de requisitos, arquitetura técnica, ADRs (Architecture Decision Records), histórico de sprints e registros de entregas. A seção [Limitações conhecidas](#%EF%B8%8F-limitações-conhecidas) e a *matriz de atendimento* em [docs/requisitos.md](docs/requisitos.md) informam, com transparência, o que está pronto, parcial ou pendente.
>
> **Estudante:** Consulte o backlog, as especificações arquiteturais e o guia de execução em [docs/arquitetura.md](docs/arquitetura.md), [docs/requisitos.md](docs/requisitos.md) e [docs/BACKLOG.md](docs/BACKLOG.md).

---

## 📌 Identificação do Repositório

| Campo | Informação |
|---|---|
| **Instituição** | Centro Universitário de Brasília — CEUB |
| **Curso** | Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) |
| **Disciplina** | Projeto Integrador (PI) |
| **Organização no GitHub** | CampusCEUB |
| **Repositório** | `ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL` (documentação **e** código da solução) |
| **Nome da Solução** | TechConnect 2.0 — CFO Virtual & Gestão Operacional |
| **Equipe** | Equipe TechConnect (Gabriel Salles, Abner Trindade, Caio Alexandre, Andrei Maciel) |

---

## 🎯 Problema

Pequenas e Médias Empresas (PMEs) e profissionais autônomos enfrentam sérias dificuldades para manter o controle sincronizado entre a **operação diária** (projetos, tarefas, tempo de equipe, fornecedores) e o **impacto financeiro** (fluxo de caixa, DRE, custo real por tarefa - *Cost-per-Task* e cálculo de CTC/encargos). A fragmentação de dados em planilhas desconexas resulta em:
1. Desconhecimento do custo operacional real por projeto ou cliente.
2. Dificuldade na tomada de decisões financeiras estratégicas em tempo hábil.
3. Mistura frequente entre as finanças da pessoa jurídica (PJ) e da pessoa física (PF).

---

## 💡 Solução Proposta

O **TechConnect 2.0** é uma plataforma integrada de gestão operacional e financeira que une:
- **Hub Empresarial (ERP para PMEs):** Dashboard executivo com DRE e Fluxo de Caixa, quadro Kanban de projetos com *Cost-per-Task* e cronômetro, Gestão de Equipes com CTC e histórico salarial, Fornecedores, Lançamentos Financeiros e Exportação de Relatórios.
- **Hub Pessoal (Finanças Pessoais):** Visão Geral, Contas & Cartões, Orçamentos, Metas, Dívidas/Parcelamentos, Assinaturas Recorrentes, Divisão de Despesas (*Split*) e OKRs/Timeboxes.
- **Módulo de IA (CFO Virtual):** assistente baseado em POPs (Procedimentos Operacionais Padrão) — hoje respondendo por palavras-chave, com integração a um modelo generativo (Google Gemini) prevista no backlog (IA-1).
- **Controle de acesso por cargo configurável:** Admin, Gerente e Funcionário, com módulos liberados por cargo e bloqueio real no servidor (HTTP 403).
- **Design System Obsidian Flow:** interface em Dark Mode / Glassmorphism (React 19 + Tailwind CSS v4 + Framer Motion).
- **Backend assíncrono e persistente:** FastAPI + SQLAlchemy 2.0, banco relacional real (MySQL 8 no Docker, SQLite na execução manual) e orquestração via Docker Compose.

---

## ✨ Funcionalidades

- **Dois modos de conta**: planos Pessoal, Empresarial e Completo, com Hub Empresarial e Hub Pessoal alternáveis pelo mesmo usuário.
- **Kanban interativo** com Drag & Drop, **Gestão de Equipes** (CRUD com modais), **Fornecedores**, **Financeiro** (DRE, fluxo de caixa, lançamentos) e **Exportação** de relatórios.
- **Controle de Acesso por Papel configurável**: o Admin escolhe em *Configurações → Hierarquia de Cargos* quais módulos cada cargo acessa; o bloqueio vale no servidor (403), não só no menu.
- **Onboarding guiado**: no primeiro login, o Admin de uma empresa nova passa por um assistente de 3 passos (dados da empresa → hierarquia de cargos → conexões de API).
- **Painel de Conexões de API**: mostra se o banco está online e se a chave da IA está configurada.
- **Criação de logins pelo Admin** (Gestão de Equipe → Acessos ao Sistema), com cargo Gerente ou Funcionário.

---

## 🛠 Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router v7, Framer Motion, Axios, Recharts |
| Backend | FastAPI (Python), Pydantic, SQLAlchemy 2.0 (async), Uvicorn — 29 tabelas, seed idempotente |
| Banco de dados | MySQL 8.0 (Docker Compose) · SQLite (execução manual, padrão) |
| Infraestrutura | Docker & Docker Compose; segredos via `.env` (nunca commitado) |
| Redis 7 | provisionado no Compose, **ainda não utilizado** pela aplicação (reservado para cache/filas) |

---

## ⚙️ Como Executar

### 0. Variáveis de ambiente (Docker)
```bash
cp .env.example .env
```
Edite o `.env` e defina `SECRET_KEY` (gere com `python -c "import secrets; print(secrets.token_hex(32))"`), `GEMINI_API_KEY` (opcional; [Google AI Studio](https://aistudio.google.com/app/apikey)) e as credenciais do MySQL. O `.env` nunca deve ser commitado.

### Opção 1 — Docker Compose (recomendado)
```bash
docker-compose up -d
docker ps
```
Na primeira subida o backend cria o schema no MySQL e popula os dados de demonstração (seed idempotente).

| Serviço  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173       |
| Backend  | http://localhost:8000       |
| API Docs | http://localhost:8000/docs  |
| MySQL    | localhost:3307              |
| Redis    | localhost:6379              |

Para parar: `docker-compose down`.

### Opção 2 — Execução manual (sem Docker)
> Sem Docker o backend usa um **SQLite local** (`techconnect.db`, criado e populado automaticamente) — não precisa de MySQL nem de `.env`. Para outro banco, exporte `DATABASE_URL`.

**Backend (FastAPI)** — na raiz do projeto:
```bash
python -m venv venv
venv\Scripts\activate          # Windows  |  Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (React + Vite)** — em outro terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend em `http://localhost:5173`, API em `http://localhost:8000`.

---

## 🔑 Acessos de Teste

| Papel        | E-mail                              | Senha         |
|--------------|-------------------------------------|---------------|
| Admin        | `admin@techconnect.com.br`          | `Admin@123`   |
| Gerente      | `gerente@techconnect.com.br`        | `Gerente@123` |
| Funcionário  | `funcionario@techconnect.com.br`    | `Func@123`    |

### Permissões por papel
- **Admin**: acesso total e fixo a todos os módulos; único que cria logins, edita a matriz de permissões e vê o status das integrações.
- **Gerente** (padrão): Dashboard, Projetos, Equipe, Financeiro, Fornecedores, Exportação e IA Empresarial — **sem** Configurações.
- **Funcionário** (padrão): Dashboard e Projetos.

O padrão vale até o Admin salvar uma matriz própria em *Configurações → Hierarquia de Cargos*; depois disso a matriz salva prevalece (inclusive se deixar um cargo sem módulos).

---

## ⚠️ Limitações conhecidas

Registradas abertamente para que a avaliação reflita o estado real do sistema (detalhes e prioridades em [docs/BACKLOG.md](docs/BACKLOG.md)):

- **Dados de negócio não são isolados por empresa** (MT-1): empresas, usuários e permissões são separados por empresa, mas funcionários, lançamentos, projetos, clientes, fornecedores, notificações e exportações formam um conjunto único.
- **Hub Pessoal não é isolado por usuário** (MT-2): as rotas usam um proprietário fixo (`usr-001`); todos os usuários logados enxergam os mesmos dados pessoais, embora as tabelas já tenham a coluna `owner_id`.
- **Sem gate por módulo** em Kanban, clientes, notificações, planos, pagamentos e Hub Pessoal (SEC-3); as permissões *Dashboard* e *Projetos* controlam apenas o menu.
- **IA por palavras-chave** (IA-1): não há modelo generativo real; sem sanitização de dados sensíveis para LGPD.
- Sem 2FA, sem auditoria e sem suíte de testes automatizados (o `test_api.py` é um script manual de fumaça).
- Verificação do frontend: use `npm run build` (ou `npx tsc -p tsconfig.app.json --noEmit`); `npx tsc --noEmit` sozinho não checa nada neste projeto.

---

## 🗂 Estrutura do Repositório

```
.
├── app/                        # Backend FastAPI
│   ├── api/v1/endpoints/       # Rotas (auth, company, permissions, system, financial, kanban, employees, personal...)
│   ├── core/                   # Segurança (JWT), configuração e permissões por módulo (permissions.py)
│   └── db/                     # models.py (29 tabelas), session.py, seed.py, utils.py
├── frontend/src/               # Frontend React + Vite
│   ├── components/             # Layout, PermissionMatrix, IntegrationsStatus, SystemAccessSection, modais
│   ├── context/                # Toasts e confirmação
│   ├── hooks/                  # usePermissions
│   └── pages/                  # Hub Empresarial, Hub Pessoal, Configurações, Onboarding, Login/Cadastro
├── architecture/               # POPs de IA (CFO Virtual, Conciliação, Orçamentos)
├── docs/                       # Requisitos, arquitetura, ADRs, BACKLOG, reuniões, planejamento
├── sprints/  entregas/         # Sprints e relatórios de entrega
├── docker-compose.yml  Dockerfile  .env.example  requirements.txt
├── main.py                     # Atalho para subir o backend
├── seed_financial_history.py   # Script avulso: 5 meses de lançamentos históricos (demo)
└── test_api.py                 # Script manual de fumaça da API
```

## 📚 Documentação

| Item | Descrição | Link |
|---|---|---|
| **Requisitos** | RF, RNF, critérios de aceitação e matriz de atendimento | [docs/requisitos.md](docs/requisitos.md) |
| **Arquitetura** | Componentes, modelo de dados, autorização e endpoints | [docs/arquitetura.md](docs/arquitetura.md) |
| **ADRs** | Registros de decisões de arquitetura | [docs/decisoes/README.md](docs/decisoes/README.md) |
| **Backlog** | Backlog priorizado (P0–P3) com estado real | [docs/BACKLOG.md](docs/BACKLOG.md) |
| **Registro de alterações** | Tudo o que foi implementado por área | [docs/registro-de-alteracoes-para-documentacao.md](docs/registro-de-alteracoes-para-documentacao.md) |
| **Planejamento** | Specs e planos de execução por fase | [docs/planejamento](docs/planejamento) |
| **Sprints** | Planejamento e Definition of Done | [sprints/README.md](sprints/README.md) |
| **Entregas** | Relatórios de entregas e evidências | [entregas/README.md](entregas/README.md) |
| **Reuniões** | Atas e alinhamentos | [docs/reunioes/README.md](docs/reunioes/README.md) |
| **Changelog** | Histórico de mudanças | [CHANGELOG.md](CHANGELOG.md) |
| **Contribuição / Segurança** | Guias do repositório | [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) |

---
*Desenvolvido com foco em inovação, UX e escalabilidade.*
