# Persistência Real (SQLite → MySQL-ready) Implementation Plan

**Goal:** Substituir `app/db/database.py` (listas Python em memória, perdem tudo a cada restart) por persistência real via SQLAlchemy 2 assíncrono, sem mudar nenhum contrato de API (mesmas rotas, mesmos formatos de request/response) — o frontend não deve perceber diferença nenhuma.

**Architecture:** Camada de sessão assíncrona (`app/db/session.py`) + modelos ORM completos (`app/db/models.py`, expandindo os 6 stubs não usados hoje) + script de seed idempotente que popula os mesmos dados de demonstração que já existem. Cada router (`app/api/v1/endpoints/*.py`) troca acesso a lista Python por consulta ao banco via `Depends(get_db)`, convertendo o resultado para dict com um helper compartilhado (`model_to_dict`) — preserva exatamente o mesmo formato JSON que os endpoints já devolvem hoje, sem introduzir uma camada de schemas Pydantic nova.

**Tech Stack:** SQLAlchemy 2.0 (async), `aiosqlite` como driver hoje. Banco: arquivo `techconnect.db` na raiz do projeto (gitignored). Sem Alembic nesta fase — tabelas criadas via `Base.metadata.create_all()` na subida do backend.

## Contexto importante

O Docker Desktop não está disponível nesta máquina agora (serviço `com.docker.service` parado, sem conseguir subir de forma não-interativa). O `docker-compose.yml` já provisiona um container MySQL 8 real, e a documentação do projeto (DAS) manda usar MySQL — isso continua sendo o alvo declarado. A decisão desta fase é usar SQLite **hoje**, projetando a camada de acesso a dados para que a troca para MySQL seja apenas: (1) trocar `DATABASE_URL` no `.env`, (2) instalar `aiomysql` (já listado como dependência futura), (3) subir o `docker-compose.yml`. Nenhum model ou router precisa mudar — SQLAlchemy abstrai o dialeto. Isso está registrado aqui para não ser esquecido; **não é permanente**.

## Global Constraints

- Nenhuma mudança de contrato de API: mesmos paths, mesmos métodos, mesmo formato de request/response que os endpoints já devolvem hoje (verificar comparando com o código atual de cada router antes de migrar).
- IDs continuam sendo strings no mesmo formato já usado (`f"emp-{uuid.uuid4().hex[:6]}"` etc.) — não trocar para UUID nativo ou inteiro autoincrement.
- Datas continuam armazenadas e devolvidas como strings ISO (`YYYY-MM-DD` ou ISO datetime), exatamente como os mocks fazem hoje via `.isoformat()` — usar colunas `String` para datas, não `Date`/`DateTime` nativos, para não mudar a serialização que o frontend já espera.
- Campos que hoje são listas/dicts aninhados em Python (ex.: `PersonalSplit.participants`, `PersonalOkr.key_results`) viram colunas `JSON` do SQLAlchemy — funciona em SQLite e MySQL sem mudança.
- `Plans`, `Checkout`, `Subscription` (billing mock) ficam de fora desta fase — continuam como estão hoje (não persistidos), por decisão já combinada com o usuário.
- Sem test runner configurado — verificação é manual: reiniciar o backend e confirmar que os dados persistem (não voltam ao estado inicial dos mocks).
- Projeto é repositório git (branch `main`) — cada task termina com commit.
- `.env`/`techconnect.db` devem ir para `.gitignore` (banco de dados não é versionado; se `.gitignore` não existir, criar).

---

## Fase 0 — Fundação

### Task 1: Camada de sessão assíncrona + dependências

**Files:**
- Create: `app/db/session.py`
- Create: `app/db/utils.py`
- Modify: `requirements.txt`
- Modify: `app/main.py`
- Modify (or create): `.gitignore`

**Interfaces:**
- Produces: `get_db()` (dependência FastAPI, `AsyncSession`), `init_db()` (cria tabelas), `model_to_dict(obj)` (converte instância ORM em dict), `engine`. Consumido por toda task subsequente.

- [ ] **Step 1: Dependências**

Adicionar ao final de `requirements.txt`:

```
sqlalchemy[asyncio]>=2.0
aiosqlite
```

- [ ] **Step 2: `app/db/session.py`**

```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./techconnect.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session_maker() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 3: `app/db/utils.py`**

```python
def model_to_dict(obj) -> dict:
    """Converts a SQLAlchemy ORM instance to a plain dict matching the
    same field names/shape the old in-memory mock dicts used, so every
    router's response format stays identical after the DB migration."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def models_to_dicts(objs) -> list[dict]:
    return [model_to_dict(o) for o in objs]
```

- [ ] **Step 4: Wire startup + seed into `app/main.py`**

At the top of `app/main.py`, add the import:

```python
from app.db.session import init_db
from app.db.seed import seed_if_empty
```

Add a startup event, right after the `app = FastAPI(...)` line and before `app.add_middleware(...)`:

```python
@app.on_event("startup")
async def on_startup():
    await init_db()
    await seed_if_empty()
```

(`app.db.seed` is created in Task 3 — this import will fail until then; that's expected and fine, Task 1 and Task 2 land before Task 3 runs, or note it as expected transient breakage within this same task sequence — the implementer should NOT attempt to run the server successfully until Task 3 also exists. If you need to smoke-test Task 1 in isolation, comment out the `seed_if_empty` import/call temporarily and verify `init_db()` alone creates an empty `techconnect.db` file, then restore the import before finishing — the file must NOT be committed in a broken state.)

- [ ] **Step 5: `.gitignore`**

Ensure `.gitignore` at the project root contains (add if missing, create the file if it doesn't exist):

```
techconnect.db
.env
```

- [ ] **Step 6: Verify**

Since `app/db/models.py` (Task 2) doesn't exist with a `Base` yet, this task cannot be smoke-tested end-to-end alone. Confirm instead: `pip install -r requirements.txt` succeeds with the two new packages, and `python -c "import ast; ast.parse(open('app/db/session.py').read())"` and same for `app/db/utils.py` and the diff to `app/main.py` parse without syntax errors. Note in your report that full runtime verification happens after Task 2+3 land.

- [ ] **Step 7: Commit**

```bash
git add app/db/session.py app/db/utils.py requirements.txt app/main.py .gitignore
git commit -m "feat: add async SQLAlchemy session layer (SQLite, MySQL-ready)"
```

---

### Task 2: Modelos ORM completos

**Files:**
- Modify: `app/db/models.py` (hoje tem 6 tabelas não usadas por ninguém — `CompanyModel`, `UserModel`, `PlanModel`, `SubscriptionModel`, `InvoiceModel`, `EmployeeModel`; expandir/ajustar conforme necessário e adicionar todas as tabelas faltantes)

**Interfaces:**
- Produces: `Base` (declarative base, já existe), e uma classe ORM por tabela abaixo. Consumido por toda task de migração de router (Tasks 4-13).

**Context:** `app/db/database.py` (leia o arquivo inteiro antes de começar — é a fonte de verdade de todo campo que precisa existir) tem 20 estruturas de dados mock. Você vai criar um modelo SQLAlchemy para cada uma. Os 6 modelos que já existem em `models.py` (`CompanyModel`, `UserModel`, `EmployeeModel`, mais `PlanModel`/`SubscriptionModel`/`InvoiceModel` que ficam fora de escopo desta fase — não delete, apenas não os altere) usam `String(50)` para PKs e `declarative_base()` clássico — mantenha esse estilo para consistência, não migre para o estilo `Mapped[]`/`mapped_column()` do SQLAlchemy 2 nesta task.

**Tabelas a criar** (nome sugerido → lista mock de origem → campos, com tipo):

1. `UserModel` (já existe, ajustar): adicionar campo `plan_scope = Column(String(20), default="completo")` que falta hoje. Fonte: `USERS_DB`.
2. `EmployeeModel` (já existe, ajustar): hoje só tem `id, company_id, full_name, email, role, contract_type, base_salary, is_active, hire_date`. Adicionar os campos que faltam vindos de `EMPLOYEES`: `cpf` (String), `position` (String), `ctc_snapshot` (Float), `ctc_monthly` (Float), `hourly_rate` (Float), `hourly_cost` (Float), `start_date` (String), `end_date` (String, nullable).
3. `SalaryHistoryModel` (nova): `id, employee_id (FK), base_salary, ctc_monthly, ctc_snapshot, changed_at (String), reason (String)`. Fonte: o array retornado hoje por `GET /employees/{id}/salary-history` em `employees.py` (hoje hardcoded — vira tabela real).
4. `SupplierModel` (nova): `id, name, cnpj_cpf, category, is_active, email`. Fonte: `SUPPLIERS`.
5. `FinancialEntryModel` (nova): `id, type, amount (Float), description, due_date (String), payment_date (String, nullable), status, category, supplier_id (String, nullable, FK), cost_center`. Fonte: `FINANCIAL_ENTRIES`.
6. `ClientModel` (nova): `id, name, email, phone, cnpj, contact_name, address, segment, status`. Fonte: `KANBAN_CLIENTS`.
7. `ProjectModel` (nova): `id, client_id (FK), name, description, status, start_date (String), end_date (String)`. Fonte: `KANBAN_PROJECTS`.
8. `KanbanColumnModel` (nova): `id, project_id (FK), name, order (Integer)`. Fonte: chaves `columns` dentro de `KANBAN_BOARDS[proj_id]`.
9. `KanbanCardModel` (nova): `id, column_id (FK), title, description, assignee (String), assignee_id (String, nullable), cost_per_task (Float), total_time_seconds (Integer), status, priority, due_date (String)`. Fonte: `cards` dentro de cada coluna em `KANBAN_BOARDS`.
10. `CardCommentModel` (nova): `id, card_id (FK), author, content, created_at (String)`. Fonte: hoje só existe em memória por request (`POST /kanban/cards/{cid}/comments` em `kanban.py` não persiste nada — vira tabela real).
11. `NotificationModel` (nova): `id, title, message, type, is_read (Boolean), created_at (String)`. Fonte: `NOTIFICATIONS`.
12. `CostCenterModel` (nova): `id, name, code`. Fonte: `COST_CENTERS`.
13. `CategoryModel` (nova): `id, name, type`. Fonte: `CATEGORIES`.
14. `CompanyModel` (já existe, ajustar): hoje tem `id, name, cnpj, email, phone, address, created_at`. Adicionar `fiscal_year_start (Integer)` que falta. Fonte: `COMPANY`.
15. `PersonalEntryModel` (nova): `id, owner_id (String, FK para UserModel — use `"usr-001"` como default/fallback já que hoje não há isolamento por usuário nos mocks), type, amount (Float), description, date (String), category`. Fonte: `PERSONAL_ENTRIES`.
16. `PersonalCategoryModel` (nova): `id, owner_id, name, type`. Fonte: hoje `personal.py` provavelmente deriva categorias de algum lugar — leia `app/api/v1/endpoints/personal.py` para confirmar a origem exata antes de modelar.
17. `ExportLogModel` (nova): `id, type, format, status, created_at (String), size_bytes (Integer)`. Fonte: `EXPORT_LOGS`.
18. `PersonalAccountModel` (nova): `id, owner_id, name, type, balance (Float), limit (Float, nullable), closing_day (Integer, nullable), due_day (Integer, nullable)`. Fonte: `PERSONAL_ACCOUNTS`.
19. `PersonalBudgetModel` (nova): `id, owner_id, category, limit_amount (Float), spent_amount (Float)`. Fonte: `PERSONAL_BUDGETS`.
20. `PersonalGoalModel` (nova): `id, owner_id, name, target_amount (Float), current_amount (Float), target_date (String)`. Fonte: `PERSONAL_GOALS`.
21. `PersonalDebtModel` (nova): `id, owner_id, name, total_amount (Float), remaining_amount (Float), installments_total (Integer), installments_paid (Integer), interest_rate (Float)`. Fonte: `PERSONAL_DEBTS`.
22. `PersonalSubscriptionModel` (nova): `id, owner_id, name, amount (Float), billing_day (Integer), category, is_active (Boolean)`. Fonte: `PERSONAL_SUBSCRIPTIONS`.
23. `PersonalSplitModel` (nova): `id, owner_id, description, total_amount (Float), participants (JSON)`. Fonte: `PERSONAL_SPLITS`. `participants` é uma lista de `{name, share, paid}` — usar `Column(JSON)`.
24. `PersonalTimeboxModel` (nova): `id, owner_id, title, start_time (String), end_time (String)`. Fonte: `PERSONAL_TIMEBOXES`.
25. `PersonalOkrModel` (nova): `id, owner_id, objective, key_results (JSON)`. Fonte: `PERSONAL_OKRS`. `key_results` é lista de strings — `Column(JSON)`.

Worked example (follow this exact pattern for every table above — `String(50)` primary key, no `Mapped[]` typing, matches the existing 6 models' style):

```python
class SupplierModel(Base):
    __tablename__ = "suppliers"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    cnpj_cpf = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    email = Column(String(255), nullable=True)


class FinancialEntryModel(Base):
    __tablename__ = "financial_entries"

    id = Column(String(50), primary_key=True)
    type = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    due_date = Column(String(20), nullable=True)
    payment_date = Column(String(20), nullable=True)
    status = Column(String(20), default="PENDENTE")
    category = Column(String(100), nullable=True)
    supplier_id = Column(String(50), ForeignKey("suppliers.id"), nullable=True)
    cost_center = Column(String(100), nullable=True)


class PersonalSplitModel(Base):
    __tablename__ = "personal_splits"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False, default="usr-001")
    description = Column(String(255), nullable=True)
    total_amount = Column(Float, nullable=False)
    participants = Column(JSON, nullable=False, default=list)
```

Add `JSON` to the SQLAlchemy import line at the top of `models.py` (`from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, ForeignKey, Text, JSON`).

Do not add `relationship()` back-references for every FK — only add them where a router will clearly need to navigate the relationship (e.g. `CompanyModel.employees` already exists). For the new tables, plain `Column(..., ForeignKey(...))` without a `relationship()` is fine; routers will query each table directly.

- [ ] **Step: Verify**

Run `python -c "from app.db.models import Base; print(len(Base.metadata.tables))"` from the project root — should print at least 25 (the 6 pre-existing plus the ~19-20 new ones; exact count depends on how `SalaryHistoryModel`/`PersonalCategoryModel` end up, both listed above). Confirm no import errors.

- [ ] **Step: Commit**

```bash
git add app/db/models.py
git commit -m "feat: add full ORM model set for all mock entities"
```

---

### Task 3: Seed idempotente

**Files:**
- Create: `app/db/seed.py`

**Interfaces:**
- Consumes: every model from Task 2, `async_session_maker` from Task 1.
- Produces: `seed_if_empty()`, called from `app/main.py`'s startup event (already wired in Task 1).

- [ ] **Step 1: Write the seed function**

Read `app/db/database.py` in full — every mock list/dict in that file becomes rows inserted here, using the exact same values (so the demo experience is unchanged). Structure:

```python
from datetime import datetime, timedelta, date
import bcrypt
from sqlalchemy import select
from app.db.session import async_session_maker
from app.db.models import (
    UserModel, EmployeeModel, SupplierModel, FinancialEntryModel, ClientModel,
    ProjectModel, KanbanColumnModel, KanbanCardModel, NotificationModel,
    CostCenterModel, CategoryModel, CompanyModel, PersonalEntryModel,
    ExportLogModel, PersonalAccountModel, PersonalBudgetModel, PersonalGoalModel,
    PersonalDebtModel, PersonalSubscriptionModel, PersonalSplitModel,
    # ... every model from Task 2
)

hoje = date.today()
def dias(n): return (hoje + timedelta(days=n)).isoformat()


async def seed_if_empty():
    async with async_session_maker() as session:
        result = await session.execute(select(UserModel).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # already seeded, do nothing

        admin_hash = bcrypt.hashpw(b"Admin@123", bcrypt.gensalt()).decode()
        session.add_all([
            UserModel(id="usr-001", email="admin@techconnect.com.br", full_name="Administrador", role="ADMIN", plan_scope="completo", password_hash=admin_hash, is_active=True, mfa_enabled=False),
            UserModel(id="usr-002", email="gerente@techconnect.com.br", full_name="Ana Souza", role="GERENTE", plan_scope="completo", password_hash=bcrypt.hashpw(b"Gerente@123", bcrypt.gensalt()).decode(), is_active=True, mfa_enabled=False),
            UserModel(id="usr-003", email="funcionario@techconnect.com.br", full_name="Carlos Mendes", role="FUNCIONARIO", plan_scope="completo", password_hash=bcrypt.hashpw(b"Func@123", bcrypt.gensalt()).decode(), is_active=True, mfa_enabled=False),
        ])
        # ... repeat for EVERY mock list in database.py, using the exact same
        # field values. Use `dias(n)` exactly as database.py does for any
        # relative-date field, so the seeded due dates/notification timestamps
        # stay relative to "today" just like the mock did.
        await session.commit()
```

Do this for **every** structure in `database.py`: `USERS_DB`, `EMPLOYEES`, `SUPPLIERS`, `FINANCIAL_ENTRIES`, `KANBAN_CLIENTS`, `KANBAN_PROJECTS`, `KANBAN_BOARDS` (unpack into `KanbanColumnModel` + `KanbanCardModel` rows — note `KANBAN_BOARDS` is a dict keyed by project id containing `{"columns": [...]}`, each column has `{"id", "name", "order", "cards": [...]}`), `NOTIFICATIONS`, `COST_CENTERS`, `CATEGORIES`, `COMPANY` (single row), `PERSONAL_ENTRIES`, `EXPORT_LOGS`, `PERSONAL_ACCOUNTS`, `PERSONAL_BUDGETS`, `PERSONAL_GOALS`, `PERSONAL_DEBTS`, `PERSONAL_SUBSCRIPTIONS`, `PERSONAL_SPLITS` (`participants` field maps straight into the `JSON` column). `PERSONAL_TIMEBOXES`/`PERSONAL_OKRS` are empty lists in the mock — seed nothing for those, just don't forget the tables exist for routers to write into later. `ACTIVE_TIMERS` is transient runtime state (`card_id -> {...}`), not durable data — do not seed it, and note in your report that it's intentionally excluded (Task 9, the kanban.py migration, decides where this now lives).

- [ ] **Step 2: Verify**

Start the backend fresh with no `techconnect.db` file present (`rm -f techconnect.db` first if one exists from Task 1's partial testing), run `uvicorn app.main:app --port 8000` from the project root, confirm it starts with no errors, then inspect the database: `python -c "import sqlite3; c = sqlite3.connect('techconnect.db'); print(c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"` and confirm every table from Task 2 is listed with the expected row counts (e.g. `SELECT COUNT(*) FROM users` should be 3, `SELECT COUNT(*) FROM employees` should be 5). Then restart the backend a second time (Ctrl+C, run again) and confirm no duplicate rows were inserted (row counts stay the same) — this proves the idempotency check works.

- [ ] **Step 3: Commit**

```bash
git add app/db/seed.py
git commit -m "feat: add idempotent seed matching existing mock demo data"
```

---

## Fase 1 — Migração dos routers (um por task, mesmo padrão)

Para cada task abaixo, o padrão de conversão é sempre o mesmo — leia o router atual por completo antes de editar, e para cada endpoint:
- Trocar `Depends(get_current_user)` sozinho por `Depends(get_current_user), db: AsyncSession = Depends(get_db)` (import `from sqlalchemy.ext.asyncio import AsyncSession` e `from app.db.session import get_db`).
- Trocar iteração sobre a lista Python (`next((x for x in LISTA if x["id"]==id), None)`) por `await db.get(Model, id)` (busca por PK) ou `await db.execute(select(Model).where(...))` seguido de `.scalars().all()`/`.scalar_one_or_none()` para os demais filtros.
- Trocar `LISTA.append(novo_dict)` por `db.add(NovoModel(**campos)); await db.commit(); await db.refresh(obj)`.
- Trocar `obj.update(d)` (mutação de dict) por `for k, v in d.items(): setattr(obj_orm, k, v)` seguido de `await db.commit()`.
- Toda resposta que hoje é um dict ou lista de dicts vinda direto da lista mock vira `model_to_dict(obj)` / `models_to_dicts(objs)` (de `app/db/utils.py`).
- **Preservar exatamente o mesmo formato de resposta** — se um endpoint hoje devolve `{"items": [...], "total": N, ...}`, continue devolvendo esse envelope, só trocando a fonte dos dados.
- Manter toda lógica de negócio que não depende da lista em memória (validações, cálculos como `hourly_rate = ctc/176`, filtros de query string) exatamente como está.

Cada task abaixo termina com: reiniciar o backend, testar cada endpoint do router via o frontend correspondente no navegador (não só via curl — a integração real importa), confirmar que os dados persistem entre restarts, e commit.

### Task 4: `app/api/v1/endpoints/auth.py`

Migra `USERS_DB` (dict por email) para consultas em `UserModel`. Cuidado: `USERS_DB` é indexado por email hoje (`USERS_DB[email]`), enquanto o banco será consultado por `select(UserModel).where(UserModel.email == email)`. O endpoint `/register` cria um novo usuário — vira `db.add(UserModel(...))`. `/refresh` busca por email OU por id (`next((v for v in USERS_DB.values() if v["id"]==p.get("sub")), None)`) — precisa de uma query com `or_()` ou duas tentativas sequenciais. Teste: login com os 3 usuários seedados, cadastro de um usuário novo, refresh de token.

### Task 4b: `app/core/security.py` — `get_current_user` para o banco real

**Descoberto durante a Task 4**: `get_current_user` (usado por `Depends(get_current_user)` em praticamente todo endpoint protegido do backend) continua lendo `USERS_DB` (o dict em memória de `app/db/database.py`), não `UserModel`. Os 3 usuários seedados escapam do bug por coincidência (mesmos dados presentes nos dois lugares hoje), mas qualquer usuário criado via `/register` depois da migração da Task 4 cai em 401 em todo endpoint que dependa de autenticação — porque não existe em `USERS_DB`. Sem corrigir isso agora, o mesmo bug se repetiria de forma mascarada em cada uma das 9 tasks de migração de router restantes.

**Files:**
- Modify: `app/core/security.py`

**Interfaces:**
- Consumes: `get_db` de `app/db/session.py`, `UserModel` de `app/db/models.py`.
- Produces: `get_current_user` continua com a mesma assinatura de uso (`Depends(get_current_user)`) para quem já a consome — FastAPI resolve a dependência aninhada `Depends(get_db)` automaticamente, então nenhum dos 13 arquivos de router precisa mudar a forma como chamam `get_current_user`.

- [ ] **Step 1: Migrar `get_current_user` para consulta assíncrona real**

`app/core/security.py` hoje (linhas 20-25):

```python
def get_current_user(creds:HTTPAuthorizationCredentials=Depends(bearer)):
    if not creds: raise HTTPException(401,"Token ausente")
    p=decode_token(creds.credentials)
    u=USERS_DB.get(p.get("email")) or next((v for v in USERS_DB.values() if v["id"]==p.get("sub")),None)
    if not u: raise HTTPException(401,"Usuario nao encontrado")
    return u
```

Substituir por:

```python
async def get_current_user(creds:HTTPAuthorizationCredentials=Depends(bearer), db: AsyncSession = Depends(get_db)):
    if not creds: raise HTTPException(401,"Token ausente")
    p=decode_token(creds.credentials)
    result = await db.execute(select(UserModel).where(or_(UserModel.email == p.get("email"), UserModel.id == p.get("sub"))))
    u = result.scalars().first()
    if not u: raise HTTPException(401,"Usuario nao encontrado")
    return model_to_dict(u)
```

Adicionar aos imports do topo do arquivo:

```python
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import UserModel
from app.db.utils import model_to_dict
```

E remover o import `from app.db.database import USERS_DB` (linha 8) — não é mais usado neste arquivo.

`return model_to_dict(u)` é importante: todo router que hoje faz `u["id"]`, `u["role"]` etc. sobre o retorno de `get_current_user` espera um dict simples, não uma instância ORM — devolver o dict mantém compatibilidade com os 13 routers sem precisar tocar em nenhum deles nesta task.

- [ ] **Step 2: Verificar**

Reiniciar o backend. Repetir exatamente o teste que expôs o bug: logar como um usuário seedado (deve continuar funcionando), cadastrar um usuário novo via `/cadastro`, e imediatamente testar um endpoint protegido qualquer com o token desse usuário novo (ex.: `GET /api/v1/auth/me`, ou qualquer chamada que o frontend faça logo após o cadastro) — confirmar que retorna 200, não mais 401. Reiniciar o backend de novo e repetir o teste com o mesmo usuário, confirmando que persiste.

- [ ] **Step 3: Commit**

```bash
git add app/core/security.py
git commit -m "fix: migrate get_current_user to query the real database instead of in-memory USERS_DB"
```

---

### Task 5: `app/api/v1/endpoints/employees.py` + histórico salarial

Migra `EMPLOYEES` para `EmployeeModel`, e o endpoint `/employees/{id}/salary-history` (hoje retorna 2 registros hardcoded calculados na hora) para consultar `SalaryHistoryModel` de verdade — ao criar/editar um colaborador com mudança de `base_salary`, inserir uma nova linha em `SalaryHistoryModel` (não seedada previamente para os 5 colaboradores mock, exceto se você preferir seedar 1-2 linhas de histórico por colaborador para não quebrar a demo — decida e documente no seu relatório). Teste: tela "Equipe" completa (listar, criar, editar, ver histórico, desligar).

### Task 6: `app/api/v1/endpoints/suppliers.py`

Migra `SUPPLIERS` para `SupplierModel`. Teste: tela "Fornecedores" completa (listar, criar, editar, desativar).

### Task 7: `app/api/v1/endpoints/financial.py`

Migra `FINANCIAL_ENTRIES` para `FinancialEntryModel`. O endpoint `/financial/dre` e `/financial/cashflow` fazem agregação em Python hoje sobre a lista — pode continuar agregando em Python após buscar todas as linhas do banco (`await db.execute(select(FinancialEntryModel))`), não precisa virar SQL agregado nesta fase. Teste: tela "Financeiro" completa (lançamentos, marcar como pago, DRE, fluxo de caixa) e o card "Transações Recentes" do Dashboard.

### Task 8: `app/api/v1/endpoints/company.py`

Migra `COMPANY` (registro único), `COST_CENTERS`, `CATEGORIES` para `CompanyModel`/`CostCenterModel`/`CategoryModel`. `/company/calendar` e `/company/ctc-params` hoje devolvem valores hardcoded sem nenhuma lista de origem — podem continuar hardcoded (fora de escopo persistir isso agora), apenas confirme lendo o arquivo. Teste: tela "Configurações" completa.

### Task 9: `app/api/v1/endpoints/kanban.py`

O maior deste grupo. Migra `KANBAN_CLIENTS`→`ClientModel`, `KANBAN_PROJECTS`→`ProjectModel`, `KANBAN_BOARDS`→`KanbanColumnModel`+`KanbanCardModel`, comentários (hoje não persistidos)→`CardCommentModel`. Para `ACTIVE_TIMERS` (dict em memória `card_id -> {started_at, employee_id, timer_id}`): pode continuar como um dict Python em memória neste módulo (é estado transiente de "timer rodando agora", não histórico — perdê-lo num restart do backend é aceitável e não é o que esta fase resolve). Ao parar um timer, o cálculo de `cost_per_task`/`total_time_seconds` que hoje atualiza o dict do card em memória passa a fazer `UPDATE` na linha do `KanbanCardModel` correspondente. Teste: tela "Projetos" completa — clientes, projetos, colunas, cards, drag-and-drop, timer, comentários.

### Task 10: `app/api/v1/endpoints/notifications.py`

Migra `NOTIFICATIONS` para `NotificationModel`. Teste: sino de notificações no header (contagem, marcar como lida, marcar todas).

### Task 11: `app/api/v1/endpoints/exports.py`

Migra `EXPORT_LOGS` para `ExportLogModel`. Teste: tela "Exportação".

### Task 12: `app/api/v1/endpoints/personal.py` (parte 1 — base)

Migra `PERSONAL_ENTRIES`→`PersonalEntryModel` e as categorias pessoais→`PersonalCategoryModel` (confirme a origem exata lendo o router primeiro). Todo registro criado usa `owner_id="usr-001"` como valor fixo por enquanto (não há isolamento real por usuário logado nesta fase — é uma simplificação deliberada, documentada nos Global Constraints; ficaria pra uma fase de RBAC real). Teste: Hub Pessoal → Visão Geral e Extrato.

### Task 13: `app/api/v1/endpoints/personal.py` (parte 2 — submódulos)

Migra as 6 tabelas restantes adicionadas nesta mesma sessão: `PERSONAL_ACCOUNTS`→`PersonalAccountModel`, `PERSONAL_BUDGETS`→`PersonalBudgetModel`, `PERSONAL_GOALS`→`PersonalGoalModel` (incluindo o endpoint `/goals/{id}/contribute`, que faz `UPDATE current_amount`), `PERSONAL_DEBTS`→`PersonalDebtModel`, `PERSONAL_SUBSCRIPTIONS`→`PersonalSubscriptionModel`, `PERSONAL_SPLITS`→`PersonalSplitModel`. `PERSONAL_TIMEBOXES`/`PERSONAL_OKRS` (hoje listas vazias) migram para `PersonalTimeboxModel`/`PersonalOkrModel` — sem dados pra migrar, só troca onde o `POST`/`GET` lê e escreve. O endpoint `/personal/analytics` agrega em Python sobre `PersonalEntryModel` — mesma lógica de agregação em Python após buscar do banco, igual à Task 7. Teste: todas as abas restantes do Hub Pessoal (Contas & Cartões, Orçamento, Metas, Dívidas, Assinaturas, Divisão de Despesas, Analítico, Timeboxes & OKRs).

---

## Fase 2 — Fechamento

### Task 13b: `clients.py`, `search.py` e o import de `hoje`/`dias` em `financial.py`

**Descoberto durante o Task 14**: a Task 14 (grep de confirmação antes de apagar `database.py`) encontrou 3 imports remanescentes que não foram cobertos por nenhuma das Tasks 4–13, porque `clients.py` e `search.py` nunca foram atribuídos a nenhuma task do plano original de 10 routers:

```
app/api/v1/endpoints/clients.py:4:from app.db.database import KANBAN_CLIENTS
app/api/v1/endpoints/financial.py:14:from app.db.database import hoje, dias
app/api/v1/endpoints/search.py:3:from app.db.database import EMPLOYEES, KANBAN_CLIENTS, KANBAN_PROJECTS, FINANCIAL_ENTRIES, SUPPLIERS
```

Investigação: `clients.py` (montado em `/clients/*`) duplica exatamente o CRUD de clientes que já existe em `kanban.py` (`/kanban/clients`, migrado e aprovado no Task 9) — o frontend só chama `/kanban/clients`, nunca `/clients/` diretamente (confirmado via grep em `frontend/src`). `search.py` (`/search/`) é uma busca global independente, também não chamada pelo frontend hoje (a caixa de busca no header do `Layout.tsx` é um `<input>` estático, sem `onChange`/estado). Ambos continuam sendo superfície de API real e travariam o backend na inicialização assim que `database.py` for removido — não são código morto no sentido de "seguro pra apagar sem pensar", precisam ser migrados como qualquer outro router.

**Files:**
- Modify: `app/api/v1/endpoints/clients.py`
- Modify: `app/api/v1/endpoints/search.py`
- Modify: `app/api/v1/endpoints/financial.py`

- [ ] **Step 1: Migrar `clients.py` para `ClientModel`**

Mesmo padrão de conversão das Tasks 4–13: trocar `KANBAN_CLIENTS` por `db.execute(select(ClientModel))` / `db.get(ClientModel, cid)` / `db.add` / `setattr`+commit / `db.delete`, resposta via `model_to_dict`/`models_to_dicts`. `ClientModel` já existe (usado por `kanban.py` desde o Task 9) e já tem os clientes seedados — este router passa a ler/escrever exatamente a mesma tabela que `kanban.py` já usa, então os clientes criados por um endpoint aparecem no outro (correto — é a mesma tabela).

- [ ] **Step 2: Migrar `search.py` para consultar os modelos reais**

Trocar os 5 imports de lista mock por consultas reais a `EmployeeModel`, `ClientModel`, `ProjectModel`, `FinancialEntryModel`, `SupplierModel` (todos já existem). Buscar cada um via `select(Model)` e manter a mesma lógica de filtro/match em Python sobre os resultados — não precisa virar `LIKE`/SQL, só trocar a fonte dos dados, igual ao padrão de `/dre` e `/cashflow` de tasks anteriores.

- [ ] **Step 3: Remover o import de `hoje`/`dias` em `financial.py`**

`hoje = date.today()` e `dias(n) = (hoje + timedelta(days=n)).isoformat()` são funções puras sem dependência de dado mock — copiar essas 2 linhas para dentro do próprio `financial.py` (ou de um pequeno módulo de utilidades, se preferir) em vez de importar de `database.py`.

- [ ] **Step 4: Verificar**

Reiniciar o backend. Testar `/clients/` e `/kanban/clients` via curl ou navegador e confirmar que os dois enxergam os mesmos clientes (mesma tabela). Testar `/search/?q=carlos` (ou outro termo que bata com dado seedado) e confirmar que retorna resultados reais. Confirmar que `/financial/dre` e `/financial/cashflow` continuam funcionando normalmente.

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/clients.py app/api/v1/endpoints/search.py app/api/v1/endpoints/financial.py
git commit -m "feat(db): migrate clients and search routers to real database, drop stale date-helper import in financial.py"
```

---

### Task 14: Remover o módulo mock e QA final

**Files:**
- Modify: `app/db/database.py` — deletar o conteúdo, deixar um comentário curto explicando que foi substituído por `app/db/models.py` + `app/db/seed.py`, OU deletar o arquivo inteiramente se nada mais o importa.

- [ ] **Step 1: Confirmar que nada mais importa de `database.py`**

`grep -rn "from app.db.database import" app/` deve retornar zero resultados depois que as Tasks 4-13 estiverem todas completas. Se sobrar algum import, é sinal de que uma task anterior não migrou tudo — não prossiga, volte e corrija a task correspondente primeiro.

- [ ] **Step 2: Deletar `app/db/database.py`**

```bash
git rm app/db/database.py
```

- [ ] **Step 3: QA manual completo**

Apagar `techconnect.db`, subir o backend do zero (confirma que o seed roda), subir o frontend, e percorrer manualmente no navegador — login como os 3 usuários de teste, e pelo menos um fluxo de criação + edição + exclusão em cada módulo (Equipe, Fornecedores, Financeiro, Projetos/Kanban, Configurações, Hub Pessoal completo, Notificações, Exportação). Depois, **reiniciar o backend** (Ctrl+C, subir de novo) e confirmar que tudo que foi criado/editado durante o teste continua lá — essa é a prova real de que a persistência funciona.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove in-memory mock data module, now backed by real database"
```
