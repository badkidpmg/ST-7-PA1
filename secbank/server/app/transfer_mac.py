import hashlib
import hmac
import os
import re


HEX_64 = re.compile(r"^[0-9a-fA-F]{64}$")


def get_hmac_key() -> bytes:
    value = os.environ.get("SECBANK_HMAC_KEY_HEX", "")

    if not HEX_64.fullmatch(value):
        raise RuntimeError(
            "SECBANK_HMAC_KEY_HEX debe contener exactamente "
            "64 caracteres hexadecimales (32 bytes)"
        )

    return bytes.fromhex(value)


def signed_bytes(
    method: str,
    path: str,
    token: str,
    timestamp: str,
    nonce: str,
    body: bytes,
) -> bytes:
    parts = (
        method.encode("ascii"),
        path.encode("ascii"),
        token.encode("ascii"),
        timestamp.encode("ascii"),
        nonce.encode("ascii"),
        body,
    )

    return b"".join(
        len(part).to_bytes(4, "big") + part
        for part in parts
    )


def make_signature(
    key: bytes,
    method: str,
    path: str,
    token: str,
    timestamp: str,
    nonce: str,
    body: bytes,
) -> str:
    if len(key) < 32:
        raise ValueError("La clave HMAC debe tener al menos 32 bytes")

    message = signed_bytes(
        method,
        path,
        token,
        timestamp,
        nonce,
        body,
    )

    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_signature(expected: str, received: str) -> bool:
    if not HEX_64.fullmatch(received):
        return False

    return hmac.compare_digest(
        expected,
        received.lower(),
    )