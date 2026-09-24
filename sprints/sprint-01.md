# Sprint 01 — Implementação do MVP e Persistência Relacional

## 1. Identificação da sprint
Período de 01/08/2026 a 20/08/2026. Status: concluída.

## 2. Objetivo da sprint
Implementar os módulos centrais da interface (Hub Empresarial e Hub Pessoal), migrar a camada de dados de mocks em memória para persistência real em MySQL 8.0 com SQLAlchemy 2.0 assíncrono, e configurar o ambiente conteinerizado com Docker Compose.

## 3. Entregas e funcionalidades desenvolvidas

### 3.1 Frontend (React 19 + Tailwind v4 + Obsidian Flow)
No Hub Empresarial: dashboard operacional e financeiro com gráficos Recharts (DRE e fluxo de caixa D+90), quadro Kanban com drag and drop HTML5, cronômetro de execução e cálculo de *Cost-per-Task*, gestão de equipes com CTC (CLT e PJ), histórico de alterações salariais e modal de desligamento, além dos módulos de Fornecedores, Lançamentos Financeiros e Exportação.

No Hub Pessoal: navegação independente via rotas na barra lateral (`/pessoal/:tab`), com os módulos de Extrato, Contas & Cartões, Orçamentos por Categoria, Metas, Dívidas/Parcelamentos, Assinaturas, Divisão de Despesas (*Split*) e Timeboxes/OKRs.

No cabeçalho, um alternador de workspace (Empresarial ↔ Pessoal) para usuários com plano `completo`.

### 3.2 Backend e banco de dados (FastAPI + MySQL 8.0)
Cerca de 28 modelos SQLAlchemy criados em `app/db/models.py`, com 13 routers convertidos para consultas assíncronas. Uma rotina de seed idempotente inicializa os dados de teste (usuários, projetos, funcionários) automaticamente. Senhas e tokens saíram do código-fonte para o `.env`, e a `SECRET_KEY` foi rotacionada.

### 3.3 Infraestrutura
`docker-compose.yml` orquestrando 4 serviços: `db` (MySQL 8.0), `redis` (Redis 7), `backend` (FastAPI) e `frontend` (React/Vite).

## 4. Evidências de conclusão
- Código-fonte neste repositório — o histórico da Sprint 01 foi preservado por merge.
- Swagger OpenAPI operacional em `http://localhost:8000/docs`.
- Sistema executando localmente e via Docker, sem pendências impeditivas.
