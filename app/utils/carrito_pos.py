"""Carrito de venta del POS, en sesión — se vacía al completar o cancelar la venta."""
from flask import session

from app.models import Producto

CLAVE_SESION = "pos_carrito"


def _carrito_crudo() -> dict:
    return session.setdefault(CLAVE_SESION, {})


def agregar_producto(producto_id: int, cantidad: int = 1) -> None:
    carrito = _carrito_crudo()
    clave = str(producto_id)
    carrito[clave] = carrito.get(clave, 0) + cantidad
    session[CLAVE_SESION] = carrito
    session.modified = True


def actualizar_cantidad(producto_id: int, cantidad: int) -> None:
    carrito = _carrito_crudo()
    clave = str(producto_id)
    if cantidad <= 0:
        carrito.pop(clave, None)
    else:
        carrito[clave] = cantidad
    session[CLAVE_SESION] = carrito
    session.modified = True


def eliminar_producto(producto_id: int) -> None:
    carrito = _carrito_crudo()
    carrito.pop(str(producto_id), None)
    session[CLAVE_SESION] = carrito
    session.modified = True


def vaciar_carrito() -> None:
    session[CLAVE_SESION] = {}
    session.modified = True


def contar_items() -> int:
    return sum(_carrito_crudo().values())


def obtener_items_detallados() -> list[dict]:
    carrito = _carrito_crudo()
    if not carrito:
        return []

    ids = [int(pid) for pid in carrito.keys()]
    productos = {p.id: p for p in Producto.query.filter(Producto.id.in_(ids)).all()}

    items = []
    for pid_str, cantidad in carrito.items():
        producto = productos.get(int(pid_str))
        if not producto or not producto.activo:
            continue
        items.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": float(producto.precio_venta) * cantidad,
            }
        )
    return items


def calcular_subtotal() -> float:
    return sum(item["subtotal"] for item in obtener_items_detallados())
