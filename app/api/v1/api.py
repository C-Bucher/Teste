from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, company, employees, suppliers, financial, kanban, notifications, personal, search, exports, ai, clients, plans, payments, permissions
from app.core.permissions import require_module

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"], dependencies=[Depends(require_module("equipe"))])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(require_module("fornecedores"))])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"], dependencies=[Depends(require_module("financeiro"))])
api_router.include_router(kanban.router, prefix="/kanban", tags=["kanban"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(personal.router, prefix="/personal", tags=["personal"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"], dependencies=[Depends(require_module("exportacao"))])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"], dependencies=[Depends(require_module("ia"))])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(ai.router, prefix="/ai-consultant", tags=["ai-consultant"], dependencies=[Depends(require_module("ia"))])
