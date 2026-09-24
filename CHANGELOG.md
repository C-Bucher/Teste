# Histórico de mudanças

## 2026-09-23 - Isolamento, autorização e persistência operacional

- Dados empresariais passaram a ser isolados por `company_id` em modelos, CRUDs, busca, notificações e exportações.
- O Hub Pessoal passou a usar o usuário autenticado como `owner_id`, com verificação de propriedade nas mutações.
- Kanban e clientes agora exigem o módulo correspondente; escopos de plano são verificados no backend e nas rotas React.
- Assinaturas, faturas, timers ativos, calendário de trabalho e preferências de notificação passaram a ser persistidos no banco.
- Corrigidos: timer inexistente adicionando uma hora, resposta de custo divergente, DRE ignorando período e dupla contagem no fluxo de caixa.
- IDs de empresa/usuário passaram a usar UUID; cadastro valida senha/plano e a gestão de acessos protege o último administrador.
- Exportações passaram a aceitar apenas CSV/JSON válidos e a consultar dados reais da empresa.
- CORS tornou-se configurável e `SECRET_KEY` insegura bloqueia inicialização em produção.
- Adicionada migração aditiva de compatibilidade para bancos existentes e ADR-006.

Registre aqui as mudanças relevantes por sprint ou marco avaliativo.

## Sprint 00 - Planejamento

- Criação do repositório.
- Definição do problema, da equipe, dos papéis e do backlog inicial.

## Sprint 01 - MVP e Persistência Relacional

- Hub Empresarial e Hub Pessoal no frontend (React 19 + Tailwind v4, design Obsidian Flow).
- Backend FastAPI com SQLAlchemy 2.0 assíncrono, seed idempotente e Docker Compose (MySQL, Redis, backend, frontend).
- Segredos migrados para `.env`.

## Sprint 02 - Controle de Acesso por Cargo e Onboarding

- Hierarquia de cargos configurável com bloqueio real (HTTP 403) no servidor e nas páginas (RF16, [ADR 004](docs/decisoes/adr-004-permissoes-por-cargo-e-onboarding.md)).
- Onboarding guiado de 3 passos, painel de conexões de API e criação de logins pelo Admin (RF17–RF19).
- Correções de segurança em `/auth/users` (escalação de privilégio), `is_active` exigido, busca filtrada por módulo.
- Repositório consolidado: código e histórico completo incorporados, README e `.gitignore` unificados, documentação atualizada com a matriz de atendimento dos requisitos.
- Registradas como pendências: MT-1 (dados de negócio por empresa) e MT-2 (Hub Pessoal por usuário) — ver [BACKLOG](docs/BACKLOG.md).

## 2026-09-23 - Suporte a PostgreSQL Gerenciado (Supabase)

- `DATABASE_URL` passa a aceitar PostgreSQL (via `asyncpg`) além de MySQL e SQLite, com `.env.example` ativando o Supabase por padrão ([ADR 005](docs/decisoes/adr-005-suporte-postgresql-supabase.md)).
- `load_dotenv()` adicionado ao backend: a execução manual (fora do Docker) agora lê o `.env` automaticamente.
- Correção de segurança: um commit deste mesmo dia (`913f78d`) havia colado credenciais reais do Supabase e um `SECRET_KEY` real em texto puro no `README.md`; foram substituídas por placeholders (`3210242`). Os valores antigos ainda não foram rotacionados no Supabase — ver SEC-5 no [BACKLOG](docs/BACKLOG.md).
- Registrada como pendência a DB-5: a troca entre Supabase, MySQL (Docker) e SQLite exige editar manualmente a `DATABASE_URL` no `.env`.
