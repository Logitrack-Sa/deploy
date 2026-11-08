"""Prepara imágenes y configuración para la notebook, sin usar un registry ni publicar Git."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import tarfile
from urllib.parse import urlsplit

DEPLOY = Path(__file__).resolve().parents[1]
WORKSPACE = DEPLOY.parent
JAVA_PORTS = {"config-server": 8888, "eureka-server": 8065, "security-service": 8083,
              "courier-service": 8082, "shipment-service": 8081, "api-gateway": 8080, "chatbot-service": 8084}
MEMORY_LIMITS = {"mysql": "1G", "security-service": "768M", "shipment-service": "768M",
                 "courier-service": "512M", "api-gateway": "512M", "config-server": "384M",
                 "eureka-server": "384M"}


def run(*args):
    return subprocess.check_output(args, text=True, encoding="utf-8").strip()


def prepare(directory, public_url):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError('La carpeta de entrega ya contiene archivos; elegir otra.')
    env = dict(line.split("=", 1) for line in (DEPLOY / "target/sprint4/runtime.env").read_text().splitlines() if line and not line.startswith("#"))
    env.pop("JWT_CERTS_DIRECTORY", None)
    config = json.loads(run("docker", "compose", "--env-file", str(DEPLOY / "target/sprint4/runtime.env"),
                            "-f", str(DEPLOY / "docker-compose.yml"), "-f", str(DEPLOY / "docker-compose.local.yml"),
                            "-p", "logitrack-sprint4-local", "config", "--format", "json"))
    project = {"name": "logitrack-notebook", "services": {}, "volumes": {},
               "networks": {"app": {}, "proxy": {"external": True, "name": "proxy"}}}
    date = datetime.now().strftime("%Y%m%d")
    images, manifest = [], {}
    env.update({"LOGITRACK_PUBLIC_URL": public_url.rstrip("/") + "/logitrack",
                "HOST_GATEWAY_PORT": "18080", "HOST_MAILPIT_PORT": "18025"})
    parsed_url = urlsplit(public_url)
    env["CORS_ALLOWED_ORIGINS"] = f"{parsed_url.scheme}://{parsed_url.netloc},http://192.168.0.103"
    for name in ("SECURITY_DB_PASSWORD", "COURIER_DB_PASSWORD", "SHIPMENT_DB_PASSWORD"):
        env[name] = secrets.token_hex(24)
    secret_names = {"MYSQL_ROOT_PASSWORD": "DB_ROOT_PASSWORD", "DB_PASSWORD": "DB_ROOT_PASSWORD",
                    "SECURITY_ADMIN_PASSWORD": "SECURITY_ADMIN_PASSWORD", "SECURITY_ADMIN_EMAIL": "SECURITY_ADMIN_EMAIL",
                    "SECURITY_ADMIN_USERNAME": "SECURITY_ADMIN_USERNAME", "JWT_KEY_ID": "JWT_KEY_ID",
                    "RABBITMQ_DEFAULT_PASS": "RABBITMQ_DEFAULT_PASS", "SPRING_RABBITMQ_PASSWORD": "RABBITMQ_DEFAULT_PASS",
                    "GF_SECURITY_ADMIN_PASSWORD": "GRAFANA_ADMIN_PASSWORD"}
    private_ports = {"frontend": (13000, 3000), "api-gateway": (18080, 8080), "eureka-server": (18065, 8065),
                     "config-server": (18888, 8888), "grafana": (13001, 3000), "prometheus": (19090, 9090),
                     "rabbitmq": (15672, 15672), "mailpit": (18025, 8025)}
    for name, source in config["services"].items():
        if name == "chatbot-service":
            continue  # No se configura un modelo ni una clave ficticia.
        service = dict(source)
        if 'deploy' in service:
            service['deploy'].pop('placement', None)
        image = "logitrack-frontend:notebook" if name == "frontend" else service.get("image", f"logitrack-sprint4-local-{name}:latest")
        image_id = run("docker", "image", "inspect", image, "--format", "{{.Id}}")
        tag = f"logitrack-notebook-{name}:{date}"
        subprocess.run(["docker", "tag", image_id, tag], check=True)
        images.append(tag)
        manifest[name] = {"image": tag, "id": image_id}
        for key in ("build", "container_name", "ports", "profiles", "volumes", "networks"):
            service.pop(key, None)
        service["image"], service["networks"] = tag, {"app": None}
        service["restart"] = "unless-stopped"
        if name in MEMORY_LIMITS:
            service.setdefault("deploy", {}).setdefault("resources", {}).setdefault("limits", {})["memory"] = MEMORY_LIMITS[name]
        environment = dict(service.get("environment", {}))
        for key, variable in secret_names.items():
            if key in environment:
                environment[key] = "${" + variable + "}"
        if name in ("security-service", "courier-service", "shipment-service"):
            prefix = name.split("-")[0].upper()
            environment["DB_USERNAME"] = name.split("-")[0] + "_app"
            environment["DB_USER"] = environment["DB_USERNAME"]
            environment["DB_PASSWORD"] = "${" + prefix + "_DB_PASSWORD}"
        service["environment"] = environment
        if name in private_ports:
            host, internal = private_ports[name]
            service["ports"] = [f"127.0.0.1:{host}:{internal}"]
        if name in JAVA_PORTS:
            service["volumes"] = ["./healthcheck/http-health.sh:/healthcheck/http-health.sh:ro"]
            service["healthcheck"] = {"test": ["CMD", "bash", "/healthcheck/http-health.sh", str(JAVA_PORTS[name])],
                                      "interval": "15s", "timeout": "4s", "start_period": "90s", "retries": 20}
            if name != "config-server":
                service.setdefault("depends_on", {})["config-server"] = {"condition": "service_healthy"}
        if name == "config-server":
            service["volumes"].append("./config:/config:ro")
        if name in ("security-service", "courier-service", "shipment-service", "api-gateway"):
            service["volumes"].append("./secrets:/secrets:ro")
        if name == "security-service":
            environment["FRONTEND_URL"] = "${LOGITRACK_PUBLIC_URL}"
        if name == "api-gateway":
            environment["CORS_ALLOWED_ORIGINS"] = "${CORS_ALLOWED_ORIGINS}"
        if name in ("frontend", "api-gateway"):
            alias = "logitrack-web" if name == "frontend" else "logitrack-gateway"
            service["networks"]["proxy"] = {"aliases": [alias]}
        if name == "frontend":
            environment["APP_BASE_PATH"] = "/logitrack"
            service.setdefault("depends_on", {})["api-gateway"] = {"condition": "service_healthy"}
        volume = {"mysql": ("mysql_data", "/var/lib/mysql"), "redis": ("redis_data", "/data"),
                  "rabbitmq": ("rabbitmq_data", "/var/lib/rabbitmq"), "grafana": ("grafana_data", "/var/lib/grafana"),
                  "prometheus": ("prometheus_data", "/prometheus"), "mailpit": ("mailpit_data", "/data")}.get(name)
        if volume:
            project["volumes"][volume[0]] = {}
            service.setdefault("volumes", []).append(volume[0] + ":" + volume[1])
        if name == "mysql":
            service["volumes"].append("./mysql-init:/docker-entrypoint-initdb.d:ro")
            for key in ("SECURITY_DB_PASSWORD", "COURIER_DB_PASSWORD", "SHIPMENT_DB_PASSWORD"):
                environment[key] = "${" + key + "}"
        if name == "redis":
            service["command"] += ["--appendonly", "yes"]
        if name == "grafana":
            service["volumes"].append("./docker/grafana/provisioning:/etc/grafana/provisioning:ro")
        if name == "prometheus":
            service["volumes"].append("./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro")
        if name == "mailpit":
            environment["MP_DATABASE"] = "/data/mailpit.db"
        project["services"][name] = service
    for path in ("config", "secrets", "backups", "healthcheck", "mysql-init"):
        (root / path).mkdir()
    config_tar = root / "config.tar"
    subprocess.run(["git", "-C", str(WORKSPACE / "config-repo"), "archive", "--format=tar", "--output", str(config_tar), "HEAD"], check=True)
    with tarfile.open(config_tar) as archive:
        archive.extractall(root / "config", filter="data")
    config_tar.unlink()
    for name in ("private.pem", "public.pem"):
        shutil.copyfile(DEPLOY / "target/sprint4/certs" / name, root / "secrets" / name)
    shutil.copytree(DEPLOY / "docker/prometheus", root / "docker/prometheus")
    shutil.copytree(DEPLOY / "docker/grafana", root / "docker/grafana")
    # Crear solo los esquemas. Las cuentas del servidor usan contraseñas propias.
    (root / "mysql-init/01-databases.sql").write_text("\n".join(f"CREATE DATABASE IF NOT EXISTS `{db}`;" for db in ("security_db", "courier_db", "logitrack", "shipment_db")) + "\n")
    shutil.copyfile(DEPLOY / "notebook/02-users.sh", root / "mysql-init/02-users.sh")
    shutil.copyfile(DEPLOY / "notebook/http-health.sh", root / "healthcheck/http-health.sh")
    shutil.copyfile(DEPLOY / "notebook/logitrack.caddy", root / "logitrack.caddy")
    shutil.copyfile(DEPLOY / "scripts/verify_local.py", root / "verify.py")
    shutil.copyfile(DEPLOY / "notebook/backup.sh", root / "backup.sh")
    shutil.copyfile(DEPLOY / "notebook/update_public_url.py", root / "update_public_url.py")
    shutil.copyfile(DEPLOY / "docs/NOTEBOOK-SERVIDOR.md", root / "README.md")
    (root / "compose.yaml").write_text(json.dumps(project, indent=2), encoding="utf-8")
    (root / ".env").write_text("\n".join(f"{key}={value}" for key, value in env.items()) + "\n", encoding="utf-8")
    (root / "images.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (root / "sources.json").write_text((DEPLOY / "target/sprint4/sources.json").read_text(), encoding="utf-8")
    # Detectar secretos de runtime que se hayan incrustado accidentalmente en Compose.
    serialized = (root / "compose.yaml").read_text()
    for key, value in env.items():
        if len(value) > 15 and ("PASSWORD" in key or key.endswith("_PASS")) and value in serialized:
            raise ValueError("Una credencial quedó incrustada en compose.yaml")
    print(f"Configuración preparada: {root}", flush=True)
    print("Exportando imágenes locales comprimidas, sin publicar en Docker Hub…", flush=True)
    process = subprocess.Popen(["docker", "save", *images], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with gzip.open(root / "images.tar.gz", "wb", compresslevel=1) as output:
        shutil.copyfileobj(process.stdout, output, length=8 * 1024 * 1024)
    if process.wait() != 0:
        raise RuntimeError("No se pudieron exportar las imágenes Docker")
    print(f"Imágenes exportadas: {(root / 'images.tar.gz').stat().st_size} bytes", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--public-url", required=True)
    args = parser.parse_args()
    prepare(args.directory, args.public_url)
