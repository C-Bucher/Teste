# TechConnect 2.0 - CFO Virtual IA 🚀

TechConnect 2.0 é a evolução da plataforma financeira inteligente, projetada com uma interface ultrarrápida, design premium ("Obsidian Flow") e funcionalidades interativas como o Kanban de projetos. Ele integra um painel gerencial robusto focado em proporcionar uma experiência fluida para tomada de decisões financeiras.

## ✨ Características do Projeto
- **Dois modos de conta**: planos Pessoal, Empresarial e Completo, com um Hub Empresarial (ERP para PMEs) e um Hub Pessoal (finanças pessoais) alternáveis pelo mesmo usuário.
- **Hub Empresarial**: Dashboard financeiro, Kanban de projetos, Gestão de equipe, Fornecedores, Financeiro, Exportação de relatórios e um módulo de IA (CFO Virtual).
- **Hub Pessoal**: Visão geral, Contas & Cartões, Orçamento por Categoria, Metas Financeiras, Dívidas & Parcelamentos, Assinaturas Recorrentes, Divisão de Despesas, Dashboard Analítico e CFO Pessoal IA.
- **Design Obsidian Flow**: Interface moderna e elegante baseada no Glassmorphism (efeitos de vidro) com tipografia de alta performance (Inter e Outfit) e temas escuros focados em visibilidade.
- **Kanban Interativo**: Gerenciamento de tarefas em colunas com recursos HTML5 de Drag & Drop (arrastar e soltar).
- **Gestão de Equipes**: CRUD completo com sincronização imediata utilizando modais estilizados.
- **Controle de Acesso por Papel**: Três níveis de acesso (Admin, Gerente, Funcionário) com menus e permissões diferenciados.
- **Persistência real**: todo o backend roda sobre um banco de dados MySQL de verdade (via SQLAlchemy async), não mais dados em memória.

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
- **SQLAlchemy 2.0 (async)**: ORM assíncrono sobre o banco real, com seed idempotente dos dados de demonstração.
- **Uvicorn**: Servidor ASGI leve para rodar o backend.
- **MySQL 8.0**: Banco de dados relacional real (via Docker).
- **Redis 7**: Cache e filas (via Docker).

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

> Fora do Docker Compose, as variáveis do `.env` não são carregadas automaticamente. Exporte-as manualmente no terminal antes de subir o backend (ou rode `sqlite+aiosqlite:///./techconnect.db` como `DATABASE_URL` para testar rápido em SQLite local, sem MySQL).

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
O seed inicial popula o banco MySQL com 3 usuários de demonstração. Utilize as seguintes credenciais na tela de login:

| Papel        | E-mail                              | Senha         |
|--------------|-------------------------------------|---------------|
| Admin        | `admin@techconnect.com.br`          | `Admin@123`   |
| Gerente      | `gerente@techconnect.com.br`        | `Gerente@123` |
| Funcionário  | `funcionario@techconnect.com.br`    | `Func@123`    |

### Permissões por Papel
- **Admin**: Acesso total — Dashboard financeiro, Kanban de projetos, Gestão de equipe (CRUD completo).
- **Gerente**: Dashboard financeiro, Kanban de projetos, Gestão de equipe (somente visualização).
- **Funcionário**: Dashboard pessoal, Kanban de projetos (apenas tarefas atribuídas).

## 📁 Estrutura do Projeto

```
TechConnect2.0/
├── app/                    # Backend FastAPI
│   ├── api/v1/endpoints/   # Rotas da API (auth, financial, kanban, employees, personal...)
│   ├── core/               # Segurança (JWT) e configurações
│   └── db/                 # Banco de dados real (SQLAlchemy async)
│       ├── models.py       # ~28 tabelas
│       ├── session.py      # Engine/sessão async (MySQL, DATABASE_URL via .env)
│       ├── seed.py         # Seed idempotente dos dados de demonstração
│       └── utils.py        # Helpers de serialização
├── frontend/               # Frontend React + Vite
│   └── src/
│       ├── components/     # Componentes reutilizáveis (Layout com toggle Empresarial/Pessoal)
│       └── pages/          # Páginas do Hub Empresarial e do Hub Pessoal
├── architecture/           # POPs de IA (CFO Virtual, Conciliação, Orçamentos)
├── docs/                   # Documentação do projeto (Escopo, ERS, DAS, planos de desenvolvimento)
├── docker-compose.yml      # Orquestração Docker (MySQL, Redis, Backend, Frontend)
├── Dockerfile              # Imagem do backend
├── .env.example            # Modelo de variáveis de ambiente (sem segredos reais)
└── requirements.txt        # Dependências Python
```

---
*Desenvolvido focado em inovação, UX premium e escalabilidade.*
