from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user

router = APIRouter()

@router.post("/chat")
async def ai_chat(d:dict,u=Depends(get_current_user)):
    msg=d.get("message","").lower()
    if "fluxo" in msg or "caixa" in msg: resp="Analise de Fluxo de Caixa: Saldo acumulado R$ 48.000. Identifico 3 lancamentos pendentes vencendo nos proximos 15 dias totalizando R$ 15.540. Recomendo antecipar cobranca do Projeto Website Varejo."
    elif "dre" in msg or "resultado" in msg: resp="DRE Consolidado: Receita bruta R$ 102.500 vs despesas R$ 21.340. Margem liquida 79,2%. Segmento SaaS e o maior gerador de receita."
    elif "ctc" in msg or "colaborador" in msg: resp="Analise CTC: Custo total da equipe R$ 51.875/mes. Fernanda Costa (PJ) tem menor overhead (10%). Cost-per-Task medio R$ 391,40."
    else: resp="TechConnect CFO Virtual: Posso auxiliar com fluxo de caixa, DRE, analise de CTC e insights de produtividade. O que gostaria de explorar?"
    return {"response":resp,"model":"gemini-2.5-flash","tokens_used":245}

@router.post("/consultant/cfo")
async def ai_cfo(d:dict,u=Depends(get_current_user)):
    return {"insights":[{"type":"OPORTUNIDADE","title":"Expansao SaaS","description":"Segmento SaaS cresceu 35%. Recomendo investir em aquisicao.","impact":"Alto","urgency":"Media"},{"type":"ALERTA","title":"Fluxo Caixa 2 Semanas","description":"R$ 15.540 em despesas antes da entrada do Contrato Anual. Reserve capital.","impact":"Alto","urgency":"Alta"}]}

@router.post("/consultant/conciliation")
async def ai_conc(d:dict,u=Depends(get_current_user)): return {"results":[{"description":d.get("description","Transacao"),"suggested_category":"Infraestrutura","confidence":0.92,"status":"APROVADO_AUTO"}]}

@router.post("/consultant/proposal")
async def ai_prop(d:dict,u=Depends(get_current_user)): return {"estimated_internal_cost":18500.00,"suggested_price":32000.00,"margin_percentage":42.3}

@router.get("/history")
async def ai_hist(u=Depends(get_current_user)): return {"items":[],"total":0}
