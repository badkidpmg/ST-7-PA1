import sqlite3

from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from app.main import app


def test_register_stores_hash_and_rejects_duplicate(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "test_secbank.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))

    payload = {
        "username": "ines_test",
        "password": "ClaveDePrueba123!",
    }

    with TestClient(app) as client:
        first = client.post("/api/v1/register", json=payload)
        second = client.post("/api/v1/register", json=payload)

    assert first.status_code == 201
    assert first.json()["username"] == "ines_test"
    assert "password" not in first.json()
    assert "password_hash" not in first.json()
    assert second.status_code == 409

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            ("ines_test",),
        ).fetchall()

    assert len(rows) == 1
    stored_hash = rows[0][0]

    assert stored_hash != payload["password"]
    assert stored_hash.startswith("$argon2id$")
    assert PasswordHasher().verify(stored_hash, payload["password"])



def test_same_password_gets_different_argon2_hashes(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "salt.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))

    password = "ClaveDePrueba123!"

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/register",
            json={
                "username": "usuario_uno",
                "password": password,
            },
        )
        second = client.post(
            "/api/v1/register",
            json={
                "username": "usuario_dos",
                "password": password,
            },
        )

        assert first.status_code == 201
        assert second.status_code == 201

    with sqlite3.connect(db_path) as connection:
        hashes = [
            row[0]
            for row in connection.execute(
                """
                SELECT password_hash
                FROM users
                ORDER BY username
                """
            ).fetchall()
        ]

    assert len(hashes) == 2
    assert hashes[0] != hashes[1]
    assert all(password_hash.startswith("$argon2id$") for password_hash in hashes)