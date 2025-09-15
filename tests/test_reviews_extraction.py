import argparse
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest


@pytest.fixture
def reviews_extraction(monkeypatch):
    """Import ``reviews_extraction`` with a stub ``google_play_scraper`` module."""

    stub_scraper = ModuleType("google_play_scraper")

    class DummySort:
        MOST_RELEVANT = "most_relevant"
        NEWEST = "newest"
        RATING = "rating"

    stub_scraper.Sort = DummySort

    def default_reviews(*args, **kwargs):  # pragma: no cover - defensive
        raise AssertionError("tests must patch google_play_scraper.reviews")

    stub_scraper.reviews = default_reviews

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    monkeypatch.setitem(sys.modules, "google_play_scraper", stub_scraper)
    sys.modules.pop("reviews_extraction", None)
    module = importlib.import_module("reviews_extraction")
    return module


def test_positive_int_accepts_valid_value(reviews_extraction):
    assert reviews_extraction.positive_int("10") == 10


@pytest.mark.parametrize("value", ["0", "-5", "not-a-number"])
def test_positive_int_rejects_invalid_values(value, reviews_extraction):
    with pytest.raises(argparse.ArgumentTypeError):
        reviews_extraction.positive_int(value)


def test_parse_args_defaults(reviews_extraction):
    args = reviews_extraction.parse_args(["com.example.app"])
    assert args.app_id == "com.example.app"
    assert args.count == 100
    assert args.format == "csv"
    assert args.sort == "newest"
    assert args.overwrite is False


def test_parse_args_rejects_non_positive_count(reviews_extraction):
    with pytest.raises(SystemExit):
        reviews_extraction.parse_args(["--count", "0", "com.example.app"])


def test_parse_args_rejects_unknown_sort_choice(reviews_extraction):
    with pytest.raises(SystemExit):
        reviews_extraction.parse_args(["--sort", "unsupported", "com.example.app"])


def test_normalise_review_formats_fields(reviews_extraction):
    class DummyDate:
        def __init__(self, value):
            self._value = value

        def isoformat(self):
            return self._value

    review = {
        "reviewId": "r-1",
        "userName": "Alice",
        "userImage": "https://example.com/avatar.png",
        "score": 4,
        "thumbsUpCount": 7,
        "reviewCreatedVersion": "1.2.3",
        "appVersion": "1.2.4",
        "content": "Great app!",
        "replyContent": None,
        "at": DummyDate("2023-09-18T12:00:00"),
        "repliedAt": DummyDate("2023-09-19T08:30:00"),
    }

    normalised = reviews_extraction._normalise_review(review)

    assert normalised == {
        "review_id": "r-1",
        "user_name": "Alice",
        "user_image": "https://example.com/avatar.png",
        "score": 4,
        "thumbs_up_count": 7,
        "review_created_version": "1.2.3",
        "app_version": "1.2.4",
        "content": "Great app!",
        "reply_content": None,
        "at": "2023-09-18T12:00:00",
        "replied_at": "2023-09-19T08:30:00",
    }


def test_fetch_reviews_paginates_and_respects_count(reviews_extraction, monkeypatch):
    module = reviews_extraction
    sample_reviews = [
        {
            "reviewId": "id-1",
            "userName": "User 1",
            "userImage": None,
            "score": 5,
            "thumbsUpCount": 1,
            "reviewCreatedVersion": "1.0.0",
            "appVersion": "1.0.0",
            "content": "Review 1",
            "replyContent": "Reply 1",
            "at": None,
            "repliedAt": None,
        },
        {
            "reviewId": "id-2",
            "userName": "User 2",
            "userImage": None,
            "score": 4,
            "thumbsUpCount": 2,
            "reviewCreatedVersion": "1.0.1",
            "appVersion": "1.0.1",
            "content": "Review 2",
            "replyContent": "Reply 2",
            "at": None,
            "repliedAt": None,
        },
        {
            "reviewId": "id-3",
            "userName": "User 3",
            "userImage": None,
            "score": 3,
            "thumbsUpCount": 3,
            "reviewCreatedVersion": "1.0.2",
            "appVersion": "1.0.2",
            "content": "Review 3",
            "replyContent": "Reply 3",
            "at": None,
            "repliedAt": None,
        },
    ]

    responses = [
        (sample_reviews[:2], "token-1"),
        (sample_reviews[2:], None),
    ]
    call_kwargs = []

    def fake_reviews(app_id, lang, country, sort, count, continuation_token):
        call_kwargs.append(
            {
                "app_id": app_id,
                "lang": lang,
                "country": country,
                "sort": sort,
                "count": count,
                "continuation_token": continuation_token,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr(module, "reviews", fake_reviews)

    result = module.fetch_reviews(
        "com.example.app",
        lang="it",
        country="it",
        sort=module.Sort.NEWEST,
        count=3,
    )

    assert result == [module._normalise_review(review) for review in sample_reviews]
    assert call_kwargs == [
        {
            "app_id": "com.example.app",
            "lang": "it",
            "country": "it",
            "sort": module.Sort.NEWEST,
            "count": 3,
            "continuation_token": None,
        },
        {
            "app_id": "com.example.app",
            "lang": "it",
            "country": "it",
            "sort": module.Sort.NEWEST,
            "count": 1,
            "continuation_token": "token-1",
        },
    ]


def test_fetch_reviews_applies_score_filter(reviews_extraction, monkeypatch):
    module = reviews_extraction
    responses = [
        (
            [
                {"reviewId": "a", "score": 5},
                {"reviewId": "b", "score": 4},
                {"reviewId": "c", "score": 5},
            ],
            "token-next",
        ),
        (
            [
                {"reviewId": "d", "score": 5},
                {"reviewId": "e", "score": 3},
            ],
            None,
        ),
    ]
    requested_counts = []

    def fake_reviews(app_id, lang, country, sort, count, continuation_token):
        requested_counts.append((count, continuation_token))
        return responses.pop(0)

    monkeypatch.setattr(module, "reviews", fake_reviews)

    result = module.fetch_reviews(
        "com.example.app",
        count=4,
        score=5,
    )

    assert [item["review_id"] for item in result] == ["a", "c", "d"]
    assert requested_counts == [(4, None), (2, "token-next")]


def test_write_csv_outputs_rows(tmp_path, reviews_extraction):
    module = reviews_extraction
    rows = [
        {
            "review_id": "r1",
            "user_name": "Alice",
            "user_image": "img1",
            "score": 5,
            "thumbs_up_count": 10,
            "review_created_version": "1.0.0",
            "app_version": "1.0.1",
            "content": "Great",
            "reply_content": "Thanks",
            "at": "2023-01-01T00:00:00",
            "replied_at": "2023-01-02T00:00:00",
        }
    ]

    output_path = tmp_path / "reviews.csv"
    module._write_csv(rows, str(output_path))

    with output_path.open(encoding="utf-8") as file_obj:
        contents = file_obj.read().splitlines()

    assert contents[0] == (
        "review_id,user_name,user_image,score,thumbs_up_count,"
        "review_created_version,app_version,content,reply_content,at,replied_at"
    )
    assert (
        contents[1]
        == "r1,Alice,img1,5,10,1.0.0,1.0.1,Great,Thanks,2023-01-01T00:00:00,2023-01-02T00:00:00"
    )


def test_write_json_persists_data(tmp_path, reviews_extraction):
    module = reviews_extraction
    rows = (
        {
            "review_id": "r1",
            "score": 5,
        },
        {
            "review_id": "r2",
            "score": 3,
        },
    )

    output_path = tmp_path / "reviews.json"
    module._write_json(rows, str(output_path))

    text = output_path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == [
        {"review_id": "r1", "score": 5},
        {"review_id": "r2", "score": 3},
    ]


def test_main_refuses_to_overwrite_existing_file(tmp_path, reviews_extraction, monkeypatch, capsys):
    module = reviews_extraction
    existing_path = tmp_path / "existing.csv"
    existing_path.write_text("original", encoding="utf-8")

    fake_fetch = Mock(return_value=[{"review_id": "r1"}])
    monkeypatch.setattr(module, "fetch_reviews", fake_fetch)

    exit_code = module.main(["com.example.app", "--output", str(existing_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Refusing to overwrite" in captured.err
    fake_fetch.assert_called_once()
    assert existing_path.read_text(encoding="utf-8") == "original"
