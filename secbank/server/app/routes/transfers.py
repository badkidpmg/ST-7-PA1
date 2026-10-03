import json
import sqlite3
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import ValidationError

from app.database import get_db_path
from app.models import TransferRequest
from app.routes.users import active_user, get_bearer_token
from app.transfer_mac import (
    get_hmac_key,
    make_signature,
    verify_signature,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["transfers"],
)

TIMESTAMP_WINDOW_SECONDS = 60


@router.post("/transfer", status_code=201)
async def create_transfer(
    request: Request,
    user: tuple[int, str, str] = Depends(active_user),
    db_path: Path = Depends(get_db_path),
    authorization: str | None = Header(default=None),
    x_nonce: str | None = Header(default=None),
    x_timestamp: str | None = Header(default=None),
    x_signature: str | None = Header(default=None),
) -> dict[str, str]:
    if not x_nonce or not x_timestamp or not x_signature:
        raise HTTPException(
            status_code=400,
            detail="Faltan cabeceras de seguridad",
        )

    token = get_bearer_token(authorization)
    body = await request.body()

    try:
        key = get_hmac_key()
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Clave HMAC no configurada en el servidor",
        )

    expected = make_signature(
        key=key,
        method=request.method,
        path=request.url.path,
        token=token,
        timestamp=x_timestamp,
        nonce=x_nonce,
        body=body,
    )

    if not verify_signature(expected, x_signature):
        raise HTTPException(
            status_code=401,
            detail="Firma HMAC no válida",
        )

    try:
        transfer = TransferRequest.model_validate(json.loads(body))
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422,
            detail="Transferencia inválida",
        )

    try:
        parsed_nonce = uuid.UUID(x_nonce)

        if parsed_nonce.version != 4 or str(parsed_nonce) != x_nonce:
            raise ValueError

        if not x_timestamp.isdecimal():
            raise ValueError

        timestamp = int(x_timestamp)

    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Nonce o timestamp con formato inválido",
        )

    now = int(time.time())

    if abs(now - timestamp) > TIMESTAMP_WINDOW_SECONDS:
        raise HTTPException(
            status_code=400,
            detail="Timestamp fuera de la ventana permitida",
        )


    transaction_id = str(uuid.uuid4())

    try:
        with sqlite3.connect(db_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            connection.execute(
                """
                INSERT INTO transactions (
                    id,
                    user_id,
                    tx_id,
                    origin_account,
                    destination_account,
                    amount,
                    currency,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    user[0],
                    transfer.tx_id,
                    transfer.origin_account,
                    transfer.destination_account,
                    str(transfer.amount),
                    transfer.currency,
                    now,
                ),
            )

            connection.execute(
                """
                INSERT INTO processed_nonces (nonce, user_id, seen_at)
                VALUES (?, ?, ?)
                """,
                (x_nonce, user[0], now),
            )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Replay: nonce ya procesado",
        )

    return {
        "status": "created",
        "message": "Transferencia registrada",
        "transaction_id": transaction_id,
    }