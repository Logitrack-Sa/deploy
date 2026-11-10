"""Comprueba HTTP real con datos sintéticos. No imprime ni exporta tokens o claves."""
import argparse
from http.client import HTTPException
import json
from pathlib import Path
import re
import secrets
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def verify(directory, base_url=None):
    root = Path(directory).resolve()
    env_file = root / "runtime.env"
    if not env_file.exists():
        env_file = root / ".env"
    env = dict(line.split("=", 1) for line in env_file.read_text().splitlines() if line and not line.startswith("#"))
    private_base = "http://127.0.0.1:" + env.get("HOST_GATEWAY_PORT", "8080")
    base = base_url.rstrip("/") if base_url else private_base
    checks = []

    def call(method, path, body=None, token=None, expected=200, host=base):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        request = Request(host + path, data=data, headers=headers, method=method)
        try:
            response = urlopen(request, timeout=20)
        except HTTPError as error:
            response = error
        status = response.status if hasattr(response, "status") else response.code
        raw = response.read()
        value = json.loads(raw) if raw else None
        if status != expected:
            code = value.get("code", "") if isinstance(value, dict) else ""
            raise AssertionError(f"{method} {path.split('?')[0]}: {status}, esperado {expected}; {code}")
        checks.append({"method": method, "path": path.split("?")[0], "status": status})
        return value

    deadline = time.monotonic() + 300
    while True:
        try:
            call("GET", "/api/v1/auth/public-key", host=private_base)
            break
        except (AssertionError, URLError, TimeoutError, ValueError, HTTPException, ConnectionError):
            pass
        if time.monotonic() > deadline:
            raise TimeoutError("Gateway no quedó disponible en cinco minutos")
        time.sleep(2)

    admin = call("POST", "/api/v1/auth/login", {"email": env["SECURITY_ADMIN_EMAIL"], "password": env["SECURITY_ADMIN_PASSWORD"]})["accessToken"]
    profile = call("GET", "/api/v1/auth/me", token=admin)
    assert profile["emailVerified"] is True
    run = secrets.token_hex(6)
    customer = call("POST", "/api/v1/customers", {"name": "Prueba de integración " + run, "email": run + "@example.test", "phone": "123456"}, admin, 201)
    call("POST", "/api/v1/customers", {"name": "", "email": "incorrecto"}, admin, 400)
    call("GET", "/api/v1/customers?page=0&size=10", token=admin)
    call("GET", "/api/v1/customers/" + customer["id"], token=admin)
    courier = call("POST", "/api/v1/couriers", {"name": "Repartidor " + run, "dni": str(secrets.randbelow(90000000) + 10000000), "vehicleType": "MOTO"}, admin, 201)
    call("GET", "/api/v1/couriers?status=ACTIVO&page=0&size=10", token=admin)
    call("GET", "/api/v1/couriers/" + courier["id"], token=admin)
    for courier_status in ("INACTIVO", "ACTIVO"):
        assert call("PATCH", "/api/v1/couriers/" + courier["id"] + "/status", {"status": courier_status}, admin)["status"] == courier_status
    address = {"street": "Bolivia", "number": "1239", "city": "Jujuy", "postalCode": "4600"}
    shipment_body = {"customerId": customer["id"], "origin": address, "destination": address, "weightKg": 2.5, "widthCm": 30, "heightCm": 20, "lengthCm": 40}
    shipment = call("POST", "/api/v1/shipments", shipment_body, admin, 201)
    route = "/api/v1/shipments/" + shipment["id"]
    call("PUT", route + "/courier", {"courierId": courier["id"]}, admin)
    assert call("GET", route, token=admin)["courierId"] == courier["id"]
    call("GET", "/api/v1/shipments/tracking/" + shipment["trackingCode"], token=admin)
    call("GET", "/api/v1/shipments?status=PENDIENTE&page=0&size=10", token=admin)
    parallel_shipment = call("POST", "/api/v1/shipments", shipment_body, admin, 201)
    parallel_route = "/api/v1/shipments/" + parallel_shipment["id"]
    call("PUT", parallel_route + "/courier", {"courierId": courier["id"]}, admin)
    call("PATCH", route + "/status", {"status": "EN_RUTA", "observation": "Prueba local"}, admin)
    call("PATCH", parallel_route + "/status", {"status": "EN_RUTA"}, admin)

    def wait_availability(expected):
        deadline = time.monotonic() + 45
        while True:
            availability = call("GET", "/api/v1/couriers/" + courier["id"] + "/availability", token=admin)
            assert availability["status"] == "ACTIVO"
            if availability["available"] is expected:
                return
            if time.monotonic() >= deadline:
                raise TimeoutError("RabbitMQ no actualizó la disponibilidad del repartidor")
            time.sleep(1)

    wait_availability(False)
    call("PATCH", route + "/status", {"status": "ENTREGADO"}, admin)
    wait_availability(False)
    call("PATCH", parallel_route + "/status", {"status": "ENTREGADO"}, admin)
    wait_availability(True)
    call("PATCH", route + "/status", {"status": "EN_RUTA"}, admin, 422)
    call("GET", route + "/history", token=admin)
    cancelled = call("POST", "/api/v1/shipments", shipment_body, admin, 201)
    cancel_route = "/api/v1/shipments/" + cancelled["id"] + "/cancellation"
    assert call("POST", cancel_route, token=admin)["status"] == "CANCELADO"
    call("POST", cancel_route, token=admin, expected=422)
    call("GET", "/api/v1/shipments", expected=401)

    email, password = f"register-{run}@example.test", secrets.token_hex(20)
    registered = call("POST", "/api/v1/auth/register", {"email": email, "password": password}, expected=201)
    call("POST", "/api/v1/auth/login", {"email": email, "password": password}, expected=401)
    mail_host = "http://127.0.0.1:" + env.get("HOST_MAILPIT_PORT", "8025")
    token = None
    for _ in range(30):
        messages = call("GET", "/api/v1/messages", host=mail_host)
        for message in messages.get("messages", []):
            if any(recipient.get("Address") == email for recipient in message.get("To", [])):
                detail = call("GET", "/api/v1/message/" + message["ID"], host=mail_host)
                match = re.search(r"/verify-email\?token=([0-9a-f-]{36})", detail.get("Text", ""))
                if match:
                    token = match[1]
                    break
        if token:
            break
        time.sleep(1)
    assert token, "No se capturó el correo de verificación local"
    call("POST", "/api/v1/auth/verify-email?" + urlencode({"token": token}))
    call("POST", "/api/v1/auth/verify-email?" + urlencode({"token": token}), expected=404)
    client = call("POST", "/api/v1/auth/login", {"email": email, "password": password})["accessToken"]
    client_profile = call("GET", "/api/v1/auth/me", token=client)
    assert client_profile["customerId"], "El registro verificado debe vincular su propio cliente automáticamente"
    call("GET", route, token=client, expected=403)
    own_body = dict(shipment_body, customerId=client_profile["customerId"])
    own_shipment = call("POST", "/api/v1/shipments", own_body, client, 201)
    own_route = "/api/v1/shipments/" + own_shipment["id"]
    call("GET", own_route, token=client)
    assert call("POST", own_route + "/cancellation", token=client)["status"] == "CANCELADO"
    call("POST", own_route + "/cancellation", token=client, expected=422)
    call("GET", "/api/v1/customers", token=client, expected=403)
    call("GET", "/api/v1/users", token=client, expected=403)
    call("POST", cancel_route, token=client, expected=403)
    report = {"passed": True, "requests": checks, "requestCount": len(checks), "mailDelivery": "SMTP local capturado en Mailpit, sin Gmail", "ai": "Pendiente de AI_API_KEY y AI_MODEL"}
    (root / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Verificación HTTP real aprobada: {len(checks)} solicitudes. Informe: {root / 'verification.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="target/local")
    parser.add_argument("--base-url", help="URL propia del Gateway, incluyendo el prefijo público si existe")
    args = parser.parse_args()
    verify(args.directory, args.base_url)
