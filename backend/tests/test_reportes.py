# -*- coding: utf-8 -*-
"""Pruebas MVP de reportes: dashboard, perfil y exportación."""
from tests.conftest import headers


def test_dashboard(client, tokens):
    r = client.get("/api/reportes/dashboard", params={"periodo": "2026-S1"},
                   headers=headers(tokens["consulta"]))
    assert r.status_code == 200
    cuerpo = r.json()
    kpis = cuerpo["kpis"]
    assert kpis["evaluaciones_periodo"] > 0
    assert kpis["colaboradores_activos"] >= 12
    assert sum(cuerpo["distribucion_clasificacion"].values()) == kpis["evaluaciones_periodo"]
    assert cuerpo["evolucion_periodos"]


def test_perfil_consolidado_e_historico(client, tokens):
    auth = headers(tokens["consulta"])
    r = client.get("/api/colaboradores?incluir_inactivos=true", headers=auth)
    col001 = next(i for i in r.json()["items"] if i["codigo"] == "COL-001")

    r2 = client.get(f"/api/colaboradores/{col001['id']}/perfil", headers=auth)
    assert r2.status_code == 200
    perfil = r2.json()
    assert perfil["colaborador"]["codigo"] == "COL-001"
    assert perfil["mediciones"]
    assert perfil["historial"], "El perfil debe incluir evaluaciones (RF-10)"

    r3 = client.get(f"/api/colaboradores/{col001['id']}/historial", headers=auth)
    assert r3.status_code == 200
    assert {h["periodo"] for h in r3.json()}


def test_export_csv_respeta_permisos(client, tokens):
    # CONSULTA no tiene permiso de exportar (RN-07 / RF-14)
    r = client.get("/api/reportes/export/evaluaciones.csv",
                   headers=headers(tokens["consulta"]))
    assert r.status_code == 403

    r2 = client.get("/api/reportes/export/evaluaciones.csv",
                    params={"periodo": "2026-S1"}, headers=headers(tokens["gestor"]))
    assert r2.status_code == 200
    assert "text/csv" in r2.headers["content-type"]
    lineas = r2.text.strip().splitlines()
    assert lineas[0].startswith("evaluacion_id")
    assert any("COL-0" in linea for linea in lineas[1:])
