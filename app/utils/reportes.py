import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

VINO_TINTO = colors.HexColor("#722F37")
DORADO = colors.HexColor("#C9A227")
GRAFITO = colors.HexColor("#2B2B2B")


def generar_pdf_cierre_diario(fecha, ventas, cajas, output_dir: str) -> str:
    """Genera el reporte de cierre diario en PDF: ventas del día + arqueo de cajas."""
    os.makedirs(output_dir, exist_ok=True)
    nombre_archivo = f"cierre-{fecha.isoformat()}.pdf"
    ruta_pdf = os.path.join(output_dir, nombre_archivo)

    doc = SimpleDocTemplate(ruta_pdf, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm)
    estilos = getSampleStyleSheet()
    titulo_estilo = ParagraphStyle("Titulo", parent=estilos["Heading1"], textColor=VINO_TINTO, fontSize=18)
    subtitulo_estilo = ParagraphStyle("Subtitulo", parent=estilos["Normal"], textColor=GRAFITO, fontSize=10)

    elementos = [
        Paragraph("Licorería — Reporte de Cierre Diario", titulo_estilo),
        Paragraph(f"Fecha: {fecha.strftime('%d/%m/%Y')}", subtitulo_estilo),
        Spacer(1, 0.6 * cm),
    ]

    total_dia = sum(float(v.total) for v in ventas)
    ticket_promedio = total_dia / len(ventas) if ventas else 0

    resumen = [
        ["Ventas totales del día:", f"${total_dia:,.2f}"],
        ["N° de ventas:", str(len(ventas))],
        ["Ticket promedio:", f"${ticket_promedio:,.2f}"],
    ]
    tabla_resumen = Table(resumen, colWidths=[8 * cm, 6 * cm])
    tabla_resumen.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (-1, -1), GRAFITO),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 0.7 * cm))

    elementos.append(Paragraph("Detalle de ventas", ParagraphStyle("H2", parent=estilos["Heading2"], textColor=VINO_TINTO, fontSize=13)))
    filas = [["N° Venta", "Hora", "Cajero", "Método", "Total"]]
    for v in ventas:
        filas.append([v.numero_venta, v.fecha.strftime("%H:%M"), v.empleado.nombre_completo, v.metodo_pago.value, f"${v.total:,.2f}"])

    tabla_ventas = Table(filas, colWidths=[3.5 * cm, 2.2 * cm, 5 * cm, 3 * cm, 3 * cm])
    tabla_ventas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), VINO_TINTO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ALIGN", (4, 0), (4, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF8F5")]),
            ]
        )
    )
    elementos.append(tabla_ventas)
    elementos.append(Spacer(1, 0.8 * cm))

    if cajas:
        elementos.append(Paragraph("Arqueo de cajas", ParagraphStyle("H2b", parent=estilos["Heading2"], textColor=VINO_TINTO, fontSize=13)))
        filas_cajas = [["Caja", "Cajero", "Apertura", "Sistema", "Contado", "Diferencia"]]
        for c in cajas:
            filas_cajas.append(
                [
                    c.nombre,
                    c.empleado.nombre_completo,
                    f"${c.monto_apertura:,.2f}",
                    f"${c.monto_sistema:,.2f}" if c.monto_sistema is not None else "-",
                    f"${c.monto_contado:,.2f}" if c.monto_contado is not None else "-",
                    f"${c.diferencia:,.2f}" if c.diferencia is not None else "-",
                ]
            )
        tabla_cajas = Table(filas_cajas, colWidths=[2.5 * cm, 4 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
        tabla_cajas.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), DORADO),
                    ("TEXTCOLOR", (0, 0), (-1, 0), GRAFITO),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ]
            )
        )
        elementos.append(tabla_cajas)

    doc.build(elementos)
    return ruta_pdf


def generar_excel_cierre_diario(fecha, ventas, output_dir: str) -> str:
    """Genera el reporte de cierre diario en Excel (detalle de ventas + productos vendidos)."""
    os.makedirs(output_dir, exist_ok=True)
    nombre_archivo = f"cierre-{fecha.isoformat()}.xlsx"
    ruta_excel = os.path.join(output_dir, nombre_archivo)

    wb = Workbook()
    ws_ventas = wb.active
    ws_ventas.title = "Ventas"

    relleno_encabezado = PatternFill(start_color="722F37", end_color="722F37", fill_type="solid")
    fuente_encabezado = Font(color="FFFFFF", bold=True)

    encabezados = ["N° Venta", "Fecha", "Hora", "Cajero", "Cliente", "Método de pago", "Subtotal", "Impuesto", "Total"]
    ws_ventas.append(encabezados)
    for celda in ws_ventas[1]:
        celda.fill = relleno_encabezado
        celda.font = fuente_encabezado

    for v in ventas:
        ws_ventas.append(
            [
                v.numero_venta,
                v.fecha.strftime("%d/%m/%Y"),
                v.fecha.strftime("%H:%M"),
                v.empleado.nombre_completo,
                v.cliente.nombre_completo if v.cliente else "-",
                v.metodo_pago.value,
                float(v.subtotal),
                float(v.impuesto),
                float(v.total),
            ]
        )

    for columna in ws_ventas.columns:
        longitud = max(len(str(celda.value)) for celda in columna if celda.value is not None)
        ws_ventas.column_dimensions[columna[0].column_letter].width = max(12, longitud + 2)

    ws_productos = wb.create_sheet("Productos vendidos")
    ws_productos.append(["Producto", "Cantidad", "Total"])
    for celda in ws_productos[1]:
        celda.fill = relleno_encabezado
        celda.font = fuente_encabezado

    resumen_productos: dict[str, list] = {}
    for v in ventas:
        for d in v.detalles:
            nombre = d.producto.nombre
            if nombre not in resumen_productos:
                resumen_productos[nombre] = [0, 0.0]
            resumen_productos[nombre][0] += d.cantidad
            resumen_productos[nombre][1] += float(d.subtotal)

    for nombre, (cantidad, total) in sorted(resumen_productos.items(), key=lambda x: x[1][1], reverse=True):
        ws_productos.append([nombre, cantidad, total])

    wb.save(ruta_excel)
    return ruta_excel
