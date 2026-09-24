# TechConnect 2.0 — Dashboard para Gestão Operacional & CFO Virtual IA

Repositório institucional de Projeto Integrador do curso de Análise e Desenvolvimento de Sistemas (ADS) — CEUB. Reúne o código-fonte da solução e a documentação de engenharia do projeto: requisitos, arquitetura, decisões técnicas (ADRs), sprints e entregas.

A documentação segue o padrão pedido pela disciplina, com rastreabilidade entre requisito, decisão e código. A seção [Limitações conhecidas](#limitações-conhecidas), mais adiante, e a matriz de atendimento em [docs/requisitos.md](docs/requisitos.md) mostram o que está pronto, o que está parcial e o que ainda falta, sem maquiar o estado real do sistema. Para entender a arquitetura e o backlog em detalhe, os pontos de partida são [docs/arquitetura.md](docs/arquitetura.md), [docs/requisitos.md](docs/requisitos.md) e [docs/BACKLOG.md](docs/BACKLOG.md).

---

## Identificação do repositório

| Campo | Informação |
|---|---|
| Instituição | Centro Universitário de Brasília — CEUB |
| Curso | Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) |
| Disciplina | Projeto Integrador (PI) |
| Organização no GitHub | CampusCEUB |
| Repositório | `ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL` (documentação e código da solução) |
| Nome da solução | TechConnect 2.0 — CFO Virtual & Gestão Operacional |
| Equipe | Gabriel Salles, Abner Trindade, Caio Alexandre, Andrei Maciel |

---

## Problema

PMEs e profissionais autônomos costumam gerenciar a operação do dia a dia (projetos, tarefas, equipe, fornecedores) separada do impacto financeiro real dessas decisões (fluxo de caixa, DRE, custo por tarefa, encargos). Isso, na prática, gera três problemas recorrentes:

1. Ninguém sabe ao certo quanto custou um projeto ou um cliente específico.
2. Decisões financeiras importantes acabam tomadas tarde, sem dado que as sustente.
3. As finanças da empresa (PJ) se misturam com as da pessoa física (PF) do dono do negócio.

---

## Solução proposta

O TechConnect 2.0 junta duas frentes num só sistema: um Hub Empresarial, que funciona como um ERP enxuto para PMEs (dashboard com DRE e fluxo de caixa, Kanban de projetos com custo por tarefa e cronômetro, gestão de equipe com CTC e histórico salarial, fornecedores, lançamentos financeiros e exportação de relatórios); e um Hub Pessoal, para quem quer manter as próprias finanças organizadas à parte (visão geral, contas e cartões, orçamento por categoria, metas, dívidas, assinaturas, divisão de despesas e OKRs/timeboxes).

O acesso a cada módulo do Hub Empresarial é controlado por cargo (Admin, Gerente, Funcionário), e esse controle é aplicado de verdade no servidor: quem não tem permissão recebe HTTP 403, não fica só escondido no menu. Há também um módulo de IA (CFO Virtual) pensado para rodar sobre Procedimentos Operacionais Padrão e um modelo generativo; hoje ele ainda responde por palavras-chave, e a integração com um LLM real está no backlog (IA-1).

No backend, o mesmo código aceita três bancos relacionais diferentes por trás de uma única variável de ambiente: PostgreSQL gerenciado via Supabase (o padrão em `.env.example`), MySQL 8 rodando no Docker Compose, ou SQLite como fallback local quando nenhum dos dois está configurado. A interface segue o design system Obsidian Flow, em dark mode com efeito de vidro (React 19 + Tailwind CSS v4 + Framer Motion).

---

## Funcionalidades

- Dois modos de conta (Pessoal, Empresarial e Completo), com Hub Empresarial e Hub Pessoal alternáveis pelo mesmo usuário, sem precisar logar de novo.
- Kanban com arrastar e soltar, gestão de equipe com modais de CRUD, fornecedores, financeiro (DRE, fluxo de caixa, lançamentos) e exportação de relatórios.
- Hierarquia de cargos configurável: o Admin escolhe em Configurações → Hierarquia de Cargos quais módulos cada cargo acessa, e o bloqueio vale no servidor, não só na tela.
- Assistente de onboarding de 3 passos (dados da empresa, hierarquia de cargos, conexões de API) no primeiro login do Admin de uma empresa nova.
- Painel de conexões de API, mostrando se o banco está online e se a chave da IA foi configurada.
- Criação de logins de Gerente e Funcionário pelo próprio Admin, em Gestão de Equipe → Acessos ao Sistema.

---

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router v7, Framer Motion, Axios, Recharts |
| Backend | FastAPI (Python), Pydantic, SQLAlchemy 2.0 assíncrono (via `asyncpg`), Uvicorn — 29 tabelas, seed idempotente |
| Banco de dados | PostgreSQL gerenciado (Supabase, via Connection Pooler), MySQL 8.0 (Docker) ou SQLite (fallback local) |
| Infraestrutura | Docker e Docker Compose; segredos via `.env`, que fica de fora do Git |
| Redis 7 | provisionado no Compose, mas ainda não usado pela aplicação (reservado para cache/filas) |

---

## Como executar

### 0. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas próprias credenciais. Nunca use valores reais neste README ou em qualquer outro arquivo versionado; o formato está em [`.env.example`](.env.example). Para conectar no Supabase, a connection string do pooler fica assim:

```env
DATABASE_URL=postgresql+asyncpg://postgres.<PROJECT_REF>:<SENHA_URL_ENCODED>@aws-0-us-east-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://<PROJECT_REF>.supabase.co
SUPABASE_ANON_KEY=<sua-anon-key>
SECRET_KEY=<gere-com-o-comando-abaixo>
```

A senha do banco no pooler precisa de URL-encoding para caracteres especiais (o `@`, por exemplo, vira `%40`). Para gerar o `SECRET_KEY`, rode `python -c "import secrets; print(secrets.token_hex(32))"`.

### Opção 1 — Execução com Supabase (recomendada)

Backend (FastAPI):

```bash
python -m venv venv
venv\Scripts\activate          # Windows  |  Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Na primeira inicialização, o backend cria as 29 tabelas no Supabase e roda o seed idempotente com os dados de demonstração.

Frontend (React + Vite), em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend em `http://localhost:5173`, API em `http://localhost:8000`.

### Opção 2 — Docker Compose (MySQL)

O `.env.example` vem com a `DATABASE_URL` do Supabase ativa por padrão. Para usar o MySQL do Compose é preciso comentar essa linha e descomentar a do MySQL (`mysql+aiomysql://techuser:...@db:3306/techconnect`) no `.env` antes de subir os containers. Do contrário, o backend, mesmo rodando em Docker, tenta conectar no Supabase em vez do MySQL local que o próprio Compose acabou de subir — esse comportamento está registrado como item DB-5 no [BACKLOG](docs/BACKLOG.md).

```bash
docker-compose up -d
docker ps
```

Na primeira subida, o backend cria o schema no MySQL e popula os dados de demonstração.

| Serviço  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173       |
| Backend  | http://localhost:8000       |
| API Docs | http://localhost:8000/docs  |
| MySQL    | localhost:3307              |
| Redis    | localhost:6379              |

Para parar: `docker-compose down`.

### Opção 3 — Execução manual com SQLite

Comente ou remova toda linha `DATABASE_URL=` do `.env`. Sem essa variável, o backend cai automaticamente no SQLite local (`techconnect.db`). Só copiar o `.env.example` sem editar não ativa esse fallback, porque ele já vem com a `DATABASE_URL` do Supabase preenchida.

---

## Acessos de teste

| Papel        | E-mail                              | Senha         |
|--------------|-------------------------------------|---------------|
| Admin        | `admin@techconnect.com.br`          | `Admin@123`   |
| Gerente      | `gerente@techconnect.com.br`        | `Gerente@123` |
| Funcionário  | `funcionario@techconnect.com.br`    | `Func@123`    |

### Permissões por papel

O Admin tem acesso total e fixo a todos os módulos, e é o único que cria logins, edita a matriz de permissões e vê o status das integrações. Por padrão, o Gerente acessa Dashboard, Projetos, Equipe, Financeiro, Fornecedores, Exportação e IA Empresarial, mas não Configurações; o Funcionário acessa só Dashboard e Projetos. Esse padrão vale até o Admin salvar uma matriz própria em Configurações → Hierarquia de Cargos. A partir daí, a matriz salva prevalece, mesmo que deixe algum cargo sem nenhum módulo.

---

## Limitações conhecidas

Estão registradas aqui de propósito, para que a avaliação parta do estado real do sistema. Os detalhes e a prioridade de cada uma estão em [docs/BACKLOG.md](docs/BACKLOG.md).

- Os dados de negócio não são isolados por empresa (**MT-1**): empresas, usuários e permissões são separados por `company_id`, mas funcionários, lançamentos, projetos, clientes, fornecedores, notificações e exportações continuam num conjunto único, compartilhado por todas as empresas cadastradas.
- O Hub Pessoal não é isolado por usuário (**MT-2**): as rotas usam um proprietário fixo (`usr-001`) em vez do usuário autenticado, então qualquer pessoa logada vê os mesmos dados pessoais, embora as tabelas já tenham a coluna `owner_id`.
- Kanban, clientes, notificações, planos, pagamentos e o próprio Hub Pessoal ainda não têm bloqueio por módulo no servidor (**SEC-3**); as permissões de Dashboard e Projetos, hoje, só controlam o menu.
- A IA responde por palavras-chave, sem modelo generativo real, e não há sanitização de dados sensíveis para LGPD (**IA-1**).
- Não há 2FA, auditoria nem suíte de testes automatizados. O `test_api.py` é um script manual de fumaça, não uma suíte de testes.
- A troca entre os três bancos não é automática (**DB-5**): como o `.env.example` ativa o Supabase por padrão, usar o MySQL do Docker Compose ou o fallback em SQLite exige editar manualmente a `DATABASE_URL` antes de subir o sistema.
- Um commit chegou a expor, em texto puro neste README, a senha real do banco no Supabase, a `SUPABASE_ANON_KEY` e um `SECRET_KEY` reais (**SEC-5**). Um commit seguinte trocou esses valores por placeholders, mas eles ainda não foram rotacionados no Supabase e continuam visíveis no histórico do Git.
- Para checar o frontend, use `npm run build` ou `npx tsc -p tsconfig.app.json --noEmit`; rodar só `npx tsc --noEmit` não verifica nada neste projeto.

---

## Estrutura do repositório

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

## Documentação

| Item | Descrição | Link |
|---|---|---|
| Requisitos | RF, RNF, critérios de aceitação e matriz de atendimento | [docs/requisitos.md](docs/requisitos.md) |
| Arquitetura | Componentes, modelo de dados, autorização e endpoints | [docs/arquitetura.md](docs/arquitetura.md) |
| ADRs | Registros de decisões de arquitetura | [docs/decisoes/README.md](docs/decisoes/README.md) |
| Backlog | Backlog priorizado (P0–P3) com o estado real de cada item | [docs/BACKLOG.md](docs/BACKLOG.md) |
| Registro de alterações | O que foi implementado, por área, para alimentar Escopo/ERS/DAS | [docs/registro-de-alteracoes-para-documentacao.md](docs/registro-de-alteracoes-para-documentacao.md) |
| Planejamento | Specs e planos de execução por fase | [docs/planejamento](docs/planejamento) |
| Sprints | Planejamento e Definition of Done de cada sprint | [sprints/README.md](sprints/README.md) |
| Entregas | Relatórios de entregas e evidências | [entregas/README.md](entregas/README.md) |
| Reuniões | Atas e alinhamentos da equipe | [docs/reunioes/README.md](docs/reunioes/README.md) |
| Changelog | Histórico de mudanças por sprint/marco | [CHANGELOG.md](CHANGELOG.md) |
| Contribuição / Segurança | Guias do repositório | [CONTRIBUTING.md](CONTRIBUTING.md) e [SECURITY.md](SECURITY.md) |
