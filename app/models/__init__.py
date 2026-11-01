from app.models.empleado import Empleado
from app.models.categoria import Categoria
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.orden_compra import OrdenCompra, DetalleOrdenCompra
from app.models.caja import Caja
from app.models.cliente_frecuente import ClienteFrecuente
from app.models.venta import Venta, DetalleVenta

__all__ = [
    "Empleado",
    "Categoria",
    "Proveedor",
    "Producto",
    "OrdenCompra",
    "DetalleOrdenCompra",
    "Caja",
    "ClienteFrecuente",
    "Venta",
    "DetalleVenta",
]
