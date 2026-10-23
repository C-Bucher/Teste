# NOTA: Ponto de partida do servidor. Importa o app de app/main.py e, se for executado direto
#       (python main.py), liga o servidor na porta 8000 com recarga automática ao salvar.

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)