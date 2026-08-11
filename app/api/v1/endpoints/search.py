from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user
from app.db.database import EMPLOYEES, KANBAN_CLIENTS, KANBAN_PROJECTS, FINANCIAL_ENTRIES, SUPPLIERS

router = APIRouter()

@router.get("/")
async def global_search(q:str="",limit:int=15,u=Depends(get_current_user)):
    q=q.strip().lower()
    if len(q)<2: return {"results":[],"total":0,"query":q}
    results=[]
    for emp in EMPLOYEES:
        if q in emp.get("full_name","").lower() or q in emp.get("role","").lower() or q in emp.get("email","").lower():
            results.append({"type":"employee","id":emp["id"],"title":emp["full_name"],"subtitle":emp.get("role",""),"url":"/employees"})
    for cli in KANBAN_CLIENTS:
        if q in cli.get("name","").lower() or q in cli.get("contact_name","").lower() or q in cli.get("segment","").lower():
            results.append({"type":"client","id":cli["id"],"title":cli["name"],"subtitle":cli.get("segment",""),"url":"/clients"})
    for proj in KANBAN_PROJECTS:
        if q in proj.get("name","").lower() or q in proj.get("description","").lower():
            results.append({"type":"project","id":proj["id"],"title":proj["name"],"subtitle":proj.get("status",""),"url":f"/kanban/{proj['id']}"})
    for en in FINANCIAL_ENTRIES:
        if q in en.get("description","").lower() or q in en.get("category","").lower():
            results.append({"type":"financial","id":en["id"],"title":en["description"],"subtitle":f"{en['type']} · R$ {en['amount']:,.2f}","url":"/financial"})
    for sup in SUPPLIERS:
        if q in sup.get("name","").lower() or q in sup.get("category","").lower():
            results.append({"type":"supplier","id":sup["id"],"title":sup["name"],"subtitle":sup.get("category",""),"url":"/suppliers"})
    return {"results":results[:limit],"total":len(results),"query":q}
