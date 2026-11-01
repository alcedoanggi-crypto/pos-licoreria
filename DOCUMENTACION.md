# Documentación técnica — POS Licorería

Documento de referencia del sistema: arquitectura, modelo de datos, reglas de
negocio implementadas, endpoints, seguridad y decisiones de diseño.
Complementa al `README.md` (que cubre solo instalación rápida).

---

## 1. Visión general

Sistema de punto de venta (POS) para una licorería boutique: venta rápida
tipo mostrador con búsqueda por código de barras/nombre, teclado numérico
táctil con cálculo automático de cambio, control de apertura/cierre de caja
con arqueo, inventario en tiempo real, programa de puntos para clientes
frecuentes, y reportes de cierre diario exportables a PDF/Excel.

**Stack:**

| Capa | Tecnología |
|---|---|
| Backend / controladores | Python 3 + Flask (Blueprints) |
| ORM / modelos | SQLAlchemy (Flask-SQLAlchemy) |
| Migraciones | Flask-Migrate (Alembic) |
| Base de datos | PostgreSQL |
| Autenticación | Flask-Login (roles cajero/supervisor/administrador) |
| Vistas | Jinja2 + Bootstrap 5 |
| Gráficos | Chart.js (dashboard) |
| Reportes | ReportLab (PDF) + openpyxl (Excel) |
| Carrito de venta | Sesión de Flask, actualizado por `fetch`/AJAX |

---

## 2. Arquitectura MVC y estructura de carpetas

```
pos-licoreria/
├── run.py                     # Punto de entrada
├── seed.py                    # Datos de ejemplo para desarrollo
├── config.py                  # Config (IVA, puntos, umbrales de alerta)
├── requirements.txt
├── .env.example
│
└── app/
    ├── __init__.py             # Application factory; inyecta a todas las
    │                             vistas el contador del carrito POS y la
    │                             caja abierta del empleado actual
    ├── extensions.py
    │
    ├── models/                  # (M)
    │   ├── empleado.py             Empleado + RolEmpleado (cajero/supervisor/admin)
    │   ├── categoria.py             Categoria
    │   ├── proveedor.py             Proveedor
    │   ├── producto.py               Producto (stock y vencimiento directos,
    │   │                               sin modelo de lotes — ver §4.7)
    │   ├── orden_compra.py            OrdenCompra + DetalleOrdenCompra
    │   ├── caja.py                     Caja (representa un TURNO: apertura → cierre)
    │   ├── cliente_frecuente.py          ClienteFrecuente (con puntos)
    │   └── venta.py                       Venta + DetalleVenta
    │
    ├── controllers/             # (C)
    │   ├── auth_controller.py       login/logout (cajero → POS, resto → dashboard)
    │   ├── pos_controller.py         pantalla de venta, búsqueda AJAX, carrito,
    │   │                              cliente frecuente, completar venta, recibo
    │   ├── caja_controller.py         abrir, cerrar (arqueo), historial, detalle
    │   ├── dashboard_controller.py    KPIs + 3 endpoints JSON para Chart.js
    │   ├── producto_controller.py     CRUD productos + categorías
    │   ├── proveedor_controller.py     CRUD proveedores + órdenes de compra
    │   ├── cliente_controller.py       CRUD clientes frecuentes
    │   ├── empleado_controller.py      CRUD empleados (solo admin)
    │   ├── reporte_controller.py       cierre diario (HTML/PDF/Excel)
    │   └── errores.py                  manejadores 401/403/404/500
    │
    ├── templates/                # (V)
    │   ├── base.html                layout con sidebar + indicador de caja
    │   ├── partials/                  sidebar.html, navbar.html, mensajes.html
    │   ├── auth/login.html
    │   ├── pos/                        pantalla.html (venta táctil), recibo.html
    │   ├── caja/                        abrir, cerrar, historial, detalle
    │   ├── dashboard/index.html
    │   ├── productos/, proveedores/, clientes/, empleados/, reportes/
    │   └── errors/
    │
    ├── static/
    │   ├── css/variables.css        paleta "boutique de vinos"
    │   ├── css/custom.css           layout POS táctil, teclado numérico,
    │   │                             alerta de edad, tarjetas KPI
    │   ├── js/pos.js                búsqueda, carrito, cliente, teclado, cambio
    │   └── js/dashboard-charts.js   fetch a /api/* + Chart.js
    │
    └── utils/
        ├── decorators.py            @roles_requeridos(*roles)
        ├── carrito_pos.py            carrito de venta en sesión
        ├── formularios.py            parsear_fecha()
        └── reportes.py                generar_pdf_cierre_diario(),
                                         generar_excel_cierre_diario()
```

---

## 3. Modelo de datos

### 3.1 Entidades y relaciones principales

- **Empleado** `1 -- N` **Caja** (turnos que ha abierto)
- **Empleado** `1 -- N` **Venta** (ventas que ha procesado)
- **Categoria** `1 -- N` **Producto**
- **Proveedor** `1 -- N` **Producto**, **Proveedor** `1 -- N` **OrdenCompra**
- **OrdenCompra** `1 -- N` **DetalleOrdenCompra**
- **Caja** `1 -- N` **Venta** (todas las ventas del turno)
- **ClienteFrecuente** `1 -- N` **Venta** (opcional — una venta puede no
  tener cliente asociado)
- **Venta** `1 -- N` **DetalleVenta**

### 3.2 Enums de estado

| Enum | Valores | Dónde vive |
|---|---|---|
| `RolEmpleado` | cajero, supervisor, administrador | `empleado.py` |
| `EstadoOrdenCompra` | pendiente, recibida, cancelada | `orden_compra.py` |
| `EstadoCaja` | abierta, cerrada | `caja.py` |
| `MetodoPago` | efectivo, tarjeta, mixto | `venta.py` |
| `EstadoVenta` | completada, anulada | `venta.py` |

### 3.3 Decisión de diseño: stock directo en `Producto`, sin modelo de lotes

A diferencia del proyecto "Distribuidora de Licores" (que sí necesita
trazabilidad por lote para venta mayorista), este POS es de venta al detalle
rápida: `Producto.stock_actual` es un contador simple que se descuenta en
cada venta y se incrementa al recibir una orden de compra.
`Producto.fecha_vencimiento` es un campo único opcional (no una lista de
lotes con fechas distintas) — suficiente para la alerta "productos próximos
a vencer" que pide el enunciado, sin la complejidad de un sistema
multi-lote que el flujo de POS no necesita.

### 3.4 Propiedades calculadas (no columnas)

- `Producto.stock_bajo` → `stock_actual <= stock_minimo`.
- `Producto.dias_para_vencer` / `proximo_a_vencer` → derivado de
  `fecha_vencimiento` comparado con `date.today()` y el umbral
  `VENCIMIENTO_ALERTA_DIAS` de `config.py`.
- `Caja.total_ventas_efectivo` / `total_ventas` → suman `Venta.total` de las
  ventas completadas del turno (convertido explícitamente a `float`, ver
  nota en §9 sobre el bug de tipos corregido).
- `OrdenCompra.total` → suma de `DetalleOrdenCompra.subtotal`.
- `DetalleVenta.subtotal` / `DetalleOrdenCompra.subtotal` → cantidad × precio/costo.

---

## 4. Reglas de negocio clave

### 4.1 Apertura y cierre de caja (arqueo)

`Caja` no representa una terminal física, sino **un turno**: se abre con un
monto de efectivo inicial (`monto_apertura`) y se cierra con un arqueo.

- **Abrir** (`caja_controller.abrir`): un empleado no puede tener dos cajas
  abiertas a la vez — se verifica antes de crear una nueva.
- **Vender**: `pos_controller` exige una caja abierta del empleado actual
  para acceder a `/pos/` o completar una venta; si no hay, redirige a abrir
  caja.
- **Cerrar** (`caja_controller.cerrar`): calcula
  `monto_sistema = monto_apertura + total_ventas_efectivo` (solo ventas en
  efectivo cuentan para el arqueo de caja física; tarjeta no mueve
  efectivo). El cajero ingresa `monto_contado` (lo que hay físicamente en
  caja) y el sistema calcula `diferencia = contado − sistema`, mostrando en
  vivo (JS) si sobra, falta o cuadra exacto antes de confirmar.

### 4.2 Venta rápida y cálculo de cambio

El carrito de venta vive en `flask.session` (`app/utils/carrito_pos.py`),
igual que en LicoresPremium — no ensucia la base de datos con carritos
abandonados y funciona sin fricción para el flujo rápido de mostrador.

- **Búsqueda** (`pos.buscar`): si el término coincide **exacto** con un
  `codigo_barras`, se prioriza ese resultado (así una pistola lectora que
  envía el código completo + Enter agrega el producto directo, sin mostrar
  una lista). Si no, busca por coincidencia parcial en nombre/SKU/código.
- **Cambio automático**: el teclado numérico táctil (`static/js/pos.js`)
  construye el monto recibido dígito por dígito y **recalcula el cambio en
  el navegador** en cada tecla, usando el subtotal ya renderizado por el
  servidor (`SUBTOTAL`, `IVA`, `VALOR_PUNTO_DESCUENTO` como constantes JS
  inyectadas en la plantilla) — no hay ida y vuelta al servidor para la
  vista previa, solo al confirmar la venta.
- **Validación de stock**: al completar la venta, se revisa que
  `producto.stock_actual >= cantidad` para cada línea antes de tocar la
  base de datos; si falta stock de cualquier producto, no se crea la venta.

### 4.3 Alerta de mayoría de edad

El checkbox "Confirmo que el cliente es mayor de 18 años" (`.alerta-edad`
en `pos/pantalla.html`) es `required` en el HTML **y** se revalida en el
backend: `pos_controller.completar_venta` rechaza la venta con un mensaje
flash si `edad_confirmada` no llega en el POST, sin importar si el HTML fue
manipulado. No hay forma de completar una venta sin ese campo.

### 4.4 Programa de puntos de clientes frecuentes

- **Acumulación**: al completar una venta con un cliente asociado, se
  otorgan `int(total * PUNTOS_POR_DOLAR)` puntos (configurable, 1 punto por
  dólar por defecto).
- **Canje**: el cajero puede indicar cuántos puntos canjear
  (`puntos_canjear`); el backend limita el canje al mínimo entre lo pedido
  y los puntos que el cliente realmente tiene (`min(puntos_canjear,
  cliente.puntos)`), y aplica `puntos_canjear * VALOR_PUNTO_DESCUENTO` como
  descuento **antes** de calcular el IVA (`subtotal_neto = subtotal −
  descuento_puntos`).
- Los puntos del cliente se actualizan en una sola operación:
  `cliente.puntos = cliente.puntos - puntos_canjeados + puntos_otorgados`.

### 4.5 Órdenes de compra y recepción

Una orden de compra nace en estado `pendiente`. Solo al marcarla como
**recibida** (`proveedores.ordenes_recibir`) se suma el stock: se recorre
cada `DetalleOrdenCompra` y se incrementa `producto.stock_actual` en la
cantidad pedida, además de actualizar `producto.costo` al costo unitario de
esa orden. Una orden ya recibida o cancelada no se puede volver a procesar
(se valida el estado antes de aplicar cambios).

### 4.6 Reportes de cierre diario (PDF / Excel)

`app/utils/reportes.py` genera ambos formatos a partir del mismo conjunto
de ventas/cajas del día (`reporte_controller._ventas_y_cajas_del_dia`):

- **PDF** (ReportLab): resumen (total del día, N° de ventas, ticket
  promedio), tabla de ventas y tabla de arqueo de cajas, en los colores de
  la paleta (vino tinto / dorado).
- **Excel** (openpyxl): una hoja "Ventas" con el detalle transaccional
  completo y una hoja "Productos vendidos" con el consumo agregado por
  producto (cantidad y total), ordenada de mayor a menor venta — útil para
  análisis que el PDF no muestra.

### 4.7 Alertas de inventario

Dos alertas independientes, visibles en `/productos` (filtro) y en el
dashboard:

- **Stock bajo**: `stock_actual <= stock_minimo`, configurable por
  producto (`stock_minimo`), con default `STOCK_MINIMO_DEFAULT` en
  `config.py`.
- **Próximo a vencer**: productos con `fecha_vencimiento` dentro de los
  próximos `VENCIMIENTO_ALERTA_DIAS` (30 por defecto) — ya vencidos
  (`dias < 0`) no se muestran como "próximos a vencer" sino que deberían
  tratarse aparte operativamente (el modelo expone `dias_para_vencer`
  negativo para que la vista pueda distinguirlo si se necesita).

---

## 5. Roles y control de acceso

Tres roles (`RolEmpleado`): `cajero`, `supervisor`, `administrador`.
Implementado con Flask-Login + el decorador `@roles_requeridos(*roles)` en
`app/utils/decorators.py` (401 sin sesión, 403 si el rol no aplica).

| Acción | Roles permitidos |
|---|---|
| Vender en el POS, abrir/cerrar su propia caja | cualquier empleado autenticado |
| Ver dashboard, clientes frecuentes | cualquier empleado autenticado |
| Crear/editar producto, categorías | administrador, supervisor |
| Crear/editar proveedor, empleados | administrador |
| Crear orden de compra / recibirla | administrador, supervisor |
| Ver historial de cajas de **todos** los empleados | administrador, supervisor (un cajero solo ve las suyas — verificado en `caja.detalle`) |
| Ver/exportar cierre diario | administrador, supervisor |

Al hacer login, un `cajero` es enviado directo a `/pos/` (su pantalla de
trabajo); supervisor y administrador van al `/dashboard`.

---

## 6. Endpoints principales

| Blueprint | Prefijo | Rutas clave |
|---|---|---|
| `auth` | — | `GET/POST /login`, `GET /logout` |
| `pos` | `/pos` | `GET /`, `GET /buscar`, `POST /carrito/agregar\|actualizar\|eliminar\|vaciar`, `GET /cliente-buscar`, `POST /venta/completar`, `GET /venta/<id>/recibo` |
| `caja` | `/caja` | `GET/POST /abrir`, `GET/POST /cerrar`, `GET /historial`, `GET /<id>` |
| `dashboard` | `/` | `GET /`, `GET /api/ventas-periodo`, `GET /api/productos-mas-vendidos`, `GET /api/horas-pico` |
| `productos` | `/productos` | listar, nuevo, `<id>/editar`, `GET/POST /categorias` |
| `proveedores` | `/proveedores` | listar, nuevo, `<id>/editar`, `/ordenes-compra` (listar/nueva/detalle/recibir) |
| `clientes` | `/clientes` | listar, nuevo, `<id>` (detalle), `<id>/editar` |
| `empleados` | `/empleados` | listar, nuevo, `<id>/editar` (solo admin) |
| `reportes` | `/reportes` | `/cierre-diario` (HTML), `/cierre-diario/pdf`, `/cierre-diario/excel` |

En total **41 rutas** registradas (verificado con `app.url_map`).

---

## 7. Diseño UI/UX

Paleta en `app/static/css/variables.css`:

| Variable | Hex | Uso |
|---|---|---|
| `--vino-tinto` | `#722F37` | Sidebar, encabezados, botón primario |
| `--grafito` | `#2B2B2B` | Caja de total de la venta, texto principal |
| `--dorado` | `#C9A227` | Acentos, botón "Completar venta", bordes de KPI |
| `--blanco-calido` | `#FAF8F5` | Fondo general |

Piezas específicas del pedido:

- **`.pos-layout`**: pantalla de venta a dos columnas — carrito (izquierda,
  ocupa el espacio disponible) y panel de pago (derecha, ancho fijo) — para
  uso en tablet apaisada de mostrador.
- **`.teclado-numerico` / `.tecla`**: grilla 3×4 de botones grandes
  (`padding: 0.9rem`, `font-size: 1.4rem`) con feedback táctil
  (`:active { transform: scale(0.96) }`).
- **`.alerta-edad`**: caja con fondo degradado cálido y borde rojo sólido de
  2px — diseñada para ser imposible de pasar por alto antes de vender.
- **`.metodo-pago-btn`**: botones grandes de método de pago con estado
  `.activo` resaltado en vino tinto.
- **`.pos-total-box`**: fondo grafito con el monto en dorado, tipografía
  grande (2.2rem) — el número que más importa en la pantalla.

---

## 8. Seguridad y límites conocidos

- **CSRF**: no se usa `Flask-WTF` con `{{ form.csrf_token }}` en los
  formularios — pendiente antes de producción, igual que en los otros
  proyectos de esta serie.
- **Contraseñas**: hasheadas con `werkzeug.security`.
- **PIN rápido** (`Empleado.pin`): se guarda en texto plano (no hasheado)
  porque está pensado como una confirmación secundaria de 4 dígitos en el
  mostrador, no como credencial de autenticación completa — **no
  reemplaza** el login por email/contraseña. Actualmente el campo existe en
  el modelo y el formulario de empleados, pero ninguna vista lo exige aún
  (queda como punto de extensión, por ejemplo para un "bloqueo rápido" de
  pantalla entre cajeros del mismo turno).
- Sin paginación en listados, sin tests automatizados — mismos límites de
  alcance que el resto de scaffolds de esta serie.

---

## 9. Validación realizada

Antes de entregar el proyecto se corrió (con un venv temporal, luego
eliminado):

1. `python -m py_compile` sobre todo `app/` + `config.py`/`run.py`/`seed.py`
   → sin errores de sintaxis.
2. `create_app()` + inspección de `app.url_map` → 9 blueprints, 41 rutas,
   sin errores de import.
3. **Flujo completo** vía `test_client`: login como cajero → `/pos/` sin
   caja abierta redirige correctamente a `/caja/abrir` → abrir caja →
   buscar producto por código de barras exacto → agregar al carrito →
   buscar cliente frecuente por teléfono → **intentar completar la venta
   sin marcar la edad confirmada → se verificó que la venta NO se crea**
   (0 ventas en BD) → completar la venta con edad confirmada + canje de 20
   puntos → verificado que el total, el descuento por puntos, el stock
   descontado y los puntos actualizados del cliente son matemáticamente
   correctos → ver recibo → cerrar caja con arqueo exacto (verificado
   `diferencia = 0.00`) → dashboard y los 3 endpoints JSON de gráficos como
   administrador → reporte de cierre diario en HTML, PDF (verificado
   `content-type: application/pdf`) y Excel (verificado `content-type`
   `.xlsx`) → crear orden de compra → recibirla → **verificado que el
   stock del producto se incrementó exactamente en la cantidad de la
   orden**. Todo pasó sin errores 500 en la segunda corrida.
4. Durante la primera corrida se detectó y corrigió un bug real: las
   propiedades `Caja.total_ventas_efectivo` y `Caja.total_ventas` sumaban
   valores `Decimal` (columnas `Numeric` de SQLAlchemy) y
   `caja_controller.cerrar` intentaba sumarlos con un `float` de Python
   (`float(caja.monto_apertura) + caja.total_ventas_efectivo`), lo que
   lanzaba `TypeError: unsupported operand type(s) for +: 'float' and
   'decimal.Decimal'` y tumbaba la pantalla de cierre de caja con un 500.
   Se corrigió convirtiendo explícitamente a `float` dentro de las
   propiedades del modelo `Caja` (`app/models/caja.py`), no solo en el
   controlador, para que cualquier otro consumidor futuro de esas
   propiedades no repita el mismo error.
5. Se usó `psycopg[binary]` (v3) en vez de `psycopg2-binary` en
   `requirements.txt`, mismo motivo que en los proyectos anteriores de esta
   serie (sin wheel de psycopg2 para Python 3.14 en Windows sin compilador
   C).

---

## 10. Cómo correrlo (resumen — detalle en README.md)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
createdb pos_licoreria                # en PostgreSQL
copy .env.example .env                # y completar DATABASE_URL / SECRET_KEY

flask --app run.py db init
flask --app run.py db migrate -m "Esquema inicial"
flask --app run.py db upgrade

python seed.py                        # empleados, productos, clientes de ejemplo
flask --app run.py run --debug        # http://localhost:5000
```
