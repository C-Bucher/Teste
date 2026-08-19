# Swap SQLite → MySQL real + fechar pendências de segurança e MySQL-readiness

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Ligar o backend (já 100% migrado para SQLAlchemy async) ao MySQL 8 real via Docker Compose, corrigir a exposição de credenciais em texto puro no `docker-compose.yml`, e fechar os 3 achados de "MySQL-readiness" que a revisão final do plano de banco de dados deixou documentados para esta etapa (cascata de FK, `pool_recycle`, e-mail case-insensitive).

**Architecture:** Nenhum model ou router muda de lógica — a troca de banco é só a `DATABASE_URL`, exatamente como desenhado desde o início. O trabalho real desta fase é: (1) configuração seesegura (variáveis de ambiente em `.env`, não versionado), (2) os 3 ajustes de robustez que só importam quando o banco é MySQL de verdade (SQLite não força FK nem tem os mesmos limites de conexão/collation).

**Tech Stack:** `aiomysql` como driver assíncrono, mesmo SQLAlchemy 2 já em uso.

## Contexto importante

Havia um deploy Docker antigo (semanas/meses) deste mesmo projeto rodando em paralelo, com um schema divergente e ocupando as portas 8000/5173/3306 — já foi parado (`docker compose down`, só os 4 containers deste projeto: db/redis/backend/frontend). Os volumes nomeados (`techconnect20-main_mysql_data`, `techconnect20-main_uploads_data`) continuam existindo no disco; como o MySQL vai subir de novo apontando pro mesmo volume, ele pode conter dados de schema antigo incompatível — por segurança, a Task 1 abaixo remove esse volume antes de subir (ele não tem nada que precise ser preservado — dados de teste de um deploy semanas mais velho, com um schema totalmente diferente do atual).

## Global Constraints

- Nenhuma mudança de contrato de API — só a fonte de dados muda de SQLite pra MySQL.
- Projeto é repositório git na branch `main` — cada task termina com commit (arquivos de segredo real, como `.env`, nunca são commitados).
- Sem test runner configurado — verificação é manual, com o stack Docker rodando de verdade.

---

### Task 1: `DATABASE_URL` real + segredos fora do compose + `pool_recycle`

**Files:**
- Modify: `docker-compose.yml`
- Modify: `requirements.txt`
- Modify: `app/db/session.py`
- Create: `.env` (não commitado — já deve estar no `.gitignore`, confirmar)
- Create: `.env.example` (commitado, com os nomes das variáveis e valores de placeholder, sem segredo real)
- Modify (se necessário): `.gitignore`

- [ ] **Step 1: Adicionar `aiomysql` como dependência**

Em `requirements.txt`, adicionar `aiomysql` (nova linha, junto de `aiosqlite`).

- [ ] **Step 2: Criar `.env` e `.env.example`**

Criar `.env` na raiz do projeto (não commitado) com os valores reais que hoje estão hardcoded no `docker-compose.yml`:

```
SECRET_KEY=***REMOVED-SECRET_KEY***
GEMINI_API_KEY=***REMOVED-GEMINI_API_KEY***
MYSQL_ROOT_PASSWORD=rootpassword123
MYSQL_DATABASE=techconnect
MYSQL_USER=techuser
MYSQL_PASSWORD=techpassword123
DATABASE_URL=mysql+aiomysql://techuser:techpassword123@db:3306/techconnect
```

Criar `.env.example` (este SIM é commitado) com a mesma estrutura mas valores de placeholder:

```
SECRET_KEY=troque-por-uma-chave-aleatoria-longa
GEMINI_API_KEY=sua-chave-gemini-aqui
MYSQL_ROOT_PASSWORD=troque-esta-senha
MYSQL_DATABASE=techconnect
MYSQL_USER=techuser
MYSQL_PASSWORD=troque-esta-senha
DATABASE_URL=mysql+aiomysql://techuser:troque-esta-senha@db:3306/techconnect
```

Confirmar que `.gitignore` já ignora `.env` (deve estar lá desde a Task 1 do plano de banco de dados) — se não estiver, adicionar.

**Nota de segurança**: a chave Gemini real (`***REMOVED-GEMINI_API_KEY***`) e o `SECRET_KEY` real, listados acima, já estavam commitados em texto puro no histórico do git deste repositório antes desta task. Mover para `.env` impede que continuem sendo commitados dali pra frente, mas **não remove o que já está no histórico**. Isso é uma limitação conhecida — sinalizar no relatório final, não tentar reescrever o histórico do git nesta task (fora de escopo, requer decisão explícita do usuário).

- [ ] **Step 3: `docker-compose.yml` — usar `.env`, remover segredo hardcoded, adicionar `DATABASE_URL`, remover o volume antigo**

Adicionar `env_file: .env` ao serviço `backend`. Trocar os valores hardcoded de `environment:` do serviço `backend` para referenciar variáveis do `.env` (sintaxe `${VAR}`), e adicionar `DATABASE_URL`:

```yaml
  backend:
    build: .
    container_name: techconnect_backend
    restart: always
    working_dir: /app
    env_file:
      - .env
    environment:
      - MYSQL_HOST=db
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=HS256
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./:/app
      - uploads_data:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

No serviço `db`, trocar os valores hardcoded de `MYSQL_ROOT_PASSWORD`/`MYSQL_DATABASE`/`MYSQL_USER`/`MYSQL_PASSWORD` para `${...}` também, referenciando o mesmo `.env` (adicionar `env_file: .env` ao serviço `db` também).

Antes de subir o stack, remover o volume `mysql_data` antigo (dados de um deploy semanas mais velho, schema incompatível com o atual):

```bash
docker volume rm techconnect20-main_mysql_data
```

(Se o comando falhar porque o volume está em uso por algo, parar primeiro qualquer container que o esteja usando — não deve haver nenhum, já que o stack foi derrubado antes desta task.)

- [ ] **Step 4: `pool_recycle` em `session.py`**

Em `app/db/session.py`, adicionar `pool_recycle=280` (segundos, abaixo do `wait_timeout` padrão de 8h do MySQL, mas um valor pequeno como 280s é seguro e comum) ao `create_async_engine(...)`:

```python
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True, pool_recycle=280)
```

(`pool_pre_ping=True` também vale adicionar — testa a conexão antes de cada uso, evitando erros de "MySQL server has gone away". Ambos os parâmetros são inofensivos no SQLite, não quebram nada lá.)

- [ ] **Step 5: Subir o stack e verificar**

```bash
docker compose up -d --build
```

Acompanhar os logs do backend (`docker compose logs -f backend`) até confirmar que ele conectou no MySQL e rodou o seed sem erro. Testar login via `curl http://localhost:8000/api/v1/auth/login` com um dos 3 usuários seedados, confirmar 200. Reiniciar o container do backend (`docker compose restart backend`) e confirmar que os dados continuam lá (prova de que está persistindo no MySQL de verdade, não teve fallback silencioso pra SQLite). Testar 2-3 endpoints adicionais dos módulos migrados (ex: `GET /employees/`, `GET /kanban/clients`) pra confirmar que o schema criado no MySQL está correto.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml requirements.txt app/db/session.py .env.example .gitignore
git commit -m "feat: wire real MySQL connection via Docker Compose, move secrets to .env"
```

(`.env` nunca é commitado — confirmar que `git status` não o lista como staged.)

---

### Task 2: Cascata de FK + e-mail case-insensitive

**Files:**
- Modify: `app/db/models.py`
- Modify: `app/api/v1/endpoints/auth.py`

**Contexto**: a revisão final do plano de banco de dados documentou 2 comportamentos que funcionam sem erro no SQLite (que não força chaves estrangeiras por padrão) mas que quebrariam com um `IntegrityError` (500) assim que o banco fosse MySQL de verdade — que é exatamente o que a Task 1 acabou de fazer. Esta task fecha essas duas pendências, agora que dá pra testar contra o MySQL real.

- [ ] **Step 1: `ondelete="SET NULL"` nas FKs afetadas**

Em `app/db/models.py`, ajustar as colunas `ForeignKey` que hoje ficam "penduradas" (referenciando um registro já excluído) quando o registro pai é apagado:

- `FinancialEntryModel.supplier_id` — hoje `ForeignKey("suppliers.id")`, trocar para `ForeignKey("suppliers.id", ondelete="SET NULL")`. Também garantir que a própria coluna aceita `nullable=True` (já deveria aceitar, já que despesas antigas de fornecedor desativado continuam existindo).
- `ProjectModel.client_id` — mesmo tratamento: `ForeignKey("clients.id", ondelete="SET NULL")`, coluna `nullable=True`.
- Qualquer outra FK que a Task 9 (migração do `kanban.py`) ou tasks irmãs tenham deixado sem `ondelete` e que sofra do mesmo problema — ler `del_sup`, `del_client`, `del_cc` em `suppliers.py`/`clients.py`/`company.py` pra confirmar quais tabelas são realmente afetadas por exclusões que hoje deixam referência pendurada, e aplicar `ondelete="SET NULL"` só nessas, sem tocar em FKs que não têm esse problema.

Como o MySQL só aplica `ondelete` na criação da tabela (não retroativo em tabela já existente), isso significa que o schema precisa ser recriado do zero pra pegar essa mudança — o volume MySQL já foi recriado do zero na Task 1, então isso deve funcionar automaticamente já que as tabelas serão criadas pela primeira vez com o schema novo. Se por algum motivo o container MySQL da Task 1 já tiver essas tabelas criadas (schema antigo, sem `ondelete`), apagar o volume de novo (`docker compose down -v` seguido de `docker compose up -d --build`) pra forçar recriação.

- [ ] **Step 2: E-mail case-insensitive no login/cadastro**

Em `app/api/v1/endpoints/auth.py`, normalizar o e-mail pra minúsculas antes de comparar ou gravar, em `login`, `register` e no lookup do `/refresh` — e em `app/core/security.py`'s `get_current_user`. Padrão: `email.strip().lower()` no momento em que o valor chega da requisição, tanto pra gravar (`UserModel(email=b.email.lower(), ...)`) quanto pra consultar (`UserModel.email == p.get("email", "").lower()`). Isso evita que o comportamento mude de "case-sensitive" (SQLite, hoje) pra "case-insensitive" (MySQL, collation padrão) de forma inconsistente — normalizando sempre pra minúsculas, o comportamento fica determinístico nos dois bancos.

- [ ] **Step 3: Verificar**

Com o stack MySQL rodando (da Task 1): excluir um fornecedor que tenha lançamentos financeiros vinculados (ex: `sup-001`, ligado a vários `FINANCIAL_ENTRIES` do seed) e confirmar que retorna 200, não 500 — e que o lançamento financeiro correspondente passa a ter `supplier_id: null` em vez de manter uma referência quebrada. Mesmo teste para excluir um cliente com projetos vinculados. Testar login com o e-mail em maiúsculas (`ADMIN@TECHCONNECT.COM.BR`) e confirmar que funciona igual ao e-mail original.

- [ ] **Step 4: Commit**

```bash
git add app/db/models.py app/api/v1/endpoints/auth.py app/core/security.py
git commit -m "fix: add FK cascade (SET NULL) and normalize email case for MySQL compatibility"
```
