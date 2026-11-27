// Buscador de texto completo sobre buscar.json (título, otros títulos y texto de cada reseña).
(() => {
  const zona = document.querySelector(".buscar");
  if (!zona) return;
  const raiz = zona.dataset.raiz;
  const campo = document.getElementById("q");
  const recuento = zona.querySelector(".buscar-recuento");
  const lista = zona.querySelector(".buscar-resultados");
  const MAX = 100;

  // Sin tildes y en minúsculas, conservando la longitud del texto para poder recortar fragmentos.
  const normalizar = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const escapar = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const terminos = (q) => {
    const t = [];
    q.replace(/"([^"]+)"|(\S+)/g, (_, frase, palabra) => {
      const v = normalizar((frase || palabra).trim());
      if (v.length >= 2) t.push(v);
    });
    return t;
  };
  const contar = (texto, t) => { let n = 0, i = texto.indexOf(t); while (i !== -1) { n++; i = texto.indexOf(t, i + t.length); } return n; };

  const resaltar = (original, normal, ts) => {
    const marcas = [];
    ts.forEach((t) => { let i = normal.indexOf(t); while (i !== -1) { marcas.push([i, i + t.length]); i = normal.indexOf(t, i + t.length); } });
    marcas.sort((a, b) => a[0] - b[0]);
    let out = "", pos = 0;
    marcas.forEach(([a, b]) => { if (a < pos) return; out += escapar(original.slice(pos, a)) + "<mark>" + escapar(original.slice(a, b)) + "</mark>"; pos = b; });
    return out + escapar(original.slice(pos));
  };

  const fragmento = (doc, ts) => {
    const i = Math.min(...ts.map((t) => doc._x.indexOf(t)).filter((i) => i >= 0));
    if (!isFinite(i)) return "";
    let a = Math.max(0, i - 90), b = Math.min(doc.x.length, i + 150);
    if (a > 0) a = doc.x.indexOf(" ", a) + 1;
    if (b < doc.x.length) b = doc.x.lastIndexOf(" ", b);
    return (a > 0 ? "…" : "") + resaltar(doc.x.slice(a, b), doc._x.slice(a, b), ts) + (b < doc.x.length ? "…" : "");
  };

  const manchas = (v) => `<span class="manchas" style="--n:${Number(v)}" role="img" aria-label="${v} de 5 manchas de sangre"></span>`;

  let docs = null;
  const buscar = () => {
    const q = campo.value.trim();
    const url = new URL(location.href);
    if (q) url.searchParams.set("q", q); else url.searchParams.delete("q");
    history.replaceState(null, "", url);
    const ts = terminos(q);
    if (!ts.length || !docs) { lista.innerHTML = ""; recuento.textContent = q && docs ? "Escribe al menos dos letras." : ""; return; }
    const hallados = [];
    docs.forEach((d) => {
      if (!ts.every((t) => d._todo.includes(t))) return;
      const puntos = ts.reduce((s, t) => s + contar(d._x, t) + (d._titulo.includes(t) ? 25 : 0), 0);
      hallados.push([puntos, d]);
    });
    hallados.sort((a, b) => b[0] - a[0] || a[1].a - b[1].a);
    const n = hallados.length;
    recuento.textContent = n ? `${n} ${n === 1 ? "reseña" : "reseñas"}${n > MAX ? `; se muestran las ${MAX} con más coincidencias` : ""}.` : "Ninguna reseña contiene eso. Prueba con otra palabra o sin comillas.";
    lista.innerHTML = hallados.slice(0, MAX).map(([, d]) => `
      <li class="resultado">
        <a class="resultado-enlace" href="${raiz}${d.r}">
          ${d.m ? `<img class="resultado-cartel" src="${raiz}img/miniaturas/${escapar(d.m)}" alt="" width="40" height="58" loading="lazy" decoding="async">` : `<span class="resultado-cartel"></span>`}
          <span class="resultado-titulo">${resaltar(d.t, normalizar(d.t), ts)}</span>
          <span class="resultado-meta"><span class="resultado-anio">${d.a}</span>${manchas(d.v)}</span>
          <span class="resultado-fragmento">${fragmento(d, ts)}</span>
        </a>
      </li>`).join("");
  };

  let espera;
  campo.addEventListener("input", () => { clearTimeout(espera); espera = setTimeout(buscar, 180); });
  zona.querySelector(".buscar-form").addEventListener("submit", (e) => { e.preventDefault(); buscar(); });
  campo.value = new URLSearchParams(location.search).get("q") || "";
  recuento.textContent = campo.value ? "Buscando…" : "";
  fetch(zona.dataset.indice, { mode: "cors", credentials: "same-origin" }).then((r) => r.json()).then((datos) => {
    docs = datos.map((d) => ({ ...d, _x: normalizar(d.x), _titulo: normalizar(d.t + " " + d.o), _todo: normalizar(d.t + " " + d.o + " " + d.x) }));
    buscar();
    if (!campo.value) campo.focus();
  }).catch(() => { recuento.textContent = "No se ha podido cargar el índice de búsqueda."; });
})();
