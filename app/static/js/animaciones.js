// Animaciones de presentación: contadores en los KPI y revelado al hacer scroll.
(function () {
  const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Cuenta desde 0 hasta el valor mostrado, respetando prefijo ($) y decimales.
  function animarContador(el) {
    const texto = el.textContent.trim();
    const coincidencia = texto.match(/^([^\d-]*)(-?[\d,]+(?:\.\d+)?)(.*)$/);
    if (!coincidencia) return;
    const [, prefijo, numero, sufijo] = coincidencia;
    const objetivo = parseFloat(numero.replace(/,/g, ""));
    if (!isFinite(objetivo) || objetivo === 0) return;
    const decimales = (numero.split(".")[1] || "").length;
    const conComas = numero.includes(",");
    const formato = (v) => {
      const fijo = v.toFixed(decimales);
      return conComas ? Number(fijo).toLocaleString("en-US", { minimumFractionDigits: decimales, maximumFractionDigits: decimales }) : fijo;
    };
    const duracion = 1200;
    const inicio = performance.now();
    function paso(ahora) {
      const t = Math.min((ahora - inicio) / duracion, 1);
      const suave = 1 - Math.pow(1 - t, 3);
      el.textContent = prefijo + formato(objetivo * suave) + sufijo;
      if (t < 1) requestAnimationFrame(paso);
    }
    requestAnimationFrame(paso);
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (reducir) return;
    document.querySelectorAll(".kpi-value, .kpi-valor, [data-contador]").forEach(animarContador);

    const objetivos = document.querySelectorAll(".panel, .panel-admin, .revelar-auto");
    if (!("IntersectionObserver" in window)) return;
    const observador = new IntersectionObserver((entradas) => {
      entradas.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("visible"); observador.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    objetivos.forEach((el, i) => {
      el.classList.add("revelar");
      el.style.transitionDelay = (i % 3) * 0.08 + "s";
      observador.observe(el);
    });
  });
})();
