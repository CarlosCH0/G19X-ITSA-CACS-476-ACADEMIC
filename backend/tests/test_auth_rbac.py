# -*- coding: utf-8 -*-
"""Pruebas MVP de autenticación, RBAC y auditoría (RF-01, RF-02, RF-15)."""
from tests.conftest import headers


def test_salud(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["version_modelo"]


def test_login_correcto_devuelve_token_y_permisos(client):
    r = client.post("/api/auth/login", json={
        "correo": "admin@develop.com.mx", "password": "Admin123!",
    })
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["access_token"]
    assert cuerpo["usuario"]["rol"] == "ADMINISTRADOR"
    assert "usuarios.gestionar" in cuerpo["usuario"]["permisos"]


def test_login_password_incorrecta(client):
    r = client.post("/api/auth/login", json={
        "correo": "admin@develop.com.mx", "password": "Incorrecta99!",
    })
    assert r.status_code == 401


def test_sin_token_es_401(client):
    assert client.get("/api/colaboradores").status_code == 401


def test_me_devuelve_usuario(client, tokens):
    r = client.get("/api/auth/me", headers=headers(tokens["gestor"]))
    assert r.status_code == 200
    assert r.json()["rol"] == "GESTOR_TALENTO"


def test_rol_consulta_no_puede_crear_colaboradores(client, tokens):
    r = client.post("/api/colaboradores", json={
        "codigo": "X-001", "nombre": "X", "area": "X", "puesto": "X",
    }, headers=headers(tokens["consulta"]))
    assert r.status_code == 403


def test_rol_consulta_no_ve_auditoria(client, tokens):
    assert client.get("/api/auditoria", headers=headers(tokens["consulta"])).status_code == 403


def test_auditoria_registra_eventos(client, tokens):
    r = client.get("/api/auditoria", params={"tamanio": 5}, headers=headers(tokens["admin"]))
    assert r.status_code == 200
    assert r.json()["total"] > 0
    acciones = {i["accion"] for i in r.json()["items"]}
    assert acciones, "Debe haber eventos registrados"
