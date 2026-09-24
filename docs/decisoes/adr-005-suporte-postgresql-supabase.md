# ADR 005 — Suporte a PostgreSQL Gerenciado (Supabase) como Banco Padrão

## Status
Aprovado / Implementado (com pendências registradas — ver Consequências)

## Data
2026-09-23

## Contexto
O ADR 001 fixou MySQL 8.0 via Docker Compose como banco relacional do projeto. Isso funciona bem localmente, mas exige que cada avaliador ou colega suba o Compose inteiro (4 containers) só para ver o sistema funcionando com dados reais, e não oferece um banco acessível fora da máquina de quem está rodando. A equipe decidiu adicionar um banco PostgreSQL gerenciado (Supabase) como alternativa que qualquer membro possa acessar sem subir infraestrutura local.

## Decisão
1. **`DATABASE_URL` continua sendo a única fonte de verdade** sobre qual banco o backend usa (`app/db/session.py`), agora aceitando `postgresql+asyncpg://…` além de `mysql+aiomysql://…` e `sqlite+aiosqlite://…`; quando o dialeto é `postgresql`, o engine é criado com `connect_args={"ssl": "require"}`.
2. **`.env.example` passa a trazer a `DATABASE_URL` do Supabase ativa por padrão**, com a linha do MySQL comentada como alternativa.
3. **`load_dotenv()`** foi adicionado em `app/core/config.py` e `app/db/session.py`, para que a execução manual (fora do Docker) leia o `.env` automaticamente — sem isso, era preciso exportar as variáveis manualmente no terminal (item **DB-1** do backlog).
4. `SUPABASE_URL` e `SUPABASE_ANON_KEY` foram adicionados ao `.env.example`, mas **nenhum código em `app/` ou `frontend/src/` os lê hoje** — a integração é só via `DATABASE_URL` (conexão direta ao Postgres pelo pooler), não via SDK do Supabase.
5. `asyncpg` foi adicionado a `requirements.txt` como driver do dialeto `postgresql+asyncpg`.

## Alternativas consideradas
- **Manter só MySQL/Docker:** mais simples de raciocinar, mas exige Docker rodando para qualquer verificação com banco real; adiado por ora.
- **Usar o SDK do Supabase (`supabase-py`) em vez de conexão SQL direta:** exigiria reescrever a camada de acesso a dados (hoje 100% SQLAlchemy); fora de escopo desta mudança pontual.

## Consequências
- **Positivas:** qualquer pessoa com a `DATABASE_URL` correta roda o backend com um banco real, sem subir Docker; a execução manual passa a ler `.env` automaticamente (resolve parte do **DB-1**).
- **Negativas / pendências (ver [BACKLOG](../BACKLOG.md)):**
  - **SEC-5 (crítico):** o commit que introduziu esta mudança (`913f78d`) colou a senha real do banco, a `SUPABASE_ANON_KEY` real e um `SECRET_KEY` real em texto puro no `README.md`, em vez de placeholders. Um commit seguinte (`3210242`) corrigiu o `README` para usar placeholders, mas **os valores antigos permanecem válidos e visíveis no histórico do Git** — a equipe optou, em 2026-09-23, por não rotacioná-los por ora. Isso é uma exposição real de credencial em um repositório visível a toda a organização no GitHub, não só à equipe.
  - **DB-5:** como o `.env.example` agora ativa o Supabase por padrão e o `docker-compose.yml` repassa `DATABASE_URL=${DATABASE_URL}` ao container do backend sem sobrescrevê-la, quem sobe o Docker Compose sem editar manualmente essa linha faz o backend em Docker tentar falar com o Supabase, não com o MySQL que o próprio Compose acabou de subir. O fallback SQLite também deixou de ser automático (era o padrão quando não havia `.env`); agora exige remover/comentar a linha `DATABASE_URL` por completo.
  - Este commit não passou pelo fluxo de `issue` → `branch` → `pull request` → `review` descrito em [CONTRIBUTING.md](../../CONTRIBUTING.md): foi um push direto na `main`, com o autor Git identificado como `Trindaddy <admin@techconnect.com.br>` (o e-mail do usuário administrador de demonstração do seed, não um e-mail pessoal).

## Links relacionados
- Decisão anterior: [ADR 001](adr-001-stack-fastapi-mysql-sqlalchemy.md)
- Backlog: [DB-1, DB-5, SEC-5](../BACKLOG.md)
- Requisitos: RNF02, RNF03, RNF05 em [docs/requisitos.md](../requisitos.md)
