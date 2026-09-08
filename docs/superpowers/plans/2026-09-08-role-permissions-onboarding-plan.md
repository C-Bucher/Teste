# Hierarquia de Cargos, Conexões de API e Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Trocar o controle de acesso por cargo (hoje só visual, hardcoded) por um sistema real de permissões edit-ável e aplicado no backend, adicionar um painel de status de integrações em Configurações, e guiar toda empresa nova por um wizard de configuração inicial — corrigindo no caminho um bug de multi-tenant que faria todas essas features colidirem entre empresas diferentes.

**Architecture:** Uma nova tabela `role_permissions` (company_id, role, module_key) substitui os `if user.role !== 'X'` hardcoded do frontend; uma dependência FastAPI `require_module(...)` aplica o mesmo controle no backend com 403 real. Um wizard de 3 passos (`/onboarding`) reaproveita os mesmos componentes usados em Configurações. Nenhuma mudança de contrato nas rotas já existentes além do que está listado aqui.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async (já em uso), React + TypeScript + Tailwind (já em uso). Sem test runner configurado neste projeto — verificação é manual, com o backend rodando de verdade (curl + navegador), seguindo o mesmo padrão dos planos anteriores deste repositório.

**Spec:** `docs/superpowers/specs/2026-09-08-role-permissions-onboarding-design.md`

## Global Constraints

- Cargos fixos: `ADMIN`, `GERENTE`, `FUNCIONARIO` — sem cargos customizados.
- Módulos permissionáveis (constante `MODULES`, idêntica no backend e no frontend): `dashboard, kanban, equipe, financeiro, fornecedores, configuracoes, exportacao, ia`.
- ADMIN sempre tem acesso total — nunca é gravado em `role_permissions`, é tratado como caso especial no código.
- Nenhuma edição de credenciais reais (string de conexão, chaves de API) pela interface — só leitura de status.
- `GET /company/` nunca pode ficar atrás de `require_module` — é chamado por qualquer usuário autenticado para checar `onboarding_completed`.
- O projeto usa `Base.metadata.create_all` (sem Alembic) — tabelas/colunas novas só aparecem recriando o banco do zero. Isso é feito explicitamente na Task 2.
- Backend local roda via `venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000` (SQLite, arquivo `techconnect.db` na raiz) — é o setup já validado nesta sessão. Os comandos de verificação abaixo assumem esse ambiente.

---

### Task 1: Corrigir a base multi-tenant (bug crítico bloqueante)

**Contexto:** `company.py` usa hoje um ID de empresa fixo no código (`_COMPANY_ID = "cmp-001"`), e `/auth/register` nunca cria uma `CompanyModel` nem seta `company_id` no usuário novo. Isso faz toda empresa cadastrada colidir na mesma linha de configuração — inclusive os usuários de demonstração, que também têm `company_id` nulo. Sem corrigir isso primeiro, `role_permissions` e `onboarding_completed` (Tasks 2+) não conseguem isolar corretamente uma empresa da outra.

**Files:**
- Modify: `app/api/v1/endpoints/auth.py`
- Modify: `app/api/v1/endpoints/company.py`
- Modify: `app/db/seed.py`

**Interfaces:**
- Produces: todo `UserModel` (novo ou semeado) passa a ter `company_id` preenchido de verdade; `_get_company(db, company_id)` em `company.py` passa a aceitar um segundo parâmetro.

- [ ] **Step 1: `auth.py` — criar uma `CompanyModel` real no registro**

Em `app/api/v1/endpoints/auth.py`, adicionar o import de `CompanyModel`:

```python
from app.db.models import UserModel, CompanyModel
```

Substituir o corpo de `register` (a partir da linha `existing = ...` até `db.add(new_user)`) por:

```python
@router.post("/register")
async def register(b: RegisterReq, db: AsyncSession = Depends(get_db)):
    email = b.email.strip().lower()
    existing = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Este e-mail já está cadastrado no sistema")

    company_count = (await db.execute(select(func.count()).select_from(CompanyModel))).scalar() or 0
    company_id = f"cmp-{company_count + 1:03d}"
    db.add(CompanyModel(id=company_id, name=b.company_name or "Minha Empresa"))

    user_count = (await db.execute(select(func.count()).select_from(UserModel))).scalar() or 0
    user_id = f"usr-{user_count + 1:03d}"
    pwd_hash = bcrypt.hashpw(b.password.encode(), bcrypt.gensalt()).decode()

    plan = next((p for p in PLANS_DB if p["id"] == b.selected_plan), None)
    plan_scope = plan["scope"] if plan else "completo"

    new_user = UserModel(
        id=user_id,
        company_id=company_id,
        email=email,
        full_name=b.full_name,
        role="ADMIN",
        plan_scope=plan_scope,
        password_hash=pwd_hash,
        is_active=True,
        mfa_enabled=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
```

(O restante da função — montagem de `user_dict`, `create_token`, `return` — continua igual, não mexer.)

- [ ] **Step 2: `company.py` — parar de usar um ID fixo**

Em `app/api/v1/endpoints/company.py`, remover a linha `_COMPANY_ID = "cmp-001"` e substituir a função `_get_company` por:

```python
async def _get_company(db: AsyncSession, company_id: str | None) -> CompanyModel:
    if company_id:
        company = await db.get(CompanyModel, company_id)
        if company:
            return company
    result = await db.execute(select(CompanyModel).limit(1))
    return result.scalars().first()
```

Atualizar as duas chamadas existentes para passar o `company_id` do usuário logado:

```python
@router.get("/")
async def get_company(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await _get_company(db, u["company_id"])
    if not company:
        raise HTTPException(404)
    return model_to_dict(company)


@router.put("/")
async def upd_company(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await _get_company(db, u["company_id"])
    if not company:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _COMPANY_COLUMNS:
            setattr(company, k, v)
    await db.commit()
    await db.refresh(company)
    return model_to_dict(company)
```

- [ ] **Step 3: `seed.py` — dar `company_id` aos usuários de demonstração**

Em `app/db/seed.py`, localizar o bloco dos 3 `UserModel(...)` de demonstração (linhas 113-115) e adicionar `company_id="cmp-001"` a cada um:

```python
                UserModel(id="usr-001", company_id="cmp-001", email="admin@techconnect.com.br", full_name="Administrador", role="ADMIN", plan_scope="completo", password_hash=admin_hash, is_active=True, mfa_enabled=False),
                UserModel(id="usr-002", company_id="cmp-001", email="gerente@techconnect.com.br", full_name="Ana Souza", role="GERENTE", plan_scope="completo", password_hash=gerente_hash, is_active=True, mfa_enabled=False),
                UserModel(id="usr-003", company_id="cmp-001", email="funcionario@techconnect.com.br", full_name="Carlos Mendes", role="FUNCIONARIO", plan_scope="completo", password_hash=func_hash, is_active=True, mfa_enabled=False),
```

- [ ] **Step 4: Verificar**

Apagar o banco local pra forçar reseed e reiniciar o backend:

```bash
rm -f techconnect.db
```

(o `--reload` do uvicorn reinicia sozinho ao apagar o arquivo não é suficiente — pare o processo com Ctrl+C no terminal onde ele roda e suba de novo: `venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000`)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"admin@techconnect.com.br","password":"Admin@123"}' | grep -o '"company_id":"[^"]*"'
```

Esperado: `"company_id":"cmp-001"`.

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"full_name":"Teste Dois","email":"teste2@empresa.com","password":"Teste@123","company_name":"Empresa Dois"}' | python -c "import sys,json; d=json.load(sys.stdin); print(d['user']['company_id'])"
```

Esperado: `cmp-002` (não `cmp-001` — prova que cada registro agora ganha sua própria empresa).

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/auth.py app/api/v1/endpoints/company.py app/db/seed.py
git commit -m "fix: give every registered company its own row instead of a hardcoded shared id"
```

---

### Task 2: Modelo de dados — `RolePermissionModel` e `onboarding_completed`

**Files:**
- Modify: `app/db/models.py`

**Interfaces:**
- Produces: `RolePermissionModel` (colunas `id, company_id, role, module_key`), `CompanyModel.onboarding_completed` (bool, default `False`).

- [ ] **Step 1: Adicionar a coluna em `CompanyModel`**

Em `app/db/models.py`, dentro de `class CompanyModel`, logo após a linha `fiscal_year_start = Column(Integer, default=1)`, adicionar:

```python
    onboarding_completed = Column(Boolean, default=False)
```

- [ ] **Step 2: Criar `RolePermissionModel`**

No final do arquivo `app/db/models.py`, adicionar:

```python
class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)        # GERENTE | FUNCIONARIO (ADMIN nunca é gravado aqui)
    module_key = Column(String(50), nullable=False)  # ver MODULES em app/core/permissions.py
```

- [ ] **Step 3: Marcar a empresa de demonstração como já configurada**

Em `app/db/seed.py`, no bloco `CompanyModel(...)` já editado na Task 1 (linhas ~96-105), adicionar `onboarding_completed=True`:

```python
        session.add(
            CompanyModel(
                id="cmp-001",
                name="TechConnect Solucoes Ltda",
                cnpj="12.345.678/0001-90",
                email="contato@techconnect.com.br",
                phone="(61) 3344-5566",
                address="SHCGN 713 Bloco A - Brasilia/DF",
                fiscal_year_start=1,
                onboarding_completed=True,
            )
        )
```

(Isso é essencial — sem isso a conta de demonstração cairia no wizard de onboarding na próxima vez que alguém logasse com ela.)

- [ ] **Step 4: Verificar**

```bash
rm -f techconnect.db
```

Reiniciar o backend (Ctrl+C + subir de novo, como na Task 1). Confirmar que sobe sem erro (logs devem mostrar `Application startup complete`) e que a tabela nova existe:

```bash
"venv/Scripts/python.exe" -c "import sqlite3; c=sqlite3.connect('techconnect.db'); print(c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='role_permissions'\").fetchall())"
```

Esperado: `[('role_permissions',)]`.

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"admin@techconnect.com.br","password":"Admin@123"}' > /tmp/login.json
curl -s http://localhost:8000/api/v1/company/ -H "Authorization: Bearer $(python -c "import json;print(json.load(open('/tmp/login.json'))['access_token'])")" | grep -o '"onboarding_completed":[a-z]*'
```

Esperado: `"onboarding_completed":true`.

- [ ] **Step 5: Commit**

```bash
git add app/db/models.py app/db/seed.py
git commit -m "feat: add RolePermissionModel and CompanyModel.onboarding_completed"
```

---

### Task 3: Backend de permissões — constantes, dependência de autorização, endpoints

**Files:**
- Create: `app/core/permissions.py`
- Create: `app/api/v1/endpoints/permissions.py`
- Modify: `app/api/v1/api.py`
- Modify: `app/db/seed.py`

**Interfaces:**
- Consumes: `RolePermissionModel` (Task 2), `get_current_user` (`app/core/security.py`, já existente).
- Produces: `MODULES: list[str]`, `DEFAULT_PERMISSIONS: dict[str, list[str]]`, `require_module(module_key: str) -> Depends` (todos em `app/core/permissions.py`) — usados pela Task 4. Endpoints `GET/PUT /permissions/matrix`, `GET /permissions/mine`.

- [ ] **Step 1: Criar `app/core/permissions.py`**

```python
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import RolePermissionModel

MODULES = ["dashboard", "kanban", "equipe", "financeiro", "fornecedores", "configuracoes", "exportacao", "ia"]

DEFAULT_PERMISSIONS = {
    "GERENTE": ["dashboard", "kanban", "equipe", "financeiro", "fornecedores", "exportacao", "ia"],
    "FUNCIONARIO": ["dashboard", "kanban"],
}


def require_module(module_key: str):
    async def _check(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        if u["role"] == "ADMIN":
            return u
        result = await db.execute(
            select(RolePermissionModel).where(
                RolePermissionModel.company_id == u["company_id"],
                RolePermissionModel.role == u["role"],
                RolePermissionModel.module_key == module_key,
            )
        )
        if not result.scalars().first():
            raise HTTPException(403, "Seu cargo não tem acesso a este módulo")
        return u
    return _check
```

- [ ] **Step 2: Criar `app/api/v1/endpoints/permissions.py`**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.security import get_current_user
from app.core.permissions import MODULES, DEFAULT_PERMISSIONS
from app.db.session import get_db
from app.db.models import RolePermissionModel

router = APIRouter()


def _require_admin(u):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem gerenciar permissões")


@router.get("/matrix")
async def get_matrix(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(u)
    result = await db.execute(
        select(RolePermissionModel).where(RolePermissionModel.company_id == u["company_id"])
    )
    rows = result.scalars().all()
    if not rows:
        return {k: list(v) for k, v in DEFAULT_PERMISSIONS.items()}
    matrix: dict[str, list[str]] = {"GERENTE": [], "FUNCIONARIO": []}
    for r in rows:
        matrix.setdefault(r.role, []).append(r.module_key)
    return matrix


@router.put("/matrix")
async def put_matrix(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(u)
    await db.execute(delete(RolePermissionModel).where(RolePermissionModel.company_id == u["company_id"]))
    for role in ("GERENTE", "FUNCIONARIO"):
        for module_key in d.get(role, []):
            if module_key not in MODULES:
                continue
            db.add(RolePermissionModel(
                id=f"rp-{uuid.uuid4().hex[:8]}",
                company_id=u["company_id"],
                role=role,
                module_key=module_key,
            ))
    await db.commit()
    return await get_matrix(u=u, db=db)


@router.get("/mine")
async def get_mine(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] == "ADMIN":
        return {"modules": MODULES}
    result = await db.execute(
        select(RolePermissionModel.module_key).where(
            RolePermissionModel.company_id == u["company_id"],
            RolePermissionModel.role == u["role"],
        )
    )
    modules = [row[0] for row in result.all()]
    if not modules and u["role"] in DEFAULT_PERMISSIONS:
        modules = DEFAULT_PERMISSIONS[u["role"]]
    return {"modules": modules}
```

- [ ] **Step 3: Registrar o router**

Em `app/api/v1/api.py`, adicionar `permissions` ao import da linha 2 e registrar o router:

```python
from app.api.v1.endpoints import auth, company, employees, suppliers, financial, kanban, notifications, personal, search, exports, ai, clients, plans, payments, permissions
```

```python
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
```

- [ ] **Step 4: Semear as permissões padrão da empresa de demonstração**

Em `app/db/seed.py`, importar `RolePermissionModel` e `DEFAULT_PERMISSIONS`:

```python
from app.db.models import (
    CompanyModel,
    UserModel,
    RolePermissionModel,
    ...  # manter os demais imports já existentes na lista
)
from app.core.permissions import DEFAULT_PERMISSIONS
```

Logo após o bloco `session.add_all([UserModel(...), ...])` dos 3 usuários de demonstração (editado na Task 1), adicionar:

```python
        # --- ROLE PERMISSIONS (empresa de demonstração) ---------------------
        session.add_all([
            RolePermissionModel(id=f"rp-seed-{role.lower()}-{module}", company_id="cmp-001", role=role, module_key=module)
            for role, modules in DEFAULT_PERMISSIONS.items()
            for module in modules
        ])
```

- [ ] **Step 5: Verificar**

```bash
rm -f techconnect.db
```

Reiniciar o backend. Testar como admin (deve ver a matriz padrão) e como gerente (deve ver só o próprio cargo):

```bash
TOKEN_ADMIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"admin@techconnect.com.br","password":"Admin@123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:8000/api/v1/permissions/matrix -H "Authorization: Bearer $TOKEN_ADMIN"
```

Esperado: JSON com `GERENTE` contendo 7 módulos (tudo menos `configuracoes`) e `FUNCIONARIO` contendo `["dashboard","kanban"]`.

```bash
TOKEN_GER=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"gerente@techconnect.com.br","password":"Gerente@123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:8000/api/v1/permissions/mine -H "Authorization: Bearer $TOKEN_GER"
```

Esperado: `{"modules":["dashboard","kanban","equipe","financeiro","fornecedores","exportacao","ia"]}`.

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/permissions/matrix -H "Authorization: Bearer $TOKEN_GER"
```

Esperado: `403` (gerente não é admin, não pode ver a matriz completa).

- [ ] **Step 6: Commit**

```bash
git add app/core/permissions.py app/api/v1/endpoints/permissions.py app/api/v1/api.py app/db/seed.py
git commit -m "feat: add role-based module permissions (matrix, mine, require_module dependency)"
```

---

### Task 4: Aplicar o bloqueio real (403) nos routers existentes

**Files:**
- Modify: `app/api/v1/api.py`
- Modify: `app/api/v1/endpoints/company.py`

**Interfaces:**
- Consumes: `require_module` (Task 3).

- [ ] **Step 1: Gate por router inteiro (employees, suppliers, financial, exports, ai)**

Em `app/api/v1/api.py`, substituir a linha `from fastapi import APIRouter` (linha 1) por:

```python
from fastapi import APIRouter, Depends
```

E adicionar, logo abaixo dos imports existentes:

```python
from app.core.permissions import require_module
```

Substituir as linhas de `include_router` desses 5 routers (mantendo as demais linhas do arquivo intactas):

```python
api_router.include_router(employees.router, prefix="/employees", tags=["employees"], dependencies=[Depends(require_module("equipe"))])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(require_module("fornecedores"))])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"], dependencies=[Depends(require_module("financeiro"))])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"], dependencies=[Depends(require_module("exportacao"))])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"], dependencies=[Depends(require_module("ia"))])
api_router.include_router(ai.router, prefix="/ai-consultant", tags=["ai-consultant"], dependencies=[Depends(require_module("ia"))])
```

(Isso aplica a checagem a TODAS as rotas desses routers de uma vez, sem precisar editar cada função individualmente — `kanban.py`, `personal.py`, `clients.py`, `notifications.py`, `search.py`, `plans.py`, `payments.py`, `auth.py` e `company.py` ficam de fora dessa lista de propósito.)

- [ ] **Step 2: Gate seletivo em `company.py` (só as rotas que alteram configuração)**

Em `app/api/v1/endpoints/company.py`, importar `require_module`:

```python
from app.core.permissions import require_module
```

Adicionar `, _p=Depends(require_module("configuracoes"))` na assinatura de exatamente estas 5 funções (**não** mexer em `get_company`, que precisa continuar aberta a qualquer autenticado):

```python
@router.put("/")
async def upd_company(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
```

```python
@router.post("/cost-centers")
async def create_cc(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
```

```python
@router.delete("/cost-centers/{cid}")
async def del_cc(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
```

```python
@router.post("/categories")
async def create_cat(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
```

```python
@router.put("/calendar")
async def upd_calendar(d:dict,u=Depends(get_current_user), _p=Depends(require_module("configuracoes"))): return {"work_days":[1,2,3,4,5],"work_hours_per_day":8,**d}
```

- [ ] **Step 3: Verificar**

Reiniciar o backend (mudança de código só, não precisa apagar o banco).

```bash
TOKEN_FUNC=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"funcionario@techconnect.com.br","password":"Func@123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/financial/entries -H "Authorization: Bearer $TOKEN_FUNC"
```

Esperado: `403` (Funcionário não tem `financeiro`).

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/kanban/projects -H "Authorization: Bearer $TOKEN_FUNC"
```

Esperado: `200` (Kanban não é gateado).

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/company/ -H "Authorization: Bearer $TOKEN_FUNC"
```

Esperado: `200` (GET / continua aberto).

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X PUT http://localhost:8000/api/v1/company/ -H "Authorization: Bearer $TOKEN_FUNC" -H "Content-Type: application/json" -d '{}'
```

Esperado: `403` (PUT / agora exige `configuracoes`).

- [ ] **Step 4: Commit**

```bash
git add app/api/v1/api.py app/api/v1/endpoints/company.py
git commit -m "feat: enforce role-based module permissions with real 403s on protected routers"
```

---

### Task 5: Painel de integrações + corrigir o `/health` falso

**Files:**
- Create: `app/api/v1/endpoints/system.py`
- Modify: `app/api/v1/api.py`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `GET /system/integrations` → `{"integrations": [{"key", "label", "status"}, ...]}`.

- [ ] **Step 1: Criar `app/api/v1/endpoints/system.py`**

```python
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db, DATABASE_URL

router = APIRouter()


@router.get("/integrations")
async def get_integrations(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem ver o status das integrações")

    try:
        await db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        db_status = "offline"

    dialect = DATABASE_URL.split("://")[0].split("+")[0] if "://" in DATABASE_URL else "desconhecido"
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "integrations": [
            {"key": "database", "label": f"Banco de Dados ({dialect})", "status": db_status},
            {"key": "gemini", "label": "IA Gemini", "status": "configured" if gemini_configured else "unconfigured"},
        ]
    }
```

- [ ] **Step 2: Registrar o router**

Em `app/api/v1/api.py`, adicionar `system` ao final da linha de import de `app.api.v1.endpoints` (a mesma linha editada na Task 3, que a esta altura já inclui `permissions`) — ficando `from app.api.v1.endpoints import auth, company, employees, suppliers, financial, kanban, notifications, personal, search, exports, ai, clients, plans, payments, permissions, system` — e registrar o router:

```python
api_router.include_router(system.router, prefix="/system", tags=["system"])
```

- [ ] **Step 3: Corrigir o `/health` que mentia sobre o Redis**

Em `app/main.py`, trocar a rota `/health` (o Redis nunca foi usado em nenhum lugar do código — confirmado por busca no projeto inteiro — então parar de alegar que está "ok"):

```python
@app.get("/health")
async def health(): return {"status":"ok","version":"2.0.0","database":"ok","timestamp":datetime.now().isoformat()}
```

- [ ] **Step 4: Verificar**

Reiniciar o backend.

```bash
curl -s http://localhost:8000/health
```

Esperado: JSON sem a chave `"redis"`.

```bash
curl -s http://localhost:8000/api/v1/system/integrations -H "Authorization: Bearer $TOKEN_ADMIN"
```

(reusar `$TOKEN_ADMIN` da Task 3, ou gerar de novo com o mesmo curl de login)

Esperado: `{"integrations":[{"key":"database","label":"Banco de Dados (sqlite+aiosqlite)","status":"online"},{"key":"gemini","label":"IA Gemini","status":...}]}`.

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/system/integrations -H "Authorization: Bearer $TOKEN_GER"
```

Esperado: `403` (só admin).

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/system.py app/api/v1/api.py app/main.py
git commit -m "feat: add integrations status endpoint; fix /health lying about an unused Redis"
```

---

### Task 6: Endpoint de conclusão do onboarding

**Files:**
- Modify: `app/api/v1/endpoints/company.py`

**Interfaces:**
- Produces: `POST /company/onboarding/complete` → retorna a empresa atualizada (com `onboarding_completed: true`).

- [ ] **Step 1: Adicionar o endpoint**

Em `app/api/v1/endpoints/company.py`, adicionar (logo após `upd_company`, por exemplo):

```python
@router.post("/onboarding/complete")
async def complete_onboarding(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem concluir a configuração inicial")
    company = await _get_company(db, u["company_id"])
    if not company:
        raise HTTPException(404)
    company.onboarding_completed = True
    await db.commit()
    await db.refresh(company)
    return model_to_dict(company)
```

- [ ] **Step 2: Verificar**

Reiniciar o backend.

```bash
TOKEN_NEW=$(curl -s -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"full_name":"Teste Onboarding","email":"onboard@empresa.com","password":"Teste@123","company_name":"Empresa Onboarding"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:8000/api/v1/company/ -H "Authorization: Bearer $TOKEN_NEW" | grep -o '"onboarding_completed":[a-z]*'
```

Esperado: `"onboarding_completed":false`.

```bash
curl -s -X POST http://localhost:8000/api/v1/company/onboarding/complete -H "Authorization: Bearer $TOKEN_NEW" | grep -o '"onboarding_completed":[a-z]*'
```

Esperado: `"onboarding_completed":true`.

- [ ] **Step 3: Commit**

```bash
git add app/api/v1/endpoints/company.py
git commit -m "feat: add POST /company/onboarding/complete"
```

---

### Task 7: Admin cria login de Gerente/Funcionário

**Files:**
- Modify: `app/api/v1/endpoints/auth.py`

**Interfaces:**
- Produces: `POST /auth/users` → cria um `UserModel` com `role` GERENTE ou FUNCIONARIO, associado à empresa do admin que chamou.

- [ ] **Step 1: Adicionar o schema e o endpoint**

Em `app/api/v1/endpoints/auth.py`, adicionar a classe de request (perto de `RegisterReq`):

```python
class CreateUserReq(BaseModel):
    full_name: str
    email: str
    password: str
    role: str
```

Adicionar o endpoint (logo após o bloco de `GET /users`, antes de `PUT /users/{uid}`):

```python
@router.post("/users")
async def create_user(b: CreateUserReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem criar novos acessos")
    if b.role not in ("GERENTE", "FUNCIONARIO"):
        raise HTTPException(400, "Cargo inválido. Use GERENTE ou FUNCIONARIO")

    email = b.email.strip().lower()
    existing = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Este e-mail já está cadastrado no sistema")

    user_count = (await db.execute(select(func.count()).select_from(UserModel))).scalar() or 0
    new_id = f"usr-{user_count + 1:03d}"
    pwd_hash = bcrypt.hashpw(b.password.encode(), bcrypt.gensalt()).decode()

    new_user = UserModel(
        id=new_id,
        company_id=u["company_id"],
        email=email,
        full_name=b.full_name,
        role=b.role,
        plan_scope="empresarial",
        password_hash=pwd_hash,
        is_active=True,
        mfa_enabled=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {k: v for k, v in model_to_dict(new_user).items() if k != "password_hash"}
```

- [ ] **Step 2: Verificar**

Reiniciar o backend.

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/users -H "Authorization: Bearer $TOKEN_ADMIN" -H "Content-Type: application/json" -d '{"full_name":"Novo Gerente","email":"novogerente@techconnect.com.br","password":"Senha@123","role":"GERENTE"}'
```

Esperado: 200, JSON do usuário criado com `"role":"GERENTE"` e `"company_id":"cmp-001"`, sem `password_hash`.

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"novogerente@techconnect.com.br","password":"Senha@123"}' | grep -o '"access_token"'
```

Esperado: login funciona.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/auth/users -H "Authorization: Bearer $TOKEN_GER" -H "Content-Type: application/json" -d '{"full_name":"X","email":"x@x.com","password":"Senha@123","role":"FUNCIONARIO"}'
```

Esperado: `403` (gerente não pode criar acessos, só admin).

- [ ] **Step 3: Commit**

```bash
git add app/api/v1/endpoints/auth.py
git commit -m "feat: add POST /auth/users for admins to create team member logins"
```

---

### Task 8: Componente `PermissionMatrix`

**Files:**
- Create: `frontend/src/components/PermissionMatrix.tsx`

**Interfaces:**
- Consumes: `GET /permissions/matrix`, `PUT /permissions/matrix` (Task 3).
- Produces: `<PermissionMatrix onSaved={() => void} />` — usado pela Task 10 (Configurações) e Task 11 (Onboarding).

- [ ] **Step 1: Criar o componente**

```tsx
import { useState, useEffect } from 'react';
import api from '../api';
import { useToast } from '../context/ToastContext';

const MODULE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  kanban: 'Projetos (Kanban)',
  equipe: 'Gestão de Equipe',
  financeiro: 'Financeiro',
  fornecedores: 'Fornecedores',
  configuracoes: 'Configurações',
  exportacao: 'Exportação',
  ia: 'IA Empresarial',
};

const MODULES = Object.keys(MODULE_LABELS);
const ROLES: { key: 'GERENTE' | 'FUNCIONARIO'; label: string }[] = [
  { key: 'GERENTE', label: 'Gerente' },
  { key: 'FUNCIONARIO', label: 'Funcionário' },
];

interface Props {
  onSaved?: () => void;
}

export default function PermissionMatrix({ onSaved }: Props) {
  const toast = useToast();
  const [matrix, setMatrix] = useState<Record<string, string[]>>({ GERENTE: [], FUNCIONARIO: [] });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/permissions/matrix').then((res) => setMatrix(res.data)).finally(() => setLoading(false));
  }, []);

  const toggle = (role: string, moduleKey: string) => {
    setMatrix((prev) => {
      const current = prev[role] || [];
      const has = current.includes(moduleKey);
      return { ...prev, [role]: has ? current.filter((m) => m !== moduleKey) : [...current, moduleKey] };
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await api.put('/permissions/matrix', matrix);
      setMatrix(res.data);
      toast.success('Permissões salvas.');
      onSaved?.();
    } catch (err) {
      console.error('Erro ao salvar permissões', err);
      toast.error('Erro ao salvar permissões.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-xl">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
            <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Módulo</th>
            <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-center">Admin</th>
            {ROLES.map((r) => (
              <th key={r.key} className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-center">{r.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle/50">
          {MODULES.map((moduleKey) => (
            <tr key={moduleKey} className="hover:bg-surface-bright/40 transition-colors">
              <td className="px-lg py-md text-label-md text-on-surface">{MODULE_LABELS[moduleKey]}</td>
              <td className="px-lg py-md text-center">
                <input type="checkbox" checked disabled className="w-4 h-4 accent-primary opacity-60" />
              </td>
              {ROLES.map((r) => (
                <td key={r.key} className="px-lg py-md text-center">
                  <input
                    type="checkbox"
                    checked={(matrix[r.key] || []).includes(moduleKey)}
                    onChange={() => toggle(r.key, moduleKey)}
                    className="w-4 h-4 accent-primary cursor-pointer"
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex justify-end p-lg border-t border-border-subtle">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50"
        >
          {saving ? 'Salvando...' : 'Salvar Permissões'}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar**

Este componente não tem uso próprio ainda (entra em Configurações/Onboarding nas Tasks 10/11) — a verificação real acontece lá. Por enquanto, confirmar que o arquivo compila sem erro de tipo:

```bash
cd frontend && npx tsc --noEmit -p . 2>&1 | grep PermissionMatrix
```

Esperado: nenhuma saída (sem erros referentes a este arquivo).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PermissionMatrix.tsx
git commit -m "feat: add PermissionMatrix component"
```

---

### Task 9: Componente `IntegrationsStatus`

**Files:**
- Create: `frontend/src/components/IntegrationsStatus.tsx`

**Interfaces:**
- Consumes: `GET /system/integrations` (Task 5).
- Produces: `<IntegrationsStatus />` — usado pela Task 10 e Task 11.

- [ ] **Step 1: Criar o componente**

```tsx
import { useState, useEffect } from 'react';
import api from '../api';

interface Integration {
  key: string;
  label: string;
  status: string;
}

const STATUS_STYLES: Record<string, string> = {
  online: 'bg-success/10 text-success',
  configured: 'bg-success/10 text-success',
  offline: 'bg-error/10 text-error',
  unconfigured: 'bg-warning/10 text-warning',
};

const STATUS_LABELS: Record<string, string> = {
  online: 'Online',
  configured: 'Configurada',
  offline: 'Offline',
  unconfigured: 'Não configurada',
};

export default function IntegrationsStatus() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await api.get('/system/integrations');
      setIntegrations(res.data.integrations);
      setLastChecked(new Date());
    } catch (err) {
      console.error('Erro ao verificar integrações', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="space-y-md">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
        {integrations.map((it) => (
          <div key={it.key} className="glass-card p-lg rounded-2xl flex items-center justify-between">
            <span className="text-label-md text-on-surface">{it.label}</span>
            <span className={`inline-flex items-center gap-xs px-2 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${STATUS_STYLES[it.status] || 'bg-surface-container-highest text-on-surface-variant'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${it.status === 'online' || it.status === 'configured' ? 'bg-success' : it.status === 'offline' ? 'bg-error' : 'bg-warning'}`}></span>
              {STATUS_LABELS[it.status] || it.status}
            </span>
          </div>
        ))}
        {loading && integrations.length === 0 && (
          <div className="col-span-2 flex justify-center py-xl">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between pt-sm">
        <span className="text-body-sm text-on-surface-variant">
          {lastChecked ? `Última checagem: ${lastChecked.toLocaleTimeString('pt-BR')}` : ''}
        </span>
        <button
          onClick={fetchStatus}
          disabled={loading}
          className="px-4 py-2 rounded-lg font-label-md text-label-md bg-surface-container border border-border-subtle hover:bg-surface-container-highest transition-colors disabled:opacity-50"
        >
          Testar Conexão
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar**

```bash
cd frontend && npx tsc --noEmit -p . 2>&1 | grep IntegrationsStatus
```

Esperado: nenhuma saída.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/IntegrationsStatus.tsx
git commit -m "feat: add IntegrationsStatus component"
```

---

### Task 10: Duas abas novas em `Configuracoes.tsx`

**Files:**
- Modify: `frontend/src/pages/Configuracoes.tsx`

**Interfaces:**
- Consumes: `PermissionMatrix` (Task 8), `IntegrationsStatus` (Task 9).

- [ ] **Step 1: Importar os componentes e estender o tipo `Tab`**

No topo do arquivo, adicionar aos imports existentes:

```tsx
import PermissionMatrix from '../components/PermissionMatrix';
import IntegrationsStatus from '../components/IntegrationsStatus';
```

Trocar a linha `type Tab = 'empresa' | 'plano-contas' | 'centros-custo' | 'calendario';` por:

```tsx
type Tab = 'empresa' | 'plano-contas' | 'centros-custo' | 'calendario' | 'cargos' | 'conexoes';
```

Trocar o array `TABS` (linhas 29-34) por:

```tsx
const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'empresa', label: 'Dados da Empresa', icon: 'domain' },
  { id: 'plano-contas', label: 'Plano de Contas', icon: 'account_tree' },
  { id: 'centros-custo', label: 'Centros de Custo', icon: 'apartment' },
  { id: 'calendario', label: 'Calendário Útil', icon: 'calendar_month' },
  { id: 'cargos', label: 'Hierarquia de Cargos', icon: 'admin_panel_settings' },
  { id: 'conexoes', label: 'Conexões de API', icon: 'cable' },
];
```

Trocar `const TAB_IDS: Tab[] = ['empresa', 'plano-contas', 'centros-custo', 'calendario'];` por:

```tsx
  const TAB_IDS: Tab[] = ['empresa', 'plano-contas', 'centros-custo', 'calendario', 'cargos', 'conexoes'];
```

- [ ] **Step 2: Adicionar o conteúdo das duas abas**

Logo antes do fechamento `{/* Modal: Nova Categoria */}` (final do bloco de abas, depois da aba `calendario`), adicionar:

```tsx
      {/* Aba: Hierarquia de Cargos */}
      {activeTab === 'cargos' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="mb-lg">
            <h3 className="font-headline-sm text-headline-sm text-on-surface">Hierarquia de Cargos</h3>
            <p className="text-on-surface-variant text-body-sm mt-xs">Escolha quais módulos cada cargo pode acessar. Bloqueado também no servidor, não só na tela.</p>
          </div>
          <PermissionMatrix />
        </motion.div>
      )}

      {/* Aba: Conexões de API */}
      {activeTab === 'conexoes' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl">
          <div className="mb-lg">
            <h3 className="font-headline-sm text-headline-sm text-on-surface">Conexões de API</h3>
            <p className="text-on-surface-variant text-body-sm mt-xs">Status das integrações do sistema em tempo real.</p>
          </div>
          <IntegrationsStatus />
        </motion.div>
      )}

```

- [ ] **Step 3: Verificar**

Com o backend e o frontend rodando (`npm run dev` já ativo em `frontend/`), abrir `http://localhost:5173`, logar como `admin@techconnect.com.br` / `Admin@123`, ir em Configurações. Confirmar visualmente que aparecem 6 abas, que "Hierarquia de Cargos" mostra a tabela com Gerente/Funcionário marcados conforme o padrão semeado, e que "Conexões de API" mostra o banco Online.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Configuracoes.tsx
git commit -m "feat: add Hierarquia de Cargos and Conexões de API tabs to Configuracoes"
```

---

### Task 11: Wizard de onboarding + guarda de rota

**Files:**
- Create: `frontend/src/pages/Onboarding.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/pages/Login.tsx`
- Modify: `frontend/src/pages/Register.tsx`

**Interfaces:**
- Consumes: `PermissionMatrix`, `IntegrationsStatus` (Tasks 8-9), `PUT /company/`, `POST /company/onboarding/complete` (Task 6), `GET /company/` (existente).

- [ ] **Step 1: Criar `Onboarding.tsx`**

```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import api from '../api';
import { useToast } from '../context/ToastContext';
import PermissionMatrix from '../components/PermissionMatrix';
import IntegrationsStatus from '../components/IntegrationsStatus';

const STEPS = [
  { id: 1, label: 'Dados da Empresa' },
  { id: 2, label: 'Hierarquia de Cargos' },
  { id: 3, label: 'Conexões de API' },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const toast = useToast();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [savingCompany, setSavingCompany] = useState(false);
  const [companyForm, setCompanyForm] = useState({ name: '', cnpj: '', email: '', phone: '', address: '' });

  const handleSaveCompanyStep = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingCompany(true);
    try {
      await api.put('/company/', companyForm);
      toast.success('Dados da empresa salvos.');
      setStep(2);
    } catch (err) {
      console.error('Erro ao salvar dados da empresa', err);
      toast.error('Erro ao salvar dados da empresa.');
    } finally {
      setSavingCompany(false);
    }
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      const res = await api.post('/company/onboarding/complete');
      localStorage.setItem('company', JSON.stringify(res.data));
      toast.success('Configuração concluída!');
      navigate('/dashboard');
    } catch (err) {
      console.error('Erro ao concluir configuração', err);
      toast.error('Erro ao concluir configuração.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-lg">
      <div className="w-full max-w-3xl">
        <div className="flex items-center justify-center gap-md mb-2xl">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-md">
              <div className={`flex items-center gap-sm ${step >= s.id ? 'text-primary' : 'text-on-surface-variant'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-label-md border ${step >= s.id ? 'bg-primary-container border-primary text-on-primary-container' : 'border-border-subtle'}`}>
                  {s.id}
                </div>
                <span className="text-label-md hidden sm:inline">{s.label}</span>
              </div>
              {i < STEPS.length - 1 && <div className="w-8 h-px bg-border-subtle" />}
            </div>
          ))}
        </div>

        <div className="glass-card p-xl rounded-2xl">
          {step === 1 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Dados da Empresa</h2>
              <form onSubmit={handleSaveCompanyStep} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Razão Social</label>
                  <input required type="text" value={companyForm.name} onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">CNPJ</label>
                    <input required type="text" value={companyForm.cnpj} onChange={(e) => setCompanyForm({ ...companyForm, cnpj: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">E-mail</label>
                    <input required type="email" value={companyForm.email} onChange={(e) => setCompanyForm({ ...companyForm, email: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                </div>
                <div className="flex justify-end pt-md mt-lg border-t border-border-subtle">
                  <button type="submit" disabled={savingCompany}
                    className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingCompany ? 'Salvando...' : 'Próximo'}
                  </button>
                </div>
              </form>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Hierarquia de Cargos</h2>
              <p className="text-on-surface-variant text-body-sm mb-lg">Defina o que Gerentes e Funcionários vão poder ver quando você adicioná-los depois. Você pode ajustar isso a qualquer momento em Configurações.</p>
              <PermissionMatrix />
              <div className="flex justify-between pt-lg mt-lg border-t border-border-subtle">
                <button onClick={() => setStep(1)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">Voltar</button>
                <button onClick={() => setStep(3)} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">Próximo</button>
              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Conexões de API</h2>
              <p className="text-on-surface-variant text-body-sm mb-lg">Confirme que a infraestrutura do sistema está saudável antes de começar a usar.</p>
              <IntegrationsStatus />
              <div className="flex justify-between pt-lg mt-lg border-t border-border-subtle">
                <button onClick={() => setStep(2)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">Voltar</button>
                <button onClick={handleFinish} disabled={saving}
                  className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                  {saving ? 'Concluindo...' : 'Concluir Configuração'}
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: `App.tsx` — nova rota e guarda de onboarding**

Adicionar o import:

```tsx
import Onboarding from './pages/Onboarding';
```

Substituir o componente `PrivateRoute` inteiro por:

```tsx
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  const location = useLocation();
  if (!token) return <Navigate to="/" />;

  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const company = JSON.parse(localStorage.getItem('company') || '{}');
  if (user.role === 'ADMIN' && company.onboarding_completed === false && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" />;
  }

  return children;
};
```

Adicionar `useLocation` ao import do `react-router-dom` no topo do arquivo:

```tsx
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
```

Adicionar a rota nova (junto das outras `PrivateRoute`, por exemplo logo após `/dashboard`):

```tsx
        <Route path="/onboarding" element={<PrivateRoute><Onboarding /></PrivateRoute>} />
```

- [ ] **Step 3: `Login.tsx` — buscar e guardar a empresa, redirecionar se pendente**

Trocar as 3 linhas depois de `const response = await api.post('/auth/login', ...)`:

```tsx
      const response = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      try {
        const companyRes = await api.get('/company/');
        localStorage.setItem('company', JSON.stringify(companyRes.data));
        if (response.data.user.role === 'ADMIN' && companyRes.data.onboarding_completed === false) {
          navigate('/onboarding');
          return;
        }
      } catch (err) {
        console.error('Erro ao carregar dados da empresa', err);
      }
      navigate('/dashboard');
```

- [ ] **Step 4: `Register.tsx` — guardar a empresa (sem mudar o redirecionamento pro checkout)**

Depois das 2 linhas `localStorage.setItem('token', ...)` / `localStorage.setItem('user', ...)` e antes do `navigate('/checkout?...)`, adicionar:

```tsx
      try {
        const companyRes = await api.get('/company/');
        localStorage.setItem('company', JSON.stringify(companyRes.data));
      } catch (err) {
        console.error('Erro ao carregar dados da empresa', err);
      }
```

- [ ] **Step 5: Verificar**

Com backend e frontend rodando: registrar uma empresa nova em `http://localhost:5173/cadastro`, completar o checkout (se aplicável no fluxo atual), logar com essa conta nova — confirmar que cai em `/onboarding`, não em `/dashboard`. Passar pelos 3 passos, clicar "Concluir Configuração", confirmar que cai em `/dashboard`. Deslogar e logar de novo com essa mesma conta — confirmar que **não** cai mais em `/onboarding`. Logar com `admin@techconnect.com.br` (conta de demonstração) — confirmar que vai direto pro `/dashboard`, sem passar pelo wizard.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Onboarding.tsx frontend/src/App.tsx frontend/src/pages/Login.tsx frontend/src/pages/Register.tsx
git commit -m "feat: add first-login onboarding wizard for new company admins"
```

---

### Task 12: Menu lateral dirigido por permissão real

**Files:**
- Modify: `frontend/src/components/Layout.tsx`

**Interfaces:**
- Consumes: `GET /permissions/mine` (Task 3).

- [ ] **Step 1: Buscar as permissões do usuário ao montar o Layout**

Adicionar um novo state e `useEffect`, próximo ao `useEffect` existente que busca `unreadCount` (linhas 65-75):

```tsx
  const [allowedModules, setAllowedModules] = useState<string[]>([]);

  useEffect(() => {
    if (user.role === 'ADMIN') {
      setAllowedModules(['dashboard', 'kanban', 'equipe', 'financeiro', 'fornecedores', 'configuracoes', 'exportacao', 'ia']);
      return;
    }
    const fetchPermissions = async () => {
      try {
        const res = await api.get('/permissions/mine');
        setAllowedModules(res.data.modules);
      } catch (err) {
        console.error('Erro ao carregar permissões', err);
      }
    };
    fetchPermissions();
  }, []);
```

- [ ] **Step 2: Trocar `businessNavItems` para filtrar por módulo em vez de cargo hardcoded**

Substituir o bloco (linhas 162-171):

```tsx
  const businessNavItems = [
    { name: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
    { name: 'Projetos', path: '/kanban', icon: 'view_kanban' },
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Equipe', path: '/equipe', icon: 'groups' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Financeiro', path: '/financeiro', icon: 'payments' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Fornecedores', path: '/fornecedores', icon: 'local_shipping' }] : []),
    ...(user.role === 'ADMIN' ? [{ name: 'Configurações', path: '/configuracoes', icon: 'settings' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Exportação', path: '/exportacao', icon: 'file_download' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'IA Empresarial', path: '/ia', icon: 'auto_awesome' }] : []),
  ];
```

por:

```tsx
  const ALL_BUSINESS_ITEMS = [
    { name: 'Dashboard', path: '/dashboard', icon: 'dashboard', module: 'dashboard' },
    { name: 'Projetos', path: '/kanban', icon: 'view_kanban', module: 'kanban' },
    { name: 'Equipe', path: '/equipe', icon: 'groups', module: 'equipe' },
    { name: 'Financeiro', path: '/financeiro', icon: 'payments', module: 'financeiro' },
    { name: 'Fornecedores', path: '/fornecedores', icon: 'local_shipping', module: 'fornecedores' },
    { name: 'Configurações', path: '/configuracoes', icon: 'settings', module: 'configuracoes' },
    { name: 'Exportação', path: '/exportacao', icon: 'file_download', module: 'exportacao' },
    { name: 'IA Empresarial', path: '/ia', icon: 'auto_awesome', module: 'ia' },
  ];

  const businessNavItems = ALL_BUSINESS_ITEMS.filter((item) => allowedModules.includes(item.module));
```

- [ ] **Step 3: Verificar**

Com backend e frontend rodando: logar como `funcionario@techconnect.com.br` / `Func@123` — confirmar que o menu lateral mostra só Dashboard e Projetos. Logar como `gerente@techconnect.com.br` / `Gerente@123` — confirmar que mostra tudo, menos Configurações. Ir em Configurações (como admin) → Hierarquia de Cargos → marcar "Fornecedores" para Funcionário → Salvar. Deslogar, logar de novo como Funcionário — confirmar que "Fornecedores" agora aparece no menu.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.tsx
git commit -m "feat: drive sidebar nav items from real permissions instead of hardcoded role checks"
```

---

### Task 13: Admin cria contas de equipe pela interface

**Files:**
- Create: `frontend/src/components/SystemAccessSection.tsx`
- Modify: `frontend/src/pages/GestaoEquipe.tsx`

**Interfaces:**
- Consumes: `GET /auth/users` (existente), `POST /auth/users` (Task 7).

- [ ] **Step 1: Criar `SystemAccessSection.tsx`**

```tsx
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api';
import { useToast } from '../context/ToastContext';

interface SystemUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

const ROLE_LABELS: Record<string, string> = {
  ADMIN: 'Administrador',
  GERENTE: 'Gerente',
  FUNCIONARIO: 'Funcionário',
};

export default function SystemAccessSection() {
  const toast = useToast();
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'FUNCIONARIO' });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get('/auth/users');
      setUsers(res.data);
    } catch (err) {
      console.error('Erro ao carregar acessos', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/auth/users', form);
      toast.success('Acesso criado com sucesso.');
      setIsModalOpen(false);
      setForm({ full_name: '', email: '', password: '', role: 'FUNCIONARIO' });
      fetchUsers();
    } catch (err: any) {
      console.error('Erro ao criar acesso', err);
      toast.error(err?.response?.data?.detail || 'Erro ao criar acesso.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="glass-card p-lg rounded-2xl mb-xl">
      <div className="flex justify-between items-center mb-lg">
        <div>
          <h3 className="font-headline-sm text-headline-sm text-on-surface">Acessos ao Sistema</h3>
          <p className="text-on-surface-variant text-body-sm mt-xs">Contas de login da sua empresa e o cargo de cada uma.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
        >
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>person_add</span>
          Adicionar Acesso
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Nome</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">E-mail</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Cargo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-surface-bright/40 transition-colors">
                  <td className="px-lg py-md text-label-md text-on-surface">{u.full_name}</td>
                  <td className="px-lg py-md text-label-md text-on-surface-variant">{u.email}</td>
                  <td className="px-lg py-md">
                    <span className="px-sm py-0.5 rounded-full text-[11px] font-bold bg-surface-container-highest text-on-surface-variant uppercase tracking-wider">
                      {ROLE_LABELS[u.role] || u.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Acesso</h3>
                <button onClick={() => setIsModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>
              <form onSubmit={handleCreate} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome Completo</label>
                  <input required type="text" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">E-mail</label>
                  <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Senha</label>
                  <input required type="password" minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Cargo</label>
                  <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none">
                    <option value="GERENTE">Gerente</option>
                    <option value="FUNCIONARIO">Funcionário</option>
                  </select>
                </div>
                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">Cancelar</button>
                  <button type="submit" disabled={saving} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {saving ? 'Criando...' : 'Criar Acesso'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

- [ ] **Step 2: Inserir na página de Gestão de Equipe (só para Admin)**

Em `frontend/src/pages/GestaoEquipe.tsx`, adicionar o import (depois de `import { useConfirm } from '../context/ConfirmContext';`):

```tsx
import SystemAccessSection from '../components/SystemAccessSection';
```

Substituir:

```tsx
  return (
    <Layout>
      {/* Page Header & Actions */}
```

por:

```tsx
  return (
    <Layout>
      {user.role === 'ADMIN' && <SystemAccessSection />}
      {/* Page Header & Actions */}
```

- [ ] **Step 3: Verificar**

Logar como Admin, ir em Gestão de Equipe — confirmar que aparece a seção "Acessos ao Sistema" no topo, listando os 3 usuários de demonstração. Clicar "Adicionar Acesso", criar um Gerente novo com e-mail/senha, confirmar que aparece na lista. Deslogar, logar com esse e-mail/senha novo — confirmar que entra no sistema com o cargo Gerente. Logar como Gerente ou Funcionário — confirmar que a seção "Acessos ao Sistema" **não** aparece.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/SystemAccessSection.tsx frontend/src/pages/GestaoEquipe.tsx
git commit -m "feat: let admins create Gerente/Funcionario logins from Gestao de Equipe"
```

---

### Task 14: Verificação de ponta a ponta

**Files:** nenhum (só verificação manual).

- [ ] **Step 1: Banco limpo**

```bash
rm -f techconnect.db
```

Reiniciar o backend (`venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000`) e o frontend (`npm run dev` em `frontend/`, se não estiver rodando).

- [ ] **Step 2: Jornada completa, empresa nova**

No navegador: `/cadastro` → criar uma empresa nova → completar o fluxo até logar → confirmar redirecionamento automático para `/onboarding` → completar os 3 passos → confirmar chegada em `/dashboard` com o menu já refletindo as permissões escolhidas no passo 2.

- [ ] **Step 3: Conta de demonstração não é afetada**

Deslogar, logar com `admin@techconnect.com.br` / `Admin@123` → confirmar que vai direto para `/dashboard`, sem `/onboarding`.

- [ ] **Step 4: Bloqueio real, não só visual**

Logar como `funcionario@techconnect.com.br` / `Func@123`. Abrir o DevTools do navegador (Network tab). Tentar acessar `http://localhost:5173/financeiro` diretamente pela URL — confirmar que a tela não mostra dados (a chamada à API deve retornar 403). Confirmar visualmente que "Financeiro" não aparece no menu lateral.

- [ ] **Step 5: Ajuste de permissão em tempo real**

Logar como Admin → Configurações → Hierarquia de Cargos → adicionar "Financeiro" para Funcionário → Salvar. Deslogar, logar de novo como Funcionário → confirmar que "Financeiro" agora aparece no menu e a página carrega sem 403.

- [ ] **Step 6: Painel de conexões**

Como Admin, em Configurações → Conexões de API → confirmar "Banco de Dados (sqlite+aiosqlite)" Online, clicar "Testar Conexão" e confirmar que o horário da última checagem atualiza.

Se tudo passar, a feature está completa e verificada — nenhum commit adicional necessário nesta task (é só checklist).
