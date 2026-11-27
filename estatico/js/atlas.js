// Atlas: lectura del gráfico y filtros del catálogo. Sin dependencias.
(() => {
  const normalizar = (t) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  // Lectura: al señalar un cuadrado, muestra qué película es.
  const lectura = document.querySelector(".lectura");
  const grafico = document.querySelector(".grafico");
  const ayuda = lectura.innerHTML;
  const plantillaManchas = (n) => {
    const s = document.querySelector(`.filtro-valoracion button[data-v="${n}"] .manchas`);
    return s ? s.cloneNode(true) : document.createTextNode(`${n} de 5`);
  };
  const mostrar = (celda) => {
    lectura.textContent = "";
    const t = document.createElement("strong");
    t.textContent = celda.dataset.titulo;
    lectura.append(t, ` (${celda.dataset.anio})`, plantillaManchas(celda.dataset.v));
  };
  const celdas = [...document.querySelectorAll(".celda")];
  celdas.forEach((c) => {
    c.addEventListener("mouseenter", () => mostrar(c));
    c.addEventListener("focus", () => mostrar(c));
  });
  grafico.addEventListener("mouseleave", () => { lectura.innerHTML = ayuda; });
  grafico.addEventListener("focusout", (e) => { if (!grafico.contains(e.relatedTarget)) lectura.innerHTML = ayuda; });

  // Filtros: búsqueda por título y por valoración.
  const filas = [...document.querySelectorAll(".catalogo .fila")];
  const decadas = [...document.querySelectorAll(".catalogo .decada")];
  const buscar = document.getElementById("buscar");
  const botones = [...document.querySelectorAll(".filtro-valoracion button")];
  const recuento = document.querySelector(".recuento");
  const sinResultados = document.querySelector(".sin-resultados");

  const aplicar = () => {
    const q = normalizar(buscar.value.trim());
    const activas = botones.filter((b) => b.getAttribute("aria-pressed") === "true").map((b) => b.dataset.v);
    const visibles = new Set();
    filas.forEach((f) => {
      const ok = (!q || f.dataset.busca.includes(q)) && (!activas.length || activas.includes(f.dataset.v));
      f.hidden = !ok;
      if (ok) visibles.add(f.dataset.id);
    });
    const filtrando = Boolean(q || activas.length);
    decadas.forEach((d) => {
      const todas = d.querySelectorAll(".fila").length;
      const vis = d.querySelectorAll(".fila:not([hidden])").length;
      d.hidden = vis === 0;
      const total = d.querySelector(".decada-total");
      total.textContent = filtrando ? `${vis} de ${todas} películas` : `${todas} ${todas === 1 ? "película" : "películas"}`;
    });
    celdas.forEach((c) => c.classList.toggle("apagada", filtrando && !visibles.has(c.dataset.id)));
    const n = visibles.size;
    recuento.textContent = filtrando ? `${n} de ${filas.length} películas` : `${filas.length} películas`;
    sinResultados.hidden = n > 0;
  };

  buscar.addEventListener("input", aplicar);
  botones.forEach((b) => b.addEventListener("click", () => {
    b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") === "true" ? "false" : "true");
    aplicar();
  }));
})();
