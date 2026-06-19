import pytest
from app.services.content_type_detector import detect_content_type, ContentType


def test_detector_identifies_convocatoria():
    content = {
        "title": "Ford Foundation 2026 Innovation Grants - Deadline June 30",
        "description": "Apply now for USD $500K innovation grants",
        "url": "https://fordfoundation.org/grants/2026-innovation"
    }
    result = detect_content_type(content)
    assert result.type == ContentType.CONVOCATORIA
    assert result.confidence > 0.85


def test_detector_rejects_news_article():
    content = {
        "title": "Ford Foundation announces new gender justice initiative",
        "description": "The foundation says it will invest $2B",
        "url": "https://fordfoundation.org/news/2026-gender-justice"
    }
    result = detect_content_type(content)
    assert result.type == ContentType.NEWS
    assert result.confidence > 0.85


def test_detector_classifies_relief_report_as_not_convocatoria():
    content = {
        "title": "Panama: Soluciones Duraderas - Ficha Técnica 2023",
        "description": "This technical fact sheet reports on UNHCR operations",
        "url": "https://reliefweb.int/report/panama/..."
    }
    result = detect_content_type(content)
    assert result.type != ContentType.CONVOCATORIA
    assert result.type in (ContentType.REPORT, ContentType.UNKNOWN)
    assert result.confidence >= 0.5


def test_detector_recognizes_known_grant_portal():
    content = {
        "title": "Some Grant Opportunity",
        "description": "Some description",
        "url": "https://grants.gov/some-grant"
    }
    result = detect_content_type(content)
    assert result.type == ContentType.CONVOCATORIA
    assert result.confidence >= 0.9


def test_detector_handles_empty_content():
    content = {
        "title": "",
        "description": "",
        "url": ""
    }
    result = detect_content_type(content)
    assert result.type == ContentType.UNKNOWN
    assert 0 <= result.confidence <= 1
