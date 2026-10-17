# -*- coding: utf-8 -*-
"""Pruebas de autenticación, RBAC y auditoría (RF-01, RF-02, RF-15, RNF-01/02)."""


def test_salud(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["version_modelo"] == "reglas-v1"


def test_login_correcto_devuelve_token_y_permisos(client):
    r = client.post(
        "/api/auth/login",
        json={"correo": "admin@develop.com.mx", "password": "Admin123!"},
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"]["rol"] == "ADMINISTRADOR"
    assert "usuarios.gestionar" in cuerpo["usuario"]["permisos"]


def test_login_password_incorrecta(client):
    r = client.post(
        "/api/auth/login",
        json={"correo": "admin@develop.com.mx", "password": "incorrecta"},
    )
    assert r.status_code == 401


def test_sin_token_es_401(client):
    r = client.get("/api/colaboradores")
    assert r.status_code == 401


def test_rol_consulta_no_puede_crear_colaboradores(client, tokens):
    r = client.post(
        "/api/colaboradores",
        json={"codigo": "COL-999", "nombre": "Prueba", "area": "TI", "puesto": "X"},
        headers={"Authorization": f"Bearer {tokens['consulta']}"},
    )
    assert r.status_code == 403


def test_rol_consulta_no_ve_auditoria(client, tokens):
    r = client.get(
        "/api/auditoria", headers={"Authorization": f"Bearer {tokens['consulta']}"}
    )
    assert r.status_code == 403


def test_rol_evaluador_no_gestiona_usuarios(client, tokens):
    r = client.get(
        "/api/usuarios", headers={"Authorization": f"Bearer {tokens['evaluador']}"}
    )
    assert r.status_code == 403


def test_me_devuelve_usuario(client, tokens):
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['gestor']}"})
    assert r.status_code == 200
    assert r.json()["correo"] == "gestor@develop.com.mx"


def test_auditoria_registra_eventos(client, tokens):
    r = client.get("/api/auditoria", headers={"Authorization": f"Bearer {tokens['admin']}"})
    assert r.status_code == 200
    acciones = {i["accion"] for i in r.json()["items"]}
    assert "auth.login" in acciones
    assert "auth.login_fallido" in acciones
