from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from app.api.v1.api import api_router
from app.db.session import init_db
from app.db.seed import seed_if_empty
from app.core.config import CORS_ORIGINS
from app.core.audit import client_ip
from app.core import rate_limit
import logging
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse as _JSONResponse

app = FastAPI(title="TechConnect API v2.0 - Clean Arch", version="2.0.0")

@app.on_event("startup")
async def on_startup():
    await init_db()
    await seed_if_empty()
    if os.getenv("APP_ENV", "development").lower() == "production":
        from app.core.readiness import production_warnings
        for warning in production_warnings():
            logging.getLogger("techconnect").warning("Configuração de produção: %s", warning)
    if os.getenv("DEMO_REFRESH_DATES") == "1":
        from app.db.demo_dates import refresh_demo_dates
        from app.db.session import async_session_maker
        async with async_session_maker() as db:
            await refresh_demo_dates(db)

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition", "X-Subscription", "Retry-After"])

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc: IntegrityError):
    # Endpoints take free-form dicts; a missing required field or duplicate must be a 400, not a 500.
    logging.getLogger("techconnect").warning("IntegrityError em %s: %s", request.url.path, exc.orig)
    return _JSONResponse(status_code=400, content={"detail": "Dados inválidos ou incompletos: verifique os campos obrigatórios"})


@app.middleware("http")
async def remember_client_ip(request, call_next):
    ip = rate_limit.resolve_client_ip(request)
    client_ip.set(ip)
    if rate_limit.is_limited(request.url.path, request.method):
        wait = rate_limit.check(ip)
        if wait:
            return _JSONResponse(status_code=429, headers={"Retry-After": str(wait)},
                                 content={"detail": f"Muitas tentativas. Aguarde {wait} segundos e tente de novo."})
    return await call_next(request)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health(): return {"status":"ok","version":"2.0.0","database":"ok","timestamp":datetime.now().isoformat()}

@app.get("/api/v1/health")
async def health2(): return {"status":"ok","version":"2.0.0","timestamp":datetime.now().isoformat()}

# Serve static files for frontend
import os
from fastapi.responses import FileResponse
from fastapi import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

# Ensure uploads directory exists and mount it
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.exception_handler(404)
    async def not_found(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith("/api/") or request.url.path.startswith("/health"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse("frontend/dist/index.html")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "health" or full_path.startswith("docs") or full_path.startswith("redoc") or full_path == "openapi.json":
            raise StarletteHTTPException(status_code=404, detail="Not Found")
        path = f"frontend/dist/{full_path}"
        if os.path.isfile(path):
            return FileResponse(path)
        return FileResponse("frontend/dist/index.html")
elif os.path.exists("../frontend/dist"):
    app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")
    
    @app.exception_handler(404)
    async def not_found(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith("/api/") or request.url.path.startswith("/health"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse("../frontend/dist/index.html")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "health" or full_path.startswith("docs") or full_path.startswith("redoc") or full_path == "openapi.json":
            raise StarletteHTTPException(status_code=404, detail="Not Found")
        path = f"../frontend/dist/{full_path}"
        if os.path.isfile(path):
            return FileResponse(path)
        return FileResponse("../frontend/dist/index.html")
