# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Fábrica HMAC-SHA256 de claves AWS, URI PostgreSQL, JWT y pares SSH. Implementa la generación del puerto CanarySource.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.defense, honey_agent.composition

import hashlib
import hmac

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_canary_aws_key(
    attacker_ip: str,
    session_id: str,
    *,
    secret: bytes,
    timestamp: int,
) -> dict:
    """Return a synthetic AWS key pair whose access key embeds an HMAC-SHA256 stamp."""
    if secret == b"":
        raise ValueError("secret must not be empty")
    access_key_id = _aws_access_key_id(attacker_ip, session_id, timestamp, secret)
    secret_access_key = hmac.new(
        secret,
        access_key_id.encode(),
        hashlib.sha256,
    ).hexdigest()
    return {
        "AWS_ACCESS_KEY_ID": access_key_id,
        "AWS_SECRET_ACCESS_KEY": secret_access_key,
        "EMBEDDED_IP": attacker_ip,
        "SESSION_ID": session_id,
    }


def verify_aws_access_key(
    access_key_id: str,
    attacker_ip: str,
    session_id: str,
    timestamp: int,
    secret: bytes,
) -> bool:
    """Recompute the access-key signature and compare it with hmac.compare_digest."""
    expected = _aws_access_key_id(attacker_ip, session_id, timestamp, secret)
    return hmac.compare_digest(access_key_id, expected)


def _aws_access_key_id(
    attacker_ip: str,
    session_id: str,
    timestamp: int,
    secret: bytes,
) -> str:
    payload = f"{attacker_ip}:{session_id}:{timestamp}".encode()
    signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()[:12].upper()
    return f"AKIA{signature}CANARY"


def generate_rsa_private_key_pem() -> str:
    """Return a new unencrypted PKCS#8 PEM for a 2048-bit RSA private key."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
