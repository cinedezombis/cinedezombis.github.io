// Últimas reseñas: marca como «Nueva» la que se publicó hace menos de 30 días
(() => {
  const hoy = new Date();
  document.querySelectorAll(".ultima[data-publicado]").forEach((li) => {
    const f = new Date(li.dataset.publicado + "T12:00:00");
    if (!isNaN(f) && (hoy - f) / 86400000 <= 30) {
      const t = li.querySelector(".ultima-fecha");
      t.insertAdjacentHTML("afterbegin", '<span class="ultima-nueva">Nueva</span>');
    }
  });
})();

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
  // Con el dedo no hay «pasar por encima»: el primer toque en un cuadrado muestra qué
  // película es y el segundo abre su ficha (también hay un enlace en la lectura).
  let puntero = "mouse";
  let elegida = null;
  const soltar = () => { if (elegida) elegida.classList.remove("elegida"); elegida = null; };
  const anotarPuntero = (e) => { puntero = e.pointerType || "mouse"; };
  grafico.addEventListener("pointerover", anotarPuntero);
  grafico.addEventListener("pointerdown", anotarPuntero);
  celdas.forEach((c) => {
    c.addEventListener("mouseenter", () => { if (puntero === "mouse") mostrar(c); });
    c.addEventListener("focus", () => { if (puntero === "mouse") mostrar(c); });
  });
  grafico.addEventListener("click", (e) => {
    const c = e.target.closest(".celda");
    if (!c || puntero === "mouse" || c === elegida) return;
    e.preventDefault();
    soltar();
    elegida = c;
    c.classList.add("elegida");
    mostrar(c);
    const abrir = document.createElement("a");
    abrir.href = c.href;
    abrir.className = "lectura-abrir";
    abrir.textContent = "Abrir la ficha";
    lectura.append(abrir);
  });
  document.addEventListener("click", (e) => {
    if (elegida && !grafico.contains(e.target) && !lectura.contains(e.target)) { soltar(); lectura.innerHTML = ayuda; }
  });
  grafico.addEventListener("mouseleave", () => { if (puntero === "mouse") lectura.innerHTML = ayuda; });
  grafico.addEventListener("focusout", (e) => {
    if (puntero === "mouse" && !grafico.contains(e.relatedTarget)) lectura.innerHTML = ayuda;
  });

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
