from fastapi import APIRouter
from app.api.v1.endpoints import auth, company, employees, suppliers, financial, kanban, notifications, personal, search, exports, ai, clients, plans, payments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
api_router.include_router(kanban.router, prefix="/kanban", tags=["kanban"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(personal.router, prefix="/personal", tags=["personal"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(ai.router, prefix="/ai-consultant", tags=["ai-consultant"])
