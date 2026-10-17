"""Pruebas de asignación de indicadores por área."""
from tests.conftest import headers


def test_gestor_configura_pruebas_que_usa_el_area(client, tokens):
    auth = headers(tokens["gestor"])
    configuracion = client.get("/api/configuracion/areas-pruebas", headers=auth)
    assert configuracion.status_code == 200, configuracion.text
    datos = configuracion.json()
    area = next(area for area in datos["areas"] if area["area"] == "Tecnología")
    indicadores = {indicador["id"]: indicador for indicador in datos["indicadores"]}
    asignados_originales = area["indicador_ids"]

    colaboradores = client.get(
        "/api/colaboradores",
        params={"area": "Tecnología", "tamanio": 100},
        headers=auth,
    ).json()["items"]
    colaborador = colaboradores[0]
    indicador_id = next(
        indicador_id
        for indicador_id in asignados_originales
        if indicadores[indicador_id]["en_criterios"]
    )

    try:
        actualizada = client.put(
            "/api/configuracion/areas-pruebas",
            json={"area": "Tecnología", "indicador_ids": [indicador_id]},
            headers=auth,
        )
        assert actualizada.status_code == 200, actualizada.text
        tecnologia = next(
            item for item in actualizada.json()["areas"] if item["area"] == "Tecnología"
        )
        assert tecnologia["indicador_ids"] == [indicador_id]

        medicion = client.post(
            "/api/indicadores/mediciones",
            json={
                "colaborador_id": colaborador["id"],
                "periodo": "AREA-T1",
                "mediciones": [
                    {"indicador_id": indicador_id, "valor": 75, "validez": "valida"}
                ],
            },
            headers=auth,
        )
        assert medicion.status_code == 201, medicion.text

        ejecucion = client.post(
            "/api/evaluaciones/ejecutar",
            json={
                "periodo": "AREA-T1",
                "colaborador_id": colaborador["id"],
                "generar_explicacion_ia": False,
            },
            headers=auth,
        )
        assert ejecucion.status_code == 200, ejecucion.text
        evaluacion_id = ejecucion.json()["evaluacion_ids"][0]
        detalle = client.get(
            f"/api/evaluaciones/{evaluacion_id}", headers=auth
        ).json()
        assert [factor["codigo"] for factor in detalle["resultado"]["factores"]] == [
            indicadores[indicador_id]["codigo"]
        ]
    finally:
        restauracion = client.put(
            "/api/configuracion/areas-pruebas",
            json={"area": "Tecnología", "indicador_ids": asignados_originales},
            headers=auth,
        )
        assert restauracion.status_code == 200, restauracion.text

    sin_permiso = client.get(
        "/api/configuracion/areas-pruebas", headers=headers(tokens["evaluador"])
    )
    assert sin_permiso.status_code == 403
