from app.extensions import db


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))

    productos = db.relationship("Producto", back_populates="categoria")

    def __repr__(self) -> str:
        return f"<Categoria {self.nombre}>"
