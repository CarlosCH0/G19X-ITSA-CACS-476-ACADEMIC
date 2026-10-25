# -*- coding: utf-8 -*-
"""Pruebas del módulo de planes de desarrollo y sucesión (liderazgo/desarrollo)."""
from tests.conftest import headers


def test_listar_planes_y_estadisticas_demo(client, tokens):
    auth = headers(tokens["gestor"])
    r = client.get("/api/planes", headers=auth)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] >= 3, "La semilla debe incluir planes de demostración"
    plan = cuerpo["items"][0]
    assert plan["colaborador_codigo"].startswith("COL-")
    assert 0 <= plan["progreso"] <= 100

    r2 = client.get("/api/planes/estadisticas", headers=auth)
    assert r2.status_code == 200
    stats = r2.json()
    assert stats["total"] == cuerpo["total"]
    assert sum(stats["por_estado"].values()) == stats["total"]


def test_crear_actualizar_plan_con_acciones(client, tokens):
    auth = headers(tokens["gestor"])

    # Colaborador COL-002 para el plan
    colabs = client.get("/api/colaboradores?q=COL-002", headers=auth).json()["items"]
    assert colabs, "Debe existir COL-002 en la semilla"

    r = client.post(
        "/api/planes",
        json={
            "colaborador_id": colabs[0]["id"],
            "titulo": "Plan de prueba QA",
            "objetivo": "Validar el flujo de planes",
            "foco": "liderazgo",
            "fecha_inicio": "2026-09-01",
            "fecha_fin": "2026-12-31",
            "acciones": [
                {"descripcion": "Acción uno", "fecha_limite": "2026-10-15"},
                {"descripcion": "Acción dos", "completada": True},
            ],
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    plan = r.json()
    assert plan["total_acciones"] == 2
    assert plan["acciones_completadas"] == 1
    assert plan["progreso"] == 50.0
    assert plan["estado"] == "en_progreso"  # avance parcial

    # Actualizar estado
    r2 = client.put(
        f"/api/planes/{plan['id']}", json={"estado": "cancelado"}, headers=auth
    )
    assert r2.status_code == 200
    assert r2.json()["estado"] == "cancelado"

    # Agregar una accion a un plan cerrado debe responder 422.
    r3 = client.post(
        f"/api/planes/{plan['id']}/acciones",
        json={"descripcion": "Acción tardía"},
        headers=auth,
    )
    assert r3.status_code == 422

    # Eliminar plan de prueba
    r4 = client.delete(f"/api/planes/{plan['id']}", headers=auth)
    assert r4.status_code == 204


def test_avance_se_recalcula_al_marcar_acciones(client, tokens):
    auth = headers(tokens["gestor"])
    planes = client.get(
        "/api/planes", params={"solo_abiertos": True}, headers=auth
    ).json()["items"]
    assert planes, "Debe haber planes abiertos de la semilla"
    plan_id = planes[0]["id"]

    detalle = client.get(f"/api/planes/{plan_id}", headers=auth).json()
    pendiente = next(a for a in detalle["acciones"] if not a["completada"])

    r = client.patch(
        f"/api/planes/acciones/{pendiente['id']}",
        json={"completada": True},
        headers=auth,
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["progreso"] == 100.0
    assert cuerpo["estado"] == "completado"  # El plan se cierra automaticamente.

    # Revertir para no afectar otras pruebas
    r2 = client.patch(
        f"/api/planes/acciones/{pendiente['id']}",
        json={"completada": False},
        headers=auth,
    )
    assert r2.status_code == 200
    assert r2.json()["estado"] in ("en_progreso", "planificado")


def test_permisos_planes_por_rol(client, tokens):
    # CONSULTA no tiene permiso de planes
    r = client.get("/api/planes", headers=headers(tokens["consulta"]))
    assert r.status_code == 403

    # EVALUADOR solo consulta, no gestiona
    r2 = client.get("/api/planes", headers=headers(tokens["evaluador"]))
    assert r2.status_code == 200
    r3 = client.post(
        "/api/planes",
        json={
            "colaborador_id": 1,
            "titulo": "Plan sin permiso",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-02-01",
        },
        headers=headers(tokens["evaluador"]),
    )
    assert r3.status_code == 403


def test_planes_del_colaborador(client, tokens):
    auth = headers(tokens["gestor"])
    planes = client.get("/api/planes", params={"q": "COL-001"}, headers=auth).json()
    assert planes["total"] >= 1
    cid = planes["items"][0]["colaborador_id"]
    r = client.get(f"/api/colaboradores/{cid}/planes", headers=auth)
    assert r.status_code == 200
    assert any(p["colaborador_id"] == cid for p in r.json())


def test_validaciones_de_negocio_planes(client, tokens):
    auth = headers(tokens["gestor"])
    # Fechas inconsistentes → 422 por el validador del esquema
    r = client.post(
        "/api/planes",
        json={
            "colaborador_id": 1,
            "titulo": "Fechas invertidas",
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2026-01-01",
        },
        headers=auth,
    )
    assert r.status_code == 422

    # Colaborador inexistente → 422 por regla de negocio
    r2 = client.post(
        "/api/planes",
        json={
            "colaborador_id": 99999,
            "titulo": "Plan fantasma",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-02-01",
        },
        headers=auth,
    )
    assert r2.status_code == 422

    # Detalle de plan inexistente → 404
    r3 = client.get("/api/planes/99999", headers=auth)
    assert r3.status_code == 404


def test_plan_sin_acciones_inicia_sin_progreso(client, tokens):
    auth = headers(tokens["gestor"])
    colaboradores = client.get(
        "/api/colaboradores?q=COL-002", headers=auth
    ).json()["items"]
    assert colaboradores

    respuesta = client.post(
        "/api/planes",
        json={
            "colaborador_id": colaboradores[0]["id"],
            "titulo": "Plan sin acciones",
            "fecha_inicio": "2026-09-01",
            "fecha_fin": "2026-12-31",
            "acciones": [],
        },
        headers=auth,
    )
    assert respuesta.status_code == 201, respuesta.text
    plan = respuesta.json()
    assert plan["total_acciones"] == 0
    assert plan["progreso"] == 0.0
    assert plan["estado"] == "planificado"

    eliminacion = client.delete(f"/api/planes/{plan['id']}", headers=auth)
    assert eliminacion.status_code == 204
