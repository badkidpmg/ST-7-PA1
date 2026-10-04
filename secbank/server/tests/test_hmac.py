import pytest

from app.transfer_mac import get_hmac_key, verify_signature


def test_hmac_key_has_at_least_256_bits(monkeypatch) -> None:
    monkeypatch.setenv("SECBANK_HMAC_KEY_HEX", "11" * 32)
    assert len(get_hmac_key()) == 32


def test_short_hmac_key_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("SECBANK_HMAC_KEY_HEX", "11" * 31)

    with pytest.raises(RuntimeError):
        get_hmac_key()


def test_signature_verification_is_exact() -> None:
    expected = "a" * 64

    assert verify_signature(expected, expected)
    assert not verify_signature(expected, "b" * 64)
    assert not verify_signature(expected, "a" * 63)
    assert not verify_signature(expected, "not-a-signature")