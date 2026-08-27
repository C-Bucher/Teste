# Sprint 01 — Implementação do MVP e Persistência Relacional

## 1. Identificação da Sprint
- **Período:** 01/08/2026 a 20/08/2026
- **Status:** Concluída

## 2. Objetivo da Sprint
Implementar os módulos centrais da interface (Hub Empresarial e Hub Pessoal), migrar a camada de dados de mocks em memória para persistência real em MySQL 8.0 com SQLAlchemy 2.0 Async e configurar o ambiente de execução conteinerizado com Docker Compose.

## 3. Entregas e Funcionalidades Desenvolvidas

### 3.1 Frontend (React 19 + Tailwind v4 + Obsidian Flow)
- **Hub Empresarial:**
  - Dashboard operacional e financeiro com gráficos Recharts (DRE e fluxo de caixa D+90).
  - Quadro Kanban com Drag & Drop HTML5, cronômetro de execução e cálculo de *Cost-per-Task*.
  - Gestão de Equipes com cálculo de CTC (CLT e PJ), histórico de alterações salariais e modal de desligamento.
  - Módulos de Fornecedores, Lançamentos Financeiros e Exportação.
- **Hub Pessoal:**
  - Navegação independente via rotas da barra lateral (`/pessoal/:tab`).
  - Módulos de Extrato, Contas & Cartões, Orçamentos por Categoria, Metas, Dívidas/Parcelamentos, Assinaturas, Divisão de Despesas (*Split*) e Timeboxes/OKRs.
- **Controle de Acesso:**
  - Alternador de workspace (Empresarial ↔ Pessoal) no cabeçalho para usuários com plano `completo`.

### 3.2 Backend & Banco de Dados (FastAPI + MySQL 8.0)
- **Modelagem Relacional:** ~28 modelos SQLAlchemy criados em `app/db/models.py`.
- **Rotas e Endpoints Migrados:** 13 routers convertidos para consultas assíncronas no banco de dados.
- **Rotina de Seed Idempotente:** Inicialização automática de dados de teste (usuários, projetos, funcionários).
- **Segurança de Credenciais:** Remoção de senhas e tokens do código-fonte, migração para `.env` e rotação da `SECRET_KEY`.

### 3.3 Infraestrutura
- Configuração de `docker-compose.yml` orquestrando 4 serviços: `db` (MySQL 8.0), `redis` (Redis 7), `backend` (FastAPI) e `frontend` (React/Vite).

## 4. Evidências de Conclusão
- Repositório de código atualizado: [gabrielsalles-bit/TechConnect2.0](https://github.com/gabrielsalles-bit/TechConnect2.0)
- Swagger OpenAPI operacional em `http://localhost:8000/docs`.
- Sistema executando localmente e via Docker sem pendências impeditivas.
