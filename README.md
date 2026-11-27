# Atlas del cine de zombis

299 películas de zombis (1932–2016) comentadas y valoradas de una a cinco manchas de sangre. Las reseñas se publicaron originalmente en el blog ZombisBlog entre 2012 y 2016; aquí forman una web estática que no depende de ninguna plataforma de blogs. De las mismas fichas sale también el libro en PDF y EPUB.

Dirección: https://cinedezombis.github.io

## Qué hay aquí

| Carpeta o archivo | Qué contiene |
|---|---|
| `contenido/peliculas/` | Una ficha por película en Markdown: título, año, nota, fecha de publicación, cartel, tráileres y el texto de la reseña. |
| `contenido/paginas/` | Las páginas «Sobre el atlas» y «Sagas y remakes». |
| `estatico/` | Carteles, miniaturas, tipografías, estilos, el script del atlas y el libro ya generado. |
| `plantillas/` | El diseño de cada tipo de página. |
| `build.py` | Genera la web en la carpeta `_site/`. |
| `libro/` | Todo lo necesario para regenerar el libro (plantilla, cubierta, tipografías). |
| `sitio.yml` | La dirección pública de la web. |

Cada reseña conserva la ruta que tenía en el blog original (por ejemplo `/2012/04/1932-white-zombie.html`).

## Publicación en GitHub Pages

La web ocupa unos 25 MB. GitHub recomienda que un repositorio no pase de 1 GB y limita cada web publicada a 1 GB, así que hay margen de sobra, y este repositorio no afecta a los de tus juegos.

La web se publica desde el repositorio `cinedezombis/cinedezombis.github.io`. Si alguna vez hubiera que montarla de nuevo:

1. Crea un repositorio público vacío llamado `nombre.github.io` dentro de la organización o cuenta `nombre`.
2. Sube el contenido de esta carpeta, incluida la carpeta oculta `.github`, que es la que publica la web.
3. En el repositorio: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. Pon la dirección pública en `sitio.yml` (`url`) y, si la web no está en la raíz del dominio, la carpeta en `ruta_base`.

## Corregir o añadir una reseña

Abre el archivo de la película en `contenido/peliculas/`, pulsa el lápiz, cambia lo que quieras y guarda (*Commit changes*). La web se vuelve a generar sola en un par de minutos.

Para una película nueva, copia una ficha existente, cambia los datos de la cabecera (`titulo`, `anio`, `valoracion`, `publicado` y `ruta`, por ejemplo `/2027/01/2024-titulo.html`) y escribe el texto debajo. Si tiene cartel, sube la imagen a `estatico/img/carteles/` y una versión pequeña (112 px de ancho) a `estatico/img/miniaturas/` con el mismo nombre; si no, deja `cartel: null`.

## Probar la web en tu ordenador

```
pip install -r requirements.txt
python3 build.py
python3 -m http.server -d _site 8000
```

Y abre `http://localhost:8000`.

## Regenerar el libro

Hace falta pandoc, XeLaTeX (TeX Live con el paquete de español) y, para la cubierta, Playwright con Chrome:

```
python3 libro/generar_portada.py
python3 libro/generar_libro.py
```

El PDF y el EPUB se guardan en `estatico/libro/`, de donde los toma la web. Si consigues un DOI (por ejemplo, al depositarlo en Zenodo) o un ISBN, anótalos en `libro/libro.yml` antes de regenerarlo y aparecerán en la página de créditos.

## Revisión de 2026

La carpeta `revision/` recoge las erratas corregidas en las reseñas (`correcciones.csv`, con el texto antes y después) y los tráileres añadidos a las fichas que se habían quedado sin vídeo (`trailers-nuevos.csv`). Las fichas sin tráiler localizado muestran un enlace para buscarlo en YouTube.

## Licencias

Los textos tienen licencia CC BY-NC-SA 4.0; los detalles de carteles, tipografías y código están en [LICENCIA.md](LICENCIA.md).
