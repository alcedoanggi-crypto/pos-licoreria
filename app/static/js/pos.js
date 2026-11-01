let montoTexto = "";
let descuentoActual = 0;

function totalActual() {
  const subtotalNeto = Math.max(0, SUBTOTAL - descuentoActual);
  return subtotalNeto * (1 + IVA);
}

function actualizarTotalYCambio() {
  const total = totalActual();
  document.getElementById("total-venta").textContent = `$${total.toFixed(2)}`;

  const metodo = document.getElementById("metodo_pago").value;
  const recibido = parseFloat(montoTexto || "0") || 0;
  const cambioDiv = document.getElementById("cambio-venta");

  if (metodo === "tarjeta") {
    cambioDiv.textContent = "";
  } else {
    const cambio = recibido - total;
    cambioDiv.textContent = `Cambio: $${cambio >= 0 ? cambio.toFixed(2) : "0.00"}`;
    cambioDiv.style.color = cambio < 0 ? "#e0a0a0" : "";
  }
}

// ---------- Búsqueda de productos ----------
const inputBuscar = document.getElementById("input-buscar");
const resultadosDiv = document.getElementById("pos-resultados");
let temporizadorBusqueda = null;

async function agregarAlCarrito(productoId, cantidad = 1) {
  const datos = new FormData();
  datos.append("producto_id", productoId);
  datos.append("cantidad", cantidad);
  const respuesta = await fetch("/pos/carrito/agregar", { method: "POST", body: datos });
  const resultado = await respuesta.json();
  if (resultado.ok) {
    window.location.reload();
  } else {
    alert(resultado.mensaje || "No se pudo agregar el producto.");
  }
}

function mostrarResultados(productos) {
  if (!productos.length) {
    resultadosDiv.classList.add("d-none");
    resultadosDiv.innerHTML = "";
    return;
  }
  resultadosDiv.innerHTML = productos
    .map(
      (p) => `
      <div class="pos-resultado-item" data-id="${p.id}">
        <div>
          <strong>${p.nombre}</strong>
          <div class="small text-muted">${p.presentacion || ""} ${p.stock <= 0 ? '<span class="text-danger">· Sin stock</span>' : ""}</div>
        </div>
        <div class="text-end">
          <div class="fw-bold">$${p.precio.toFixed(2)}</div>
          <div class="small text-muted">Stock: ${p.stock}</div>
        </div>
      </div>`
    )
    .join("");
  resultadosDiv.classList.remove("d-none");

  resultadosDiv.querySelectorAll(".pos-resultado-item").forEach((el) => {
    el.addEventListener("click", () => agregarAlCarrito(el.dataset.id));
  });
}

inputBuscar?.addEventListener("input", () => {
  clearTimeout(temporizadorBusqueda);
  const q = inputBuscar.value.trim();
  if (!q) {
    mostrarResultados([]);
    return;
  }
  temporizadorBusqueda = setTimeout(async () => {
    const respuesta = await fetch(`/pos/buscar?q=${encodeURIComponent(q)}`);
    const productos = await respuesta.json();
    mostrarResultados(productos);
  }, 250);
});

inputBuscar?.addEventListener("keydown", async (evento) => {
  if (evento.key !== "Enter") return;
  evento.preventDefault();
  const q = inputBuscar.value.trim();
  if (!q) return;
  const respuesta = await fetch(`/pos/buscar?q=${encodeURIComponent(q)}`);
  const productos = await respuesta.json();
  if (productos.length === 1) {
    agregarAlCarrito(productos[0].id);
  } else {
    mostrarResultados(productos);
  }
});

document.addEventListener("click", (evento) => {
  if (!resultadosDiv?.contains(evento.target) && evento.target !== inputBuscar) {
    resultadosDiv?.classList.add("d-none");
  }
});

// ---------- Cantidad / eliminar en el carrito ----------
document.querySelectorAll(".input-cantidad-pos").forEach((input) => {
  input.addEventListener("change", async () => {
    const datos = new FormData();
    datos.append("producto_id", input.dataset.productoId);
    datos.append("cantidad", input.value);
    const respuesta = await fetch("/pos/carrito/actualizar", { method: "POST", body: datos });
    const resultado = await respuesta.json();
    if (resultado.ok) window.location.reload();
  });
});

document.querySelectorAll(".btn-quitar-pos").forEach((boton) => {
  boton.addEventListener("click", async () => {
    const datos = new FormData();
    datos.append("producto_id", boton.dataset.productoId);
    const respuesta = await fetch("/pos/carrito/eliminar", { method: "POST", body: datos });
    const resultado = await respuesta.json();
    if (resultado.ok) window.location.reload();
  });
});

document.getElementById("btn-vaciar-carrito")?.addEventListener("click", async () => {
  if (!confirm("¿Vaciar todo el carrito?")) return;
  await fetch("/pos/carrito/vaciar", { method: "POST" });
  window.location.reload();
});

// ---------- Cliente frecuente ----------
document.getElementById("btn-buscar-cliente")?.addEventListener("click", async () => {
  const telefono = document.getElementById("input-telefono-cliente").value.trim();
  if (!telefono) return;
  const respuesta = await fetch(`/pos/cliente-buscar?telefono=${encodeURIComponent(telefono)}`);
  const cliente = await respuesta.json();
  const infoDiv = document.getElementById("cliente-info");
  const bloquePuntos = document.getElementById("bloque-puntos");

  if (cliente) {
    infoDiv.innerHTML = `<span class="text-success"><i class="bi bi-check-circle"></i> ${cliente.nombre} — ${cliente.puntos} puntos disponibles</span>`;
    document.getElementById("cliente_id").value = cliente.id;
    bloquePuntos.classList.remove("d-none");
    document.getElementById("puntos_canjear").max = cliente.puntos;
  } else {
    infoDiv.innerHTML = '<span class="text-danger">Cliente no encontrado.</span>';
    document.getElementById("cliente_id").value = "";
    bloquePuntos.classList.add("d-none");
  }
});

document.getElementById("puntos_canjear")?.addEventListener("input", (evento) => {
  const puntos = parseInt(evento.target.value) || 0;
  descuentoActual = puntos * VALOR_PUNTO_DESCUENTO;
  actualizarTotalYCambio();
});

// ---------- Método de pago ----------
document.querySelectorAll(".metodo-pago-btn").forEach((boton) => {
  boton.addEventListener("click", () => {
    document.querySelectorAll(".metodo-pago-btn").forEach((b) => b.classList.remove("activo"));
    boton.classList.add("activo");
    const metodo = boton.dataset.metodo;
    document.getElementById("metodo_pago").value = metodo;

    const bloqueEfectivo = document.getElementById("bloque-efectivo");
    if (metodo === "tarjeta") {
      bloqueEfectivo.classList.add("d-none");
      montoTexto = totalActual().toFixed(2);
      document.getElementById("monto_recibido").value = montoTexto;
    } else {
      bloqueEfectivo.classList.remove("d-none");
    }
    actualizarTotalYCambio();
  });
});

// ---------- Teclado numérico ----------
document.querySelectorAll(".tecla").forEach((tecla) => {
  tecla.addEventListener("click", () => {
    const valor = tecla.dataset.tecla;
    if (valor === "borrar") {
      montoTexto = montoTexto.slice(0, -1);
    } else if (valor === "." && montoTexto.includes(".")) {
      // evita más de un punto decimal
    } else {
      montoTexto += valor;
    }
    document.getElementById("monto_recibido").value = montoTexto || "0.00";
    actualizarTotalYCambio();
  });
});

document.getElementById("form-venta")?.addEventListener("submit", () => {
  document.getElementById("monto_recibido").readOnly = false;
});

actualizarTotalYCambio();
