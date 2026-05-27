"""Tests para los scrapers."""

import pytest
from bs4 import BeautifulSoup

from app.scrapers.bid import BidScraper
from app.scrapers.bid import _extract_deadline_text as bid_extract_deadline_text
from app.scrapers.bid import _parse_deadline as bid_parse_deadline
from app.scrapers.developmentaid import DevelopmentAidScraper
from app.scrapers.grantsgov import GrantsGovScraper, _extract_sectors, _parse_date, _usd_to_cop
from app.scrapers.nacional_colombia import NacionalColombiaScraper
from app.scrapers.rss_feeds import (
    FeedSource,
    RssFeedsScraper,
    _clean_html,
    _extract_categories,
    _extract_deadline,
)
from app.scrapers.unwomen import UnWomenScraper
from app.scrapers.unwomen import _parse_deadline as unwomen_parse_deadline


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


# ── BID: _parse_deadline ──────────────────────────────────────────────────────


def test_bid_parse_deadline_iso():
    d = bid_parse_deadline("2026-07-15")
    assert d is not None and d.year == 2026 and d.month == 7 and d.day == 15


def test_bid_parse_deadline_dmy_slash():
    d = bid_parse_deadline("15/07/2026")
    assert d is not None and d.day == 15 and d.month == 7


def test_bid_parse_deadline_mdy_slash():
    # "07/15/2026" fails %d/%m/%Y (month 15 invalid) -> falls to %m/%d/%Y
    d = bid_parse_deadline("07/15/2026")
    assert d is not None and d.month == 7 and d.day == 15


def test_bid_parse_deadline_dmy_dash():
    d = bid_parse_deadline("15-07-2026")
    assert d is not None and d.day == 15 and d.month == 7


def test_bid_parse_deadline_none():
    assert bid_parse_deadline(None) is None


def test_bid_parse_deadline_invalid():
    assert bid_parse_deadline("not-a-date") is None


# ── BID: _extract_deadline_text ───────────────────────────────────────────────


def test_bid_extract_deadline_iso():
    html = "<body><p>Fecha de cierre: 2026-07-15 para la convocatoria.</p></body>"
    soup = BeautifulSoup(html, "lxml")
    result = bid_extract_deadline_text(soup)
    assert result is not None
    assert "2026-07-15" in result


def test_bid_extract_deadline_slash():
    html = "<body><p>Deadline: 15/07/2026.</p></body>"
    soup = BeautifulSoup(html, "lxml")
    result = bid_extract_deadline_text(soup)
    assert result is not None


def test_bid_extract_deadline_no_match():
    html = "<body><p>Open call for proposals, no specific date mentioned.</p></body>"
    soup = BeautifulSoup(html, "lxml")
    assert bid_extract_deadline_text(soup) is None


# ── BID: normalize ────────────────────────────────────────────────────────────


def test_bid_normalize_relevant_ecd():
    scraper = BidScraper()
    raw = {
        "title": "Early Childhood Development Grant 2026",
        "description": "Supporting ECD programs across LATAM",
        "url": "https://bidlab.org/calls/ecd-2026",
        "deadline_text": "2026-09-30",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.funder_name == "BID Lab"
    assert result.source_name == "bid"
    assert result.eligible_countries == ["LATAM"]
    assert result.deadline is not None and result.deadline.year == 2026


def test_bid_normalize_relevant_gender():
    scraper = BidScraper()
    raw = {
        "title": "Women Empowerment Fund for Latin America",
        "description": "",
        "url": "https://bidlab.org/calls/gender-2026",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.capital_type == "grant"


def test_bid_normalize_irrelevant():
    scraper = BidScraper()
    raw = {
        "title": "Infrastructure Roads and Transport Program",
        "description": "Improving transportation networks across South America",
        "url": "https://bidlab.org/calls/roads-2026",
    }
    assert scraper.normalize(raw) is None


def test_bid_normalize_missing_title():
    scraper = BidScraper()
    assert scraper.normalize({"title": "", "url": "https://bidlab.org/x"}) is None


def test_bid_normalize_no_deadline():
    scraper = BidScraper()
    raw = {
        "title": "Formacion Docente en Primera Infancia",
        "description": "",
        "url": "https://bidlab.org/calls/docentes",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.deadline is None


# ── UN Women: _parse_deadline ─────────────────────────────────────────────────


def test_unwomen_parse_deadline_iso():
    d = unwomen_parse_deadline("2026-08-20")
    assert d is not None and d.year == 2026 and d.month == 8 and d.day == 20


def test_unwomen_parse_deadline_dmy():
    d = unwomen_parse_deadline("20/08/2026")
    assert d is not None and d.day == 20 and d.month == 8


def test_unwomen_parse_deadline_mdy():
    # "08/20/2026" fails %d/%m/%Y (month 20 invalid) -> falls to %m/%d/%Y
    d = unwomen_parse_deadline("08/20/2026")
    assert d is not None and d.month == 8 and d.day == 20


def test_unwomen_parse_deadline_none():
    assert unwomen_parse_deadline(None) is None


def test_unwomen_parse_deadline_empty():
    assert unwomen_parse_deadline("") is None


# ── UN Women: normalize ───────────────────────────────────────────────────────


def test_unwomen_normalize_gender_equality():
    scraper = UnWomenScraper()
    raw = {
        "title": "Fund for Gender Equality 2026",
        "description": "Supporting women leadership in Latin America",
        "url": "https://www.unwomen.org/en/grants/fge-2026",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.funder_name == "UN Women"
    assert result.source_name == "unwomen"
    assert "GLOBAL" in result.eligible_countries


def test_unwomen_normalize_early_childhood():
    scraper = UnWomenScraper()
    raw = {
        "title": "Early Childhood Care and Education Initiative",
        "description": "",
        "url": "https://www.unwomen.org/en/grants/ece",
        "deadline_text": "2026-11-30",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.deadline is not None


def test_unwomen_normalize_irrelevant():
    scraper = UnWomenScraper()
    raw = {
        "title": "Annual Report Publication Guidelines",
        "description": "How to submit reports to headquarters.",
        "url": "https://www.unwomen.org/en/about/reports",
    }
    assert scraper.normalize(raw) is None


def test_unwomen_normalize_missing_title():
    scraper = UnWomenScraper()
    assert scraper.normalize({"title": "", "url": "https://www.unwomen.org/x"}) is None


def test_unwomen_normalize_uses_snippet_when_no_description():
    scraper = UnWomenScraper()
    raw = {
        "title": "New Initiative",
        "snippet": "Care economy and women caregivers empowerment program",
        "url": "https://www.unwomen.org/en/grants/care",
    }
    result = scraper.normalize(raw)
    assert result is not None  # keyword found in snippet


# ── DevelopmentAid: normalize ─────────────────────────────────────────────────


def test_devaid_normalize_ecd_in_title():
    scraper = DevelopmentAidScraper()
    raw = {
        "title": "Grants for Early Childhood Development Organizations",
        "snippet": "Open call for NGOs",
        "url": "https://www.developmentaid.org/grants/ecd-2026",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.funder_name is None  # aggregator — no specific funder
    assert result.source_name == "developmentaid"
    assert result.deadline is None  # paywall restricts deadline info


def test_devaid_normalize_keyword_in_snippet():
    scraper = DevelopmentAidScraper()
    raw = {
        "title": "International Funding Opportunity",
        "snippet": "Supporting teacher training and educational leadership in LATAM",
        "url": "https://www.developmentaid.org/grants/teachers",
    }
    assert scraper.normalize(raw) is not None


def test_devaid_normalize_irrelevant():
    scraper = DevelopmentAidScraper()
    raw = {
        "title": "Road Construction Tender Notice",
        "snippet": "Seeking contractors for highway projects in East Africa",
        "url": "https://www.developmentaid.org/tenders/roads",
    }
    assert scraper.normalize(raw) is None


def test_devaid_normalize_missing_title():
    scraper = DevelopmentAidScraper()
    assert scraper.normalize({"title": "", "snippet": "ECD program", "url": "https://x.org"}) is None


def test_devaid_normalize_keyword_in_title_only():
    scraper = DevelopmentAidScraper()
    raw = {
        "title": "Economía del Cuidado en Colombia 2026",
        "snippet": "",
        "url": "https://www.developmentaid.org/grants/cuidado",
    }
    assert scraper.normalize(raw) is not None  # keyword in title


# ── Nacional Colombia: _parse_deadline ───────────────────────────────────────


def test_nacional_parse_deadline_iso():
    d = NacionalColombiaScraper._parse_deadline("2026-03-15")
    assert d is not None and d.year == 2026 and d.month == 3 and d.day == 15


def test_nacional_parse_deadline_dmy_slash():
    d = NacionalColombiaScraper._parse_deadline("15/03/2026")
    assert d is not None and d.day == 15 and d.month == 3


def test_nacional_parse_deadline_dmy_dash():
    d = NacionalColombiaScraper._parse_deadline("15-03-2026")
    assert d is not None and d.day == 15 and d.month == 3


def test_nacional_parse_deadline_spanish_full():
    d = NacionalColombiaScraper._parse_deadline("15 de marzo de 2026")
    assert d is not None and d.day == 15 and d.month == 3 and d.year == 2026


def test_nacional_parse_deadline_spanish_all_months():
    cases = [
        ("1 de enero de 2026", 1),
        ("1 de febrero de 2026", 2),
        ("1 de abril de 2026", 4),
        ("1 de mayo de 2026", 5),
        ("1 de junio de 2026", 6),
        ("1 de julio de 2026", 7),
        ("1 de agosto de 2026", 8),
        ("1 de septiembre de 2026", 9),
        ("1 de octubre de 2026", 10),
        ("1 de noviembre de 2026", 11),
        ("1 de diciembre de 2026", 12),
    ]
    for raw, expected_month in cases:
        d = NacionalColombiaScraper._parse_deadline(raw)
        assert d is not None, f"Failed for: {raw}"
        assert d.month == expected_month


def test_nacional_parse_deadline_none():
    assert NacionalColombiaScraper._parse_deadline(None) is None


def test_nacional_parse_deadline_invalid():
    assert NacionalColombiaScraper._parse_deadline("some random text") is None


# ── Nacional Colombia: normalize ──────────────────────────────────────────────


def test_nacional_normalize_official_source_icbf():
    """Fuentes oficiales (icbf) bypass el filtro de keywords."""
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Convocatoria de alianzas estrategicas 2026",
        "url": "https://www.icbf.gov.co/convocatorias/alianzas",
        "source": "icbf",
        "funder": "ICBF",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.source_name == "nacional_colombia"
    assert result.market_window == "funding_colombia"
    assert result.capital_type == "consultoria"


def test_nacional_normalize_official_source_mineducacion():
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Programa de becas para docentes rurales",
        "url": "https://www.mineducacion.gov.co/becas",
        "source": "mineducacion",
        "funder": "Ministerio de Educacion Nacional",
    }
    assert scraper.normalize(raw) is not None


def test_nacional_normalize_core_keyword_accept():
    """1 keyword CORE es suficiente para fuentes no oficiales."""
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Formación docente para educación inicial en Bogotá",
        "url": "https://www.fundacion.org/convocatoria",
        "source": "fundacion",
        "funder": "Fundacion Local",
    }
    assert scraper.normalize(raw) is not None


def test_nacional_normalize_secondary_keywords_accept():
    """2+ keywords SECONDARY aceptan cuando no hay CORE."""
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Convocatoria de becas para ninos en vulnerabilidad",
        "url": "https://www.org.co/becas",
        "source": "fundacion",
        "funder": "Fundacion",
    }
    # "convocatoria" + "becas" + "ninos" + "vulnerabilidad" >= 2 secondary
    assert scraper.normalize(raw) is not None


def test_nacional_normalize_insufficient_secondary_keywords():
    """Solo 1 keyword SECONDARY sin CORE -> rechazado."""
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Convocatoria de proyectos ambientales en Bogota",
        "url": "https://www.fundacion.org/ambiental",
        "source": "fundacion",
    }
    # "convocatoria" = 1 secondary, no CORE -> rejected
    assert scraper.normalize(raw) is None


def test_nacional_normalize_reject_empleo():
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Vacante de empleo: docente de primera infancia",
        "url": "https://www.empresa.com/empleo/docente",
        "source": "fundacion",
    }
    assert scraper.normalize(raw) is None


def test_nacional_normalize_reject_seleccion():
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Convocatoria para seleccion de personal educativo",
        "url": "https://www.cnsc.gov.co/seleccion",
        "source": "unknown",
    }
    assert scraper.normalize(raw) is None


def test_nacional_normalize_reject_short_title():
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "CDI",  # 3 chars < 10
        "url": "https://www.icbf.gov.co/cdi",
        "source": "icbf",
    }
    assert scraper.normalize(raw) is None


def test_nacional_normalize_reject_empty_url():
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Convocatoria primera infancia Colombia 2026",
        "url": "",
        "source": "icbf",
    }
    assert scraper.normalize(raw) is None


def test_nacional_normalize_reject_relative_url():
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Convocatoria primera infancia Colombia 2026",
        "url": "/convocatoria/123",
        "source": "icbf",
    }
    assert scraper.normalize(raw) is None


def test_nacional_normalize_with_spanish_deadline():
    scraper = NacionalColombiaScraper()
    raw = {
        "title": "Convocatoria CDI primera infancia en Colombia",
        "url": "https://www.icbf.gov.co/convocatoria-cdi",
        "source": "icbf",
        "deadline_text": "15 de marzo de 2026",
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.deadline is not None
    assert result.deadline.month == 3 and result.deadline.day == 15
