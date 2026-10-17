# -*- coding: utf-8 -*-
"""Smoke test end-to-end contra el servidor uvicorn en ejecución."""
import httpx

BASE = "http://127.0.0.1:8001"

with httpx.Client(timeout=30) as c:
    salud = c.get(f"{BASE}/api/health").json()
    print("1) health:", salud["estado"], "| modelo:", salud["version_modelo"])

    login = c.post(
        f"{BASE}/api/auth/login",
        json={"correo": "gestor@develop.com.mx", "password": "Gestor123!"},
    ).json()
    auth = {"Authorization": f"Bearer {login['access_token']}"}
    print("2) login OK:", login["usuario"]["nombre"], "| rol:", login["usuario"]["rol"])

    resumen = c.post(
        f"{BASE}/api/evaluaciones/ejecutar", json={"periodo": "2026-S1"}, headers=auth
    ).json()
    print(
        "3) pipeline:", resumen["total_evaluados"], "evaluados |",
        resumen["completos"], "completos |", resumen["incompletos"], "incompletos |",
        resumen["por_clasificacion"],
    )

    dash = c.get(f"{BASE}/api/reportes/dashboard", params={"periodo": "2026-S1"}, headers=auth).json()
    print("4) dashboard KPIs:", dash["kpis"])

    evaluaciones = c.get(f"{BASE}/api/evaluaciones", params={"periodo": "2026-S1"}, headers=auth).json()
    hipo = [e for e in evaluaciones["items"] if e["clasificacion"] == "alto_potencial"]
    print("5) evaluaciones:", evaluaciones["total"], "| HiPo:", len(hipo))

    detalle = c.get(f"{BASE}/api/evaluaciones/{hipo[0]['id']}", headers=auth).json()
    print("6) detalle HiPo:", detalle["colaborador_nombre"], detalle["puntuacion"],
          "| factores:", len(detalle["resultado"]["factores"]),
          "| explicacion:", detalle["resultado"]["explicacion_origen"])

    rev = c.post(
        f"{BASE}/api/revisiones/resultados/{hipo[0]['id']}",
        json={"estado": "confirmado", "comentario": "Validado en comité de talento"},
        headers=auth,
    )
    print("7) revisión humana:", rev.status_code, rev.json()["estado"])

    csv = c.get(f"{BASE}/api/reportes/export/evaluaciones.csv", params={"periodo": "2026-S1"}, headers=auth)
    lineas = csv.text.strip().splitlines()
    print("8) export CSV:", csv.headers["content-type"], "| filas:", len(lineas))

print("\nSMOKE E2E OK")
