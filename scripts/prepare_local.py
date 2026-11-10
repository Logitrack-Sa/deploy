"""Genera configuración privada reproducible sin reemplazar claves ni volúmenes existentes."""
import argparse
import getpass
import os
from pathlib import Path
import secrets
import shutil
import subprocess

DEPLOY = Path(__file__).resolve().parents[1]

def prepare(directory):
    root = Path(directory).resolve()
    env = root / "runtime.env"
    if env.exists():
        print(f"Se conserva el entorno existente: {env}")
        return
    root.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(["icacls", str(root), "/inheritance:r", "/grant:r",
                        getpass.getuser() + ":(OI)(CI)F", "*S-1-5-18:(OI)(CI)F"], check=True, capture_output=True)
    else:
        root.chmod(0o700)
    certs = root / "certs"
    certs.mkdir(exist_ok=True)
    certs.chmod(0o755)
    if any(certs.iterdir()):
        raise ValueError("La carpeta de certificados no está vacía; elegir otro directorio.")
    openssl = shutil.which("openssl")
    if not openssl and os.name == "nt":
        candidate = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/usr/bin/openssl.exe"
        if candidate.exists():
            openssl = str(candidate)
    if not openssl:
        raise RuntimeError("Instalar OpenSSL y agregarlo al PATH.")
    private, public = certs / "private.pem", certs / "public.pem"
    subprocess.run([openssl, "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(private)], check=True, capture_output=True)
    subprocess.run([openssl, "pkey", "-in", str(private), "-pubout", "-out", str(public)], check=True, capture_output=True)
    # Docker monta solo certs en modo lectura. El directorio padre sigue siendo privado.
    for path in (private, public):
        path.chmod(0o444)
    values = dict(line.split("=", 1) for line in (DEPLOY / ".env.example").read_text(encoding="utf-8").splitlines()
                  if line.strip() and not line.startswith("#"))
    for name in ("DB_ROOT_PASSWORD", "SECURITY_DB_PASSWORD", "COURIER_DB_PASSWORD", "SHIPMENT_DB_PASSWORD",
                 "PAYMENT_DB_PASSWORD", "SECURITY_ADMIN_PASSWORD", "RABBITMQ_DEFAULT_PASS", "GRAFANA_ADMIN_PASSWORD"):
        values[name] = secrets.token_hex(24)
    values["JWT_CERTS_DIRECTORY"] = os.path.relpath(certs, DEPLOY).replace(os.sep, "/")
    values["JWT_KEY_ID"] = "logitrack-local-" + secrets.token_hex(6)
    with env.open("x", encoding="utf-8") as output:
        output.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
    env.chmod(0o600)
    print(f"Entorno privado preparado en {root}. No publicar runtime.env ni los certificados.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="target/local")
    prepare(parser.parse_args().directory)
