"""Genera estatico/img/compartir.png: la imagen de 1200×630 que muestran las redes
sociales y los programas de mensajería al compartir la portada o las páginas generales
del atlas (las fichas usan su cartel). Solo hay que volver a ejecutarlo si cambian
los colores, las fuentes o el texto.

    python herramientas/generar_compartir.py

Necesita Playwright con Chromium (pip install playwright; playwright install chromium).
Lee los colores de las variables :root de estatico/css/estilo.css.
"""
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
ESTATICO = RAIZ / "estatico"
DESTINO = ESTATICO / "img" / "compartir.png"


def paleta():
    css = (ESTATICO / "css" / "estilo.css").read_text(encoding="utf-8")
    raiz = re.search(r":root\s*{(.*?)}", css, re.S).group(1)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", raiz))


def simbolo_mancha():
    base = (RAIZ / "plantillas" / "base.html").read_text(encoding="utf-8")
    return re.search(r'<symbol id="mancha" viewBox="0 0 24 24">\s*(.*?)\s*</symbol>', base, re.S).group(1)


def html(c):
    fuentes = (ESTATICO / "fuentes").as_uri()
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
@font-face {{ font-family: "Big Shoulders Display"; font-weight: 800; src: url({fuentes}/big-shoulders-display-latin-800-normal.woff2); }}
@font-face {{ font-family: "Literata"; font-weight: 200 900; src: url({fuentes}/literata-latin-wght-normal.woff2); }}
html, body {{ margin: 0; }}
.lienzo {{ position: relative; width: 1200px; height: 630px; overflow: hidden; background: {c['hueso']}; color: {c['tinta']}; }}
.mancha {{ position: absolute; right: -120px; top: -90px; width: 640px; height: 640px; fill: {c['sangre']}; transform: rotate(14deg); }}
.texto {{ position: absolute; left: 84px; bottom: 76px; right: 84px; }}
h1 {{ font-family: "Big Shoulders Display"; font-weight: 800; font-size: 168px; line-height: .84; margin: 0 0 34px; max-width: 7.2ch; }}
p {{ font-family: "Literata"; font-size: 34px; margin: 0; color: {c['formol']}; }}
</style></head><body><div class="lienzo">
<svg class="mancha" viewBox="0 0 24 24" aria-hidden="true">{simbolo_mancha()}</svg>
<div class="texto"><h1>Atlas del cine de zombis</h1><p>cinedezombis.github.io</p></div>
</div></body></html>"""


def main():
    pagina_html = RAIZ / "herramientas" / "_compartir.html"
    pagina_html.write_text(html(paleta()), encoding="utf-8")
    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch()
            pagina = navegador.new_page(viewport={"width": 1200, "height": 630})
            pagina.goto(pagina_html.as_uri())
            pagina.evaluate("document.fonts.ready")
            pagina.locator(".lienzo").screenshot(path=str(DESTINO))
            navegador.close()
    finally:
        pagina_html.unlink(missing_ok=True)
    print(f"Imagen creada: {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
