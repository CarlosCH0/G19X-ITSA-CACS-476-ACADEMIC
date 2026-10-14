# -*- coding: utf-8 -*-
"""Pruebas MVP de CRUD: colaboradores, usuarios, indicadores y mediciones."""
from tests.conftest import headers


def test_crear_listar_actualizar_desactivar(client, tokens):
    auth = headers(tokens["gestor"])

    r = client.post("/api/colaboradores", json={
        "codigo": "MVP-001", "nombre": "Colaborador MVP",
        "area": "Tecnología", "puesto": "Desarrollador",
    }, headers=auth)
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    r = client.get("/api/colaboradores", params={"q": "MVP-001"}, headers=auth)
    assert r.status_code == 200 and r.json()["total"] == 1

    r = client.put(f"/api/colaboradores/{cid}", json={"puesto": "Senior"}, headers=auth)
    assert r.status_code == 200 and r.json()["puesto"] == "Senior"

    r = client.delete(f"/api/colaboradores/{cid}", headers=auth)
    assert r.status_code == 200
    r = client.get("/api/colaboradores", params={"incluir_inactivos": "true"}, headers=auth)
    assert any(c["codigo"] == "MVP-001" and not c["estado"] for c in r.json()["items"])


def test_crear_usuario_nuevo_como_admin(client, tokens):
    r = client.post("/api/usuarios", json={
        "nombre": "Usuario MVP", "correo": "mvp@develop.com.mx",
        "password": "Clave12345!", "rol_id": 4,
    }, headers=headers(tokens["admin"]))
    assert r.status_code == 201, r.text

    # Correo duplicado → 409
    r2 = client.post("/api/usuarios", json={
        "nombre": "Otro", "correo": "mvp@develop.com.mx",
        "password": "Clave12345!", "rol_id": 4,
    }, headers=headers(tokens["admin"]))
    assert r2.status_code == 409


def test_indicadores_crud_y_mediciones(client, tokens):
    auth = headers(tokens["gestor"])

    r = client.get("/api/indicadores", headers=headers(tokens["consulta"]))
    assert r.status_code == 200
    indicadores = r.json()
    assert len(indicadores) >= 10
    por_codigo = {i["codigo"]: i["id"] for i in indicadores}

    # Carga bulk de mediciones (RF-04) con upsert RN-01
    colabs = client.get("/api/colaboradores?q=COL-002", headers=auth).json()["items"]
    cid = colabs[0]["id"]
    r = client.post("/api/indicadores/mediciones", json={
        "colaborador_id": cid, "periodo": "2026-MVP",
        "mediciones": [
            {"indicador_id": por_codigo["LIDERAZGO"], "valor": 88.5, "validez": "valida"},
            {"indicador_id": por_codigo["COMUNICACION"], "valor": 75.0, "validez": "pendiente"},
        ],
    }, headers=auth)
    assert r.status_code == 201, r.text

    r = client.get("/api/indicadores/mediciones",
                   params={"colaborador_id": cid, "periodo": "2026-MVP"}, headers=auth)
    assert r.status_code == 200 and len(r.json()) == 2

    # Recargar el mismo indicador hace upsert y regresa a PENDIENTE (RN-01)
    r = client.post("/api/indicadores/mediciones", json={
        "colaborador_id": cid, "periodo": "2026-MVP",
        "mediciones": [{"indicador_id": por_codigo["LIDERAZGO"], "valor": 90.0, "validez": "valida"}],
    }, headers=auth)
    assert r.status_code == 201
    r = client.get("/api/indicadores/mediciones",
                   params={"colaborador_id": cid, "periodo": "2026-MVP"}, headers=auth)
    lid = [m for m in r.json() if m["indicador_codigo"] == "LIDERAZGO"]
    assert len(lid) == 1 and lid[0]["valor"] == 90.0
