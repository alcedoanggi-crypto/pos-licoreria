import enum
from datetime import datetime

from app.extensions import db


class MetodoPago(str, enum.Enum):
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    MIXTO = "mixto"


class EstadoVenta(str, enum.Enum):
    COMPLETADA = "completada"
    ANULADA = "anulada"


class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    numero_venta = db.Column(db.String(30), unique=True, nullable=False, index=True)

    caja_id = db.Column(db.Integer, db.ForeignKey("cajas.id"), nullable=False)
    caja = db.relationship("Caja", back_populates="ventas")

    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="ventas")

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes_frecuentes.id"))
    cliente = db.relationship("ClienteFrecuente", back_populates="ventas")

    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    impuesto = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    descuento_puntos = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    metodo_pago = db.Column(db.Enum(MetodoPago, name="metodo_pago"), nullable=False, default=MetodoPago.EFECTIVO)
    monto_recibido = db.Column(db.Numeric(12, 2), default=0)
    cambio = db.Column(db.Numeric(12, 2), default=0)

    puntos_otorgados = db.Column(db.Integer, nullable=False, default=0)
    puntos_canjeados = db.Column(db.Integer, nullable=False, default=0)

    edad_confirmada = db.Column(db.Boolean, nullable=False, default=False)  # alerta de mayoría de edad
    estado = db.Column(db.Enum(EstadoVenta, name="estado_venta"), nullable=False, default=EstadoVenta.COMPLETADA)

    detalles = db.relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Venta {self.numero_venta} ${self.total}>"


class DetalleVenta(db.Model):
    __tablename__ = "detalle_venta"

    id = db.Column(db.Integer, primary_key=True)

    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    venta = db.relationship("Venta", back_populates="detalles")

    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto")

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __repr__(self) -> str:
        return f"<DetalleVenta producto={self.producto_id} cant={self.cantidad}>"
