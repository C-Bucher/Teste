from fastapi import APIRouter, HTTPException

router = APIRouter()

PLANS_DB = [
    {
        "id": "plan-starter",
        "name": "Starter",
        "tagline": "Ideal para autônomos e pequenas equipes",
        "price_monthly": 99.00,
        "price_yearly": 79.00,
        "popular": False,
        "features": [
            "Até 3 membros na equipe",
            "Até 2 projetos simultâneos no Kanban",
            "Relatórios financeiros básicos (DRE e Fluxo de Caixa)",
            "50 consultas mensais ao CFO Virtual IA",
            "Suporte via e-mail"
        ],
        "limits": {
            "max_employees": 3,
            "max_projects": 2,
            "ai_queries": 50
        }
    },
    {
        "id": "plan-pro",
        "name": "Pro",
        "tagline": "Mais popular para empresas em crescimento",
        "price_monthly": 249.00,
        "price_yearly": 199.00,
        "popular": True,
        "features": [
            "Até 15 membros na equipe",
            "Projetos e colunas Kanban ilimitados",
            "DRE Consolidado, DFC e Projeções Financeiras",
            "CFO Virtual IA Ilimitado com insights preditivos",
            "Exportação de relatórios em PDF e Excel",
            "Suporte prioritário"
        ],
        "limits": {
            "max_employees": 15,
            "max_projects": -1,
            "ai_queries": -1
        }
    },
    {
        "id": "plan-enterprise",
        "name": "Enterprise",
        "tagline": "Para grandes empresas que necessitam de escopo customizado",
        "price_monthly": 599.00,
        "price_yearly": 499.00,
        "popular": False,
        "features": [
            "Membros de equipe ilimitados",
            "Múltiplas empresas / holding no mesmo painel",
            "Integrações bancárias via Open Finance",
            "CFO Virtual IA dedicado com treinamento de dados",
            "Gerente de conta exclusivo e SLA de 2 horas",
            "Segurança avançada (SSO, Audit Logs, MFA Obrigatório)"
        ],
        "limits": {
            "max_employees": -1,
            "max_projects": -1,
            "ai_queries": -1
        }
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
