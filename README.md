# TechConnect 2.0 - CFO Virtual IA 🚀

TechConnect 2.0 é a evolução da plataforma financeira inteligente, projetada com uma interface ultrarrápida, design premium ("Obsidian Flow") e funcionalidades interativas como o Kanban de projetos. Ele integra um painel gerencial robusto focado em proporcionar uma experiência fluida para tomada de decisões financeiras.

## ✨ Características do Projeto
- **Design Obsidian Flow**: Interface moderna e elegante baseada no Glassmorphism (efeitos de vidro) com tipografia de alta performance (Inter e Outfit) e temas escuros focados em visibilidade.
- **Kanban Interativo**: Gerenciamento de tarefas em colunas com recursos HTML5 de Drag & Drop (arrastar e soltar).
- **Gestão de Equipes**: CRUD completo com sincronização imediata utilizando modais estilizados.
- **Controle de Acesso por Papel**: Três níveis de acesso (Admin, Gerente, Funcionário) com menus e permissões diferenciados.
- **Integração Real-time**: Todo o frontend consome diretamente de uma API Python feita em FastAPI.

## 🛠 Tecnologias Utilizadas

### Frontend
- **React 19**: A última versão do React para melhor performance e concorrência.
- **Vite**: Build tool ultrarrápido.
- **Tailwind CSS v4**: O novo motor do Tailwind sem a necessidade de configuração complexa, utilizando `@theme` nativo.
- **Framer Motion**: Para as micro-interações e animações de modais.
- **Axios**: Gerenciador de requisições.
- **Recharts**: Para os gráficos financeiros dinâmicos (DRE / Cashflow).

### Backend
- **FastAPI (Python)**: Construído com pydantic, garantindo extrema rapidez.
- **Uvicorn**: Servidor ASGI leve para rodar o backend.
- **MySQL 8.0**: Banco de dados relacional (via Docker).
- **Redis 7**: Cache e filas (via Docker).

### Infraestrutura
- **Docker & Docker Compose**: Orquestração dos 4 containers (DB, Redis, Backend, Frontend).

## ⚙️ Como Executar o Projeto

### Opção 1 — Docker Compose (Recomendado)
Certifique-se de ter o **Docker** e o **Docker Compose** instalados.

```bash
# Subir todos os serviços (banco, cache, backend e frontend)
docker-compose up -d

# Verificar se os containers estão rodando
docker ps
```

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

## 🔑 Acessos de Teste (Mock DB)
Como o backend está executando dados em memória (para fins de demonstração), utilize as seguintes credenciais na tela de login:

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
│   ├── api/v1/endpoints/   # Rotas da API (auth, financial, kanban, employees...)
│   ├── core/               # Segurança e configurações
│   └── db/                 # Banco de dados em memória (mock)
├── frontend/               # Frontend React + Vite
│   └── src/
│       ├── components/     # Componentes reutilizáveis (Layout)
│       └── pages/          # Páginas (Login, Dashboard, Kanban, GestaoEquipe)
├── architecture/           # POPs de IA (CFO Virtual, Conciliação, Orçamentos)
├── docker-compose.yml      # Orquestração Docker
├── Dockerfile              # Imagem do backend
└── requirements.txt        # Dependências Python
```

---
*Desenvolvido focado em inovação, UX premium e escalabilidade.*
