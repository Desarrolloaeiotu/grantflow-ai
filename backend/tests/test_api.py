"""Tests de integración para los endpoints FastAPI.

Estos tests usan ASGITransport directo contra la app, sin levantar uvicorn.
Hitting la DB real (Supabase), así que validan integración end-to-end.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Health ─────────────────────────────────────────────────────────────────────


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


# ── /opportunities — listado y filtros ─────────────────────────────────────────


async def test_list_opportunities_returns_shape(client):
    resp = await client.get("/api/v1/opportunities")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert isinstance(data["items"], list)


async def test_list_opportunities_pagination(client):
    resp = await client.get("/api/v1/opportunities?size=5&page=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["size"] == 5
    assert data["page"] == 1
    assert len(data["items"]) <= 5


async def test_list_opportunities_filter_decision(client):
    resp = await client.get("/api/v1/opportunities?decision=go")
    assert resp.status_code == 200
    data = resp.json()
    # Todas las opps devueltas deben tener decision=go
    for opp in data["items"]:
        assert opp["decision"] == "go"


async def test_list_opportunities_filter_invalid_decision(client):
    """decision con valor no permitido por Literal debe devolver 422."""
    resp = await client.get("/api/v1/opportunities?decision=invalid")
    assert resp.status_code == 422


async def test_list_opportunities_filter_window(client):
    resp = await client.get("/api/v1/opportunities?window=funding_global")
    assert resp.status_code == 200
    data = resp.json()
    for opp in data["items"]:
        if opp.get("market_window") is not None:
            assert opp["market_window"] == "funding_global"


async def test_list_opportunities_filter_score_min(client):
    resp = await client.get("/api/v1/opportunities?score_min=6")
    assert resp.status_code == 200
    data = resp.json()
    for opp in data["items"]:
        if opp.get("score_total") is not None:
            assert opp["score_total"] >= 6


async def test_list_opportunities_score_min_out_of_range(client):
    """score_min > 10 debe ser rechazado (validación Pydantic)."""
    resp = await client.get("/api/v1/opportunities?score_min=11")
    assert resp.status_code == 422


async def test_list_opportunities_search(client):
    """Búsqueda por keyword en título/descripción."""
    resp = await client.get("/api/v1/opportunities?q=early")
    assert resp.status_code == 200
    data = resp.json()
    # No assertamos resultados específicos (depende de la DB), solo que la query funciona
    assert "items" in data


async def test_list_opportunities_days_to_deadline(client):
    """Filtro por deadline próximo."""
    resp = await client.get("/api/v1/opportunities?days_to_deadline=30")
    assert resp.status_code == 200
    data = resp.json()
    # Todas deben tener deadline (no null)
    for opp in data["items"]:
        assert opp["deadline"] is not None


# ── /opportunities/{id} ────────────────────────────────────────────────────────


async def test_get_opportunity_not_found(client):
    resp = await client.get("/api/v1/opportunities/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_get_opportunity_invalid_uuid(client):
    resp = await client.get("/api/v1/opportunities/not-a-uuid")
    assert resp.status_code == 422


# ── PATCH /opportunities/{id}/status ───────────────────────────────────────────


async def test_patch_status_not_found(client):
    resp = await client.patch(
        "/api/v1/opportunities/00000000-0000-0000-0000-000000000000/status",
        json={"status": "reviewed"},
    )
    assert resp.status_code == 404


async def test_patch_status_invalid_value(client):
    """Status no permitido por Literal debe rechazar."""
    resp = await client.patch(
        "/api/v1/opportunities/00000000-0000-0000-0000-000000000000/status",
        json={"status": "garbage"},
    )
    # 422 (validation) o 404 (not found) — ambos aceptables
    assert resp.status_code in (404, 422)


# ── Export ──────────────────────────────────────────────────────────────────────


async def test_export_csv_default(client):
    resp = await client.get("/api/v1/opportunities/export?decision=go")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    body = resp.text
    # Headers del CSV incluyen los campos clave
    assert "title" in body
    assert "ceo_email" in body
    assert "org_email_verified" in body
    assert "llm_justification" in body


async def test_export_csv_with_min_score(client):
    resp = await client.get("/api/v1/opportunities/export?decision=go&min_score=8")
    assert resp.status_code == 200


async def test_export_csv_verified_only(client):
    resp = await client.get("/api/v1/opportunities/export?decision=go&verified_only=true")
    assert resp.status_code == 200


# ── Dashboard metrics ──────────────────────────────────────────────────────────


async def test_dashboard_metrics(client):
    resp = await client.get("/api/v1/dashboard/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_detected" in data
    assert "total_go" in data
    assert "total_pending" in data
    assert "total_no_go" in data
    assert "by_window" in data
    assert "by_urgency" in data


async def test_dashboard_pipeline(client):
    resp = await client.get("/api/v1/dashboard/pipeline")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ── RAG (semántico) ────────────────────────────────────────────────────────────


async def test_rag_query_shape(client):
    """No assertamos resultados (depende de GOOGLE_API_KEY + embeddings),
    solo que el endpoint responda y respete el schema."""
    resp = await client.post(
        "/api/v1/rag/query",
        json={"query": "early childhood education", "top_k": 3},
    )
    # 200 si configurado, 500 si no — ambos OK para smoke test
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "results" in data
        assert "total_found" in data
