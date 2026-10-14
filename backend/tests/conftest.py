# -*- coding: utf-8 -*-
"""Configuración de pruebas MVP: BD SQLite aislada y clientes autenticados."""
import os

# Variables de entorno ANTES de importar la aplicación.
os.environ["DATABASE_URL"] = "sqlite:///./test_mvp.db"
os.environ["SEED_DEMO_DATA"] = "true"

for _db in ("test_mvp.db",):
    if os.path.exists(_db):
        os.remove(_db)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

CREDENCIALES = {
    "admin": ("admin@develop.com.mx", "Admin123!"),
    "gestor": ("gestor@develop.com.mx", "Gestor123!"),
    "evaluador": ("evaluador@develop.com.mx", "Evaluador123!"),
    "consulta": ("consulta@develop.com.mx", "Consulta123!"),
}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def tokens(client):
    """Tokens JWT por rol (RF-01)."""
    resultado = {}
    for rol, (correo, password) in CREDENCIALES.items():
        r = client.post("/api/auth/login", json={"correo": correo, "password": password})
        assert r.status_code == 200, f"login {rol}: {r.text}"
        resultado[rol] = r.json()["access_token"]
    return resultado


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
