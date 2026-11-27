#!/usr/bin/env python3
"""Genera el libro del Atlas del cine de zombis en PDF y EPUB a partir del mismo contenido que la web.

Uso:  python3 libro/generar_libro.py
Necesita pandoc y XeLaTeX (TeX Live con el idioma español). El resultado se guarda en
estatico/libro/, de donde lo toma la web para ofrecer la descarga.
"""
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

LIBRO = Path(__file__).resolve().parent
RAIZ = LIBRO.parent
sys.path.insert(0, str(RAIZ))
import build  # noqa: E402

AJUSTES = yaml.safe_load((LIBRO / "libro.yml").read_text(encoding="utf-8"))
TRABAJO = LIBRO / "_construccion"
DESTINO = RAIZ / "estatico" / "libro"
NOMBRE = AJUSTES["archivo"]
MESES = build.MESES
HOY = date.today()
FECHA_EDICION = f"{MESES[HOY.month - 1]} de {HOY.year}"
ID = {p["ruta"]: "p-" + p["id"] for p in build.PELICULAS}


def tex(texto):
    """Escapa un texto corto para LaTeX."""
    reemplazos = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
                  "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}"}
    return "".join(reemplazos.get(c, c) for c in texto)


def enlaces(md):
    """zb:/ruta pasa a enlace interno del libro; los enlaces externos se quedan en texto."""
    def interno(m):
        destino = ID.get(m.group(2))
        return f"[{m.group(1)}](#{destino})" if destino else m.group(1)
    md = re.sub(r"\[([^\]]+)\]\(zb:([^)]+)\)", interno, md)
    md = re.sub(r"\[([^\]]+)\]\((?:https?|mailto):[^)]*\)", r"\1", md)
    return rayas(md)


def rayas(md):
    """Incisos escritos con guiones ( -así- ) pasan a rayas ( —así— ), como pide la ortografía."""
    return re.sub(r"(?<=[\s(“\"])-(?=[^\s\d-])([^\n]{1,240}?[^\s-])-(?=[\s.,;:)”\"!?…])", r"—\1—", md)


def leer_pagina(nombre):
    meta, cuerpo = build.leer(RAIZ / "contenido" / "paginas" / f"{nombre}.md")
    return meta, cuerpo


def introduccion():
    _, cuerpo = leer_pagina("sobre")
    parrafos = cuerpo.split("\n\n")
    # Fuera la nota del atlas (primer párrafo en cursiva) y el saludo final de la web.
    parrafos = [p for p in parrafos if not p.startswith("*Este atlas") and "Gracias por visitarnos" not in p]
    return enlaces("\n\n".join(parrafos))


def sagas():
    _, cuerpo = leer_pagina("sagas")
    return enlaces(cuerpo)


NOTA = f"""Este libro reúne las {len(build.PELICULAS)} reseñas que se publicaron en el blog ZombisBlog entre marzo de 2012 y diciembre de 2016. Los textos se reproducen tal y como aparecieron en el blog, con ajustes únicamente tipográficos; se han suprimido los carteles y los vídeos que acompañaban a cada entrada.

Las películas se ordenan por año de estreno y se agrupan por décadas; dentro de cada año siguen el orden alfabético. Cada reseña conserva la valoración original, de una a cinco manchas de sangre. La introducción recoge los criterios con los que se decidió qué es una película de zombis y cuáles entraban en la revisión.

Al final del volumen se incluyen las sagas y remakes, las películas mejor valoradas y un índice alfabético de títulos."""


def cuerpo(formato):
    """Markdown completo del libro. formato: 'pdf' (con LaTeX en bruto) o 'epub'."""
    pdf = formato == "pdf"
    partes = []

    def crudo(latex):
        partes.append("```{=latex}\n" + latex + "\n```")

    partes.append("# Nota a esta edición {-}")
    if pdf:
        crudo(r"\markboth{Nota a esta edición}{Nota a esta edición}")
    partes.append(NOTA)
    partes.append("# Introducción {-}")
    if pdf:
        crudo(r"\markboth{Introducción}{Introducción}")
    partes.append(introduccion())
    if pdf:
        crudo(r"\mainmatter")

    for d in build.DECADAS:
        n = len(d["peliculas"])
        rango = f"{d['decada']}–{d['decada'] + 9}" if d["decada"] + 9 <= build.ANIO_MAX else f"{d['decada']}–{build.ANIO_MAX}"
        total = f"{n} {'película' if n == 1 else 'películas'}"
        if pdf:
            crudo(rf"\decada{{d{d['decada']}}}{{{d['decada']}}}{{{rango}}}{{{total}}}")
        else:
            partes.append(f"# {rango} {{#d{d['decada']}}}")
            partes.append(f"*{total}*")
        for p in d["peliculas"]:
            ident = "p-" + p["id"]
            if pdf:
                crudo(rf"\pelicula{{{ident}}}{{{p['anio']}}}{{{p['valoracion']}}}{{{tex(p['titulo'])}}}")
            else:
                partes.append(f"## {p['titulo']} {{#{ident}}}")
                partes.append(f'[{p["anio"]}\\. Valoración: {p["valoracion"]} de 5.]{{.ficha}}')
            partes.append(enlaces(p["cuerpo"]))

    if pdf:
        crudo(r"\backmatter")
    partes.append("# Sagas y remakes {-}")
    if pdf:
        crudo(r"\markboth{Sagas y remakes}{Sagas y remakes}")
    partes.append(sagas())

    partes.append("# Las mejor valoradas {-}")
    if pdf:
        crudo(r"\markboth{Las mejor valoradas}{Las mejor valoradas}")
    for v in (5, 4, 3):
        pelis = [p for p in build.PELICULAS if p["valoracion"] == v]
        partes.append(f"## Con {v} manchas {{-}}")
        if pdf:
            filas = "\n".join(rf"\noindent\hyperlink{{p-{p['id']}}}{{{tex(p['titulo'])} ({p['anio']})}}\dotfill\pageref{{p-{p['id']}}}\par" for p in pelis)
            crudo("{\\small\\setlength{\\parskip}{1pt}\n" + filas + "\n}")
        else:
            partes.append("\n".join(f"- [{p['titulo']} ({p['anio']})](#p-{p['id']})" for p in pelis))

    partes.append("# Índice alfabético {-}")
    orden = sorted(build.PELICULAS, key=lambda p: (p["orden"], p["anio"]))
    if pdf:
        crudo(r"\markboth{Índice alfabético}{Índice alfabético}")
        filas, letra = [], None
        for p in orden:
            inicial = p["orden"][0].upper() if p["orden"][0].isalpha() else "#"
            if inicial != letra:
                letra = inicial
                filas.append(rf"\par\vspace{{5pt}}{{\noindent\displaymedia\fontsize{{12}}{{14}}\selectfont\color{{liquen}} {tex(inicial)}\par}}\nobreak\vspace{{1pt}}")
            filas.append(rf"\noindent\hangindent=1em\hyperlink{{p-{p['id']}}}{{{tex(p['titulo'])}, {p['anio']}}}\dotfill\pageref{{p-{p['id']}}}\par")
        crudo("\\begin{multicols}{2}\\footnotesize\\setlength{\\parskip}{.5pt}\\raggedright\n" + "\n".join(filas) + "\n\\end{multicols}")
    else:
        partes.append("\n".join(f"- [{p['titulo']} ({p['anio']})](#p-{p['id']})" for p in orden))

    return "\n\n".join(partes) + "\n"


def metadatos(formato):
    datos = {
        "title": "Atlas del cine de zombis",
        "subtitle": AJUSTES["subtitulo"],
        "author": AJUSTES["autor"],
        "lang": "es-ES",
        "rights": "CC BY-NC-SA 4.0. Textos de Miguel Ángel Gómez Ruiz, 2012-2016.",
        "date": str(HOY.year),
        "description": f"Las {len(build.PELICULAS)} reseñas de películas de zombis publicadas originalmente en el blog ZombisBlog entre 2012 y 2016.",
        "fecha_edicion": FECHA_EDICION,
        "total": len(build.PELICULAS),
        "url_web": AJUSTES.get("url_web") or "",
        "doi": AJUSTES.get("doi") or "",
        "isbn": AJUSTES.get("isbn") or "",
    }
    if AJUSTES.get("doi"):
        datos["identifier"] = [{"scheme": "DOI", "text": AJUSTES["doi"]}]
    if formato == "epub":
        datos["cover-image"] = str(LIBRO / "portada.png")
        datos["css"] = str(LIBRO / "epub.css")
    return "---\n" + yaml.safe_dump(datos, allow_unicode=True, sort_keys=False) + "---\n\n"


def ejecutar(orden, carpeta):
    r = subprocess.run(orden, cwd=carpeta, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Error al ejecutar {' '.join(map(str, orden[:2]))}:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r


def generar_pdf():
    md = TRABAJO / "libro-pdf.md"
    md.write_text(metadatos("pdf") + cuerpo("pdf"), encoding="utf-8")
    for nombre in ("fuentes", "img"):
        destino = TRABAJO / nombre
        if destino.exists():
            shutil.rmtree(destino)
        shutil.copytree(LIBRO / nombre, destino)
    shutil.copy(LIBRO / "portada.pdf", TRABAJO / "portada.pdf")
    ejecutar(["pandoc", md.name, "-f", "markdown+smart", "-t", "latex", "--standalone",
              "--template", str(LIBRO / "plantilla.tex"), "--top-level-division=chapter",
              "-o", "libro.tex"], TRABAJO)
    # Tras una raya de apertura no se corta la línea, pero la palabra siguiente sí puede dividirse.
    texto = (TRABAJO / "libro.tex").read_text(encoding="utf-8")
    cabecera, cuerpo_tex = texto.split("\\begin{document}", 1)
    cuerpo_tex = cuerpo_tex.replace("---", "—")
    cuerpo_tex = re.sub(r"(?<=\s)—(?=\w)", r"—\\nobreak\\hspace{0pt}", cuerpo_tex)
    cuerpo_tex = re.sub(r"(?<=[\w.!?…])—(?=[\s.,;:)'!?…])", r"\\nobreak\\hspace{0pt}—", cuerpo_tex)
    texto = cabecera + "\\begin{document}" + cuerpo_tex
    (TRABAJO / "libro.tex").write_text(texto, encoding="utf-8")
    for _ in range(3):  # tres pasadas para el índice y las referencias de página
        ejecutar(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "libro.tex"], TRABAJO)
    shutil.copy(TRABAJO / "libro.pdf", DESTINO / f"{NOMBRE}.pdf")


def generar_epub():
    md = TRABAJO / "libro-epub.md"
    md.write_text(metadatos("epub") + cuerpo("epub"), encoding="utf-8")
    orden = ["pandoc", md.name, "-f", "markdown+smart", "-t", "epub3", "--toc", "--toc-depth=1",
             "--split-level=1", "-o", str(DESTINO / f"{NOMBRE}.epub")]
    for f in ("Literata-Regular", "Literata-Italic", "Literata-Bold", "Literata-BoldItalic",
              "BigShouldersDisplay-ExtraBold"):
        orden += ["--epub-embed-font", str(LIBRO / "fuentes" / f"{f}.ttf")]
    ejecutar(orden, TRABAJO)


if __name__ == "__main__":
    TRABAJO.mkdir(exist_ok=True)
    DESTINO.mkdir(parents=True, exist_ok=True)
    generar_pdf()
    generar_epub()
    print(f"Libro generado en estatico/libro/: {NOMBRE}.pdf y {NOMBRE}.epub")
