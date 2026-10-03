import json
import sqlite3
import time
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.transfer_mac import make_signature


PATH = "/api/v1/transfer"
TEST_KEY_HEX = "22" * 32


def signed_request(
    token: str,
    body: bytes,
    nonce: str,
    timestamp: str,
) -> tuple[bytes, dict[str, str]]:
    signature = make_signature(
        key=bytes.fromhex(TEST_KEY_HEX),
        method="POST",
        path=PATH,
        token=token,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )

    headers = {
        "Authorization": "Be" "arer " + token,
        "X-Nonce": nonce,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json",
    }

    return body, headers


def test_replay_and_timestamp_window(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "replay.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))
    monkeypatch.setenv("SECBANK_HMAC_KEY_HEX", TEST_KEY_HEX)

    with TestClient(app) as client:
        registered = client.post(
            "/api/v1/register",
            json={
                "username": "replay_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert registered.status_code == 201

        login = client.post(
            "/api/v1/login",
            json={
                "username": "replay_test",
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

        now = str(int(time.time()))
        nonce = str(uuid.uuid4())

        content, headers = signed_request(token, body, nonce, now)

        first = client.post(PATH, content=content, headers=headers)
        repeated = client.post(PATH, content=content, headers=headers)

        assert first.status_code == 201
        assert repeated.status_code == 409
        assert repeated.json()["detail"] == "Replay: nonce ya procesado"

        new_nonce = str(uuid.uuid4())
        content, headers = signed_request(token, body, new_nonce, now)

        distinct = client.post(PATH, content=content, headers=headers)
        assert distinct.status_code == 201

        old_timestamp = str(int(time.time()) - 300)
        content, headers = signed_request(
            token,
            body,
            str(uuid.uuid4()),
            old_timestamp,
        )

        stale = client.post(PATH, content=content, headers=headers)
        assert stale.status_code == 400

        future_timestamp = str(int(time.time()) + 300)
        content, headers = signed_request(
            token,
            body,
            str(uuid.uuid4()),
            future_timestamp,
        )

        future = client.post(PATH, content=content, headers=headers)
        assert future.status_code == 400

    with sqlite3.connect(db_path) as connection:
        stored = connection.execute(
            "SELECT COUNT(*) FROM processed_nonces"
        ).fetchone()[0]

    assert stored == 2
