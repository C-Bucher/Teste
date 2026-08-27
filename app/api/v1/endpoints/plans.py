from fastapi import APIRouter, HTTPException

router = APIRouter()

PLANS_DB = [
    {
        "id": "plan-pessoal",
        "name": "Pessoal",
        "scope": "pessoal",
        "tagline": "Organize suas finanças pessoais com apoio de IA",
        "price_monthly": 19.90,
        "price_yearly": 15.90,
        "popular": False,
        "features": [
            "Hub Pessoal completo: contas, cartões, orçamento e metas",
            "Controle de dívidas e assinaturas recorrentes",
            "Divisão de despesas com terceiros",
            "CFO Pessoal IA com dicas de economia",
            "Dashboard analítico de evolução patrimonial"
        ],
        "limits": {"max_employees": 0, "max_projects": 0, "ai_queries": 30}
    },
    {
        "id": "plan-empresarial",
        "name": "Empresarial",
        "scope": "empresarial",
        "tagline": "Gestão financeira e operacional completa da sua PME",
        "price_monthly": 249.00,
        "price_yearly": 199.00,
        "popular": True,
        "features": [
            "Kanban operacional com Cost-per-Task em tempo real",
            "Financeiro empresarial: DRE, fluxo de caixa D+90, conciliação",
            "Colaboradores com CTC automático, fornecedores e centros de custo",
            "CFO Virtual IA, conciliação bancária e gerador de orçamentos",
            "Exportação de relatórios em CSV, XLSX e PDF"
        ],
        "limits": {"max_employees": 15, "max_projects": -1, "ai_queries": -1}
    },
    {
        "id": "plan-completo",
        "name": "Completo",
        "scope": "completo",
        "tagline": "Pessoa física e empresa, tudo em uma conta só",
        "price_monthly": 279.00,
        "price_yearly": 229.00,
        "popular": False,
        "features": [
            "Tudo do plano Empresarial",
            "Tudo do plano Pessoal",
            "Um único login para gerir sua empresa e suas finanças pessoais",
            "CFO Virtual IA (empresarial) + CFO Pessoal IA (pessoal)"
        ],
        "limits": {"max_employees": 15, "max_projects": -1, "ai_queries": -1}
    }
]

@router.get("/")
async def list_plans():
    return PLANS_DB

@router.get("/{plan_id}")
async def get_plan(plan_id: str):
    plan = next((p for p in PLANS_DB if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan
