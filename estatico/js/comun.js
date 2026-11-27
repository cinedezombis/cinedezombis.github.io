// Lupa de la cabecera: al abrirla, el cursor va al campo; Escape o un clic fuera la cierran.
(() => {
  const lupa = document.querySelector(".lupa");
  if (!lupa) return;
  const campo = lupa.querySelector("input");
  lupa.addEventListener("toggle", () => { if (lupa.open) campo.focus(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && lupa.open) { lupa.open = false; lupa.querySelector("summary").focus(); }
  });
  document.addEventListener("click", (e) => { if (lupa.open && !lupa.contains(e.target)) lupa.open = false; });
})();
