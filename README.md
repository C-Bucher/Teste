# TechConnect 2.0 - CFO Virtual IA 🚀

TechConnect 2.0 é a evolução da plataforma financeira inteligente, projetada com uma interface ultrarrápida, design premium ("Obsidian Flow") e funcionalidades interativas como o Kanban de projetos. Ele integra um painel gerencial robusto focado em proporcionar uma experiência fluida para tomada de decisões financeiras.

## ✨ Características do Projeto
- **Dois modos de conta**: planos Pessoal, Empresarial e Completo, com um Hub Empresarial (ERP para PMEs) e um Hub Pessoal (finanças pessoais) alternáveis pelo mesmo usuário.
- **Hub Empresarial**: Dashboard financeiro, Kanban de projetos, Gestão de equipe, Fornecedores, Financeiro, Exportação de relatórios e um módulo de IA (CFO Virtual).
- **Hub Pessoal**: Visão geral, Contas & Cartões, Orçamento por Categoria, Metas Financeiras, Dívidas & Parcelamentos, Assinaturas Recorrentes, Divisão de Despesas, Dashboard Analítico e CFO Pessoal IA.
- **Design Obsidian Flow**: Interface moderna e elegante baseada no Glassmorphism (efeitos de vidro) com tipografia de alta performance (Inter e Outfit) e temas escuros focados em visibilidade.
- **Kanban Interativo**: Gerenciamento de tarefas em colunas com recursos HTML5 de Drag & Drop (arrastar e soltar).
- **Gestão de Equipes**: CRUD completo com sincronização imediata utilizando modais estilizados.
- **Controle de Acesso por Papel configurável**: três cargos (Admin, Gerente, Funcionário); o Admin escolhe em *Configurações → Hierarquia de Cargos* quais módulos cada cargo acessa, e o bloqueio vale de verdade no servidor (resposta 403), não só no menu.
- **Onboarding guiado**: no primeiro login, o Admin de uma empresa nova passa por um assistente de 3 passos (dados da empresa → hierarquia de cargos → conexões de API).
- **Painel de Conexões de API**: mostra em tempo real se o banco de dados está online e se a chave da IA está configurada.
- **Persistência real**: o backend roda sobre um banco relacional de verdade via SQLAlchemy async — MySQL no Docker Compose, SQLite local na execução manual — e não mais sobre dados em memória.

## 🛠 Tecnologias Utilizadas

### Frontend
- **React 19**: A última versão do React para melhor performance e concorrência.
- **React Router v7**: Roteamento client-side, incluindo as rotas por aba do Hub Pessoal.
- **Vite**: Build tool ultrarrápido.
- **Tailwind CSS v4**: O novo motor do Tailwind sem a necessidade de configuração complexa, utilizando `@theme` nativo.
- **Framer Motion**: Para as micro-interações e animações de modais.
- **Axios**: Gerenciador de requisições.
- **Recharts**: Para os gráficos financeiros dinâmicos (DRE / Cashflow).

### Backend
- **FastAPI (Python)**: Construído com pydantic, garantindo extrema rapidez.
- **SQLAlchemy 2.0 (async)**: ORM assíncrono sobre o banco real (29 tabelas), com seed idempotente dos dados de demonstração.
- **Uvicorn**: Servidor ASGI leve para rodar o backend.
- **MySQL 8.0**: Banco de dados relacional real (via Docker).
- **Redis 7**: provisionado no Docker Compose, **ainda não utilizado** pela aplicação (reservado para cache/filas futuros).

### Infraestrutura
- **Docker & Docker Compose**: Orquestração dos 4 containers (DB, Redis, Backend, Frontend).
- **Variáveis de ambiente (`.env`)**: segredos (chave JWT, chave da API Gemini, credenciais do MySQL) nunca ficam hardcoded — veja a seção de configuração abaixo.

## ⚙️ Como Executar o Projeto

### 0. Configurar variáveis de ambiente (obrigatório)
Copie o arquivo de exemplo e preencha com valores reais antes de subir o projeto:

```bash
cp .env.example .env
```

Edite o `.env` e defina `SECRET_KEY` (uma string aleatória longa — pode gerar com `python -c "import secrets; print(secrets.token_hex(32))"`), `GEMINI_API_KEY` (obtida em [Google AI Studio](https://aistudio.google.com/app/apikey)) e as credenciais do MySQL. **O arquivo `.env` nunca deve ser commitado** — já está no `.gitignore`.

### Opção 1 — Docker Compose (Recomendado)
Certifique-se de ter o **Docker** e o **Docker Compose** instalados.

```bash
# Subir todos os serviços (banco, cache, backend e frontend)
docker-compose up -d

# Verificar se os containers estão rodando
docker ps
```

Na primeira subida, o backend cria o schema no MySQL e popula os dados de demonstração automaticamente (seed idempotente — só roda se o banco estiver vazio).

| Serviço  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173       |
| Backend  | http://localhost:8000       |
| API Docs | http://localhost:8000/docs  |
| MySQL    | localhost:3307              |
| Redis    | localhost:6379              |

Para parar os serviços:
```bash
docker-compose down
```

### Opção 2 — Execução Manual

> Sem Docker, o backend usa por padrão um **SQLite local** (`techconnect.db`, criado e populado automaticamente na primeira execução) — não precisa de MySQL nem de `.env` para rodar. Para apontar para outro banco, exporte `DATABASE_URL` no terminal; o `.env` só é carregado automaticamente pelo Docker Compose.

#### 1. Rodando o Backend (FastAPI)
Abra um terminal na pasta raiz do projeto:
```bash
# 1. Crie o ambiente virtual
python -m venv venv

# 2. Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie o servidor
uvicorn app.main:app --reload --port 8000
```
A API estará rodando em `http://localhost:8000`.

#### 2. Rodando o Frontend (React + Vite)
Abra um segundo terminal e navegue até a pasta `frontend`:
```bash
cd frontend

# 1. Instale os pacotes NPM
npm install

# 2. Inicie a aplicação
npm run dev
```
O Frontend estará rodando em `http://localhost:5173`.

## 🔑 Acessos de Teste
O seed inicial popula o banco (MySQL via Docker Compose; SQLite local na execução manual) com 3 usuários de demonstração, todos da empresa de demonstração. Utilize as seguintes credenciais na tela de login:

| Papel        | E-mail                              | Senha         |
|--------------|-------------------------------------|---------------|
| Admin        | `admin@techconnect.com.br`          | `Admin@123`   |
| Gerente      | `gerente@techconnect.com.br`        | `Gerente@123` |
| Funcionário  | `funcionario@techconnect.com.br`    | `Func@123`    |

### Permissões por Papel
- **Admin**: acesso total e fixo (não editável) a todos os módulos; é o único que cria logins, edita a matriz de permissões e vê o status das integrações.
- **Gerente** (padrão): Dashboard, Projetos, Equipe, Financeiro, Fornecedores, Exportação e IA Empresarial — **sem** Configurações.
- **Funcionário** (padrão): Dashboard e Projetos.

O padrão vale até o Admin salvar uma matriz própria em *Configurações → Hierarquia de Cargos*; a partir daí, a matriz salva prevalece (inclusive se ela deixar um cargo sem nenhum módulo). Novos Gerentes/Funcionários são criados pelo Admin em *Gestão de Equipe → Acessos ao Sistema*.

## ⚠️ Limitações conhecidas (leia antes de avaliar o projeto)
- **Os dados de negócio não são isolados por empresa.** Empresas, usuários e permissões são separados por empresa, mas funcionários, lançamentos financeiros, projetos/Kanban, clientes, fornecedores, notificações e exportações são um conjunto único: uma empresa recém-cadastrada enxerga os dados da empresa de demonstração. O isolamento completo está previsto no [BACKLOG](docs/BACKLOG.md) (item MT-1).
- Ainda sem gate por módulo: Kanban, clientes, notificações, planos, pagamentos e Hub Pessoal (SEC-3). As permissões *Dashboard* e *Projetos* da matriz só controlam o menu.
- A IA (CFO Virtual etc.) responde por palavras-chave, não usa um modelo generativo real; não há 2FA, auditoria/LGPD nem testes automatizados.
- Verificação do frontend: use `npm run build` (ou `npx tsc -p tsconfig.app.json --noEmit`) — o comando `npx tsc --noEmit` sozinho não checa nada neste repositório.
- Lista completa e priorizada: [docs/BACKLOG.md](docs/BACKLOG.md).

## 📁 Estrutura do Projeto

```
TechConnect2.0/
├── app/                        # Backend FastAPI
│   ├── api/v1/endpoints/       # Rotas (auth, company, permissions, system, financial, kanban, employees, personal...)
│   ├── core/                   # Segurança (JWT), configuração e permissões por módulo (permissions.py)
│   └── db/                     # Banco real (SQLAlchemy async)
│       ├── models.py           # 29 tabelas
│       ├── session.py          # Engine/sessão async (SQLite por padrão; MySQL via DATABASE_URL)
│       ├── seed.py             # Seed idempotente dos dados de demonstração
│       └── utils.py            # Helpers de serialização
├── frontend/                   # Frontend React + Vite
│   └── src/
│       ├── components/         # Layout, PermissionMatrix, IntegrationsStatus, SystemAccessSection, modais
│       ├── context/            # Toasts e confirmação (ToastContext, ConfirmContext)
│       ├── hooks/              # usePermissions (módulos liberados ao usuário)
│       └── pages/              # Hub Empresarial, Hub Pessoal, Configurações, Onboarding, Login/Cadastro
├── architecture/               # POPs de IA (CFO Virtual, Conciliação, Orçamentos)
├── docs/                       # BACKLOG, registro de alterações e planos/specs de desenvolvimento
├── docker-compose.yml          # Orquestração Docker (MySQL, Redis, Backend, Frontend)
├── Dockerfile                  # Imagem do backend
├── main.py                     # Atalho para subir o backend (uvicorn)
├── .env.example                # Modelo de variáveis de ambiente (sem segredos reais)
└── requirements.txt            # Dependências Python
```

## 📚 Documentação
- [docs/BACKLOG.md](docs/BACKLOG.md) — backlog priorizado (P0–P3), com o estado real de cada item e as limitações conhecidas.
- [docs/registro-de-alteracoes-para-documentacao.md](docs/registro-de-alteracoes-para-documentacao.md) — tudo que foi implementado por área, para atualizar Escopo, ERS e DAS.
- [docs/planejamento/specs](docs/planejamento/specs) e [docs/planejamento/plans](docs/planejamento/plans) — especificações e planos de execução de cada fase, em ordem cronológica (registro histórico do processo).

---
*Desenvolvido focado em inovação, UX premium e escalabilidade.*
