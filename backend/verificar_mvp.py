# -*- coding: utf-8 -*-
"""Verificación end-to-end del MVP contra uvicorn vivo.

Levanta el servidor con una BD temporal y ejercita los 8 módulos del MVP:
salud, login/RBAC, colaboradores, indicadores/mediciones, configuración,
pipeline de evaluación + revisión humana, reportes y auditoría.
Uso: venv\\Scripts\\python verificar_mvp.py
"""
import os
import subprocess
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./e2e_mvp.db"
os.environ["SEED_DEMO_DATA"] = "true"
if os.path.exists("e2e_mvp.db"):
    os.remove("e2e_mvp.db")

import httpx  # noqa: E402

BASE = "http://127.0.0.1:8018"
PROCESO = None
OK, FALLOS = [], []


def paso(numero, nombre, funcion):
    try:
        detalle = funcion()
        OK.append(nombre)
        print(f"  [OK] {numero}) {nombre}" + (f" - {detalle}" if detalle else ""))
    except Exception as e:  # noqa: BLE001
        FALLOS.append((nombre, str(e)))
        print(f"  [FALLO] {numero}) {nombre} - {e}")


def main() -> int:
    global PROCESO
    PROCESO = subprocess.Popen(
        [os.path.join("venv", "Scripts", "python.exe"),
         "-m", "uvicorn", "app.main:app", "--port", "8018", "--log-level", "warning"],
        env={**os.environ},
    )
    c = httpx.Client(timeout=60)
    try:
        for _ in range(60):
            try:
                if c.get(f"{BASE}/api/health").status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        else:
            raise RuntimeError("El servidor no arranco")

        tokens, auth = {}, {}

        def login_y_rbac():
            for rol, (correo, pw) in {
                "admin": ("admin@develop.com.mx", "Admin123!"),
                "gestor": ("gestor@develop.com.mx", "Gestor123!"),
                "evaluador": ("evaluador@develop.com.mx", "Evaluador123!"),
                "consulta": ("consulta@develop.com.mx", "Consulta123!"),
            }.items():
                r = c.post(f"{BASE}/api/auth/login", json={"correo": correo, "password": pw})
                r.raise_for_status()
                tokens[rol] = r.json()["access_token"]
                auth[rol] = {"Authorization": f"Bearer {tokens[rol]}"}
            assert c.get(f"{BASE}/api/colaboradores").status_code == 401
            assert c.get(f"{BASE}/api/auditoria", headers=auth["consulta"]).status_code == 403
            return "4 roles, 401 sin token y 403 por permisos"

        def prueba_colaboradores():
            r = c.get(f"{BASE}/api/colaboradores", params={"tamanio": 5},
                      headers=auth["consulta"])
            r.raise_for_status()
            total = r.json()["total"]
            cid = r.json()["items"][0]["id"]
            r = c.get(f"{BASE}/api/colaboradores/{cid}/perfil",
                      headers=auth["consulta"])
            r.raise_for_status()
            assert "mediciones" in r.json() and "historial" in r.json()
            return f"{total} colaboradores y perfil consolidado OK"

        def prueba_mediciones():
            inds = c.get(f"{BASE}/api/indicadores", headers=auth["consulta"]).json()
            por = {i["codigo"]: i["id"] for i in inds}
            colabs = c.get(f"{BASE}/api/colaboradores?q=COL-003",
                           headers=auth["consulta"]).json()["items"]
            cid = colabs[0]["id"]
            r = c.post(f"{BASE}/api/indicadores/mediciones", json={
                "colaborador_id": cid, "periodo": "2026-MVP",
                "mediciones": [
                    {"indicador_id": por["LIDERAZGO"], "valor": 91.5, "validez": "valida"},
                    {"indicador_id": por["COMUNICACION"], "valor": 80.0, "validez": "pendiente"},
                ],
            }, headers=auth["gestor"])
            assert r.status_code == 201, r.text
            meds = c.get(f"{BASE}/api/indicadores/mediciones",
                         params={"colaborador_id": cid, "periodo": "2026-MVP"},
                         headers=auth["gestor"]).json()
            pend = [m for m in meds if m["validez"] == "pendiente"][0]
            r = c.patch(f"{BASE}/api/indicadores/mediciones/{pend['id']}/validez",
                        json={"validez": "valida"}, headers=auth["gestor"])
            assert r.status_code == 200, r.text
            return f"{len(inds)} indicadores, carga bulk y validacion OK"

        def prueba_configuracion():
            r = c.get(f"{BASE}/api/configuracion/activa", headers=auth["gestor"])
            r.raise_for_status()
            v1 = r.json()["version"]
            r = c.post(f"{BASE}/api/configuracion", json={
                "nombre": "MVP v2", "pesos": {"LIDERAZGO": 0.6, "DESEMPENO_GLOBAL": 0.4},
                "umbral_hipo": 70, "activar": True,
            }, headers=auth["gestor"])
            assert r.status_code == 201, r.text
            c.post(f"{BASE}/api/configuracion/{v1}/activar", headers=auth["gestor"])
            return f"versionado de criterios OK (activa v{v1})"


        def prueba_pipeline_revision():
            r = c.post(f"{BASE}/api/evaluaciones/ejecutar",
                       json={"periodo": "2026-S1"}, headers=auth["gestor"])
            r.raise_for_status()
            resumen = r.json()
            r = c.get(f"{BASE}/api/evaluaciones", params={"periodo": "2026-S1"},
                      headers=auth["consulta"])
            items = r.json()["items"]
            ev = [e for e in items if e["clasificacion"] == "alto_potencial"][0]
            det = c.get(f"{BASE}/api/evaluaciones/{ev['id']}",
                        headers=auth["consulta"]).json()
            res_id = det["resultado"]["id"]
            assert det["resultado"]["factores"]
            r = c.post(f"{BASE}/api/revisiones/resultados/{res_id}",
                       json={"estado": "confirmado", "comentario": "Comite MVP"},
                       headers=auth["evaluador"])
            r.raise_for_status()
            r = c.post(f"{BASE}/api/evaluaciones/{ev['id']}/observaciones",
                       json={"texto": "Observacion MVP"}, headers=auth["evaluador"])
            r.raise_for_status()
            return (f"{resumen['total_evaluados']} evaluados, factores, revision "
                    f"humana y observacion OK")

        def prueba_reportes():
            r = c.get(f"{BASE}/api/reportes/dashboard", headers=auth["consulta"])
            r.raise_for_status()
            assert r.json()["kpis"]["evaluaciones_periodo"] > 0
            r = c.get(f"{BASE}/api/reportes/export/evaluaciones.csv",
                      headers=auth["gestor"])
            r.raise_for_status()
            assert "evaluacion_id" in r.text
            assert c.get(f"{BASE}/api/reportes/export/evaluaciones.csv",
                         headers=auth["consulta"]).status_code == 403
            return "dashboard y export CSV (con 403 para CONSULTA) OK"

        def prueba_auditoria():
            r = c.get(f"{BASE}/api/auditoria", params={"tamanio": 5},
                      headers=auth["admin"])
            r.raise_for_status()
            eventos = r.json()["total"]
            assert eventos > 0
            return f"{eventos} eventos registrados"

        print("\n=== Verificacion E2E del MVP (servidor vivo) ===")
        paso(1, "Salud del servicio",
             lambda: c.get(f"{BASE}/api/health").json()["estado"])
        paso(2, "Login JWT y RBAC", login_y_rbac)
        paso(3, "Colaboradores y perfil", prueba_colaboradores)
        paso(4, "Indicadores y mediciones", prueba_mediciones)
        paso(5, "Configuracion de criterios", prueba_configuracion)
        paso(6, "Pipeline + revision humana", prueba_pipeline_revision)
        paso(7, "Reportes y exportacion", prueba_reportes)
        paso(8, "Auditoria", prueba_auditoria)

    finally:
        c.close()
        if PROCESO:
            PROCESO.terminate()
            try:
                PROCESO.wait(timeout=15)
            except subprocess.TimeoutExpired:
                PROCESO.kill()
        for _intento in range(10):
            try:
                if os.path.exists("e2e_mvp.db"):
                    os.remove("e2e_mvp.db")
                break
            except PermissionError:
                time.sleep(0.5)

    print(f"\n=== Resultado: {len(OK)} modulos OK, {len(FALLOS)} fallos ===")
    if FALLOS:
        for nombre, err in FALLOS:
            print(f"  FALLO: {nombre}: {err}")
        return 1
    print("MVP COMPLETO Y FUNCIONAL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
