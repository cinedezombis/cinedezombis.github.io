#!/usr/bin/env python3
"""Genera la cubierta y la contraportada del libro (portada.pdf/png y contraportada.pdf/png).

Cubierta: los títulos de todas las películas en orden cronológico, en letra pequeña, alrededor
del título; las de cinco manchas en rojo oscuro y las de cuatro en rojo claro. El cuerpo de la
lista se ajusta solo para llenar la página, así que añadir películas no obliga a tocar nada.

Contraportada: texto de presentación, el gráfico del atlas (una casilla por película sobre su
año de estreno) y los datos de licencia, DOI y web.

Los colores se leen de las variables de estatico/css/estilo.css, así la web y el libro
comparten siempre la misma paleta.

Uso: python3 libro/generar_portada.py      (necesita Playwright con Chrome o Chromium)
"""
import asyncio
import html
import re
import sys
from pathlib import Path

import yaml

LIBRO = Path(__file__).resolve().parent
RAIZ = LIBRO.parent
sys.path.insert(0, str(RAIZ))
import build  # noqa: E402  (reutiliza los datos de las películas)

AJUSTES = yaml.safe_load((LIBRO / "libro.yml").read_text(encoding="utf-8"))

PRESENTACION = [
    "Entre 2012 y 2016, el blog ZombisBlog se propuso ver y comentar todas las películas de zombis "
    "que existieran. Creía que no llegarían al centenar. Terminó con {total} reseñas, desde "
    "“White Zombie” ({primero}) hasta “Orgullo y prejuicio y zombis” ({ultimo}).",
    "Este atlas las reúne todas, ordenadas por año de estreno y valoradas de una a cinco manchas de "
    "sangre: los clásicos de Romero y de Fulci, los templarios ciegos de Amando de Ossorio, la serie B "
    "de los años cuarenta, el cine italiano de los ochenta y la avalancha del nuevo siglo. Cierran el "
    "volumen las sagas y remakes, las películas mejor valoradas y un índice de títulos.",
]

# Ajusta el cuerpo de la lista hasta que ocupe todo el alto disponible sin desbordarse.
AJUSTAR = """() => { const l = document.querySelector('.lista'); if (!l) return 0;
  let lo = 3, hi = 12;
  for (let i = 0; i < 24; i++) { const m = (lo + hi) / 2; l.style.fontSize = m + 'pt';
    if (l.scrollHeight <= l.clientHeight) lo = m; else hi = m; }
  l.style.fontSize = lo + 'pt'; return lo; }"""


def paleta_web():
    css = (RAIZ / "estatico" / "css" / "estilo.css").read_text(encoding="utf-8")
    raiz = css[css.index(":root"):]
    raiz = raiz[:raiz.index("}")]
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{3,6})", raiz))


def cabecera_css(c):
    f = (LIBRO / "fuentes").as_uri()
    return f"""
@font-face {{ font-family: BS; font-weight: 800; src: url({f}/BigShouldersDisplay-ExtraBold.ttf); }}
@font-face {{ font-family: BS; font-weight: 700; src: url({f}/BigShouldersDisplay-Bold.ttf); }}
@font-face {{ font-family: Lit; src: url({f}/Literata-Regular.ttf); }}
@font-face {{ font-family: Lit; font-style: italic; src: url({f}/Literata-Italic.ttf); }}
@page {{ size: 150mm 230mm; margin: 0; }}
html, body {{ margin: 0; }}
body {{ width: 150mm; height: 230mm; background: {c['hueso']}; color: {c['tinta']}; position: relative; overflow: hidden; }}
"""


def html_portada(c):
    piezas = []
    for p in build.PELICULAS:
        titulo = html.escape(p["titulo"].replace("(remake)", "").strip())
        clase = {5: "v5", 4: "v4"}.get(p["valoracion"], "")
        piezas.append(f'<span class="{clase}"><b>{p["anio"]}</b>&nbsp;{titulo}</span>')
    lineas = AJUSTES.get("subtitulo_lineas") or [AJUSTES["subtitulo"]]
    bloque = (f'<div class="bloque"><p class="autor">{html.escape(AJUSTES["autor"])}</p>'
              f'<h1>Atlas del cine<br>de zombis</h1>'
              f'<p class="sub">{"<br>".join(html.escape(x) for x in lineas)}</p></div>')
    # El bloque del título se intercala hacia el 11 % de la lista, para que quede en el tercio superior.
    corte = round(len(piezas) * 0.115)
    lista = " ".join(piezas[:corte]) + " " + bloque + " ".join(piezas[corte:])
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{cabecera_css(c)}
.lista {{ position: absolute; inset: 8mm; overflow: hidden; font: 700 6pt/1.42 BS; color: {c['lista']};
  text-align: justify; hyphens: none; word-spacing: .4mm; }}
.lista b {{ font-weight: 800; color: {c['lista-anio']}; }}
.lista .v4, .lista .v4 b {{ color: {c['r3']}; }}
.lista .v5, .lista .v5 b {{ color: {c['r4']}; }}
.bloque {{ float: left; width: 100%; padding: 7mm 3mm 8mm; box-sizing: border-box; text-align: left; color: {c['tinta']}; }}
.autor {{ margin: 0 0 4mm; font: 11.5pt Lit; }}
h1 {{ margin: 0; font: 800 64pt/.84 BS; letter-spacing: -.01em; }}
.sub {{ margin: 5mm 0 0; font: 13pt/1.35 Lit; color: {c['formol']}; word-spacing: normal; }}
</style></head><body><div class="lista">{lista}</div></body></html>"""


def html_contraportada(c):
    total = len(build.PELICULAS)
    textos = "".join(f"<p>{html.escape(t.format(total=total, primero=build.PELICULAS[0]['anio'], ultimo=build.ANIO_MAX))}</p>"
                     for t in PRESENTACION)
    columnas = []
    for col in build.COLUMNAS:
        celdas = "".join(f'<i style="background:{c["r" + str(p["valoracion"])]}"></i>' for p in col["peliculas"])
        columnas.append(f"<div>{celdas}</div>")
    n = len(build.COLUMNAS)
    etiquetas = "".join(
        f'<span style="grid-column:{i * 10 + 1} / span {min(10, n - i * 10)}">{build.ANIO_MIN + i * 10}</span>'
        for i in range((n + 9) // 10))
    leyenda = "".join(f'<span><i style="background:{c["r" + str(v)]}"></i>{v}</span>' for v in range(1, 6))
    datos = [f"Licencia Creative Commons BY-NC-SA 4.0"]
    if AJUSTES.get("doi"):
        datos.append(f"DOI {html.escape(AJUSTES['doi'])}")
    if AJUSTES.get("url_web"):
        datos.append(html.escape(AJUSTES["url_web"].replace("https://", "")))
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{cabecera_css(c)}
.texto {{ position: absolute; left: 16mm; right: 18mm; top: 20mm; font: 10.6pt/1.5 Lit; hyphens: manual; text-wrap: pretty; }}
.texto p {{ margin: 0 0 3.2mm; }}
.texto p:first-child {{ font-size: 12pt; line-height: 1.42; }}
.grafico {{ position: absolute; left: 16mm; right: 16mm; bottom: 52mm; display: grid;
  grid-template-columns: repeat({n}, 1fr); column-gap: .3mm; align-items: end;
  border-bottom: .7mm solid {c['tinta']}; height: 76mm; }}
.grafico div {{ display: flex; flex-direction: column-reverse; gap: .3mm; }}
.grafico i {{ display: block; height: 4.1mm; }}
.suelo {{ position: absolute; left: 16mm; right: 16mm; bottom: 46mm; display: grid; grid-template-columns: repeat({n}, 1fr); column-gap: .3mm; }}
.suelo span {{ font: 700 7.5pt/1 BS; color: {c['formol']}; border-left: .2mm solid {c['formol']}; padding: 1mm 0 0 .7mm; min-width: 0; overflow: hidden; }}
.pie-grafico {{ position: absolute; left: 16mm; right: 16mm; bottom: 34mm; font: italic 8.5pt/1.35 Lit; color: {c['formol']};
  display: flex; justify-content: space-between; align-items: baseline; gap: 4mm; }}
.leyenda {{ font: 700 7.5pt BS; font-style: normal; display: flex; gap: 2mm; white-space: nowrap; }}
.leyenda span {{ display: inline-flex; align-items: center; gap: .8mm; }}
.leyenda i {{ display: inline-block; width: 2.6mm; height: 2.6mm; }}
.datos {{ position: absolute; left: 16mm; right: 16mm; bottom: 13mm; border-top: .3mm solid {c['liquen']}; padding-top: 3mm;
  font: 8.5pt/1.5 Lit; color: {c['formol']}; }}
.datos p {{ margin: 0; }}
</style></head><body>
<div class="texto">{textos}</div>
<div class="grafico">{"".join(columnas)}</div>
<div class="suelo">{etiquetas}</div>
<div class="pie-grafico"><span>Las {total} películas sobre su año de estreno. Cada casilla es una película; el color, su valoración.</span>
<span class="leyenda">{leyenda}</span></div>
<div class="datos">{"".join(f"<p>{d}</p>" for d in datos)}</div>
</body></html>"""


def colores(paleta=None):
    c = dict(paleta or paleta_web())
    c.setdefault("lista", c["liquen"])
    # Los años de la lista de la cubierta van en gris: la escala de valoración de la web ya es toda roja.
    c.setdefault("lista-anio", "#94938e")
    return c


async def generar(paleta=None, destino=LIBRO, pdf=True):
    from playwright.async_api import async_playwright
    c = colores(paleta)
    trabajo = LIBRO / "_construccion"
    trabajo.mkdir(exist_ok=True)
    resultado = {}
    async with async_playwright() as p:
        try:
            navegador = await p.chromium.launch(args=["--no-sandbox"])
        except Exception:
            navegador = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pagina = await navegador.new_page(viewport={"width": 567, "height": 869}, device_scale_factor=2.822)
        for nombre, fabrica in (("portada", html_portada), ("contraportada", html_contraportada)):
            fuente = trabajo / f"{nombre}.html"
            fuente.write_text(fabrica(c), encoding="utf-8")
            await pagina.goto(fuente.as_uri())
            await pagina.evaluate("document.fonts.ready")
            resultado[nombre] = await pagina.evaluate(AJUSTAR)
            await pagina.screenshot(path=str(destino / f"{nombre}.png"))
            if nombre == "portada":  # versión ligera para la cubierta del EPUB
                from PIL import Image
                Image.open(destino / "portada.png").convert("RGB").save(destino / "portada.jpg", quality=88, optimize=True)
            if pdf:
                await pagina.emulate_media(media="print")
                await pagina.evaluate(AJUSTAR)
                await pagina.pdf(path=str(destino / f"{nombre}.pdf"), width="150mm", height="230mm", print_background=True)
                await pagina.emulate_media(media="screen")
        await navegador.close()
    return resultado


if __name__ == "__main__":
    r = asyncio.run(generar())
    print(f"Cubierta y contraportada generadas en libro/ (lista de títulos a {r['portada']:.2f} pt)")
