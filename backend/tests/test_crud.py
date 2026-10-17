# -*- coding: utf-8 -*-
"""Pruebas de CRUD de colaboradores e indicadores (RF-03, RF-04, RN-01)."""
from tests.conftest import headers


def test_crear_listar_actualizar_desactivar(client, tokens):
    auth = headers(tokens["gestor"])

    r = client.post(
        "/api/colaboradores",
        json={
            "codigo": "COL-900",
            "nombre": "Colaborador De Prueba",
            "area": "Tecnología",
            "puesto": "QA",
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    # Un codigo duplicado debe responder 409.
    r2 = client.post(
        "/api/colaboradores",
        json={"codigo": "COL-900", "nombre": "Otro", "area": "TI"},
        headers=auth,
    )
    assert r2.status_code == 409

    # Se prueban la busqueda y los filtros (RF-11).
    r3 = client.get("/api/colaboradores", params={"q": "COL-900"}, headers=auth)
    assert r3.status_code == 200
    assert r3.json()["total"] == 1

    r4 = client.put(
        f"/api/colaboradores/{cid}",
        json={"puesto": "QA Senior"},
        headers=auth,
    )
    assert r4.status_code == 200
    assert r4.json()["puesto"] == "QA Senior"

    r5 = client.delete(f"/api/colaboradores/{cid}", headers=auth)
    assert r5.status_code == 200
    assert r5.json()["estado"] is False  # El registro se desactiva sin borrarlo.

    # El historial y el perfil siguen disponibles.
    r6 = client.get(f"/api/colaboradores/{cid}/perfil", headers=auth)
    assert r6.status_code == 200


def test_indicadores_crud_y_mediciones(client, tokens):
    auth = headers(tokens["gestor"])

    r = client.get("/api/indicadores", headers=headers(tokens["consulta"]))
    assert r.status_code == 200
    codigos = {i["codigo"] for i in r.json()}
    assert "DESEMPENO_GLOBAL" in codigos

    # Cargar mediciones bulk (2 indicadores) para COL-001 en periodo de prueba
    indicadores = {i["codigo"]: i["id"] for i in r.json()}
    r2 = client.post(
        "/api/indicadores/mediciones",
        json={
            "colaborador_id": 1,
            "periodo": "2026-TEST",
            "mediciones": [
                {"indicador_id": indicadores["DESEMPENO_GLOBAL"], "valor": 88.0},
                {"indicador_id": indicadores["LIDERAZGO"], "valor": 78.5, "validez": "valida"},
            ],
        },
        headers=auth,
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["cantidad"] == 2

    r3 = client.get(
        "/api/indicadores/mediciones", params={"colaborador_id": 1, "periodo": "2026-TEST"}, headers=auth
    )
    assert r3.status_code == 200
    assert len(r3.json()) == 2

    # La primera queda pendiente por defecto (RN-01), asi que se valida.
    pendiente = next(m for m in r3.json() if m["validez"] == "pendiente")
    r4 = client.patch(
        f"/api/indicadores/mediciones/{pendiente['id']}/validez",
        json={"validez": "valida", "comentario": "Verificado contra fuente"},
        headers=auth,
    )
    assert r4.status_code == 200

    # Periodos disponibles incluye el de prueba
    r5 = client.get("/api/indicadores/periodos", headers=auth)
    assert "2026-TEST" in r5.json()


def test_limites_de_valor_por_tipo_de_indicador(client, tokens):
    auth = headers(tokens["gestor"])
    indicadores = {
        item["codigo"]: item["id"]
        for item in client.get("/api/indicadores", headers=auth).json()
    }

    puntuacion_fuera_de_rango = client.post(
        "/api/indicadores/mediciones",
        json={
            "colaborador_id": 1,
            "periodo": "2026-RANGO",
            "mediciones": [
                {"indicador_id": indicadores["LIDERAZGO"], "valor": 101},
            ],
        },
        headers=auth,
    )
    assert puntuacion_fuera_de_rango.status_code == 422
    assert "entre 0 y 100" in puntuacion_fuera_de_rango.json()["detail"]

    cantidad_mayor_a_cien = client.post(
        "/api/indicadores/mediciones",
        json={
            "colaborador_id": 1,
            "periodo": "2026-RANGO",
            "mediciones": [
                {"indicador_id": indicadores["ANIOS_EXPERIENCIA"], "valor": 101},
            ],
        },
        headers=auth,
    )
    assert cantidad_mayor_a_cien.status_code == 201

    puntuacion_negativa = client.post(
        "/api/indicadores/mediciones",
        json={
            "colaborador_id": 1,
            "periodo": "2026-RANGO",
            "mediciones": [
                {"indicador_id": indicadores["DESEMPENO_GLOBAL"], "valor": -1},
            ],
        },
        headers=auth,
    )
    assert puntuacion_negativa.status_code == 422


def test_crear_usuario_nuevo_como_admin(client, tokens):
    r = client.get("/api/usuarios/roles", headers=headers(tokens["admin"]))
    assert r.status_code == 200
    rol_consulta = next(rol for rol in r.json() if rol["nombre"] == "CONSULTA")

    r2 = client.post(
        "/api/usuarios",
        json={
            "nombre": "Nuevo Analista",
            "correo": "analista@develop.com.mx",
            "password": "Analista123!",
            "rol_id": rol_consulta["id"],
        },
        headers=headers(tokens["admin"]),
    )
    assert r2.status_code == 201, r2.text

    # El usuario nuevo puede iniciar sesion.
    r3 = client.post(
        "/api/auth/login",
        json={"correo": "analista@develop.com.mx", "password": "Analista123!"},
    )
    assert r3.status_code == 200
