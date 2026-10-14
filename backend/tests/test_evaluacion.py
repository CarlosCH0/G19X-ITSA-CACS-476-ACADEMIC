# -*- coding: utf-8 -*-
"""Pruebas MVP del pipeline de evaluación, configuración y revisión humana."""
from tests.conftest import headers


def test_configuracion_nueva_version_y_umbral(client, tokens):
    auth = headers(tokens["gestor"])
    r = client.get("/api/configuracion/activa", headers=auth)
    assert r.status_code == 200 and r.json()["activa"] is True

    r = client.post("/api/configuracion", json={
        "nombre": "MVP v2",
        "pesos": {"LIDERAZGO": 0.6, "DESEMPENO_GLOBAL": 0.4},
        "umbral_hipo": 70, "activar": True,
    }, headers=auth)
    assert r.status_code == 201, r.text
    v2 = r.json()
    assert v2["activa"] is True and v2["umbral_hipo"] == 70

    # La versión 1 dejó de estar activa (RN-03: una sola activa)
    r = client.get("/api/configuracion", headers=auth)
    activas = [c for c in r.json() if c["activa"]]
    assert len(activas) == 1 and activas[0]["version"] == v2["version"]

    # Pesos con indicador inexistente → 422
    r = client.post("/api/configuracion", json={
        "nombre": "Mala", "pesos": {"NO_EXISTE": 1.0}, "umbral_hipo": 50,
    }, headers=auth)
    assert r.status_code == 422


def test_ejecutar_evaluacion_periodo(client, tokens):
    r = client.post("/api/evaluaciones/ejecutar", json={"periodo": "2026-S1"},
                    headers=headers(tokens["gestor"]))
    assert r.status_code == 200, r.text
    resumen = r.json()
    assert resumen["total_evaluados"] >= 12
    assert resumen["total_evaluados"] == resumen["completos"] + resumen["incompletos"]
    assert resumen["configuracion_version"] >= 1
    # COL-012 tiene datos insuficientes en 2026-S1 (RN-02)
    assert resumen["incompletos"] >= 1


def test_evaluacion_con_configuracion_inexistente(client, tokens):
    r = client.post("/api/evaluaciones/ejecutar",
                    json={"periodo": "2026-S1", "configuracion_id": 99999},
                    headers=headers(tokens["gestor"]))
    assert r.status_code == 422


def test_evaluaciones_listado_y_detalle(client, tokens):
    auth = headers(tokens["consulta"])
    r = client.get("/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth)
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    hipo = [e for e in items if e["clasificacion"] == "alto_potencial"]
    assert hipo, "Debe existir al menos un HiPo en los datos demo"

    ev = (hipo or items)[0]
    r = client.get(f"/api/evaluaciones/{ev['id']}", headers=auth)
    assert r.status_code == 200
    detalle = r.json()
    assert detalle["resultado"]["factores"], "Trazabilidad de factores (RF-09)"
    assert detalle["version_modelo"]


def test_reejecucion_conserva_historico(client, tokens):
    auth = headers(tokens["gestor"])
    antes = client.get("/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth).json()["total"]
    r = client.post("/api/evaluaciones/ejecutar", json={"periodo": "2026-S1"}, headers=auth)
    assert r.status_code == 200
    despues = client.get("/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth).json()["total"]
    assert despues > antes, "RN-05: el histórico no se sobrescribe"


def test_revision_humana_y_observaciones(client, tokens):
    auth = headers(tokens["evaluador"])
    lista = client.get("/api/evaluaciones", params={"periodo": "2026-S1", "tamanio": 5},
                       headers=auth).json()["items"]
    ev = lista[0]
    res_id = client.get(f"/api/evaluaciones/{ev['id']}", headers=auth).json()["resultado"]["id"]

    r = client.post(f"/api/revisiones/resultados/{res_id}",
                    json={"estado": "confirmado", "comentario": "Validado en comité"},
                    headers=auth)
    assert r.status_code == 201 and r.json()["estado"] == "confirmado"

    r = client.post(f"/api/evaluaciones/{ev['id']}/observaciones",
                    json={"texto": "Observación de prueba MVP"}, headers=auth)
    assert r.status_code == 201
