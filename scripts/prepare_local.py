"""Prepara una instalación de desarrollo aislada, sin reemplazar claves ni datos previos."""
import argparse
from pathlib import Path
import secrets
import shutil
import subprocess


def prepare(directory):
    root = Path(directory).resolve()
    env = root / "runtime.env"
    if env.exists():
        print(f"Se conserva el entorno existente: {env}")
        return
    root.mkdir(parents=True, exist_ok=True)
    certs = root / "certs"
    certs.mkdir(exist_ok=True)
    if any(certs.iterdir()):
        raise ValueError("La carpeta de certificados no está vacía; elegir otro directorio.")
    openssl = shutil.which("openssl") or r"C:\Program Files\Git\usr\bin\openssl.exe"
    private, public = certs / "private.pem", certs / "public.pem"
    subprocess.run([openssl, "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(private)], check=True, capture_output=True)
    subprocess.run([openssl, "pkey", "-in", str(private), "-pubout", "-out", str(public)], check=True, capture_output=True)
    for path in (private, public):
        path.chmod(0o444)
    values = {
        "DB_ROOT_PASSWORD": secrets.token_hex(24),
        "JWT_CERTS_DIRECTORY": certs.as_posix(),
        "JWT_KEY_ID": "sprint4-local-" + secrets.token_hex(6),
        "JWT_ISSUER": "https://security-service",
        "JWT_AUDIENCES": "security-service,courier-service,shipment-service,chatbot-service",
        "SECURITY_ADMIN_ENABLED": "true",
        "SECURITY_ADMIN_USERNAME": "local-admin",
        "SECURITY_ADMIN_EMAIL": "local-admin@example.test",
        "SECURITY_ADMIN_PASSWORD": secrets.token_hex(20),
        "MYSQL_VOLUME_NAME": "logitrack_sprint4_local_mysql",
        "LOGITRACK_NETWORK_NAME": "logitrack_sprint4_local_network",
        "HOST_CONFIG_PORT": "9088", "HOST_EUREKA_PORT": "9065",
        "HOST_GATEWAY_PORT": "8086", "HOST_FRONTEND_PORT": "3000",
        "HOST_MYSQL_PORT": "3308", "HOST_REDIS_PORT": "6380",
        "HOST_RABBITMQ_AMQP_PORT": "5673", "HOST_RABBITMQ_MGMT_PORT": "15673",
        "FRONTEND_API_GATEWAY_URL": "http://localhost:8086",
        "FRONTEND_COURIER_STATUS_MODEL": "legacy",
        "FRONTEND_CUSTOMER_CANCELLATION_ENABLED": "false",
        "RABBITMQ_DEFAULT_USER": "local-app",
        "RABBITMQ_DEFAULT_PASS": secrets.token_hex(20),
        "GRAFANA_ADMIN_PASSWORD": secrets.token_hex(20),
        "GMAIL_SMTP_USERNAME": "", "GMAIL_SMTP_APP_PASSWORD": "",
        "AI_API_KEY": "", "AI_MODEL": "",
    }
    with env.open("x", encoding="utf-8") as file:
        file.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
    env.chmod(0o600)
    print(f"Entorno local preparado en {root}. No compartir runtime.env ni private.pem.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="target/sprint4")
    prepare(parser.parse_args().directory)
