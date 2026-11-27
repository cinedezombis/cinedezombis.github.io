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
