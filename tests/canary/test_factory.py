# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Pruebas deterministas del formato AKIA/CANARY y de la verificación HMAC.
# Puede importar: honey_agent.canary y tests.fakes
# No importar: honey_agent.ingress, honey_agent.posix, honey_agent.defense

import hashlib
import hmac
import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from honey_agent.canary.factory import (
    generate_canary_aws_key,
    verify_aws_access_key,
)

# Fixture local. No es el secreto de ejemplo de la documentación.
_SECRET = b"t2-factory-unit-secret"
_TIMESTAMP = 1700000000
_IP = "203.0.113.10"
_SESSION = "sess-unit-1"


def _expected_access_key(attacker_ip: str, session_id: str, timestamp: int, secret: bytes) -> str:
    payload = f"{attacker_ip}:{session_id}:{timestamp}".encode()
    signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()[:12].upper()
    return f"AKIA{signature}CANARY"


def _flip_signature_character(access_key: str) -> str:
    index = 4
    replacement = "0" if access_key[index] != "0" else "1"
    return access_key[:index] + replacement + access_key[index + 1 :]


class GenerateCanaryAwsKeyTests(unittest.TestCase):
    def test_access_key_starts_with_akia_and_contains_canary(self) -> None:
        issued = generate_canary_aws_key(
            _IP,
            _SESSION,
            secret=_SECRET,
            timestamp=_TIMESTAMP,
        )
        access_key = issued["AWS_ACCESS_KEY_ID"]
        self.assertTrue(access_key.startswith("AKIA"))
        self.assertTrue(access_key.endswith("CANARY"))
        self.assertIn("CANARY", access_key)
        self.assertEqual(access_key, _expected_access_key(_IP, _SESSION, _TIMESTAMP, _SECRET))
        self.assertEqual(issued["EMBEDDED_IP"], _IP)
        self.assertEqual(issued["SESSION_ID"], _SESSION)
        secret_access_key = hmac.new(_SECRET, access_key.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(issued["AWS_SECRET_ACCESS_KEY"], secret_access_key)

    def test_same_inputs_produce_the_same_key(self) -> None:
        first = generate_canary_aws_key(
            _IP,
            _SESSION,
            secret=_SECRET,
            timestamp=_TIMESTAMP,
        )
        second = generate_canary_aws_key(
            _IP,
            _SESSION,
            secret=_SECRET,
            timestamp=_TIMESTAMP,
        )
        self.assertEqual(first["AWS_ACCESS_KEY_ID"], second["AWS_ACCESS_KEY_ID"])
        self.assertEqual(first["AWS_SECRET_ACCESS_KEY"], second["AWS_SECRET_ACCESS_KEY"])

    def test_different_ip_produces_a_different_key(self) -> None:
        first = generate_canary_aws_key(
            _IP,
            _SESSION,
            secret=_SECRET,
            timestamp=_TIMESTAMP,
        )
        second = generate_canary_aws_key(
            "203.0.113.11",
            _SESSION,
            secret=_SECRET,
            timestamp=_TIMESTAMP,
        )
        self.assertNotEqual(first["AWS_ACCESS_KEY_ID"], second["AWS_ACCESS_KEY_ID"])

    def test_verify_accepts_generated_key_and_rejects_one_character_change(self) -> None:
        issued = generate_canary_aws_key(
            _IP,
            _SESSION,
            secret=_SECRET,
            timestamp=_TIMESTAMP,
        )
        access_key = issued["AWS_ACCESS_KEY_ID"]
        self.assertTrue(
            verify_aws_access_key(access_key, _IP, _SESSION, _TIMESTAMP, _SECRET)
        )
        tampered = _flip_signature_character(access_key)
        self.assertNotEqual(tampered, access_key)
        self.assertFalse(
            verify_aws_access_key(tampered, _IP, _SESSION, _TIMESTAMP, _SECRET)
        )

    def test_empty_secret_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            generate_canary_aws_key(
                _IP,
                _SESSION,
                secret=b"",
                timestamp=_TIMESTAMP,
            )


if __name__ == "__main__":
    unittest.main()
