"""Tipos de datos del juego — nombres descriptivos, claves JS documentadas.

Cada dataclass representa un dato estático del catálogo (carta, secta,
nivel, enemigo, píldora…). Los campos usan nombres en español claros; en
el docstring de cada campo se cita la clave críptica del monolito JS para
poder cruzar referencias con `js/01-datos.js` y `js/02-motor.js`.

Convención de serialización:
- Los identificadores (`'cf'`, `'esp'`, `'vit'`…) se conservan tal cual:
  son el pegamento con el JS, con los saves (`xcg3`) y con la UI.
- Los números y listas se copian sin traducir (paridad de fórmulas).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TipoCarta(StrEnum):
    """Tipo de carta (`carta.t` en el JS: C/T/P/F/R).

    - CRIATURA: entra al tablero y acumula (`'C'`).
    - TECNICA: efecto inmediato (`'T'`).
    - PILDORA: carta-píldora de mazo (`'P'`).
    - FORMACION: pieza de formación (`'F'`; usado en el mando v47+).
    - RUNA: pieza de runa (`'R'`; idem).
    """

    CRIATURA = "C"
    TECNICA = "T"
    PILDORA = "P"
    FORMACION = "F"
    RUNA = "R"


class Material(StrEnum):
    """Materiales de alquimia (`mat.h/n/p` en el JS; ver `MN`).

    Las claves cortas (`h`, `n`, `p`) son las que usa el guardado.
    """

    HIERBAS = "h"
    NUCLEOS = "n"
    POLVO_JADE = "p"


class TipoEfecto(StrEnum):
    """Código de un efecto simple (`fx` de `js/02-motor.js:25`).

    El monolito usa una letra por efecto dentro de `ul`/`ab`/`bc`; aquí
    es un enum legible. El valor del miembro **es** esa letra, así que la
    serialización al JS (`a_js`) es directa y no hay pérdida.

    - DANO_HROE (`d`): daña al héroe rival.
    - CURAR (`h`): cura a quien provoca el efecto.
    - ROBAR (`r`): roba cartas.
    - ESCUDO (`s`): gana escudo.
    - DRENAR_QI (`e`): el rival pierde Qi sellado en su siguiente turno.
    - GANAR_QI (`q`): gana Qi.
    - DANO_CRIATURA_AL_AZAR (`m`): daña a una criatura rival al azar
      (al héroe rival si no hay criaturas). Sólo lo usa `bc`.
    - AUTO_DANO (`x`): el lado dueño pierde la vida (el escudo
      absorbe). Sólo lo usan los `ts` de Formación/Runa (`fmTurn`
      de js/04-mazos-formaciones.js:32).
    """

    DANO_HROE = "d"
    CURAR = "h"
    ROBAR = "r"
    ESCUDO = "s"
    DRENAR_QI = "e"
    GANAR_QI = "q"
    DANO_CRIATURA_AL_AZAR = "m"
    AUTO_DANO = "x"


@dataclass(frozen=True, slots=True)
class MejoraAliada:
    """Mejora que aplica una carta a una criatura aliada (`carta.bf`).

    Atributos:
        ataque: puntos de ataque añadidos (`bf[0]`).
        vida: puntos de vida añadidos (`bf[1]`).
    """

    ataque: int
    vida: int


@dataclass(frozen=True, slots=True)
class UltimoAliento:
    """Efecto al morir la criatura (`carta.ul`).

    Atributos:
        tipo: qué hace el efecto (`ul[0]`; ver `TipoEfecto`).
        valor: magnitud del efecto (`ul[1]`).
    """

    tipo: TipoEfecto
    valor: int


@dataclass(frozen=True, slots=True)
class HabilidadActiva:
    """Habilidad que la criatura puede activar gastando Qi (`carta.ab`).

    Atributos:
        coste_qi: Qi que cuesta activarla (`ab[0]`).
        tipo: qué hace el efecto (`ab[1]`; ver `TipoEfecto`).
        valor: magnitud (`ab[2]`).
        descripcion: texto mostrado en la UI (`ab[3]`).
    """

    coste_qi: int
    tipo: TipoEfecto
    valor: int
    descripcion: str


@dataclass(frozen=True, slots=True)
class AlEntrar:
    """Efecto al jugar la carta (`carta.bc`).

    Atributos:
        tipo: qué hace el efecto (`bc[0]`; en el JS sólo se usa `'m'`,
            ver `TipoEfecto.DANO_CRIATURA_AL_AZAR`).
        valor: magnitud (`bc[1]`).
    """

    tipo: TipoEfecto
    valor: int


@dataclass(frozen=True, slots=True)
class CartaData:
    """Definición inmutable de una carta del catálogo (`C[id]` en el JS).

    Los campos con ``None``/``False`` significan "la carta no tiene ese
    atributo", igual que la ausencia de la clave en el objeto JS. El
    motor de combate (`app/engine/combat.py`, Fase 2) debe leer estos
    campos y **nunca** asumir que un campo está presente solo porque
    otra carta lo tenga.

    Atributos:
        identificador: clave corta del catálogo (`la clave del dict C`).
        nombre: nombre visible (`n`).
        coste_qi: coste para jugarla (`c`).
        tipo: ver `TipoCarta` (`t`).
        dano_hroe: daño directo al héroe rival (`d`).
        es_espada: participa en el contador "Intención de Espada" de la
            secta Espada Celestial (`k`).
        ataque: ataque inicial de la criatura (`A`).
        vida: vida inicial de la criatura (`H`).
        curar: curación fija (`he`).
        curar_porcentaje: si existe, `he` es el mínimo y el valor real
            es ``max(he, round(vida_max * hq / 100))`` (`hq`).
        escudo: escudo ganado (`sh`).
        robar: cartas que robas (`dr`).
        ganar_qi: Qi que ganas al jugarla (`q`).
        drenar_qi_rival: el rival pierde ese Qi en su siguiente turno
            (máx. +4 acumulables) (`eq`).
        sacrificar_vida: vida que pagas al jugarla (`sac`).
        dano_area: daño a todas las criaturas rivales (`aoe`).
        dano_criatura: daño a una criatura rival (`td`; si no hay
            criaturas, cae al héroe).
        congelar: congela al objetivo de `dano_criatura` (`fz`).
        mejorar_aliada: mejora a una criatura propia (`bf`).
        ultimo_aliento: efecto al morir (`ul`).
        habilidad_activa: activable gastando Qi (`ab`).
        al_entrar: efecto al entrar en juego (`bc`).
        robar_vida: el daño de ataque cura al portador (`vm`).
        impetu: entra ya preparada para atacar (`rs`).
        crece: +N de ataque al atacar (`gr`).
        provocar: los rivales deben atacarla primero (`tk`).
        tribulacion: daña 3 a ambos héroes y 4 a todas las criaturas (`trib`).
        renovar: devuelve tu mano al mazo y roba N (`rf`).
        vacio_descarte: el rival descarta N cartas al Agujero Negro (`fd`).
        ciclo: descarta tu mano y roba otras tantas (`cy`).
        abismo_traer: cartas que traes del Agujero Negro (`vb`).
        abismo_elegir: si es True, eliges las cartas del Agujero Negro;
            si False, salen al azar (`vp`, sólo relevante con `vb`).
        samsara: baraja N cartas al azar del Agujero Negro (`vs`).
        disipa: destruye formaciones y runas rivales (`dsp`).
        rareza_fija: rareza explícita; si existe, manda sobre la tabla
            de rareza por coste (`r`).
        reliquia: no aparece en el mercado ni en recompensas normales
            (`lk`).
        bestia: criatura especial de bestia; no se acumula (`bst`).
    """

    identificador: str
    nombre: str
    coste_qi: int
    tipo: TipoCarta
    # --- efectos ofensivos / defensivos ---
    dano_hroe: int | None = None
    dano_criatura: int | None = None
    dano_area: int | None = None
    congelar: bool = False
    tribulacion: bool = False
    sacrificar_vida: int | None = None
    curar: int | None = None
    curar_porcentaje: int | None = None
    escudo: int | None = None
    robar: int | None = None
    ganar_qi: int | None = None
    drenar_qi_rival: int | None = None
    # --- criatura ---
    ataque: int | None = None
    vida: int | None = None
    provocar: bool = False
    impetu: bool = False
    robar_vida: bool = False
    crece: int | None = None
    es_espada: bool = False
    # --- efectos compuestos ---
    mejorar_aliada: MejoraAliada | None = None
    ultimo_aliento: UltimoAliento | None = None
    habilidad_activa: HabilidadActiva | None = None
    al_entrar: AlEntrar | None = None
    # --- efectos v47+ (Agujero Negro / formaciones) ---
    renovar: int | None = None
    vacio_descarte: int | None = None
    ciclo: int | None = None
    abismo_traer: int | None = None
    abismo_elegir: bool = False
    samsara: int | None = None
    disipa: bool = False
    # --- formaciones / runas (piezas F/R; ver fmPut en el motor) ---
    mejora_ataque_al_trazar: int | None = None
    mejora_vida_al_trazar: int | None = None
    efecto_inicio_turno: tuple[TipoEfecto, int] | None = None
    duracion_turnos: int | None = None
    # --- clasificación ---
    rareza_fija: int | None = None
    reliquia: bool = False
    bestia: bool = False

    @classmethod
    def desde_js(cls, identificador: str, bruto: dict) -> CartaData:
        """Construye desde el dict crudo de `C[id]` del monolito.

        Mapea cada clave corta a su campo con nombre. Las claves
        desconocidas se ignoran a propósito (si el monolito añade una,
        el test de integridad de `test_datos.py` fallará y se documentará
        aquí).

        Args:
            identificador: clave de la carta (`'cf'`, `'ev'`…).
            bruto: el objeto JS tal cual (`C[id]`).

        Returns:
            Instancia inmutable de `CartaData`.
        """
        tipo = TipoCarta(bruto["t"])
        mejora = bruto.get("bf")
        aliento = bruto.get("ul")
        habilidad = bruto.get("ab")
        efecto_entrada = bruto.get("bc")
        return cls(
            identificador=identificador,
            nombre=bruto["n"],
            coste_qi=bruto["c"],
            tipo=tipo,
            dano_hroe=bruto.get("d"),
            dano_criatura=bruto.get("td"),
            dano_area=bruto.get("aoe"),
            congelar=bool(bruto.get("fz")),
            tribulacion=bool(bruto.get("trib")),
            sacrificar_vida=bruto.get("sac"),
            curar=bruto.get("he"),
            curar_porcentaje=bruto.get("hq"),
            escudo=bruto.get("sh"),
            robar=bruto.get("dr"),
            ganar_qi=bruto.get("q"),
            drenar_qi_rival=bruto.get("eq"),
            ataque=bruto.get("A"),
            vida=bruto.get("H"),
            provocar=bool(bruto.get("tk")),
            impetu=bool(bruto.get("rs")),
            robar_vida=bool(bruto.get("vm")),
            crece=bruto.get("gr"),
            es_espada=bool(bruto.get("k")),
            mejorar_aliada=(
                MejoraAliada(mejora[0], mejora[1]) if mejora else None
            ),
            ultimo_aliento=(
                UltimoAliento(TipoEfecto(aliento[0]), aliento[1])
                if aliento
                else None
            ),
            habilidad_activa=(
                HabilidadActiva(
                    coste_qi=habilidad[0],
                    tipo=TipoEfecto(habilidad[1]),
                    valor=habilidad[2],
                    descripcion=habilidad[3],
                )
                if habilidad
                else None
            ),
            al_entrar=(
                AlEntrar(TipoEfecto(efecto_entrada[0]), efecto_entrada[1])
                if efecto_entrada
                else None
            ),
            renovar=bruto.get("rf"),
            vacio_descarte=bruto.get("fd"),
            ciclo=bruto.get("cy"),
            abismo_traer=bruto.get("vb"),
            abismo_elegir=bool(bruto.get("vp")),
            samsara=bruto.get("vs"),
            disipa=bool(bruto.get("dsp")),
            mejora_ataque_al_trazar=bruto.get("pa"),
            mejora_vida_al_trazar=bruto.get("ph"),
            efecto_inicio_turno=(
                (TipoEfecto(ts[0]), ts[1]) if (ts := bruto.get("ts")) else None
            ),
            duracion_turnos=bruto.get("du"),
            rareza_fija=bruto.get("r"),
            reliquia=bool(bruto.get("lk")),
            bestia=bool(bruto.get("bst")),
        )

    def a_js(self) -> dict:
        """Serializa de vuelta al formato crudo del JS (`C[id]`).

        Sólo emite las claves presentes (no las None/False), para que
        el dict resultante sea equivalente al original y utilizable en
        tests espejo.
        """
        salida: dict = {
            "n": self.nombre,
            "c": self.coste_qi,
            "t": self.tipo.value,
        }
        simples = {
            "d": self.dano_hroe,
            "td": self.dano_criatura,
            "aoe": self.dano_area,
            "fz": self.congelar or None,
            "trib": self.tribulacion or None,
            "sac": self.sacrificar_vida,
            "he": self.curar,
            "hq": self.curar_porcentaje,
            "sh": self.escudo,
            "dr": self.robar,
            "q": self.ganar_qi,
            "eq": self.drenar_qi_rival,
            "A": self.ataque,
            "H": self.vida,
            "tk": self.provocar or None,
            "rs": self.impetu or None,
            "vm": self.robar_vida or None,
            "gr": self.crece,
            "k": self.es_espada or None,
            "rf": self.renovar,
            "fd": self.vacio_descarte,
            "cy": self.ciclo,
            "vb": self.abismo_traer,
            "vp": self.abismo_elegir or None,
            "vs": self.samsara,
            "dsp": self.disipa or None,
            "r": self.rareza_fija,
            "lk": self.reliquia or None,
            "bst": self.bestia or None,
            "pa": self.mejora_ataque_al_trazar,
            "ph": self.mejora_vida_al_trazar,
            "du": self.duracion_turnos,
        }
        for clave_js, valor in simples.items():
            if valor is not None:
                salida[clave_js] = valor
        if self.mejorar_aliada:
            mejora = self.mejorar_aliada
            salida["bf"] = [mejora.ataque, mejora.vida]
        if self.ultimo_aliento:
            aliento = self.ultimo_aliento
            salida["ul"] = [aliento.tipo.value, aliento.valor]
        if self.habilidad_activa:
            habilidad = self.habilidad_activa
            salida["ab"] = [
                habilidad.coste_qi,
                habilidad.tipo.value,
                habilidad.valor,
                habilidad.descripcion,
            ]
        if self.al_entrar:
            salida["bc"] = [self.al_entrar.tipo.value, self.al_entrar.valor]
        if self.efecto_inicio_turno:
            tipo_ts, valor_ts = self.efecto_inicio_turno
            salida["ts"] = [tipo_ts.value, valor_ts]
        return salida


@dataclass(frozen=True, slots=True)
class SectaData:
    """Secta jugable (`S[id]` en el JS).

    Atributos:
        identificador: clave corta (`'esp'`, `'lot'`…).
        nombre: nombre visible (`n`).
        descripcion: descripción de estilo (`i`).
        cartas_iniciales: las 5 cartas base del mazo (`l`).
    """

    identificador: str
    nombre: str
    descripcion: str
    cartas_iniciales: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PildoraData:
    """Píldora del catálogo (`PIL[id]` en el JS).

    Atributos:
        identificador: clave corta.
        nombre: nombre visible (`n`).
        coste: materiales para elaborarla (`c`); dict `Material → cantidad`.
        efecto: descripción del efecto (`t`).
        es_combate: True si es de bolsa de combate (flag `b`); las de
            inicio no llevan flag en el JS (ausencia = False).
        es_recuperación: True si es de la Cueva de Reclusión (flag `o`;
            añadidas con `Object.assign(PIL, …)` en `js/12-v47-init.js:60`).
        porcentaje_recuperacion: % de vida máxima que recupera (`rcv`);
            sólo relevante con `es_recuperación`.
    """

    identificador: str
    nombre: str
    coste: dict[Material, int]
    efecto: str
    es_combate: bool = False
    es_recuperacion: bool = False
    porcentaje_recuperacion: int | None = None


@dataclass(frozen=True, slots=True)
class DisenioTalisman:
    """Diseño de talismán fabricable (`DESIGN[id]` en el JS, v47+).

    Atributos:
        identificador: clave corta.
        nombre: nombre visible (`n`).
        coste: materiales para fabricarlo (`c`).
        efecto: descripción (`t`).
    """

    identificador: str
    nombre: str
    coste: dict[Material, int]
    efecto: str


@dataclass(frozen=True, slots=True)
class HabilidadEnemigo:
    """Habilidad pasiva de un enemigo (`RT[clave]` en el JS).

    Atributos:
        clave: clave corta (`'heal'`, `'regen'`…).
        texto: descripción mostrada en la ficha (`RT[clave]`).
    """

    clave: str
    texto: str


@dataclass(frozen=True, slots=True)
class CombateEnemigo:
    """Un combate del árbol de enemigos (entrada de `LV`/`DG`/`SQ`).

    Los campos `nombre_enemigo`, `secta`, `habilidades`, `frase_inicio`
    y `frase_derrota` vienen del array literal
    `[e, s, rl, i, x]` (y `[e, s, rl, i, x, rcp]` en mazmorras).

    Atributos:
        nombre_enemigo: nombre del oponente (`e`).
        secta: identificador de secta (arte/estilo; `s`).
        habilidades: claves de `TEXTO_HABILIDAD_ENEMIGO` (`rl`).
        frase_inicio: frase al presentarse (`i`).
        frase_derrota: frase al ser vencido (`x`).
        receta: píldora cuya receta revela este jefe de mazmorra (`rcp`).
    """

    nombre_enemigo: str
    secta: str
    habilidades: tuple[str, ...]
    frase_inicio: str
    frase_derrota: str
    receta: str | None = None


@dataclass(frozen=True, slots=True)
class NivelData:
    """Nivel principal de la campaña (`LV[i]` en el JS).

    Atributos:
        nombre: título del nivel (`n`).
        gradiente_color: par de colores hex para el fondo del nodo
            (`sky` = `[oscuro, claro]`).
        combates: los 6 enemigos del nivel, en orden.
    """

    nombre: str
    gradiente_color: tuple[str, str]
    combates: tuple[CombateEnemigo, ...]


@dataclass(frozen=True, slots=True)
class MazmorraData:
    """Mazmorra de recetas de alquimia (entrada de `DG` en el JS).

    Atributos:
        nombre: título (`n`).
        nivel: índice de nivel del que cuelga (`li`).
        indice_receta: rareza/índice de la receta que enseña (`u`);
            usado por el UI para mostrar la pista de la receta oculta.
        pista: texto de pista (`hint`).
        historia: texto narrativo de la mazmorra (`st`).
        jefes: los 3 combates de la mazmorra (`f`).
    """

    nombre: str
    nivel: int
    indice_receta: int
    pista: str
    historia: str
    jefes: tuple[CombateEnemigo, ...]


@dataclass(frozen=True, slots=True)
class RecompensaMision:
    """Recompensa de una misión secundaria (objeto `rw` de `SQ`).

    Atributos:
        piedras: piedras espirituales (`s`).
        hierbas: (`h`).
        nucleos: (`n`).
        polvo: polvo de jade (`p`).
        cartas: rareza de la carta gratuita (`card`).
        talisman_escape: nº de Talismanes de Escape (`tes`).
    """

    piedras: int = 0
    hierbas: int = 0
    nucleos: int = 0
    polvo: int = 0
    cartas: int | None = None
    talisman_escape: int = 0


@dataclass(frozen=True, slots=True)
class MisionSecundaria:
    """Misión secundaria por nivel (entrada de `SQ` en el JS).

    Atributos:
        nombre: título (`n`).
        pista: descripción corta (`hint`).
        historia: texto narrativo (`st`).
        recompensa: ver `RecompensaMision` (`rw`).
        fases: los 3 combates de la misión (`f`).
    """

    nombre: str
    pista: str
    historia: str
    recompensa: RecompensaMision
    fases: tuple[CombateEnemigo, ...]


@dataclass(frozen=True, slots=True)
class EnemigoCatalogo:
    """Enemigo aplanado del catálogo (`CH[k]` en el JS, calculado).

    Se construye al importar el módulo de niveles combinando `LV`,
    `DG` y `SQ` con las fórmulas de vida/capacidad/recompensa del JS.
    Los campos derivados se congelan aquí para que el motor de combate
    no tenga que recalcularlos.

    Atributos:
        nombre_enemigo: nombre del oponente (`e`).
        secta: secta/estilo (`s`).
        habilidades: claves de habilidad (`rl`).
        frase_inicio: (`i`).
        frase_derrota: (`x`).
        receta: píldora revelada, si es jefe de mazmorra (`rcp`).
        nombre_nivel: título del nivel/misión (`n`).
        historia: texto narrativo del nivel o mazmorra (`story`).
        indice_nivel: índice de nivel (`li`).
        dificultad: índice de dificultad 0–5 (`d`).
        indice_mazmorra: nº de mazmorra (1-based) o None (`dg`).
        indice_mision: nº de misión secundaria (1-based) o None (`sq`).
        fase_mision: fase dentro de la misión 0–2 o None (`sqf`).
        vida: vida calculada (`hp` = round(VIDA_BASE_NIVEL[li] * MULT_DIFICULTAD[d])).
        capacidad: criaturas máximas en tablero (`cap`).
        rareza_recompensa: rareza de recompensa (`rw`).
        texto_habilidades: descripción concatenada (`r`).
        es_emboscada: True si la ficha es una emboscada dinámica
            (`amb: 1` de `mkAmb`, js/06-contenido.js:207).
        es_boticario: True si es un boticario errante (`bot: 1` de
            `mkBot`, js/12-v47-init.js:84).
    """

    nombre_enemigo: str
    secta: str
    habilidades: tuple[str, ...]
    frase_inicio: str
    frase_derrota: str
    receta: str | None
    nombre_nivel: str
    historia: str | None
    indice_nivel: int
    dificultad: int
    indice_mazmorra: int | None
    indice_mision: int | None
    fase_mision: int | None
    vida: int
    capacidad: int
    rareza_recompensa: int
    texto_habilidades: str
    es_emboscada: bool = False
    es_boticario: bool = False


@dataclass(frozen=True, slots=True)
class FrasesCombate:
    """Frases del enemigo por situación (`SAY[secta]` en el JS).

    Atributos:
        ataque: frases al jugar una carta ofensiva (`a`).
        invocacion: frases al invocar una criatura (`s`).
        defensa: frases al jugar una carta defensiva (`d`).
        burla: frases al hablar sin efecto ofensivo ni criatura (`h`).
        criatura: frases al atacar con criatura (`c`).
        criatura_objetivo: frases al dañar una criatura con técnica (`t`;
            añadidas con `Object.assign` en el JS).
    """

    ataque: tuple[str, ...]
    invocacion: tuple[str, ...]
    defensa: tuple[str, ...]
    burla: tuple[str, ...]
    criatura: tuple[str, ...]
    criatura_objetivo: tuple[str, ...]
