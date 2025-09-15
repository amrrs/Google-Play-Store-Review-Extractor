#!/usr/bin/env python3
"""Command line tool for downloading Google Play Store reviews."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence

from google_play_scraper import Sort, reviews


SORT_CHOICES = {
    "relevant": Sort.MOST_RELEVANT,
    "newest": Sort.NEWEST,
    "rating": Sort.RATING,
}


def positive_int(value: str) -> int:
    """Argparse helper that ensures a strictly positive integer."""

    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise argparse.ArgumentTypeError(str(exc)) from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Download Google Play Store reviews for the given app id and "
            "save them to a CSV or JSON file."
        )
    )

    parser.add_argument(
        "app_id",
        help="Google Play application id, e.g. com.spotify.music",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=positive_int,
        default=100,
        help="Maximum number of reviews to download (default: %(default)s).",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Two-letter language code to request (default: %(default)s).",
        metavar="LANG",
    )
    parser.add_argument(
        "--country",
        default="us",
        help="Two-letter country code to request (default: %(default)s).",
        metavar="COUNTRY",
    )
    parser.add_argument(
        "--sort",
        choices=sorted(SORT_CHOICES.keys()),
        default="newest",
        help="Sort order to use for reviews (default: %(default)s).",
    )
    parser.add_argument(
        "--score",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Optional star rating (1-5) to filter reviews after download.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path. Defaults to <app-id>.<format> for file output.",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: %(default)s).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing output file.",
    )

    return parser.parse_args(argv)


def _isoformat(value):
    """Return ISO formatted timestamps or ``None`` for non-datetime values."""

    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value if value is not None else None


def _normalise_review(review: Dict[str, object]) -> Dict[str, object]:
    """Convert the google-play-scraper review into a serialisable dict."""

    return {
        "review_id": review.get("reviewId"),
        "user_name": review.get("userName"),
        "user_image": review.get("userImage"),
        "score": review.get("score"),
        "thumbs_up_count": review.get("thumbsUpCount"),
        "review_created_version": review.get("reviewCreatedVersion"),
        "app_version": review.get("appVersion"),
        "content": review.get("content"),
        "reply_content": review.get("replyContent"),
        "at": _isoformat(review.get("at")),
        "replied_at": _isoformat(review.get("repliedAt")),
    }


def fetch_reviews(
    app_id: str,
    *,
    lang: str = "en",
    country: str = "us",
    sort: Sort = Sort.NEWEST,
    count: int = 100,
    score: Optional[int] = None,
) -> List[Dict[str, object]]:
    """Download reviews using ``google-play-scraper``.

    Parameters are equivalent to the CLI flags. ``count`` controls the maximum
    number of reviews returned after normalisation. When ``score`` is provided,
    the filter happens after fetching reviews from Google Play; therefore fewer
    than ``count`` items may be returned if there are not enough matching
    entries.
    """

    collected: List[Dict[str, object]] = []
    token = None

    while len(collected) < count:
        batch_size = min(200, count - len(collected))
        result, token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=sort,
            count=batch_size,
            continuation_token=token,
        )

        if not result:
            break

        if score is not None:
            result = [item for item in result if item.get("score") == score]

        for item in result:
            collected.append(_normalise_review(item))
            if len(collected) >= count:
                break

        if not token:
            break

    return collected


def _write_csv(rows: Iterable[Dict[str, object]], path: str) -> None:
    """Persist rows to ``path`` in CSV format."""

    rows = list(rows)
    fieldnames = [
        "review_id",
        "user_name",
        "user_image",
        "score",
        "thumbs_up_count",
        "review_created_version",
        "app_version",
        "content",
        "reply_content",
        "at",
        "replied_at",
    ]

    with open(path, "w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(rows: Iterable[Dict[str, object]], path: Optional[str]) -> None:
    """Persist rows as JSON. When ``path`` is ``None`` output to stdout."""

    serialisable = list(rows)

    if path:
        with open(path, "w", encoding="utf-8") as file_obj:
            json.dump(serialisable, file_obj, indent=2, ensure_ascii=False)
            file_obj.write("\n")
    else:
        json.dump(serialisable, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the CLI."""

    args = parse_args(argv)
    sort = SORT_CHOICES[args.sort]

    try:
        reviews_list = fetch_reviews(
            args.app_id,
            lang=args.lang,
            country=args.country,
            sort=sort,
            count=args.count,
            score=args.score,
        )
    except Exception as exc:  # pragma: no cover - defensive programming
        print(f"Failed to download reviews: {exc}", file=sys.stderr)
        return 1

    if not reviews_list:
        print("No reviews returned for the specified parameters.", file=sys.stderr)
        return 0

    if args.format == "csv":
        output_path = args.output or f"{args.app_id.replace('.', '_')}_reviews.csv"
        if os.path.exists(output_path) and not args.overwrite:
            print(
                f"Refusing to overwrite existing file '{output_path}'. "
                "Use --overwrite to replace it.",
                file=sys.stderr,
            )
            return 1
        _write_csv(reviews_list, output_path)
        print(f"Saved {len(reviews_list)} reviews to {output_path}")
    else:
        output_path = args.output
        if output_path and os.path.exists(output_path) and not args.overwrite:
            print(
                f"Refusing to overwrite existing file '{output_path}'. "
                "Use --overwrite to replace it.",
                file=sys.stderr,
            )
            return 1
        _write_json(reviews_list, output_path)
        if output_path:
            print(f"Saved {len(reviews_list)} reviews to {output_path}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

