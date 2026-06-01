# Monitor de Estructura HTML — Documentación Técnica

**Estado:** Implementado (Sprint S7 - Fase 1)  
**Última actualización:** 1 Junio 2026  
**Responsable:** GrantFlow AI  

---

## 📋 Descripción

El **Monitor de Estructura HTML** detecta cambios en la estructura HTML de sitios web que los scrapers dependen. Si selectores CSS dejan de encontrar elementos, alertar a Slack en < 15 minutos.

**Fuentes monitoreadas:**
- `bid.py` → https://bidlab.org/es/convocatorias
- `unwomen.py` → https://www.unwomen.org/en/get-involved/grants
- `developmentaid.py` → https://www.developmentaid.org/news-stream/grants

---

## 🏗️ Arquitectura

```
n8n Scheduler (5 ejecuciones diarias)
    ↓
FastAPI Endpoint: POST /api/v1/monitor/run
    ↓
scraper_monitor.py: run_all_monitors()
    ├─ validate_selectors("bid")
    ├─ validate_selectors("unwomen")
    └─ validate_selectors("developmentaid")
    ↓
Si status != "healthy":
    └─ alert_to_slack() → Slack Webhook
    └─ persist_monitor_log() → Supabase (scraper_monitor_log table)
```

---

## 📁 Archivos Implementados

### 1. Core Monitor Logic
**Archivo:** `backend/app/scrapers/scraper_monitor.py`

**Funciones principales:**
- `validate_selectors(source_name)` — Valida que selectores encuentran elementos
  - Retorna: `{source, status, results, error, checked_at}`
  - Status: `"healthy"` | `"degraded"` | `"failed"`

- `run_all_monitors()` — Ejecuta validación para todas las fuentes
  - Retorna: `list[dict]` con resultados de cada fuente

- `alert_to_slack(result)` — Envía alerta Slack si hay problema
  - Solo alerta si status != `"healthy"`
  - Formato: Slack Block Kit (títulos, colores, detalles)

- `persist_monitor_log(result, db)` — Guarda histórico en BD

### 2. Configuration
**Archivo:** `config/scraper_selectors.json`

Centraliza selectores CSS por fuente:
```json
{
  "bid": {
    "url": "https://bidlab.org/es/convocatorias",
    "selectors": {
      "card": "article, .views-row, .card, li",
      "title": "h1, h2, h3, h4",
      "link": "a[href]",
      "description": "p, .description, .snippet"
    },
    "expected_min": {
      "card": 3,
      "title": 3,
      "link": 3,
      "description": 1
    }
  }
  // ... unwomen, developmentaid
}
```

**Ventajas:**
- Actualizar selectores sin editar código de scraper
- Fácil de auditar: todos los selectores en un lugar
- Versionable con Git

### 3. Database Migration
**Archivo:** `backend/alembic/versions/007_create_scraper_monitor_log.py`

Crea tabla `scraper_monitor_log`:
```sql
CREATE TABLE scraper_monitor_log (
  id UUID PRIMARY KEY,
  source_name VARCHAR(50),
  url VARCHAR(255),
  status VARCHAR(20),  -- 'healthy' | 'degraded' | 'failed'
  results JSONB,       -- {selector: {found, expected, status}}
  error_message TEXT,
  checked_at TIMESTAMP,
  alerted_at TIMESTAMP,
  INDEX(source_name, checked_at),
  INDEX(status)
);
```

### 4. API Endpoint
**Archivo:** `backend/app/api/monitor.py`

**Endpoints:**
```
GET  /api/v1/monitor/health              # Estado actual de todos scrapers
GET  /api/v1/monitor/validate/{source}   # Validar fuente específica
POST /api/v1/monitor/run                 # Ejecutar monitor (n8n trigger)
GET  /api/v1/monitor/log                 # Histórico de monitoreos
```

Ejemplo:
```bash
# Validar BID
curl http://localhost:8000/api/v1/monitor/validate/bid

# Ejecutar monitor completo (típicamente desde n8n)
curl -X POST http://localhost:8000/api/v1/monitor/run \
  -H "Authorization: Bearer gf_live_..."
```

### 5. n8n Workflow
**Archivo:** `n8n-workflows/daily-monitor-html.json`

**Schedule:** Ejecuta 30min ANTES de cada scraper:
- 04:30 (30min antes de nacional_colombia @ 5am)
- 06:30 (30min antes de grantsgov @ 7am)
- 07:30 (30min antes de bid @ 8am)
- 08:30 (30min antes de unwomen @ 9am)
- 09:30 (30min antes de developmentaid @ 10am)

**Lógica:**
1. HTTP POST → `/api/v1/monitor/run`
2. Si respuesta tiene `status: "critical"` → Slack alert detallada
3. Si status OK → Slack confirmación silenciosa

---

## 🚀 Instalación & Setup

### Paso 1: Migración de Base de Datos
```bash
cd backend
alembic upgrade head
```

Crea tabla `scraper_monitor_log`.

### Paso 2: Verificar Configuración
Editar `backend/.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
GRANTFLOW_API_KEY=gf_live_...
```

### Paso 3: Test del Monitor Manualmente
```bash
# Test individual
python -m app.scrapers.scraper_monitor

# Debería output:
# {
#   "source": "bid",
#   "status": "healthy|degraded|failed",
#   "results": {...}
# }
```

### Paso 4: Deploy n8n Workflow
1. Login a n8n (`http://localhost:5678`)
2. `Create new workflow` → `Import from file`
3. Seleccionar `n8n-workflows/daily-monitor-html.json`
4. Actualizar configuración:
   - Webhook URL: Tu Slack webhook
   - API Key: Tu `GRANTFLOW_API_KEY`
5. `Activate` el workflow

---

## 📊 Ejemplo de Alerta Slack

**Si BID selector falla:**

```
🚨 CRITICAL: BID scraper monitor failed

Source:     bid
Status:     FAILED
URL:        https://bidlab.org/es/convocatorias
Checked:    2026-06-01T06:28:45Z

Failed Selectors:
• card: 0 found (expected ≥3)
• title: 0 found (expected ≥3)

Error:
Timeout exceeded while fetching page
```

---

## 🔍 Monitoreo de Resultados

### Dashboard Metabase (Futuro S6)
Query para trackear salud de monitors:
```sql
SELECT
  DATE(checked_at) as fecha,
  source_name,
  COUNT(*) as total_checks,
  SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
  SUM(CASE WHEN status = 'degraded' THEN 1 ELSE 0 END) as degraded_count,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
FROM scraper_monitor_log
WHERE checked_at >= NOW() - INTERVAL '7 days'
GROUP BY fecha, source_name
ORDER BY fecha DESC;
```

### Alertas Automáticas en BD
Cuando `status = 'failed'`, tabla guarda:
- Qué selector falló exactamente
- Cuántos elementos encontró vs esperados
- Timestamp exacto del fallo
- Error message para debugging

---

## 🛠️ Troubleshooting

### Problema: Monitor siempre retorna "degraded" para BID

**Causa probable:** Selectores CSS muy genéricos capturan elementos falsos

**Solución:**
1. Abrir https://bidlab.org/es/convocatorias
2. Inspector → Buscar estructura real (puede haber cambiado)
3. Actualizar `config/scraper_selectors.json`
4. Reejecutar: `curl http://localhost:8000/api/v1/monitor/validate/bid`

### Problema: Slack alerts no llegan

**Causa 1:** SLACK_WEBHOOK_URL no configurado
```bash
# Verificar
echo $SLACK_WEBHOOK_URL
```

**Causa 2:** Webhook URL expirada o incorrecta
- Regenerar en Slack: Workspace Settings → Apps → Manage
- Crear nuevo Incoming Webhook
- Actualizar `.env` y redeploy

### Problema: n8n workflow ejecuta pero no llama al endpoint

**Debugar:**
1. n8n → View logs (ícono de engranaje)
2. Buscar HTTP request errors
3. Verificar que `http://localhost:8000` es alcanzable desde Docker/n8n
4. Si en producción: reemplazar `localhost:8000` con URL pública

---

## 📈 Métricas de Éxito (S7)

| Métrica | Objetivo | Cómo medir |
|---------|----------|-----------|
| **MTTR** (Mean Time To Repair) | < 15 min | Tiempo entre detección de fallo y Slack alert |
| **Cobertura** | 100% de fuentes HTML | Todas 3 fuentes (bid, unwomen, devaid) monitoreadas |
| **False Positives** | < 5% | Alerts que no corresponden a cambios reales |
| **Uptime del monitor** | 99% | Monitor ejecuta 5x diario sin errores |

---

## 🔄 Próximas Fases

### Sprint S7.2 (Mes 2)
- [ ] Task 2: Monitor de API Endpoints
- [ ] Task 3: Monitor de Tasa de Éxito por Scraper
- [ ] Task 5: Alertas en Tiempo Real mejoradas (n8n)

### Sprint S8 (Mes 3)
- [ ] Task 4: Testing Automático de Scrapers
- [ ] Integración de Historical Dashboard en Metabase

---

## 📚 Referencias

- **CLAUDE.md § 6:** Arquitectura de scrapers y stack
- **PLANNER_ACTIVIDADES.md § Task 1:** Descripción original de la tarea
- **Slack Block Kit:** https://api.slack.com/block-kit
- **BeautifulSoup4:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/

---

**Resumen de cambios (hoy 1 junio 2026):**
- ✅ Creado `scraper_monitor.py` con `validate_selectors()` y `alert_to_slack()`
- ✅ Centralizado selectores en `config/scraper_selectors.json`
- ✅ Migración BD para `scraper_monitor_log` table
- ✅ API endpoints `/api/v1/monitor/*` implementados
- ✅ n8n workflow `daily-monitor-html.json` listo para import
- ⏳ Siguiente: Deploy en ambiente dev y test 48h

