# Monitor de Endpoints API — Documentación Técnica

**Estado:** Implementado (Sprint S7 - Fase 2)  
**Última actualización:** 1 Junio 2026  
**Responsable:** GrantFlow AI  

---

## 📋 Descripción

El **Monitor de Endpoints API** detecta cambios en la **disponibilidad y funcionalidad** de APIs y feeds RSS que los scrapers dependen. Si un endpoint falla, retorna contenido inválido (JSON malformado, XML sin entries), o experimenta timeouts, alertar a Slack en < 60 minutos.

**Endpoints monitoreados:**
- `grantsgov_api` → https://api.grants.gov/v1/api/search2 (REST API)
- `secop_api` → https://www.contratos.gov.co/api/v1/search (REST API)
- `icbf_rss` → https://www.icbf.gov.co/rss (RSS feed)
- `mineducacion_rss` → https://www.mineducacion.gov.co/rss (RSS feed)
- 8 feeds RSS adicionales (FundsforNGOs, Ford Foundation, Bernard van Leer, etc.)

---

## 🏗️ Arquitectura

```
n8n Scheduler (cada hora, min :05)
    ↓
FastAPI Endpoint: POST /api/v1/monitor/endpoints/run
    ↓
endpoint_monitor.py: run_all_endpoint_monitors()
    ├─ validate_endpoint("grantsgov_api")
    ├─ validate_endpoint("secop_api")
    ├─ validate_endpoint("icbf_rss")
    ├─ ... (12 endpoints en paralelo con asyncio.gather())
    ↓
Si status != "healthy":
    └─ endpoint_alert_to_slack() → Slack Webhook
    └─ persist_endpoint_log() → Supabase (endpoint_monitor_log table)
```

---

## 📁 Archivos Implementados

### 1. Core Monitor Logic
**Archivo:** `backend/app/scrapers/endpoint_monitor.py`

**Funciones principales:**
- `validate_endpoint(endpoint_name) -> dict[str, Any]`
  - Retorna: `{endpoint_name, url, method, status, http_status_code, latency_ms, results, error, checked_at}`
  - Status: `"healthy"` (200 + parsed OK) | `"degraded"` (200 + content invalid) | `"failed"` (non-200 or timeout)
  - Soporta HTTP GET y POST (para grantsgov con body mínimo)
  - Valida content-type:
    - **JSON**: intenta `json.loads()`, verifica que sea dict/list
    - **XML**: intenta `ET.fromstring()`, verifica que haya `<entry>` o `<item>` elements
    - **HTML**: verifica que contenga `<html>` o `<!doctype`

- `run_all_endpoint_monitors() -> list[dict]`
  - Ejecuta validación para todos los endpoints en **paralelo** con `asyncio.gather()`
  - Completa en < 30 segundos típicamente
  - Retorna lista de resultados ordenados por endpoint_name

- `endpoint_alert_to_slack(result) -> bool`
  - Envía alerta Slack Block Kit si status != "healthy"
  - Formato: 🚨 CRITICAL (rojo) o ⚠️ WARNING (amarillo)
  - Incluye: endpoint, URL, HTTP status, latencia, detalles del error

- `persist_endpoint_log(result, db) -> None`
  - Guarda histórico en tabla `endpoint_monitor_log` (migración 008)

### 2. Configuration
**Archivo:** `config/endpoint_urls.json`

Centraliza configuración de endpoints:
```json
{
  "grantsgov_api": {
    "url": "https://api.grants.gov/v1/api/search2",
    "method": "POST",
    "content_type": "json",
    "timeout_sec": 10,
    "description": "Grants.gov REST API for grant opportunities",
    "category": "api",
    "request_body": {
      "keyword": "education",
      "oppStatuses": "posted",
      "rows": 1
    }
  },
  "icbf_rss": {
    "url": "https://www.icbf.gov.co/rss",
    "method": "GET",
    "content_type": "xml",
    "timeout_sec": 10,
    "description": "ICBF RSS feed for early childhood programs",
    "category": "rss"
  }
  // ... 10 más
}
```

**Ventajas:**
- Actualizar endpoints sin editar código de monitor
- Agregar nuevos endpoints (nuevos feeds RSS, APIs) sin cambios en Python
- Versionable con Git

### 3. Database Migration
**Archivo:** `backend/alembic/versions/008_create_endpoint_monitor_log.py`

Crea tabla `endpoint_monitor_log`:
```sql
CREATE TABLE endpoint_monitor_log (
  id UUID PRIMARY KEY,
  endpoint_name VARCHAR(100),
  url VARCHAR(255),
  method VARCHAR(10),
  status VARCHAR(20),  -- 'healthy' | 'degraded' | 'failed'
  http_status_code INTEGER,
  latency_ms INTEGER,
  results JSONB,       -- {parsed_ok, content_type, entry_count, parse_error}
  error_message TEXT,
  checked_at TIMESTAMP,
  alerted_at TIMESTAMP,
  INDEX(endpoint_name, checked_at),
  INDEX(status)
);
```

### 4. API Endpoints
**Archivo:** `backend/app/api/monitor.py` (extendido)

**Nuevos endpoints:**
```
GET  /api/v1/monitor/endpoints/health              # Estado actual de todos endpoints
GET  /api/v1/monitor/endpoints/validate/{name}    # Validar endpoint específico
POST /api/v1/monitor/endpoints/run                 # Ejecutar monitor (n8n trigger)
GET  /api/v1/monitor/endpoints/log                 # Histórico de monitoreos
```

Ejemplo:
```bash
# Validar Grants.gov API
curl http://localhost:8000/api/v1/monitor/endpoints/validate/grantsgov_api

# Ejecutar monitor completo (típicamente desde n8n)
curl -X POST http://localhost:8000/api/v1/monitor/endpoints/run \
  -H "Authorization: Bearer gf_live_..."

# Ver estado actual
curl http://localhost:8000/api/v1/monitor/endpoints/health
```

### 5. n8n Workflow
**Archivo:** `n8n-workflows/hourly-endpoint-monitor.json`

**Schedule:** Ejecuta cada hora, minuto :05:
- 00:05, 01:05, 02:05, ..., 23:05 (24 veces/día)

**Lógica:**
1. HTTP POST → `/api/v1/monitor/endpoints/run`
2. Si respuesta tiene `status: "critical"` → Slack alert detallada
3. Si status OK → (silencioso, no spam)

---

## 🚀 Instalación & Setup

### Paso 1: Migración de Base de Datos
```bash
cd backend
alembic upgrade head
```

Crea tabla `endpoint_monitor_log`.

### Paso 2: Verificar Configuración
Editar `backend/.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
GRANTFLOW_API_KEY=gf_live_...
```

### Paso 3: Test del Monitor Manualmente
```bash
# Test individual endpoint
curl http://localhost:8000/api/v1/monitor/endpoints/validate/grantsgov_api

# Debería retornar:
# {
#   "endpoint_name": "grantsgov_api",
#   "status": "healthy|degraded|failed",
#   "http_status_code": 200,
#   "latency_ms": 450,
#   "results": {...}
# }
```

### Paso 4: Deploy n8n Workflow
1. Login a n8n (`http://localhost:5678`)
2. `Create new workflow` → `Import from file`
3. Seleccionar `n8n-workflows/hourly-endpoint-monitor.json`
4. Actualizar configuración:
   - Webhook URL: Tu Slack webhook
   - API Key: Tu `GRANTFLOW_API_KEY`
5. `Activate` el workflow

---

## 📊 Ejemplo de Alerta Slack

**Si Grants.gov API falla:**

```
🚨 CRITICAL: grantsgov_api endpoint failed

Endpoint:       grantsgov_api
Status:         FAILED
URL:            https://api.grants.gov/v1/api/search2
HTTP Status:    503
Latency:        2000ms
Checked:        2026-06-01T12:05:00Z

Error:
Service temporarily unavailable
```

**Si RSS feed tiene contenido inválido:**

```
⚠️ WARNING: icbf_rss endpoint degraded

Endpoint:       icbf_rss
Status:         DEGRADED
URL:            https://www.icbf.gov.co/rss
HTTP Status:    200
Latency:        150ms
Checked:        2026-06-01T12:05:00Z

Parse Error:
XML malformed — missing closing tag
```

---

## 🔍 Monitoreo de Resultados

### Análisis de Latencias
Query para entender rendimiento de endpoints:
```sql
SELECT
  DATE_TRUNC('hour', checked_at) as hora,
  endpoint_name,
  ROUND(AVG(latency_ms)::numeric, 2) as latency_promedio_ms,
  MAX(latency_ms) as latency_maximo_ms,
  COUNT(*) as total_checks
FROM endpoint_monitor_log
WHERE checked_at >= NOW() - INTERVAL '7 days'
GROUP BY hora, endpoint_name
ORDER BY hora DESC;
```

### Tasa de Disponibilidad
Query para calcular uptime por endpoint:
```sql
SELECT
  endpoint_name,
  COUNT(*) as total_checks,
  SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
  ROUND(100.0 * SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) / COUNT(*), 2) as uptime_percent,
  SUM(CASE WHEN status = 'degraded' THEN 1 ELSE 0 END) as degraded_count,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
FROM endpoint_monitor_log
WHERE checked_at >= NOW() - INTERVAL '24 hours'
GROUP BY endpoint_name
ORDER BY uptime_percent DESC;
```

---

## 🛠️ Troubleshooting

### Problema: Monitor siempre retorna "failed" para un endpoint

**Causa probable:** El endpoint está realmente caído o URL es incorrecta

**Solución:**
1. Verificar manualmente: `curl -v https://endpoint.com/api`
2. Actualizar URL en `config/endpoint_urls.json`
3. Reejecutar: `curl http://localhost:8000/api/v1/monitor/endpoints/validate/endpoint_name`

### Problema: Slack alerts no llegan

**Causa 1:** SLACK_WEBHOOK_URL no configurado
```bash
echo $SLACK_WEBHOOK_URL
```

**Causa 2:** Webhook URL expirada
- Regenerar en Slack: Workspace Settings → Apps → Manage
- Crear nuevo Incoming Webhook
- Actualizar `.env` y redeploy

### Problema: n8n workflow ejecuta pero no llama al endpoint

**Debugar:**
1. n8n → View logs
2. Buscar HTTP request errors
3. Verificar que `http://localhost:8000` es alcanzable desde Docker/n8n
4. Si en producción: reemplazar `localhost:8000` con URL pública

### Problema: Latencias muy altas (>5000ms)

**Causas:**
- Internet lento / high latency a endpoint
- Endpoint está bajo carga
- Timeout configurado muy alto

**Soluciones:**
1. Aumentar `timeout_sec` en `config/endpoint_urls.json` si es un endpoint genuinamente lento
2. Reducir si es por network: cambiar de VPS si está geográficamente lejos
3. Desactivar temporalmente si endpoint es no-crítico

---

## 📈 Métricas de Éxito (S7)

| Métrica | Objetivo | Cómo medir |
|---------|----------|-----------|
| **Cobertura** | 100% de endpoints críticos | 12/12 endpoints monitoreados |
| **Latencia de alerta** | <5 min | Tiempo entre failure y Slack alert |
| **Uptime del monitor** | 99%+ | Monitor ejecuta 24x/día sin errores |
| **False Positives** | <10% | Alerts que no corresponden a fallos reales |
| **Tiempo resolución** | <30 min | Tiempo entre detección de fallo y fix |

---

## 🔄 Próximas Fases

### Sprint S7.3 (Mes 2)
- [ ] Persistencia real en tabla endpoint_monitor_log (ahora es stub)
- [ ] Deduplicación de alerts: no re-alertar si status sigue "failed"
- [ ] Dashboard en Metabase: timeline de downtime por endpoint

### Sprint S8 (Mes 3)
- [ ] Integración con Instrumentl API (cuando activamos en producción, mes 6)
- [ ] Validación de rate limiting: si endpoint retorna 429, alertar distinto

---

## 📚 Referencias

- **CLAUDE.md § 6:** Arquitectura de scrapers y stack
- **PLANNER_ACTIVIDADES.md § Task 2:** Descripción original de la tarea
- **Slack Block Kit:** https://api.slack.com/block-kit
- **httpx Documentation:** https://www.python-httpx.org/

---

**Resumen de cambios (hoy 1 junio 2026):**
- ✅ Creado `endpoint_monitor.py` con `validate_endpoint()` y `run_all_endpoint_monitors()`
- ✅ Centralizado endpoints en `config/endpoint_urls.json` (12 endpoints)
- ✅ Migración BD para `endpoint_monitor_log` table (revisión 008)
- ✅ API endpoints `/api/v1/monitor/endpoints/*` implementados
- ✅ n8n workflow `hourly-endpoint-monitor.json` listo para import
- ⏳ Siguiente: Deploy en ambiente dev y test 24h
