import sqlite3

from fastapi.testclient import TestClient

from server.main import app


def test_login_me_logout(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "auth.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))

    with TestClient(app) as client:
        registered = client.post(
            "/api/v1/register",
            json={
                "username": "usuario_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert registered.status_code == 201

        bad_login = client.post(
            "/api/v1/login",
            json={
                "username": "usuario_test",
                "password": "clave_incorrecta",
            },
        )
        assert bad_login.status_code == 401

        good_login = client.post(
            "/api/v1/login",
            json={
                "username": "usuario_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert good_login.status_code == 200

        token = good_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        assert client.get("/api/v1/me").status_code == 401

        profile = client.get("/api/v1/me", headers=headers)
        assert profile.status_code == 200
        assert profile.json()["username"] == "usuario_test"

        logout = client.post("/api/v1/logout", headers=headers)
        assert logout.status_code == 200

        assert client.get("/api/v1/me", headers=headers).status_code == 401

    with sqlite3.connect(db_path) as connection:
        stored = connection.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]

    assert stored == 0


def test_login_temporarily_locks_after_five_failures(
    tmp_path, monkeypatch
) -> None:
    db_path = tmp_path / "lock.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))

    with TestClient(app) as client:
        client.post(
            "/api/v1/register",
            json={
                "username": "bloqueo_test",
                "password": "ClaveDePrueba123!",
            },
        )

        for attempt in range(1, 6):
            response = client.post(
                "/api/v1/login",
                json={
                    "username": "bloqueo_test",
                    "password": "clave_incorrecta",
                },
            )
            assert response.status_code == (429 if attempt == 5 else 401)

        correct_while_locked = client.post(
            "/api/v1/login",
            json={
                "username": "bloqueo_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert correct_while_locked.status_code == 429




def test_unknown_token_is_rejected(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "unknown_token.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer token-inventado"},
        )

    assert response.status_code == 401


def test_expired_session_is_rejected_and_deleted(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "expired_session.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))

    with TestClient(app) as client:
        registered = client.post(
            "/api/v1/register",
            json={
                "username": "caducidad_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert registered.status_code == 201

        login = client.post(
            "/api/v1/login",
            json={
                "username": "caducidad_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert login.status_code == 200

        token = login.json()["access_token"]

        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "UPDATE sessions SET expires_at = 0"
            )

        response = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Sesión caducada"

    with sqlite3.connect(db_path) as connection:
        remaining = connection.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]

    assert remaining == 0

def test_logged_out_token_cannot_be_reused(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "logout_reuse.db"
    monkeypatch.setenv("SECBANK_DB_PATH", str(db_path))

    with TestClient(app) as client:
        registered = client.post(
            "/api/v1/register",
            json={
                "username": "logout_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert registered.status_code == 201

        login = client.post(
            "/api/v1/login",
            json={
                "username": "logout_test",
                "password": "ClaveDePrueba123!",
            },
        )
        assert login.status_code == 200

        headers = {
            "Authorization": f"Bearer {login.json()['access_token']}"
        }

        assert client.get("/api/v1/me", headers=headers).status_code == 200
        assert client.post("/api/v1/logout", headers=headers).status_code == 200

        reused = client.get("/api/v1/me", headers=headers)

    assert reused.status_code == 401