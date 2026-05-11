"""Tests para el motor de scoring de 5 criterios."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.scoring_engine import (
    GO_THRESHOLD,
    STRATEGIC_FUNDERS,
    ScoringEngine,
    _extract_json,
)

engine = ScoringEngine()


# ── Criterio 3: Coherencia del ticket ─────────────────────────────────────────


def test_ticket_within_range():
    assert engine._score_ticket(500_000_000, 2_000_000_000) == 2


def test_ticket_min_edge():
    # Justo en el mínimo: dentro del rango
    assert engine._score_ticket(None, 400_000_000) == 2


def test_ticket_max_edge():
    # Justo en el máximo: dentro del rango
    assert engine._score_ticket(None, 5_000_000_000) == 2


def test_ticket_adjacent_range():
    # ±30% del rango — 6B COP cae en zona adyacente (max + 30%)
    assert engine._score_ticket(None, 6_000_000_000) == 1


def test_ticket_adjacent_below():
    # 300M COP cae en zona adyacente (min - 30% ≈ 280M)
    assert engine._score_ticket(None, 300_000_000) == 1


def test_ticket_out_of_range_low():
    # Muy pequeño
    assert engine._score_ticket(None, 50_000_000) == 0


def test_ticket_out_of_range_high():
    # Muy grande
    assert engine._score_ticket(None, 20_000_000_000) == 0


def test_ticket_no_amount():
    # Sin monto: puntaje neutro
    assert engine._score_ticket(None, None) == 1


def test_ticket_uses_max_if_available():
    # Si hay max y min, debe usar max para evaluar
    assert engine._score_ticket(100_000_000, 1_000_000_000) == 2


# ── Criterio 4: Viabilidad operativa ─────────────────────────────────────────


def test_viability_plenty_of_time():
    future = date.today() + timedelta(days=90)
    assert engine._score_viability(future) == 2


def test_viability_just_over_60():
    future = date.today() + timedelta(days=61)
    assert engine._score_viability(future) == 2


def test_viability_at_60_boundary():
    future = date.today() + timedelta(days=60)
    assert engine._score_viability(future) == 1


def test_viability_tight():
    future = date.today() + timedelta(days=45)
    assert engine._score_viability(future) == 1


def test_viability_too_close():
    future = date.today() + timedelta(days=15)
    assert engine._score_viability(future) == 0


def test_viability_no_deadline():
    assert engine._score_viability(None) == 1


def test_viability_already_passed():
    past = date.today() - timedelta(days=5)
    assert engine._score_viability(past) == 0


# ── Criterio 5: Potencial relacional ─────────────────────────────────────────


def test_relational_with_history(make_funder):
    funder = make_funder(has_history=True)
    assert engine._score_relational(funder) == 2


def test_relational_strategic_target(make_funder):
    funder = make_funder(name="LEGO Foundation", has_history=False)
    assert engine._score_relational(funder) == 1


def test_relational_strategic_case_insensitive(make_funder):
    funder = make_funder(name="LeGo FoUnDaTiOn", has_history=False)
    assert engine._score_relational(funder) == 1


def test_relational_unknown(make_funder):
    funder = make_funder(name="Unknown Foundation XYZ", has_history=False)
    assert engine._score_relational(funder) == 0


def test_relational_no_funder():
    assert engine._score_relational(None) == 0


def test_strategic_funders_list_contains_expected():
    """Sanity check: los financiadores estratégicos clave están registrados."""
    assert "lego foundation" in STRATEGIC_FUNDERS
    assert "grand challenges canada" in STRATEGIC_FUNDERS
    assert "bid" in STRATEGIC_FUNDERS
    assert "usaid" in STRATEGIC_FUNDERS


# ── Urgencia ──────────────────────────────────────────────────────────────────


def test_urgency_high():
    assert engine._classify_urgency(date.today() + timedelta(days=10)) == "high"


def test_urgency_at_30_boundary():
    assert engine._classify_urgency(date.today() + timedelta(days=30)) == "high"


def test_urgency_medium():
    assert engine._classify_urgency(date.today() + timedelta(days=45)) == "medium"


def test_urgency_at_60_boundary():
    assert engine._classify_urgency(date.today() + timedelta(days=60)) == "medium"


def test_urgency_low():
    assert engine._classify_urgency(date.today() + timedelta(days=90)) == "low"


def test_urgency_no_deadline():
    assert engine._classify_urgency(None) == "medium"


# ── _extract_json: parser robusto de respuestas LLM ──────────────────────────


def test_extract_json_plain():
    raw = '{"criterion_1": 2, "criterion_2": 1}'
    data = _extract_json(raw)
    assert data["criterion_1"] == 2
    assert data["criterion_2"] == 1


def test_extract_json_with_markdown_fences():
    """Gemini a veces envuelve la respuesta en ```json ... ```"""
    raw = '```json\n{"window": "funding_global"}\n```'
    data = _extract_json(raw)
    assert data["window"] == "funding_global"


def test_extract_json_with_plain_fences():
    raw = '```\n{"criterion_1": 0}\n```'
    data = _extract_json(raw)
    assert data["criterion_1"] == 0


def test_extract_json_invalid_raises():
    with pytest.raises(Exception):
        _extract_json("not valid json {")


# ── Provider detection ──────────────────────────────────────────────────────


def test_provider_none_when_no_keys(monkeypatch):
    """Sin keys, el engine cae a provider 'none' y _score_llm devuelve fallback."""
    monkeypatch.setattr("app.services.scoring_engine.settings.ANTHROPIC_API_KEY", "")
    monkeypatch.setattr("app.services.scoring_engine.settings.GOOGLE_API_KEY", "")
    e = ScoringEngine()
    assert e._provider == "none"


# ── Threshold + decisión ──────────────────────────────────────────────────────


def test_go_threshold_value():
    """El threshold de GO es 6 según CLAUDE.md sección 5.1."""
    assert GO_THRESHOLD == 6


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture
def make_funder():
    def _make(name="Test Foundation", has_history=False, org_type="foundation"):
        funder = MagicMock()
        funder.name = name
        funder.has_history = has_history
        funder.org_type = org_type
        return funder

    return _make
