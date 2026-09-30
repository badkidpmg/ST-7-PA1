from fastapi import FastAPI

app = FastAPI(title="SecBank API", description="Servidor de transferencias bancarias (PAI-1 IntegriDos)")


@app.get("/health")
def health():
    return {"status": "ok", "service": "secbank-server"}