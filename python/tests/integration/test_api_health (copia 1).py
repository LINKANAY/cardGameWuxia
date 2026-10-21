def test_health_ok(cliente):
    respuesta = cliente.get("/api/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    assert "version" in cuerpo["data"]
    assert cuerpo["data"]["uptime"] >= 0
