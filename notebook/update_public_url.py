"""Actualiza la URL temporal de esta instalación sin reconstruir el frontend."""
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

root = Path(__file__).resolve().parent
url = subprocess.check_output(["vps-url"], text=True).strip().rstrip("/")
parsed = urlsplit(url)
if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".trycloudflare.com") or parsed.username or parsed.port or parsed.query or parsed.fragment or parsed.path:
    raise SystemExit("vps-url no devolvió un enlace HTTPS de Quick Tunnel válido")

path = root / ".env"
lines = path.read_text().splitlines()
values = dict(line.split("=", 1) for line in lines if line and not line.startswith("#"))
changes = {"LOGITRACK_PUBLIC_URL": url + "/logitrack",
           "CORS_ALLOWED_ORIGINS": url + ",http://192.168.0.103"}
if all(values.get(key) == value for key, value in changes.items()):
    print("La URL pública ya está actualizada")
else:
    backup = root / "backups" / "env-before-url-change"
    backup.touch(mode=0o600)
    backup.write_bytes(path.read_bytes())
    path.write_text("\n".join(line for line in lines if line.split("=", 1)[0] not in changes)
                    + "\n" + "\n".join(f"{key}={value}" for key, value in changes.items()) + "\n")
    path.chmod(0o600)
    subprocess.run(["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "240",
                    "security-service", "api-gateway", "frontend"], cwd=root, check=True)
    print("URL pública y orígenes permitidos actualizados")
