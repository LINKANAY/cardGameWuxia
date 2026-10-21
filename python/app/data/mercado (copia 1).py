"""Datos del Mercado del Sendero — paridad con `MK`/`SELL`/`MI`.

Fuente: `js/03-cartas-mercado.js:5-6` (puestos y precios de venta) y
`js/12-v47-init.js:132` (píldoras básicas de compra directa). El
catálogo es determinista: no hay rotación, stock ni RNG de ofertas.

Cada puesto (`MK[k]`) tiene nombre de NPC, frase y opcionalmente un
lote de material (`{n, m, q, c}`: nombre, material, cantidad, costo en
piedras). El puesto `neu` (General) no tiene lote propio pero sí las
secciones de venta de materiales, píldoras y talismanes.
"""

from __future__ import annotations

from dataclasses import dataclass

from .tipos import Material


@dataclass(frozen=True, slots=True)
class LoteMaterial:
    """Lote de material que vende un puesto de secta (`MK[k][2]`).

    Atributos:
        nombre: nombre visible del lote (`n`).
        material: clave del material que recibe el comprador (`m`).
        cantidad: unidades del material (`q`).
        costo: precio en piedras espirituales (`c`).
    """

    nombre: str
    material: Material
    cantidad: int
    costo: int


@dataclass(frozen=True, slots=True)
class PuestoMercado:
    """Puesto de mercado de una secta o el General (`MK[k]`).

    Atributos:
        identificador: clave de la secta o `'neu'` (General).
        vendedor: nombre del NPC (`MK[k][0]`).
        frase: frase del puesto (`MK[k][1]`).
        lote: material en venta, si el puesto lo tiene (`MK[k][2]`).
    """

    identificador: str
    vendedor: str
    frase: str
    lote: LoteMaterial | None = None


def _lote(
    nombre: str, material: Material, cantidad: int, costo: int
) -> LoteMaterial:
    return LoteMaterial(
        nombre=nombre, material=material, cantidad=cantidad, costo=costo
    )


#: Puestos del mercado (`MK` de `js/03-cartas-mercado.js:5`).
PUESTOS_MERCADO: dict[str, PuestoMercado] = {
    "esp": PuestoMercado(
        "esp",
        "Herrero Qiu",
        "Un filo sin dueño solo es hierro.",
        _lote("Limaduras de Espada", Material.POLVO_JADE, 3, 14),
    ),
    "lot": PuestoMercado(
        "lot",
        "Hermana Mei",
        "Toda flor tiene su precio, y su espina.",
        _lote("Pétalos de Loto", Material.HIERBAS, 3, 12),
    ),
    "tal": PuestoMercado(
        "tal",
        "Anciano Fu",
        "Papel, cinabrio y paciencia.",
        _lote("Papel de Talismán", Material.POLVO_JADE, 2, 10),
    ),
    "lun": PuestoMercado(
        "lun",
        "Dama Xue",
        "Compra a la luz de la luna; el sol miente.",
        _lote("Rocío Lunar", Material.HIERBAS, 2, 10),
    ),
    "val": PuestoMercado(
        "val",
        "Mercader Gui",
        "Aquí todo se paga. Con vida, si hace falta.",
        _lote("Colmillo Demoníaco", Material.NUCLEOS, 1, 28),
    ),
    "dra": PuestoMercado(
        "dra",
        "Maestro Long",
        "Las escamas no se regalan.",
        _lote("Escama de Dragón", Material.NUCLEOS, 1, 30),
    ),
    "mon": PuestoMercado(
        "mon",
        "Guardián Shan",
        "La montaña no se mueve; quien sube, sí.",
        _lote("Roca de la Montaña", Material.POLVO_JADE, 3, 14),
    ),
    "pil": PuestoMercado(
        "pil",
        "Boticaria Lan",
        "Cada hierba es una promesa; cada píldora, una deuda.",
        _lote("Hierbas del Pabellón", Material.HIERBAS, 4, 14),
    ),
    "tru": PuestoMercado(
        "tru",
        "Monje Lei",
        "El trueno no pregunta, golpea.",
        _lote("Fragmento de Rayo", Material.NUCLEOS, 1, 28),
    ),
    "bam": PuestoMercado(
        "bam",
        "Guardabosques Zhu",
        "El bambú se dobla, pero no se rompe.",
        _lote("Brotes de Bambú", Material.HIERBAS, 3, 11),
    ),
    "neu": PuestoMercado(
        "neu",
        "Pabellón de los Mil Caminos",
        "Todo cultivador necesita lo básico.",
    ),
}

#: Precio de venta de 1 unidad de material (`SELL` del JS).
PRECIO_VENTA_MATERIAL: dict[Material, int] = {
    Material.HIERBAS: 1,
    Material.POLVO_JADE: 2,
    Material.NUCLEOS: 8,
}

#: Clase de icono por material (`MI` del JS: herb/dust/core).
ICONO_MATERIAL: dict[Material, str] = {
    Material.HIERBAS: "herb",
    Material.POLVO_JADE: "dust",
    Material.NUCLEOS: "core",
}

#: Píldoras/talismanes siempre a la venta, aunque no se conozca su
#: receta (`MKC_BASIC` de `js/12-v47-init.js:132`). `inm`/`rar` nunca
#: se venden (los excluye `mkcList`).
PILDORAS_BASICAS_MERCADO: tuple[str, ...] = (
    "vit",
    "esc",
    "tes",
    "cur",
    "qiR",
    "pet",
    "tor",
    "dra",
)
