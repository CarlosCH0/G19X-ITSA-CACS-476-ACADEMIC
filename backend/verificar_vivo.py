# -*- coding: utf-8 -*-
"""Verificación en vivo contra el stack DESPLEGADO (nginx :8081, cadena completa).

A diferencia de verificar_modulos_e2e.py (que levanta su propio servidor con
una BD temporal), este script comprueba el sistema desplegado con Docker
Compose: http://localhost:8081 (nginx -> backend -> PostgreSQL).
Uso: venv\\Scripts\\python verificar_vivo.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx  # noqa: E402

BASE = "http://localhost:8081/api"  # Nginx envia las peticiones /api al backend.
OK, FALLOS = [], []


def paso(nombre, funcion):
    try:
        detalle = funcion()
        OK.append(nombre)
        print(f"  [OK] {nombre}" + (f" - {detalle}" if detalle else ""))
    except Exception as e:
        FALLOS.append(nombre)
        print(f"  [FALLO] {nombre} - {e}")


c = httpx.Client(timeout=60)


def login():
    tokens = {}
    for rol, (correo, pw) in {
        "admin": ("admin@develop.com.mx", "Admin123!"),
        "gestor": ("gestor@develop.com.mx", "Gestor123!"),
        "evaluador": ("evaluador@develop.com.mx", "Evaluador123!"),
        "consulta": ("consulta@develop.com.mx", "Consulta123!"),
    }.items():
        r = c.post(f"{BASE}/auth/login", json={"correo": correo, "password": pw})
        r.raise_for_status()
        tokens[rol] = {"Authorization": f"Bearer {r.json()['access_token']}"}
    globals()["auth"] = tokens
    return "4 roles autenticados vía nginx"


def rbac():
    assert c.get(f"{BASE}/usuarios").status_code == 401
    assert c.get(f"{BASE}/usuarios", headers=auth["consulta"]).status_code == 403
    return "401 sin token y 403 por permisos"


def colaboradores():
    r = c.get(f"{BASE}/colaboradores", params={"tamanio": 3}, headers=auth["consulta"])
    r.raise_for_status()
    total = r.json()["total"]
    cid = r.json()["items"][0]["id"]
    r = c.get(f"{BASE}/colaboradores/{cid}/perfil", headers=auth["consulta"])
    r.raise_for_status()
    assert "mediciones" in r.json() and "historial" in r.json()
    return f"{total} colaboradores, perfil consolidado OK"


def ejecutar_evaluacion():
    r = c.post(f"{BASE}/evaluaciones/ejecutar", json={"periodo": "2026-S1"},
               headers=auth["gestor"])
    r.raise_for_status()
    resumen = r.json()
    return (f"{resumen['total_evaluados']} evaluados | "
            f"{resumen['por_clasificacion']}")


def reportes():
    r = c.get(f"{BASE}/reportes/dashboard", headers=auth["consulta"])
    r.raise_for_status()
    k = r.json()["kpis"]
    r = c.get(f"{BASE}/reportes/matriz-9box", params={"periodo": "2026-S1"},
              headers=auth["consulta"])
    r.raise_for_status()
    cuadrantes = sum(len(q.get("colaboradores", q.get("evaluados", [])))
                     for q in r.json().get("cuadrantes", [])) if isinstance(r.json().get("cuadrantes"), list) else "OK"
    r = c.get(f"{BASE}/reportes/comparar", params={"ids": "1,2,3"},
              headers=auth["consulta"])
    r.raise_for_status()
    r = c.get(f"{BASE}/reportes/alertas", headers=auth["consulta"])
    r.raise_for_status()
    r = c.get(f"{BASE}/reportes/export/evaluaciones.csv", headers=auth["gestor"])
    r.raise_for_status()
    assert "evaluacion_id" in r.text
    return (f"KPIs activos={k['colaboradores_activos']} hipo={k['alto_potencial']} | "
            f"9-box, comparador, alertas y CSV OK")


def revision_humana():
    r = c.get(f"{BASE}/evaluaciones", params={"periodo": "2026-S1", "tamanio": 50},
              headers=auth["consulta"])
    r.raise_for_status()
    items = r.json()["items"]
    assert items, "sin evaluaciones"
    ev = items[0]
    det = c.get(f"{BASE}/evaluaciones/{ev['id']}", headers=auth["consulta"]).json()
    res_id = det["resultado"]["id"]
    r = c.post(f"{BASE}/revisiones/resultados/{res_id}",
               json={"estado": "confirmado", "comentario": "Verificado en vivo"},
               headers=auth["evaluador"])
    assert r.status_code == 201
    return f"resultado de {det['colaborador_nombre']} confirmado"


def planes():
    r = c.get(f"{BASE}/planes/estadisticas", headers=auth["evaluador"])
    r.raise_for_status()
    return "estadísticas de planes OK"


def ia():
    r = c.post(f"{BASE}/ia/consulta", json={"pregunta": "Quienes son HiPo?",
                                            "periodo": "2026-S1"},
               headers=auth["gestor"])
    r.raise_for_status()
    return f"origen: {r.json()['origen']}"


def auditoria():
    r = c.get(f"{BASE}/auditoria", params={"tamanio": 5}, headers=auth["admin"])
    r.raise_for_status()
    return f"{r.json()['total']} eventos registrados"


def frontend_servido():
    r = httpx.get("http://localhost:8081/", timeout=30)
    r.raise_for_status()
    assert "<div id=\"root\">" in r.text or "root" in r.text
    return "index.html servido por nginx"


paso("Health vía nginx", lambda: c.get(f"{BASE}/health").json()["estado"])
paso("Login 4 roles", login)
paso("RBAC", rbac)
paso("Colaboradores + perfil", colaboradores)
paso("Ejecutar evaluacion 2026-S1", ejecutar_evaluacion)
paso("Reportes completos", reportes)
paso("Revision humana", revision_humana)
paso("Planes de desarrollo", planes)
paso("IA asistida (degradacion local)", ia)
paso("Auditoria", auditoria)
paso("Frontend servido", frontend_servido)

c.close()
print(f"\n=== RESULTADO EN VIVO: {len(OK)} OK, {len(FALLOS)} fallos ===")
sys.exit(1 if FALLOS else 0)
