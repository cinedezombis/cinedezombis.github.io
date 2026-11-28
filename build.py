#!/usr/bin/env python3
"""Genera la web estática del Atlas del cine de zombis en la carpeta _site/.

Uso:  python3 build.py

Lee las fichas de contenido/peliculas/*.md y las páginas de contenido/paginas/*.md,
aplica las plantillas de plantillas/ y copia estatico/ tal cual.
"""
import json
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


def ancla(texto, separador="-"):
    """Identificador de un título para enlazarlo con #: sin tildes, en minúsculas y con guiones."""
    return re.sub(r"[^a-z0-9]+", separador, normalizar(texto)).strip(separador)


def md_a_html(texto, raiz, anclas=False):
    """Markdown a HTML; los enlaces zb:/ruta apuntan a otras páginas del propio archivo.
    Con anclas=True, cada título recibe un id (para enlazar, por ejemplo, a una saga concreta)."""
    def enlace(m):
        etiqueta, ruta = m.group(1), m.group(2)
        if ruta in RUTAS or ruta in PAGINAS_FIJAS:
            return f"[{etiqueta}]({raiz}{ruta.lstrip('/')})"
        return etiqueta
    texto = re.sub(r"\[([^\]]+)\]\(zb:([^)]+)\)", enlace, texto)
    extensiones = ["smarty"]
    if anclas:
        from markdown.extensions.toc import TocExtension
        extensiones.append(TocExtension(slugify=ancla, toc_depth="2-3"))
    return markdown.markdown(texto, extensions=extensiones, output_format="html")


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

# Sagas y remakes: cada película sabe en qué apartados de la página de sagas aparece
for p in PELICULAS:
    p["sagas"] = []
_por_ruta = {p["ruta"]: p for p in PELICULAS}
_sagas_md = (RAIZ / "contenido" / "paginas" / "sagas.md").read_text(encoding="utf-8")
for bloque in re.split(r"^## ", _sagas_md, flags=re.M)[1:]:
    cabecera, _, resto = bloque.partition("\n")
    titulo, _, tipo = cabecera.strip().rpartition(" - ")
    saga = {"titulo": titulo or cabecera.strip(), "tipo": tipo.lower() if titulo else "", "id": ancla(cabecera.strip())}
    for ruta in re.findall(r"^- .*?\(zb:([^)]+)\)", resto, flags=re.M):
        if ruta in _por_ruta and saga not in _por_ruta[ruta]["sagas"]:
            _por_ruta[ruta]["sagas"].append(saga)

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
VERSION = hashlib.sha1(b"".join((RAIZ / "estatico" / f).read_bytes() for f in ("css/estilo.css", "js/atlas.js", "js/comun.js", "js/buscar.js"))).hexdigest()[:8]
PAGINAS = [leer(f) for f in sorted((RAIZ / "contenido" / "paginas").glob("*.md"))]
PAGINAS_FIJAS |= {meta["ruta"] for meta, _ in PAGINAS}
# Apartados de «Sobre el atlas»: las páginas con «menu» en la cabecera, en el orden que marca «orden».
SOBRE = sorted(({"menu": m["menu"], "ruta": m["ruta"], "orden": m.get("orden", 99)} for m, _ in PAGINAS if m.get("menu")),
               key=lambda x: x["orden"])
comunes = {"config": CONFIG, "libro": LIBRO, "total": len(PELICULAS), "version": VERSION,
           "primera": PELICULAS[0], "anio_min": PELICULAS[0]["anio"], "anio_max": ANIO_MAX, "sobre": SOBRE}


URL = CONFIG.get("url", "").rstrip("/")
AUTOR = "Miguel Ángel Gómez Ruiz"
# Imagen por defecto al compartir una página (herramientas/generar_compartir.py)
COMPARTIR = {"url": f"{URL}/img/compartir.png", "ancho": 1200, "alto": 630, "tarjeta": "summary_large_image",
             "alt": "Atlas del cine de zombis: el título junto a una gran mancha de sangre"}
MAPA = []  # (dirección, fecha de última modificación o None) de cada página, para sitemap.xml


def escribir(ruta_salida, plantilla, lastmod=None, **datos):
    raiz = prefijo(ruta_salida)
    datos.setdefault("canonica", f"{URL}/{ruta_salida.lstrip('/')}" if URL else "")
    datos.setdefault("compartir", COMPARTIR)
    if datos["canonica"]:
        MAPA.append((datos["canonica"], lastmod))
    html = entorno.get_template(plantilla).render(raiz=raiz, **comunes, **datos)
    destino = SALIDA / ruta_salida.lstrip("/")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")


def preparar_imagenes():
    """Prepara las versiones web de cada cartel sin tocar los originales:
    - miniatura JPG de 112×168 (últimas reseñas de la portada),
    - miniatura WebP de 84×126 (filas del atlas y resultados del buscador),
    - cartel WebP de hasta 560×840 para la ficha; el JPG se queda para compartir en redes.
    Las que ya están en estatico/img se copian tal cual; aquí solo se crean las que faltan."""
    from PIL import Image
    mini_dir = SALIDA / "img" / "miniaturas"
    cart_dir = SALIDA / "img" / "carteles"
    mini_dir.mkdir(parents=True, exist_ok=True)
    for p in PELICULAS:
        if not p.get("cartel_origen"):
            p["cartel"] = p["miniatura"] = p["miniatura_webp"] = p["cartel_webp"] = None
            continue
        origen = CARTELES / p["cartel_origen"]
        base = Path(p["cartel_origen"]).stem
        p["miniatura"], p["miniatura_webp"], p["cartel_webp"] = f"{base}.jpg", f"{base}.webp", f"{base}.webp"
        original = origen.suffix.lower() != ".jpg"
        imagen = None
        if not (mini_dir / p["miniatura"]).exists():
            imagen = imagen or Image.open(origen).convert("RGB")
            mini = imagen.copy(); mini.thumbnail((112, 168))
            mini.save(mini_dir / p["miniatura"], "JPEG", quality=80, optimize=True)
        if not (mini_dir / p["miniatura_webp"]).exists():
            imagen = imagen or Image.open(origen).convert("RGB")
            mini = imagen.copy(); mini.thumbnail((84, 126), Image.LANCZOS)
            mini.save(mini_dir / p["miniatura_webp"], "WEBP", quality=78, method=6)
        if not p.get("cartel_tamano") or original:
            imagen = imagen or Image.open(origen).convert("RGB")
            grande = imagen.copy(); grande.thumbnail((560, 840))
            grande.save(cart_dir / f"{base}.jpg", "JPEG", quality=84, optimize=True, progressive=True)
            p["cartel"], p["cartel_tamano"] = f"{base}.jpg", list(grande.size)
        if not (cart_dir / p["cartel_webp"]).exists() or original:
            imagen = imagen or Image.open(origen).convert("RGB")
            grande = imagen.copy(); grande.thumbnail((560, 840), Image.LANCZOS)
            grande.save(cart_dir / p["cartel_webp"], "WEBP", quality=80, method=6)


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


def escribir_indice_busqueda():
    """buscar.json: título, otros títulos y texto plano de cada reseña, y títulos de las descartadas."""
    import html as html_mod
    docs = []
    for p in PELICULAS:
        html_texto = re.sub(r"</(p|li|h\d|blockquote)>|<br\s*/?>", " ", md_a_html(p["cuerpo"], ""))
        plano = re.sub(r"<[^>]+>", "", html_texto)
        plano = re.sub(r"\s+", " ", html_mod.unescape(plano)).strip()
        docs.append({"t": p["titulo"], "a": p["anio"], "v": p["valoracion"], "r": p["ruta"].lstrip("/"),
                     "m": p.get("miniatura_webp") or "", "o": " · ".join(p.get("etiquetas") or []), "x": plano})
    # Las descartadas solo se buscan por título y llevan al criterio que las deja fuera.
    descartadas = (RAIZ / "contenido" / "paginas" / "descartadas.md").read_text(encoding="utf-8")
    criterios = {g: n for n, g in re.findall(r"\*\*([^*]+?)\.\*\*[^\n]*\n\n<!-- descartes:([\w-]+) -->", descartadas)}
    for p in DESCARTES:
        original = p.get("original") or ""
        docs.append({"t": p["titulo"], "a": p.get("anio") or "s. f.", "r": f"p/peliculas-descartadas.html#descartes-{p['grupo']}",
                     "o": original if normalizar(original) != normalizar(p["titulo"]) else "",
                     "d": criterios[p["grupo"]], "x": ""})
    datos = json.dumps(docs, ensure_ascii=False, separators=(",", ":"))
    (SALIDA / "buscar.json").write_text(datos, encoding="utf-8")
    # La dirección lleva la huella del contenido: cambia solo cuando cambia alguna reseña.
    comunes["indice"] = "buscar.json?v=" + hashlib.sha1(datos.encode()).hexdigest()[:8]


def resumen(texto, limite=155):
    """Primer párrafo en texto plano, cortado en una palabra y con puntos suspensivos si no cabe."""
    plano = re.sub(r"[\[\]*_]|\(zb:[^)]*\)|\([^)]*https?://[^)]*\)", "", texto).strip().split("\n")[0].strip()
    if len(plano) <= limite:
        return plano
    return plano[:limite].rsplit(" ", 1)[0].rstrip(" ,;:.") + "…"


def json_ld(datos):
    """Bloque JSON-LD listo para incrustar en un <script>."""
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def datos_ficha(p, canonica):
    """Datos estructurados de una ficha: una reseña (Review) de una película (Movie)."""
    pelicula = {"@type": "Movie", "name": p["titulo"], "dateCreated": str(p["anio"])}
    if p.get("etiquetas"):
        pelicula["alternateName"] = p["etiquetas"]
    if p.get("cartel"):
        pelicula["image"] = f"{URL}/img/carteles/{p['cartel']}"
    resena = {"@context": "https://schema.org", "@type": "Review", "url": canonica, "inLanguage": "es",
              "name": f"{p['titulo']} ({p['anio']})", "itemReviewed": pelicula,
              "reviewRating": {"@type": "Rating", "ratingValue": p["valoracion"], "bestRating": 5, "worstRating": 1},
              "author": {"@type": "Person", "name": AUTOR, "url": f"{URL}/p/los-zombis.html"},
              "isPartOf": {"@type": "WebSite", "name": "Atlas del cine de zombis", "url": f"{URL}/"}}
    if p.get("publicado"):
        resena["datePublished"] = str(p["publicado"])
    return json_ld(resena)


def escribir_mapa():
    """sitemap.xml con todas las páginas públicas, y robots.txt que lo anuncia."""
    from xml.sax.saxutils import escape
    lineas = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for direccion, fecha in MAPA:
        extra = f"<lastmod>{fecha}</lastmod>" if fecha else ""
        lineas.append(f"  <url><loc>{escape(direccion)}</loc>{extra}</url>")
    lineas.append("</urlset>")
    (SALIDA / "sitemap.xml").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    (SALIDA / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n", encoding="utf-8")


DESCARTES = yaml.safe_load((RAIZ / "contenido" / "descartadas.yml").read_text(encoding="utf-8"))


def lista_descartes(grupo):
    """Películas descartadas por un criterio de «Sobre el atlas»: título en España y año, y debajo el original."""
    from html import escape
    pelis = sorted((p for p in DESCARTES if p["grupo"] == grupo),
                   key=lambda p: (p.get("anio") or 9999, normalizar(p["titulo"])))
    if not pelis:
        return ""
    filas = "".join(
        f'<li><span class="descarte-titulo">{escape(p["titulo"])}</span>'
        f' <span class="descarte-anio">{p.get("anio") or "s. f."}</span>'
        + (f'<span class="descarte-original">{escape(p["original"])}</span>'
           if p.get("original") and normalizar(p["original"]) != normalizar(p["titulo"]) else "")
        + "</li>"
        for p in pelis)
    n = len(pelis)
    texto = "película descartada" if n == 1 else "películas descartadas"
    return (f'<details class="descartes"><summary>{n} {texto}</summary>'
            f'<ul class="descartes-lista">{filas}</ul></details>')


CRITERIO = re.compile(r"<p>(<strong>[^<]+</strong>(?:(?!</?p>).)*)</p>\s*<!-- descartes:([\w-]+) -->", re.S)


def criterios_descarte(html):
    """Une cada criterio («**Nombre.** Definición.») con su lista de películas descartadas."""
    return CRITERIO.sub(lambda m: (f'<div class="criterio" id="descartes-{m.group(2)}">'
                                   f'<p>{m.group(1)}</p>{lista_descartes(m.group(2))}</div>'), html)


def construir():
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    shutil.copytree(RAIZ / "estatico", SALIDA)
    preparar_imagenes()
    preparar_cubierta()
    escribir_canal()
    escribir_indice_busqueda()

    ultima_fecha = str(ULTIMAS[0]["publicado"]) if ULTIMAS else None
    escribir("index.html", "inicio.html", seccion="atlas", columnas=COLUMNAS, decadas=DECADAS, max_por_anio=MAX_POR_ANIO,
             ultimas=ULTIMAS[:5],
             titulo_pagina="Atlas del cine de zombis",
             descripcion=f"{len(PELICULAS)} películas de zombis comentadas y valoradas, de {PELICULAS[0]['anio']} a {ANIO_MAX}.",
             lastmod=ultima_fecha,
             jsonld=json_ld({"@context": "https://schema.org", "@type": "WebSite", "name": "Atlas del cine de zombis",
                             "url": f"{URL}/", "inLanguage": "es", "author": {"@type": "Person", "name": AUTOR},
                             "potentialAction": {"@type": "SearchAction",
                                                 "target": {"@type": "EntryPoint", "urlTemplate": f"{URL}/p/buscar.html?q={{search_term_string}}"},
                                                 "query-input": "required name=search_term_string"}}))

    for p in PELICULAS:
        raiz = prefijo(p["ruta"])
        canonica = f"{URL}{p['ruta']}"
        compartir = COMPARTIR
        if p.get("cartel"):
            ancho, alto = p.get("cartel_tamano") or (None, None)
            compartir = {"url": f"{URL}/img/carteles/{p['cartel']}", "ancho": ancho, "alto": alto,
                         "tarjeta": "summary", "alt": f"Cartel de {p['titulo']}"}
        escribir(p["ruta"], "pelicula.html", seccion="", p=p, texto=md_a_html(p["cuerpo"], raiz),
                 titulo_pagina=f"{p['titulo']} ({p['anio']}). Atlas del cine de zombis",
                 descripcion=resumen(p["cuerpo"]), canonica=canonica, compartir=compartir, og_tipo="article",
                 lastmod=str(p.get("actualizado") or p.get("publicado") or "") or None,
                 jsonld=datos_ficha(p, canonica))

    for meta, cuerpo in PAGINAS:
        seccion = "sagas" if "sagas" in meta["ruta"] else "sobre"
        html_pagina = criterios_descarte(md_a_html(cuerpo, prefijo(meta["ruta"]), anclas=True))
        escribir(meta["ruta"], "pagina.html", seccion=seccion, meta=meta, ruta_actual=meta["ruta"],
                 texto=html_pagina,
                 titulo_pagina=f"{meta['titulo']}. Atlas del cine de zombis",
                 descripcion=meta.get("descripcion") or resumen(cuerpo))

    letras = {}
    for p in sorted(PELICULAS, key=lambda p: (p["orden"], p["anio"])):
        inicial = p["orden"][0].upper() if p["orden"][0].isalpha() else "#"
        letras.setdefault(inicial, []).append(p)
    escribir("/p/peliculas-comentadas.html", "indice.html", seccion="indice", letras=letras,
             titulo_pagina="Índice de la A a la Z. Atlas del cine de zombis",
             descripcion="Todas las películas del atlas, por orden alfabético.", lastmod=ultima_fecha)

    grupos = [(v, [p for p in PELICULAS if p["valoracion"] == v]) for v in (5, 4, 3)]
    escribir("/p/las-mejores.html", "mejores.html", seccion="mejores", grupos=grupos,
             titulo_pagina="Mejor valoradas. Atlas del cine de zombis",
             descripcion="Las películas de zombis que he puntuado con 3, 4 o 5 manchas de sangre.", lastmod=ultima_fecha)

    escribir("/p/buscar.html", "buscar.html", seccion="buscar",
             titulo_pagina="Buscar en las reseñas. Atlas del cine de zombis",
             descripcion="Busca cualquier palabra en las reseñas del atlas: títulos, directores, actores, países o lo que quieras.")

    escribir("404.html", "404.html", seccion="", titulo_pagina="Página no encontrada. Atlas del cine de zombis",
             descripcion="", canonica="")
    escribir_mapa()
    print(f"Web generada en {SALIDA.relative_to(RAIZ)}/: {len(PELICULAS)} películas.")


if __name__ == "__main__":
    construir()
