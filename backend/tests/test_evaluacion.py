# -*- coding: utf-8 -*-
"""Pruebas del pipeline de evaluación HiPo (RF-05..RF-09, RN-02..RN-06)."""
from tests.conftest import headers


def test_ejecutar_evaluacion_periodo(client, tokens):
    auth = headers(tokens["gestor"])
    r = client.post(
        "/api/evaluaciones/ejecutar",
        json={"periodo": "2026-S1"},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    resumen = r.json()
    assert resumen["periodo"] == "2026-S1"
    assert resumen["total_evaluados"] == 12
    assert resumen["completos"] + resumen["incompletos"] == 12
    # COL-012 tiene datos insuficientes (RN-02)
    assert resumen["incompletos"] >= 1
    assert resumen["por_clasificacion"].get("no_evaluable", 0) >= 1


def test_evaluaciones_listado_y_detalle(client, tokens):
    auth = headers(tokens["consulta"])
    r = client.get("/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 12

    ev = next(e for e in items if e["clasificacion"] == "alto_potencial")
    assert ev["puntuacion"] >= 75  # umbral v1

    r2 = client.get(f"/api/evaluaciones/{ev['id']}", headers=auth)
    assert r2.status_code == 200
    detalle = r2.json()
    assert detalle["resultado"]["factores"], "Debe incluir factores principales (RF-09)"
    assert detalle["resultado"]["explicacion_origen"] == "local_determinista"
    assert detalle["resultado"]["explicacion"]
    # Los factores aparecen ordenados de mayor a menor aporte.
    contribuciones = [f["contribucion"] for f in detalle["resultado"]["factores"]]
    assert contribuciones == sorted(contribuciones, reverse=True)


def test_reejecucion_conserva_historico(client, tokens):
    """RN-05/RF-17: re-ejecutar no sobrescribe, conserva por periodo."""
    auth = headers(tokens["evaluador"])
    r = client.get("/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth)
    antes = r.json()["total"]

    r2 = client.post("/api/evaluaciones/ejecutar", json={"periodo": "2026-S1"}, headers=auth)
    assert r2.status_code == 200

    r3 = client.get("/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth)
    assert r3.json()["total"] == antes + 12


def test_revision_humana_y_observaciones(client, tokens):
    auth = headers(tokens["evaluador"])
    r = client.get("/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth)
    ev = r.json()["items"][0]

    resultado_id = ev["id"]  # Cada resultado corresponde a una evaluacion.
    r2 = client.post(
        f"/api/revisiones/resultados/{resultado_id}",
        json={"estado": "confirmado", "comentario": "Validado con el líder de área"},
        headers=auth,
    )
    assert r2.status_code == 201, r2.text

    r3 = client.get(f"/api/evaluaciones/{ev['id']}", headers=auth)
    assert r3.json()["estado_revision"] == "confirmado"

    r4 = client.post(
        f"/api/evaluaciones/{ev['id']}/observaciones",
        json={"texto": "Se sugiere asignar mentoring ejecutivo el próximo periodo."},
        headers=auth,
    )
    assert r4.status_code == 201

    # La observacion tambien aparece en el perfil del colaborador (RF-10, RF-19).
    r5 = client.get(f"/api/colaboradores/{ev['colaborador_id']}/perfil", headers=auth)
    assert any("mentoring" in o["texto"] for o in r5.json()["observaciones"])


def test_configuracion_nueva_version_y_umbral(client, tokens):
    """RF-16/RN-03: el umbral es configurable y versionado."""
    auth = headers(tokens["gestor"])

    r = client.post(
        "/api/configuracion",
        json={
            "nombre": "Criterios HiPo v2 — umbral ajustado",
            "pesos": {"DESEMPENO_GLOBAL": 0.5, "LIDERAZGO": 0.3, "CUMPLIMIENTO_OBJETIVOS": 0.2},
            "umbral_hipo": 60,
            "cobertura_minima": 0.5,
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    v2 = r.json()
    assert v2["version"] == 2
    assert v2["activa"] is True

    r2 = client.get("/api/configuracion/activa", headers=auth)
    assert r2.json()["version"] == 2

    # Con un umbral menor y menos indicadores, mas personas pueden ser HiPo.
    r3 = client.post(
        "/api/evaluaciones/ejecutar",
        json={"periodo": "2026-S1", "configuracion_id": v2["id"]},
        headers=headers(tokens["evaluador"]),
    )
    assert r3.status_code == 200
    assert r3.json()["por_clasificacion"].get("alto_potencial", 0) > 0


def test_evaluacion_sin_configuracion_activa(client, tokens):
    auth = headers(tokens["gestor"])
    # Desactivar v2 y v1 no debe dejar activa ninguna… pero activar v1 de nuevo
    r = client.get("/api/configuracion", headers=auth)
    v1 = next(c for c in r.json() if c["version"] == 1)
    r2 = client.post(f"/api/configuracion/{v1['id']}/activar", headers=auth)
    assert r2.status_code == 200
    assert r2.json()["activa"] is True
