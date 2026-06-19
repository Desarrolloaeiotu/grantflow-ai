import pytest
from datetime import date
from app.schemas.convocation import ConvocationCreate, ConvocationRead


def test_valid_convocation_create():
    data = {
        "title": "Ford Foundation 2026 Innovation Grants",
        "objective": "Support innovative models for early childhood development",
        "type": "grant",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://fordfoundation.org/grants/2026-innovation",
        "source_name": "grantsgov",
    }
    conv = ConvocationCreate(**data)
    assert conv.title == "Ford Foundation 2026 Innovation Grants"
    assert conv.type == "grant"
    assert conv.verified == True


def test_convocation_missing_mandatory_field():
    data = {
        "title": "Ford Foundation 2026 Innovation Grants",
        "type": "grant",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://fordfoundation.org/grants/2026-innovation",
        "source_name": "grantsgov",
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)


def test_convocation_invalid_type():
    data = {
        "title": "Some Grant",
        "objective": "Some objective",
        "type": "invalid_type",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://example.com",
        "source_name": "rss",
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)


def test_convocation_deadline_before_open_date():
    data = {
        "title": "Some Grant",
        "objective": "Some objective",
        "type": "grant",
        "open_date": date(2026, 6, 30),
        "deadline": date(2026, 5, 1),
        "url_convocation": "https://example.com",
        "source_name": "rss",
    }
    with pytest.raises(ValueError, match="deadline must be after open_date"):
        ConvocationCreate(**data)


def test_convocation_amount_validation():
    data = {
        "title": "Some Grant",
        "objective": "Some objective",
        "type": "grant",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://example.com",
        "amount_max_cop": 1000,
        "amount_min_cop": 5000,
        "source_name": "rss",
    }
    with pytest.raises(ValueError, match="amount_max_cop must be >= amount_min_cop"):
        ConvocationCreate(**data)


def test_data_completeness_calculation():
    minimal = {
        "title": "Grant Title",
        "objective": "This is a minimal objective with more than ten characters",
        "type": "grant",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://example.com",
        "source_name": "rss",
    }
    conv = ConvocationCreate(**minimal)
    assert 0 <= conv.data_completeness <= 100
    assert conv.verified == True
