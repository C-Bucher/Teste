from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, company, employees, suppliers, financial, kanban, notifications, personal, search, exports, ai, clients, plans, payments, permissions, system, audit, account, bank, bank_hooks, jobs
from app.core.permissions import require_module, require_plan_scope
from app.core.billing import require_active_subscription

# Modules that stop working while the subscription is inactive (billing, account and auth stay open).
paid = Depends(require_active_subscription)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"], dependencies=[Depends(require_module("equipe")), paid])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(require_module("fornecedores")), paid])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"], dependencies=[paid])
api_router.include_router(kanban.router, prefix="/kanban", tags=["kanban"], dependencies=[Depends(require_module("kanban")), paid])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(personal.router, prefix="/personal", tags=["personal"], dependencies=[Depends(require_plan_scope("pessoal", "completo")), paid])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"], dependencies=[Depends(require_module("kanban")), paid])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"], dependencies=[Depends(require_module("exportacao")), paid])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"], dependencies=[Depends(require_module("ia")), paid])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(search.router, prefix="/search", tags=["search"], dependencies=[paid])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(account.router, prefix="/account", tags=["account"])
api_router.include_router(bank.router, prefix="/bank", tags=["bank"], dependencies=[paid])
api_router.include_router(bank_hooks.router, prefix="/bank", tags=["bank-hooks"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(ai.router, prefix="/ai-consultant", tags=["ai-consultant"], dependencies=[Depends(require_module("ia")), paid])
