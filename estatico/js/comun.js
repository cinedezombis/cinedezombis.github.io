// Lupa de la cabecera: al abrirla, el cursor va al campo; Escape o un clic fuera la cierran.
(() => {
  const lupa = document.querySelector(".lupa");
  if (!lupa) return;
  const campo = lupa.querySelector("input");
  // Al abrirla se pide ya el índice del buscador, para que la página de resultados lo tenga listo.
  let pedido = false;
  lupa.addEventListener("toggle", () => {
    if (!lupa.open) return;
    campo.focus();
    const indice = lupa.querySelector("form").dataset.indice;
    if (pedido || !indice) return;
    pedido = true;
    const l = document.createElement("link");
    l.rel = "prefetch"; l.href = indice; l.as = "fetch"; l.crossOrigin = "anonymous";
    document.head.append(l);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && lupa.open) { lupa.open = false; lupa.querySelector("summary").focus(); }
  });
  document.addEventListener("click", (e) => { if (lupa.open && !lupa.contains(e.target)) lupa.open = false; });
})();

// En «Películas descartadas», un enlace a #descartes-… abre la lista de películas de ese criterio.
(() => {
  const abrir = () => {
    const criterio = location.hash.startsWith("#descartes-") && document.getElementById(location.hash.slice(1));
    const lista = criterio && criterio.querySelector("details.descartes");
    if (lista) lista.open = true;
  };
  abrir();
  addEventListener("hashchange", abrir);
})();

// Desplegable «Sobre el atlas»: Escape o un clic fuera lo cierran, y abrirlo cierra la lupa (y al revés).
(() => {
  const submenu = document.querySelector(".submenu");
  const lupa = document.querySelector(".lupa");
  if (!submenu) return;
  submenu.addEventListener("toggle", () => { if (submenu.open && lupa) lupa.open = false; });
  if (lupa) lupa.addEventListener("toggle", () => { if (lupa.open) submenu.open = false; });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && submenu.open) { submenu.open = false; submenu.querySelector("summary").focus(); }
  });
  document.addEventListener("click", (e) => { if (submenu.open && !submenu.contains(e.target)) submenu.open = false; });
})();

// Volver arriba: se muestra cuando la cabecera ha quedado más de una pantalla por encima.
(() => {
  const boton = document.querySelector(".arriba");
  const cabecera = document.getElementById("arriba");
  if (!boton || !cabecera || !("IntersectionObserver" in window)) return;
  boton.hidden = false;
  const marca = document.createElement("div");
  marca.style.cssText = "position:absolute;top:0;left:0;width:1px;height:150vh;pointer-events:none";
  marca.setAttribute("aria-hidden", "true");
  document.body.style.position ||= "relative";
  document.body.prepend(marca);
  new IntersectionObserver(([e]) => {
    const visible = !e.isIntersecting;
    boton.classList.toggle("visible", visible);
    boton.tabIndex = visible ? 0 : -1;
  }).observe(marca);
  boton.addEventListener("click", (e) => {
    e.preventDefault();
    const suave = !matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: suave ? "smooth" : "auto" });
    cabecera.querySelector("a").focus({ preventScroll: true });
    history.replaceState(null, "", location.pathname + location.search);
  });
})();

// Las direcciones antiguas de «Sobre el atlas» con ancla (#y-que-otras-no-comento, #descartes-…) llevan a su apartado nuevo.
(() => {
  if (!location.pathname.endsWith("/p/los-zombis.html") || !location.hash) return;
  const ancla = location.hash.slice(1);
  const cine = ["que-es-un-zombi-para-este-atlas", "las-peliculas-de-zombis"];
  const descartes = ["entonces-que-peliculas-comento-aqui", "y-que-otras-no-comento"];
  let destino = null;
  if (cine.includes(ancla)) destino = "el-cine-de-zombis.html#" + ancla;
  else if (ancla.startsWith("etapa-")) destino = "el-cine-de-zombis.html#las-peliculas-de-zombis";
  else if (ancla === "entonces-que-peliculas-comento-aqui") destino = "peliculas-descartadas.html#que-peliculas-comento-aqui";
  else if (descartes.includes(ancla) || ancla.startsWith("descartes-")) destino = "peliculas-descartadas.html#" + ancla;
  if (destino) location.replace(destino);
})();
