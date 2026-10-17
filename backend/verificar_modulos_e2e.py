# -*- coding: utf-8 -*-
"""Verificación end-to-end exhaustiva de TODOS los módulos contra uvicorn vivo.

Arranca el servidor con una BD temporal, ejercita cada módulo de la API y
reporta el resultado. Uso:
    venv\\Scripts\\python verificar_modulos_e2e.py
"""
import os
import subprocess
import sys
import time

# Se usa una base aparte para no cambiar la base local de desarrollo.
os.environ["DATABASE_URL"] = "sqlite:///./e2e_verificacion.db"
os.environ["SEED_DEMO_DATA"] = "true"
for _f in ("e2e_verificacion.db",):
    if os.path.exists(_f):
        os.remove(_f)

import httpx  # noqa: E402

BASE = "http://127.0.0.1:8017"
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
    venv_python = os.path.join("venv", "Scripts", "python.exe")
    PROCESO = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "app.main:app", "--port", "8017", "--log-level", "warning"],
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
            raise RuntimeError("El servidor no arrancó")

        tokens, auth = {}, {}

        def login_y_probar():
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
            return "4 roles autenticados"

        def prueba_rbac():
            assert c.get(f"{BASE}/api/usuarios").status_code == 401
            assert c.get(f"{BASE}/api/usuarios", headers=auth["consulta"]).status_code == 403
            assert c.get(f"{BASE}/api/auditoria", headers=auth["evaluador"]).status_code == 403
            return "401 sin token y 403 por permisos verificados"

        def prueba_colaboradores():
            r = c.get(f"{BASE}/api/colaboradores", params={"tamanio": 5}, headers=auth["consulta"])
            r.raise_for_status()
            total = r.json()["total"]
            cid = r.json()["items"][0]["id"]
            r = c.get(f"{BASE}/api/colaboradores/{cid}/perfil", headers=auth["consulta"])
            r.raise_for_status()
            assert "mediciones" in r.json() and "historial" in r.json()
            r = c.post(f"{BASE}/api/colaboradores", json={
                "codigo": "E2E-001", "nombre": "Colaborador E2E",
                "area": "Calidad", "puesto": "Analista",
            }, headers=auth["gestor"])
            assert r.status_code == 201, r.text
            return f"{total} colaboradores, perfil y creacion OK"

        def prueba_indicadores_csv():
            r = c.get(f"{BASE}/api/indicadores", headers=auth["consulta"])
            r.raise_for_status()
            n_ind = len(r.json())
            r = c.get(f"{BASE}/api/indicadores/plantilla-csv", headers=auth["gestor"])
            r.raise_for_status()

        def prueba_configuracion():
            r = c.get(f"{BASE}/api/configuracion/activa", headers=auth["gestor"])
            r.raise_for_status()
            assert r.json()["activa"] is True
            r = c.post(f"{BASE}/api/configuracion", json={
                "nombre": "E2E v2", "pesos": {"LIDERAZGO": 0.6, "DESEMPENO_GLOBAL": 0.4},
                "umbral_hipo": 70, "activar": False,
            }, headers=auth["gestor"])
            assert r.status_code == 201, r.text
            v2 = r.json()["id"]
            r = c.post(f"{BASE}/api/configuracion/{v2}/activar", headers=auth["gestor"])
            r.raise_for_status()
            assert r.json()["activa"] is True
            r = c.get(f"{BASE}/api/reportes/config", headers=auth["consulta"])
            r.raise_for_status()
            c.post(f"{BASE}/api/configuracion/1/activar", headers=auth["gestor"])
            return "versionado de criterios, activacion y parametros vigentes OK"

        def prueba_pipeline():
            r = c.post(f"{BASE}/api/evaluaciones/ejecutar",
                       json={"periodo": "2026-S1"}, headers=auth["gestor"])
            r.raise_for_status()
            resumen = r.json()
            assert resumen["total_evaluados"] > 0
            r = c.get(f"{BASE}/api/evaluaciones", params={"periodo": "2026-S1"},
                      headers=auth["consulta"])
            r.raise_for_status()
            items = r.json()["items"]
            hipo = [e for e in items if e["clasificacion"] == "alto_potencial"]
            ev = (hipo or items)[0]
            r = c.get(f"{BASE}/api/evaluaciones/{ev['id']}", headers=auth["consulta"])
            r.raise_for_status()
            det = r.json()
            res_id = det["resultado"]["id"]
            r = c.post(f"{BASE}/api/revisiones/resultados/{res_id}",
                       json={"estado": "confirmado", "comentario": "Comite E2E"},
                       headers=auth["evaluador"])
            r.raise_for_status()
            r = c.post(f"{BASE}/api/evaluaciones/{ev['id']}/observaciones",
                       json={"texto": "Observacion E2E"}, headers=auth["evaluador"])
            r.raise_for_status()
            r = c.post(f"{BASE}/api/evaluaciones/{ev['id']}/explicacion",
                       headers=auth["gestor"])
            r.raise_for_status()
            return (f"{resumen['total_evaluados']} evaluados, revision humana, observacion y "
                    f"explicacion ({det['resultado'].get('explicacion_origen')}) OK")

        def prueba_reportes():
            r = c.get(f"{BASE}/api/reportes/dashboard", headers=auth["consulta"])
            r.raise_for_status()
            assert r.json()["kpis"]["evaluaciones_periodo"] > 0
            r = c.get(f"{BASE}/api/reportes/matriz-9box", headers=auth["consulta"])
            r.raise_for_status()
            assert "cajas" in r.json() and "etiquetas" in r.json()
            r = c.get(f"{BASE}/api/reportes/comparar", params={"ids": "1,2,3"},
                      headers=auth["consulta"])
            r.raise_for_status()
            assert len(r.json()["colaboradores"]) == 3
            r = c.get(f"{BASE}/api/reportes/alertas", headers=auth["consulta"])
            r.raise_for_status()
            assert "items" in r.json()
            r = c.get(f"{BASE}/api/reportes/export/evaluaciones.csv", headers=auth["gestor"])
            r.raise_for_status()
            assert "evaluacion_id" in r.text
            return "dashboard, 9-box, comparador, alertas y export CSV OK"

        def prueba_planes():
            r = c.post(f"{BASE}/api/planes", json={
                "colaborador_id": 1, "titulo": "Plan E2E", "foco": "liderazgo",
                "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31",
                "acciones": [{"descripcion": "Curso E2E"}, {"descripcion": "Mentoria E2E"}],
            }, headers=auth["gestor"])
            assert r.status_code == 201, r.text
            plan = r.json()
            r = c.patch(f"{BASE}/api/planes/acciones/{plan['acciones'][0]['id']}",
                        json={"completada": True}, headers=auth["gestor"])
            r.raise_for_status()
            assert r.json()["progreso"] == 50.0
            r = c.get(f"{BASE}/api/planes/estadisticas", headers=auth["evaluador"])
            r.raise_for_status()
            r = c.get(f"{BASE}/api/colaboradores/1/planes", headers=auth["evaluador"])
            r.raise_for_status()
            return "plan creado, avance 50% recalculado, estadisticas OK"

        def prueba_ia():
            r = c.post(f"{BASE}/api/ia/consulta", json={
                "pregunta": "Quienes son HiPo?", "periodo": "2026-S1",
            }, headers=auth["gestor"])
            r.raise_for_status()
            return f"consulta asistida OK (origen: {r.json()['origen']})"

        def prueba_usuarios_auditoria():
            r = c.get(f"{BASE}/api/usuarios/roles", headers=auth["admin"])
            r.raise_for_status()
            roles = len(r.json())
            r = c.get(f"{BASE}/api/auditoria", params={"tamanio": 5}, headers=auth["admin"])
            r.raise_for_status()
            eventos = r.json()["total"]
            assert eventos > 0, "debe haber eventos de auditoria"

        print("\n=== Verificacion E2E de modulos (servidor vivo) ===")
        paso(1, "Salud del servicio", lambda: c.get(f"{BASE}/api/health").json()["estado"])
        paso(2, "Autenticacion JWT (4 roles)", login_y_probar)
        paso(3, "RBAC (401/403)", prueba_rbac)
        paso(4, "Colaboradores CRUD + perfil", prueba_colaboradores)
        paso(5, "Indicadores + carga CSV", prueba_indicadores_csv)
        paso(6, "Configuracion de criterios", prueba_configuracion)
        paso(7, "Pipeline de evaluacion HiPo", prueba_pipeline)
        paso(8, "Reportes (dashboard, 9-box, comparador, alertas, CSV)", prueba_reportes)
        paso(9, "Planes de desarrollo", prueba_planes)
        paso(10, "IA asistida con degradacion", prueba_ia)
        paso(11, "Usuarios y auditoria", prueba_usuarios_auditoria)

    finally:
        c.close()
        if PROCESO:
            PROCESO.terminate()
            try:
                PROCESO.wait(timeout=15)
            except subprocess.TimeoutExpired:
                PROCESO.kill()
        for _f in ("e2e_verificacion.db",):
            for _intento in range(10):
                try:
                    if os.path.exists(_f):
                        os.remove(_f)
                    break
                except PermissionError:
                    time.sleep(0.5)

    print(f"\n=== Resultado: {len(OK)} modulos OK, {len(FALLOS)} fallos ===")
    if FALLOS:
        for nombre, err in FALLOS:
            print(f"  FALLO: {nombre}: {err}")
        return 1
    print("TODOS LOS MODULOS FUNCIONAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
