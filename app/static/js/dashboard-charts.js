const PALETA = {
  vino: "#16263D",
  vinoClaro: "#8E2C48",
  dorado: "#E0A93B",
  doradoClaro: "#DDBB55",
  grafito: "#2B2B2B",
};

const COLORES_SERIE = [PALETA.vino, PALETA.dorado, PALETA.vinoClaro, PALETA.doradoClaro, "#4a3a1c", "#5c1f26", "#9c7a1f", "#b06a70"];

async function obtenerJSON(url) {
  const respuesta = await fetch(url);
  return respuesta.json();
}

function opcionesBase() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, grid: { color: "#eee8dc" } },
      x: { grid: { display: false } },
    },
  };
}

document.addEventListener("DOMContentLoaded", async () => {
  const ventasPeriodo = await obtenerJSON("/api/ventas-periodo");
  new Chart(document.getElementById("graficoVentasPeriodo"), {
    type: "line",
    data: {
      labels: ventasPeriodo.labels,
      datasets: [{
        data: ventasPeriodo.valores,
        borderColor: PALETA.vino,
        backgroundColor: "rgba(224,169,59,0.15)",
        fill: true,
        tension: 0.3,
        pointBackgroundColor: PALETA.dorado,
      }],
    },
    options: opcionesBase(),
  });

  const masVendidos = await obtenerJSON("/api/productos-mas-vendidos");
  new Chart(document.getElementById("graficoMasVendidos"), {
    type: "bar",
    data: { labels: masVendidos.labels, datasets: [{ data: masVendidos.valores, backgroundColor: PALETA.dorado, borderRadius: 4 }] },
    options: { ...opcionesBase(), indexAxis: "y" },
  });

  const horasPico = await obtenerJSON("/api/horas-pico");
  new Chart(document.getElementById("graficoHorasPico"), {
    type: "bar",
    data: { labels: horasPico.labels, datasets: [{ data: horasPico.valores, backgroundColor: PALETA.vino, borderRadius: 3 }] },
    options: opcionesBase(),
  });
});
