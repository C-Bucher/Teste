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
| Backend | FastAPI (Python), Pydantic, SQLAlchemy 2.0 assíncrono, Uvicorn — 32 tabelas, seed idempotente e migrações aditivas de compatibilidade |
| Banco de dados | PostgreSQL gerenciado (Supabase, via Connection Pooler), MySQL 8.0 (Docker) ou SQLite (fallback local) |
| Infraestrutura | Docker e Docker Compose; segredos e credenciais via `.env`, que fica fora do Git |
| Redis 7 | provisionado no Compose, mas ainda não utilizado pela aplicação (reservado para cache/filas) |

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
Na inicialização, o backend aplica as migrações versionadas do Alembic (`alembic upgrade head`) e executa a carga de dados inicial (seed idempotente) se o banco estiver vazio. Uma base criada antes do Alembic é reconhecida automaticamente: recebe as colunas de compatibilidade, é marcada na revisão base e então atualizada. Para criar uma nova migração depois de alterar `app/db/models.py`, rode `alembic revision --autogenerate -m "descricao"`.

Frontend (React + Vite), em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend em `http://localhost:5173`, API em `http://localhost:8000`.

### Opção 2 — Docker Compose (MySQL)

Dentro do Compose, o backend usa automaticamente o MySQL do próprio Compose, montado a partir de `MYSQL_USER`, `MYSQL_PASSWORD` e `MYSQL_DATABASE`, independentemente da `DATABASE_URL` do `.env`, que continua valendo para a execução manual. Para apontar o backend em Docker para o Supabase, defina `COMPOSE_DATABASE_URL` no `.env`.

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

Comente ou remova toda linha `DATABASE_URL=` do `.env`. Sem essa variável, o backend cai automaticamente no SQLite local (`techconnect.db`, sempre na raiz do projeto, independentemente da pasta de onde o `uvicorn` foi iniciado). Só copiar o `.env.example` sem editar não ativa esse fallback, porque ele já vem com a `DATABASE_URL` do Supabase preenchida.

### Testes automatizados

```bash
pip install -r requirements-dev.txt
python -m pytest
```

A suíte sobe a API em memória sobre um SQLite temporário e cobre isolamento entre empresas e entre usuários, gates por módulo e por plano, regras de acesso, política de senha, bloqueio de login, tokens, auditoria e migrações. Para rodá-la contra um banco real, aponte `TEST_DATABASE_URL` para um banco **descartável**, por exemplo um PostgreSQL local em Docker com `DATABASE_SSL=disable`; a suíte grava dados nele.

---

## Acessos de teste

| Papel        | E-mail                              | Senha         |
|--------------|-------------------------------------|---------------|
| Admin        | `admin@techconnect.com.br`          | `Admin@123`   |
| Gerente      | `gerente@techconnect.com.br`        | `Gerente@123` |
| Funcionário  | `funcionario@techconnect.com.br`    | `Func@123`    |

### Permissões por papel

As senhas precisam ter pelo menos 8 caracteres, com letras e números. Depois de 5 senhas erradas seguidas, a conta fica bloqueada por 15 minutos. A sessão dura 60 minutos e é renovada automaticamente por até 7 dias; trocar a senha encerra as sessões antigas.

O Admin tem acesso total e fixo a todos os módulos, e é o único que cria logins, edita a matriz de permissões e vê o status das integrações. Por padrão, o Gerente acessa Dashboard, Projetos, Equipe, Financeiro, Fornecedores, Exportação e IA Empresarial, mas não Configurações; o Funcionário acessa só Dashboard e Projetos. Esse padrão vale até o Admin salvar uma matriz própria em Configurações → Hierarquia de Cargos. A partir daí, a matriz salva prevalece, mesmo que deixe algum cargo sem nenhum módulo.

---

## Limitações conhecidas

Estão registradas aqui de propósito, para que a avaliação parta do estado real do sistema. Os detalhes e a prioridade de cada uma estão em [docs/BACKLOG.md](docs/BACKLOG.md).

- A IA generativa ainda não está integrada: CFO, conciliação e propostas continuam demonstrativos baseados em regras; a API identifica corretamente o modelo como `rule-based-demo` e não declara consumo fictício de tokens (IA-1).
- O checkout não processa pagamento real: assinaturas e faturas são persistidas no banco, mas cartão e Pix continuam sendo uma simulação sem gateway externo.
- MFA ainda não foi implementado, apesar do campo existente no usuário (AUTH-1).
- Uploads permanecem locais no volume `uploads`; não há storage externo nem antivírus.
- A trilha de auditoria (`GET /api/v1/audit/`, só Admin) já registra logins, acessos, permissões, troca de senha e lançamentos financeiros, mas ainda não tem tela, e os direitos do titular da LGPD (exportar e excluir os próprios dados) ainda não existem (SEC-2).
- Os testes automatizados cobrem o backend; o frontend ainda não tem testes.
- Um commit anterior expôs credenciais reais (senha do banco Supabase, `SUPABASE_ANON_KEY` e um `SECRET_KEY`) em texto puro neste README; os valores foram substituídos por placeholders num commit seguinte, mas ainda não foram rotacionados no Supabase e permanecem visíveis no histórico do Git (SEC-5).
- Verificação do frontend: use `npm run build` (ou `npx tsc -p tsconfig.app.json --noEmit`); `npx tsc --noEmit` sozinho não checa nada neste projeto.

---

## Estrutura do repositório

```
.
├── app/                        # Backend FastAPI
│   ├── api/v1/endpoints/       # Rotas (auth, company, permissions, system, financial, kanban, employees, personal...)
│   ├── core/                   # Segurança (JWT), configuração e permissões por módulo (permissions.py)
│   └── db/                     # models.py (32 tabelas), migrations.py, session.py, seed.py, utils.py
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
