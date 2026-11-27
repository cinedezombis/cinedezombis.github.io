#!/usr/bin/env python3
"""Genera la cubierta del libro (portada.pdf y portada.png) a partir de los datos del atlas.

Uso: python3 libro/generar_portada.py      (necesita Playwright con Chrome o Chromium)
"""
import asyncio
import sys
from pathlib import Path

LIBRO = Path(__file__).resolve().parent
sys.path.insert(0, str(LIBRO.parent))
import build  # noqa: E402  (reutiliza los datos de las películas)

COLORES = {1: "#c2cabb", 2: "#96a292", 3: "#b85b4e", 4: "#8a1a12", 5: "#4a0b06"}


def html():
    columnas = []
    for col in build.COLUMNAS:
        celdas = "".join(f'<i style="background:{COLORES[p["valoracion"]]}"></i>' for p in col["peliculas"])
        columnas.append(f"<div>{celdas}</div>")
    n = len(build.COLUMNAS)
    etiquetas = "".join(
        f'<span style="grid-column:{i * 10 + 1} / span {min(10, n - i * 10)}">{build.ANIO_MIN + i * 10}</span>'
        for i in range((n + 9) // 10))
    f = (LIBRO / "fuentes").as_uri()
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
@font-face {{ font-family: BS; font-weight: 800; src: url({f}/BigShouldersDisplay-ExtraBold.ttf); }}
@font-face {{ font-family: BS; font-weight: 700; src: url({f}/BigShouldersDisplay-Bold.ttf); }}
@font-face {{ font-family: Lit; src: url({f}/Literata-Regular.ttf); }}
@page {{ size: 150mm 230mm; margin: 0; }}
html, body {{ margin: 0; }}
body {{ width: 150mm; height: 230mm; background: #e4e7dd; color: #18201c; position: relative; overflow: hidden; }}
.autor {{ position: absolute; left: 12mm; top: 13mm; font: 11pt Lit; letter-spacing: .01em; }}
.titulo {{ position: absolute; left: 11mm; top: 28mm; font: 800 54pt/0.86 BS; margin: 0; letter-spacing: -.01em; }}
.sub {{ position: absolute; left: 12mm; top: 66mm; font: 700 25pt/1 BS; margin: 0; }}
.anios {{ position: absolute; left: 12mm; top: 77mm; font: 700 25pt/1 BS; margin: 0; color: #8c9886; }}
.grafico {{ position: absolute; left: 12mm; right: 12mm; bottom: 30mm; display: grid;
  grid-template-columns: repeat({n}, 1fr); column-gap: .32mm; align-items: end;
  border-bottom: .9mm solid #18201c; height: 80mm; }}
.grafico div {{ display: flex; flex-direction: column-reverse; gap: .32mm; }}
.grafico i {{ display: block; height: 4.4mm; }}
.suelo {{ position: absolute; left: 12mm; right: 12mm; bottom: 22mm; display: grid; grid-template-columns: repeat({n}, 1fr); column-gap: .32mm; }}
.suelo span {{ font: 700 8.5pt/1 BS; color: #56645a; border-left: .2mm solid #56645a; padding: 1.2mm 0 0 .8mm; }}
.pie {{ position: absolute; left: 12mm; bottom: 10mm; font: 8.5pt Lit; color: #56645a; }}
</style></head><body>
<p class="autor">Miguel Ángel Gómez Ruiz</p>
<h1 class="titulo">Atlas del cine<br>de zombis</h1>
<p class="sub">{len(build.PELICULAS)} películas</p>
<p class="anios">{build.PELICULAS[0]["anio"]}–{build.ANIO_MAX}</p>
<div class="grafico">{"".join(columnas)}</div>
<div class="suelo">{etiquetas}</div>
<p class="pie">Reseñas publicadas en ZombisBlog (2012–2016). Cada cuadrado es una película, sobre su año de estreno.</p>
</body></html>"""


async def main():
    from playwright.async_api import async_playwright
    fuente = LIBRO / "_construccion" / "portada.html"
    fuente.parent.mkdir(exist_ok=True)
    fuente.write_text(html(), encoding="utf-8")
    async with async_playwright() as p:
        try:
            navegador = await p.chromium.launch(args=["--no-sandbox"])
        except Exception:
            navegador = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pagina = await navegador.new_page(viewport={"width": 567, "height": 869}, device_scale_factor=2.822)
        await pagina.goto(fuente.as_uri())
        await pagina.evaluate("document.fonts.ready")
        await pagina.pdf(path=str(LIBRO / "portada.pdf"), width="150mm", height="230mm", print_background=True)
        await pagina.screenshot(path=str(LIBRO / "portada.png"))
        await navegador.close()
    print("Cubierta generada: libro/portada.pdf y libro/portada.png")


if __name__ == "__main__":
    asyncio.run(main())
