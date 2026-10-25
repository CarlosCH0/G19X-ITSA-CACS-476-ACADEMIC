def test_endpoint_health(client):
    respuesta = client.get("/api/health")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["aplicacion"]
    assert cuerpo["entorno"]
    assert cuerpo["version_modelo"]
    assert isinstance(cuerpo["ia_configurada"], bool)
