"""Tests para los scrapers."""

import pytest

from app.scrapers.grantsgov import GrantsGovScraper, _extract_sectors, _parse_date, _usd_to_cop
from app.scrapers.rss_feeds import (
    FeedSource,
    RssFeedsScraper,
    _clean_html,
    _extract_categories,
    _extract_deadline,
)


# ── Grants.gov: helpers ──────────────────────────────────────────────────────


def test_parse_date_us_format():
    d = _parse_date("04/30/2026")
    assert d is not None
    assert d.year == 2026
    assert d.month == 4
    assert d.day == 30


def test_parse_date_iso_format():
    d = _parse_date("2026-04-30")
    assert d is not None
    assert d.year == 2026


def test_parse_date_none():
    assert _parse_date(None) is None


def test_parse_date_invalid():
    assert _parse_date("not-a-date") is None


def test_usd_to_cop():
    cop = _usd_to_cop(1000)
    assert cop is not None
    assert cop > 1_000_000  # 1000 USD >> 1M COP aprox


def test_usd_to_cop_none():
    assert _usd_to_cop(None) is None


def test_extract_sectors_with_cfda_list():
    raw = {"cfdaList": ["84.282", "93.840"], "docType": "synopsis"}
    sectors = _extract_sectors(raw)
    assert "cfda:84.282" in sectors
    assert "cfda:93.840" in sectors
    assert "synopsis" in sectors


def test_extract_sectors_empty():
    assert _extract_sectors({}) == []


# ── Grants.gov: normalize ────────────────────────────────────────────────────


def test_normalize_relevant_opportunity():
    """search2 NO devuelve synopsis ni amounts. Solo título + agency + closeDate."""
    scraper = GrantsGovScraper()
    raw = {
        "id": "12345",
        "number": "HHS-2026-ACF-OCC-CE-0001",
        "title": "Early Childhood Education Capacity Building Program",
        "agency": "Administration for Children and Families",
        "closeDate": "06/30/2026",
        "openDate": "01/01/2026",
        "oppStatus": "posted",
        "docType": "synopsis",
        "cfdaList": ["84.282"],
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert "Early Childhood" in result.title
    assert result.deadline is not None
    assert result.deadline.year == 2026
    assert result.source_name == "grantsgov"
    assert result.funder_name == "Administration for Children and Families"
    # search2 no expone amounts → None
    assert result.amount_max_cop is None
    assert result.amount_min_cop is None
    # URL construida con id
    assert "12345" in (result.url_rfp or "")


def test_normalize_uses_agency_first_then_agencyName():
    """Fallback al campo 'agencyName' si 'agency' no existe."""
    scraper = GrantsGovScraper()
    raw = {
        "id": "1",
        "title": "Early Childhood Initiative",
        "agencyName": "Fallback Agency",  # solo agencyName, no agency
        "closeDate": "12/31/2026",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.funder_name == "Fallback Agency"


def test_normalize_missing_title():
    scraper = GrantsGovScraper()
    result = scraper.normalize({"id": "1", "title": "", "agency": "Test"})
    assert result is None


def test_normalize_no_deadline():
    """Sin closeDate, debe devolver opp con deadline=None (no rompe)."""
    scraper = GrantsGovScraper()
    raw = {"id": "1", "title": "Early Childhood Grant", "agency": "Test Agency"}
    result = scraper.normalize(raw)
    assert result is not None
    assert result.deadline is None


# ── RSS Feeds: helpers ────────────────────────────────────────────────────────


def test_clean_html_removes_tags():
    html = "<p>Hello <strong>world</strong></p>"
    assert _clean_html(html) == "Hello world"


def test_clean_html_decodes_entities():
    html = "Tom &amp; Jerry &quot;quoted&quot;"
    cleaned = _clean_html(html)
    assert "&" in cleaned
    assert '"' in cleaned
    assert "&amp;" not in cleaned


def test_clean_html_collapses_whitespace():
    html = "<p>Hello\n\n\n  world</p>"
    assert _clean_html(html) == "Hello world"


def test_extract_deadline_iso():
    entry = {}
    desc = "Apply by Deadline: 2026-06-30 for funding."
    d = _extract_deadline(entry, desc)
    assert d is not None
    assert d.year == 2026
    assert d.month == 6
    assert d.day == 30


def test_extract_deadline_us_format():
    entry = {}
    desc = "Application closes 12/31/2026."
    d = _extract_deadline(entry, desc)
    assert d is not None
    assert d.year == 2026


def test_extract_deadline_no_match():
    entry = {}
    desc = "Beautiful opportunity with no specific date mentioned."
    assert _extract_deadline(entry, desc) is None


def test_extract_categories_from_tags():
    entry = {"tags": [{"term": "early childhood"}, {"term": "education"}]}
    cats = _extract_categories(entry)
    assert "early childhood" in cats
    assert "education" in cats


def test_extract_categories_empty():
    assert _extract_categories({}) == []


# ── RSS Feeds: normalize ──────────────────────────────────────────────────────


def test_rss_normalize_relevant():
    scraper = RssFeedsScraper()
    raw = {
        "_feed": FeedSource(
            name="test_feed",
            url="https://example.org/feed",
            funder_hint="Test Foundation",
            org_website="https://example.org",
        ),
        "entry": {
            "title": "Early Childhood Development Grant",
            "summary": "Funding for ECD programs in Latin America. Deadline: 2026-09-30",
            "link": "https://example.org/grants/123",
            "author": "Test Foundation",
        },
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert "Early Childhood" in result.title
    assert result.funder_name == "Test Foundation"
    assert result.source_name == "rss:test_feed"
    assert result.url_rfp == "https://example.org/grants/123"
    assert result.deadline is not None  # extraído del summary


def test_rss_normalize_irrelevant():
    """Entry sin keywords ECD relevantes debe descartarse."""
    scraper = RssFeedsScraper()
    raw = {
        "_feed": FeedSource(name="x", url="https://x.org/feed"),
        "entry": {
            "title": "New Software Release Notes v2.1.0",
            "summary": "Bug fixes and performance improvements.",
            "link": "https://x.org/release-notes",
        },
    }
    assert scraper.normalize(raw) is None


def test_rss_normalize_missing_title():
    scraper = RssFeedsScraper()
    raw = {
        "_feed": FeedSource(name="x", url="https://x.org/feed"),
        "entry": {"title": "", "summary": "Early childhood matters."},
    }
    assert scraper.normalize(raw) is None
