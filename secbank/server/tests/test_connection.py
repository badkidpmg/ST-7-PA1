from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_transfer_requires_authentication() -> None:
    transfer = {
        "tx_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "origin_account": "ES1234567890123456789012",
        "destination_account": "ES9876543210987654321098",
        "amount": 1250.75,
        "currency": "EUR",
        "timestamp": 1741690000,
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/transfer", json=transfer)

    assert response.status_code == 401