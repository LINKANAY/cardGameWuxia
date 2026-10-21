"""Endpoints /api/data/* — catálogos servidos a la UI (solo lectura)."""

from __future__ import annotations

from app.data import (
    CARTAS,
    ENEMIGOS,
    FINAL,
    MAZMORRAS,
    NIVELES,
    PROLOGO,
    REINOS,
    SECTA_DE_CARTA,
    SECTAS,
    TEXTO_FIN_NIVEL,
    TEXTO_INTRO_NIVEL,
    rareza_de,
)
from app.data.bestias import BESTIAS_DOMADAS
from app.engine.rules import descripcion_carta


def test_sectas(cliente):
    respuesta = cliente.get("/api/data/sectas")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    sectas = cuerpo["data"]["sectas"]
    assert len(sectas) == len(SECTAS) == 10
    assert [secta["identificador"] for secta in sectas] == list(SECTAS)
    primera = sectas[0]
    assert set(primera) == {
        "identificador",
        "nombre",
        "descripcion",
        "cartas_iniciales",
    }
    assert primera["identificador"] == "esp"
    assert len(primera["cartas_iniciales"]) == 5
    assert primera["cartas_iniciales"] == list(
        SECTAS["esp"].cartas_iniciales
    )


def test_cartas_paridad_con_catalogo(cliente):
    datos = cliente.get("/api/data/cartas").json()["data"]["cartas"]
    assert len(datos) == len(CARTAS) == 235
    por_id = {resumen["identificador"]: resumen for resumen in datos}
    for identificador, carta in CARTAS.items():
        resumen = por_id[identificador]
        assert resumen["nombre"] == carta.nombre, identificador
        assert resumen["tipo"] == carta.tipo.value, identificador
        assert resumen["coste_qi"] == carta.coste_qi, identificador
        assert resumen["ataque"] == carta.ataque, identificador
        assert resumen["vida"] == carta.vida, identificador
        assert resumen["rareza"] == rareza_de(carta), identificador
        assert resumen["secta"] == SECTA_DE_CARTA.get(identificador)
        assert resumen["disipa"] is carta.disipa, identificador
        assert resumen["descripcion"] == descripcion_carta(carta), (
            identificador
        )
    # casos conocidos: cf rara 0 por coste; pr Celestial rara 5
    assert por_id["cf"]["rareza"] == 0
    assert por_id["pr"]["rareza"] == 5
    # única técnica con `dsp` (Disipar Formación, bloque Y del v47)
    assert por_id["Y21"]["disipa"] is True


def test_enemigos_paridad_y_origen(cliente):
    datos = cliente.get("/api/data/enemigos").json()["data"]["enemigos"]
    assert len(datos) == len(ENEMIGOS) == 90
    for indice, enemigo in enumerate(ENEMIGOS):
        resumen = datos[indice]
        assert resumen["indice"] == indice
        assert resumen["nombre_enemigo"] == enemigo.nombre_enemigo
        assert resumen["secta"] == enemigo.secta
        assert resumen["vida"] == enemigo.vida
        assert resumen["dificultad"] == enemigo.dificultad
        assert resumen["frase_inicio"] == enemigo.frase_inicio
        assert resumen["rareza_recompensa"] == enemigo.rareza_recompensa
    # orden del catálogo aplanado: 48 campaña, 18 mazmorras, 24 misiones
    assert all(resumen["origen"] == "nivel" for resumen in datos[:48])
    assert all(resumen["origen"] == "mazmorra" for resumen in datos[48:66])
    assert all(resumen["origen"] == "mision" for resumen in datos[66:])


def test_narrativa(cliente):
    datos = cliente.get("/api/data/narrativa").json()["data"]["narrativa"]
    assert datos["prologo"] == PROLOGO
    assert datos["final"] == FINAL
    assert datos["reinos"] == list(REINOS)
    assert datos["textos_intro_nivel"] == list(TEXTO_INTRO_NIVEL)
    assert datos["textos_fin_nivel"] == list(TEXTO_FIN_NIVEL)
    assert datos["gradientes_nivel"] == [
        list(nivel.gradiente_color) for nivel in NIVELES
    ]


def test_mazmorras_paridad(cliente):
    datos = cliente.get("/api/data/mazmorras").json()["data"]["mazmorras"]
    assert len(datos) == len(MAZMORRAS) == 6
    for indice, mazmorra in enumerate(MAZMORRAS):
        resumen = datos[indice]
        assert resumen["indice"] == indice
        assert resumen["nombre"] == mazmorra.nombre
        assert resumen["nivel"] == mazmorra.nivel
        assert resumen["indice_receta"] == mazmorra.indice_receta
        assert resumen["pista"] == mazmorra.pista
        assert resumen["historia"] == mazmorra.historia
        assert resumen["pisos"] == [48 + indice * 3 + fase for fase in range(3)]


def test_bestias_domadas(cliente):
    datos = cliente.get("/api/data/bestias").json()["data"]["bestias"]
    assert len(datos) == len(BESTIAS_DOMADAS) == 8
    for indice, bestia in enumerate(BESTIAS_DOMADAS):
        resumen = datos[indice]
        assert resumen["identificador"] == bestia.identificador
        assert resumen["nombre"] == bestia.nombre
        assert resumen["ataque"] == bestia.ataque
        assert resumen["vida"] == bestia.vida
        assert resumen["indice_nivel"] == bestia.indice_nivel


def test_misiones_catalogo(cliente):
    datos = cliente.get(
        "/api/data/misiones", params={"secta": "esp"}
    ).json()["data"]["misiones"]
    assert len(datos) == 21 + 15  # GQ + missions(esp)
    ids = [m["identificador"] for m in datos]
    assert "g1" in ids and "g6" in ids and "esp15" in ids
    por_id = {m["identificador"]: m for m in datos}
    assert por_id["g1"]["clave"] == "w" and por_id["g1"]["meta"] == 1
    assert por_id["esp3"]["clave"] == "ek.val"
    assert por_id["g1"]["es_general"] is True
    assert por_id["esp1"]["es_general"] is False
    # missionGroup: ek.* cae en Progreso (quirk del JS)
    assert por_id["esp3"]["grupo"] == "Progreso"
    assert por_id["g1"]["grupo"] == "Combate"
    assert por_id["g4"]["grupo"] == "Exploración"
