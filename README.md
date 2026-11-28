# Atlas del cine de zombis

Películas de zombis comentadas y valoradas de una a cinco manchas de sangre. Las primeras 299 reseñas (de 1932 a 2016) se publicaron en el blog ZombisBlog entre 2012 y 2016; aquí forman una web estática que no depende de ninguna plataforma de blogs y que desde 2026 sigue creciendo. De esas fichas sale también el libro en PDF y EPUB.

Dirección: https://cinedezombis.github.io

## Qué hay aquí

| Carpeta o archivo | Qué contiene |
|---|---|
| `contenido/peliculas/` | Una ficha por película en Markdown: título, año, nota, fecha de publicación, cartel, tráileres y el texto de la reseña. |
| `contenido/paginas/` | Las páginas de «Sobre el atlas» (`sobre.md`, `cine.md` y `descartadas.md`) y «Sagas y remakes». Las que llevan `menu` y `orden` en la cabecera forman el desplegable «Sobre el atlas», en ese orden. |
| `contenido/descartadas.yml` | Las películas revisadas que no entran en el atlas, con el criterio que las deja fuera. |
| `estatico/` | Carteles, miniaturas, tipografías, estilos, el script del atlas y el libro ya generado. |
| `plantillas/` | El diseño de cada tipo de página. |
| `build.py` | Genera la web en la carpeta `_site/`. |
| `libro/` | Todo lo necesario para regenerar el libro (plantilla, cubierta, tipografías). |
| `herramientas/` | Utilidades que se usan rara vez, como la que crea la imagen para compartir en redes. |
| `sitio.yml` | La dirección pública de la web, el DOI del libro y el contador de visitas. |

Cada reseña conserva la ruta que tenía en el blog original (por ejemplo `/2012/04/1932-white-zombie.html`).

## Publicación en GitHub Pages

La web ocupa unos 25 MB. GitHub recomienda que un repositorio no pase de 1 GB y limita cada web publicada a 1 GB, así que hay margen de sobra, y este repositorio no afecta a los de tus juegos.

La web se publica desde el repositorio `cinedezombis/cinedezombis.github.io`. Si alguna vez hubiera que montarla de nuevo:

1. Crea un repositorio público vacío llamado `nombre.github.io` dentro de la organización o cuenta `nombre`.
2. Sube el contenido de esta carpeta, incluida la carpeta oculta `.github`, que es la que publica la web.
3. En el repositorio: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. Pon la dirección pública en `sitio.yml` (`url`) y, si la web no está en la raíz del dominio, la carpeta en `ruta_base`.

## Añadir una película nueva

Todo se hace desde la propia web de GitHub, sin instalar nada:

1. Abre `contenido/plantilla-nueva-pelicula.md` y copia su contenido.
2. Entra en la carpeta `contenido/peliculas/`, pulsa **Add file → Create new file** y llama al archivo con el año y el título en minúsculas, sin tildes y con guiones: `2024-titulo-de-la-pelicula.md`.
3. Pega la plantilla, rellena título, año, valoración (1 a 5), fecha y enlace del tráiler, y escribe la reseña debajo. Pulsa **Commit changes**.
4. Si tienes el cartel, entra en `estatico/img/carteles/`, pulsa **Add file → Upload files** y súbelo con el mismo nombre que la ficha (`2024-titulo-de-la-pelicula.jpg`, también vale .png o .webp, de cualquier tamaño). La miniatura y el tamaño adecuado se generan solos.

En uno o dos minutos la película aparece en el atlas: se actualizan el número de la portada, el gráfico (que se alarga hasta el año más reciente), el listado por décadas, el índice de la A a la Z y las mejor valoradas. Las reseñas nuevas muestran «Publicada en el atlas el…» en lugar de la referencia a ZombisBlog.

El libro no cambia: es la edición fija de las reseñas de 2012–2016.

## Lo que la web genera sola

Cada vez que cambias algo, `build.py` vuelve a crear, además de las páginas:

- las miniaturas y los carteles en WebP, más ligeros que los JPG (los JPG se conservan para compartir en redes);
- el índice del buscador (`buscar.json`) y el canal de novedades por RSS (`feed.xml`);
- `sitemap.xml` y `robots.txt`, para que los buscadores encuentren todas las fichas;
- las etiquetas para compartir: al pegar el enlace de una ficha en WhatsApp, Telegram o una red social aparece su cartel, y en las demás páginas la imagen `estatico/img/compartir.png`;
- los datos estructurados (JSON-LD) que permiten a Google mostrar la nota de cada reseña.

Los enlaces de «Sagas y remakes» que aparecen en cada ficha salen de las listas de `contenido/paginas/sagas.md`: basta con añadir una película a la lista de su saga.

La web tiene modo oscuro (paleta «Sala oscura»): se activa sola cuando el móvil o el ordenador del lector lo tiene puesto.

Si cambias los colores o las tipografías, vuelve a crear la imagen para compartir:

```
python3 herramientas/generar_compartir.py
```

## Estadísticas de visitas

Las visitas se cuentan con GoatCounter, sin cookies ni datos personales, así que no hace falta aviso de cookies. El panel está en https://cinedezombis.goatcounter.com. Para desactivar el contador, deja vacío `goatcounter` en `sitio.yml`.

## Registrar una película descartada

Las películas que revisas y no cumplen los criterios se apuntan en `contenido/descartadas.yml` y aparecen en la página «Películas descartadas», en el desplegable de su criterio, y en el buscador.

1. Abre `contenido/descartadas.yml` y pulsa el lápiz.
2. Copia una entrada y cambia los datos:

   ```
   - grupo: infectados
     titulo: 28 días después
     original: 28 Days Later
     anio: 2002
   ```

   `grupo` es el criterio: `infectados`, `posesiones`, `fantasmas`, `hipnotizados`, `animales`, `mutantes`, `sin-muertos`, `esqueletos`, `cortos`, `documentales`, `animacion` o `musicales`. `titulo` es el título en España y `original`, el original; si coinciden, el original no se muestra.
3. Guarda con **Commit changes**.

Apunta solo las películas cuyo motivo tengas claro. Los vampiros, momias y demás figuras con imaginario propio no se apuntan: son demasiadas. Las definiciones de los criterios están en `contenido/paginas/descartadas.md`; si añades un criterio nuevo, pon debajo de su párrafo la marca `<!-- descartes:nombre -->` y usa ese nombre como `grupo`.

## Corregir una reseña

Abre el archivo de la película en `contenido/peliculas/`, pulsa el lápiz, cambia lo que quieras y guarda con **Commit changes**. La web se vuelve a generar sola.

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

El PDF y el EPUB se guardan en `estatico/libro/`, de donde los toma la web. El DOI, el ISBN y el subtítulo están en `libro/libro.yml`: lo que anotes allí aparece en la cubierta, la portada, los créditos y la contraportada.

`generar_portada.py` crea la cubierta (los títulos de todas las películas alrededor del título) y la contraportada (texto de presentación y gráfico del atlas). Los colores los toma de las variables del principio de `estatico/css/estilo.css` (paleta «Celuloide»), así que, si cambias la paleta de la web, basta con volver a generar la cubierta y el libro para que coincidan.

## Revisión de 2026

La carpeta `revision/` recoge las erratas corregidas en las reseñas (`correcciones.csv`, con el texto antes y después) y los tráileres añadidos a las fichas que se habían quedado sin vídeo (`trailers-nuevos.csv`). Las fichas sin tráiler localizado muestran un enlace para buscarlo en YouTube.

## Licencias

Los textos tienen licencia CC BY-NC-SA 4.0; los detalles de carteles, tipografías y código están en [LICENCIA.md](LICENCIA.md).
