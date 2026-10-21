"""Estado de partida — paridad con el bloque de estado/save de `js/01-datos.js`.

Este módulo define dos cosas distintas:

- `Partida`: el estado **persistente** de una partida (meta-progreso).
  Es el objeto que se serializa al formato `xcg3` del monolito. No
  incluye el estado de combate en curso (`P`/`E` del JS), que vive en
  `app.engine.combat` (Fase 2) y no se guarda.
- `CartaJuego`: la instancia **mutable** de una carta en combate
  (lo que `mk(id)` produce en el JS: definición + stats actuales +
  flags de instancia).

Formato de guardado (`xcg3`): el JS envuelve en ``{v: 1, t: <ms>, data}``.
Las claves de `data` son cortas y se conservan tal cual para poder leer
partidas del monolito y escribir legibles para él. La correspondencia
completa está documentada en `Partida.a_dict`.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from app.data.hierbas import desde_horno, nuevo_horno
from app.data.jardin import (
    CLAVE_FORMACIONES,
    CLAVE_JARDIN,
    CLAVE_SEMILLAS,
    desde_formaciones,
    desde_jardin,
    desde_semillas,
    nuevo_jardin,
)
from app.data.pildoras import RECETA_TALISMAN_ESCAPE
from app.data.tipos import (
    CartaData,
    HabilidadActiva,
    TipoCarta,
    UltimoAliento,
)

#: Versión del sobre de guardado (`SAVE_VER` del JS).
VERSION_GUARDADO: int = 1


@dataclass
class CartaJuego:
    """Instancia jugable de una carta en combate (`mk(id)` del JS).

    El JS copia la definición con spread (``{...C[id], id, A, H, ready}``)
    y luego muta `A`/`H`/`ready`/`used`/`fz`/`sk` sobre el mismo objeto.
    Aquí se separa lo inmutable (`definicion`) de lo mutable (stats y
    flags), para no duplicar los ~30 campos de la definición.

    Cuando una pila sube de nivel (`stkUp`), el JS sobrescribe `ul`/`ab`/`gr`
    en la instancia. Aquí esos overrides viven en campos propios; las
    propiedades `ultimo_aliento`/`habilidad_activa`/`crece` prefieren el
    override y si no hay, leen la definición.

    Atributos:
        definicion: `CartaData` del catálogo (inmutable).
        ataque: ataque actual de la criatura (`A` de la instancia).
        vida: vida actual de la criatura (`H` de la instancia).
        lista_para_atacar: puede atacar este turno (`ready`).
        usada: habilidad activa ya usada este combate (`used`).
        congelada: está congelada este turno (`fz` de instancia;
            no confundir con `definicion.congelar`, que es el efecto
            ofensivo de las técnicas).
        copias_apiladas: nº de copias acumuladas en la pila (`sk`;
            1 = criatura normal; las bestias no se apilan).
        es_bestia: no se acumula (`bst` de la definición, copiado
            aquí por conveniencia del motor).
        recien_entrante: entró/apiló este turno (`fresh`; 1 = no puede
            ser objetivo de ciertos efectos de turno).
        aliento_apilado: override de `ul` tras apilar.
        habilidad_apilada: override de `ab` tras apilar.
        crece_apilado: override de `gr` tras apilar.
    """

    definicion: CartaData
    ataque: int | None
    vida: int | None
    lista_para_atacar: bool = False
    usada: bool = False
    congelada: bool = False
    copias_apiladas: int = 1
    es_bestia: bool = False
    recien_entrante: bool = False
    aliento_apilado: UltimoAliento | None = None
    habilidad_apilada: HabilidadActiva | None = None
    crece_apilado: int | None = None

    # --- acceso cómodo a la definición (evita `carta.definicion.x` por doquier) ---

    @property
    def identificador(self) -> str:
        """Id de la carta en el catálogo (`c.id` del JS)."""
        return self.definicion.identificador

    @property
    def nombre(self) -> str:
        """Nombre visible (`c.n`)."""
        return self.definicion.nombre

    @property
    def tipo(self) -> TipoCarta:
        """Tipo de carta (`c.t`)."""
        return self.definicion.tipo

    @property
    def coste_qi(self) -> int:
        """Coste en Qi (`c.c`)."""
        return self.definicion.coste_qi

    @property
    def ultimo_aliento(self) -> UltimoAliento | None:
        """Último aliento efectivo (override de pila o definición)."""
        if self.aliento_apilado is not None:
            return self.aliento_apilado
        return self.definicion.ultimo_aliento

    @property
    def habilidad_activa(self) -> HabilidadActiva | None:
        """Habilidad activa efectiva (override de pila o definición)."""
        if self.habilidad_apilada is not None:
            return self.habilidad_apilada
        return self.definicion.habilidad_activa

    @property
    def crece(self) -> int | None:
        """Crece al atacar efectivo (override de pila o definición)."""
        if self.crece_apilado is not None:
            return self.crece_apilado
        return self.definicion.crece


def crear_carta_juego(identificador: str) -> CartaJuego:
    """Crea una instancia jugable a partir del catálogo (`mk(id)`).

    Busca primero en `CARTAS`; si no está (bestias espirituales
    `EB1`…`EB6`), en el catálogo de bestias.

    Args:
        identificador: clave de la carta en `CARTAS` o `BESTIAS_POR_ID`.

    Returns:
        `CartaJuego` con stats base y `lista_para_atacar=False`.

    Raises:
        KeyError: el id no existe en ningún catálogo.
    """
    from app.data.cartas import CARTAS
    from app.data.tipos import TipoEfecto

    if identificador in CARTAS:
        base = CARTAS[identificador]
    else:
        from app.data.bestias import BESTIAS_POR_ID

        b = BESTIAS_POR_ID.get(identificador)
        if b is None:
            raise KeyError(f"Carta desconocida: {identificador!r}")
        aliento = (
            UltimoAliento(TipoEfecto(b.ultimo_aliento[0]), b.ultimo_aliento[1])
            if b.ultimo_aliento
            else None
        )
        habilidad = (
            HabilidadActiva(
                coste_qi=b.habilidad_activa[0],
                tipo=TipoEfecto(b.habilidad_activa[1]),
                valor=b.habilidad_activa[2],
                descripcion=b.habilidad_activa[3],
            )
            if b.habilidad_activa
            else None
        )
        base = CartaData(
            identificador=b.identificador,
            nombre=b.nombre,
            coste_qi=0,
            tipo=TipoCarta.CRIATURA,
            ataque=b.ataque,
            vida=b.vida,
            provocar=b.provocar,
            impetu=b.impetu,
            robar_vida=b.robar_vida,
            crece=b.crece_bonus,
            ultimo_aliento=aliento,
            habilidad_activa=habilidad,
            rareza_fija=b.rareza,
            reliquia=True,
            bestia=True,
        )
    return CartaJuego(
        definicion=base,
        ataque=base.ataque,
        vida=base.vida,
        lista_para_atacar=False,
        es_bestia=base.bestia,
    )


def nuevas_misiones() -> dict:
    """Estado por defecto de misiones/contadores (`newQs()` del JS).

    Devuelve una copia fresca; el JS lo hace con `Object.assign(newQs(),
    d.qs || {})` al cargar, es decir, fusiona el guardado sobre estos
    defaults.
    """
    return {
        "track": "",
        "bu": 0,
        "ss": 0,
        "sv": 0,
        "ge": 0,
        "bsc": 0,
        "bm": 0,
        "w": 0,
        "bk": 0,
        "bs": 0,
        "sp": 0,
        "hl": 0,
        "tg": 0,
        "tt": 0,
        "eq": 0,
        "sc": 0,
        "sm": 0,
        "rsm": 0,
        "sh": 0,
        "br": 0,
        "dg": 0,
        "am": 0,
        "pu": 0,
        "ek": {},
        "n": {},
    }


def _fusionar_gacha(guardado, defaults: dict) -> dict:
    """Fusiona el estado del gacha guardado sobre los defaults.

    Reproduce `GachaSystem.setState({tickets: d.gt, pity: d.gp})` de
    `js/01-datos.js:214`: si el valor guardado es un dict se fusiona
    clave a clave sobre los defaults; si es None u otro tipo (guardados
    viejos del backend que aún no tenían el dict) se conservan los
    defaults.

    Args:
        guardado: valor leído de `gt`/`gp` (dict, None u otro).
        defaults: dict por defecto a fusionar.

    Returns:
        Dict fusionado (nuevo objeto).
    """
    resultado = dict(defaults)
    if isinstance(guardado, dict):
        resultado.update(guardado)
    return resultado


@dataclass
class Partida:
    """Estado persistente de una partida (el `data` de `xcg3`).

    Cada atributo documenta la clave corta del JS. Al serializar con
    `a_dict` se usan esas claves para que el JSON sea compatible con el
    monolito (y viceversa con `desde_dict`).

    Atributos:
        nivel_reino: índice en `REINOS` (`realm`; 0–14).
        vida_hroe: vida actual del héroe entre combates, o None
            si aún no hay partida en curso (`hp`/`hpNow`).
        victorias: índices globales de `ENEMIGOS` vencidos (`wins`).
        coleccion: cartas poseídas, id → nº de copias (`col`; máx. 3).
        secta: secta elegida (`sect`; clave de `SECTAS`).
        materiales: Material → cantidad (`mat.h/n/p`; default 0).
        piedras_espirituales: moneda principal (`stn`; default 30).
        mazos: mazos guardados por el jugador (`dk`/`mzs`).
        mazo_activo: índice del mazo activo o -1 (`ad`/`mza`).
        pildoras: id → cantidad (`pil`).
        atuendo: secta → variante de arte (`of`/`outfit`).
        recetas: id de píldora aprendida → 1 (`rec`); el JS siempre
            fuerza `tes` al cargar y arranca con `vit`.
        bestia_equipada: id de bestia o None (`be`/`beastEq`).
        equipo_guardado: armaduras forjadas (`gr`/`gear`).
        equipado: armaduras puestas (`eq`/`equip`).
        secta_elegida_confirmada: secta ya confirmada en la primera
            partida (`sc`/`schosen`); None = aún no ha elegido.
        usos_equipo: usos restantes de equipo con cargas (`du`/`dur`).
        muertes: contador de muertes (`dt`/`deaths`).
        mejor_racha: victorias seguidas máximas (`bt`/`best`).
        misiones: estado de misiones y contadores (`qs`; ver `nuevas_misiones`).
        misiones_reclamadas: ids de misiones ya reclamadas (`qd`).
        entradas_gacha: tickets de gacha (`gt`; estado de
            `GachaSystem.tickets`: `ticket_common`/`ticket_premium`).
        piedad_gacha: contador de piedad del gacha (`gp`; estado de
            `GachaSystem.pity`: `standard_pity`/`premium_pity`).
        horno: estado del Horno de Alquimia (`xn` aquí;
            en el monolito es el `localStorage` aparte `xcg_horno` de
            `js/11-horno.js`: `{hierbas, pildoras, refinadas, fallos}`).
        jardin: estado del Jardín Medicinal (`jdn`): nivel/casillas de
            la cuadrícula y formación equipada. Contenido nuevo, no
            existe en el monolito.
        semillas: semillas de jardín, id de hierba → nº (`sd`);
            arranca con 2 «hs».
        formaciones_crecimiento: formaciones de crecimiento poseídas,
            id `fc*` → nº de copias (`fg`).
    """

    nivel_reino: int = 0
    vida_hroe: int | None = None
    victorias: list[int] = field(default_factory=list)
    coleccion: dict[str, int] = field(default_factory=dict)
    secta: str = "esp"
    materiales: dict[str, int] = field(
        default_factory=lambda: {"h": 0, "n": 0, "p": 0}
    )
    piedras_espirituales: int = 30
    mazos: list = field(default_factory=list)
    mazo_activo: int = -1
    pildoras: dict[str, int] = field(default_factory=dict)
    atuendo: dict[str, int] = field(default_factory=dict)
    recetas: dict[str, int] = field(default_factory=lambda: {"vit": 1})
    bestia_equipada: str | None = None
    equipo_guardado: dict = field(default_factory=dict)
    equipado: dict = field(default_factory=dict)
    secta_elegida_confirmada: str | None = None
    usos_equipo: dict[str, int] = field(default_factory=dict)
    muertes: int = 0
    mejor_racha: int = 0
    misiones: dict = field(default_factory=nuevas_misiones)
    misiones_reclamadas: dict[str, int] = field(default_factory=dict)
    entradas_gacha: dict[str, int] = field(
        default_factory=lambda: {"ticket_common": 5, "ticket_premium": 2}
    )
    piedad_gacha: dict[str, int] = field(
        default_factory=lambda: {"standard_pity": 0, "premium_pity": 0}
    )
    horno: dict = field(default_factory=nuevo_horno)
    jardin: dict = field(default_factory=nuevo_jardin)
    semillas: dict[str, int] = field(
        default_factory=lambda: {"hs": 2}
    )
    formaciones_crecimiento: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Fuerza `rec.tes = 1` como el JS al cargar el save."""
        self.recetas.setdefault(RECETA_TALISMAN_ESCAPE, 1)

    # --- serialización al formato xcg3 -------------------------------------

    def a_dict(self) -> dict:
        """Serializa al dict `data` del guardado `xcg3`.

        Claves del JS entre paréntesis. El orden es el del `save()`
        original para facilitar la comparación visual:

        ``realm, hp, wins, col, sect, mat, stn, dk, ad, pil, of, rec,
        be, gr, eq, sc, du, dt, bt, qs, qd, gt, gp``

        y ``xn`` al final: el estado del Horno de Alquimia. `xn` es la
        clave **backend** del `xcg_horno` del monolito (allí el horno
        se guarda en su propio `localStorage`, fuera del `xcg3`); se
        incluye aquí para que el backend maneje una sola partida.

        Después van ``jdn, sd, fg`` (jardín, semillas y formaciones de
        crecimiento): claves nuevas del backend, sin equivalente en el
        monolito.
        """
        return {
            "realm": self.nivel_reino,
            "hp": self.vida_hroe,
            "wins": list(self.victorias),
            "col": dict(self.coleccion),
            "sect": self.secta,
            "mat": dict(self.materiales),
            "stn": self.piedras_espirituales,
            "dk": copy.deepcopy(self.mazos),
            "ad": self.mazo_activo,
            "pil": dict(self.pildoras),
            "of": dict(self.atuendo),
            "rec": dict(self.recetas),
            "be": self.bestia_equipada,
            "gr": copy.deepcopy(self.equipo_guardado),
            "eq": copy.deepcopy(self.equipado),
            "sc": self.secta_elegida_confirmada,
            "du": dict(self.usos_equipo),
            "dt": self.muertes,
            "bt": self.mejor_racha,
            "qs": copy.deepcopy(self.misiones),
            "qd": dict(self.misiones_reclamadas),
            "gt": self.entradas_gacha,
            "gp": self.piedad_gacha,
            "xn": copy.deepcopy(self.horno),
            CLAVE_JARDIN: copy.deepcopy(self.jardin),
            CLAVE_SEMILLAS: dict(self.semillas),
            CLAVE_FORMACIONES: dict(self.formaciones_crecimiento),
        }

    @classmethod
    def desde_dict(cls, data: dict | None, *, legacy_xcg2: bool = False) -> Partida:
        """Reconstruye una partida desde el dict `data` guardado.

        Replica los defaults del bloque de carga del JS (línea ~6341 de
        `sendero_del_inmortal_v48.html` / sección save de `js/01-datos.js`):

        - `realm` se recorta a ``len(REINOS) - 1``.
        - `wins` vacío por defecto; con `legacy_xcg2=True` aplica la
          re-claveación ``floor(k/3)*6 + [1,3,5][k%3]` que el JS usa
          al migrar partidas antiguas de `xcg2`.
        - `rec` arranca con `{vit: 1}` y **siempre** incluye `tes`
          (el JS hace `rec.tes = 1` tras cargar).
        - `qs` se fusiona sobre `nuevas_misiones()` (claves nuevas del JS
          aparecen con su default aunque el save sea viejo).
        - `schosen`: si no está, se deduce de `wins`/`col` como el JS.
        - `xn` (horno): ausente o corrupto → inventario inicial; ids de
          hierbas desconocidos o cantidades ≤ 0 se filtran, como el
          `cargar()` de `js/11-horno.js:265`.
        - `jdn`/`sd`/`fg` (jardín): ausentes (saves anteriores al
          módulo) o corruptos → jardín nuevo, 2 semillas «hs» y sin
          formaciones; ver `app.data.jardin`.

        Args:
            data: el dict guardado (puede ser None o {} para partida nueva).
            legacy_xcg2: aplicar la conversión de `wins` del xcg2.

        Returns:
            `Partida` lista para usar.
        """
        datos = data or {}
        victorias = [int(indice) for indice in (datos.get("wins") or [])]
        if legacy_xcg2:
            victorias = [
                (indice // 3) * 6 + (1, 3, 5)[indice % 3]
                for indice in victorias
            ]
        materiales = datos.get("mat") or {"h": 0, "n": 0, "p": 0}
        # Asegura las 3 claves aunque el save viejo falte alguna.
        materiales = {
            "h": materiales.get("h", 0),
            "n": materiales.get("n", 0),
            "p": materiales.get("p", 0),
        }
        recetas = dict(datos.get("rec") or {"vit": 1})
        recetas.setdefault(RECETA_TALISMAN_ESCAPE, 1)
        misiones = nuevas_misiones()
        misiones.update(datos.get("qs") or {})
        # `ek` y `n` son dicts anidados: fusionar por clave.
        for clave_anidada in ("ek", "n"):
            base_anidada = nuevas_misiones()[clave_anidada]
            base_anidada.update(
                (datos.get("qs") or {}).get(clave_anidada) or {}
            )
            misiones[clave_anidada] = base_anidada
        coleccion = datos.get("col") or {}
        secta_confirmada = datos.get("sc")
        if secta_confirmada is None:
            secta_confirmada = (
                (datos.get("sect") or "esp")
                if (victorias or coleccion)
                else None
            )
        from app.data.narrativa import REINOS

        return cls(
            nivel_reino=min(len(REINOS) - 1, datos.get("realm") or 0),
            vida_hroe=datos.get("hp"),
            victorias=victorias,
            coleccion=dict(coleccion),
            secta=datos.get("sect") or "esp",
            materiales=materiales,
            piedras_espirituales=(
                datos["stn"] if datos.get("stn") is not None else 30
            ),
            mazos=datos.get("dk") or [],
            mazo_activo=(
                datos["ad"] if datos.get("ad") is not None else -1
            ),
            pildoras=datos.get("pil") or {},
            atuendo=datos.get("of") or {},
            recetas=recetas,
            bestia_equipada=datos.get("be"),
            equipo_guardado=datos.get("gr") or {},
            equipado=datos.get("eq") or {},
            secta_elegida_confirmada=secta_confirmada,
            usos_equipo=datos.get("du") or {},
            muertes=datos.get("dt") or 0,
            mejor_racha=datos.get("bt") or 0,
            misiones=misiones,
            misiones_reclamadas=datos.get("qd") or {},
            entradas_gacha=_fusionar_gacha(
                datos.get("gt"),
                {"ticket_common": 5, "ticket_premium": 2},
            ),
            piedad_gacha=_fusionar_gacha(
                datos.get("gp"),
                {"standard_pity": 0, "premium_pity": 0},
            ),
            horno=desde_horno(datos.get("xn")),
            jardin=desde_jardin(datos.get(CLAVE_JARDIN)),
            semillas=desde_semillas(datos.get(CLAVE_SEMILLAS)),
            formaciones_crecimiento=desde_formaciones(
                datos.get(CLAVE_FORMACIONES)
            ),
        )

    # --- helpers de negocio (reglas puras de Fase 1) ----------------------

    def puede_comprar_carta(self, identificador: str) -> bool:
        """`okBuy(id)` del JS: rareza < 5 y sin secta restringida.

        Las reliquias (`lk`) y las Celestiales (rareza 5) no se venden;
        las cartas de otra secta sólo si coincide con
        `secta_elegida_confirmada`. La regla vive en `engine.rules`
        (aquí sólo se aporta la secta confirmada de la partida).
        """
        from app.engine.rules import puede_comprar_carta

        return puede_comprar_carta(identificador, self.secta_elegida_confirmada)

    def precio_compra(self, identificador: str) -> int:
        """Precio en piedras de una carta (`PR(id)` del JS)."""
        from app.engine.rules import precio_compra

        return precio_compra(identificador)
