"""
Genera el tráfico necesario para las evidencias del PAI1 (Wireshark).

Colocar en secbank/client/ y ejecutar dentro de la red de Docker:

    docker compose run --rm client python attack_demo.py alice_demo DemoAlice123!

Escenarios (con pausa entre ellos para distinguirlos en la captura):
  1. Transferencia legítima          -> 201
  2. Replay (mismo paquete exacto)   -> 409 (nonce ya procesado)
  3. MitM (cuerpo alterado, misma firma) -> 401 (firma HMAC no válida)
  4. Timestamp caducado (firmado bien)   -> 400 (fuera de ventana)
"""
import json
import sys
import time
import uuid

import requests

# Reutiliza la misma lógica de firma que el cliente real
from client import SERVER_URL, TRANSFER_PATH, get_hmac_key, make_signature

PAUSE = 3  # segundos entre escenarios


def login(username: str, password: str) -> str:
    r = requests.post(
        f"{SERVER_URL}/api/v1/login",
        json={"username": username, "password": password},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def build_request(token: str, ts_offset: int = 0):
    """Devuelve (body, headers) con una transferencia correctamente firmada."""
    payload = {
        "tx_id": str(uuid.uuid4()),
        "origin_account": "ES1234567890123456789012",
        "destination_account": "ES9876543210987654321098",
        "amount": "1500.50",
        "currency": "EUR",
        "timestamp": int(time.time()) + ts_offset,
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    nonce = str(uuid.uuid4())
    timestamp = str(int(time.time()) + ts_offset)

    signature = make_signature(
        key=get_hmac_key(),
        method="POST",
        path=TRANSFER_PATH,
        token=token,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Nonce": nonce,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
    }
    return body, headers


def send(label: str, body: bytes, headers: dict) -> None:
    r = requests.post(
        f"{SERVER_URL}{TRANSFER_PATH}", data=body, headers=headers, timeout=5
    )
    print(f"[{label}] HTTP {r.status_code} -> {r.text}")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Uso: python attack_demo.py <usuario> <contraseña>")

    token = login(sys.argv[1], sys.argv[2])
    print("[login] OK\n")

    # 1. Legítima
    body, headers = build_request(token)
    send("1 LEGÍTIMA", body, headers)
    time.sleep(PAUSE)

    # 2. Replay: se reenvía EXACTAMENTE el mismo paquete
    send("2 REPLAY", body, headers)
    time.sleep(PAUSE)

    # 3. MitM: se altera el importe en tránsito sin recalcular la firma
    body3, headers3 = build_request(token)
    tampered = body3.replace(b'"amount":"1500.50"', b'"amount":"9999.99"')
    assert tampered != body3
    send("3 MITM (amount alterado)", tampered, headers3)
    time.sleep(PAUSE)

    # 4. Timestamp fuera de ventana (firma válida, pero 120 s en el pasado)
    body4, headers4 = build_request(token, ts_offset=-120)
    send("4 TIMESTAMP CADUCADO", body4, headers4)


if __name__ == "__main__":
    main()
