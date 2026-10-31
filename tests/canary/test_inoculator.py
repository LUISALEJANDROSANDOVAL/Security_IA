# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Pruebas de que inoculate sustituye la lectura de secretos por el señuelo de la sesión.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.defense, honey_agent.composition

import sys
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from honey_agent.canary.factory import generate_canary_aws_key
from honey_agent.canary.inoculator import inoculate

# Fixture local. No es el secreto de ejemplo de la documentación.
_SECRET = b"t3-inoculator-unit-secret"
_TIMESTAMP = 1700000000
_IP = "203.0.113.10"
_SESSION = "sess-unit-1"
_POSTGRES_URI = "postgres://db_backup:p4ss@10.0.8.44:5432/corp_fin"
_SSH_LINE = "ssh -i ~/.ssh/backup_key dbadmin@10.0.12.88"
_DNS_NAME = "vault-internal.corp.canary.domain"
_REPLICA_PASSWORD = "canary_replica_p4ss"


def _call(command: str, attacker_ip: str = _IP):
    return inoculate(
        command,
        attacker_ip=attacker_ip,
        session_id=_SESSION,
        secret=_SECRET,
        timestamp=_TIMESTAMP,
    )


def _access_key(attacker_ip: str = _IP) -> str:
    issued = generate_canary_aws_key(
        attacker_ip,
        _SESSION,
        secret=_SECRET,
        timestamp=_TIMESTAMP,
    )
    return issued["AWS_ACCESS_KEY_ID"]


class InoculateTests(unittest.TestCase):
    def test_cat_dotenv_contains_aws_access_key_and_canary(self) -> None:
        # S3 y S4: cat /var/www/html/.env muestra la credencial sintética.
        result = _call("cat /var/www/html/.env")
        self.assertIsNotNone(result)
        output = result.output
        self.assertIn("AWS_ACCESS_KEY_ID", output)
        self.assertIn("CANARY", output)
        access_key = _access_key()
        self.assertIn(access_key, output)
        self.assertIn(_POSTGRES_URI, output)
        self.assertEqual(result.token_type, "AWS_IAM_CREDENTIAL")
        self.assertEqual(result.token_identifier, access_key)
        self.assertEqual(result.destination_asset, "/var/www/html/.env")

    def test_dotenv_match_is_case_insensitive(self) -> None:
        result = _call('CAT "/VAR/WWW/HTML/.ENV"')
        self.assertIsNotNone(result)
        self.assertIn(_access_key(), result.output)
        self.assertEqual(result.destination_asset, "/var/www/html/.env")

    def test_aws_credentials_include_key_canary_and_postgres(self) -> None:
        result = _call("cat ~/.aws/credentials")
        self.assertIsNotNone(result)
        self.assertIn("AWS_ACCESS_KEY_ID", result.output)
        self.assertIn("CANARY", result.output)
        self.assertIn(_access_key(), result.output)
        self.assertIn(_POSTGRES_URI, result.output)
        self.assertEqual(result.token_type, "AWS_IAM_CREDENTIAL")
        self.assertEqual(result.token_identifier, _access_key())
        self.assertEqual(result.destination_asset, "~/.aws/credentials")

    def test_access_key_follows_the_attacker_ip(self) -> None:
        first = _call("cat /var/www/html/.env")
        second = _call("cat /var/www/html/.env", attacker_ip="198.51.100.20")
        self.assertEqual(first.token_identifier, _access_key())
        self.assertEqual(second.token_identifier, _access_key("198.51.100.20"))
        self.assertNotEqual(first.token_identifier, second.token_identifier)

    def test_whoami_returns_none(self) -> None:
        self.assertIsNone(_call("whoami"))

    def test_history_contains_the_ssh_line_verbatim(self) -> None:
        for command in ("history", "HISTORY"):
            with self.subTest(command=command):
                result = _call(command)
                self.assertIsNotNone(result)
                self.assertIn(_SSH_LINE, result.output)
                self.assertEqual(result.output.strip(), _SSH_LINE)
                self.assertEqual(result.output.strip().splitlines(), [_SSH_LINE])
                self.assertEqual(result.token_type, "BASH_HISTORY")
                self.assertEqual(result.destination_asset, "history")

    def test_bash_history_read_contains_the_same_ssh_line(self) -> None:
        result = _call("cat ~/.bash_history")
        self.assertIsNotNone(result)
        self.assertEqual(result.output.strip(), _SSH_LINE)
        self.assertEqual(result.token_type, "BASH_HISTORY")
        self.assertEqual(result.destination_asset, "~/.bash_history")

    def test_hosts_contains_vault_canary_domain(self) -> None:
        result = _call("cat /etc/hosts")
        self.assertIsNotNone(result)
        self.assertIn(_DNS_NAME, result.output)
        self.assertEqual(result.token_type, "DNS_CANARY")
        self.assertEqual(result.token_identifier, _DNS_NAME)
        self.assertEqual(result.destination_asset, "/etc/hosts")

    def test_mysql_client_section_has_replica_password(self) -> None:
        result = _call("cat /etc/mysql/my.cnf")
        self.assertIsNotNone(result)
        self.assertIn("[client]", result.output)
        self.assertIn(_REPLICA_PASSWORD, result.output)
        self.assertEqual(result.token_type, "DB_CONFIG")
        self.assertEqual(result.token_identifier, _REPLICA_PASSWORD)
        self.assertEqual(result.destination_asset, "/etc/mysql/my.cnf")

    def test_env_command_contains_access_key_and_canary(self) -> None:
        for command in ("env", "ENV"):
            with self.subTest(command=command):
                result = _call(command)
                self.assertIsNotNone(result)
                self.assertIn("AWS_ACCESS_KEY_ID", result.output)
                self.assertIn("CANARY", result.output)
                self.assertIn(_access_key(), result.output)
                self.assertEqual(result.token_type, "AWS_IAM_CREDENTIAL")
                self.assertEqual(result.token_identifier, _access_key())
                self.assertEqual(result.destination_asset, "env")

    def test_env_must_be_the_first_token(self) -> None:
        self.assertIsNone(_call("echo env"))
        self.assertIsNone(_call("grep env /etc/passwd"))

    def test_cat_id_rsa_returns_2048_bit_private_key(self) -> None:
        # destination_asset is the path argument as written when its final
        # component is id_rsa. whoami is not a read, so it stays unmatched.
        home = _call("cat ~/.ssh/id_rsa")
        root = _call("cat /root/.ssh/id_rsa")
        self.assertIsNone(_call("whoami"))
        self.assertIsNotNone(home)
        self.assertIsNotNone(root)
        for result, path in ((home, "~/.ssh/id_rsa"), (root, "/root/.ssh/id_rsa")):
            with self.subTest(path=path):
                self.assertEqual(result.token_type, "SSH_PRIVATE_KEY")
                self.assertEqual(result.token_identifier, "id_rsa")
                self.assertEqual(result.destination_asset, path)
                self.assertTrue(result.output.endswith("\n"))
                key = serialization.load_pem_private_key(result.output.encode(), password=None)
                self.assertIsInstance(key, rsa.RSAPrivateKey)
                self.assertEqual(key.key_size, 2048)
        self.assertNotEqual(home.output, root.output)


if __name__ == "__main__":
    unittest.main()
