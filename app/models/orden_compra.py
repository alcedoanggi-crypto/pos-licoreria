import enum
from datetime import datetime

from app.extensions import db


class EstadoOrdenCompra(str, enum.Enum):
    PENDIENTE = "pendiente"
    RECIBIDA = "recibida"
    CANCELADA = "cancelada"


class OrdenCompra(db.Model):
    __tablename__ = "ordenes_compra"

    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.String(30), unique=True, nullable=False, index=True)

    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"), nullable=False)
    proveedor = db.relationship("Proveedor", back_populates="ordenes_compra")

    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado")

    estado = db.Column(db.Enum(EstadoOrdenCompra, name="estado_orden_compra"), nullable=False, default=EstadoOrdenCompra.PENDIENTE)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_recepcion = db.Column(db.DateTime)

    detalles = db.relationship("DetalleOrdenCompra", back_populates="orden", cascade="all, delete-orphan")

    @property
    def total(self):
        return sum(d.subtotal for d in self.detalles)

    def __repr__(self) -> str:
        return f"<OrdenCompra {self.numero_orden} {self.estado.value}>"


class DetalleOrdenCompra(db.Model):
    __tablename__ = "detalles_orden_compra"

    id = db.Column(db.Integer, primary_key=True)

    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_compra.id"), nullable=False)
    orden = db.relationship("OrdenCompra", back_populates="detalles")

    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto")

    cantidad = db.Column(db.Integer, nullable=False)
    costo_unitario = db.Column(db.Numeric(12, 2), nullable=False)

    @property
    def subtotal(self):
        return self.cantidad * self.costo_unitario
