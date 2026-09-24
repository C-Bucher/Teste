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
- **Backend assíncrono e persistente:** FastAPI + SQLAlchemy 2.0, banco relacional real — PostgreSQL gerenciado via Supabase (padrão em `.env.example`), MySQL 8 via Docker ou SQLite como fallback local — com orquestração via Docker Compose para a opção MySQL.

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
| Backend | FastAPI (Python), Pydantic, SQLAlchemy 2.0 (async via `asyncpg`), Uvicorn — 29 tabelas, seed idempotente |
| Banco de dados | PostgreSQL gerenciado (Supabase, via Connection Pooler) · MySQL 8.0 (Docker) · SQLite (fallback local) |
| Infraestrutura | Docker & Docker Compose; segredos e credenciais via `.env` (ignorado pelo Git) |
| Redis 7 | provisionado no Compose, **ainda não utilizado** pela aplicação (reservado para cache/filas) |

---

## ⚙️ Como Executar

### 0. Variáveis de ambiente (.env)
```bash
cp .env.example .env
```
Edite o arquivo `.env` com suas credenciais (nunca use valores reais neste README ou em qualquer arquivo versionado — veja [`.env.example`](.env.example) para o formato). Para conectar ao **Supabase**, defina a connection string do pooler:
```env
DATABASE_URL=postgresql+asyncpg://postgres.<PROJECT_REF>:<SENHA_URL_ENCODED>@aws-0-us-east-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://<PROJECT_REF>.supabase.co
SUPABASE_ANON_KEY=<sua-anon-key>
SECRET_KEY=<gere-com-o-comando-abaixo>
```
> *Nota:* A senha do banco no pooler requer URL-encoding para caracteres especiais (ex: `@` torna-se `%40`). Gere `SECRET_KEY` com `python -c "import secrets; print(secrets.token_hex(32))"`.

### Opção 1 — Execução com Supabase (Recomendado)
**Backend (FastAPI)**:
```bash
python -m venv venv
venv\Scripts\activate          # Windows  |  Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Na primeira inicialização com o Supabase, o backend cria automaticamente as 29 tabelas relacionais e executa a carga de dados inicial (seed idempotente).

**Frontend (React + Vite)** — em outro terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend disponível em `http://localhost:5173` e API em `http://localhost:8000`.

### Opção 2 — Docker Compose (MySQL)
> **Importante:** `.env.example` traz a `DATABASE_URL` do Supabase **ativa** por padrão. Para usar o MySQL do Compose, comente a linha `DATABASE_URL=postgresql+asyncpg://...` e descomente `DATABASE_URL=mysql+aiomysql://techuser:...@db:3306/techconnect` no seu `.env` **antes** de subir os containers — senão o backend do container tenta conectar no Supabase, não no MySQL local (ver DB-5 no [BACKLOG](docs/BACKLOG.md)).
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

### Opção 3 — Execução manual com SQLite (Local Fallback)
> Comente (ou remova) toda linha `DATABASE_URL=...` do `.env` — com a variável ausente, o backend usa automaticamente o **SQLite local** (`techconnect.db`). Copiar `.env.example` sem editar **não** ativa este fallback, pois ele já vem com a `DATABASE_URL` do Supabase preenchida.

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
- **Troca de banco não é automática** (DB-5): o `.env.example` ativa o Supabase (PostgreSQL) por padrão; usar o MySQL do Docker Compose ou o fallback SQLite exige editar manualmente a linha `DATABASE_URL` no `.env` antes de subir o sistema.
- **Um commit anterior expôs credenciais reais** (senha do banco Supabase, `SUPABASE_ANON_KEY` e um `SECRET_KEY`) em texto puro neste README; os valores foram substituídos por placeholders num commit seguinte, mas ainda **não foram rotacionados** no Supabase e permanecem visíveis no histórico do Git (SEC-5).
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
