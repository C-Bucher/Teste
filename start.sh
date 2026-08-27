#!/bin/sh
# Só instala se os pacotes ainda não existem — startup instantâneo após primeiro boot
if ! python -c "import fastapi, uvicorn, jwt, bcrypt" 2>/dev/null; then
    echo "[TechConnect] Instalando dependências..."
    pip install fastapi "uvicorn[standard]" PyJWT bcrypt "passlib[bcrypt]" \
        python-multipart aiofiles httpx python-dotenv -q
    echo "[TechConnect] Dependências instaladas."
else
    echo "[TechConnect] Dependências já instaladas — iniciando direto."
fi
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning
