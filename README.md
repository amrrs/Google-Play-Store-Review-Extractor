[![CI](https://github.com/amrrs/Google-Play-Store-Review-Extractor/actions/workflows/tests.yml/badge.svg)](https://github.com/amrrs/Google-Play-Store-Review-Extractor/actions/workflows/tests.yml)

# Google Play Store Review Extractor

Modern command line utility for downloading reviews of an Android application
from the Google Play Store. The original version of this project relied on a
hard-coded Selenium workflow that no longer worked with the Play Store UI. This
updated tool uses the [`google-play-scraper`](https://pypi.org/project/google-play-scraper/)
library to access reviews directly via HTTP requests, making it faster and more
reliable.

## Features

- Fetch reviews for any public Play Store app by app id (e.g. `com.spotify.music`).
- Choose the number of reviews, language, country and sort order.
- Optional filtering by star rating.
- Save reviews as CSV or JSON.
- Friendly CLI with sensible defaults and helpful error messages.

## Requirements

- Python 3.9 or newer
- [`google-play-scraper`](https://pypi.org/project/google-play-scraper/)

Install the dependency with:

```bash
pip install google-play-scraper
```

## Usage

Run the script directly with Python. Examples below assume the current working
directory is the repository root.

### Download reviews to CSV (default)

```bash
python reviews_extraction.py com.spotify.music --count 200
```

The command above saves up to 200 of the newest English reviews from the US
storefront into `com_spotify_music_reviews.csv`.

### Customising requests

- Use `--lang` and `--country` to request a specific locale.
- Use `--sort` with one of `relevant`, `newest` (default) or `rating`.
- Use `--score` to keep only reviews with a given star rating (1-5).

```bash
python reviews_extraction.py com.nintendo.zara --count 100 --lang fr --country ca --sort rating --score 5
```

### JSON output

```bash
python reviews_extraction.py com.spotify.music --format json --output spotify.json
```

If `--output` is omitted when using `--format json`, the JSON document is
written to stdout.

### Overwriting files

To replace an existing output file pass `--overwrite`:

```bash
python reviews_extraction.py com.spotify.music -n 50 --overwrite
```

## Output columns (CSV)

The CSV writer stores the following columns:

- `review_id`
- `user_name`
- `user_image`
- `score`
- `thumbs_up_count`
- `review_created_version`
- `app_version`
- `content`
- `reply_content`
- `at` (ISO 8601 timestamp)
- `replied_at` (ISO 8601 timestamp)

## Troubleshooting

- **Empty output** – the chosen locale or filters might not have any reviews.
- **HTTP errors** – retry later; the library respects Google rate limits but the
  Play Store occasionally blocks repeated requests temporarily.

Feel free to open an issue or submit a PR if you encounter a bug or have ideas
for improvements.

