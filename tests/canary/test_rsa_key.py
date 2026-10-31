# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Pruebas de que la clave id_rsa es RSA de 2048 bits y carga con cryptography.
# Puede importar: honey_agent.canary
# No importar: honey_agent.ingress, honey_agent.posix, honey_agent.defense

import sys
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from honey_agent.canary.factory import generate_rsa_private_key_pem


class GenerateRsaPrivateKeyPemTests(unittest.TestCase):
    def test_pem_loads_as_2048_bit_rsa(self) -> None:
        pem = generate_rsa_private_key_pem()
        key = serialization.load_pem_private_key(pem.encode(), password=None)
        self.assertIsInstance(key, rsa.RSAPrivateKey)
        self.assertEqual(key.key_size, 2048)

    def test_two_calls_return_different_pems(self) -> None:
        first = generate_rsa_private_key_pem()
        second = generate_rsa_private_key_pem()
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
