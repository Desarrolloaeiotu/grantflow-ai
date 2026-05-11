# API Reference — GrantFlow AI

**Base URL Dev:** `http://localhost:8000`  
**Base URL Prod:** `https://api.grantflow.aeiotu.org`

---

## Oportunidades

### `GET /api/v1/opportunities`
Lista oportunidades con filtros.

**Query params:**
| Param | Tipo | Valores |
|-------|------|---------|
| `window` | string | `funding_colombia\|funding_global\|strategic\|latam` |
| `decision` | string | `go\|no_go\|pending` |
| `urgency` | string | `high\|medium\|low` |
| `score_min` | int | 0–10 |
| `source` | string | `grantsgov\|bid\|unwomen\|manual` |
| `status` | string | `detected\|reviewed\|in_crm\|discarded` |
| `page` | int | default 1 |
| `size` | int | default 25, max 100 |

### `GET /api/v1/opportunities/{id}`
Detalle de una oportunidad.

### `POST /api/v1/opportunities/{id}/score`
Fuerza re-scoring de una oportunidad.

### `PATCH /api/v1/opportunities/{id}/status`
Actualiza estado, decisión o urgencia.

**Body:** `{"status": "in_crm", "decision": "go", "urgency": "high"}`

### `GET /api/v1/opportunities/export`
Exporta CSV para importar al CRM.

---

## Dashboard

### `GET /api/v1/dashboard/metrics`
KPIs: total detectadas, Go, pendientes, No Go, score promedio, por ventana, por urgencia.

### `GET /api/v1/dashboard/pipeline`
Pipeline por ventana de mercado (solo decisión Go).

---

## Contactos

### `GET /api/v1/contacts?funder_id={id}`
Contactos por financiador.

### `POST /api/v1/contacts/verify`
Verifica email vía Apollo.io (activar mes 5).

### `POST /api/v1/contacts/enrich`
Dispara enriquecimiento de contactos vía n8n.

---

## RAG

### `POST /api/v1/rag/query`
Consulta semántica sobre oportunidades.

**Body:** `{"query": "early childhood colombia", "top_k": 5}`
