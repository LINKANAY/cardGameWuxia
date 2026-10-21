"""Árbol de enemigos — paridad con `LV`, `DG`, `SQ`, `RT`, `CH` de `js/01-datos.js`.

El catálogo aplanado `ENEMIGOS` se calcula al importar con exactamente
las mismas fórmulas que el JS:

- Vida:      ``hp = redondear_js(VIDA_BASE_NIVEL[li] * MULT_DIFICULTAD[d])``
- Capacidad: niveles ``[5,6,7,8,9,10][d]``; mazmorras ``[7,8,9][fase]``;
  misiones ``[6,7,8][fase]``.
- Rareza de recompensa:
  niveles ``min(5, floor(li*0.45) + ceil(d*0.6))``;
  misiones idem ``+ 1``.
- Texto de habilidades: ``'. '.join(RT[k] for k in rl) + '.'`` o
  ``'Sin habilidades.'`` si `rl` está vacío.

El orden de `ENEMIGOS` es el del JS: primero los 48 de niveles (por
nivel y dificultad), luego los de mazmorras, luego los de misiones
secundarias. El índice global es el que usan `wins`, `intro(k)` y el
guardado.
"""

from __future__ import annotations

import math

from .narrativa import (
    MULT_DIFICULTAD,
    VIDA_BASE_NIVEL,
    redondear_js,
)
from .tipos import (
    CombateEnemigo,
    EnemigoCatalogo,
    MazmorraData,
    MisionSecundaria,
    NivelData,
    RecompensaMision,
)

#: Texto de cada habilidad pasiva de enemigo (`RT` del JS).
TEXTO_HABILIDAD_ENEMIGO: dict[str, str] = {
    "heal": "Cura 2 al inicio de su turno",
    "regen": "Gana 4 de escudo cada turno",
    "drain": "Cada 3 turnos tu Qi máximo baja 1",
    "seal": "Cada 3 turnos pierdes 2 Qi el turno siguiente",
    "mist": "Cada 3 turnos devora una carta de tu mano",
    "blade": "Cada 2 turnos te hace 3 de daño directo",
    "breath": (
        "Cada 3 turnos Aliento Primordial: 5 de daño y cura 4"
    ),
}

# --- Niveles principales (`LV`) ---------------------------------------------

def _combate(
    nombre_enemigo: str,
    secta: str,
    *,
    habilidades: tuple[str, ...] = (),
    frase_inicio: str,
    frase_derrota: str,
    receta: str | None = None,
) -> CombateEnemigo:
    """Un combate del árbol de enemigos, con argumentos nombrados.

    Sustituye a las tuplas crudas ``[e, s, rl, i, x]`` del JS: el
    orden de lectura pasa a ser por nombre, así que añadir un campo
    nuevo (p. ej. `receta`) no obliga a recordar posiciones.

    Args:
        nombre_enemigo: nombre visible del oponente (`e`).
        secta: secta/estilo del arte del enemigo (`s`).
        habilidades: claves de pasivas (`rl`; `TEXTO_HABILIDAD_ENEMIGO`).
        frase_inicio: frase al presentarse (`i`).
        frase_derrota: frase al ser vencido (`x`).
        receta: receta que revela el jefe (sólo mazmorras; `rcp`).

    Returns:
        `CombateEnemigo` inmutable.
    """
    return CombateEnemigo(
        nombre_enemigo=nombre_enemigo,
        secta=secta,
        habilidades=tuple(habilidades),
        frase_inicio=frase_inicio,
        frase_derrota=frase_derrota,
        receta=receta,
    )


def _nivel(
    nombre: str,
    gradiente: tuple[str, str],
    combates: list[CombateEnemigo],
) -> NivelData:
    """Construye un nivel con sus 6 combates (ya convertidos)."""
    return NivelData(
        nombre=nombre,
        gradiente_color=gradiente,
        combates=tuple(combates),
    )


NIVELES: tuple[NivelData, ...] = (
    _nivel(
        "Nivel 1. La aldea mortal",
        ("#2b4a63", "#9fc7d8"),
        [
            _combate(
                "Aldeano Furioso",
                "esp",
                frase_inicio="¡Esa espada es de la aldea!",
                frase_derrota="Perdón... solo quería protegerla.",
            ),
            _combate(
                "Bandido de Montaña",
                "esp",
                frase_inicio="¡Entrega esa espada, chiquillo, o te la arranco!",
                frase_derrota="¡Maldita sea! Ese chico es un monstruo.",
            ),
            _combate(
                "Cazador de Recompensas",
                "bam",
                frase_inicio="Hay precio por la cabeza de quien carga esa espada.",
                frase_derrota="Cobra tú la recompensa, entonces.",
            ),
            _combate(
                "Discípulo Rival",
                "esp",
                habilidades=("heal",),
                frase_inicio=(
                    "Un leñador con espada celestial... esa gloria debía ser mía."
                ),
                frase_derrota="Entonces el Cielo te eligió a ti.",
            ),
            _combate(
                "Capitán de los Bandidos",
                "mon",
                habilidades=("blade",),
                frase_inicio="Mis hombres no fallan, muchacho.",
                frase_derrota="Retirada... ¡retirada!",
            ),
            _combate(
                "Hermano Mayor Rebelde",
                "esp",
                habilidades=("blade", "heal"),
                frase_inicio="Bai Heng me negó el Dao. Yo tomaré lo que me deba.",
                frase_derrota="Maestro, tenía razón. Perdóname.",
            ),
        ],
    ),
    _nivel(
        "Nivel 2. La prueba de la secta",
        ("#3b5a4a", "#cfe3c8"),
        [
            _combate(
                "Novicia del Loto",
                "pil",
                frase_inicio="Solo soy una novicia, pero no me rendiré.",
                frase_derrota="Qué fuerte eres. Pasa.",
            ),
            _combate(
                "Aprendiz del Loto",
                "lot",
                frase_inicio="Si quieres entrar a la secta, primero pasa por mí.",
                frase_derrota="Tu loto florece. Pasa.",
            ),
            _combate(
                "Jardinera Espiritual",
                "pil",
                habilidades=("heal",),
                frase_inicio="Mis flores sanan lo que tu espada corta.",
                frase_derrota="Marchitas incluso mis flores.",
            ),
            _combate(
                "Discípula del Loto Caído",
                "lot",
                habilidades=("heal",),
                frase_inicio=(
                    "El loto sangra cuando se le arranca de su estanque, mortal."
                ),
                frase_derrota="Tu Qi es limpio. Bai Heng eligió bien.",
            ),
            _combate(
                "Maestra de Pétalos",
                "bam",
                habilidades=("regen",),
                frase_inicio="Cada pétalo es una armadura.",
                frase_derrota="Mis pétalos... caen.",
            ),
            _combate(
                "Anciana de la Prueba",
                "mon",
                habilidades=("regen", "heal"),
                frase_inicio="Mil aspirantes cayeron aquí. Veamos si tú floreces.",
                frase_derrota="Has superado la prueba. La secta te acoge.",
            ),
        ],
    ),
    _nivel(
        "Nivel 3. El valle demoníaco",
        ("#3a1418", "#8a3a30"),
        [
            _combate(
                "Cultista Menor",
                "val",
                frase_inicio="Un mortal en nuestro valle... ¡qué festín!",
                frase_derrota="No... aún no debía morir.",
            ),
            _combate(
                "Cultivador Demoníaco",
                "val",
                frase_inicio="El Anciano pagará bien por tu espada y tu cabeza.",
                frase_derrota="El Anciano no me perdonará.",
            ),
            _combate(
                "Hechicero de Sangre",
                "val",
                habilidades=("drain",),
                frase_inicio="Tu Qi será mi alimento.",
                frase_derrota="Mi sangre... se seca.",
            ),
            _combate(
                "Maestro de Talismanes",
                "tal",
                habilidades=("seal",),
                frase_inicio="Cada sello que escribo es una jaula. Prueba la mía.",
                frase_derrota="Mis sellos, rotos como papel.",
            ),
            _combate(
                "Verdugo del Valle",
                "val",
                habilidades=("drain", "blade"),
                frase_inicio="El Anciano pidió tu cabeza intacta. No prometo nada.",
                frase_derrota="El valle me consume.",
            ),
            _combate(
                "Anciano Demoníaco",
                "val",
                habilidades=("drain", "heal"),
                frase_inicio="Esa espada ya sabe a sangre. Dámela y dejaré tu alma "
                    "intacta.",
                frase_derrota="La espada aún no me pertenecía. Aún.",
            ),
        ],
    ),
    _nivel(
        "Nivel 4. El palacio de las sombras",
        ("#1c1c46", "#6a5aa8"),
        [
            _combate(
                "Sombra Menor",
                "lun",
                frase_inicio="Solo soy un eco del miedo.",
                frase_derrota="El eco se apaga.",
            ),
            _combate(
                "Espectro Lunar",
                "lun",
                frase_inicio="Las sombras cuentan secretos a quien se atreve a "
                    "escucharlas.",
                frase_derrota="Vuelvo a las sombras.",
            ),
            _combate(
                "Doncella Espejo",
                "lun",
                habilidades=("mist",),
                frase_inicio="Mira mi espejo: verás lo que temes.",
                frase_derrota="Mi espejo se quiebra.",
            ),
            _combate(
                "Zorro de Mil Colas",
                "lun",
                habilidades=("mist",),
                frase_inicio="Cada cola esconde un engaño. ¿Cuál es tu verdad, "
                    "joven?",
                frase_derrota="Un buen engaño exige un buen ojo. Lo tienes.",
            ),
            _combate(
                "Guardiana de las Sombras",
                "lun",
                habilidades=("mist", "seal"),
                frase_inicio="Las sombras no se dejan atrapar.",
                frase_derrota="La luz me atraviesa...",
            ),
            _combate(
                "Emperatriz de los Mil Fantasmas",
                "lun",
                habilidades=("mist", "blade"),
                frase_inicio="Mil almas susurran tu nombre. Únete a ellas.",
                frase_derrota="Mil almas te observarán desde ahora.",
            ),
        ],
    ),
    _nivel(
        "Nivel 5. La tribulación celestial",
        ("#5a3a0a", "#f0c860"),
        [
            _combate(
                "Lagarto Espiritual",
                "dra",
                frase_inicio="Solo soy un lagarto, pero muerdo.",
                frase_derrota="Sss... huyo.",
            ),
            _combate(
                "Cría de Dragón Celestial",
                "dra",
                frase_inicio="¡Rugiré hasta que el cielo te rechace!",
                frase_derrota="¡Creceré y volveré más fuerte!",
            ),
            _combate(
                "Serpiente del Trueno",
                "tru",
                habilidades=("blade",),
                frase_inicio="El trueno me acompaña, mortal.",
                frase_derrota="Mi rayo se apaga.",
            ),
            _combate(
                "Rey Dragón",
                "dra",
                habilidades=("breath",),
                frase_inicio="Pocos sobreviven a mi aliento. Menos aún al rayo que "
                    "lo sigue.",
                frase_derrota="El rayo ya te reconoce, cultivador.",
            ),
            _combate(
                "Dragón Anciano",
                "dra",
                habilidades=("breath", "heal"),
                frase_inicio="Un milenio durmiendo, y vienes a despertarme.",
                frase_derrota="Vuelvo a dormir. Soñaré contigo.",
            ),
            _combate(
                "Inmortal Caído",
                "val",
                habilidades=("heal", "blade", "regen"),
                frase_inicio="Yo también fui discípulo de Bai Heng. Mira en lo que "
                    "me convirtió el Cielo.",
                frase_derrota="Si ves a Bai Heng, dile que no lo odio.",
            ),
        ],
    ),
    _nivel(
        "Nivel 6. El mar de nubes inmortal",
        ("#1e3b5a", "#a8d8f0"),
        [
            _combate(
                "Pez Celeste",
                "bam",
                frase_inicio="¡Glub! Las nubes son mi hogar.",
                frase_derrota="Glub... me voy nadando.",
            ),
            _combate(
                "Garza de las Nubes",
                "lot",
                frase_inicio="El Mar de Nubes no admite pasos pesados.",
                frase_derrota="Las nubes te dejan pasar.",
            ),
            _combate(
                "Hada del Viento",
                "tru",
                habilidades=("mist",),
                frase_inicio="El viento te lleva donde yo quiera.",
                frase_derrota="El viento cambia. Adiós.",
            ),
            _combate(
                "Guardián del Puente Celestial",
                "tal",
                habilidades=("seal", "heal"),
                frase_inicio="Nadie cruza sin pagar el peaje de su Qi.",
                frase_derrota="Puedes cruzar. El peaje está pagado.",
            ),
            _combate(
                "Inmortal Errante",
                "pil",
                habilidades=("mist", "heal"),
                frase_inicio="He cruzado este mar mil veces. ¿Y tú?",
                frase_derrota="Qué lástima, era un buen camino.",
            ),
            _combate(
                "Sabio del Mar de Nubes",
                "lun",
                habilidades=("mist", "regen", "seal"),
                frase_inicio="He visto caer a mil inmortales. Ninguno miró atrás.",
                frase_derrota="Interesante. Hacía siglos que nadie miraba atrás.",
            ),
        ],
    ),
    _nivel(
        "Nivel 7. El abismo de las mil espadas",
        ("#2a2a30", "#8a8f9a"),
        [
            _combate(
                "Espada Oxidada",
                "esp",
                frase_inicio="Oxidada, sí, pero aún corto.",
                frase_derrota="Me rompo. Descansa.",
            ),
            _combate(
                "Espada Errante",
                "esp",
                frase_inicio="Una hoja sin dueño busca un filo digno.",
                frase_derrota="Ahora conozco a mi dueño.",
            ),
            _combate(
                "Aprendiz del Filo",
                "tru",
                habilidades=("blade",),
                frase_inicio="Aprendí del mejor: de mí mismo.",
                frase_derrota="Debo entrenar más.",
            ),
            _combate(
                "Maestro del Filo Eterno",
                "esp",
                habilidades=("blade", "heal"),
                frase_inicio="Cien años afilé esta hoja esperándote.",
                frase_derrota="Cien años valieron este combate.",
            ),
            _combate(
                "Espadachín del Abismo",
                "esp",
                habilidades=("blade", "regen"),
                frase_inicio="El abismo me dio esta hoja. Toma su filo.",
                frase_derrota="El abismo me reclama.",
            ),
            _combate(
                "Rey de las Mil Espadas",
                "esp",
                habilidades=("blade", "regen", "heal"),
                frase_inicio="Tu espada es mi fragmento perdido. Devuélvemela.",
                frase_derrota="El fragmento y la espada vuelven a ser uno.",
            ),
        ],
    ),
    _nivel(
        "Nivel 8. El trono celestial",
        ("#3a2060", "#f0d890"),
        [
            _combate(
                "Sirviente Celestial",
                "mon",
                frase_inicio="El trono exige limpieza. Tú estás sucio.",
                frase_derrota="Perdón, mi señor...",
            ),
            _combate(
                "Guardia Celestial",
                "dra",
                frase_inicio="El trono no recibe visitas sin invitación.",
                frase_derrota="El trono es tuyo, si te atreves.",
            ),
            _combate(
                "Capitán de la Guardia",
                "mon",
                habilidades=("regen",),
                frase_inicio="Ningún mortal pasa mi lanza.",
                frase_derrota="Mi lanza se quiebra.",
            ),
            _combate(
                "Emperatriz Celestial",
                "lun",
                habilidades=("breath", "mist"),
                frase_inicio="Has llegado lejos, mortal. Demasiado lejos.",
                frase_derrota="El Cielo tiembla, pero aún queda el origen.",
            ),
            _combate(
                "General de las Nueve Nubes",
                "tru",
                habilidades=("breath", "blade", "heal"),
                frase_inicio="Nueve nubes, nueve rayos. ¿Cuántos resistirás?",
                frase_derrota="Ni los nueve rayos bastaron.",
            ),
            _combate(
                "Dao Primordial",
                "val",
                habilidades=("heal", "blade", "regen", "breath"),
                frase_inicio="Soy el origen de todo Qi. Soy lo que buscas y lo que "
                    "te destruirá.",
                frase_derrota="Eres el Dao. Ahora comprendo.",
            ),
        ],
    ),
)

# --- Mazmorras de alquimia (`DG`) -------------------------------------------
def _mazmorra(
    nombre: str,
    nivel: int,
    indice_receta: int,
    pista: str,
    historia: str,
    jefes: list[CombateEnemigo],
) -> MazmorraData:
    """Construye una mazmorra con sus 3 jefes (ya convertidos)."""
    return MazmorraData(
        nombre=nombre,
        nivel=nivel,
        indice_receta=indice_receta,
        pista=pista,
        historia=historia,
        jefes=tuple(jefes),
    )


MAZMORRAS: tuple[MazmorraData, ...] = (
    _mazmorra(
        "Cueva del Alquimista Olvidado",
        nivel=1,
        indice_receta=5,
        pista="Una cueva sin dueño donde un viejo alquimista dejó sus notas.",
        historia="Tras la prueba de la secta, Bai Heng habla de una cueva donde "
            "un alquimista desapareció dejando sus recetas. Lin Yu la "
            "encuentra sellada por hongos y vapor.",
        jefes=[
            _combate(
                "Murciélago de Hongo",
                "bam",
                habilidades=("heal",),
                frase_inicio="Chirrrr... el murciélago te observa con ojos brillantes.",
                frase_derrota="Chirr... se esconde entre los hongos.",
                receta="cla",
            ),
            _combate(
                "Gólem de Caldero",
                "mon",
                habilidades=("regen",),
                frase_inicio="Hierro y vapor: nadie toca mis calderos.",
                frase_derrota="El vapor se disipa y deja una nota antigua.",
                receta="esc",
            ),
            _combate(
                "Espíritu del Alquimista",
                "pil",
                habilidades=("heal", "seal"),
                frase_inicio="Cien años esperé a alguien digno de mis notas.",
                frase_derrota="Mis notas son tuyas. Haz buen uso de ellas.",
                receta="reg",
            ),
        ],
    ),
    _mazmorra(
        "Gruta de las Mil Hierbas",
        nivel=3,
        indice_receta=17,
        pista="Entre mil hierbas crece la receta que buscas.",
        historia="Un rumor habla de una gruta donde cada hierba guarda un "
            "secreto. Allí, las raíces se mueven como si respiraran.",
        jefes=[
            _combate(
                "Planta Carnívora",
                "bam",
                frase_inicio="¡Ñam! Tú hueles a Qi fresco.",
                frase_derrota="Mi savia... era para ti.",
                receta="dra",
            ),
            _combate(
                "Hada Venenosa",
                "lun",
                habilidades=("mist",),
                frase_inicio="Mis polvos curan... o matan. Tú elige.",
                frase_derrota="Qué cruel eres. Toma la receta.",
                receta="dsp",
            ),
            _combate(
                "Rey de los Hongos",
                "bam",
                habilidades=("regen", "heal"),
                frase_inicio="Todo lo que crece aquí me pertenece.",
                frase_derrota="El bosque de hongos se inclina ante ti.",
                receta="fur",
            ),
        ],
    ),
    _mazmorra(
        "Caldero del Abismo",
        nivel=5,
        indice_receta=29,
        pista="En el fondo de un caldero que nunca se apaga.",
        historia="En el abismo hierve un caldero eterno. Se dice que quien lo "
            "vence se lleva las recetas prohibidas de mil alquimistas.",
        jefes=[
            _combate(
                "Demonio del Vapor",
                "val",
                habilidades=("drain",),
                frase_inicio="Mi vapor sofoca a los mortales.",
                frase_derrota="El vapor se disipa. Solo queda una receta.",
                receta="ven",
            ),
            _combate(
                "Alquimista Corrupto",
                "tal",
                habilidades=("seal", "blade"),
                frase_inicio="Vendí mi alma por una fórmula. ¿Qué vendes tú?",
                frase_derrota="Mi fórmula... al menos no morirá conmigo.",
                receta="qi2",
            ),
            _combate(
                "Gran Caldero Viviente",
                "pil",
                habilidades=("regen", "heal", "blade"),
                frase_inicio="¡BLUB! El caldero despierta.",
                frase_derrota="El caldero se enfría y deja caer un pergamino.",
                receta="dr2",
            ),
        ],
    ),
    _mazmorra(
        "Santuario de la Inmortalidad",
        nivel=7,
        indice_receta=41,
        pista="Solo los dignos ven el santuario donde nace la inmortalidad.",
        historia="Más allá del Mar de Nubes se alza un santuario cuyas puertas "
            "solo se abren a quien domina el fuego y la medicina. Allí "
            "nació la primera píldora de inmortalidad.",
        jefes=[
            _combate(
                "Guardián de Jade",
                "mon",
                habilidades=("regen",),
                frase_inicio="Nadie roba las fórmulas del santuario.",
                frase_derrota="Las puertas ceden. Pasa, cultivador.",
                receta="tor",
            ),
            _combate(
                "Sabio del Elixir Eterno",
                "pil",
                habilidades=("heal", "mist"),
                frase_inicio="He bebido mil elixires y aún espero a un aprendiz.",
                frase_derrota="Un aprendiz digno, al fin.",
                receta="rar",
            ),
            _combate(
                "Inmortal Alquimista Primigenio",
                "tru",
                habilidades=("blade", "regen", "heal", "breath"),
                frase_inicio="Yo inventé la inmortalidad. ¿Quién te dio permiso "
                    "para buscarla?",
                frase_derrota="Así que la inmortalidad es tuya. Úsala bien.",
                receta="inm",
            ),
        ],
    ),
    _mazmorra(
        "Jardín de las Píldoras Celestiales",
        nivel=2,
        indice_receta=11,
        pista="Un jardín flotante donde las píldoras maduran como frutos.",
        historia="Entre las nubes flota un jardín donde las píldoras crecen en "
            "los árboles. Sus guardianes no regalan ni una hoja.",
        jefes=[
            _combate(
                "Abeja Dorada",
                "bam",
                frase_inicio="Bzzz... mi miel no es para mortales.",
                frase_derrota="Bzz... toma una receta y vete.",
                receta="cur",
            ),
            _combate(
                "Sacerdotisa del Jardín",
                "lot",
                habilidades=("heal",),
                frase_inicio="Cada fruto de este jardín lo cuidé yo.",
                frase_derrota="Cuídalo como yo lo hice.",
                receta="qiR",
            ),
            _combate(
                "Árbol Anciano de las Píldoras",
                "bam",
                habilidades=("regen", "heal"),
                frase_inicio="Mil años dando frutos, ¿y tú quieres mis hojas?",
                frase_derrota="Mis hojas son tuyas. Planta una semilla.",
                receta="pet",
            ),
        ],
    ),
    _mazmorra(
        "Cámara del Fuego Interior",
        nivel=4,
        indice_receta=23,
        pista="Donde el fuego no quema, sino que enseña.",
        historia="En lo profundo de la montaña arde un fuego que no consume. "
            "Dicen que quien lo domina puede encender su propio Qi en "
            "pleno combate.",
        jefes=[
            _combate(
                "Salamandra Ígnea",
                "dra",
                habilidades=("blade",),
                frase_inicio="¡Siente cómo arde mi fuego interior!",
                frase_derrota="El fuego se apaga. Aprende de él.",
                receta="fue",
            ),
            _combate(
                "Maestro del Horno Sagrado",
                "pil",
                habilidades=("heal", "regen"),
                frase_inicio="El horno exige paciencia, no prisa.",
                frase_derrota="Paciencia: eso fue lo que aprendiste.",
                receta="rob",
            ),
            _combate(
                "Fénix Alquimista",
                "dra",
                habilidades=("breath", "heal"),
                frase_inicio="Renazco cada vez que ardo.",
                frase_derrota="Renaces tú también, cultivador.",
                receta="cng",
            ),
        ],
    ),
)

# --- Misiones secundarias (`SQ`) --------------------------------------------
def _mision(
    nombre: str,
    pista: str,
    historia: str,
    recompensa: RecompensaMision,
    fases: list[CombateEnemigo],
) -> MisionSecundaria:
    """Construye una misión con sus 3 fases (ya convertidas)."""
    return MisionSecundaria(
        nombre=nombre,
        pista=pista,
        historia=historia,
        recompensa=recompensa,
        fases=tuple(fases),
    )


MISIONES_SECUNDARIAS: tuple[MisionSecundaria, ...] = (
    _mision(
        "El cargamento perdido",
        "Un mercader pide ayuda: unos bandidos le robaron su carga "
            "de hierbas.",
        "Un mercader herido espera al borde del camino. Dice que los "
            "bandidos escondieron su carga en un barranco cercano.",
        RecompensaMision(piedras=40, hierbas=4, polvo=3, cartas=2),
        [
            _combate(
                "Ladrón de Caminos",
                "esp",
                frase_inicio="¡Suelta esa bolsa, chiquillo!",
                frase_derrota="Mi cuchillo... se me cae.",
            ),
            _combate(
                "Mastín de la Banda",
                "mon",
                frase_inicio="¡Grrr! (el mastín custodia el botín).",
                frase_derrota="Aúlla y huye a la montaña.",
            ),
            _combate(
                "Líder de la Banda",
                "esp",
                habilidades=("blade",),
                frase_inicio="Nadie recupera lo que ya es mío.",
                frase_derrota="Llévate la carga y déjame en paz.",
            ),
        ],
    ),
    _mision(
        "Las pruebas ocultas",
        "Las discípulas guardan pruebas secretas que pocos conocen.",
        "Una discípula susurra que existen pruebas que la maestra "
            "nunca anuncia. Quien las supera gana su favor.",
        RecompensaMision(
            piedras=60, hierbas=5, nucleos=4, cartas=2
        ),
        [
            _combate(
                "Discípula Celosa",
                "lot",
                habilidades=("heal",),
                frase_inicio="Solo yo merezco el favor de la maestra.",
                frase_derrota="Quizá... me equivoqué contigo.",
            ),
            _combate(
                "Guardiana del Jardín",
                "lot",
                habilidades=("regen",),
                frase_inicio="Estas flores no se tocan.",
                frase_derrota="Pasa, pero con cuidado.",
            ),
            _combate(
                "Maestra de la Prueba Oculta",
                "lot",
                habilidades=("heal", "regen"),
                frase_inicio="¿Crees que superaste todo? Falta lo difícil.",
                frase_derrota="Has superado incluso la prueba oculta.",
            ),
        ],
    ),
    _mision(
        "La caravana demoníaca",
        "Una caravana del Valle transporta tesoros robados a los "
            "mortales.",
        "Entre las dunas rojas avanza una caravana que huele a azufre "
            "y a monedas. Sus guardianes no aceptan testigos.",
        RecompensaMision(piedras=80, nucleos=6, cartas=3),
        [
            _combate(
                "Mercader de Almas",
                "val",
                habilidades=("drain",),
                frase_inicio="Compra o muere, muchacho.",
                frase_derrota="Mis almas... se escapan.",
            ),
            _combate(
                "Escolta Sangrienta",
                "val",
                habilidades=("blade",),
                frase_inicio="¡Para proteger la caravana, todo vale!",
                frase_derrota="Cumplí... hasta aquí.",
            ),
            _combate(
                "Anciano de la Caravana",
                "val",
                habilidades=("blade", "drain"),
                frase_inicio="Mil años de comercio, ¿y me detiene un niño?",
                frase_derrota="Que el Valle te recuerde.",
            ),
        ],
    ),
    _mision(
        "Susurros en la sombra",
        "Algo en el palacio imita tu voz y roba tus recuerdos.",
        "Cada noche, una voz idéntica a la de Lin Yu recorre los "
            "pasillos del palacio. Nadie sabe qué busca.",
        RecompensaMision(piedras=100, hierbas=6, cartas=3),
        [
            _combate(
                "Sombra Curiosa",
                "lun",
                habilidades=("mist",),
                frase_inicio="Te veo... aunque tú no me veas.",
                frase_derrota="Me desvanezco en la bruma.",
            ),
            _combate(
                "Reflejo del Palacio",
                "lun",
                habilidades=("seal",),
                frase_inicio="Soy lo que ocultas.",
                frase_derrota="El espejo se quiebra.",
            ),
            _combate(
                "Dama de las Mil Sombras",
                "lun",
                habilidades=("mist", "seal"),
                frase_inicio="Las sombras guardan tus secretos.",
                frase_derrota="Las sombras... se apagan.",
            ),
        ],
    ),
    _mision(
        "Rayos olvidados",
        "Tres altares guardan rayos que ningún cielo reclamó.",
        "Tras la tribulación, quedan altares con rayos atrapados. Los "
            "cultivadores del trueno los custodian con celo.",
        RecompensaMision(
            piedras=120, nucleos=8, cartas=3, talisman_escape=1
        ),
        [
            _combate(
                "Discípulo del Trueno",
                "tru",
                frase_inicio="¡El rayo me eligió a mí!",
                frase_derrota="El rayo... me abandona.",
            ),
            _combate(
                "Monje Fulminado",
                "tru",
                habilidades=("regen",),
                frase_inicio="Soporté mil tribulaciones.",
                frase_derrota="Aún me quedan mil más.",
            ),
            _combate(
                "Heraldo de la Tormenta",
                "tru",
                habilidades=("breath",),
                frase_inicio="La tormenta no pide permiso.",
                frase_derrota="Que el cielo juzgue.",
            ),
        ],
    ),
    _mision(
        "El jardín flotante",
        "Sobre el mar de nubes flota un jardín que cura cualquier "
            "herida.",
        "Un jardín blanco flota entre las nubes. Dicen que sus raíces "
            "cuelgan de las estrellas y que tiene guardianes.",
        RecompensaMision(piedras=150, hierbas=8, cartas=4),
        [
            _combate(
                "Hada de las Nubes",
                "lot",
                habilidades=("heal",),
                frase_inicio="Este jardín no es para mortales.",
                frase_derrota="Las nubes te guiarán.",
            ),
            _combate(
                "Alquimista Celestial",
                "pil",
                habilidades=("regen", "heal"),
                frase_inicio="Cada hoja es un siglo de trabajo.",
                frase_derrota="Tómala, la ganaste.",
            ),
            _combate(
                "Guardián del Jardín Inmortal",
                "bam",
                habilidades=("regen", "breath"),
                frase_inicio="Las raíces te sujetan.",
                frase_derrota="Me arranco... y descanso.",
            ),
        ],
    ),
    _mision(
        "El cementerio de espadas",
        "Miles de espadas clavadas en la tierra aún recuerdan a sus "
            "dueños.",
        "En el abismo hay un cementerio donde cada espada es una tumba. "
            "Sus dueños no han terminado de morir.",
        RecompensaMision(
            piedras=190, nucleos=10, cartas=4, talisman_escape=1
        ),
        [
            _combate(
                "Espectro Errante",
                "esp",
                habilidades=("blade",),
                frase_inicio="Mi espada me espera.",
                frase_derrota="Por fin... descanso.",
            ),
            _combate(
                "Maestro Caído",
                "esp",
                habilidades=("blade", "heal"),
                frase_inicio="Mil espadas, ninguna digna.",
                frase_derrota="Esta sí lo era.",
            ),
            _combate(
                "Rey de las Mil Espadas",
                "esp",
                habilidades=("blade", "breath"),
                frase_inicio="Quien me venza heredará mi filo.",
                frase_derrota="El filo es tuyo, joven.",
            ),
        ],
    ),
    _mision(
        "Los jueces del trono",
        "Tres jueces examinan a quien aspira al trono celestial.",
        "Antes del trono, tres jueces del Cielo miden cada acto del "
            "aspirante. Ninguno ha sido vencido jamás.",
        RecompensaMision(
            piedras=250,
            hierbas=10,
            nucleos=12,
            cartas=5,
            talisman_escape=1,
        ),
        [
            _combate(
                "Juez del Trueno",
                "tru",
                habilidades=("breath",),
                frase_inicio="El Cielo mide tus actos.",
                frase_derrota="Tus actos pesan... a tu favor.",
            ),
            _combate(
                "Juez de la Luna",
                "lun",
                habilidades=("seal", "mist"),
                frase_inicio="El Cielo recuerda tus dudas.",
                frase_derrota="Dudas que superaste.",
            ),
            _combate(
                "Juez Supremo del Trono",
                "dra",
                habilidades=("breath", "heal", "blade"),
                frase_inicio="Aquí se decide quién asciende.",
                frase_derrota="Asciende, cultivador.",
            ),
        ],
    ),
)

# --- Catálogo aplanado (`CH`) -----------------------------------------------


def _texto_habilidades(habilidades: tuple[str, ...]) -> str:
    """Concatena el texto de habilidades (`r` en el JS)."""
    if not habilidades:
        return "Sin habilidades."
    return (
        ". ".join(TEXTO_HABILIDAD_ENEMIGO[clave] for clave in habilidades)
        + "."
    )


def _aplanar_nivel(
    indice_nivel: int,
    dificultad: int,
    combate: CombateEnemigo,
    nombre_nivel: str,
    historia: str | None,
) -> EnemigoCatalogo:
    """Construye un `EnemigoCatalogo` de nivel principal."""
    vida = redondear_js(
        VIDA_BASE_NIVEL[indice_nivel] * MULT_DIFICULTAD[dificultad]
    )
    capacidad = (5, 6, 7, 8, 9, 10)[dificultad]
    rareza = min(
        5,
        math.floor(indice_nivel * 0.45) + math.ceil(dificultad * 0.6),
    )
    return EnemigoCatalogo(
        nombre_enemigo=combate.nombre_enemigo,
        secta=combate.secta,
        habilidades=combate.habilidades,
        frase_inicio=combate.frase_inicio,
        frase_derrota=combate.frase_derrota,
        receta=combate.receta,
        nombre_nivel=nombre_nivel,
        historia=historia,
        indice_nivel=indice_nivel,
        dificultad=dificultad,
        indice_mazmorra=None,
        indice_mision=None,
        fase_mision=None,
        vida=vida,
        capacidad=capacidad,
        rareza_recompensa=rareza,
        texto_habilidades=_texto_habilidades(combate.habilidades),
    )


def _aplanar_mazmorra(
    indice_mazmorra: int,
    fase: int,
    combate: CombateEnemigo,
    mazmorra: MazmorraData,
) -> EnemigoCatalogo:
    """Construye un `EnemigoCatalogo` de mazmorra (`DG` del JS)."""
    dificultad = (3, 4, 5)[fase]
    vida = redondear_js(
        VIDA_BASE_NIVEL[mazmorra.nivel] * MULT_DIFICULTAD[dificultad]
    )
    capacidad = (7, 8, 9)[fase]
    rareza = min(
        5,
        math.floor(mazmorra.nivel * 0.45) + math.ceil(dificultad * 0.6),
    )
    return EnemigoCatalogo(
        nombre_enemigo=combate.nombre_enemigo,
        secta=combate.secta,
        habilidades=combate.habilidades,
        frase_inicio=combate.frase_inicio,
        frase_derrota=combate.frase_derrota,
        receta=combate.receta,
        nombre_nivel=mazmorra.nombre,
        historia=mazmorra.historia,
        indice_nivel=mazmorra.nivel,
        dificultad=dificultad,
        indice_mazmorra=indice_mazmorra + 1,
        indice_mision=None,
        fase_mision=None,
        vida=vida,
        capacidad=capacidad,
        rareza_recompensa=rareza,
        texto_habilidades=_texto_habilidades(combate.habilidades),
    )


def _aplanar_mision(
    indice_mision: int,
    fase: int,
    combate: CombateEnemigo,
    mision: MisionSecundaria,
) -> EnemigoCatalogo:
    """Construye un `EnemigoCatalogo` de misión secundaria (`SQ` del JS)."""
    dificultad = (2, 3, 4)[fase]
    vida = redondear_js(
        VIDA_BASE_NIVEL[indice_mision] * MULT_DIFICULTAD[dificultad]
    )
    capacidad = (6, 7, 8)[fase]
    rareza = min(
        5,
        math.floor(indice_mision * 0.45) + math.ceil(dificultad * 0.6) + 1,
    )
    return EnemigoCatalogo(
        nombre_enemigo=combate.nombre_enemigo,
        secta=combate.secta,
        habilidades=combate.habilidades,
        frase_inicio=combate.frase_inicio,
        frase_derrota=combate.frase_derrota,
        receta=combate.receta,
        nombre_nivel=mision.nombre,
        historia=mision.historia,
        indice_nivel=indice_mision,
        dificultad=dificultad,
        indice_mazmorra=None,
        indice_mision=indice_mision + 1,
        fase_mision=fase,
        vida=vida,
        capacidad=capacidad,
        rareza_recompensa=rareza,
        texto_habilidades=_texto_habilidades(combate.habilidades),
    )


def _construir_enemigos() -> tuple[EnemigoCatalogo, ...]:
    """Aplana niveles + mazmorras + misiones en el orden del JS (`CH`)."""
    enemigos: list[EnemigoCatalogo] = []
    for indice_nivel, nivel in enumerate(NIVELES):
        for dificultad, combate in enumerate(nivel.combates):
            enemigos.append(
                _aplanar_nivel(
                    indice_nivel, dificultad, combate, nivel.nombre, None
                )
            )
    for indice_mazmorra, mazmorra in enumerate(MAZMORRAS):
        for fase, jefe in enumerate(mazmorra.jefes):
            enemigos.append(
                _aplanar_mazmorra(indice_mazmorra, fase, jefe, mazmorra)
            )
    for indice_mision, mision in enumerate(MISIONES_SECUNDARIAS):
        for fase, combate in enumerate(mision.fases):
            enemigos.append(
                _aplanar_mision(indice_mision, fase, combate, mision)
            )
    return tuple(enemigos)


#: Catálogo aplanado de enemigos (índice global = índice de `wins`).
ENEMIGOS: tuple[EnemigoCatalogo, ...] = _construir_enemigos()

#: Nº de enemigos de niveles principales (índice donde empiezan mazmorras).
#: El JS lo llama `SQB` (`const SQB = CH.length` justo antes de push de SQ;
#: aquí es el offset tras mazmorras).
OFFSET_MISIONES_SECUNDARIAS: int = (
    len(NIVELES) * 6 + len(MAZMORRAS) * 3
)


def clave_mision_secundaria(indice_nivel: int, fase: int) -> int:
    """Índice global del combate de misión secundaria (`sqK` del JS).

    Args:
        indice_nivel: índice de nivel 0–7.
        fase: fase de la misión 0–2.

    Returns:
        Índice en `ENEMIGOS`.
    """
    return OFFSET_MISIONES_SECUNDARIAS + indice_nivel * 3 + fase
