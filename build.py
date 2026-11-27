#!/usr/bin/env python3
"""Genera la web estática del Atlas del cine de zombis en la carpeta _site/.

Uso:  python3 build.py

Lee las fichas de contenido/peliculas/*.md y las páginas de contenido/paginas/*.md,
aplica las plantillas de plantillas/ y copia estatico/ tal cual.
"""
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "_site"
CONFIG = yaml.safe_load((RAIZ / "sitio.yml").read_text(encoding="utf-8"))

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
PAGINAS_FIJAS = {"/p/los-zombis.html", "/p/sagas.html", "/p/las-mejores.html", "/p/peliculas-comentadas.html"}


def leer(ruta):
    texto = ruta.read_text(encoding="utf-8")
    _, cabecera, cuerpo = texto.split("---\n", 2)
    return yaml.safe_load(cabecera), cuerpo.strip()


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower()


def comillas(texto):
    """Comillas tipográficas en los títulos: "X" y ''X'' pasan a “X”."""
    texto = re.sub(r"''(.+?)''", r"“\1”", texto)
    return re.sub(r'"(.+?)"', r"“\1”", texto)


def fecha_larga(iso):
    d = date.fromisoformat(str(iso))
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


MESES_CORTOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sept.", "oct.", "nov.", "dic."]


def fecha_corta(iso):
    d = date.fromisoformat(str(iso))
    return f"{d.day} {MESES_CORTOS[d.month - 1]} {d.year}"


def prefijo(ruta_salida):
    """Prefijo relativo desde una página hasta la raíz del sitio ('', '../', '../../')."""
    profundidad = ruta_salida.strip("/").count("/")
    return "../" * profundidad


def md_a_html(texto, raiz):
    """Markdown a HTML; los enlaces zb:/ruta apuntan a otras páginas del propio archivo."""
    def enlace(m):
        etiqueta, ruta = m.group(1), m.group(2)
        if ruta in RUTAS or ruta in PAGINAS_FIJAS:
            return f"[{etiqueta}]({raiz}{ruta.lstrip('/')})"
        return etiqueta
    texto = re.sub(r"\[([^\]]+)\]\(zb:([^)]+)\)", enlace, texto)
    return markdown.markdown(texto, extensions=["smarty"], output_format="html")


# --- Datos ---------------------------------------------------------------
CARTELES = RAIZ / "estatico" / "img" / "carteles"


def video_desde_url(url):
    """Convierte el enlace de un tráiler (YouTube, Internet Archive u otra web) en una entrada de vídeo."""
    url = url.strip()
    m = re.search(r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if m:
        return {"etiqueta": "Tráiler", "youtube": m.group(1)}
    m = re.search(r"archive\.org/details/([^/?#]+)", url)
    if m:
        return {"etiqueta": "Tráiler", "archive": m.group(1)}
    dominio = re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0])
    return {"etiqueta": "Tráiler", "url": url, "fuente": dominio}


PELICULAS = []
for archivo in sorted((RAIZ / "contenido" / "peliculas").glob("*.md")):
    meta, cuerpo = leer(archivo)
    meta["cuerpo"] = cuerpo
    meta["titulo"] = comillas(meta["titulo"])
    meta["id"] = archivo.stem
    meta["decada"] = meta["anio"] // 10 * 10
    meta["busca"] = normalizar(" ".join([meta["titulo"], *meta.get("etiquetas", [])]))
    meta["orden"] = normalizar(meta["titulo"])
    meta.setdefault("etiquetas", [])
    # Dirección de la ficha: las del blog conservan la suya; las nuevas van en /peliculas/
    meta["ruta"] = meta.get("ruta") or f"/peliculas/{archivo.stem}.html"
    # Cartel: el indicado o, si no se indica, una imagen con el mismo nombre que la ficha
    if not meta.get("cartel"):
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            if (CARTELES / f"{archivo.stem}{ext}").exists():
                meta["cartel"] = f"{archivo.stem}{ext}"
                break
    meta["cartel_origen"] = meta.get("cartel")
    # Tráiler escrito como enlace (trailer: https://...) en las fichas nuevas
    if meta.get("trailer") and isinstance(meta["trailer"], str):
        meta["videos"] = [video_desde_url(meta["trailer"])] + list(meta.get("videos") or [])
    for v in meta.get("videos") or []:
        if v.get("youtube"):
            v["url"], v["fuente"] = f"https://www.youtube.com/watch?v={v['youtube']}", "YouTube"
        elif v.get("archive"):
            v["url"], v["fuente"] = f"https://archive.org/details/{v['archive']}", "Internet Archive"
    videos = meta.get("videos") or []
    meta["trailer"] = next((v for v in videos if v["etiqueta"].startswith("Tráiler")), None)
    meta["otros_videos"] = [v for v in videos if v is not meta["trailer"]]
    busqueda = re.sub(r"[“”\"]", "", meta["titulo"]) + f" {meta['anio']} tráiler"
    meta["busqueda_trailer"] = "https://www.youtube.com/results?search_query=" + quote_plus(busqueda)
    # Las reseñas hasta 2016 vienen del blog; las posteriores se escribieron ya para el atlas
    meta["del_blog"] = bool(meta.get("publicado")) and str(meta["publicado"]) <= "2016-12-31"
    PELICULAS.append(meta)

PELICULAS.sort(key=lambda p: (p["anio"], p["orden"]))
RUTAS = {p["ruta"] for p in PELICULAS}
for i, p in enumerate(PELICULAS):
    p["anterior"] = PELICULAS[i - 1] if i > 0 else None
    p["siguiente"] = PELICULAS[i + 1] if i < len(PELICULAS) - 1 else None

ANIO_MIN = PELICULAS[0]["anio"] // 10 * 10
ANIO_MAX = PELICULAS[-1]["anio"]
COLUMNAS = []
for anio in range(ANIO_MIN, ANIO_MAX + 1):
    del_anio = sorted((p for p in PELICULAS if p["anio"] == anio), key=lambda p: (-p["valoracion"], p["orden"]))
    COLUMNAS.append({"anio": anio, "peliculas": del_anio})
MAX_POR_ANIO = max(len(c["peliculas"]) for c in COLUMNAS)

# Últimas reseñas publicadas (blog o atlas), de la más reciente a la más antigua
ULTIMAS = sorted((p for p in PELICULAS if p.get("publicado")), key=lambda p: (str(p["publicado"]), p["id"]), reverse=True)
DECADAS = []
for d in range(ANIO_MIN, ANIO_MAX + 1, 10):
    DECADAS.append({"decada": d, "peliculas": [p for p in PELICULAS if p["decada"] == d]})

LIBRO = None
carpeta_libro = RAIZ / "estatico" / "libro"
if carpeta_libro.exists():
    pdf = next(carpeta_libro.glob("*.pdf"), None)
    epub = next(carpeta_libro.glob("*.epub"), None)
    if pdf or epub:
        LIBRO = {"pdf": pdf.name if pdf else None, "epub": epub.name if epub else None,
                 "pdf_mb": round(pdf.stat().st_size / 1e6, 1) if pdf else None,
                 "epub_mb": round(epub.stat().st_size / 1e6, 1) if epub else None}

# --- Plantillas ----------------------------------------------------------
entorno = Environment(loader=FileSystemLoader(RAIZ / "plantillas"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
entorno.filters["fecha"] = fecha_larga
entorno.filters["fecha_corta"] = fecha_corta
import hashlib
VERSION = hashlib.sha1(b"".join((RAIZ / "estatico" / f).read_bytes() for f in ("css/estilo.css", "js/atlas.js"))).hexdigest()[:8]
comunes = {"config": CONFIG, "libro": LIBRO, "total": len(PELICULAS), "version": VERSION,
           "primera": PELICULAS[0], "anio_min": PELICULAS[0]["anio"], "anio_max": ANIO_MAX}


def escribir(ruta_salida, plantilla, **datos):
    raiz = prefijo(ruta_salida)
    canonica = CONFIG.get("url", "").rstrip("/")
    datos.setdefault("canonica", f"{canonica}/{ruta_salida.lstrip('/')}" if canonica else "")
    html = entorno.get_template(plantilla).render(raiz=raiz, **comunes, **datos)
    destino = SALIDA / ruta_salida.lstrip("/")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")


def preparar_imagenes():
    """Crea la miniatura de cada cartel y reduce los carteles nuevos grandes. No toca los originales."""
    from PIL import Image
    mini_dir = SALIDA / "img" / "miniaturas"
    cart_dir = SALIDA / "img" / "carteles"
    mini_dir.mkdir(parents=True, exist_ok=True)
    for p in PELICULAS:
        if not p.get("cartel_origen"):
            p["cartel"] = p["miniatura"] = None
            continue
        origen = CARTELES / p["cartel_origen"]
        base = Path(p["cartel_origen"]).stem
        p["miniatura"] = f"{base}.jpg"
        imagen = None
        if not (mini_dir / p["miniatura"]).exists():
            imagen = Image.open(origen).convert("RGB")
            mini = imagen.copy(); mini.thumbnail((112, 168))
            mini.save(mini_dir / p["miniatura"], "JPEG", quality=80, optimize=True)
        if not p.get("cartel_tamano") or origen.suffix.lower() != ".jpg":
            imagen = imagen or Image.open(origen).convert("RGB")
            grande = imagen.copy(); grande.thumbnail((560, 840))
            grande.save(cart_dir / f"{base}.jpg", "JPEG", quality=84, optimize=True, progressive=True)
            p["cartel"], p["cartel_tamano"] = f"{base}.jpg", list(grande.size)


def preparar_cubierta():
    """Miniatura de la cubierta del libro para el pie de página."""
    portada = RAIZ / "libro" / "portada.png"
    if not LIBRO or not portada.exists():
        return
    from PIL import Image
    imagen = Image.open(portada).convert("RGB")
    imagen.thumbnail((200, 320))
    imagen.save(SALIDA / "img" / "libro-cubierta.jpg", "JPEG", quality=82, optimize=True)
    LIBRO["cubierta"], LIBRO["cubierta_tamano"] = "libro-cubierta.jpg", imagen.size


def escribir_canal(cuantas=20):
    """Canal Atom (feed.xml) con las últimas reseñas, para quien quiera seguir las novedades."""
    from xml.sax.saxutils import escape
    base = CONFIG.get("url", "").rstrip("/")
    entradas = []
    for p in ULTIMAS[:cuantas]:
        url = f"{base}{p['ruta']}"
        fecha = f"{p['publicado']}T12:00:00Z"
        resumen = re.sub(r"[\[\]*]|\(zb:[^)]*\)|\([^)]*https?://[^)]*\)", "", p["cuerpo"]).split("\n")[0][:400]
        entradas.append(
            f"<entry><title>{escape(p['titulo'])} ({p['anio']})</title><link href=\"{escape(url)}\"/>"
            f"<id>{escape(url)}</id><published>{fecha}</published><updated>{fecha}</updated>"
            f"<summary>{escape(resumen)}</summary></entry>")
    actualizado = f"{ULTIMAS[0]['publicado']}T12:00:00Z" if ULTIMAS else "2016-12-31T12:00:00Z"
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="es">'
           f"<title>Atlas del cine de zombis</title><subtitle>Últimas películas comentadas</subtitle>"
           f'<link href="{escape(base)}/"/><link rel="self" href="{escape(base)}/feed.xml"/><id>{escape(base)}/</id>'
           f"<updated>{actualizado}</updated><author><name>Miguel Ángel Gómez Ruiz</name></author>"
           + "".join(entradas) + "</feed>\n")
    (SALIDA / "feed.xml").write_text(xml, encoding="utf-8")


def construir():
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    shutil.copytree(RAIZ / "estatico", SALIDA)
    preparar_imagenes()
    preparar_cubierta()
    escribir_canal()

    escribir("index.html", "inicio.html", seccion="atlas", columnas=COLUMNAS, decadas=DECADAS, max_por_anio=MAX_POR_ANIO,
             ultimas=ULTIMAS[:5],
             titulo_pagina="Atlas del cine de zombis",
             descripcion=f"{len(PELICULAS)} películas de zombis comentadas y valoradas, de {PELICULAS[0]['anio']} a {ANIO_MAX}.")

    for p in PELICULAS:
        raiz = prefijo(p["ruta"])
        escribir(p["ruta"], "pelicula.html", seccion="", p=p, texto=md_a_html(p["cuerpo"], raiz),
                 titulo_pagina=f"{p['titulo']} ({p['anio']}). Atlas del cine de zombis",
                 descripcion=re.sub(r"[\[\]*]|\(zb:[^)]*\)|\([^)]*https?://[^)]*\)", "", p["cuerpo"]).split("\n")[0][:155])

    for archivo in sorted((RAIZ / "contenido" / "paginas").glob("*.md")):
        meta, cuerpo = leer(archivo)
        seccion = "sagas" if "sagas" in meta["ruta"] else "sobre"
        escribir(meta["ruta"], "pagina.html", seccion=seccion, meta=meta,
                 texto=md_a_html(cuerpo, prefijo(meta["ruta"])),
                 titulo_pagina=f"{meta['titulo']}. Atlas del cine de zombis", descripcion=meta["titulo"])

    letras = {}
    for p in sorted(PELICULAS, key=lambda p: (p["orden"], p["anio"])):
        inicial = p["orden"][0].upper() if p["orden"][0].isalpha() else "#"
        letras.setdefault(inicial, []).append(p)
    escribir("/p/peliculas-comentadas.html", "indice.html", seccion="indice", letras=letras,
             titulo_pagina="Índice de la A a la Z. Atlas del cine de zombis",
             descripcion="Todas las películas del atlas, por orden alfabético.")

    grupos = [(v, [p for p in PELICULAS if p["valoracion"] == v]) for v in (5, 4, 3)]
    escribir("/p/las-mejores.html", "mejores.html", seccion="mejores", grupos=grupos,
             titulo_pagina="Mejor valoradas. Atlas del cine de zombis",
             descripcion="Las películas de zombis que he puntuado con 3, 4 o 5 manchas de sangre.")

    escribir("404.html", "404.html", seccion="", titulo_pagina="Página no encontrada. Atlas del cine de zombis",
             descripcion="", canonica="")
    print(f"Web generada en {SALIDA.relative_to(RAIZ)}/: {len(PELICULAS)} películas.")


if __name__ == "__main__":
    construir()
