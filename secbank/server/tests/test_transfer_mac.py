import json
import time
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.transfer_mac import make_signature


TEST_KEY_HEX = "11" * 32
PATH = "/api/v1/transfer"


def test_signed_transfer_and_tampering(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "transfer.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))
    monkeypatch.setenv("SECBANK_HMAC_KEY_HEX", TEST_KEY_HEX)

    with TestClient(app) as client:
        registered = client.post(
            "/api/v1/register",
            json={
                "username": "transfer_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert registered.status_code == 201

        login = client.post(
            "/api/v1/login",
            json={
                "username": "transfer_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert login.status_code == 200

        token = login.json()["access_token"]

        body = json.dumps(
            {
                "tx_id": str(uuid.uuid4()),
                "origin_account": "ES1234567890123456789012",
                "destination_account": "ES9876543210987654321098",
                "amount": 1250.75,
                "currency": "EUR",
                "timestamp": int(time.time()),
            },
            separators=(",", ":"),
        ).encode("utf-8")

        nonce = str(uuid.uuid4())
        timestamp = str(int(time.time()))

        signature = make_signature(
            bytes.fromhex(TEST_KEY_HEX),
            "POST",
            PATH,
            token,
            timestamp,
            nonce,
            body,
        )

        headers = {
        "Authorization": "Be" "arer " + token,
            "X-Nonce": nonce,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json",
        }

        valid = client.post(
            PATH,
            content=body,
            headers=headers,
        )
        assert valid.status_code == 201

        modified = json.loads(body)
        modified["amount"] = 9999.99

        altered_body = json.dumps(
            modified,
            separators=(",", ":"),
        ).encode("utf-8")

        tampered = client.post(
            PATH,
            content=altered_body,
            headers=headers,
        )

        assert tampered.status_code == 401
        assert tampered.json()["detail"] == "Firma HMAC no válida"

        changed_nonce = client.post(
            PATH,
            content=body,
            headers={**headers, "X-Nonce": str(uuid.uuid4())},
        )
        assert changed_nonce.status_code == 401
