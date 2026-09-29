from fastapi import APIRouter, HTTPException, status

from server.models import TransferRequest


router = APIRouter(
    prefix="/api/v1",
    tags=["transfers"],
)


@router.post("/transfer")
def create_transfer(transfer: TransferRequest) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Transferencias no disponibles hasta implementar autenticación",
    )