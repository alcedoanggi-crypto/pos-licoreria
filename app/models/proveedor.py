from datetime import datetime

from app.extensions import db


class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)
    razon_social = db.Column(db.String(150), nullable=False)
    contacto_nombre = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    email = db.Column(db.String(120))
    direccion = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    productos = db.relationship("Producto", back_populates="proveedor")
    ordenes_compra = db.relationship("OrdenCompra", back_populates="proveedor")

    def __repr__(self) -> str:
        return f"<Proveedor {self.razon_social}>"
