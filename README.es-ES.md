

[![CI](https://github.com/amrrs/Google-Play-Store-Review-Extractor/actions/workflows/tests.yml/badge.svg)](https://github.com/amrrs/Google-Play-Store-Review-Extractor/actions/workflows/tests.yml)

# Extractor de Reseñas de Google Play Store

Utilidad moderna de línea de comandos para descargar las reseñas de una aplicación de Android desde la Google Play Store. La versión original de este proyecto dependía de un flujo de trabajo de Selenium con código rígido que ya no funcionaba con la interfaz de la Play Store. Esta herramienta actualizada utiliza la biblioteca [`google-play-scraper`](https://pypi.org/project/google-play-scraper/) para acceder a las reseñas directamente mediante solicitudes HTTP, lo que la hace más rápida y fiable.

## Características

- Obtén reseñas de cualquier aplicación pública de la Play Store por su ID (por ejemplo, `com.spotify.music`).
- Elige el número de reseñas, idioma, país y orden de clasificación.
- Filtrado opcional por puntuación de estrellas.
- Guarda las reseñas en formato CSV o JSON.
- CLI amigable con valores predeterminados lógicos y mensajes de error útiles.

## Requisitos

- Python 3.9 o más reciente
- [`google-play-scraper`](https://pypi.org/project/google-play-scraper/)

Instala la dependencia con:

```bash
pip install google-play-scraper
```

## Uso

Ejecuta el script directamente con Python. Los ejemplos a continuación asumen que el directorio de trabajo actual es la raíz del repositorio.

### Descargar reseñas a CSV (predeterminado)

```bash
python reviews_extraction.py com.spotify.music --count 200
```

El comando anterior guarda hasta 200 de las reseñas en inglés más recientes de la tienda de EE. UU. en el archivo `com_spotify_music_reviews.csv`.

### Personalizar solicitudes

- Usa `--lang` y `--country` para solicitar una configuración regional específica.
- Usa `--sort` con una de las opciones: `relevant`, `newest` (predeterminado) o `rating`.
- Usa `--score` para conservar solo las reseñas con una puntuación específica de estrellas (1-5).

```bash
python reviews_extraction.py com.nintendo.zara --count 100 --lang fr --country ca --sort rating --score 5
```

### Salida en JSON

```bash
python reviews_extraction.py com.spotify.music --format json --output spotify.json
```

Si se omite `--output` al usar `--format json`, el documento JSON se escribe en la salida estándar (stdout).

### Sobrescribir archivos

Para reemplazar un archivo de salida existente, pasa `--overwrite`:

```bash
python reviews_extraction.py com.spotify.music -n 50 --overwrite
```

## Columnas de salida (CSV)

El generador de CSV guarda las siguientes columnas:

- `review_id`
- `user_name`
- `user_image`
- `score`
- `thumbs_up_count`
- `review_created_version`
- `app_version`
- `content`
- `reply_content`
- `at` (marca de tiempo ISO 8601)
- `replied_at` (marca de tiempo ISO 8601)

## Solución de problemas

- **Salida vacía** – es posible que la configuración regional o los filtros seleccionados no tengan reseñas.
- **Errores HTTP** – inténtalo de nuevo más tarde; la biblioteca respeta los límites de tasa de Google, pero la Play Store bloquea temporalmente las solicitudes repetidas de forma ocasional.

No dudes en abrir un issue o enviar un PR si encuentras un error o tienes ideas para mejorarla.
