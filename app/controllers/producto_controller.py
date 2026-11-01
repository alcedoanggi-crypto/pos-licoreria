from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Categoria, Producto, Proveedor
from app.utils.decorators import roles_requeridos
from app.utils.formularios import parsear_fecha

producto_bp = Blueprint("productos", __name__)


@producto_bp.route("/")
@login_required
def listar():
    busqueda = request.args.get("q", "").strip()
    filtro = request.args.get("filtro", "")

    query = Producto.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            (Producto.nombre.ilike(like)) | (Producto.sku.ilike(like)) | (Producto.codigo_barras.ilike(like))
        )

    productos = query.order_by(Producto.nombre).all()
    if filtro == "stock_bajo":
        productos = [p for p in productos if p.stock_bajo]
    elif filtro == "por_vencer":
        productos = [p for p in productos if p.proximo_a_vencer]

    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("productos/list.html", productos=productos, categorias=categorias, busqueda=busqueda, filtro=filtro)


@producto_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador", "supervisor")
def nuevo():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.razon_social).all()

    if request.method == "POST":
        producto = Producto(
            codigo_barras=request.form.get("codigo_barras", "").strip() or None,
            sku=request.form["sku"].strip(),
            nombre=request.form["nombre"].strip(),
            presentacion=request.form.get("presentacion", "").strip(),
            categoria_id=request.form.get("categoria_id", type=int) or None,
            proveedor_id=request.form.get("proveedor_id", type=int) or None,
            precio_venta=request.form.get("precio_venta", type=float) or 0,
            costo=request.form.get("costo", type=float) or 0,
            stock_actual=request.form.get("stock_actual", type=int) or 0,
            stock_minimo=request.form.get("stock_minimo", type=int) or 10,
            fecha_vencimiento=parsear_fecha(request.form.get("fecha_vencimiento")),
        )
        db.session.add(producto)
        db.session.commit()
        flash(f"Producto {producto.nombre} creado.", "success")
        return redirect(url_for("productos.listar"))

    return render_template("productos/form.html", producto=None, categorias=categorias, proveedores=proveedores)


@producto_bp.route("/<int:producto_id>/editar", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador", "supervisor")
def editar(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.razon_social).all()

    if request.method == "POST":
        producto.codigo_barras = request.form.get("codigo_barras", "").strip() or None
        producto.sku = request.form["sku"].strip()
        producto.nombre = request.form["nombre"].strip()
        producto.presentacion = request.form.get("presentacion", "").strip()
        producto.categoria_id = request.form.get("categoria_id", type=int) or None
        producto.proveedor_id = request.form.get("proveedor_id", type=int) or None
        producto.precio_venta = request.form.get("precio_venta", type=float) or 0
        producto.costo = request.form.get("costo", type=float) or 0
        producto.stock_actual = request.form.get("stock_actual", type=int) or 0
        producto.stock_minimo = request.form.get("stock_minimo", type=int) or 10
        producto.fecha_vencimiento = parsear_fecha(request.form.get("fecha_vencimiento"))
        producto.activo = bool(request.form.get("activo"))
        db.session.commit()
        flash(f"Producto {producto.nombre} actualizado.", "success")
        return redirect(url_for("productos.listar"))

    return render_template("productos/form.html", producto=producto, categorias=categorias, proveedores=proveedores)


@producto_bp.route("/categorias", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador", "supervisor")
def categorias():
    if request.method == "POST":
        categoria = Categoria(nombre=request.form["nombre"].strip(), descripcion=request.form.get("descripcion", "").strip())
        db.session.add(categoria)
        db.session.commit()
        flash(f"Categoría {categoria.nombre} creada.", "success")
        return redirect(url_for("productos.categorias"))

    todas = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("productos/categorias.html", categorias=todas)
