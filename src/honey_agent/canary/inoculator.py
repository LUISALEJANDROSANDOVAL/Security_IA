# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Si el comando lee secretos simulados, sustituye el cuerpo por credenciales sintéticas de esta sesión.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.defense, honey_agent.composition

import shlex
from dataclasses import dataclass

from honey_agent.canary.factory import (
    generate_canary_aws_key,
    generate_canary_jwt,
    generate_rsa_private_key_pem,
)

_POSTGRES_URI = "postgres://db_backup:p4ss@10.0.8.44:5432/corp_fin"
_SSH_LINE = "ssh -i ~/.ssh/backup_key dbadmin@10.0.12.88"
_DNS_NAME = "vault-internal.corp.canary.domain"
_REPLICA_PASSWORD = "canary_replica_p4ss"

_ENV_PATH = "/var/www/html/.env"
_AWS_CREDENTIALS = "~/.aws/credentials"
_BASH_HISTORY = "~/.bash_history"
_HOSTS_PATH = "/etc/hosts"
_MYSQL_PATH = "/etc/mysql/my.cnf"

_TOKEN_AWS = "AWS_IAM_CREDENTIAL"
_TOKEN_BASH = "BASH_HISTORY"
_TOKEN_DNS = "DNS_CANARY"
_TOKEN_DB = "DB_CONFIG"
_TOKEN_SSH = "SSH_PRIVATE_KEY"
_ID_RSA = "id_rsa"

_READERS = frozenset({
    "awk",
    "base64",
    "bat",
    "cat",
    "cut",
    "dd",
    "egrep",
    "emacs",
    "fgrep",
    "grep",
    "head",
    "hexdump",
    "less",
    "more",
    "nano",
    "nl",
    "od",
    "rg",
    "sed",
    "sort",
    "strings",
    "tac",
    "tail",
    "uniq",
    "vi",
    "view",
    "vim",
    "xxd",
})

_LEFT_EDGE = set(" \t\n\"'`|&;<>()$")
_RIGHT_EDGE = set(" \t\n\"'`|&;<>()")


@dataclass(frozen=True)
class Inoculation:
    output: str
    token_type: str
    token_identifier: str
    destination_asset: str


def inoculate(
    command: str,
    *,
    attacker_ip: str,
    session_id: str,
    secret: bytes,
    timestamp: int,
) -> Inoculation | None:
    """Return session bait, or None when the command is not seeking a secret.

    A match discards any earlier stdout: the caller shows only this output.
    A read whose path's final component is id_rsa returns a new 2048-bit RSA
    private key. destination_asset is that path argument as written.
    """
    text = command.strip()
    if not text:
        return None
    tokens = _tokens(text)
    reading = _is_read(tokens)
    if reading and _mentions(text, _ENV_PATH):
        return _aws_inoculation(
            attacker_ip, session_id, secret, timestamp, _ENV_PATH, with_postgres=True,
        )
    if reading and _mentions(text, ".aws/credentials", extra_left="/"):
        return _aws_inoculation(
            attacker_ip, session_id, secret, timestamp, _AWS_CREDENTIALS, with_postgres=True,
        )
    if reading and _mentions(text, ".bash_history", extra_left="/"):
        return _history_inoculation(_BASH_HISTORY)
    if reading and _mentions(text, _HOSTS_PATH):
        return _dns_inoculation()
    if reading and _mentions(text, _MYSQL_PATH):
        return _db_inoculation()
    if reading:
        rsa_path = _id_rsa_path(text)
        if rsa_path is not None:
            return _ssh_key_inoculation(rsa_path)
    if _command_name(tokens) == "history":
        return _history_inoculation("history")
    if _command_name(tokens) == "env":
        return _aws_inoculation(
            attacker_ip, session_id, secret, timestamp, "env", with_postgres=False,
        )
    return None


def _aws_inoculation(
    attacker_ip: str,
    session_id: str,
    secret: bytes,
    timestamp: int,
    destination_asset: str,
    *,
    with_postgres: bool,
) -> Inoculation:
    issued = generate_canary_aws_key(
        attacker_ip,
        session_id,
        secret=secret,
        timestamp=timestamp,
    )
    access_key = issued["AWS_ACCESS_KEY_ID"]
    lines = []
    if with_postgres:
        lines.append(f"DATABASE_URL={_POSTGRES_URI}")
        lines.append(
            "CORP_JWT="
            + generate_canary_jwt(
                attacker_ip,
                session_id,
                secret=secret,
                timestamp=timestamp,
            )
        )
    lines.append(f"AWS_ACCESS_KEY_ID={access_key}")
    lines.append(f"AWS_SECRET_ACCESS_KEY={issued['AWS_SECRET_ACCESS_KEY']}")
    return Inoculation(
        output="\n".join(lines) + "\n",
        token_type=_TOKEN_AWS,
        token_identifier=access_key,
        destination_asset=destination_asset,
    )


def _history_inoculation(destination_asset: str) -> Inoculation:
    return Inoculation(
        output=_SSH_LINE + "\n",
        token_type=_TOKEN_BASH,
        token_identifier=_SSH_LINE,
        destination_asset=destination_asset,
    )


def _dns_inoculation() -> Inoculation:
    output = f"127.0.0.1 localhost\n10.0.8.44 {_DNS_NAME}\n"
    return Inoculation(
        output=output,
        token_type=_TOKEN_DNS,
        token_identifier=_DNS_NAME,
        destination_asset=_HOSTS_PATH,
    )


def _ssh_key_inoculation(destination_asset: str) -> Inoculation:
    pem = generate_rsa_private_key_pem()
    if not pem.endswith("\n"):
        pem += "\n"
    return Inoculation(
        output=pem,
        token_type=_TOKEN_SSH,
        token_identifier=_ID_RSA,
        destination_asset=destination_asset,
    )


def _id_rsa_path(command: str) -> str | None:
    """Return the first token whose final path component is id_rsa."""
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        parts = command.split()
    for part in parts:
        leaf = part.rsplit("/", 1)[-1]
        if leaf.lower() == _ID_RSA:
            return part
    return None


def _db_inoculation() -> Inoculation:
    output = (
        "[client]\n"
        "host=10.0.8.44\n"
        "user=repl_corp\n"
        f"password={_REPLICA_PASSWORD}\n"
    )
    return Inoculation(
        output=output,
        token_type=_TOKEN_DB,
        token_identifier=_REPLICA_PASSWORD,
        destination_asset=_MYSQL_PATH,
    )


def _tokens(command: str) -> list[str]:
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        parts = command.split()
    return [part.lower() for part in parts]


def _command_name(tokens: list[str]) -> str:
    if not tokens:
        return ""
    return _basename(tokens[0])


def _basename(token: str) -> str:
    name = token
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    return name


def _is_read(tokens: list[str]) -> bool:
    return any(_basename(token) in _READERS for token in tokens)


def _mentions(command: str, needle: str, extra_left: str = "") -> bool:
    folded = command.lower()
    target = needle.lower()
    left_edge = _LEFT_EDGE | set(extra_left)
    start = 0
    while True:
        index = folded.find(target, start)
        if index < 0:
            return False
        end = index + len(target)
        left_ok = index == 0 or folded[index - 1] in left_edge
        right_ok = end == len(folded) or folded[end] in _RIGHT_EDGE
        if left_ok and right_ok:
            return True
        start = index + 1
