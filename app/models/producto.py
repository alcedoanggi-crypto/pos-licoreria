from datetime import date, datetime

from flask import current_app

from app.extensions import db


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(40), unique=True, index=True)
    sku = db.Column(db.String(40), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    presentacion = db.Column(db.String(80))  # ej: "Botella 750ml"

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"))
    categoria = db.relationship("Categoria", back_populates="productos")

    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"))
    proveedor = db.relationship("Proveedor", back_populates="productos")

    precio_venta = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    costo = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    stock_actual = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=10)
    fecha_vencimiento = db.Column(db.Date)  # opcional: control de vencimiento por producto

    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def stock_bajo(self) -> bool:
        return self.stock_actual <= self.stock_minimo

    @property
    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - date.today()).days

    @property
    def proximo_a_vencer(self) -> bool:
        dias = self.dias_para_vencer
        if dias is None:
            return False
        umbral = current_app.config.get("VENCIMIENTO_ALERTA_DIAS", 30)
        return 0 <= dias <= umbral

    def __repr__(self) -> str:
        return f"<Producto {self.sku} {self.nombre}>"
