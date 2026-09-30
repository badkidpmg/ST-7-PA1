import time
import uuid
from decimal import Decimal

import httpx


SERVER_URL = "http://127.0.0.1:8000"


def check_server() -> None:
    response = httpx.get(f"{SERVER_URL}/health")

    print("Código HTTP:", response.status_code)
    print("Respuesta:", response.json())


def send_transfer() -> None:
    transfer = {
        "tx_id": str(uuid.uuid4()),
        "origin_account": "ES1234567890123456789012",
        "destination_account": "ES9876543210987654321098",
        "amount": 1500.50,
        "currency": "EUR",
        "timestamp": int(time.time()),
    }

    response = httpx.post(
        f"{SERVER_URL}/api/v1/transfer",
        json=transfer,
    )

    print("Código HTTP:", response.status_code)
    print("Respuesta:", response.json())


if __name__ == "__main__":
    check_server()
    send_transfer()