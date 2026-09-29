from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.database import configured_db_path, init_db
from server.routes.transfers import router as transfers_router
from server.routes.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_path = configured_db_path()
    init_db(app.state.db_path)
    yield


app = FastAPI(
    title="SecBank API",
    description="API REST del proyecto IntegriDos",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "application": "SecBank",
        "status": "running",
        "version": "0.2.0",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(transfers_router)