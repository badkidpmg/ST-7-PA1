from fastapi import FastAPI

app = FastAPI(title="SecBank API", description="Servidor de transferencias bancarias (PAI-1 IntegriDos)")


@app.get("/health")
def health():
    """Endpoint simple para comprobar que el servidor esta arriba y responde."""
    return {"status": "ok", "service": "secbank-server"}
