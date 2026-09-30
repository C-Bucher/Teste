from fastapi import APIRouter, HTTPException

router = APIRouter()

# Prices approved on 2026-09-30 (docs/BACKLOG.md PLAN-1); to be revisited with the bank aggregator quote.
# limits: -1 = unlimited; ai_queries is a monthly fair-use cap; bank_connections counts linked bank accounts.
PLANS_DB = [
    {
        "id": "plan-pessoal",
        "name": "Pessoal Essencial",
        "scope": "pessoal",
        "tagline": "Organize suas finanças pessoais com apoio de IA",
        "price_monthly": 29.90,
        "price_yearly": 24.90,
        "popular": False,
        "features": [
            "Hub Pessoal completo: contas, cartões, orçamento e metas",
            "Controle de dívidas, assinaturas e divisão de despesas",
            "Importação de extrato bancário (OFX/CSV)",
            "CFO Pessoal IA: até 100 perguntas por mês",
            "Dashboard analítico de evolução patrimonial"
        ],
        "limits": {"max_employees": 0, "max_projects": 0, "ai_queries": 100, "bank_connections": 0}
    },
    {
        "id": "plan-pessoal-conectado",
        "name": "Pessoal Conectado",
        "scope": "pessoal",
        "tagline": "Suas contas se atualizam sozinhas, sem digitar nada",
        "price_monthly": 59.90,
        "price_yearly": 49.90,
        "popular": False,
        "features": [
            "Tudo do Pessoal Essencial",
            "Até 3 bancos conectados com sincronização automática",
            "Categorização e conciliação automáticas do extrato",
            "CFO Pessoal IA sem limite mensal (uso justo)"
        ],
        "limits": {"max_employees": 0, "max_projects": 0, "ai_queries": 1000, "bank_connections": 3}
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
            "Até 3 contas PJ conectadas (conta extra cobrada à parte)",
            "CFO Virtual IA, conciliação e gerador de orçamentos",
            "Exportação de relatórios em CSV e JSON"
        ],
        "limits": {"max_employees": 15, "max_projects": -1, "ai_queries": 3000, "bank_connections": 3}
    },
    {
        "id": "plan-completo",
        "name": "Completo",
        "scope": "completo",
        "tagline": "Pessoa física e empresa, tudo em uma conta só",
        "price_monthly": 299.00,
        "price_yearly": 249.00,
        "popular": False,
        "features": [
            "Tudo do plano Empresarial",
            "Tudo do plano Pessoal Conectado",
            "Um único login para gerir sua empresa e suas finanças pessoais",
            "CFO Virtual IA (empresarial) + CFO Pessoal IA (pessoal)"
        ],
        "limits": {"max_employees": 15, "max_projects": -1, "ai_queries": 4000, "bank_connections": 6}
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
