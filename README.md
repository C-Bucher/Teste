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

- Quatro planos (Pessoal Essencial, Pessoal Conectado, Empresarial e Completo), com Hub Empresarial e Hub Pessoal alternáveis pelo mesmo usuário, sem precisar logar de novo.
- Kanban com arrastar e soltar, gestão de equipe com modais de CRUD, fornecedores, financeiro (DRE, fluxo de caixa, lançamentos) e exportação de relatórios.
- Hierarquia de cargos configurável: o Admin escolhe em Configurações → Hierarquia de Cargos quais módulos cada cargo acessa, e o bloqueio vale no servidor, não só na tela.
- Assistente de onboarding de 3 passos (dados da empresa, hierarquia de cargos, conexões de API) no primeiro login do Admin de uma empresa nova.
- Painel de conexões de API: banco, IA, pagamentos, e-mail, bancos, armazenamento, agendador e criptografia, com o que falta configurar.
- Criação de logins de Gerente e Funcionário pelo próprio Admin, em Gestão de Equipe → Acessos ao Sistema.
- Bancos & Conciliação: importação de extrato OFX/CSV de qualquer banco (sem duplicar), conciliação automática com contas a pagar e a receber, regras de categoria e conexão automática via agregador de Open Finance (Pluggy).
- IA com dados reais (Gemini): CFO Virtual com histórico, CFO Pessoal, sugestão de categorias e gerador de orçamentos com o custo-hora real da equipe; cota mensal por plano.
- Assinatura com cobrança recorrente pelo Asaas (Pix, boleto ou cartão na página do Asaas), 7 dias de teste, bloqueio após atraso e cancelamento.
- Segurança de conta: recuperação de senha por e-mail, verificação em duas etapas (aplicativo autenticador), bloqueio por tentativas e limite por IP.
- Anexo de comprovantes, exportação em Excel, PDF, CSV e JSON, custo de pessoal (CTC) configurável, trilha de auditoria, alertas diários de vencimento e Minha Conta (senha, 2FA e direitos da LGPD).

---

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router v7, Framer Motion, Axios, Recharts |
| Backend | FastAPI (Python 3.11+), Pydantic, SQLAlchemy 2.0 assíncrono, Alembic, Uvicorn — 41 tabelas, seed idempotente |
| Integrações | Google Gemini (IA), Asaas (cobrança), Pluggy (Open Finance), SMTP (e-mail), S3 compatível (arquivos) |
| Qualidade | pytest, Vitest + Testing Library, ESLint, GitHub Actions |
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

A suíte do backend sobe a API em memória sobre um SQLite temporário. Ela cobre:
- isolamento entre empresas e entre usuários, gates por módulo, plano e assinatura;
- autenticação, 2FA, recuperação de senha, cobrança e webhooks;
- bancos, IA (com modelo simulado), exportações e migrações;
- um teste de contrato que falha se o frontend chamar uma rota inexistente.

Nenhuma chamada sai para serviços pagos, mesmo com chaves no `.env`. Para rodar contra um banco real, aponte `TEST_DATABASE_URL` para um banco **descartável** (por exemplo, um PostgreSQL local em Docker com `DATABASE_SSL=disable`): a suíte grava dados nele.

Frontend:

```bash
cd frontend
npm run lint && npm test && npm run build
```

O CI (`.github/workflows/ci.yml`) roda tudo isso a cada pull request, com o backend em SQLite e em PostgreSQL.

### Integrações e rotinas

Cada serviço externo funciona sem credenciais em desenvolvimento:
- IA responde por regras;
- pagamento é simulado;
- e-mail vai para o log;
- bancos funcionam por importação de extrato;
- arquivos ficam em disco local.

Para produção, preencha as seções do `.env.example` e confira em Configurações → Conexões de API:

| Serviço | Onde configurar |
| --- | --- |
| Asaas | Crie o webhook para `<API>/api/v1/payments/webhook/asaas` com o token de `ASAAS_WEBHOOK_TOKEN` |
| Pluggy | Webhook para `<API>/api/v1/bank/webhook/pluggy`, com o cabeçalho `X-Webhook-Secret` |
| Agendador | Uma vez por dia, `POST <API>/api/v1/jobs/daily` com `X-Cron-Secret`: alertas de vencimento e sincronização bancária |
| Arquivos | `STORAGE_BACKEND=s3` com Supabase Storage, S3 ou R2 |

Para trazer as datas da demonstração para hoje, rode `python -m app.db.demo_dates`.

---

## Acessos de teste

| Papel        | E-mail                              | Senha         |
|--------------|-------------------------------------|---------------|
| Admin        | `admin@techconnect.com.br`          | `Admin@123`   |
| Gerente      | `gerente@techconnect.com.br`        | `Gerente@123` |
| Funcionário  | `funcionario@techconnect.com.br`    | `Func@123`    |

### Permissões por papel

As senhas precisam ter pelo menos 8 caracteres, com letras e números. Depois de 5 senhas (ou códigos de 2FA) errados seguidos, a conta fica bloqueada por 15 minutos. A sessão dura 60 minutos e é renovada automaticamente por até 7 dias; trocar ou redefinir a senha encerra as sessões antigas. A empresa demo tem assinatura ativa; contas novas começam com 7 dias de teste.

O Admin tem acesso total e fixo a todos os módulos, e é o único que cria logins, edita a matriz de permissões e vê o status das integrações. Por padrão, o Gerente acessa Dashboard, Projetos, Equipe, Financeiro, Fornecedores, Exportação e IA Empresarial, mas não Configurações; o Funcionário acessa só Dashboard e Projetos. Esse padrão vale até o Admin salvar uma matriz própria em Configurações → Hierarquia de Cargos. A partir daí, a matriz salva prevalece, mesmo que deixe algum cargo sem nenhum módulo.

---

## Limitações conhecidas

Estão registradas aqui de propósito, para que a avaliação parta do estado real do sistema. Os detalhes e a prioridade de cada uma estão em [docs/BACKLOG.md](docs/BACKLOG.md).

- **Credenciais expostas (SEC-5).** Um commit anterior colou em texto puro neste README a senha do banco Supabase, a `SUPABASE_ANON_KEY` e um `SECRET_KEY`. Foram trocadas por placeholders, mas continuam válidas no histórico do Git, e a chave do Gemini do projeto foi bloqueada pelo Google como vazada. Trocar essas credenciais é pré-requisito do lançamento.
- **IA.** Sem uma chave válida do Gemini, a IA responde por regras calculadas com os dados reais (IA-1).
- **Pagamentos e bancos.** Asaas e Pluggy estão implementados e testados com provedores simulados, mas ainda não foram validados nos sandboxes reais por falta de credenciais (PAY-1, BANK-1).
- **E-mail.** Sem SMTP configurado, os e-mails (inclusive a recuperação de senha) ficam só no log.
- **Textos legais.** Termos de uso e política de privacidade são minuta para revisão jurídica (SEC-2).
- **Operação.** O limite por IP e a cota de IA valem por instância (SEC-9); os uploads não passam por antivírus (SEC-8); a hospedagem de produção ainda não foi definida (DEP-1).
- Verificação do frontend: use `npm run build` (ou `npx tsc -p tsconfig.app.json --noEmit`); `npx tsc --noEmit` sozinho não checa nada neste projeto.

---

## Estrutura do repositório

```
.
├── app/                        # Backend FastAPI
│   ├── api/v1/endpoints/       # Rotas por domínio (auth, account, payments, bank, financial, kanban, ai, jobs...)
│   ├── core/                   # Segurança, cobrança, permissões, auditoria, e-mail, armazenamento, alertas
│   ├── integrations/           # ai/ (Gemini), bank/ (OFX/CSV, Pluggy), payments/ (Asaas)
│   └── db/                     # models.py (41 tabelas), alembic/ (migrações), session.py, seed.py, demo_dates.py
├── tests/                      # pytest: isolamento, autenticação, cobrança, bancos, IA, contrato da API
├── frontend/src/               # Frontend React + Vite
│   ├── components/             # Layout, painéis de Configurações, 2FA, banner de assinatura, modais
│   ├── context/                # Toasts e confirmação
│   ├── hooks/  utils/          # usePermissions, defer
│   ├── pages/                  # Hubs, Bancos, Assinatura/Checkout, Minha Conta, recuperação de senha, termos
│   └── types.ts  api.ts        # Tipos da API e cliente HTTP (renovação de sessão, bloqueio por assinatura)
├── .github/workflows/ci.yml    # CI: pytest (SQLite e PostgreSQL), lint, testes e build do frontend
├── architecture/               # POPs de IA (CFO Virtual, Conciliação, Orçamentos)
├── docs/                       # Requisitos, arquitetura, ADRs, BACKLOG, reuniões, planejamento
├── sprints/  entregas/         # Sprints e relatórios de entrega
└── docker-compose.yml  Dockerfile  .env.example  requirements.txt
```

## Documentação

As melhorias de precisão monetária, integridade e histórico de custos estão documentadas no [ADR 012](docs/decisoes/adr-012-precisao-integridade-apontamentos.md). A [entrega de banco](docs/analise-banco/README.md) inclui evidências da migração 0011 e roteiro de apresentação. Para usar os novos apontamentos, execute o backend atualizado junto do esquema 0011.

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
